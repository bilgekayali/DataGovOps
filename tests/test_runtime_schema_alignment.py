import unittest

from datagovops import (
    DataAssetRecord,
    DataClassification,
    DataCriticality,
    GovernanceError,
)


class RuntimeSchemaAlignmentTests(unittest.TestCase):
    def asset(self, *, owner_id="owner-1", classification_rationale="classified"):
        return DataAssetRecord(
            institution_id="bank-a",
            asset_id="asset-1",
            asset_version=1,
            name="Asset One",
            data_domain="finance",
            owner_id=owner_id,
            steward_id="steward-1",
            system_of_record_id="system-1",
            classification=DataClassification.CONFIDENTIAL,
            classification_decision_owner_id="classification-owner",
            classification_rationale=classification_rationale,
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="criticality-owner",
            criticality_rationale="criticality rationale",
            contains_personal_data=False,
            source_of_truth=False,
            retention_policy_id=None,
            quality_owner_id=None,
            registered_at="2026-08-18T07:00:00Z",
        )

    def test_identifier_bound_matches_schema(self):
        with self.assertRaises(GovernanceError):
            self.asset(owner_id="x" * 257)

    def test_rationale_uses_explicit_1024_bound(self):
        self.assertEqual(
            len(self.asset(classification_rationale="r" * 1024).classification_rationale),
            1024,
        )
        with self.assertRaises(GovernanceError):
            self.asset(classification_rationale="r" * 1025)


if __name__ == "__main__":
    unittest.main()
