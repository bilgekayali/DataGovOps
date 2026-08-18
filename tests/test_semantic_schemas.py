import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import (
    AssetPurposeBinding,
    BusinessPurpose,
    ClassificationDecision,
    ClassificationScope,
    CriticalDataElementDesignation,
    DataClassification,
    DataElementRecord,
    canonical_json,
    digest_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


class SemanticSchemaTests(unittest.TestCase):
    def validate(self, schema_name, artifact):
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        document = json.loads(canonical_json(artifact))
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(document)

    def test_semantic_artifacts_validate_release_schemas(self):
        target_digest = digest_artifact({"target": "asset-v1"})
        element = DataElementRecord(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            element_id="available-balance",
            name="Available Balance",
            data_type="decimal(18,2)",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T07:03:00Z",
        )
        classification = ClassificationDecision(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            scope=ClassificationScope.DATA_ELEMENT,
            element_id=element.element_id,
            target_digest=element.artifact_digest,
            classification=DataClassification.CONFIDENTIAL,
            decision_owner_id="class-owner",
            rationale="Explicit semantic classification.",
            evidence_digest=digest_artifact({"evidence": "classification"}),
            decided_at="2026-08-18T07:04:00Z",
        )
        cde = CriticalDataElementDesignation(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            element_id=element.element_id,
            element_digest=element.artifact_digest,
            cde_owner_id="cde-owner",
            decision_owner_id="crit-owner",
            rationale="Material governed element.",
            evidence_digest=digest_artifact({"evidence": "cde"}),
            designated_at="2026-08-18T07:05:00Z",
        )
        purpose = BusinessPurpose(
            institution_id="bank-a",
            purpose_id="customer-servicing",
            purpose_version=1,
            name="Customer servicing",
            description="Serve customer balance enquiries.",
            owner_id="purpose-owner",
            registered_at="2026-08-18T07:06:00Z",
        )
        binding = AssetPurposeBinding(
            institution_id="bank-a",
            binding_id="binding-1",
            asset_id="customer-balance",
            asset_version=1,
            asset_digest=target_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            approval_owner_id="approver",
            rationale="Approved governed use.",
            evidence_digest=digest_artifact({"evidence": "purpose"}),
            bound_at="2026-08-18T07:07:00Z",
        )

        self.validate("data-element-record.schema.json", element)
        self.validate("classification-decision.schema.json", classification)
        self.validate("critical-data-element-designation.schema.json", cde)
        self.validate("business-purpose.schema.json", purpose)
        self.validate("asset-purpose-binding.schema.json", binding)


if __name__ == "__main__":
    unittest.main()
