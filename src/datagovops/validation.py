from __future__ import annotations

from .models import (
    DataAssetRecord,
    DataAssetValidationReport,
    DataClassification,
    DataCriticality,
    GovernanceError,
    GovernancePolicy,
)
from .registry import DataAssetRegistry


class DataAssetValidator:
    def validate(
        self,
        asset: DataAssetRecord,
        policy: GovernancePolicy,
        registry: DataAssetRegistry,
        *,
        validated_at: str,
    ) -> DataAssetValidationReport:
        if asset.institution_id != policy.institution_id:
            raise GovernanceError("data asset and governance policy institutions must match")
        registry.assert_registered_asset(asset)

        errors: set[str] = set()
        warnings: set[str] = set()

        if (
            policy.personal_data_requires_retention_policy
            and asset.contains_personal_data
            and not asset.retention_policy_id
        ):
            errors.add("personal_data_retention_policy_missing")
        if (
            policy.restricted_requires_retention_policy
            and asset.classification is DataClassification.RESTRICTED
            and not asset.retention_policy_id
        ):
            errors.add("restricted_data_retention_policy_missing")
        if (
            policy.high_criticality_requires_quality_owner
            and asset.criticality in {DataCriticality.HIGH, DataCriticality.CRITICAL}
            and not asset.quality_owner_id
        ):
            errors.add("high_criticality_quality_owner_missing")

        system = registry.system(asset.institution_id, asset.system_of_record_id)
        if (
            policy.source_of_truth_requires_authoritative_system
            and asset.source_of_truth
            and not system.authoritative
        ):
            errors.add("source_of_truth_system_not_authoritative")

        if asset.owner_id == asset.steward_id:
            if policy.owner_steward_separation_required:
                errors.add("owner_steward_separation_required")
            else:
                warnings.add("owner_and_steward_are_same_principal")
        if asset.contains_personal_data:
            warnings.add("personal_data_requires_later_purpose_and_legal_basis_governance")
        if asset.source_of_truth:
            warnings.add("source_of_truth_requires_later_lineage_and_quality_evidence")

        return DataAssetValidationReport(
            institution_id=asset.institution_id,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            policy_digest=policy.artifact_digest,
            registry_snapshot_digest=registry.snapshot_digest(asset.institution_id),
            structurally_complete=not errors,
            error_codes=tuple(sorted(errors)),
            warning_codes=tuple(sorted(warnings)),
            validated_at=validated_at,
        )


def assert_validation_report_current(
    report: DataAssetValidationReport,
    asset: DataAssetRecord,
    policy: GovernancePolicy,
    registry: DataAssetRegistry,
) -> None:
    if (
        report.institution_id != asset.institution_id
        or report.asset_id != asset.asset_id
        or report.asset_version != asset.asset_version
    ):
        raise GovernanceError("validation report identity does not match data asset")
    registry.assert_registered_asset(asset)
    if report.asset_digest != asset.artifact_digest:
        raise GovernanceError("validation report is stale for current data asset")
    if report.policy_digest != policy.artifact_digest:
        raise GovernanceError("validation report is stale for current governance policy")
    if report.registry_snapshot_digest != registry.snapshot_digest(asset.institution_id):
        raise GovernanceError("validation report is stale for current registry snapshot")
