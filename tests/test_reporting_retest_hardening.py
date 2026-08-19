import unittest

import test_reporting as reporting_test_module
from datagovops import (
    GovernanceError,
    ReportingAssessmentState,
    ReportingFindingSeverity,
    ReportingRemediationEvidence,
    ReportingRetestEvidence,
    ReportingRetestOutcome,
)


class ReportingRetestHardeningTests(unittest.TestCase):
    def _breached_finding_and_remediation(self):
        *_, reporting, _, report, _ = reporting_test_module.ReportingTests()._stack()
        reporting_test_module.ReportingTests()._observation(
            reporting,
            report,
            observation_id="breach",
            period_id="2026-07",
            produced_at="2026-08-19T08:03:00Z",
            actual=90,
            reconciliation=80,
            recorded_at="2026-08-19T08:04:00Z",
        )
        breached = reporting.evaluate_report(
            report,
            "2026-07",
            assessed_at="2026-08-19T08:05:00Z",
        )
        finding = reporting.create_finding(
            breached,
            finding_id="finding-retest-hardening",
            severity=ReportingFindingSeverity.HIGH,
            owner_id="owner",
            title="Reporting control breach",
            identified_at="2026-08-19T08:06:00Z",
            evidence_digest=reporting_test_module.D1,
        )
        remediation = ReportingRemediationEvidence(
            institution_id="bank-a",
            remediation_id="remediation-retest-hardening",
            finding_digest=finding.artifact_digest,
            owner_id="remediator",
            summary="Represented remediation completed.",
            completed_at="2026-08-19T08:07:00Z",
            evidence_digest=reporting_test_module.D2,
        )
        reporting.register_remediation(remediation)
        return reporting, report, finding, remediation

    def test_passed_retest_cannot_bind_breached_post_remediation_reassessment(self):
        reporting, report, finding, remediation = self._breached_finding_and_remediation()
        still_breached = reporting.evaluate_report(
            report,
            "2026-07",
            assessed_at="2026-08-19T08:07:30Z",
        )
        self.assertEqual(still_breached.state, ReportingAssessmentState.BREACHED)
        with self.assertRaisesRegex(GovernanceError, "outcome must match"):
            reporting.register_retest(
                ReportingRetestEvidence(
                    institution_id="bank-a",
                    retest_id="forged-pass",
                    finding_digest=finding.artifact_digest,
                    remediation_digest=remediation.artifact_digest,
                    reassessment_digest=still_breached.artifact_digest,
                    reviewer_id="reviewer",
                    outcome=ReportingRetestOutcome.PASSED,
                    tested_at="2026-08-19T08:08:00Z",
                    evidence_digest=reporting_test_module.D3,
                )
            )

    def test_resolution_cannot_predate_retest_lifecycle(self):
        reporting, report, finding, remediation = self._breached_finding_and_remediation()
        reporting_test_module.ReportingTests()._observation(
            reporting,
            report,
            observation_id="healthy-after-remediation",
            period_id="2026-07",
            produced_at="2026-08-19T08:00:30Z",
            actual=100,
            reconciliation=10,
            recorded_at="2026-08-19T08:08:00Z",
        )
        reassessment = reporting.evaluate_report(
            report,
            "2026-07",
            assessed_at="2026-08-19T08:08:30Z",
        )
        retest = ReportingRetestEvidence(
            institution_id="bank-a",
            retest_id="valid-retest",
            finding_digest=finding.artifact_digest,
            remediation_digest=remediation.artifact_digest,
            reassessment_digest=reassessment.artifact_digest,
            reviewer_id="reviewer",
            outcome=ReportingRetestOutcome.PASSED,
            tested_at="2026-08-19T08:09:00Z",
            evidence_digest=reporting_test_module.D4,
        )
        reporting.register_retest(retest)
        with self.assertRaisesRegex(GovernanceError, "cannot predate lifecycle evidence"):
            reporting.resolve_finding(
                finding,
                resolved_at="2026-08-19T08:08:59Z",
            )


if __name__ == "__main__":
    unittest.main()
