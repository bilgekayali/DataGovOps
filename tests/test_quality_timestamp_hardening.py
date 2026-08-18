from types import SimpleNamespace
import unittest

from datagovops import (
    AuthoritativeSystem,
    ComparisonOperator,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    EvidenceTreatment,
    FindingSeverity,
    GovernancePrincipal,
    PrincipalType,
    QualityDimension,
    QualityEvaluationPolicy,
    QualityEvaluationState,
    QualityObservation,
    QualityRegistry,
    QualityRule,
    QualityTargetKind,
    QualityTargetRef,
    SemanticGovernanceRegistry,
    digest_artifact,
)


class QualityTimestampHardeningTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def quality_state(self):
        assets = DataAssetRegistry()
        for principal_id in ("owner", "steward", "class-owner", "crit-owner", "quality-owner", "policy-owner", "system-owner"):
            assets.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-18T08:00:00Z",
                )
            )
        for system_id in ("core", "quality-engine"):
            assets.register_system(
                AuthoritativeSystem(
                    institution_id="bank-a",
                    system_id=system_id,
                    name=system_id,
                    owner_id="system-owner",
                    system_type="data-platform",
                    authoritative=True,
                    registered_at="2026-08-18T08:00:00Z",
                )
            )
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            name="Balance",
            data_domain="risk",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="class-owner",
            classification_rationale="Governed financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="crit-owner",
            criticality_rationale="Material reporting data.",
            contains_personal_data=False,
            source_of_truth=True,
            retention_policy_id="ret-1",
            quality_owner_id="quality-owner",
            registered_at="2026-08-18T08:01:00Z",
        )
        assets.register_asset(asset)
        semantic = SemanticGovernanceRegistry(assets)
        quality = QualityRegistry(assets, semantic)
        target = QualityTargetRef(
            institution_id="bank-a",
            kind=QualityTargetKind.ASSET,
            asset_id="balance",
            asset_version=1,
            element_id=None,
            target_digest=asset.artifact_digest,
        )
        rule = QualityRule(
            institution_id="bank-a",
            rule_id="fractional-order",
            rule_version=1,
            target=target,
            dimension=QualityDimension.COMPLETENESS,
            owner_id="quality-owner",
            metric_name="coverage",
            measurement_unit="basis_points",
            comparison_operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
            threshold_value=9900,
            max_age_seconds=60,
            finding_severity=FindingSeverity.HIGH,
            evidence_digest=self.evidence("rule"),
            registered_at="2026-08-18T08:02:00Z",
        )
        policy = QualityEvaluationPolicy(
            institution_id="bank-a",
            policy_id="policy",
            policy_version=1,
            owner_id="policy-owner",
            missing_observation_treatment=EvidenceTreatment.INCOMPLETE,
            stale_observation_treatment=EvidenceTreatment.BREACH,
            freshness_grace_seconds=0,
            evidence_digest=self.evidence("policy"),
            registered_at="2026-08-18T08:02:00Z",
        )
        quality.register_rule(rule)
        quality.register_policy(policy)
        return quality, rule, policy

    def test_fractional_second_observation_is_selected_by_time_not_text(self):
        quality, rule, policy = self.quality_state()
        earlier = QualityObservation(
            institution_id="bank-a",
            observation_id="earlier-textually-larger",
            rule_id=rule.rule_id,
            rule_version=1,
            rule_digest=rule.artifact_digest,
            target_digest=rule.target.target_digest,
            observed_value=10000,
            source_system_id="quality-engine",
            measured_at="2026-08-18T08:10:00Z",
            recorded_at="2026-08-18T08:10:00Z",
            evidence_digest=self.evidence("earlier"),
        )
        later = QualityObservation(
            institution_id="bank-a",
            observation_id="later-fractional",
            rule_id=rule.rule_id,
            rule_version=1,
            rule_digest=rule.artifact_digest,
            target_digest=rule.target.target_digest,
            observed_value=9800,
            source_system_id="quality-engine",
            measured_at="2026-08-18T08:10:00.500000Z",
            recorded_at="2026-08-18T08:10:00.500000Z",
            evidence_digest=self.evidence("later"),
        )
        quality.register_observation(earlier)
        quality.register_observation(later)
        evaluation = quality.evaluate_rule(rule, policy, evaluated_at="2026-08-18T08:10:01Z")
        self.assertEqual(evaluation.state, QualityEvaluationState.BREACHED)
        self.assertEqual(evaluation.observation_digest, later.artifact_digest)

    def test_lifecycle_latest_selection_uses_parsed_timestamp(self):
        earlier = SimpleNamespace(completed_at="2026-08-18T08:10:00Z")
        later = SimpleNamespace(completed_at="2026-08-18T08:10:00.500000Z")
        self.assertIs(QualityRegistry._latest_unique([earlier, later], "completed_at"), later)


if __name__ == "__main__":
    unittest.main()
