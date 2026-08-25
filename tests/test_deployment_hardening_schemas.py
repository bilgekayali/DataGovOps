from dataclasses import asdict
from enum import Enum
import json
from pathlib import Path
import unittest

import jsonschema

from datagovops.deployment_hardening import (
    DeploymentEvidence,
    ImmutableImageReference,
    NetworkBoundary,
    RuntimeObservation,
    RuntimeSecurityProfile,
    SecretInjectionReference,
    assess_deployment,
    deployment_evidence_document,
)

ROOT = Path(__file__).resolve().parents[1]


def _plain(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    return value


class DeploymentHardeningSchemaTests(unittest.TestCase):
    def _schema(self, name):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        self.assertFalse(schema["additionalProperties"])
        return schema

    def _evidence(self):
        return DeploymentEvidence(
            institution_id="bank-a",
            environment_id="reference",
            workload_id="datagovops",
            image=ImmutableImageReference("registry.example/datagovops", "a" * 64),
            runtime_security=RuntimeSecurityProfile(True, True, False, False, True, True, False, False, False, False),
            network_boundary=NetworkBoundary(True, True, ()),
            secret_references=(SecretInjectionReference("vault", "db", "1"),),
            manifest_sha256="b" * 64,
            validator_id="validator",
            observed_at=10,
            negative_path_confirmed=True,
        )

    def test_reference_documents_validate(self):
        evidence = self._evidence()
        observation = RuntimeObservation(
            institution_id="bank-a", environment_id="reference", workload_id="datagovops",
            observation_type="health", status="represented", evidence_sha256="c" * 64, observed_at=10,
        )
        assessment = assess_deployment(evidence, assessed_at=11)
        fixtures = {
            "image-reference.schema.json": deployment_evidence_document(evidence)["image"],
            "deployment-evidence.schema.json": deployment_evidence_document(evidence),
            "runtime-observation.schema.json": _plain(asdict(observation)),
            "deployment-assessment.schema.json": _plain(asdict(assessment)),
        }
        for name, document in fixtures.items():
            with self.subTest(name=name):
                self._schema(name)
                jsonschema.Draft202012Validator(self._schema(name)).validate(document)

    def test_secret_value_inflation_is_rejected(self):
        evidence = deployment_evidence_document(self._evidence())
        evidence["secret_references"][0]["value"] = "should-never-appear"
        schema = self._schema("deployment-evidence.schema.json")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(evidence)

    def test_assessment_claim_inflation_is_rejected(self):
        assessment = _plain(asdict(assess_deployment(self._evidence(), assessed_at=11)))
        assessment["production_effectiveness_determined"] = True
        schema = self._schema("deployment-assessment.schema.json")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(assessment)


if __name__ == "__main__":
    unittest.main()
