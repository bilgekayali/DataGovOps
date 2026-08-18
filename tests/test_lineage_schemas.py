import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import (
    LineageCompletenessReport,
    LineageCompletenessRequirement,
    LineageEdge,
    LineageEndpointKind,
    LineageEndpointRef,
    LineageRelationship,
    TransformationRecord,
    canonical_json,
    digest_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


class LineageSchemaTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def schema(self, name):
        value = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(value)
        self.assertFalse(value["additionalProperties"])
        return value

    def test_runtime_lineage_artifacts_validate_against_release_schemas(self):
        source = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.DATA_ELEMENT,
            asset_id="source",
            asset_version=1,
            element_id="amount",
            target_digest=self.evidence("source-element"),
        )
        target = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.ASSET,
            asset_id="target",
            asset_version=1,
            element_id=None,
            target_digest=self.evidence("target-asset"),
        )
        transformation = TransformationRecord(
            institution_id="bank-a",
            transformation_id="t1",
            transformation_version=1,
            name="Transform",
            owner_id="owner",
            execution_system_id="etl",
            code_digest=self.evidence("code"),
            config_digest=self.evidence("config"),
            evidence_digest=self.evidence("transformation"),
            registered_at="2026-08-18T08:10:00Z",
        )
        edge = LineageEdge(
            institution_id="bank-a",
            edge_id="e1",
            source=source,
            target=target,
            relationship=LineageRelationship.TRANSFORMED_FROM,
            transformation_id="t1",
            transformation_version=1,
            transformation_digest=transformation.artifact_digest,
            producer_system_id="source-system",
            consumer_system_id="target-system",
            evidence_digest=self.evidence("edge"),
            recorded_at="2026-08-18T08:11:00Z",
        )
        requirement = LineageCompletenessRequirement(
            institution_id="bank-a",
            requirement_id="r1",
            target=target,
            owner_id="lineage-owner",
            rationale="Target requires explicit upstream lineage.",
            evidence_digest=self.evidence("requirement"),
            registered_at="2026-08-18T08:12:00Z",
        )
        report = LineageCompletenessReport(
            institution_id="bank-a",
            lineage_snapshot_digest=self.evidence("snapshot"),
            requirement_digests=(requirement.artifact_digest,),
            missing_requirement_ids=(),
            stale_requirement_ids=(),
            complete=True,
            evaluated_at="2026-08-18T08:13:00Z",
        )
        fixtures = {
            "lineage-endpoint-ref.schema.json": source,
            "transformation-record.schema.json": transformation,
            "lineage-edge.schema.json": edge,
            "lineage-completeness-requirement.schema.json": requirement,
            "lineage-completeness-report.schema.json": report,
        }
        for name, artifact in fixtures.items():
            with self.subTest(schema=name):
                payload = json.loads(canonical_json(artifact))
                jsonschema.Draft202012Validator(self.schema(name)).validate(payload)

    def test_endpoint_schema_enforces_kind_element_consistency(self):
        schema = self.schema("lineage-endpoint-ref.schema.json")
        invalid = {
            "institution_id": "bank-a",
            "kind": "asset",
            "asset_id": "a",
            "asset_version": 1,
            "element_id": "should-not-exist",
            "target_digest": "a" * 64,
            "schema_version": "datagovops.lineage-endpoint-ref.v1",
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(invalid)


if __name__ == "__main__":
    unittest.main()
