import unittest

from datagovops import (
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetRegistry,
    DataAssetValidator,
    DataClassification,
    DataCriticality,
    GovernanceError,
    GovernancePolicy,
    GovernancePrincipal,
    PrincipalType,
    assert_validation_report_current,
)


class DataGovCoreTests(unittest.TestCase):
    def principal(self, principal_id, institution="bank-a"):
        return GovernancePrincipal(
            institution_id=institution,
            principal_id=principal_id,
            display_name=principal_id.replace("-", " ").title(),
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-18T07:00:00Z",
        )

    def registry(self, institution="bank-a", *, authoritative=True):
        registry = DataAssetRegistry()
        for principal_id in (
            "owner-1",
            "steward-1",
            "quality-1",
            "classification-owner",
            "criticality-owner",
            "system-owner",
        ):
            registry.register_principal(self.principal(principal_id, institution))
        registry.register_system(
            AuthoritativeSystem(
                institution_id=institution,
                system_id="core-banking",
                name="Core Banking",
                owner_id="system-owner",
                system_type="core-banking",
                authoritative=authoritative,
                registered_at="2026-08-18T07:01:00Z",
            )
        )
        return registry

    def asset(
        self,
        institution="bank-a",
        *,
        version=1,
        retention="ret-7",
        quality_owner="quality-1",
        owner="owner-1",
        steward="steward-1",
        source_of_truth=True,
        name="Customer Balance",
    ):
        return DataAssetRecord(
            institution_id=institution,
            asset_id="customer-balance",
            asset_version=version,
            name=name,
            data_domain="customer",
            owner_id=owner,
            steward_id=steward,
            system_of_record_id="core-banking",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="classification-owner",
            classification_rationale="Contains sensitive customer financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="criticality-owner",
            criticality_rationale="Required for customer balance servicing.",
            contains_personal_data=True,
            source_of_truth=source_of_truth,
            retention_policy_id=retention,
            quality_owner_id=quality_owner,
            registered_at="2026-08-18T07:02:00Z",
        )

    def test_authoritative_references_and_snapshot_are_institution_scoped(self):
        registry = self.registry("bank-a")
        registry.register_asset(self.asset("bank-a"))
        before = registry.snapshot_digest("bank-a")

        for principal_id in (
            "owner-1",
            "steward-1",
            "quality-1",
            "classification-owner",
            "criticality-owner",
            "system-owner",
        ):
            registry.register_principal(self.principal(principal_id, "bank-b"))
        registry.register_system(
            AuthoritativeSystem(
                institution_id="bank-b",
                system_id="core-banking",
                name="Other Core",
                owner_id="system-owner",
                system_type="core-banking",
                authoritative=True,
                registered_at="2026-08-18T07:03:00Z",
            )
        )
        registry.register_asset(self.asset("bank-b"))

        self.assertEqual(before, registry.snapshot_digest("bank-a"))
        self.assertNotEqual(before, registry.snapshot_digest("bank-b"))

    def test_asset_history_is_immutable_contiguous_and_idempotent(self):
        registry = self.registry()
        v1 = self.asset(version=1)
        v2 = self.asset(version=2, name="Customer Balance Canonical")
        self.assertEqual(registry.register_asset(v1), v1.artifact_digest)
        self.assertEqual(registry.register_asset(v1), v1.artifact_digest)
        registry.register_asset(v2)
        self.assertEqual([item.asset_version for item in registry.history("bank-a", "customer-balance")], [1, 2])
        self.assertEqual(registry.latest_asset("bank-a", "customer-balance"), v2)

        with self.assertRaises(GovernanceError):
            registry.register_asset(self.asset(version=4))
        with self.assertRaises(GovernanceError):
            registry.register_asset(self.asset(version=2, name="Conflicting v2"))

    def test_dangling_and_cross_institution_references_fail_closed(self):
        registry = self.registry()
        with self.assertRaises(GovernanceError):
            registry.register_asset(self.asset(owner="unknown-owner"))

        other = self.principal("foreign-owner", "bank-b")
        registry.register_principal(other)
        with self.assertRaises(GovernanceError):
            registry.register_asset(self.asset(owner="foreign-owner"))

        empty = DataAssetRegistry()
        with self.assertRaises(GovernanceError):
            empty.register_system(
                AuthoritativeSystem(
                    institution_id="bank-a",
                    system_id="sys",
                    name="System",
                    owner_id="missing-owner",
                    system_type="source",
                    authoritative=True,
                    registered_at="2026-08-18T07:03:00Z",
                )
            )

    def test_governed_types_fail_closed(self):
        with self.assertRaises(GovernanceError):
            GovernancePrincipal(
                institution_id="bank-a",
                principal_id="p1",
                display_name="P1",
                principal_type="human",
                registered_at="2026-08-18T07:00:00Z",
            )
        with self.assertRaises(GovernanceError):
            AuthoritativeSystem(
                institution_id="bank-a",
                system_id="sys",
                name="System",
                owner_id="owner",
                system_type="source",
                authoritative=1,
                registered_at="2026-08-18T07:00:00Z",
            )
        with self.assertRaises(GovernanceError):
            self.asset(version=True)
        with self.assertRaises(GovernanceError):
            DataAssetRecord(
                **{
                    **self.asset().__dict__,
                    "classification": "restricted",
                }
            )
        with self.assertRaises(GovernanceError):
            GovernancePolicy(
                institution_id="bank-a",
                owner_steward_separation_required=1,
            )

    def test_complete_high_criticality_personal_asset(self):
        registry = self.registry()
        asset = self.asset()
        registry.register_asset(asset)
        policy = GovernancePolicy(institution_id="bank-a")
        report = DataAssetValidator().validate(
            asset,
            policy,
            registry,
            validated_at="2026-08-18T07:04:00Z",
        )
        self.assertTrue(report.structurally_complete)
        self.assertFalse(report.regulatory_compliance_determined)
        self.assertIn(
            "personal_data_requires_later_purpose_and_legal_basis_governance",
            report.warning_codes,
        )
        assert_validation_report_current(report, asset, policy, registry)

    def test_missing_retention_and_quality_owner_fail(self):
        registry = self.registry()
        asset = self.asset(retention=None, quality_owner=None)
        registry.register_asset(asset)
        report = DataAssetValidator().validate(
            asset,
            GovernancePolicy(institution_id="bank-a"),
            registry,
            validated_at="2026-08-18T07:04:00Z",
        )
        self.assertFalse(report.structurally_complete)
        self.assertIn("personal_data_retention_policy_missing", report.error_codes)
        self.assertIn("restricted_data_retention_policy_missing", report.error_codes)
        self.assertIn("high_criticality_quality_owner_missing", report.error_codes)

    def test_source_of_truth_requires_authoritative_system_when_policy_requires_it(self):
        registry = self.registry(authoritative=False)
        asset = self.asset()
        registry.register_asset(asset)
        report = DataAssetValidator().validate(
            asset,
            GovernancePolicy(institution_id="bank-a"),
            registry,
            validated_at="2026-08-18T07:04:00Z",
        )
        self.assertIn("source_of_truth_system_not_authoritative", report.error_codes)

    def test_owner_steward_separation_is_institution_policy(self):
        registry = self.registry()
        asset = self.asset(steward="owner-1")
        registry.register_asset(asset)
        report = DataAssetValidator().validate(
            asset,
            GovernancePolicy(
                institution_id="bank-a",
                owner_steward_separation_required=True,
            ),
            registry,
            validated_at="2026-08-18T07:04:00Z",
        )
        self.assertIn("owner_steward_separation_required", report.error_codes)

    def test_validation_report_fails_closed_when_registry_changes(self):
        registry = self.registry()
        asset = self.asset()
        registry.register_asset(asset)
        policy = GovernancePolicy(institution_id="bank-a")
        report = DataAssetValidator().validate(
            asset,
            policy,
            registry,
            validated_at="2026-08-18T07:04:00Z",
        )
        registry.register_principal(self.principal("new-principal"))
        with self.assertRaises(GovernanceError):
            assert_validation_report_current(report, asset, policy, registry)

    def test_cross_institution_policy_fails(self):
        registry = self.registry()
        asset = self.asset()
        registry.register_asset(asset)
        with self.assertRaises(GovernanceError):
            DataAssetValidator().validate(
                asset,
                GovernancePolicy(institution_id="bank-b"),
                registry,
                validated_at="2026-08-18T07:04:00Z",
            )


if __name__ == "__main__":
    unittest.main()
