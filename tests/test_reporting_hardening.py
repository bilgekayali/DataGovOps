import unittest

from datagovops import (
    GovernedReport,
    GovernanceDossierBuilder,
    GovernanceError,
    ReportFamily,
    ReportingAssessmentState,
    TransformationRecord,
    dossier_document,
    verify_dossier_document,
)
from test_reporting import D1, D2, D3, ReportingTests


class ReportingHardeningTests(unittest.TestCase):
    def test_old_transformation_digest_becomes_stale_after_new_version(self):
        _, _, lineage, _, _, reporting, _, _, metric = ReportingTests()._stack()
        lineage.register_transformation(
            TransformationRecord(
                institution_id="bank-a",
                transformation_id="aggregate-risk",
                transformation_version=2,
                name="Aggregate risk exposure v2",
                owner_id="metric-owner",
                execution_system_id="core",
                code_digest=D2,
                config_digest=D3,
                evidence_digest=D1,
                registered_at="2026-08-19T09:00:00Z",
            )
        )
        with self.assertRaisesRegex(GovernanceError, "latest version"):
            reporting.assert_metric_current(metric)

    def test_no_metric_assessment_is_offline_verifiable_incomplete_evidence(self):
        assets, semantic, lineage, quality, controls, reporting, _, _, _ = ReportingTests()._stack()
        report = GovernedReport(
            institution_id="bank-a",
            report_id="empty-report",
            report_version=1,
            name="Empty Metric Report",
            owner_id="owner",
            family=ReportFamily.MANAGEMENT,
            reporting_purpose="Exercise explicit missing metric evidence.",
            frequency="monthly",
            maximum_lateness_seconds=60,
            minimum_completeness_basis_points=9900,
            maximum_reconciliation_variance_basis_points=20,
            registered_at="2026-08-19T09:01:00Z",
        )
        reporting.register_report(report)
        assessment = reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T09:02:00Z",
        )
        self.assertEqual(assessment.state, ReportingAssessmentState.INCOMPLETE)
        self.assertEqual(assessment.gaps, ("metric_definition_missing",))
        dossier = GovernanceDossierBuilder(
            assets,
            semantic,
            lineage,
            quality,
            controls,
            reporting_registry=reporting,
        ).build(
            "bank-a",
            generated_at="2026-08-19T09:03:00Z",
            source_revision="reporting-no-metric-hardening",
        )
        self.assertIn("reporting:no_metric_definitions:empty-report", dossier.findings)
        verify_dossier_document(dossier_document(dossier))


if __name__ == "__main__":
    unittest.main()
