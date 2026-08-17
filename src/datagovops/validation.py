from __future__ import annotations

from .models import DataAssetRecord, DataAssetValidationReport, DataClassification, DataCriticality, GovernancePolicy


class DataAssetValidator:
    def validate(self, asset: DataAssetRecord, policy: GovernancePolicy, *, validated_at: str) -> DataAssetValidationReport:
        if asset.institution_id != policy.institution_id:
            raise ValueError("data asset and governance policy institutions must match")

        errors: set[str] = set()
        warnings: set[str] = set()

        if policy.personal_data_requires_retention_policy and asset.contains_personal_data and not asset.retention_policy_id:
            errors.add("personal_data_retention_policy_missing")
        if policy.restricted_requires_retention_policy and asset.classification is DataClassification.RESTRICTED and not asset.retention_policy_id:
            errors.add("restricted_data_retention_policy_missing")
        if policy.high_criticality_requires_quality_owner and asset.criticality in {DataCriticality.HIGH, DataCriticality.CRITICAL} and not asset.quality_owner_id:
            errors.add("high_criticality_quality_owner_missing")
        if asset.owner_id == asset.steward_id:
            warnings.add("owner_and_steward_are_same_principal")
        if asset.contains_personal_data:
            warnings.add("personal_data_requires_later_purpose_and_legal_basis_governance")
        if asset.source_of_truth:
            warnings.add("source_of_truth_requires_later_lineage_and_quality_evidence")

        return DataAssetValidationReport(
            institution_id=asset.institution_id,
            asset_id=asset.asset_id,
            asset_digest=asset.artifact_digest,
            policy_digest=policy.artifact_digest,
            structurally_complete=not errors,
            error_codes=tuple(sorted(errors)),
            warning_codes=tuple(sorted(warnings)),
            validated_at=validated_at,
        )
