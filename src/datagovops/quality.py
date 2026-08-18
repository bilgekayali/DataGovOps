from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .models import GovernanceError, _digest, _enum, _positive_int, _text, _timestamp, digest_artifact
from .registry import DataAssetRegistry
from .semantic import SemanticGovernanceRegistry


def _integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GovernanceError(f"{name} must be an integer")
    return value


def _nonnegative_int(name: str, value: int) -> int:
    _integer(name, value)
    if value < 0:
        raise GovernanceError(f"{name} must be a non-negative integer")
    return value


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


class QualityTargetKind(str, Enum):
    ASSET = "asset"
    CRITICAL_DATA_ELEMENT = "critical_data_element"


class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    INTEGRITY = "integrity"
    OTHER = "other"


class ComparisonOperator(str, Enum):
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"


class EvidenceTreatment(str, Enum):
    INCOMPLETE = "incomplete"
    BREACH = "breach"


class QualityEvaluationState(str, Enum):
    PASSED = "passed"
    BREACHED = "breached"
    INCOMPLETE = "incomplete"


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetestOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class FindingResolutionState(str, Enum):
    OPEN = "open"
    REMEDIATION_SUBMITTED = "remediation_submitted"
    RETEST_FAILED = "retest_failed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class QualityTargetRef:
    institution_id: str
    kind: QualityTargetKind
    asset_id: str
    asset_version: int
    element_id: str | None
    target_digest: str
    schema_version: str = "datagovops.quality-target-ref.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _enum("kind", self.kind, QualityTargetKind)
        _positive_int("asset_version", self.asset_version)
        if self.element_id is not None:
            object.__setattr__(self, "element_id", _text("element_id", self.element_id))
        if self.kind is QualityTargetKind.ASSET and self.element_id is not None:
            raise GovernanceError("asset quality target cannot include element_id")
        if self.kind is QualityTargetKind.CRITICAL_DATA_ELEMENT and self.element_id is None:
            raise GovernanceError("critical-data-element quality target requires element_id")
        _digest("target_digest", self.target_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityRule:
    institution_id: str
    rule_id: str
    rule_version: int
    target: QualityTargetRef
    dimension: QualityDimension
    owner_id: str
    metric_name: str
    measurement_unit: str
    comparison_operator: ComparisonOperator
    threshold_value: int
    max_age_seconds: int
    finding_severity: FindingSeverity
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.quality-rule.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "rule_id", "owner_id", "metric_name", "measurement_unit", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("rule_version", self.rule_version)
        if not isinstance(self.target, QualityTargetRef):
            raise GovernanceError("target must be a QualityTargetRef")
        if self.target.institution_id != self.institution_id:
            raise GovernanceError("quality rule target must use the same institution")
        _enum("dimension", self.dimension, QualityDimension)
        _enum("comparison_operator", self.comparison_operator, ComparisonOperator)
        _enum("finding_severity", self.finding_severity, FindingSeverity)
        _integer("threshold_value", self.threshold_value)
        _positive_int("max_age_seconds", self.max_age_seconds)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityEvaluationPolicy:
    institution_id: str
    policy_id: str
    policy_version: int
    owner_id: str
    missing_observation_treatment: EvidenceTreatment
    stale_observation_treatment: EvidenceTreatment
    freshness_grace_seconds: int
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.quality-evaluation-policy.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "policy_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("policy_version", self.policy_version)
        _enum("missing_observation_treatment", self.missing_observation_treatment, EvidenceTreatment)
        _enum("stale_observation_treatment", self.stale_observation_treatment, EvidenceTreatment)
        _nonnegative_int("freshness_grace_seconds", self.freshness_grace_seconds)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityObservation:
    institution_id: str
    observation_id: str
    rule_id: str
    rule_version: int
    rule_digest: str
    target_digest: str
    observed_value: int
    source_system_id: str
    measured_at: str
    recorded_at: str
    evidence_digest: str
    schema_version: str = "datagovops.quality-observation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "observation_id", "rule_id", "source_system_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("rule_version", self.rule_version)
        _digest("rule_digest", self.rule_digest)
        _digest("target_digest", self.target_digest)
        _integer("observed_value", self.observed_value)
        object.__setattr__(self, "measured_at", _timestamp("measured_at", self.measured_at))
        object.__setattr__(self, "recorded_at", _timestamp("recorded_at", self.recorded_at))
        if _parse_timestamp(self.recorded_at) < _parse_timestamp(self.measured_at):
            raise GovernanceError("recorded_at cannot precede measured_at")
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityRuleEvaluation:
    institution_id: str
    rule_id: str
    rule_version: int
    rule_digest: str
    target_digest: str
    policy_digest: str
    observation_digest: str | None
    state: QualityEvaluationState
    reason_code: str
    evaluated_at: str
    regulatory_compliance_determined: bool = False
    schema_version: str = "datagovops.quality-rule-evaluation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "rule_id", "reason_code", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("rule_version", self.rule_version)
        for field in ("rule_digest", "target_digest", "policy_digest"):
            _digest(field, getattr(self, field))
        if self.observation_digest is not None:
            _digest("observation_digest", self.observation_digest)
        _enum("state", self.state, QualityEvaluationState)
        object.__setattr__(self, "evaluated_at", _timestamp("evaluated_at", self.evaluated_at))
        if type(self.regulatory_compliance_determined) is not bool:
            raise GovernanceError("regulatory_compliance_determined must be a boolean")
        if self.regulatory_compliance_determined:
            raise GovernanceError("quality evaluation does not determine regulatory compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityFinding:
    institution_id: str
    finding_id: str
    evaluation_digest: str
    rule_digest: str
    severity: FindingSeverity
    owner_id: str
    title: str
    identified_at: str
    evidence_digest: str
    schema_version: str = "datagovops.quality-finding.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "finding_id", "owner_id", "title", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=512 if field == "title" else 256))
        _digest("evaluation_digest", self.evaluation_digest)
        _digest("rule_digest", self.rule_digest)
        _enum("severity", self.severity, FindingSeverity)
        object.__setattr__(self, "identified_at", _timestamp("identified_at", self.identified_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityRemediationEvidence:
    institution_id: str
    remediation_id: str
    finding_digest: str
    owner_id: str
    summary: str
    completed_at: str
    evidence_digest: str
    schema_version: str = "datagovops.quality-remediation-evidence.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "remediation_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("finding_digest", self.finding_digest)
        object.__setattr__(self, "summary", _text("summary", self.summary, limit=2048))
        object.__setattr__(self, "completed_at", _timestamp("completed_at", self.completed_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityRetestEvidence:
    institution_id: str
    retest_id: str
    finding_digest: str
    remediation_digest: str
    evaluation_digest: str
    reviewer_id: str
    outcome: RetestOutcome
    retested_at: str
    evidence_digest: str
    schema_version: str = "datagovops.quality-retest-evidence.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "retest_id", "reviewer_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        for field in ("finding_digest", "remediation_digest", "evaluation_digest", "evidence_digest"):
            _digest(field, getattr(self, field))
        _enum("outcome", self.outcome, RetestOutcome)
        object.__setattr__(self, "retested_at", _timestamp("retested_at", self.retested_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class QualityFindingResolution:
    institution_id: str
    finding_digest: str
    state: FindingResolutionState
    remediation_digest: str | None
    retest_digest: str | None
    evidence_history_digests: tuple[str, ...]
    resolved_at: str
    schema_version: str = "datagovops.quality-finding-resolution.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        _digest("finding_digest", self.finding_digest)
        _enum("state", self.state, FindingResolutionState)
        if self.remediation_digest is not None:
            _digest("remediation_digest", self.remediation_digest)
        if self.retest_digest is not None:
            _digest("retest_digest", self.retest_digest)
        if len(set(self.evidence_history_digests)) != len(self.evidence_history_digests):
            raise GovernanceError("evidence_history_digests must be unique")
        for digest in self.evidence_history_digests:
            _digest("evidence_history_digest", digest)
        object.__setattr__(self, "resolved_at", _timestamp("resolved_at", self.resolved_at))
        if self.state is FindingResolutionState.OPEN and (self.remediation_digest is not None or self.retest_digest is not None):
            raise GovernanceError("open finding resolution cannot include remediation/retest")
        if self.state is FindingResolutionState.REMEDIATION_SUBMITTED and (self.remediation_digest is None or self.retest_digest is not None):
            raise GovernanceError("remediation_submitted requires remediation only")
        if self.state in (FindingResolutionState.RETEST_FAILED, FindingResolutionState.CLOSED) and (self.remediation_digest is None or self.retest_digest is None):
            raise GovernanceError("retested finding resolution requires remediation and retest")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class QualityRegistry:
    """Deterministic data-quality governance bound to exact asset/CDE evidence."""

    def __init__(self, asset_registry: DataAssetRegistry, semantic_registry: SemanticGovernanceRegistry) -> None:
        self.asset_registry = asset_registry
        self.semantic_registry = semantic_registry
        self._rules: dict[tuple[str, str, int], QualityRule] = {}
        self._policies: dict[tuple[str, str, int], QualityEvaluationPolicy] = {}
        self._observations: dict[tuple[str, str], QualityObservation] = {}
        self._evaluations: dict[str, QualityRuleEvaluation] = {}
        self._findings: dict[tuple[str, str], QualityFinding] = {}
        self._remediations: dict[tuple[str, str], QualityRemediationEvidence] = {}
        self._retests: dict[tuple[str, str], QualityRetestEvidence] = {}

    def resolve_target(self, target: QualityTargetRef):
        if target.kind is QualityTargetKind.ASSET:
            asset = self.asset_registry.asset(target.institution_id, target.asset_id, target.asset_version)
            if target.target_digest != asset.artifact_digest:
                raise GovernanceError("quality target is bound to different asset content")
            return asset
        key = (target.institution_id, target.asset_id, target.asset_version, target.element_id or "")
        designation = self.semantic_registry._cde_designations.get(key)
        if designation is None:
            raise GovernanceError("quality CDE target has no registered CDE designation")
        if target.target_digest != designation.artifact_digest:
            raise GovernanceError("quality target is bound to different CDE designation")
        return designation

    def assert_target_current(self, target: QualityTargetRef) -> None:
        resolved = self.resolve_target(target)
        if target.kind is QualityTargetKind.ASSET:
            latest = self.asset_registry.latest_asset(target.institution_id, target.asset_id)
            if latest.asset_version != target.asset_version:
                raise GovernanceError("quality target is stale for latest asset version")
        else:
            self.semantic_registry.assert_cde_current(resolved)

    def register_rule(self, rule: QualityRule) -> str:
        self.asset_registry.principal(rule.institution_id, rule.owner_id)
        self.resolve_target(rule.target)
        key = (rule.institution_id, rule.rule_id, rule.rule_version)
        existing = self._rules.get(key)
        if existing is not None:
            if existing.artifact_digest != rule.artifact_digest:
                raise GovernanceError("quality rule identity/version has different content")
            return existing.artifact_digest
        history = self.rule_history(rule.institution_id, rule.rule_id)
        expected = 1 if not history else history[-1].rule_version + 1
        if rule.rule_version != expected:
            raise GovernanceError(f"rule_version must be contiguous; expected version {expected}")
        self._rules[key] = rule
        return rule.artifact_digest

    def rule(self, institution_id: str, rule_id: str, rule_version: int) -> QualityRule:
        try:
            return self._rules[(institution_id, rule_id, rule_version)]
        except KeyError as exc:
            raise GovernanceError("unknown quality rule version") from exc

    def rule_history(self, institution_id: str, rule_id: str) -> tuple[QualityRule, ...]:
        return tuple(sorted((item for (scope, current_id, _), item in self._rules.items() if scope == institution_id and current_id == rule_id), key=lambda item: item.rule_version))

    def latest_rule(self, institution_id: str, rule_id: str) -> QualityRule:
        history = self.rule_history(institution_id, rule_id)
        if not history:
            raise GovernanceError("unknown quality rule")
        return history[-1]

    def register_policy(self, policy: QualityEvaluationPolicy) -> str:
        self.asset_registry.principal(policy.institution_id, policy.owner_id)
        key = (policy.institution_id, policy.policy_id, policy.policy_version)
        existing = self._policies.get(key)
        if existing is not None:
            if existing.artifact_digest != policy.artifact_digest:
                raise GovernanceError("quality policy identity/version has different content")
            return existing.artifact_digest
        history = self.policy_history(policy.institution_id, policy.policy_id)
        expected = 1 if not history else history[-1].policy_version + 1
        if policy.policy_version != expected:
            raise GovernanceError(f"policy_version must be contiguous; expected version {expected}")
        self._policies[key] = policy
        return policy.artifact_digest

    def policy_history(self, institution_id: str, policy_id: str) -> tuple[QualityEvaluationPolicy, ...]:
        return tuple(sorted((item for (scope, current_id, _), item in self._policies.items() if scope == institution_id and current_id == policy_id), key=lambda item: item.policy_version))

    def latest_policy(self, institution_id: str, policy_id: str) -> QualityEvaluationPolicy:
        history = self.policy_history(institution_id, policy_id)
        if not history:
            raise GovernanceError("unknown quality evaluation policy")
        return history[-1]

    def register_observation(self, observation: QualityObservation) -> str:
        rule = self.rule(observation.institution_id, observation.rule_id, observation.rule_version)
        if observation.rule_digest != rule.artifact_digest:
            raise GovernanceError("quality observation is bound to different rule content")
        if observation.target_digest != rule.target.target_digest:
            raise GovernanceError("quality observation is bound to different target content")
        self.asset_registry.system(observation.institution_id, observation.source_system_id)
        key = (observation.institution_id, observation.observation_id)
        existing = self._observations.get(key)
        if existing is not None and existing.artifact_digest != observation.artifact_digest:
            raise GovernanceError("observation_id is already registered with different content")
        self._observations.setdefault(key, observation)
        return observation.artifact_digest

    def observations_for_rule(self, rule: QualityRule) -> tuple[QualityObservation, ...]:
        return tuple(sorted((item for item in self._observations.values() if item.institution_id == rule.institution_id and item.rule_digest == rule.artifact_digest), key=lambda item: (item.measured_at, item.observation_id)))

    @staticmethod
    def _treatment_state(treatment: EvidenceTreatment) -> QualityEvaluationState:
        return QualityEvaluationState.INCOMPLETE if treatment is EvidenceTreatment.INCOMPLETE else QualityEvaluationState.BREACHED

    @staticmethod
    def _passes(rule: QualityRule, value: int) -> bool:
        op, threshold = rule.comparison_operator, rule.threshold_value
        if op is ComparisonOperator.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        if op is ComparisonOperator.LESS_THAN_OR_EQUAL:
            return value <= threshold
        if op is ComparisonOperator.GREATER_THAN:
            return value > threshold
        if op is ComparisonOperator.LESS_THAN:
            return value < threshold
        return value == threshold

    def evaluate_rule(self, rule: QualityRule, policy: QualityEvaluationPolicy, *, evaluated_at: str) -> QualityRuleEvaluation:
        registered = self.rule(rule.institution_id, rule.rule_id, rule.rule_version)
        if registered.artifact_digest != rule.artifact_digest:
            raise GovernanceError("quality rule does not match registered exact rule")
        if self.latest_rule(rule.institution_id, rule.rule_id).artifact_digest != rule.artifact_digest:
            raise GovernanceError("quality rule is stale for latest rule version")
        self.assert_target_current(rule.target)
        latest_policy = self.latest_policy(policy.institution_id, policy.policy_id)
        if latest_policy.artifact_digest != policy.artifact_digest:
            raise GovernanceError("quality policy is stale for latest policy version")
        if policy.institution_id != rule.institution_id:
            raise GovernanceError("quality policy and rule must use the same institution")
        evaluated_at = _timestamp("evaluated_at", evaluated_at)
        evaluated_dt = _parse_timestamp(evaluated_at)
        eligible = [item for item in self.observations_for_rule(rule) if _parse_timestamp(item.measured_at) <= evaluated_dt]
        observation_digest = None
        if not eligible:
            state = self._treatment_state(policy.missing_observation_treatment)
            reason = "missing_observation"
        else:
            latest_time = max(_parse_timestamp(item.measured_at) for item in eligible)
            latest = [item for item in eligible if _parse_timestamp(item.measured_at) == latest_time]
            if len(latest) > 1:
                state = QualityEvaluationState.INCOMPLETE
                reason = "conflicting_latest_observation"
            else:
                observation = latest[0]
                observation_digest = observation.artifact_digest
                age_seconds = int((evaluated_dt - _parse_timestamp(observation.measured_at)).total_seconds())
                if age_seconds > rule.max_age_seconds + policy.freshness_grace_seconds:
                    state = self._treatment_state(policy.stale_observation_treatment)
                    reason = "stale_observation"
                elif self._passes(rule, observation.observed_value):
                    state, reason = QualityEvaluationState.PASSED, "threshold_satisfied"
                else:
                    state, reason = QualityEvaluationState.BREACHED, "threshold_breached"
        evaluation = QualityRuleEvaluation(institution_id=rule.institution_id, rule_id=rule.rule_id, rule_version=rule.rule_version, rule_digest=rule.artifact_digest, target_digest=rule.target.target_digest, policy_digest=policy.artifact_digest, observation_digest=observation_digest, state=state, reason_code=reason, evaluated_at=evaluated_at)
        self._evaluations.setdefault(evaluation.artifact_digest, evaluation)
        return evaluation

    def evaluation(self, digest: str) -> QualityRuleEvaluation:
        try:
            return self._evaluations[digest]
        except KeyError as exc:
            raise GovernanceError("unknown quality evaluation") from exc

    def assert_evaluation_current(self, evaluation: QualityRuleEvaluation, policy: QualityEvaluationPolicy) -> None:
        self.evaluation(evaluation.artifact_digest)
        rule = self.rule(evaluation.institution_id, evaluation.rule_id, evaluation.rule_version)
        recomputed = self.evaluate_rule(rule, policy, evaluated_at=evaluation.evaluated_at)
        if recomputed.artifact_digest != evaluation.artifact_digest:
            raise GovernanceError("quality evaluation is stale for current evidence")

    def register_finding(self, finding: QualityFinding) -> str:
        evaluation = self.evaluation(finding.evaluation_digest)
        if evaluation.state is QualityEvaluationState.PASSED:
            raise GovernanceError("passed quality evaluation cannot create a finding")
        if finding.rule_digest != evaluation.rule_digest:
            raise GovernanceError("quality finding is bound to different rule")
        rule = self.rule(evaluation.institution_id, evaluation.rule_id, evaluation.rule_version)
        if finding.severity is not rule.finding_severity:
            raise GovernanceError("quality finding severity cannot downgrade/override rule severity")
        self.asset_registry.principal(finding.institution_id, finding.owner_id)
        if finding.institution_id != evaluation.institution_id:
            raise GovernanceError("quality finding and evaluation must use the same institution")
        if _parse_timestamp(finding.identified_at) < _parse_timestamp(evaluation.evaluated_at):
            raise GovernanceError("finding cannot predate its quality evaluation")
        key = (finding.institution_id, finding.finding_id)
        existing = self._findings.get(key)
        if existing is not None and existing.artifact_digest != finding.artifact_digest:
            raise GovernanceError("finding_id is already registered with different content")
        self._findings.setdefault(key, finding)
        return finding.artifact_digest

    def finding_by_digest(self, institution_id: str, digest: str) -> QualityFinding:
        for (scope, _), item in self._findings.items():
            if scope == institution_id and item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown quality finding")

    def register_remediation(self, remediation: QualityRemediationEvidence) -> str:
        finding = self.finding_by_digest(remediation.institution_id, remediation.finding_digest)
        self.asset_registry.principal(remediation.institution_id, remediation.owner_id)
        if _parse_timestamp(remediation.completed_at) < _parse_timestamp(finding.identified_at):
            raise GovernanceError("remediation cannot predate finding")
        key = (remediation.institution_id, remediation.remediation_id)
        existing = self._remediations.get(key)
        if existing is not None and existing.artifact_digest != remediation.artifact_digest:
            raise GovernanceError("remediation_id is already registered with different content")
        self._remediations.setdefault(key, remediation)
        return remediation.artifact_digest

    def remediation_by_digest(self, institution_id: str, digest: str) -> QualityRemediationEvidence:
        for (scope, _), item in self._remediations.items():
            if scope == institution_id and item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown quality remediation")

    def register_retest(self, retest: QualityRetestEvidence) -> str:
        finding = self.finding_by_digest(retest.institution_id, retest.finding_digest)
        remediation = self.remediation_by_digest(retest.institution_id, retest.remediation_digest)
        if remediation.finding_digest != finding.artifact_digest:
            raise GovernanceError("quality retest remediation belongs to different finding")
        evaluation = self.evaluation(retest.evaluation_digest)
        if evaluation.rule_digest != finding.rule_digest:
            raise GovernanceError("quality retest evaluation belongs to different rule")
        if _parse_timestamp(evaluation.evaluated_at) < _parse_timestamp(remediation.completed_at):
            raise GovernanceError("quality retest evaluation cannot predate remediation")
        if _parse_timestamp(retest.retested_at) < _parse_timestamp(evaluation.evaluated_at):
            raise GovernanceError("retested_at cannot predate retest evaluation")
        self.asset_registry.principal(retest.institution_id, retest.reviewer_id)
        expected = RetestOutcome.PASSED if evaluation.state is QualityEvaluationState.PASSED else RetestOutcome.FAILED
        if retest.outcome is not expected:
            raise GovernanceError("quality retest outcome conflicts with evaluation state")
        if finding.severity in (FindingSeverity.HIGH, FindingSeverity.CRITICAL) and retest.reviewer_id == remediation.owner_id:
            raise GovernanceError("high/critical finding retest requires independent reviewer")
        key = (retest.institution_id, retest.retest_id)
        existing = self._retests.get(key)
        if existing is not None and existing.artifact_digest != retest.artifact_digest:
            raise GovernanceError("retest_id is already registered with different content")
        self._retests.setdefault(key, retest)
        return retest.artifact_digest

    @staticmethod
    def _latest_unique(items, timestamp_field: str):
        if not items:
            return None
        latest_time = max(_parse_timestamp(getattr(item, timestamp_field)) for item in items)
        latest = [item for item in items if _parse_timestamp(getattr(item, timestamp_field)) == latest_time]
        if len(latest) > 1:
            raise GovernanceError("conflicting latest quality lifecycle evidence")
        return latest[0]

    def resolve_finding(self, finding: QualityFinding, *, resolved_at: str) -> QualityFindingResolution:
        self.finding_by_digest(finding.institution_id, finding.artifact_digest)
        resolved_at = _timestamp("resolved_at", resolved_at)
        remediations = [item for item in self._remediations.values() if item.institution_id == finding.institution_id and item.finding_digest == finding.artifact_digest]
        latest_remediation = self._latest_unique(remediations, "completed_at")
        retests = [item for item in self._retests.values() if item.institution_id == finding.institution_id and item.finding_digest == finding.artifact_digest]
        history = tuple(sorted([item.artifact_digest for item in remediations] + [item.artifact_digest for item in retests]))
        if latest_remediation is None:
            state, remediation_digest, retest_digest, latest_event_time = FindingResolutionState.OPEN, None, None, finding.identified_at
        else:
            remediation_digest = latest_remediation.artifact_digest
            relevant_retests = [item for item in retests if item.remediation_digest == latest_remediation.artifact_digest]
            latest_retest = self._latest_unique(relevant_retests, "retested_at")
            if latest_retest is None:
                state, retest_digest, latest_event_time = FindingResolutionState.REMEDIATION_SUBMITTED, None, latest_remediation.completed_at
            else:
                retest_digest = latest_retest.artifact_digest
                state = FindingResolutionState.CLOSED if latest_retest.outcome is RetestOutcome.PASSED else FindingResolutionState.RETEST_FAILED
                latest_event_time = latest_retest.retested_at
        if _parse_timestamp(resolved_at) < _parse_timestamp(latest_event_time):
            raise GovernanceError("finding resolution cannot predate latest lifecycle evidence")
        return QualityFindingResolution(institution_id=finding.institution_id, finding_digest=finding.artifact_digest, state=state, remediation_digest=remediation_digest, retest_digest=retest_digest, evidence_history_digests=history, resolved_at=resolved_at)

    def snapshot_digest(self, institution_id: str) -> str:
        return digest_artifact({
            "institution_id": institution_id,
            "asset_registry_snapshot_digest": self.asset_registry.snapshot_digest(institution_id),
            "semantic_registry_snapshot_digest": self.semantic_registry.snapshot_digest(institution_id),
            "quality_rules": sorted(item.artifact_digest for (scope, _, _), item in self._rules.items() if scope == institution_id),
            "quality_policies": sorted(item.artifact_digest for (scope, _, _), item in self._policies.items() if scope == institution_id),
            "quality_observations": sorted(item.artifact_digest for (scope, _), item in self._observations.items() if scope == institution_id),
            "quality_evaluations": sorted(item.artifact_digest for item in self._evaluations.values() if item.institution_id == institution_id),
            "quality_findings": sorted(item.artifact_digest for (scope, _), item in self._findings.items() if scope == institution_id),
            "quality_remediations": sorted(item.artifact_digest for (scope, _), item in self._remediations.items() if scope == institution_id),
            "quality_retests": sorted(item.artifact_digest for (scope, _), item in self._retests.items() if scope == institution_id),
        })
