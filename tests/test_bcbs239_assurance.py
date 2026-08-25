import unittest

from datagovops import (
    AggregationAssessmentState,
    AggregationLevel,
    AttestationDecision,
    AuthoritativeSystem,
    BCBS239AssuranceRegistry,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    ExecutiveAssuranceAttestation,
    GovernanceError,
    GovernancePrincipal,
    GovernedReport,
    LineageRegistry,
    PrincipalType,
    QualityRegistry,
    ReportFamily,
    ReportMetricDefinition,
    ReportOwnerAttestation,
    ReportProductionObservation,
    ReportSourceRef,
    ReportTaxonomyEntry,
    ReportingGovernanceRegistry,
    RiskDataDomain,
    RiskDataPortfolio,
    SemanticGovernanceRegistry,
    TransformationRecord,
)

D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64
D5 = "5" * 64


class BCBS239AssuranceTests(unittest.TestCase):
    def _stack(self):
        assets = DataAssetRegistry()
        for principal_id in ("report-owner-a", "report-owner-b", "metric-owner", "portfolio-owner"):
            assets.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-25T07:00:00Z",
                )
            )
        assets.register_system(
            AuthoritativeSystem(
                institution_id="bank-a",
                system_id="risk-core",
                name="Risk Core",
                owner_id="portfolio-owner",
                system_type="risk-data-platform",
                authoritative=True,
                registered_at="2026-08-25T07:01:00Z",
            )
        )
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="risk-exposure",
            asset_version=1,
            name="Risk Exposure",
            data_domain="risk",
            owner_id="portfolio-owner",
            steward_id="portfolio-owner",
            system_of_record_id="risk-core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="portfolio-owner",
            classification_rationale="Institution-owned regulated risk data classification.",
            criticality=DataCriticality.CRITICAL,
            criticality_decision_owner_id="portfolio-owner",
            criticality_rationale="Supports material risk aggregation and reporting.",
            contains_personal_data=False,
            source_of_truth=True,
            retention_policy_id="ret-risk",
            quality_owner_id="portfolio-owner",
            registered_at="2026-08-25T07:02:00Z",
        )
        assets.register_asset(asset)
        semantic = SemanticGovernanceRegistry(assets)
        lineage = LineageRegistry(assets, semantic)
        transformation = TransformationRecord(
            institution_id="bank-a",
            transformation_id="aggregate-risk",
            transformation_version=1,
            name="Aggregate governed risk exposure",
            owner_id="metric-owner",
            execution_system_id="risk-core",
            code_digest=D1,
            config_digest=D2,
            evidence_digest=D3,
            registered_at="2026-08-25T07:03:00Z",
        )
        lineage.register_transformation(transformation)
        quality = QualityRegistry(assets, semantic)
        reporting = ReportingGovernanceRegistry(assets, lineage, quality)
        assurance = BCBS239AssuranceRegistry(reporting)
        return assets, reporting, assurance, asset, transformation

    def _register_report(self, reporting, asset, transformation, *, report_id, owner_id, family):
        report = GovernedReport(
            institution_id="bank-a",
            report_id=report_id,
            report_version=1,
            name=f"{report_id} report",
            owner_id=owner_id,
            family=family,
            reporting_purpose="Institution-owned risk-data aggregation and reporting evidence.",
            frequency="monthly",
            maximum_lateness_seconds=60,
            minimum_completeness_basis_points=9900,
            maximum_reconciliation_variance_basis_points=20,
            registered_at="2026-08-25T07:04:00Z",
        )
        reporting.register_report(report)
        metric = ReportMetricDefinition(
            institution_id="bank-a",
            metric_id=f"{report_id}-exposure",
            metric_version=1,
            report_digest=report.artifact_digest,
            name=f"{report_id} exposure",
            owner_id="metric-owner",
            source_refs=(
                ReportSourceRef(
                    institution_id="bank-a",
                    asset_id=asset.asset_id,
                    asset_version=asset.asset_version,
                    asset_digest=asset.artifact_digest,
                ),
            ),
            transformation_digests=(transformation.artifact_digest,),
            quality_rule_digests=(),
            calculation_description="Aggregate exact governed source exposure.",
            registered_at="2026-08-25T07:05:00Z",
        )
        reporting.register_metric(metric)
        return report

    def _assess_and_attest(
        self,
        reporting,
        report,
        *,
        period_id="2026-08",
        actual=100,
        reconciliation=10,
        decision=AttestationDecision.APPROVED,
        suffix="a",
    ):
        observation = ReportProductionObservation(
            institution_id="bank-a",
            observation_id=f"obs-{report.report_id}-{suffix}",
            report_digest=report.artifact_digest,
            period_id=period_id,
            reporting_basis_digest=reporting.reporting_basis_digest(report),
            due_at="2026-08-25T08:00:00Z",
            produced_at="2026-08-25T08:00:30Z",
            expected_record_count=100,
            actual_record_count=actual,
            reconciliation_variance_basis_points=reconciliation,
            source_system_id="risk-core",
            evidence_digest=D4,
            recorded_at="2026-08-25T08:01:00Z",
        )
        reporting.register_observation(observation)
        assessment = reporting.evaluate_report(
            report,
            period_id,
            assessed_at="2026-08-25T08:02:00Z",
        )
        attestation = ReportOwnerAttestation(
            institution_id="bank-a",
            attestation_id=f"att-{report.report_id}-{suffix}",
            assessment_digest=assessment.artifact_digest,
            owner_id=report.owner_id,
            decision=decision,
            rationale="Accountable report-owner review of represented control evidence.",
            attested_at="2026-08-25T08:03:00Z",
            evidence_digest=D5,
        )
        reporting.register_attestation(attestation)
        return assessment, attestation

    def _portfolio(self, assurance, reports):
        entries = []
        domains = (RiskDataDomain.CREDIT, RiskDataDomain.LIQUIDITY)
        for index, (report, domain) in enumerate(zip(reports, domains), start=1):
            entry = ReportTaxonomyEntry(
                institution_id="bank-a",
                taxonomy_id=f"taxonomy-{index}",
                taxonomy_version=1,
                report_digest=report.artifact_digest,
                risk_domain=domain,
                aggregation_level=AggregationLevel.ENTITY,
                material=True,
                owner_id="portfolio-owner",
                rationale="Institution-owned BCBS 239 assurance taxonomy.",
                registered_at="2026-08-25T08:04:00Z",
            )
            assurance.register_taxonomy(entry)
            entries.append(entry)
        portfolio = RiskDataPortfolio(
            institution_id="bank-a",
            portfolio_id="enterprise-risk",
            portfolio_version=1,
            name="Enterprise Risk Data Portfolio",
            owner_id="portfolio-owner",
            report_digests=tuple(report.artifact_digest for report in reports),
            taxonomy_digests=tuple(item.artifact_digest for item in entries),
            required_risk_domains=domains,
            registered_at="2026-08-25T08:05:00Z",
        )
        assurance.register_portfolio(portfolio)
        return portfolio, entries

    def test_multi_report_met_assurance_and_executive_attestation(self):
        _, reporting, assurance, asset, transformation = self._stack()
        report_a = self._register_report(reporting, asset, transformation, report_id="credit-risk", owner_id="report-owner-a", family=ReportFamily.RISK)
        report_b = self._register_report(reporting, asset, transformation, report_id="liquidity-risk", owner_id="report-owner-b", family=ReportFamily.REGULATORY)
        self._assess_and_attest(reporting, report_a, suffix="a")
        self._assess_and_attest(reporting, report_b, suffix="b")
        portfolio, _ = self._portfolio(assurance, (report_a, report_b))

        assessment = assurance.evaluate_portfolio(portfolio, "2026-08", assessed_at="2026-08-25T08:06:00Z")
        self.assertEqual(assessment.state, AggregationAssessmentState.MET)
        self.assertEqual(assessment.met_report_count, 2)
        self.assertEqual(assessment.gaps, ())
        self.assertFalse(assessment.bcbs239_compliance_determined)
        self.assertFalse(assessment.risk_data_accuracy_determined)
        self.assertFalse(assessment.supervisory_acceptance_determined)

        executive = ExecutiveAssuranceAttestation(
            institution_id="bank-a",
            attestation_id="exec-1",
            aggregation_assessment_digest=assessment.artifact_digest,
            owner_id="portfolio-owner",
            decision=AttestationDecision.APPROVED,
            rationale="Portfolio owner accepts the represented assurance evidence.",
            evidence_digest=D5,
            attested_at="2026-08-25T08:07:00Z",
        )
        assurance.register_executive_attestation(executive)
        self.assertEqual(len(assurance.snapshot_digest("bank-a")), 64)

    def test_missing_owner_attestation_fails_closed_to_incomplete(self):
        _, reporting, assurance, asset, transformation = self._stack()
        report_a = self._register_report(reporting, asset, transformation, report_id="credit-risk", owner_id="report-owner-a", family=ReportFamily.RISK)
        report_b = self._register_report(reporting, asset, transformation, report_id="liquidity-risk", owner_id="report-owner-b", family=ReportFamily.RISK)
        self._assess_and_attest(reporting, report_a, suffix="a")
        observation = ReportProductionObservation(
            institution_id="bank-a",
            observation_id="obs-liquidity-unattested",
            report_digest=report_b.artifact_digest,
            period_id="2026-08",
            reporting_basis_digest=reporting.reporting_basis_digest(report_b),
            due_at="2026-08-25T08:00:00Z",
            produced_at="2026-08-25T08:00:30Z",
            expected_record_count=100,
            actual_record_count=100,
            reconciliation_variance_basis_points=10,
            source_system_id="risk-core",
            evidence_digest=D4,
            recorded_at="2026-08-25T08:01:00Z",
        )
        reporting.register_observation(observation)
        reporting.evaluate_report(report_b, "2026-08", assessed_at="2026-08-25T08:02:00Z")
        portfolio, _ = self._portfolio(assurance, (report_a, report_b))

        assessment = assurance.evaluate_portfolio(portfolio, "2026-08", assessed_at="2026-08-25T08:06:00Z")
        self.assertEqual(assessment.state, AggregationAssessmentState.INCOMPLETE)
        self.assertEqual(assessment.missing_attestation_count, 1)
        self.assertIn("owner_attestation_missing:liquidity-risk", assessment.gaps)

        with self.assertRaisesRegex(GovernanceError, "non-met aggregation assessment cannot be approved"):
            assurance.register_executive_attestation(
                ExecutiveAssuranceAttestation(
                    institution_id="bank-a",
                    attestation_id="exec-invalid",
                    aggregation_assessment_digest=assessment.artifact_digest,
                    owner_id="portfolio-owner",
                    decision=AttestationDecision.APPROVED,
                    rationale="Must fail closed.",
                    evidence_digest=D5,
                    attested_at="2026-08-25T08:07:00Z",
                )
            )

    def test_breached_report_and_rejected_attestation_propagate(self):
        _, reporting, assurance, asset, transformation = self._stack()
        report_a = self._register_report(reporting, asset, transformation, report_id="credit-risk", owner_id="report-owner-a", family=ReportFamily.RISK)
        report_b = self._register_report(reporting, asset, transformation, report_id="liquidity-risk", owner_id="report-owner-b", family=ReportFamily.RISK)
        self._assess_and_attest(reporting, report_a, suffix="a")
        self._assess_and_attest(reporting, report_b, actual=90, reconciliation=80, decision=AttestationDecision.REJECTED, suffix="b")
        portfolio, _ = self._portfolio(assurance, (report_a, report_b))
        assessment = assurance.evaluate_portfolio(portfolio, "2026-08", assessed_at="2026-08-25T08:06:00Z")
        self.assertEqual(assessment.state, AggregationAssessmentState.BREACHED)
        self.assertEqual(assessment.breached_report_count, 1)
        self.assertEqual(assessment.nonapproved_attestation_count, 1)
        self.assertIn("assessment_breached:liquidity-risk", assessment.gaps)
        self.assertIn("owner_attestation_rejected:liquidity-risk", assessment.gaps)

    def test_report_version_change_stales_bound_taxonomy_and_portfolio(self):
        _, reporting, assurance, asset, transformation = self._stack()
        report_a = self._register_report(reporting, asset, transformation, report_id="credit-risk", owner_id="report-owner-a", family=ReportFamily.RISK)
        report_b = self._register_report(reporting, asset, transformation, report_id="liquidity-risk", owner_id="report-owner-b", family=ReportFamily.RISK)
        portfolio, entries = self._portfolio(assurance, (report_a, report_b))
        reporting.register_report(
            GovernedReport(
                institution_id="bank-a",
                report_id=report_a.report_id,
                report_version=2,
                name="credit-risk report v2",
                owner_id="report-owner-a",
                family=ReportFamily.RISK,
                reporting_purpose="Updated institution-owned risk-data reporting evidence.",
                frequency="monthly",
                maximum_lateness_seconds=60,
                minimum_completeness_basis_points=9900,
                maximum_reconciliation_variance_basis_points=20,
                registered_at="2026-08-25T09:00:00Z",
            )
        )
        with self.assertRaisesRegex(GovernanceError, "report definition is stale"):
            assurance.assert_taxonomy_current(entries[0])
        with self.assertRaisesRegex(GovernanceError, "report definition is stale"):
            assurance.assert_portfolio_current(portfolio)

    def test_cross_institution_taxonomy_fails_closed(self):
        assets, reporting, assurance, asset, transformation = self._stack()
        report = self._register_report(reporting, asset, transformation, report_id="credit-risk", owner_id="report-owner-a", family=ReportFamily.RISK)
        assets.register_principal(
            GovernancePrincipal(
                institution_id="bank-b",
                principal_id="owner-b",
                display_name="Owner B",
                principal_type=PrincipalType.HUMAN,
                registered_at="2026-08-25T07:10:00Z",
            )
        )
        with self.assertRaisesRegex(GovernanceError, "different institution"):
            assurance.register_taxonomy(
                ReportTaxonomyEntry(
                    institution_id="bank-b",
                    taxonomy_id="cross-bank",
                    taxonomy_version=1,
                    report_digest=report.artifact_digest,
                    risk_domain=RiskDataDomain.CREDIT,
                    aggregation_level=AggregationLevel.ENTITY,
                    material=True,
                    owner_id="owner-b",
                    rationale="Must not cross institution scope.",
                    registered_at="2026-08-25T08:04:00Z",
                )
            )


if __name__ == "__main__":
    unittest.main()
