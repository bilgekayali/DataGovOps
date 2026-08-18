import unittest

from datagovops import (
    AccessApprovalDecision,
    AccessGrant,
    AccessPurposeApproval,
    AccessRetentionPrivacyRegistry,
    AccessSubjectKind,
    AssetPurposeBinding,
    AuthoritativeSystem,
    BusinessPurpose,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    GovernanceError,
    GovernancePrincipal,
    PrincipalType,
    SemanticGovernanceRegistry,
    digest_artifact,
)


class StrictAccessGovernanceTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def test_superseded_approval_cannot_create_new_grant(self):
        base = DataAssetRegistry()
        for principal_id in (
            "owner",
            "steward",
            "decision-owner",
            "quality-owner",
            "system-owner",
            "purpose-owner",
            "purpose-approver",
            "access-reviewer",
            "grantor",
            "analyst",
        ):
            base.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-18T08:00:00Z",
                )
            )
        base.register_system(
            AuthoritativeSystem(
                institution_id="bank-a",
                system_id="core",
                name="Core",
                owner_id="system-owner",
                system_type="core-banking",
                authoritative=True,
                registered_at="2026-08-18T08:01:00Z",
            )
        )
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            name="Balance",
            data_domain="customer",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="decision-owner",
            classification_rationale="Governed data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="decision-owner",
            criticality_rationale="Critical servicing data.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="retention",
            quality_owner_id="quality-owner",
            registered_at="2026-08-18T08:02:00Z",
        )
        base.register_asset(asset)
        semantic = SemanticGovernanceRegistry(base)
        purpose = BusinessPurpose(
            institution_id="bank-a",
            purpose_id="servicing",
            purpose_version=1,
            name="Servicing",
            description="Institution-owned purpose metadata.",
            owner_id="purpose-owner",
            registered_at="2026-08-18T08:03:00Z",
        )
        semantic.register_purpose(purpose)
        binding = AssetPurposeBinding(
            institution_id="bank-a",
            binding_id="binding",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            approval_owner_id="purpose-approver",
            rationale="Explicit purpose binding.",
            evidence_digest=self.evidence("binding"),
            bound_at="2026-08-18T08:04:00Z",
        )
        semantic.register_purpose_binding(binding)
        registry = AccessRetentionPrivacyRegistry(base, semantic)
        analyst = base.principal("bank-a", "analyst")

        approved = AccessPurposeApproval(
            institution_id="bank-a",
            approval_id="approved",
            subject_kind=AccessSubjectKind.PRINCIPAL,
            subject_id="analyst",
            subject_role_version=None,
            subject_digest=analyst.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            purpose_binding_id=binding.binding_id,
            purpose_binding_digest=binding.artifact_digest,
            decision=AccessApprovalDecision.APPROVED,
            reviewer_id="access-reviewer",
            rationale="Initially approved.",
            evidence_digest=self.evidence("approved"),
            decided_at="2026-08-18T08:05:00Z",
        )
        rejected = AccessPurposeApproval(
            institution_id="bank-a",
            approval_id="rejected",
            subject_kind=AccessSubjectKind.PRINCIPAL,
            subject_id="analyst",
            subject_role_version=None,
            subject_digest=analyst.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            purpose_binding_id=binding.binding_id,
            purpose_binding_digest=binding.artifact_digest,
            decision=AccessApprovalDecision.REJECTED,
            reviewer_id="access-reviewer",
            rationale="Superseding rejection.",
            evidence_digest=self.evidence("rejected"),
            decided_at="2026-08-18T08:06:00Z",
        )
        registry.register_access_approval(approved)
        registry.register_access_approval(rejected)

        grant = AccessGrant(
            institution_id="bank-a",
            grant_id="late-grant",
            approval_digest=approved.artifact_digest,
            subject_kind=AccessSubjectKind.PRINCIPAL,
            subject_id="analyst",
            subject_role_version=None,
            subject_digest=analyst.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            permissions=("read",),
            granted_by_id="grantor",
            valid_from="2026-08-18T08:07:00Z",
            expires_at=None,
            evidence_digest=self.evidence("late-grant"),
            granted_at="2026-08-18T08:07:00Z",
        )
        with self.assertRaises(GovernanceError):
            registry.register_grant(grant)


if __name__ == "__main__":
    unittest.main()
