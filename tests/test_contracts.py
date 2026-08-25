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
    def test_version_is_v1_0_0_at_stable_gate(self):
        self.assertEqual(datagovops.__version__, "1.0.0")
        self.assertEqual(datagovops.RELEASE_VERSION, "1.0.0")

    def test_release_contract_preserves_v09_freeze_at_stable_promotion(self):
        contract = json.loads((ROOT / "release" / "release-contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["candidate_version"], "0.9.0")
        self.assertEqual(contract["target_stable_version"], "1.0.0")
        self.assertEqual(contract["current_release_version"], "1.0.0")
        self.assertEqual(contract["release_stage"], "stable")
        self.assertTrue(contract["requires_human_release_decision"])
        self.assertFalse(contract["repository_governance_enforcement_verified"])

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

    def test_governance_dossier_schema_remains_package_decoupled_after_freeze(self):
        schema = self._schema("governance-dossier.schema.json")
        release_property = schema["$defs"]["dossier"]["properties"]["release_version"]
        self.assertNotIn("const", release_property)
        self.assertEqual(release_property["pattern"], r"^[0-9]+\.[0-9]+\.[0-9]+$")


if __name__ == "__main__":
    unittest.main()
