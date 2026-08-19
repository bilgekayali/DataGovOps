from dataclasses import replace
import unittest

import test_reporting as reporting_test_module
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


class ReportingHardeningTests(unittest.TestCase):
    def test_old_transformation_digest_becomes_stale_after_new_version(self):
        _, _, lineage, _, _, reporting, _, _, metric = reporting_test_module.ReportingTests()._stack()
        lineage.register_transformation(
            TransformationRecord(
                institution_id="bank-a",
                transformation_id="aggregate-risk",
                transformation_version=2,
                name="Aggregate risk exposure v2",
                owner_id="metric-owner",
                execution_system_id="core",
                code_digest=reporting_test_module.D2,
                config_digest=reporting_test_module.D3,
                evidence_digest=reporting_test_module.D1,
                registered_at="2026-08-19T09:00:00Z",
            )
        )
        with self.assertRaisesRegex(GovernanceError, "latest version"):
            reporting.assert_metric_current(metric)

    def test_no_metric_assessment_is_offline_verifiable_incomplete_evidence(self):
        assets, semantic, lineage, quality, controls, reporting, _, _, _ = reporting_test_module.ReportingTests()._stack()
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

    def test_historical_assessment_remains_verifiable_after_source_version_change(self):
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
        reporting_test_module.ReportingTests()._observation(reporting, report)
        historical = reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T08:02:00Z",
        )
        self.assertEqual(historical.state, ReportingAssessmentState.MET)

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
            source_revision="reporting-source-version-change",
        )
        self.assertEqual(dossier.state.value, "revalidation_required")
        self.assertTrue(
            any(
                item.startswith("reporting:metric:capital-risk:total-exposure:report metric source asset is stale")
                for item in dossier.revalidation_findings
            )
        )
        self.assertTrue(
            any(
                item.startswith("reporting:assessment:capital-risk:2026-08:report metric source asset is stale")
                for item in dossier.revalidation_findings
            )
        )
        verify_dossier_document(dossier_document(dossier))


if __name__ == "__main__":
    unittest.main()
