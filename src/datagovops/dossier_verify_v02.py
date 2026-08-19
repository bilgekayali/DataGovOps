from __future__ import annotations

from copy import deepcopy

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
        "metric_definition_digests": sorted(item["digest"] for item in metrics if item["payload"].get("report_digest") == report_digest),
        "asset_registry_snapshot_digest": snapshots["inventory"],
        "semantic_registry_snapshot_digest": snapshots["semantic"],
        "lineage_registry_snapshot_digest": snapshots["lineage"],
        "quality_registry_snapshot_digest": snapshots["quality"],
    })


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
            if payload.get("regulatory_compliance_determined") is not False or payload.get("reporting_correctness_determined") is not False:
                raise GovernanceError("report assessment cannot determine compliance or correctness")
            observation_digest = payload.get("observation_digest")
            if observation_digest is not None:
                observation = reporting_by_digest.get(observation_digest)
                if observation is None or observation["artifact_type"] != "ReportProductionObservation":
                    raise GovernanceError("report assessment observation reference mismatch")
                if observation["payload"].get("report_digest") != report["digest"]:
                    raise GovernanceError("report assessment observation belongs to different report")
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
        for retest in [item for item in reporting if item["artifact_type"] == "ReportingRetestEvidence"]:
            finding = reporting_by_digest.get(retest["payload"].get("finding_digest"))
            remediation = reporting_by_digest.get(retest["payload"].get("remediation_digest"))
            if finding is None or remediation is None or finding["artifact_type"] != "ReportingFinding" or remediation["artifact_type"] != "ReportingRemediationEvidence":
                raise GovernanceError("reporting retest lifecycle reference mismatch")
            if remediation["payload"].get("finding_digest") != finding["digest"]:
                raise GovernanceError("reporting retest finding/remediation mismatch")
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
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise GovernanceError("malformed v0.2 governance dossier document") from exc
