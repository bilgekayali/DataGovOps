import json
from pathlib import Path
import unittest

import jsonschema

import datagovops
from datagovops import (
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetValidationReport,
    DataClassification,
    DataCriticality,
    GovernancePolicy,
    GovernancePrincipal,
    PrincipalType,
    canonical_json,
)

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_version_is_v0_5_0_at_release_gate(self):
        self.assertEqual(datagovops.__version__, "0.5.0")

    def _schema(self, name):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        self.assertFalse(schema["additionalProperties"])
        return schema

    def test_strict_schemas_accept_runtime_contracts(self):
        principal = GovernancePrincipal(
            institution_id="bank-a",
            principal_id="owner-1",
            display_name="Owner One",
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-18T07:00:00Z",
        )
        system = AuthoritativeSystem(
            institution_id="bank-a",
            system_id="core",
            name="Core Banking",
            owner_id="owner-1",
            system_type="core-banking",
            authoritative=True,
            registered_at="2026-08-18T07:01:00Z",
        )
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            name="Balance",
            data_domain="customer",
            owner_id="owner-1",
            steward_id="owner-1",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="owner-1",
            classification_rationale="Sensitive financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="owner-1",
            criticality_rationale="Required for servicing.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="ret-1",
            quality_owner_id="owner-1",
            registered_at="2026-08-18T07:02:00Z",
        )
        policy = GovernancePolicy(institution_id="bank-a")
        report = DataAssetValidationReport(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            asset_digest=asset.artifact_digest,
            policy_digest=policy.artifact_digest,
            registry_snapshot_digest="a" * 64,
            structurally_complete=True,
            error_codes=(),
            warning_codes=("later_control_required",),
            validated_at="2026-08-18T07:03:00Z",
        )

        fixtures = {
            "governance-principal.schema.json": principal,
            "authoritative-system.schema.json": system,
            "data-asset-record.schema.json": asset,
            "governance-policy.schema.json": policy,
            "data-asset-validation-report.schema.json": report,
        }
        for schema_name, artifact in fixtures.items():
            with self.subTest(schema=schema_name):
                schema = self._schema(schema_name)
                payload = json.loads(canonical_json(artifact))
                jsonschema.Draft202012Validator(schema).validate(payload)

    def test_asset_schema_rejects_unknown_properties(self):
        schema = self._schema("data-asset-record.schema.json")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "datagovops.data-asset-record.v1",
        )


if __name__ == "__main__":
    unittest.main()
