import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import (
    ComparisonOperator,
    EvidenceTreatment,
    FindingResolutionState,
    FindingSeverity,
    QualityDimension,
    QualityEvaluationPolicy,
    QualityEvaluationState,
    QualityFinding,
    QualityFindingResolution,
    QualityObservation,
    QualityRemediationEvidence,
    QualityRetestEvidence,
    QualityRule,
    QualityRuleEvaluation,
    QualityTargetKind,
    QualityTargetRef,
    RetestOutcome,
    canonical_json,
)

ROOT = Path(__file__).resolve().parents[1]
D = "a" * 64
E = "b" * 64
F = "c" * 64


class QualitySchemaTests(unittest.TestCase):
    def schema(self, name):
        value = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(value)
        self.assertFalse(value["additionalProperties"])
        return value

    def test_runtime_quality_artifacts_validate_release_schemas(self):
        target = QualityTargetRef(
            institution_id="bank-a", kind=QualityTargetKind.CRITICAL_DATA_ELEMENT,
            asset_id="balance", asset_version=1, element_id="available", target_digest=D,
        )
        rule = QualityRule(
            institution_id="bank-a", rule_id="q1", rule_version=1, target=target,
            dimension=QualityDimension.COMPLETENESS, owner_id="owner", metric_name="coverage",
            measurement_unit="basis_points", comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=9900, max_age_seconds=3600, finding_severity=FindingSeverity.HIGH,
            evidence_digest=E, registered_at="2026-08-18T08:00:00Z",
        )
        policy = QualityEvaluationPolicy(
            institution_id="bank-a", policy_id="p", policy_version=1, owner_id="owner",
            missing_observation_treatment=EvidenceTreatment.INCOMPLETE,
            stale_observation_treatment=EvidenceTreatment.BREACH,
            freshness_grace_seconds=0, evidence_digest=E, registered_at="2026-08-18T08:00:00Z",
        )
        observation = QualityObservation(
            institution_id="bank-a", observation_id="o", rule_id="q1", rule_version=1,
            rule_digest=D, target_digest=D, observed_value=9800, source_system_id="quality",
            measured_at="2026-08-18T08:01:00Z", recorded_at="2026-08-18T08:02:00Z",
            evidence_digest=E,
        )
        evaluation = QualityRuleEvaluation(
            institution_id="bank-a", rule_id="q1", rule_version=1, rule_digest=D,
            target_digest=D, policy_digest=E, observation_digest=F,
            state=QualityEvaluationState.BREACHED, reason_code="threshold_breached",
            evaluated_at="2026-08-18T08:03:00Z",
        )
        finding = QualityFinding(
            institution_id="bank-a", finding_id="f", evaluation_digest=D, rule_digest=E,
            severity=FindingSeverity.HIGH, owner_id="owner", title="Quality breach",
            identified_at="2026-08-18T08:04:00Z", evidence_digest=F,
        )
        remediation = QualityRemediationEvidence(
            institution_id="bank-a", remediation_id="r", finding_digest=D, owner_id="owner",
            summary="Remediated source processing.", completed_at="2026-08-18T08:05:00Z",
            evidence_digest=E,
        )
        retest = QualityRetestEvidence(
            institution_id="bank-a", retest_id="rt", finding_digest=D,
            remediation_digest=E, evaluation_digest=F, reviewer_id="reviewer",
            outcome=RetestOutcome.PASSED, retested_at="2026-08-18T08:06:00Z",
            evidence_digest=D,
        )
        resolution = QualityFindingResolution(
            institution_id="bank-a", finding_digest=D, state=FindingResolutionState.CLOSED,
            remediation_digest=E, retest_digest=F, evidence_history_digests=(D, E),
            resolved_at="2026-08-18T08:07:00Z",
        )
        fixtures = {
            "quality-target-ref.schema.json": target,
            "quality-rule.schema.json": rule,
            "quality-evaluation-policy.schema.json": policy,
            "quality-observation.schema.json": observation,
            "quality-rule-evaluation.schema.json": evaluation,
            "quality-finding.schema.json": finding,
            "quality-remediation-evidence.schema.json": remediation,
            "quality-retest-evidence.schema.json": retest,
            "quality-finding-resolution.schema.json": resolution,
        }
        for name, artifact in fixtures.items():
            with self.subTest(schema=name):
                jsonschema.Draft202012Validator(self.schema(name)).validate(
                    json.loads(canonical_json(artifact))
                )

    def test_quality_target_schema_enforces_cde_element_identity(self):
        schema = self.schema("quality-target-ref.schema.json")
        payload = {
            "institution_id":"bank-a","kind":"critical_data_element","asset_id":"a",
            "asset_version":1,"element_id":None,"target_digest":D,
            "schema_version":"datagovops.quality-target-ref.v1",
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(payload)


if __name__ == "__main__":
    unittest.main()
