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
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _reporting_snapshot(institution_id: str, artifacts: list[dict], snapshots: dict[str, str]) -> str:
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
        payload[key] = sorted(item["digest"] for item in artifacts if item["artifact_type"] == artifact_type)
    return digest_artifact(payload)


def _basis(institution_id: str, report_digest: str, metrics: list[dict], snapshots: dict[str, str]) -> str:
    return digest_artifact({
        "institution_id": institution_id,
        "report_digest": report_digest,
        "metric_definition_digests": sorted(
            item["digest"]
            for item in metrics
            if item["payload"].get("report_digest") == report_digest
        ),
        "asset_registry_snapshot_digest": snapshots["inventory"],
        "semantic_registry_snapshot_digest": snapshots["semantic"],
        "lineage_registry_snapshot_digest": snapshots["lineage"],
        "quality_registry_snapshot_digest": snapshots["quality"],
    })


def _expected_controls(report: dict, observation: dict | None) -> tuple[list[dict], str, list[str]]:
    report_payload = report["payload"]
    if observation is None:
        controls = [
            {
                "metric": "completeness",
                "state": "incomplete",
                "observed_value": None,
                "threshold_value": report_payload["minimum_completeness_basis_points"],
                "reason_code": "production_observation_missing",
            },
            {
                "metric": "reconciliation",
                "state": "incomplete",
                "observed_value": None,
                "threshold_value": report_payload["maximum_reconciliation_variance_basis_points"],
                "reason_code": "production_observation_missing",
            },
            {
                "metric": "timeliness",
                "state": "incomplete",
                "observed_value": None,
                "threshold_value": report_payload["maximum_lateness_seconds"],
                "reason_code": "production_observation_missing",
            },
        ]
        return controls, "incomplete", ["production_observation_missing"]

    payload = observation["payload"]
    lateness = max(0, int((_time(payload["produced_at"]) - _time(payload["due_at"])).total_seconds()))
    completeness = min(
        10_000,
        (payload["actual_record_count"] * 10_000) // payload["expected_record_count"],
    )
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
            "reason_code": "configured_control_satisfied" if met else "configured_control_breached",
        }
        for metric, (value, threshold, met) in values.items()
    ]
    state = "breached" if any(item["state"] == "breached" for item in controls) else "met"
    return controls, state, []


def verify_dossier_document(document: dict) -> str:
    try:
        if not isinstance(document, dict) or set(document) != {"dossier", "dossier_digest"}:
            raise GovernanceError("dossier document envelope is malformed")
        dossier = document["dossier"]
        if digest_artifact(dossier) != document["dossier_digest"]:
            raise GovernanceError("dossier document digest mismatch")
        reporting = [item for item in dossier["artifacts"] if item.get("domain") == "reporting"]
        if not reporting:
            return _verify_v01(document)
        institution_id = dossier["institution_id"]
        reporting_snapshots = [item for item in dossier["domain_snapshots"] if item.get("domain") == "reporting"]
        if len(reporting_snapshots) != 1:
            raise GovernanceError("reporting dossier requires exactly one reporting domain snapshot")
        parent_snapshots = {
            item["domain"]: item["source_snapshot_digest"]
            for item in dossier["domain_snapshots"]
            if item["domain"] != "reporting"
        }
        expected_reporting = _reporting_snapshot(institution_id, reporting, parent_snapshots)
        snapshot = reporting_snapshots[0]
        if snapshot["source_snapshot_digest"] != expected_reporting:
            raise GovernanceError("reporting domain snapshot digest mismatch")
        if snapshot["artifact_digests"] != sorted(item["digest"] for item in reporting):
            raise GovernanceError("reporting domain artifact manifest mismatch")
        all_by_digest = {item["digest"]: item for item in dossier["artifacts"]}
        reporting_by_digest = {item["digest"]: item for item in reporting}
        for artifact in reporting:
            artifact_type = artifact["artifact_type"]
            expected_schema = _REPORTING_CONTRACTS.get(artifact_type)
            if expected_schema is None:
                raise GovernanceError(f"unsupported reporting artifact type: {artifact_type}")
            payload = artifact["payload"]
            if payload.get("schema_version") != expected_schema or payload.get("institution_id") != institution_id:
                raise GovernanceError("reporting artifact schema or institution scope mismatch")
            if digest_artifact(payload) != artifact["digest"] or artifact["artifact_id"] != artifact["digest"]:
                raise GovernanceError("reporting artifact digest mismatch")
        reports = [item for item in reporting if item["artifact_type"] == "GovernedReport"]
        metrics = [item for item in reporting if item["artifact_type"] == "ReportMetricDefinition"]
        observations = [item for item in reporting if item["artifact_type"] == "ReportProductionObservation"]
        assessments = [item for item in reporting if item["artifact_type"] == "ReportAssuranceAssessment"]
        for metric in metrics:
            payload = metric["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None or report["artifact_type"] != "GovernedReport":
                raise GovernanceError("report metric does not resolve to embedded report")
            for source in payload.get("source_refs", []):
                asset = all_by_digest.get(source.get("asset_digest"))
                if asset is None or asset["artifact_type"] != "DataAssetRecord":
                    raise GovernanceError("report metric source does not resolve to embedded data asset")
                asset_payload = asset["payload"]
                if asset_payload.get("asset_id") != source.get("asset_id") or asset_payload.get("asset_version") != source.get("asset_version"):
                    raise GovernanceError("report metric source asset identity mismatch")
            for digest in payload.get("transformation_digests", []):
                artifact = all_by_digest.get(digest)
                if artifact is None or artifact["artifact_type"] != "TransformationRecord":
                    raise GovernanceError("report metric transformation reference mismatch")
            for digest in payload.get("quality_rule_digests", []):
                artifact = all_by_digest.get(digest)
                if artifact is None or artifact["artifact_type"] != "QualityRule":
                    raise GovernanceError("report metric quality-rule reference mismatch")
        for observation in observations:
            payload = observation["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None:
                raise GovernanceError("report observation does not resolve to report")
            if payload.get("reporting_basis_digest") != _basis(institution_id, report["digest"], metrics, parent_snapshots):
                raise GovernanceError("report observation basis digest mismatch")
        for assessment in assessments:
            payload = assessment["payload"]
            report = reporting_by_digest.get(payload.get("report_digest"))
            if report is None:
                raise GovernanceError("report assessment does not resolve to report")
            basis = _basis(institution_id, report["digest"], metrics, parent_snapshots)
            if payload.get("reporting_basis_digest") != basis:
                raise GovernanceError("report assessment basis digest mismatch")
            expected_metrics = sorted(
                item["digest"]
                for item in metrics
                if item["payload"].get("report_digest") == report["digest"]
            )
            if payload.get("metric_definition_digests") != expected_metrics:
                raise GovernanceError("report assessment metric-definition manifest mismatch")
            if payload.get("regulatory_compliance_determined") is not False or payload.get("reporting_correctness_determined") is not False:
                raise GovernanceError("report assessment cannot determine compliance or correctness")
            observation_digest = payload.get("observation_digest")
            observation = None
            if observation_digest is not None:
                observation = reporting_by_digest.get(observation_digest)
                if observation is None or observation["artifact_type"] != "ReportProductionObservation":
                    raise GovernanceError("report assessment observation reference mismatch")
                if observation["payload"].get("report_digest") != report["digest"]:
                    raise GovernanceError("report assessment observation belongs to different report")
                if observation["payload"].get("period_id") != payload.get("period_id"):
                    raise GovernanceError("report assessment observation belongs to different period")
            controls, state, gaps = _expected_controls(report, observation)
            if payload.get("control_assessments") != controls:
                raise GovernanceError("report assessment controls do not match embedded observation and thresholds")
            if payload.get("state") != state or payload.get("gaps") != gaps:
                raise GovernanceError("report assessment state does not match embedded reporting evidence")
        for artifact_type, ref_field, target_type in (
            ("ReportOwnerAttestation", "assessment_digest", "ReportAssuranceAssessment"),
            ("ReportingFinding", "assessment_digest", "ReportAssuranceAssessment"),
            ("ReportingRemediationEvidence", "finding_digest", "ReportingFinding"),
        ):
            for artifact in reporting:
                if artifact["artifact_type"] != artifact_type:
                    continue
                target = reporting_by_digest.get(artifact["payload"].get(ref_field))
                if target is None or target["artifact_type"] != target_type:
                    raise GovernanceError("reporting lifecycle reference mismatch")
        for attestation in [item for item in reporting if item["artifact_type"] == "ReportOwnerAttestation"]:
            assessment = reporting_by_digest[attestation["payload"]["assessment_digest"]]
            report = reporting_by_digest.get(assessment["payload"].get("report_digest"))
            if report is None or attestation["payload"].get("owner_id") != report["payload"].get("owner_id"):
                raise GovernanceError("report attestation does not use accountable report owner")
            if attestation["payload"].get("regulatory_approval_determined") is not False:
                raise GovernanceError("report attestation cannot determine regulatory approval")
            if attestation["payload"].get("decision") == "approved" and assessment["payload"].get("state") != "met":
                raise GovernanceError("non-met report assessment cannot be approved")
        for finding in [item for item in reporting if item["artifact_type"] == "ReportingFinding"]:
            assessment = reporting_by_digest[finding["payload"]["assessment_digest"]]
            if assessment["payload"].get("state") == "met":
                raise GovernanceError("met report assessment cannot carry a reporting finding")
        for retest in [item for item in reporting if item["artifact_type"] == "ReportingRetestEvidence"]:
            finding = reporting_by_digest.get(retest["payload"].get("finding_digest"))
            remediation = reporting_by_digest.get(retest["payload"].get("remediation_digest"))
            if finding is None or remediation is None or finding["artifact_type"] != "ReportingFinding" or remediation["artifact_type"] != "ReportingRemediationEvidence":
                raise GovernanceError("reporting retest lifecycle reference mismatch")
            if remediation["payload"].get("finding_digest") != finding["digest"]:
                raise GovernanceError("reporting retest finding/remediation mismatch")
            if finding["payload"].get("severity") in {"high", "critical"} and retest["payload"].get("reviewer_id") == remediation["payload"].get("owner_id"):
                raise GovernanceError("high/critical reporting finding requires independent retest")
        stripped = deepcopy(document)
        stripped_dossier = stripped["dossier"]
        stripped_dossier["artifacts"] = [item for item in stripped_dossier["artifacts"] if item["domain"] != "reporting"]
        stripped_dossier["domain_snapshots"] = [item for item in stripped_dossier["domain_snapshots"] if item["domain"] != "reporting"]
        stripped_dossier["coverage"].pop("reporting", None)
        stripped["dossier_digest"] = digest_artifact(stripped_dossier)
        _verify_v01(stripped)
        return document["dossier_digest"]
    except GovernanceError:
        raise
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        raise GovernanceError("malformed v0.2 governance dossier document") from exc
