import unittest

from datagovops import (
    AccessApprovalDecision,
    AccessGrant,
    AccessPurposeApproval,
    AccessRetentionPrivacyRegistry,
    AccessRole,
    AccessSubjectKind,
    AssetPurposeBinding,
    AuthoritativeSystem,
    BusinessPurpose,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    DataLocationEvidence,
    DataLocationKind,
    DeletionEligibilityState,
    GovernanceControlPolicy,
    GovernanceError,
    GovernancePrincipal,
    LegalHold,
    LegalHoldRelease,
    ObligationCategory,
    ObligationMappingStatus,
    PrincipalType,
    PrivacySecurityObligationMapping,
    RetentionSchedule,
    SemanticGovernanceRegistry,
    digest_artifact,
)


class AccessRetentionPrivacyTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def principal(self, principal_id, institution="bank-a"):
        return GovernancePrincipal(
            institution_id=institution,
            principal_id=principal_id,
            display_name=principal_id,
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-18T08:00:00Z",
        )

    def state(self, *, personal=True):
        base = DataAssetRegistry()
        for principal_id in (
            "owner",
            "steward",
            "class-owner",
            "crit-owner",
            "quality-owner",
            "system-owner",
            "purpose-owner",
            "purpose-approver",
            "access-owner",
            "access-reviewer",
            "grantor",
            "analyst",
            "retention-owner",
            "legal-owner",
            "privacy-reviewer",
            "policy-owner",
        ):
            base.register_principal(self.principal(principal_id))
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
            asset_id="customer-balance",
            asset_version=1,
            name="Customer balance",
            data_domain="customer",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="class-owner",
            classification_rationale="Sensitive balance data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="crit-owner",
            criticality_rationale="Required for servicing.",
            contains_personal_data=personal,
            source_of_truth=True,
            retention_policy_id="retention-reference",
            quality_owner_id="quality-owner",
            registered_at="2026-08-18T08:02:00Z",
        )
        base.register_asset(asset)

        semantic = SemanticGovernanceRegistry(base)
        purpose = BusinessPurpose(
            institution_id="bank-a",
            purpose_id="customer-servicing",
            purpose_version=1,
            name="Customer servicing",
            description="Institution-owned business purpose metadata.",
            owner_id="purpose-owner",
            registered_at="2026-08-18T08:03:00Z",
        )
        semantic.register_purpose(purpose)
        binding = AssetPurposeBinding(
            institution_id="bank-a",
            binding_id="balance-servicing",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            approval_owner_id="purpose-approver",
            rationale="Approved institutional purpose mapping.",
            evidence_digest=self.evidence("purpose-binding"),
            bound_at="2026-08-18T08:04:00Z",
        )
        semantic.register_purpose_binding(binding)
        controls = AccessRetentionPrivacyRegistry(base, semantic)
        return base, semantic, controls, asset, purpose, binding

    def role(self):
        return AccessRole(
            institution_id="bank-a",
            role_id="risk-analyst",
            role_version=1,
            name="Risk analyst",
            owner_id="access-owner",
            member_principal_ids=("analyst",),
            permissions=("read", "export"),
            evidence_digest=self.evidence("role-v1"),
            registered_at="2026-08-18T08:05:00Z",
        )

    def approval(self, role, asset, purpose, binding, *, approval_id="approval-1", decision=AccessApprovalDecision.APPROVED, decided_at="2026-08-18T08:06:00Z"):
        return AccessPurposeApproval(
            institution_id="bank-a",
            approval_id=approval_id,
            subject_kind=AccessSubjectKind.ROLE,
            subject_id=role.role_id,
            subject_role_version=role.role_version,
            subject_digest=role.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            purpose_binding_id=binding.binding_id,
            purpose_binding_digest=binding.artifact_digest,
            decision=decision,
            reviewer_id="access-reviewer",
            rationale="Explicit access-purpose review.",
            evidence_digest=self.evidence(approval_id),
            decided_at=decided_at,
        )

    def grant(self, role, asset, purpose, approval):
        return AccessGrant(
            institution_id="bank-a",
            grant_id="grant-1",
            approval_digest=approval.artifact_digest,
            subject_kind=AccessSubjectKind.ROLE,
            subject_id=role.role_id,
            subject_role_version=role.role_version,
            subject_digest=role.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            permissions=("read",),
            granted_by_id="grantor",
            valid_from="2026-08-18T08:07:00Z",
            expires_at="2026-08-20T08:07:00Z",
            evidence_digest=self.evidence("grant"),
            granted_at="2026-08-18T08:07:00Z",
        )

    def schedule(self, asset, *, version=1):
        return RetentionSchedule(
            institution_id="bank-a",
            schedule_id="balance-retention",
            schedule_version=version,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            owner_id="retention-owner",
            retention_trigger_at="2026-08-01T00:00:00Z",
            retention_days=10,
            rationale="Institution-owned retention schedule.",
            evidence_digest=self.evidence(f"retention-{version}"),
            registered_at="2026-08-18T08:08:00Z",
        )

    def policy(self):
        return GovernanceControlPolicy(
            institution_id="bank-a",
            policy_id="control-policy",
            policy_version=1,
            owner_id="policy-owner",
            require_retention_schedule=True,
            require_obligation_mapping_for_personal_data=True,
            require_location_evidence_for_personal_data=True,
            evidence_digest=self.evidence("control-policy"),
            registered_at="2026-08-18T08:09:00Z",
        )

    def test_access_grant_requires_exact_approval_and_newer_rejection_stales_it(self):
        _, _, controls, asset, purpose, binding = self.state()
        role = self.role()
        controls.register_role(role)
        approval = self.approval(role, asset, purpose, binding)
        controls.register_access_approval(approval)
        grant = self.grant(role, asset, purpose, approval)
        controls.register_grant(grant)
        controls.assert_grant_current(grant, as_of="2026-08-18T09:00:00Z")

        rejection = self.approval(
            role,
            asset,
            purpose,
            binding,
            approval_id="approval-2",
            decision=AccessApprovalDecision.REJECTED,
            decided_at="2026-08-18T09:01:00Z",
        )
        controls.register_access_approval(rejection)
        with self.assertRaises(GovernanceError):
            controls.assert_grant_current(grant, as_of="2026-08-18T09:02:00Z")

    def test_role_version_change_stales_grant_and_permissions_cannot_expand(self):
        _, _, controls, asset, purpose, binding = self.state()
        role = self.role()
        controls.register_role(role)
        approval = self.approval(role, asset, purpose, binding)
        controls.register_access_approval(approval)
        grant = self.grant(role, asset, purpose, approval)
        controls.register_grant(grant)

        role_v2 = AccessRole(
            institution_id="bank-a",
            role_id=role.role_id,
            role_version=2,
            name=role.name,
            owner_id=role.owner_id,
            member_principal_ids=role.member_principal_ids,
            permissions=("read",),
            evidence_digest=self.evidence("role-v2"),
            registered_at="2026-08-18T09:00:00Z",
        )
        controls.register_role(role_v2)
        with self.assertRaises(GovernanceError):
            controls.assert_grant_current(grant, as_of="2026-08-18T09:01:00Z")

        bad_grant = AccessGrant(
            institution_id="bank-a",
            grant_id="grant-export",
            approval_digest=approval.artifact_digest,
            subject_kind=AccessSubjectKind.ROLE,
            subject_id=role.role_id,
            subject_role_version=role.role_version,
            subject_digest=role.artifact_digest,
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            permissions=("admin",),
            granted_by_id="grantor",
            valid_from="2026-08-18T08:07:00Z",
            expires_at=None,
            evidence_digest=self.evidence("bad-grant"),
            granted_at="2026-08-18T08:07:00Z",
        )
        with self.assertRaises(GovernanceError):
            controls.register_grant(bad_grant)

    def test_legal_hold_blocks_deletion_until_released(self):
        _, _, controls, asset, _, _ = self.state()
        schedule = self.schedule(asset)
        controls.register_retention_schedule(schedule)
        eligible = controls.evaluate_deletion_eligibility(
            "bank-a",
            asset.asset_id,
            evaluated_at="2026-08-18T10:00:00Z",
        )
        self.assertEqual(eligible.state, DeletionEligibilityState.ELIGIBLE)
        self.assertFalse(eligible.deletion_executed)
        self.assertFalse(eligible.legal_compliance_determined)

        hold = LegalHold(
            institution_id="bank-a",
            hold_id="hold-1",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            owner_id="legal-owner",
            rationale="Explicit institution-owned legal hold evidence.",
            evidence_digest=self.evidence("hold"),
            starts_at="2026-08-15T00:00:00Z",
            recorded_at="2026-08-15T01:00:00Z",
        )
        controls.register_legal_hold(hold)
        blocked = controls.evaluate_deletion_eligibility(
            "bank-a",
            asset.asset_id,
            evaluated_at="2026-08-18T10:00:00Z",
        )
        self.assertEqual(blocked.state, DeletionEligibilityState.BLOCKED_BY_LEGAL_HOLD)
        self.assertEqual(blocked.active_hold_digests, (hold.artifact_digest,))

        release = LegalHoldRelease(
            institution_id="bank-a",
            release_id="release-1",
            hold_id=hold.hold_id,
            hold_digest=hold.artifact_digest,
            released_by_id="legal-owner",
            rationale="Explicit hold release evidence.",
            evidence_digest=self.evidence("release"),
            released_at="2026-08-18T11:00:00Z",
        )
        controls.register_legal_hold_release(release)
        released = controls.evaluate_deletion_eligibility(
            "bank-a",
            asset.asset_id,
            evaluated_at="2026-08-18T12:00:00Z",
        )
        self.assertEqual(released.state, DeletionEligibilityState.ELIGIBLE)
        self.assertEqual(released.active_hold_digests, ())

    def test_cross_border_mapping_requires_explicit_cross_border_location(self):
        _, _, controls, asset, _, _ = self.state()
        domestic = DataLocationEvidence(
            institution_id="bank-a",
            location_id="tr-storage",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            location_kind=DataLocationKind.STORAGE,
            country_code="TR",
            region="Istanbul",
            cross_border=False,
            reviewer_id="privacy-reviewer",
            evidence_digest=self.evidence("tr-location"),
            observed_at="2026-08-18T08:10:00Z",
        )
        controls.register_location(domestic)
        bad = PrivacySecurityObligationMapping(
            institution_id="bank-a",
            mapping_id="cross-border",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            category=ObligationCategory.CROSS_BORDER,
            obligation_reference="institution-cross-border-review",
            status=ObligationMappingStatus.MAPPED,
            reviewer_id="privacy-reviewer",
            rationale="Explicit mapping input.",
            location_evidence_digests=(domestic.artifact_digest,),
            evidence_digest=self.evidence("cross-border-mapping"),
            reviewed_at="2026-08-18T08:11:00Z",
        )
        with self.assertRaises(GovernanceError):
            controls.register_obligation_mapping(bad)

        foreign = DataLocationEvidence(
            institution_id="bank-a",
            location_id="de-processing",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            location_kind=DataLocationKind.PROCESSING,
            country_code="DE",
            region=None,
            cross_border=True,
            reviewer_id="privacy-reviewer",
            evidence_digest=self.evidence("de-location"),
            observed_at="2026-08-18T08:12:00Z",
        )
        controls.register_location(foreign)
        good = PrivacySecurityObligationMapping(
            institution_id="bank-a",
            mapping_id="cross-border-good",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            category=ObligationCategory.CROSS_BORDER,
            obligation_reference="institution-cross-border-review",
            status=ObligationMappingStatus.MAPPED,
            reviewer_id="privacy-reviewer",
            rationale="Explicit mapping input; no legal applicability inference.",
            location_evidence_digests=(foreign.artifact_digest,),
            evidence_digest=self.evidence("cross-border-good"),
            reviewed_at="2026-08-18T08:13:00Z",
        )
        controls.register_obligation_mapping(good)
        self.assertFalse(good.legal_applicability_determined)

    def test_control_gap_report_is_deterministic_and_stales_on_asset_change(self):
        base, _, controls, asset, _, _ = self.state()
        policy = self.policy()
        controls.register_policy(policy)

        report = controls.evaluate_control_gaps(
            "bank-a",
            policy.policy_id,
            evaluated_at="2026-08-18T09:00:00Z",
        )
        codes = {gap.code.value for gap in report.gaps}
        self.assertEqual(
            codes,
            {
                "missing_retention_schedule",
                "missing_obligation_mapping",
                "missing_location_evidence",
            },
        )
        self.assertFalse(report.complete)
        controls.assert_report_current(report, policy.policy_id)

        controls.register_retention_schedule(self.schedule(asset))
        location = DataLocationEvidence(
            institution_id="bank-a",
            location_id="tr-storage",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            location_kind=DataLocationKind.STORAGE,
            country_code="TR",
            region=None,
            cross_border=False,
            reviewer_id="privacy-reviewer",
            evidence_digest=self.evidence("location"),
            observed_at="2026-08-18T09:01:00Z",
        )
        controls.register_location(location)
        mapping = PrivacySecurityObligationMapping(
            institution_id="bank-a",
            mapping_id="privacy-map",
            asset_id=asset.asset_id,
            asset_version=asset.asset_version,
            asset_digest=asset.artifact_digest,
            category=ObligationCategory.PRIVACY,
            obligation_reference="institution-privacy-review",
            status=ObligationMappingStatus.REVIEW_REQUIRED,
            reviewer_id="privacy-reviewer",
            rationale="Human/legal review remains required.",
            location_evidence_digests=(location.artifact_digest,),
            evidence_digest=self.evidence("privacy-map"),
            reviewed_at="2026-08-18T09:02:00Z",
        )
        controls.register_obligation_mapping(mapping)
        complete = controls.evaluate_control_gaps(
            "bank-a",
            policy.policy_id,
            evaluated_at="2026-08-18T09:03:00Z",
        )
        self.assertTrue(complete.complete)
        self.assertEqual(complete.gaps, ())

        asset_v2 = DataAssetRecord(
            institution_id=asset.institution_id,
            asset_id=asset.asset_id,
            asset_version=2,
            name="Customer balance v2",
            data_domain=asset.data_domain,
            owner_id=asset.owner_id,
            steward_id=asset.steward_id,
            system_of_record_id=asset.system_of_record_id,
            classification=asset.classification,
            classification_decision_owner_id=asset.classification_decision_owner_id,
            classification_rationale=asset.classification_rationale,
            criticality=asset.criticality,
            criticality_decision_owner_id=asset.criticality_decision_owner_id,
            criticality_rationale=asset.criticality_rationale,
            contains_personal_data=asset.contains_personal_data,
            source_of_truth=asset.source_of_truth,
            retention_policy_id=asset.retention_policy_id,
            quality_owner_id=asset.quality_owner_id,
            registered_at="2026-08-18T10:00:00Z",
        )
        base.register_asset(asset_v2)
        stale = controls.evaluate_control_gaps(
            "bank-a",
            policy.policy_id,
            evaluated_at="2026-08-18T10:01:00Z",
        )
        stale_codes = {gap.code.value for gap in stale.gaps}
        self.assertEqual(
            stale_codes,
            {
                "stale_retention_schedule",
                "stale_obligation_mapping",
                "stale_location_evidence",
            },
        )
        with self.assertRaises(GovernanceError):
            controls.assert_report_current(complete, policy.policy_id)

    def test_conflicting_latest_access_approval_fails_closed(self):
        _, _, controls, asset, purpose, binding = self.state()
        role = self.role()
        controls.register_role(role)
        approved = self.approval(
            role,
            asset,
            purpose,
            binding,
            approval_id="approved",
            decision=AccessApprovalDecision.APPROVED,
            decided_at="2026-08-18T09:00:00.500000Z",
        )
        rejected = self.approval(
            role,
            asset,
            purpose,
            binding,
            approval_id="rejected",
            decision=AccessApprovalDecision.REJECTED,
            decided_at="2026-08-18T09:00:00.500000Z",
        )
        controls.register_access_approval(approved)
        controls.register_access_approval(rejected)
        with self.assertRaises(GovernanceError):
            controls.latest_access_approval(
                institution_id="bank-a",
                subject_kind=AccessSubjectKind.ROLE,
                subject_id=role.role_id,
                asset_id=asset.asset_id,
                purpose_id=purpose.purpose_id,
            )

    def test_governed_types_and_nonclaims_fail_closed(self):
        with self.assertRaises(GovernanceError):
            AccessRole(
                institution_id="bank-a",
                role_id="r",
                role_version=True,
                name="Role",
                owner_id="owner",
                member_principal_ids=("a",),
                permissions=("read",),
                evidence_digest=self.evidence("r"),
                registered_at="2026-08-18T08:00:00Z",
            )
        with self.assertRaises(GovernanceError):
            DataLocationEvidence(
                institution_id="bank-a",
                location_id="loc",
                asset_id="a",
                asset_version=1,
                asset_digest=self.evidence("a"),
                location_kind="storage",
                country_code="TR",
                region=None,
                cross_border=False,
                reviewer_id="reviewer",
                evidence_digest=self.evidence("loc"),
                observed_at="2026-08-18T08:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
