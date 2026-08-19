from dataclasses import replace
import unittest

import test_reporting as reporting_test_module
from datagovops import (
    GovernanceDossierBuilder,
    ReportingAssessmentState,
    ReportingFindingSeverity,
    ReportingRemediationEvidence,
    ReportingRetestEvidence,
    ReportingRetestOutcome,
    dossier_document,
    verify_dossier_document,
)


class ReportingHistoricalClosureTests(unittest.TestCase):
    def test_closed_finding_remains_historical_when_source_later_changes(self):
        (
            assets,
            semantic,
            lineage,
            quality,
            controls,
            reporting,
            asset,
            report,
            _,
        ) = reporting_test_module.ReportingTests()._stack()
        helper = reporting_test_module.ReportingTests()
        helper._observation(
            reporting,
            report,
            observation_id="breach-historical",
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
            finding_id="historical-closed-finding",
            severity=ReportingFindingSeverity.HIGH,
            owner_id="owner",
            title="Historical reporting breach",
            identified_at="2026-08-19T08:06:00Z",
            evidence_digest=reporting_test_module.D1,
        )
        remediation = ReportingRemediationEvidence(
            institution_id="bank-a",
            remediation_id="historical-remediation",
            finding_digest=finding.artifact_digest,
            owner_id="remediator",
            summary="Historical remediation completed.",
            completed_at="2026-08-19T08:07:00Z",
            evidence_digest=reporting_test_module.D2,
        )
        reporting.register_remediation(remediation)
        helper._observation(
            reporting,
            report,
            observation_id="healthy-historical",
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
        self.assertEqual(reassessment.state, ReportingAssessmentState.MET)
        retest = ReportingRetestEvidence(
            institution_id="bank-a",
            retest_id="historical-retest",
            finding_digest=finding.artifact_digest,
            remediation_digest=remediation.artifact_digest,
            reassessment_digest=reassessment.artifact_digest,
            reviewer_id="reviewer",
            outcome=ReportingRetestOutcome.PASSED,
            tested_at="2026-08-19T08:09:00Z",
            evidence_digest=reporting_test_module.D3,
        )
        reporting.register_retest(retest)
        self.assertEqual(
            reporting.resolve_finding(
                finding,
                resolved_at="2026-08-19T08:10:00Z",
            ).status.value,
            "closed",
        )

        assets.register_asset(
            replace(
                asset,
                asset_version=2,
                name="Risk Exposure v2",
                registered_at="2026-08-19T09:10:00Z",
            )
        )
        dossier = GovernanceDossierBuilder(
            assets,
            semantic,
            lineage,
            quality,
            controls,
            reporting_registry=reporting,
        ).build(
            "bank-a",
            generated_at="2026-08-19T09:11:00Z",
            source_revision="historical-closure-after-source-change",
        )
        self.assertEqual(dossier.state.value, "revalidation_required")
        self.assertTrue(
            any(
                item.startswith("reporting:metric:capital-risk:total-exposure:report metric source asset is stale")
                for item in dossier.revalidation_findings
            )
        )
        self.assertFalse(
            any(
                item.startswith("reporting:finding:historical-closed-finding:")
                or item.startswith("reporting:finding_open:historical-closed-finding:")
                for item in dossier.findings
            )
        )
        verify_dossier_document(dossier_document(dossier))


if __name__ == "__main__":
    unittest.main()
