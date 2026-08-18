import unittest

from datagovops import (
    AuthoritativeSystem,
    ComparisonOperator,
    CriticalDataElementDesignation,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    DataElementRecord,
    EvidenceTreatment,
    FindingResolutionState,
    FindingSeverity,
    GovernanceError,
    GovernancePrincipal,
    PrincipalType,
    QualityDimension,
    QualityEvaluationPolicy,
    QualityEvaluationState,
    QualityFinding,
    QualityObservation,
    QualityRegistry,
    QualityRemediationEvidence,
    QualityRetestEvidence,
    QualityRule,
    QualityTargetKind,
    QualityTargetRef,
    RetestOutcome,
    SemanticGovernanceRegistry,
    digest_artifact,
)


class QualityGovernanceTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def asset(self, version=1, name="Customer Balance"):
        return DataAssetRecord(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=version,
            name=name,
            data_domain="customer",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="class-owner",
            classification_rationale="Sensitive financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="crit-owner",
            criticality_rationale="Material customer balance data.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="ret-7",
            quality_owner_id="quality-owner",
            registered_at=f"2026-08-18T08:0{version}:00Z",
        )

    def state(self):
        base = DataAssetRegistry()
        for principal_id in (
            "owner", "steward", "class-owner", "crit-owner", "quality-owner",
            "system-owner", "element-owner", "cde-owner", "policy-owner",
            "finding-owner", "remediation-owner", "reviewer",
        ):
            base.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-18T08:00:00Z",
                )
            )
        for system_id in ("core", "quality-engine"):
            base.register_system(
                AuthoritativeSystem(
                    institution_id="bank-a",
                    system_id=system_id,
                    name=system_id,
                    owner_id="system-owner",
                    system_type="data-platform",
                    authoritative=True,
                    registered_at="2026-08-18T08:00:30Z",
                )
            )
        asset = self.asset()
        base.register_asset(asset)
        semantic = SemanticGovernanceRegistry(base)
        element = DataElementRecord(
            institution_id="bank-a",
            asset_id=asset.asset_id,
            asset_version=1,
            element_id="available-balance",
            name="Available Balance",
            data_type="decimal(18,2)",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T08:02:00Z",
        )
        semantic.register_element(element)
        cde = CriticalDataElementDesignation(
            institution_id="bank-a",
            asset_id=asset.asset_id,
            asset_version=1,
            element_id=element.element_id,
            element_digest=element.artifact_digest,
            cde_owner_id="cde-owner",
            decision_owner_id="crit-owner",
            rationale="Balance is critical to customer and risk reporting.",
            evidence_digest=self.evidence("cde"),
            designated_at="2026-08-18T08:03:00Z",
        )
        semantic.register_cde(cde)
        quality = QualityRegistry(base, semantic)
        target = QualityTargetRef(
            institution_id="bank-a",
            kind=QualityTargetKind.CRITICAL_DATA_ELEMENT,
            asset_id=asset.asset_id,
            asset_version=1,
            element_id=element.element_id,
            target_digest=cde.artifact_digest,
        )
        rule = QualityRule(
            institution_id="bank-a",
            rule_id="balance-completeness",
            rule_version=1,
            target=target,
            dimension=QualityDimension.COMPLETENESS,
            owner_id="quality-owner",
            metric_name="non_null_basis_points",
            measurement_unit="basis_points",
            comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=9900,
            max_age_seconds=3600,
            finding_severity=FindingSeverity.HIGH,
            evidence_digest=self.evidence("rule"),
            registered_at="2026-08-18T08:04:00Z",
        )
        policy = QualityEvaluationPolicy(
            institution_id="bank-a",
            policy_id="default-quality",
            policy_version=1,
            owner_id="policy-owner",
            missing_observation_treatment=EvidenceTreatment.INCOMPLETE,
            stale_observation_treatment=EvidenceTreatment.BREACH,
            freshness_grace_seconds=0,
            evidence_digest=self.evidence("policy"),
            registered_at="2026-08-18T08:05:00Z",
        )
        quality.register_rule(rule)
        quality.register_policy(policy)
        return base, semantic, quality, target, rule, policy, cde

    def observation(self, rule, observation_id, value, measured_at, recorded_at=None):
        return QualityObservation(
            institution_id="bank-a",
            observation_id=observation_id,
            rule_id=rule.rule_id,
            rule_version=rule.rule_version,
            rule_digest=rule.artifact_digest,
            target_digest=rule.target.target_digest,
            observed_value=value,
            source_system_id="quality-engine",
            measured_at=measured_at,
            recorded_at=recorded_at or measured_at,
            evidence_digest=self.evidence(observation_id),
        )

    def test_cde_rule_breach_remediation_independent_retest_and_closure(self):
        _, _, quality, _, rule, policy, _ = self.state()
        quality.register_observation(self.observation(rule, "obs-breach", 9800, "2026-08-18T08:10:00Z"))
        breach = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:20:00Z")
        self.assertEqual(breach.state, QualityEvaluationState.BREACHED)
        finding = QualityFinding(
            institution_id="bank-a", finding_id="finding-1",
            evaluation_digest=breach.artifact_digest, rule_digest=rule.artifact_digest,
            severity=FindingSeverity.HIGH, owner_id="finding-owner",
            title="Balance completeness below governed threshold",
            identified_at="2026-08-18T08:21:00Z", evidence_digest=self.evidence("finding"),
        )
        quality.register_finding(finding)
        self.assertEqual(
            quality.resolve_finding(finding, resolved_at="2026-08-18T08:21:00Z").state,
            FindingResolutionState.OPEN,
        )
        remediation = QualityRemediationEvidence(
            institution_id="bank-a", remediation_id="rem-1",
            finding_digest=finding.artifact_digest, owner_id="remediation-owner",
            summary="Corrected upstream null-handling and reprocessed the governed dataset.",
            completed_at="2026-08-18T08:30:00Z", evidence_digest=self.evidence("remediation"),
        )
        quality.register_remediation(remediation)
        quality.register_observation(self.observation(rule, "obs-pass", 10000, "2026-08-18T08:31:00Z"))
        passed = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:32:00Z")
        retest = QualityRetestEvidence(
            institution_id="bank-a", retest_id="retest-1",
            finding_digest=finding.artifact_digest, remediation_digest=remediation.artifact_digest,
            evaluation_digest=passed.artifact_digest, reviewer_id="reviewer",
            outcome=RetestOutcome.PASSED, retested_at="2026-08-18T08:33:00Z",
            evidence_digest=self.evidence("retest"),
        )
        quality.register_retest(retest)
        resolution = quality.resolve_finding(finding, resolved_at="2026-08-18T08:34:00Z")
        self.assertEqual(resolution.state, FindingResolutionState.CLOSED)
        self.assertIn(remediation.artifact_digest, resolution.evidence_history_digests)
        self.assertIn(retest.artifact_digest, resolution.evidence_history_digests)

    def test_missing_stale_and_conflicting_latest_fail_closed(self):
        _, _, quality, _, rule, policy, _ = self.state()
        missing = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:10:00Z")
        self.assertEqual(missing.state, QualityEvaluationState.INCOMPLETE)
        quality.register_observation(self.observation(rule, "old", 10000, "2026-08-18T06:00:00Z", "2026-08-18T06:01:00Z"))
        stale = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:10:00Z")
        self.assertEqual(stale.state, QualityEvaluationState.BREACHED)
        self.assertEqual(stale.reason_code, "stale_observation")
        quality.register_observation(self.observation(rule, "same-a", 10000, "2026-08-18T08:11:00Z"))
        quality.register_observation(self.observation(rule, "same-b", 9900, "2026-08-18T08:11:00Z"))
        conflict = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:12:00Z")
        self.assertEqual(conflict.state, QualityEvaluationState.INCOMPLETE)
        self.assertEqual(conflict.reason_code, "conflicting_latest_observation")
        self.assertIsNone(conflict.observation_digest)

    def test_high_finding_cannot_close_with_same_remediator_reviewer(self):
        _, _, quality, _, rule, policy, _ = self.state()
        quality.register_observation(self.observation(rule, "bad", 9700, "2026-08-18T08:10:00Z"))
        breach = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:11:00Z")
        finding = QualityFinding(
            institution_id="bank-a", finding_id="f", evaluation_digest=breach.artifact_digest,
            rule_digest=rule.artifact_digest, severity=FindingSeverity.HIGH,
            owner_id="finding-owner", title="Breach", identified_at="2026-08-18T08:12:00Z",
            evidence_digest=self.evidence("f"),
        )
        quality.register_finding(finding)
        remediation = QualityRemediationEvidence(
            institution_id="bank-a", remediation_id="r", finding_digest=finding.artifact_digest,
            owner_id="remediation-owner", summary="Fix", completed_at="2026-08-18T08:20:00Z",
            evidence_digest=self.evidence("r"),
        )
        quality.register_remediation(remediation)
        quality.register_observation(self.observation(rule, "good", 10000, "2026-08-18T08:21:00Z"))
        passed = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:22:00Z")
        with self.assertRaises(GovernanceError):
            quality.register_retest(QualityRetestEvidence(
                institution_id="bank-a", retest_id="same-person",
                finding_digest=finding.artifact_digest, remediation_digest=remediation.artifact_digest,
                evaluation_digest=passed.artifact_digest, reviewer_id="remediation-owner",
                outcome=RetestOutcome.PASSED, retested_at="2026-08-18T08:23:00Z",
                evidence_digest=self.evidence("same"),
            ))

    def test_new_asset_version_stales_cde_quality_rule(self):
        base, _, quality, _, rule, policy, _ = self.state()
        base.register_asset(self.asset(2, "Customer Balance v2"))
        with self.assertRaises(GovernanceError):
            quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T09:00:00Z")

    def test_quality_target_requires_actual_cde_designation(self):
        _, semantic, quality, _, _, _, _ = self.state()
        element = DataElementRecord(
            institution_id="bank-a", asset_id="customer-balance", asset_version=1,
            element_id="non-cde", name="Non CDE", data_type="text", owner_id="element-owner",
            nullable=True, registered_at="2026-08-18T08:06:00Z",
        )
        semantic.register_element(element)
        target = QualityTargetRef(
            institution_id="bank-a", kind=QualityTargetKind.CRITICAL_DATA_ELEMENT,
            asset_id="customer-balance", asset_version=1, element_id="non-cde",
            target_digest=element.artifact_digest,
        )
        with self.assertRaises(GovernanceError):
            quality.resolve_target(target)

    def test_rule_latest_version_is_enforced(self):
        _, _, quality, target, rule, policy, _ = self.state()
        rule2 = QualityRule(
            institution_id="bank-a", rule_id=rule.rule_id, rule_version=2, target=target,
            dimension=QualityDimension.COMPLETENESS, owner_id="quality-owner",
            metric_name="non_null_basis_points", measurement_unit="basis_points",
            comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=9950, max_age_seconds=3600, finding_severity=FindingSeverity.HIGH,
            evidence_digest=self.evidence("rule2"), registered_at="2026-08-18T08:06:00Z",
        )
        quality.register_rule(rule2)
        with self.assertRaises(GovernanceError):
            quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:10:00Z")

    def test_governed_types_fail_closed(self):
        with self.assertRaises(GovernanceError):
            QualityTargetRef(
                institution_id="bank-a", kind="asset", asset_id="a", asset_version=1,
                element_id=None, target_digest=self.evidence("a"),
            )
        target = QualityTargetRef(
            institution_id="bank-a", kind=QualityTargetKind.ASSET, asset_id="a", asset_version=1,
            element_id=None, target_digest=self.evidence("a"),
        )
        with self.assertRaises(GovernanceError):
            QualityRule(
                institution_id="bank-a", rule_id="r", rule_version=1, target=target,
                dimension=QualityDimension.ACCURACY, owner_id="owner", metric_name="m",
                measurement_unit="count", comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
                threshold_value=True, max_age_seconds=60, finding_severity=FindingSeverity.HIGH,
                evidence_digest=self.evidence("r"), registered_at="2026-08-18T08:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
