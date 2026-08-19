from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from .dossier_verify import verify_dossier_document as _verify_v01
from .models import GovernanceError, digest_artifact


_REPORTING_CONTRACTS = {
    "GovernedReport": "datagovops.governed-report.v1",
    "ReportMetricDefinition": "datagovops.report-metric-definition.v1",
    "ReportProductionObservation": "datagovops.report-production-observation.v1",
    "ReportAssuranceAssessment": "datagovops.report-assurance-assessment.v1",
    "ReportOwnerAttestation": "datagovops.report-owner-attestation.v1",
    "ReportingFinding": "datagovops.reporting-finding.v1",
    "ReportingRemediationEvidence": "datagovops.reporting-remediation-evidence.v1",
    "ReportingRetestEvidence": "datagovops.reporting-retest-evidence.v1",
}


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GovernanceError("reporting timestamp must use RFC3339 UTC Z form")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _reporting_snapshot(
    institution_id: str,
    artifacts: list[dict],
    snapshots: dict[str, str],
) -> str:
    groups = {
        "reports": "GovernedReport",
        "metrics": "ReportMetricDefinition",
        "observations": "ReportProductionObservation",
        "assessments": "ReportAssuranceAssessment",
        "attestations": "ReportOwnerAttestation",
        "findings": "ReportingFinding",
        "remediations": "ReportingRemediationEvidence",
        "retests": "ReportingRetestEvidence",
    }
    payload = {
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": snapshots["inventory"],
        "semantic_registry_snapshot_digest": snapshots["semantic"],
        "lineage_registry_snapshot_digest": snapshots["lineage"],
        "quality_registry_snapshot_digest": snapshots["quality"],
    }
    for key, artifact_type in groups.items():
        payload[key] = sorted(
            item["digest"] for item in artifacts if item["artifact_type"] == artifact_type
        )
    return digest_artifact(payload)


def _latest_metric_items(metrics: list[dict], report_digest: str) -> list[dict]:
    latest: dict[str, dict] = {}
    for item in metrics:
        payload = item["payload"]
        if payload.get("report_digest") != report_digest:
            continue
        metric_id = payload.get("metric_id")
        current = latest.get(metric_id)
        if current is None or payload.get("metric_version") > current["payload"].get("metric_version"):
            latest[metric_id] = item
    return sorted(latest.values(), key=lambda item: item["payload"]["metric_id"])


def _basis(
    institution_id: str,
    report_digest: str,
    metrics: list[dict],
    snapshots: dict[str, str],
) -> str:
    return digest_artifact(
        {
            "institution_id": institution_id,
            "report_digest": report_digest,
            "metric_definition_digests": sorted(
                item["digest"] for item in _latest_metric_items(metrics, report_digest)
            ),
            "asset_registry_snapshot_digest": snapshots["inventory"],
            "semantic_registry_snapshot_digest": snapshots["semantic"],
            "lineage_registry_snapshot_digest": snapshots["lineage"],
            "quality_registry_snapshot_digest": snapshots["quality"],
        }
    )


def _incomplete_controls(report_payload: dict, reason_code: str) -> list[dict]:
    return [
        {
            "metric": "completeness",
            "state": "incomplete",
            "observed_value": None,
            "threshold_value": report_payload["minimum_completeness_basis_points"],
            "reason_code": reason_code,
        },
        {
            "metric": "reconciliation",
            "state": "incomplete",
            "observed_value": None,
            "threshold_value": report_payload["maximum_reconciliation_variance_basis_points"],
            "reason_code": reason_code,
        },
        {
            "metric": "timeliness",
            "state": "incomplete",
            "observed_value": None,
            "threshold_value": report_payload["maximum_lateness_seconds"],
            "reason_code": reason_code,
        },
    ]


def _expected_controls(
    report: dict,
    observation: dict | None,
    *,
    metric_definitions_present: bool,
) -> tuple[list[dict], str, list[str]]:
    report_payload = report["payload"]
    if not metric_definitions_present:
        return (
            _incomplete_controls(report_payload, "metric_definition_missing"),
            "incomplete",
            ["metric_definition_missing"],
        )
    if observation is None:
        return (
            _incomplete_controls(report_payload, "production_observation_missing"),
            "incomplete",
            ["production_observation_missing"],
        )

    payload = observation["payload"]
    expected_count = payload.get("expected_record_count")
    actual_count = payload.get("actual_record_count")
    if isinstance(expected_count, bool) or not isinstance(expected_count, int) or expected_count < 1:
        raise GovernanceError("report observation expected_record_count is invalid")
    if isinstance(actual_count, bool) or not isinstance(actual_count, int) or actual_count < 0:
        raise GovernanceError("report observation actual_record_count is invalid")
    lateness = max(
        0,
        int((_time(payload["produced_at"]) - _time(payload["due_at"])).total_seconds()),
    )
    completeness = min(10_000, (actual_count * 10_000) // expected_count)
    reconciliation = payload["reconciliation_variance_basis_points"]
    values = {
        "completeness": (
            completeness,
            report_payload["minimum_completeness_basis_points"],
            completeness >= report_payload["minimum_completeness_basis_points"],
        ),
        "reconciliation": (
            reconciliation,
            report_payload["maximum_reconciliation_variance_basis_points"],
            reconciliation <= report_payload["maximum_reconciliation_variance_basis_points"],
        ),
        "timeliness": (
            lateness,
            report_payload["maximum_lateness_seconds"],
            lateness <= report_payload["maximum_lateness_seconds"],
        ),
    }
    controls = [
        {
            "metric": metric,
            "state": "met" if met else "breached",
            "observed_value": value,
            "threshold_value": threshold,
            "reason_code": "configured_control_satisfied"
            if met
            else "configured_control_breached",
        }
        for metric, (value, threshold, met) in values.items()
    ]
    state = "breached" if any(item["state"] == "breached" for item in controls) else "met"
    return controls, state, []


def _latest_version(items: list[dict], identity: str, version: str) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        key = item["payload"].get(identity)
        if not isinstance(key, str) or not key:
            raise GovernanceError(f"reporting {identity} is malformed")
        grouped.setdefault(key, []).append(item)
    latest: dict[str, dict] = {}
    for key, values in grouped.items():
        ordered = sorted(values, key=lambda item: item["payload"].get(version, 0))
        versions = [item["payload"].get(version) for item in ordered]
        if versions != list(range(1, len(versions) + 1)):
            raise GovernanceError(f"reporting {version} history is not contiguous")
        latest[key] = ordered[-1]
    return latest


def _metric_current_error(
    metric: dict,
    *,
    all_by_digest: dict[str, dict],
    latest_assets: dict[str, dict],
    latest_transformations: dict[str, dict],
    latest_quality_rules: dict[str, dict],
) -> str | None:
    payload = metric["payload"]
    for source in payload.get("source_refs", []):
        current = latest_assets.get(source.get("asset_id"))
        if (
            current is None
            or current["payload"].get("asset_version") != source.get("asset_version")
            or current["digest"] != source.get("asset_digest")
        ):
            return "report metric source asset is stale"
    for digest in payload.get("transformation_digests", []):
        transformation = all_by_digest.get(digest)
        if transformation is None:
            return "report metric transformation evidence is stale"
        current = latest_transformations.get(
            transformation["payload"].get("transformation_id")
        )
        if current is None or current["digest"] != digest:
            return "report metric transformation evidence is stale for latest version"
    for digest in payload.get("quality_rule_digests", []):
        rule = all_by_digest.get(digest)
        if rule is None:
            return "report metric quality-rule evidence is stale"
        current = latest_quality_rules.get(rule["payload"].get("rule_id"))
        if current is None or current["digest"] != digest:
            return "report metric quality-rule evidence is stale for latest version"
    return None


def _validate_assessment_semantics(
    assessment: dict,
    *,
    report: dict,
    metric_items: list[dict],
    observation: dict | None,
) -> None:
    payload = assessment["payload"]
    expected_metric_digests = sorted(item["digest"] for item in metric_items)
    if payload.get("metric_definition_digests") != expected_metric_digests:
        raise GovernanceError("report assessment metric-definition manifest mismatch")
    if (
        payload.get("regulatory_compliance_determined") is not False
        or payload.get("reporting_correctness_determined") is not False
    ):
        raise GovernanceError("report assessment cannot determine compliance or correctness")
    controls, state, gaps = _expected_controls(
        report,
        observation,
        metric_definitions_present=bool(metric_items),
    )
    if payload.get("control_assessments") != controls:
        raise GovernanceError(
            "report assessment controls do not match embedded observation and thresholds"
        )
    if payload.get("state") != state or payload.get("gaps") != gaps:
        raise GovernanceError("report assessment state does not match embedded reporting evidence")


def _current_assessment_error(
    assessment: dict,
    *,
    report: dict,
    current_metrics: list[dict],
    observations: list[dict],
    current_basis: str,
    metric_errors: dict[str, str],
) -> str | None:
    for metric in current_metrics:
        error = metric_errors.get(metric["digest"])
        if error is not None:
            return error
    payload = assessment["payload"]
    assessed_at = _time(payload["assessed_at"])
    candidates = [
        item
        for item in observations
        if item["payload"].get("report_digest") == report["digest"]
        and item["payload"].get("period_id") == payload.get("period_id")
        and _time(item["payload"]["recorded_at"]) <= assessed_at
    ]
    selected = None
    if candidates:
        latest_time = max(_time(item["payload"]["recorded_at"]) for item in candidates)
        latest = [
            item
            for item in candidates
            if _time(item["payload"]["recorded_at"]) == latest_time
        ]
        if len({item["digest"] for item in latest}) > 1:
            return "conflicting latest report production observations fail closed"
        selected = latest[0]
        if selected["payload"].get("reporting_basis_digest") != current_basis:
            return "latest report observation is stale for current reporting basis"
    expected_observation_digest = selected["digest"] if selected is not None else None
    if payload.get("reporting_basis_digest") != current_basis:
        return "report assurance assessment is stale"
    if payload.get("observation_digest") != expected_observation_digest:
        return "report assurance assessment is stale"
    try:
        _validate_assessment_semantics(
            assessment,
            report=report,
            metric_items=current_metrics,
            observation=selected,
        )
    except GovernanceError:
        return "report assurance assessment is stale"
    return None


def verify_dossier_document(document: dict) -> str:
    try:
        if not isinstance(document, dict) or set(document) != {"dossier", "dossier_digest"}:
            raise GovernanceError("dossier document envelope is malformed")
        dossier = document["dossier"]
        if not isinstance(dossier, dict) or digest_artifact(dossier) != document["dossier_digest"]:
            raise GovernanceError("dossier document digest mismatch")

        reporting_snapshots = [
            item
            for item in dossier.get("domain_snapshots", [])
            if item.get("domain") == "reporting"
        ]
        reporting = [
            item for item in dossier.get("artifacts", []) if item.get("domain") == "reporting"
        ]
        if not reporting_snapshots:
            if reporting:
                raise GovernanceError("reporting artifacts require reporting domain snapshot")
            return _verify_v01(document)
        if len(reporting_snapshots) != 1:
            raise GovernanceError("reporting dossier requires exactly one reporting domain snapshot")

        institution_id = dossier["institution_id"]
        generated_at = dossier["generated_at"]
        generated_time = _time(generated_at)
        parent_snapshots = {
            item["domain"]: item["source_snapshot_digest"]
            for item in dossier["domain_snapshots"]
            if item["domain"] != "reporting"
        }
        for required in ("inventory", "semantic", "lineage", "quality"):
            if required not in parent_snapshots:
                raise GovernanceError("reporting dossier is missing parent domain snapshot")

        snapshot = reporting_snapshots[0]
        expected_reporting = _reporting_snapshot(
            institution_id,
            reporting,
            parent_snapshots,
        )
        if snapshot.get("source_snapshot_digest") != expected_reporting:
            raise GovernanceError("reporting domain snapshot digest mismatch")
        if snapshot.get("artifact_digests") != sorted(item["digest"] for item in reporting):
            raise GovernanceError("reporting domain artifact manifest mismatch")
        if dossier.get("coverage", {}).get("reporting", 0) != len(reporting):
            raise GovernanceError("reporting dossier coverage mismatch")

        all_artifacts = dossier["artifacts"]
        all_by_digest = {item["digest"]: item for item in all_artifacts}
        if len(all_by_digest) != len(all_artifacts):
            raise GovernanceError("dossier contains duplicate artifact digests")
        reporting_by_digest = {item["digest"]: item for item in reporting}

        for artifact in reporting:
            artifact_type = artifact.get("artifact_type")
            expected_schema = _REPORTING_CONTRACTS.get(artifact_type)
            if expected_schema is None:
                raise GovernanceError(f"unsupported reporting artifact type: {artifact_type}")
            payload = artifact.get("payload")
            if not isinstance(payload, dict):
                raise GovernanceError("reporting artifact payload must be an object")
            if (
                payload.get("schema_version") != expected_schema
                or payload.get("institution_id") != institution_id
            ):
                raise GovernanceError("reporting artifact schema or institution scope mismatch")
            if (
                digest_artifact(payload) != artifact.get("digest")
                or artifact.get("artifact_id") != artifact.get("digest")
            ):
                raise GovernanceError("reporting artifact digest mismatch")

        reports = [item for item in reporting if item["artifact_type"] == "GovernedReport"]
        metrics = [item for item in reporting if item["artifact_type"] == "ReportMetricDefinition"]
        observations = [item for item in reporting if item["artifact_type"] == "ReportProductionObservation"]
        assessments = [item for item in reporting if item["artifact_type"] == "ReportAssuranceAssessment"]
        attestations = [item for item in reporting if item["artifact_type"] == "ReportOwnerAttestation"]
        findings = [item for item in reporting if item["artifact_type"] == "ReportingFinding"]
        remediations = [item for item in reporting if item["artifact_type"] == "ReportingRemediationEvidence"]
        retests = [item for item in reporting if item["artifact_type"] == "ReportingRetestEvidence"]

        latest_reports = _latest_version(reports, "report_id", "report_version")
        _latest_version(metrics, "metric_id", "metric_version")

        principals = {
            item["payload"].get("principal_id"): item
            for item in all_artifacts
            if item.get("artifact_type") == "GovernancePrincipal"
        }
        systems = {
            item["payload"].get("system_id"): item
            for item in all_artifacts
            if item.get("artifact_type") == "AuthoritativeSystem"
        }
        latest_assets: dict[str, dict] = {}
        for item in (item for item in all_artifacts if item.get("artifact_type") == "DataAssetRecord"):
            asset_id = item["payload"].get("asset_id")
            current = latest_assets.get(asset_id)
            if current is None or item["payload"].get("asset_version") > current["payload"].get("asset_version"):
                latest_assets[asset_id] = item
        latest_transformations: dict[str, dict] = {}
        for item in (item for item in all_artifacts if item.get("artifact_type") == "TransformationRecord"):
            identity = item["payload"].get("transformation_id")
            current = latest_transformations.get(identity)
            if current is None or item["payload"].get("transformation_version") > current["payload"].get("transformation_version"):
                latest_transformations[identity] = item
        latest_quality_rules: dict[str, dict] = {}
        for item in (item for item in all_artifacts if item.get("artifact_type") == "QualityRule"):
            identity = item["payload"].get("rule_id")
            current = latest_quality_rules.get(identity)
            if current is None or item["payload"].get("rule_version") > current["payload"].get("rule_version"):
                latest_quality_rules[identity] = item

        for report in reports:
            if report["payload"].get("owner_id") not in principals:
                raise GovernanceError("governed report owner does not resolve to embedded principal")

        for metric in metrics:
            payload = metric["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None or report["artifact_type"] != "GovernedReport":
                raise GovernanceError("report metric does not resolve to embedded report")
            if payload.get("owner_id") not in principals:
                raise GovernanceError("report metric owner does not resolve to embedded principal")
            for source in payload.get("source_refs", []):
                asset = all_by_digest.get(source.get("asset_digest"))
                if asset is None or asset.get("artifact_type") != "DataAssetRecord":
                    raise GovernanceError("report metric source does not resolve to embedded data asset")
                asset_payload = asset["payload"]
                if (
                    asset_payload.get("asset_id") != source.get("asset_id")
                    or asset_payload.get("asset_version") != source.get("asset_version")
                    or asset_payload.get("institution_id") != institution_id
                ):
                    raise GovernanceError("report metric source asset identity mismatch")
            for digest in payload.get("transformation_digests", []):
                artifact = all_by_digest.get(digest)
                if artifact is None or artifact.get("artifact_type") != "TransformationRecord":
                    raise GovernanceError("report metric transformation reference mismatch")
            for digest in payload.get("quality_rule_digests", []):
                artifact = all_by_digest.get(digest)
                if artifact is None or artifact.get("artifact_type") != "QualityRule":
                    raise GovernanceError("report metric quality-rule reference mismatch")

        for observation in observations:
            payload = observation["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None or report.get("artifact_type") != "GovernedReport":
                raise GovernanceError("report observation does not resolve to report")
            if payload.get("source_system_id") not in systems:
                raise GovernanceError("report observation source system does not resolve")
            if _time(payload["recorded_at"]) < _time(payload["produced_at"]):
                raise GovernanceError("report observation cannot be recorded before production")

        for assessment in assessments:
            payload = assessment["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None or report.get("artifact_type") != "GovernedReport":
                raise GovernanceError("report assessment does not resolve to report")
            metric_items = []
            for digest in payload.get("metric_definition_digests", []):
                metric = reporting_by_digest.get(digest)
                if metric is None or metric.get("artifact_type") != "ReportMetricDefinition":
                    raise GovernanceError("report assessment metric-definition reference mismatch")
                if metric["payload"].get("report_digest") != report["digest"]:
                    raise GovernanceError("report assessment metric belongs to different report")
                metric_items.append(metric)
            observation = None
            observation_digest = payload.get("observation_digest")
            if observation_digest is not None:
                observation = reporting_by_digest.get(observation_digest)
                if observation is None or observation.get("artifact_type") != "ReportProductionObservation":
                    raise GovernanceError("report assessment observation reference mismatch")
                if (
                    observation["payload"].get("report_digest") != report["digest"]
                    or observation["payload"].get("period_id") != payload.get("period_id")
                ):
                    raise GovernanceError("report assessment observation belongs to different report or period")
                if observation["payload"].get("reporting_basis_digest") != payload.get("reporting_basis_digest"):
                    raise GovernanceError("report assessment and observation basis digests disagree")
            _validate_assessment_semantics(
                assessment,
                report=report,
                metric_items=sorted(metric_items, key=lambda item: item["payload"]["metric_id"]),
                observation=observation,
            )

        for attestation in attestations:
            payload = attestation["payload"]
            assessment = reporting_by_digest.get(payload.get("assessment_digest"))
            if assessment is None or assessment.get("artifact_type") != "ReportAssuranceAssessment":
                raise GovernanceError("report attestation does not resolve to assessment")
            report = reporting_by_digest.get(assessment["payload"].get("report_digest"))
            if report is None or payload.get("owner_id") != report["payload"].get("owner_id"):
                raise GovernanceError("report attestation does not use accountable report owner")
            if payload.get("regulatory_approval_determined") is not False:
                raise GovernanceError("report attestation cannot determine regulatory approval")
            if _time(payload["attested_at"]) < _time(assessment["payload"]["assessed_at"]):
                raise GovernanceError("report attestation cannot predate assessment")
            if payload.get("decision") == "approved" and assessment["payload"].get("state") != "met":
                raise GovernanceError("non-met report assessment cannot be approved")

        for finding in findings:
            payload = finding["payload"]
            assessment = reporting_by_digest.get(payload.get("assessment_digest"))
            if assessment is None or assessment.get("artifact_type") != "ReportAssuranceAssessment":
                raise GovernanceError("reporting finding does not resolve to assessment")
            if assessment["payload"].get("state") == "met":
                raise GovernanceError("met report assessment cannot carry a reporting finding")
            if _time(payload["identified_at"]) < _time(assessment["payload"]["assessed_at"]):
                raise GovernanceError("reporting finding cannot predate assessment")

        for remediation in remediations:
            payload = remediation["payload"]
            finding = reporting_by_digest.get(payload.get("finding_digest"))
            if finding is None or finding.get("artifact_type") != "ReportingFinding":
                raise GovernanceError("reporting remediation does not resolve to finding")
            if _time(payload["completed_at"]) < _time(finding["payload"]["identified_at"]):
                raise GovernanceError("reporting remediation cannot predate finding")

        for retest in retests:
            payload = retest["payload"]
            finding = reporting_by_digest.get(payload.get("finding_digest"))
            remediation = reporting_by_digest.get(payload.get("remediation_digest"))
            reassessment = reporting_by_digest.get(payload.get("reassessment_digest"))
            if (
                finding is None
                or remediation is None
                or reassessment is None
                or finding.get("artifact_type") != "ReportingFinding"
                or remediation.get("artifact_type") != "ReportingRemediationEvidence"
                or reassessment.get("artifact_type") != "ReportAssuranceAssessment"
            ):
                raise GovernanceError("reporting retest lifecycle reference mismatch")
            if remediation["payload"].get("finding_digest") != finding["digest"]:
                raise GovernanceError("reporting retest finding/remediation mismatch")
            original = reporting_by_digest.get(finding["payload"].get("assessment_digest"))
            if original is None:
                raise GovernanceError("reporting retest original assessment is missing")
            if (
                reassessment["payload"].get("report_digest") != original["payload"].get("report_digest")
                or reassessment["payload"].get("period_id") != original["payload"].get("period_id")
            ):
                raise GovernanceError("reporting retest reassessment must cover same report and period")
            if _time(reassessment["payload"]["assessed_at"]) < _time(remediation["payload"]["completed_at"]):
                raise GovernanceError("reporting retest reassessment cannot predate remediation")
            if _time(payload["tested_at"]) < _time(reassessment["payload"]["assessed_at"]):
                raise GovernanceError("reporting retest cannot predate bound reassessment")
            expected_outcome = "passed" if reassessment["payload"].get("state") == "met" else "failed"
            if payload.get("outcome") != expected_outcome:
                raise GovernanceError("reporting retest outcome does not match reassessment state")
            if (
                finding["payload"].get("severity") in {"high", "critical"}
                and payload.get("reviewer_id") == remediation["payload"].get("owner_id")
            ):
                raise GovernanceError("high/critical reporting finding requires independent retest")

        actual_reporting_findings = {
            item for item in dossier.get("findings", []) if item.startswith("reporting:")
        }
        actual_reporting_revalidation = {
            item for item in dossier.get("revalidation_findings", []) if item.startswith("reporting:")
        }
        expected_findings: set[str] = set()
        expected_revalidation: set[str] = set()
        if not latest_reports:
            expected_findings.add("reporting:no_reports_configured")

        metric_errors_by_digest: dict[str, str] = {}
        current_assessment_errors: dict[str, str | None] = {}
        current_assessments: set[str] = set()
        current_basis_by_report: dict[str, str] = {}

        for report_id, report in sorted(latest_reports.items()):
            current_metrics = _latest_metric_items(metrics, report["digest"])
            if not current_metrics:
                expected_findings.add(f"reporting:no_metric_definitions:{report_id}")
            for metric in current_metrics:
                error = _metric_current_error(
                    metric,
                    all_by_digest=all_by_digest,
                    latest_assets=latest_assets,
                    latest_transformations=latest_transformations,
                    latest_quality_rules=latest_quality_rules,
                )
                if error is not None:
                    metric_errors_by_digest[metric["digest"]] = error
                    code = f"reporting:metric:{report_id}:{metric['payload']['metric_id']}:{error}"
                    expected_findings.add(code)
                    expected_revalidation.add(code)

            report_assessments = [
                item for item in assessments if item["payload"].get("report_digest") == report["digest"]
            ]
            if not report_assessments:
                expected_findings.add(f"reporting:no_assessment:{report_id}")
                continue
            latest_by_period: dict[str, dict] = {}
            for assessment in report_assessments:
                period_id = assessment["payload"].get("period_id")
                current = latest_by_period.get(period_id)
                if current is None or _time(assessment["payload"]["assessed_at"]) > _time(current["payload"]["assessed_at"]):
                    latest_by_period[period_id] = assessment
            basis = _basis(institution_id, report["digest"], metrics, parent_snapshots)
            current_basis_by_report[report["digest"]] = basis
            errors_for_report = {
                item["digest"]: metric_errors_by_digest[item["digest"]]
                for item in current_metrics
                if item["digest"] in metric_errors_by_digest
            }
            for period_id, assessment in sorted(latest_by_period.items()):
                current_assessments.add(assessment["digest"])
                error = _current_assessment_error(
                    assessment,
                    report=report,
                    current_metrics=current_metrics,
                    observations=observations,
                    current_basis=basis,
                    metric_errors=errors_for_report,
                )
                current_assessment_errors[assessment["digest"]] = error
                if error is not None:
                    code = f"reporting:assessment:{report_id}:{period_id}:{error}"
                    expected_findings.add(code)
                    expected_revalidation.add(code)
                    continue
                state = assessment["payload"].get("state")
                if state == "breached":
                    expected_findings.add(f"reporting:breached:{report_id}:{period_id}")
                elif state == "incomplete":
                    expected_findings.add(f"reporting:incomplete:{report_id}:{period_id}")

                eligible_attestations = [
                    item
                    for item in attestations
                    if item["payload"].get("assessment_digest") == assessment["digest"]
                    and _time(item["payload"]["attested_at"]) <= generated_time
                ]
                if not eligible_attestations:
                    expected_findings.add(f"reporting:attestation_missing:{report_id}:{period_id}")
                else:
                    latest_time = max(_time(item["payload"]["attested_at"]) for item in eligible_attestations)
                    latest = [
                        item
                        for item in eligible_attestations
                        if _time(item["payload"]["attested_at"]) == latest_time
                    ]
                    if len({item["digest"] for item in latest}) > 1:
                        code = f"reporting:attestation_conflict:{report_id}:{period_id}"
                        expected_findings.add(code)
                        expected_revalidation.add(code)
                    else:
                        decision = latest[0]["payload"].get("decision")
                        if decision == "rejected":
                            expected_findings.add(f"reporting:attestation_rejected:{report_id}:{period_id}")
                        elif decision == "escalated":
                            expected_findings.add(f"reporting:attestation_escalated:{report_id}:{period_id}")

        remediations_by_finding: dict[str, list[dict]] = {}
        for item in remediations:
            remediations_by_finding.setdefault(item["payload"]["finding_digest"], []).append(item)
        retests_by_finding: dict[str, list[dict]] = {}
        for item in retests:
            retests_by_finding.setdefault(item["payload"]["finding_digest"], []).append(item)

        for finding in sorted(findings, key=lambda item: item["payload"]["finding_id"]):
            finding_id = finding["payload"]["finding_id"]
            error: str | None = None
            status = "open"
            related_remediations = remediations_by_finding.get(finding["digest"], [])
            remediation = None
            if related_remediations:
                latest_time = max(_time(item["payload"]["completed_at"]) for item in related_remediations)
                latest = [item for item in related_remediations if _time(item["payload"]["completed_at"]) == latest_time]
                if len({item["digest"] for item in latest}) > 1:
                    error = "conflicting latest reporting remediation evidence fails closed"
                else:
                    remediation = latest[0]
                    status = "remediation_submitted"
            if error is None and remediation is not None:
                related_retests = [
                    item
                    for item in retests_by_finding.get(finding["digest"], [])
                    if item["payload"].get("remediation_digest") == remediation["digest"]
                ]
                if related_retests:
                    latest_time = max(_time(item["payload"]["tested_at"]) for item in related_retests)
                    latest = [item for item in related_retests if _time(item["payload"]["tested_at"]) == latest_time]
                    if len({item["digest"] for item in latest}) > 1:
                        error = "conflicting latest reporting retest evidence fails closed"
                    else:
                        retest = latest[0]
                        reassessment = reporting_by_digest.get(retest["payload"].get("reassessment_digest"))
                        if reassessment is None:
                            error = "reporting finding resolution requires reassessment-bound retest evidence"
                        else:
                            current_error = current_assessment_errors.get(reassessment["digest"])
                            if reassessment["digest"] not in current_assessments:
                                report = reporting_by_digest.get(reassessment["payload"].get("report_digest"))
                                if report is None:
                                    current_error = "report assurance assessment is stale"
                                else:
                                    current_metrics = _latest_metric_items(metrics, report["digest"])
                                    basis = current_basis_by_report.get(report["digest"]) or _basis(
                                        institution_id,
                                        report["digest"],
                                        metrics,
                                        parent_snapshots,
                                    )
                                    errors_for_report = {
                                        item["digest"]: metric_errors_by_digest[item["digest"]]
                                        for item in current_metrics
                                        if item["digest"] in metric_errors_by_digest
                                    }
                                    current_error = _current_assessment_error(
                                        reassessment,
                                        report=report,
                                        current_metrics=current_metrics,
                                        observations=observations,
                                        current_basis=basis,
                                        metric_errors=errors_for_report,
                                    )
                            if current_error is not None:
                                error = current_error
                            elif _time(retest["payload"]["tested_at"]) > generated_time:
                                error = "reporting finding resolution cannot predate lifecycle evidence"
                            else:
                                status = "closed" if retest["payload"].get("outcome") == "passed" else "retest_failed"
            if error is None and remediation is not None and _time(remediation["payload"]["completed_at"]) > generated_time:
                error = "reporting finding resolution cannot predate lifecycle evidence"
            if error is None and _time(finding["payload"]["identified_at"]) > generated_time:
                error = "reporting finding resolution cannot predate lifecycle evidence"

            if error is not None:
                code = f"reporting:finding:{finding_id}:{error}"
                expected_findings.add(code)
                expected_revalidation.add(code)
            elif status != "closed":
                expected_findings.add(f"reporting:finding_open:{finding_id}:{status}")

        if actual_reporting_findings != expected_findings:
            raise GovernanceError("dossier reporting findings do not match embedded current state")
        if actual_reporting_revalidation != expected_revalidation:
            raise GovernanceError("dossier reporting revalidation findings do not match embedded current state")

        stripped = deepcopy(document)
        stripped_dossier = stripped["dossier"]
        stripped_dossier["artifacts"] = [
            item for item in stripped_dossier["artifacts"] if item["domain"] != "reporting"
        ]
        stripped_dossier["domain_snapshots"] = [
            item for item in stripped_dossier["domain_snapshots"] if item["domain"] != "reporting"
        ]
        stripped_dossier["coverage"].pop("reporting", None)
        stripped["dossier_digest"] = digest_artifact(stripped_dossier)
        _verify_v01(stripped)
        return document["dossier_digest"]
    except GovernanceError:
        raise
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        raise GovernanceError("malformed v0.2 governance dossier document") from exc
