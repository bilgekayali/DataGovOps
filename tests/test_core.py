import unittest

from datagovops.models import DataAssetRecord, DataClassification, DataCriticality, GovernancePolicy
from datagovops.registry import DataAssetRegistry
from datagovops.validation import DataAssetValidator


class DataGovCoreTests(unittest.TestCase):
    def asset(self, institution="bank-a", retention="ret-7", quality_owner="quality-1"):
        return DataAssetRecord(
            institution_id=institution,
            asset_id="customer-balance",
            name="Customer Balance",
            data_domain="customer",
            owner_id="owner-1",
            steward_id="steward-1",
            system_of_record="core-banking",
            classification=DataClassification.RESTRICTED,
            criticality=DataCriticality.HIGH,
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id=retention,
            quality_owner_id=quality_owner,
            registered_at="2026-08-17T12:00:00Z",
        )

    def test_registry_is_tenant_scoped(self):
        registry = DataAssetRegistry()
        registry.register(self.asset("bank-a"))
        registry.register(self.asset("bank-b"))
        self.assertEqual(len(registry.list_for_institution("bank-a")), 1)
        self.assertEqual(len(registry.list_for_institution("bank-b")), 1)

    def test_complete_high_criticality_personal_asset(self):
        asset = self.asset()
        report = DataAssetValidator().validate(asset, GovernancePolicy(institution_id="bank-a"), validated_at="2026-08-17T12:01:00Z")
        self.assertTrue(report.structurally_complete)
        self.assertFalse(report.regulatory_compliance_determined)
        self.assertIn("personal_data_requires_later_purpose_and_legal_basis_governance", report.warning_codes)

    def test_missing_retention_and_quality_owner_fail(self):
        asset = self.asset(retention=None, quality_owner=None)
        report = DataAssetValidator().validate(asset, GovernancePolicy(institution_id="bank-a"), validated_at="2026-08-17T12:01:00Z")
        self.assertFalse(report.structurally_complete)
        self.assertIn("personal_data_retention_policy_missing", report.error_codes)
        self.assertIn("high_criticality_quality_owner_missing", report.error_codes)

    def test_cross_tenant_policy_fails(self):
        with self.assertRaises(ValueError):
            DataAssetValidator().validate(self.asset("bank-a"), GovernancePolicy(institution_id="bank-b"), validated_at="2026-08-17T12:01:00Z")


if __name__ == "__main__":
    unittest.main()
