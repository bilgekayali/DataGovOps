import copy
import unittest

from datagovops import (
    AccessRetentionPrivacyRegistry,
    AttestationDecision,
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    GovernanceDossierBuilder,
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
    ReportingAssessmentState,
    ReportingFindingSeverity,
    ReportingGovernanceRegistry,
    ReportingRemediationEvidence,
    ReportingRetestEvidence,
    ReportingRetestOutcome,
    SemanticGovernanceRegistry,
    TransformationRecord,
    dossier_document,
    digest_artifact,
    verify_dossier_document,
)
from datagovops.dossier_verify_v02 import _reporting_snapshot


D1 = "1" * 64
D2 = "2" * 64
D3 = "3" * 64
D4 = "4" * 64


class ReportingTests(unittest.TestCase):
    def _stack(self):
        assets = DataAssetRegistry()
        for principal_id in ("owner", "metric-owner", "remediator", "reviewer"):
            assets.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-19T07:00:00Z",
                )
            )
        assets.register_system(
            AuthoritativeSystem(
                institution_id="bank-a",
                system_id="core",
                name="Core Banking",
                owner_id="owner",
                system_type="core-banking",
                authoritative=True,
                registered_at="2026-08-19T07:01:00Z",
            )
        )
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="risk-exposure",
            asset_version=1,
            name="Risk Exposure",
            data_domain="risk",
            owner_id="owner",
            steward_id="owner",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="owner",
            classification_rationale="Regulated risk data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="owner",
            criticality_rationale="Supports material reporting.",
            contains_personal_data=False,
            source_of_truth=True,
            retention_policy_id="ret-1",
            quality_owner_id="owner",
            registered_at="2026-08-19T07:02:00Z",
        )
        assets.register_asset(asset)
        semantic = SemanticGovernanceRegistry(assets)
        lineage = LineageRegistry(assets, semantic)
        transformation = TransformationRecord(
            institution_id="bank-a",
            transformation_id="aggregate-risk",
            transformation_version=1,
            name="Aggregate risk exposure",
            owner_id="metric-owner",
            execution_system_id="core",
            code_digest=D1,
            config_digest=D2,
            evidence_digest=D3,
            registered_at="2026-08-19T07:03:00Z",
        )
        lineage.register_transformation(transformation)
        quality = QualityRegistry(assets, semantic)
        controls = AccessRetentionPrivacyRegistry(assets, semantic)
        reporting = ReportingGovernanceRegistry(assets, lineage, quality)
        report = GovernedReport(
            institution_id="bank-a",
            report_id="capital-risk",
            report_version=1,
            name="Capital Risk Report",
            owner_id="owner",
            family=ReportFamily.REGULATORY,
            reporting_purpose="Institution-owned capital-risk reporting control evidence.",
            frequency="monthly",
            maximum_lateness_seconds=60,
            minimum_completeness_basis_points=9900,
            maximum_reconciliation_variance_basis_points=20,
            registered_at="2026-08-19T07:04:00Z",
        )
        reporting.register_report(report)
        metric = ReportMetricDefinition(
            institution_id="bank-a",
            metric_id="total-exposure",
            metric_version=1,
            report_digest=report.artifact_digest,
            name="Total Exposure",
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
            calculation_description="Aggregate governed source exposure for the represented report metric.",
            registered_at="2026-08-19T07:05:00Z",
        )
        reporting.register_metric(metric)
        return assets, semantic, lineage, quality, controls, reporting, asset, report, metric

    def _observation(
        self,
        reporting,
        report,
        *,
        observation_id="obs-1",
        period_id="2026-08",
        produced_at="2026-08-19T08:00:30Z",
        actual=100,
        reconciliation=10,
        recorded_at="2026-08-19T08:01:00Z",
    ):
        observation = ReportProductionObservation(
            institution_id="bank-a",
            observation_id=observation_id,
            report_digest=report.artifact_digest,
            period_id=period_id,
            reporting_basis_digest=reporting.reporting_basis_digest(report),
            due_at="2026-08-19T08:00:00Z",
            produced_at=produced_at,
            expected_record_count=100,
            actual_record_count=actual,
            reconciliation_variance_basis_points=reconciliation,
            source_system_id="core",
            evidence_digest=D4,
            recorded_at=recorded_at,
        )
        reporting.register_observation(observation)
        return observation

    def test_met_breached_and_conflicting_latest_reporting_evidence(self):
        *_, reporting, _, report, _ = self._stack()
        self._observation(reporting, report)
        met = reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T08:02:00Z",
        )
        self.assertEqual(met.state, ReportingAssessmentState.MET)
        self.assertFalse(met.regulatory_compliance_determined)
        self.assertFalse(met.reporting_correctness_determined)

        self._observation(
            reporting,
            report,
            observation_id="obs-breach",
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
        self.assertEqual(breached.state, ReportingAssessmentState.BREACHED)

        self._observation(
            reporting,
            report,
            observation_id="obs-conflict-a",
            period_id="2026-06",
            recorded_at="2026-08-19T08:06:00Z",
        )
        self._observation(
            reporting,
            report,
            observation_id="obs-conflict-b",
            period_id="2026-06",
            actual=99,
            recorded_at="2026-08-19T08:06:00Z",
        )
        with self.assertRaisesRegex(GovernanceError, "conflicting latest"):
            reporting.evaluate_report(
                report,
                "2026-06",
                assessed_at="2026-08-19T08:07:00Z",
            )

    def test_source_version_change_stales_metric_and_assessment(self):
        assets, _, _, _, _, reporting, asset, report, metric = self._stack()
        self._observation(reporting, report)
        assessment = reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T08:02:00Z",
        )
        assets.register_asset(
            DataAssetRecord(
                institution_id="bank-a",
                asset_id=asset.asset_id,
                asset_version=2,
                name="Risk Exposure v2",
                data_domain="risk",
                owner_id="owner",
                steward_id="owner",
                system_of_record_id="core",
                classification=DataClassification.RESTRICTED,
                classification_decision_owner_id="owner",
                classification_rationale="Regulated risk data.",
                criticality=DataCriticality.HIGH,
                criticality_decision_owner_id="owner",
                criticality_rationale="Supports material reporting.",
                contains_personal_data=False,
                source_of_truth=True,
                retention_policy_id="ret-1",
                quality_owner_id="owner",
                registered_at="2026-08-19T09:00:00Z",
            )
        )
        with self.assertRaisesRegex(GovernanceError, "source asset is stale"):
            reporting.assert_metric_current(metric)
        with self.assertRaises(GovernanceError):
            reporting.assert_assessment_current(assessment)

    def test_attestation_and_high_finding_require_governed_owners(self):
        *_, reporting, _, report, _ = self._stack()
        self._observation(reporting, report)
        met = reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T08:02:00Z",
        )
        reporting.register_attestation(
            ReportOwnerAttestation(
                institution_id="bank-a",
                attestation_id="att-1",
                assessment_digest=met.artifact_digest,
                owner_id="owner",
                decision=AttestationDecision.APPROVED,
                rationale="Accountable owner reviewed the represented control evidence.",
                attested_at="2026-08-19T08:03:00Z",
                evidence_digest=D1,
            )
        )
        with self.assertRaisesRegex(GovernanceError, "accountable report owner"):
            reporting.register_attestation(
                ReportOwnerAttestation(
                    institution_id="bank-a",
                    attestation_id="att-wrong",
                    assessment_digest=met.artifact_digest,
                    owner_id="reviewer",
                    decision=AttestationDecision.APPROVED,
                    rationale="Wrong accountable owner.",
                    attested_at="2026-08-19T08:03:00Z",
                    evidence_digest=D2,
                )
            )

        self._observation(
            reporting,
            report,
            observation_id="obs-breach",
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
        with self.assertRaisesRegex(GovernanceError, "cannot be approved"):
            reporting.register_attestation(
                ReportOwnerAttestation(
                    institution_id="bank-a",
                    attestation_id="att-bad",
                    assessment_digest=breached.artifact_digest,
                    owner_id="owner",
                    decision=AttestationDecision.APPROVED,
                    rationale="Cannot approve breached assessment.",
                    attested_at="2026-08-19T08:06:00Z",
                    evidence_digest=D3,
                )
            )
        finding = reporting.create_finding(
            breached,
            finding_id="finding-1",
            severity=ReportingFindingSeverity.HIGH,
            owner_id="owner",
            title="Material reporting-control breach",
            identified_at="2026-08-19T08:06:00Z",
            evidence_digest=D1,
        )
        remediation = ReportingRemediationEvidence(
            institution_id="bank-a",
            remediation_id="rem-1",
            finding_digest=finding.artifact_digest,
            owner_id="remediator",
            summary="Corrected represented reporting-control process.",
            completed_at="2026-08-19T08:07:00Z",
            evidence_digest=D2,
        )
        reporting.register_remediation(remediation)
        with self.assertRaisesRegex(GovernanceError, "cannot predate remediation"):
            reporting.register_retest(
                ReportingRetestEvidence(
                    institution_id="bank-a",
                    retest_id="retest-pre-remediation-assessment",
                    finding_digest=finding.artifact_digest,
                    remediation_digest=remediation.artifact_digest,
                    reassessment_digest=breached.artifact_digest,
                    reviewer_id="reviewer",
                    outcome=ReportingRetestOutcome.PASSED,
                    tested_at="2026-08-19T08:08:00Z",
                    evidence_digest=D3,
                )
            )

        self._observation(
            reporting,
            report,
            observation_id="obs-remediated",
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

        with self.assertRaisesRegex(GovernanceError, "independent retest"):
            reporting.register_retest(
                ReportingRetestEvidence(
                    institution_id="bank-a",
                    retest_id="retest-wrong",
                    finding_digest=finding.artifact_digest,
                    remediation_digest=remediation.artifact_digest,
                    reassessment_digest=reassessment.artifact_digest,
                    reviewer_id="remediator",
                    outcome=ReportingRetestOutcome.PASSED,
                    tested_at="2026-08-19T08:09:00Z",
                    evidence_digest=D3,
                )
            )
        retest = ReportingRetestEvidence(
            institution_id="bank-a",
            retest_id="retest-1",
            finding_digest=finding.artifact_digest,
            remediation_digest=remediation.artifact_digest,
            reassessment_digest=reassessment.artifact_digest,
            reviewer_id="reviewer",
            outcome=ReportingRetestOutcome.PASSED,
            tested_at="2026-08-19T08:09:00Z",
            evidence_digest=D4,
        )
        reporting.register_retest(retest)
        self.assertEqual(
            reporting.resolve_finding(
                finding,
                resolved_at="2026-08-19T08:10:00Z",
            ).status.value,
            "closed",
        )

    def test_raw_enum_and_bool_thresholds_fail_closed(self):
        with self.assertRaises(GovernanceError):
            GovernedReport(
                institution_id="bank-a",
                report_id="bad",
                report_version=1,
                name="Bad",
                owner_id="owner",
                family="regulatory",  # type: ignore[arg-type]
                reporting_purpose="Bad raw enum.",
                frequency="monthly",
                maximum_lateness_seconds=1,
                minimum_completeness_basis_points=9900,
                maximum_reconciliation_variance_basis_points=10,
                registered_at="2026-08-19T07:00:00Z",
            )
        with self.assertRaises(GovernanceError):
            GovernedReport(
                institution_id="bank-a",
                report_id="bad-bool",
                report_version=1,
                name="Bad",
                owner_id="owner",
                family=ReportFamily.REGULATORY,
                reporting_purpose="Boolean must not pass as integer.",
                frequency="monthly",
                maximum_lateness_seconds=True,  # type: ignore[arg-type]
                minimum_completeness_basis_points=9900,
                maximum_reconciliation_variance_basis_points=10,
                registered_at="2026-08-19T07:00:00Z",
            )

    def test_dossier_propagates_reporting_gaps_and_rejects_rehashed_fake_met(self):
        assets, semantic, lineage, quality, controls, reporting, _, report, _ = self._stack()
        self._observation(
            reporting,
            report,
            observation_id="obs-breach",
            period_id="2026-08",
            produced_at="2026-08-19T08:03:00Z",
            actual=90,
            reconciliation=80,
            recorded_at="2026-08-19T08:04:00Z",
        )
        reporting.evaluate_report(
            report,
            "2026-08",
            assessed_at="2026-08-19T08:05:00Z",
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
            generated_at="2026-08-19T08:10:00Z",
            source_revision="reporting-v0.2-test",
        )
        self.assertIn("reporting:breached:capital-risk:2026-08", dossier.findings)
        self.assertIn("reporting:attestation_missing:capital-risk:2026-08", dossier.findings)
        document = dossier_document(dossier)
        verify_dossier_document(document)

        tampered = copy.deepcopy(document)
        assessment = next(
            item
            for item in tampered["dossier"]["artifacts"]
            if item["artifact_type"] == "ReportAssuranceAssessment"
        )
        assessment["payload"]["state"] = "met"
        for control in assessment["payload"]["control_assessments"]:
            control["state"] = "met"
            control["reason_code"] = "configured_control_satisfied"
        old_digest = assessment["digest"]
        new_digest = digest_artifact(assessment["payload"])
        assessment["digest"] = new_digest
        assessment["artifact_id"] = new_digest
        reporting_snapshot = next(
            item
            for item in tampered["dossier"]["domain_snapshots"]
            if item["domain"] == "reporting"
        )
        reporting_snapshot["artifact_digests"] = sorted(
            new_digest if value == old_digest else value
            for value in reporting_snapshot["artifact_digests"]
        )
        parent_snapshots = {
            item["domain"]: item["source_snapshot_digest"]
            for item in tampered["dossier"]["domain_snapshots"]
            if item["domain"] != "reporting"
        }
        reporting_artifacts = [
            item for item in tampered["dossier"]["artifacts"] if item["domain"] == "reporting"
        ]
        reporting_snapshot["source_snapshot_digest"] = _reporting_snapshot(
            "bank-a",
            reporting_artifacts,
            parent_snapshots,
        )
        tampered["dossier_digest"] = digest_artifact(tampered["dossier"])
        with self.assertRaisesRegex(GovernanceError, "controls do not match"):
            verify_dossier_document(tampered)


if __name__ == "__main__":
    unittest.main()
