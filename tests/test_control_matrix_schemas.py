import hashlib
import json
from pathlib import Path
import unittest

import jsonschema

from datagovops.control_matrix import (
    ControlDefinition,
    ControlDomain,
    ControlEvidenceReference,
    ControlEvidenceRegistry,
    EvidenceRequirement,
    EvidenceSourceBoundary,
    FrameworkReference,
)
from datagovops.models import canonical_json

ROOT = Path(__file__).resolve().parents[1]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ControlEvidenceMatrixSchemaTests(unittest.TestCase):
    def _schema(self, name: str) -> dict:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        self.assertFalse(schema["additionalProperties"])
        return schema

    def _fixtures(self):
        control = ControlDefinition(
            institution_id="bank-a",
            control_id="bcbs-aggregation",
            control_version=1,
            title="BCBS aggregation evidence",
            domain=ControlDomain.BCBS239_ASSURANCE,
            owner_id="owner-1",
            objective="Represent current aggregation-assurance evidence.",
            evidence_requirements=(
                EvidenceRequirement("aggregation_assessment", (EvidenceSourceBoundary.BCBS239,)),
            ),
            framework_references=(
                FrameworkReference(
                    framework="BCBS 239",
                    reference="Principle 6",
                    mapping_rationale="Design mapping only; applicability is not determined.",
                ),
            ),
            registered_at=100,
        )
        reference = ControlEvidenceReference(
            institution_id="bank-a",
            evidence_id="ev-1",
            control_digest=control.artifact_digest,
            evidence_type="aggregation_assessment",
            source_boundary=EvidenceSourceBoundary.BCBS239,
            artifact_type="datagovops.bcbs239-aggregation-assessment.v1",
            source_artifact_digest=digest("artifact"),
            source_snapshot_digest=digest("snapshot"),
            observed_at=120,
            revalidate_after=220,
            verifier_id="validator-1",
            verification_evidence_digest=digest("verification"),
        )
        registry = ControlEvidenceRegistry()
        registry.register_control(control)
        registry.register_evidence(reference)
        assessment = registry.assess_control("bank-a", "bcbs-aggregation", assessed_at=180)
        matrix = registry.build_matrix(
            institution_id="bank-a",
            matrix_id="enterprise-controls",
            matrix_version=1,
            control_ids=("bcbs-aggregation",),
            assessed_at=180,
        )
        return control, reference, assessment, matrix

    def test_reference_documents_validate(self):
        control, reference, assessment, matrix = self._fixtures()
        documents = {
            "control-definition.schema.json": json.loads(canonical_json(control)),
            "control-evidence-reference.schema.json": json.loads(canonical_json(reference)),
            "control-assessment.schema.json": json.loads(canonical_json(assessment)),
            "control-evidence-matrix.schema.json": json.loads(canonical_json(matrix)),
        }
        for name, document in documents.items():
            with self.subTest(name=name):
                jsonschema.Draft202012Validator(self._schema(name)).validate(document)

    def test_matrix_rejects_compliance_score_and_claim_inflation(self):
        _, _, _, matrix = self._fixtures()
        schema = self._schema("control-evidence-matrix.schema.json")
        document = json.loads(canonical_json(matrix))

        with_score = dict(document)
        with_score["compliance_score"] = 100
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(with_score)

        inflated = dict(document)
        inflated["regulatory_compliance_determined"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(inflated)

    def test_framework_reference_rejects_applicability_claim(self):
        control, _, _, _ = self._fixtures()
        schema = self._schema("control-definition.schema.json")
        document = json.loads(canonical_json(control))
        document["framework_references"][0]["applicability_determined"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(document)

    def test_nonclaim_fields_are_structurally_pinned(self):
        control_schema = self._schema("control-definition.schema.json")
        evidence_schema = self._schema("control-evidence-reference.schema.json")
        assessment_schema = self._schema("control-assessment.schema.json")
        matrix_schema = self._schema("control-evidence-matrix.schema.json")

        self.assertFalse(control_schema["properties"]["framework_applicability_determined"]["const"])
        self.assertFalse(control_schema["properties"]["legal_compliance_determined"]["const"])
        self.assertFalse(evidence_schema["properties"]["evidence_effectiveness_determined"]["const"])
        self.assertTrue(assessment_schema["properties"]["requires_human_review"]["const"])
        self.assertFalse(matrix_schema["properties"]["automated_compliance_scoring_enabled"]["const"])
        self.assertFalse(matrix_schema["properties"]["supervisory_acceptance_determined"]["const"])


if __name__ == "__main__":
    unittest.main()
