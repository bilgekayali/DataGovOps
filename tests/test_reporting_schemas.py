import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import (
    AttestationDecision,
    GovernedReport,
    ReportAssuranceAssessment,
    ReportFamily,
    ReportMetricDefinition,
    ReportOwnerAttestation,
    ReportProductionObservation,
    ReportSourceRef,
    ReportingAssessmentState,
    ReportingControlAssessment,
    ReportingFinding,
    ReportingFindingSeverity,
    ReportingMetric,
    ReportingMetricState,
    ReportingRemediationEvidence,
    ReportingRetestEvidence,
    ReportingRetestOutcome,
    canonical_json,
)


ROOT = Path(__file__).resolve().parents[1]
D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64


class ReportingSchemaTests(unittest.TestCase):
    def test_runtime_reporting_artifacts_validate_strictly(self):
        schema = json.loads(
            (ROOT / "schemas" / "reporting-governance.schema.json").read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator.check_schema(schema)
        source = ReportSourceRef("bank-a", "asset-1", 1, D1)
        report = GovernedReport(
            institution_id="bank-a",
            report_id="report-1",
            report_version=1,
            name="Risk Report",
            owner_id="owner",
            family=ReportFamily.REGULATORY,
            reporting_purpose="Governed reporting evidence.",
            frequency="monthly",
            maximum_lateness_seconds=60,
            minimum_completeness_basis_points=9900,
            maximum_reconciliation_variance_basis_points=20,
            registered_at="2026-08-19T07:00:00Z",
        )
        metric = ReportMetricDefinition(
            institution_id="bank-a",
            metric_id="metric-1",
            metric_version=1,
            report_digest=report.artifact_digest,
            name="Metric",
            owner_id="owner",
            source_refs=(source,),
            transformation_digests=(D2,),
            quality_rule_digests=(D3,),
            calculation_description="Governed calculation description.",
            registered_at="2026-08-19T07:01:00Z",
        )
        observation = ReportProductionObservation(
            institution_id="bank-a",
            observation_id="obs-1",
            report_digest=report.artifact_digest,
            period_id="2026-08",
            reporting_basis_digest=D4,
            due_at="2026-08-19T08:00:00Z",
            produced_at="2026-08-19T08:00:30Z",
            expected_record_count=100,
            actual_record_count=100,
            reconciliation_variance_basis_points=10,
            source_system_id="core",
            evidence_digest=D1,
            recorded_at="2026-08-19T08:01:00Z",
        )
        controls = (
            ReportingControlAssessment(
                ReportingMetric.COMPLETENESS,
                ReportingMetricState.MET,
                10000,
                9900,
                "configured_control_satisfied",
            ),
            ReportingControlAssessment(
                ReportingMetric.RECONCILIATION,
                ReportingMetricState.MET,
                10,
                20,
                "configured_control_satisfied",
            ),
            ReportingControlAssessment(
                ReportingMetric.TIMELINESS,
                ReportingMetricState.MET,
                30,
                60,
                "configured_control_satisfied",
            ),
        )
        assessment = ReportAssuranceAssessment(
            institution_id="bank-a",
            report_digest=report.artifact_digest,
            period_id="2026-08",
            reporting_basis_digest=D4,
            observation_digest=observation.artifact_digest,
            metric_definition_digests=(metric.artifact_digest,),
            control_assessments=controls,
            state=ReportingAssessmentState.MET,
            gaps=(),
            assessed_at="2026-08-19T08:02:00Z",
        )
        attestation = ReportOwnerAttestation(
            institution_id="bank-a",
            attestation_id="att-1",
            assessment_digest=assessment.artifact_digest,
            owner_id="owner",
            decision=AttestationDecision.APPROVED,
            rationale="Accountable owner reviewed represented evidence.",
            attested_at="2026-08-19T08:03:00Z",
            evidence_digest=D2,
        )
        finding = ReportingFinding(
            institution_id="bank-a",
            finding_id="finding-1",
            assessment_digest=D1,
            severity=ReportingFindingSeverity.HIGH,
            owner_id="owner",
            title="Reporting control finding",
            identified_at="2026-08-19T08:04:00Z",
            evidence_digest=D3,
        )
        remediation = ReportingRemediationEvidence(
            institution_id="bank-a",
            remediation_id="rem-1",
            finding_digest=finding.artifact_digest,
            owner_id="owner",
            summary="Remediation evidence.",
            completed_at="2026-08-19T08:05:00Z",
            evidence_digest=D4,
        )
        retest = ReportingRetestEvidence(
            institution_id="bank-a",
            retest_id="retest-1",
            finding_digest=finding.artifact_digest,
            remediation_digest=remediation.artifact_digest,
            reassessment_digest=assessment.artifact_digest,
            reviewer_id="reviewer",
            outcome=ReportingRetestOutcome.PASSED,
            tested_at="2026-08-19T08:06:00Z",
            evidence_digest=D1,
        )
        for artifact in (
            report,
            metric,
            observation,
            assessment,
            attestation,
            finding,
            remediation,
            retest,
        ):
            with self.subTest(artifact=type(artifact).__name__):
                payload = json.loads(canonical_json(artifact))
                jsonschema.Draft202012Validator(schema).validate(payload)

    def test_reporting_schema_is_fail_closed(self):
        schema = json.loads(
            (ROOT / "schemas" / "reporting-governance.schema.json").read_text(encoding="utf-8")
        )
        for name in ("report", "metric", "observation", "assessment", "attestation", "finding", "remediation", "retest"):
            self.assertFalse(schema["$defs"][name]["additionalProperties"])
        self.assertIn("reassessment_digest", schema["$defs"]["retest"]["required"])
        self.assertFalse(
            schema["$defs"]["assessment"]["properties"]["regulatory_compliance_determined"].get("default", False)
        )
        self.assertEqual(
            schema["$defs"]["assessment"]["properties"]["regulatory_compliance_determined"]["const"],
            False,
        )


if __name__ == "__main__":
    unittest.main()
