from __future__ import annotations

from .dossier import verify_dossier_document as _verify_base
from .models import GovernanceError


_ARTIFACT_CONTRACTS = {
    "GovernancePrincipal": ("inventory", "datagovops.governance-principal.v1"),
    "AuthoritativeSystem": ("inventory", "datagovops.authoritative-system.v1"),
    "DataAssetRecord": ("inventory", "datagovops.data-asset-record.v1"),
    "DataElementRecord": ("semantic", "datagovops.data-element-record.v1"),
    "ClassificationDecision": ("semantic", "datagovops.classification-decision.v1"),
    "CriticalDataElementDesignation": ("semantic", "datagovops.critical-data-element-designation.v1"),
    "BusinessPurpose": ("semantic", "datagovops.business-purpose.v1"),
    "AssetPurposeBinding": ("semantic", "datagovops.asset-purpose-binding.v1"),
    "TransformationRecord": ("lineage", "datagovops.transformation-record.v1"),
    "LineageEdge": ("lineage", "datagovops.lineage-edge.v1"),
    "LineageCompletenessRequirement": ("lineage", "datagovops.lineage-completeness-requirement.v1"),
    "QualityRule": ("quality", "datagovops.quality-rule.v1"),
    "QualityEvaluationPolicy": ("quality", "datagovops.quality-evaluation-policy.v1"),
    "QualityObservation": ("quality", "datagovops.quality-observation.v1"),
    "QualityRuleEvaluation": ("quality", "datagovops.quality-rule-evaluation.v1"),
    "QualityFinding": ("quality", "datagovops.quality-finding.v1"),
    "QualityRemediationEvidence": ("quality", "datagovops.quality-remediation-evidence.v1"),
    "QualityRetestEvidence": ("quality", "datagovops.quality-retest-evidence.v1"),
    "AccessRole": ("access_retention_privacy", "datagovops.access-role.v1"),
    "AccessPurposeApproval": ("access_retention_privacy", "datagovops.access-purpose-approval.v1"),
    "AccessGrant": ("access_retention_privacy", "datagovops.access-grant.v1"),
    "RetentionSchedule": ("access_retention_privacy", "datagovops.retention-schedule.v1"),
    "LegalHold": ("access_retention_privacy", "datagovops.legal-hold.v1"),
    "LegalHoldRelease": ("access_retention_privacy", "datagovops.legal-hold-release.v1"),
    "DataLocationEvidence": ("access_retention_privacy", "datagovops.data-location-evidence.v1"),
    "PrivacySecurityObligationMapping": ("access_retention_privacy", "datagovops.privacy-security-obligation-mapping.v1"),
    "GovernanceControlPolicy": ("access_retention_privacy", "datagovops.governance-control-policy.v1"),
    "DataAssetValidationReport": ("assurance", "datagovops.data-asset-validation-report.v1"),
    "LineageCompletenessReport": ("assurance", "datagovops.lineage-completeness-report.v1"),
    "QualityFindingResolution": ("assurance", "datagovops.quality-finding-resolution.v1"),
    "GovernanceControlReport": ("assurance", "datagovops.governance-control-report.v1"),
}


def verify_dossier_document(document: dict) -> str:
    try:
        digest = _verify_base(document)
        dossier = document["dossier"]
        institution_id = dossier["institution_id"]
        for artifact in dossier["artifacts"]:
            artifact_type = artifact["artifact_type"]
            contract = _ARTIFACT_CONTRACTS.get(artifact_type)
            if contract is None:
                raise GovernanceError(f"unsupported dossier artifact type: {artifact_type}")
            expected_domain, expected_schema = contract
            if artifact["domain"] != expected_domain:
                raise GovernanceError("dossier artifact domain does not match artifact type")
            payload = artifact["payload"]
            if payload.get("schema_version") != expected_schema:
                raise GovernanceError("dossier artifact schema version does not match artifact type")
            if payload.get("institution_id") != institution_id:
                raise GovernanceError("dossier artifact institution scope mismatch")

        exception_ids: set[str] = set()
        exception_digests = set(dossier["active_exception_digests"])
        if len(exception_digests) != len(dossier["active_exception_digests"]):
            raise GovernanceError("active exception digests must be unique")
        for exception in dossier["exceptions"]:
            if exception["exception_id"] in exception_ids:
                raise GovernanceError("dossier exception identities must be unique")
            exception_ids.add(exception["exception_id"])
            if exception["institution_id"] != institution_id:
                raise GovernanceError("dossier exception institution scope mismatch")
        return digest
    except GovernanceError:
        raise
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise GovernanceError("malformed governance dossier document") from exc
