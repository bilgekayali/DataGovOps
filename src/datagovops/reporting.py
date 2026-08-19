from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable

from .lineage import LineageRegistry
from .models import GovernanceError, _digest, _enum, _positive_int, _text, _timestamp, digest_artifact
from .quality import QualityRegistry
from .registry import DataAssetRegistry


class ReportFamily(str, Enum):
    REGULATORY = "regulatory"
    MANAGEMENT = "management"
    FINANCIAL = "financial"
    RISK = "risk"
    OTHER = "other"


class ReportingMetric(str, Enum):
    TIMELINESS = "timeliness"
    COMPLETENESS = "completeness"
    RECONCILIATION = "reconciliation"


class ReportingMetricState(str, Enum):
    MET = "met"
    BREACHED = "breached"
    INCOMPLETE = "incomplete"


class ReportingAssessmentState(str, Enum):
    MET = "met"
    BREACHED = "breached"
    INCOMPLETE = "incomplete"


class AttestationDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ReportingFindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportingFindingStatus(str, Enum):
    OPEN = "open"
    REMEDIATION_SUBMITTED = "remediation_submitted"
    RETEST_FAILED = "retest_failed"
    CLOSED = "closed"


class ReportingRetestOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class ReportingResolutionState(str, Enum):
    SUCCESSFUL = "successful"
    SUCCESSFUL_WITH_FINDINGS = "successful_with_findings"
    BLOCKED = "blocked"
    INCOMPLETE = "incomplete"


def _nonnegative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceError(f"{name} must be a non-negative integer")
    return value


def _basis_points(name: str, value: int, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= 10_000:
        raise GovernanceError(f"{name} must be an integer between {minimum} and 10000 basis points")
    return value


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _unique_digests(name: str, values: Iterable[str], *, allow_empty: bool = True) -> tuple[str, ...]:
    result = tuple(_digest(name, value) for value in values)
    if not allow_empty and not result:
        raise GovernanceError(f"{name}s must contain at least one digest")
    if len(result) != len(set(result)):
        raise GovernanceError(f"{name}s must be unique")
    return tuple(sorted(result))


@dataclass(frozen=True, slots=True)
class ReportSourceRef:
    institution_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    schema_version: str = "datagovops.report-source-ref.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("asset_digest", self.asset_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernedReport:
    institution_id: str
    report_id: str
    report_version: int
    name: str
    owner_id: str
    family: ReportFamily
    reporting_purpose: str
    frequency: str
    maximum_lateness_seconds: int
    minimum_completeness_basis_points: int
    maximum_reconciliation_variance_basis_points: int
    registered_at: str
    schema_version: str = "datagovops.governed-report.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "report_id", "name", "owner_id", "reporting_purpose", "frequency", "schema_version"):
            limit = 1024 if field == "reporting_purpose" else 512 if field == "name" else 256
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=limit))
        _positive_int("report_version", self.report_version)
        _enum("family", self.family, ReportFamily)
        _nonnegative_int("maximum_lateness_seconds", self.maximum_lateness_seconds)
        _basis_points("minimum_completeness_basis_points", self.minimum_completeness_basis_points, positive=True)
        _basis_points("maximum_reconciliation_variance_basis_points", self.maximum_reconciliation_variance_basis_points)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportMetricDefinition:
    institution_id: str
    metric_id: str
    metric_version: int
    report_digest: str
    name: str
    owner_id: str
    source_refs: tuple[ReportSourceRef, ...]
    transformation_digests: tuple[str, ...]
    quality_rule_digests: tuple[str, ...]
    calculation_description: str
    registered_at: str
    schema_version: str = "datagovops.report-metric-definition.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "metric_id", "name", "owner_id", "calculation_description", "schema_version"):
            limit = 2048 if field == "calculation_description" else 512 if field == "name" else 256
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=limit))
        _positive_int("metric_version", self.metric_version)
        _digest("report_digest", self.report_digest)
        if not self.source_refs or len(set(self.source_refs)) != len(self.source_refs):
            raise GovernanceError("report metric source_refs must be non-empty and unique")
        if any(item.institution_id != self.institution_id for item in self.source_refs):
            raise GovernanceError("report metric source refs must remain in institution scope")
        object.__setattr__(self, "source_refs", tuple(sorted(self.source_refs, key=lambda item: (item.asset_id, item.asset_version))))
        object.__setattr__(self, "transformation_digests", _unique_digests("transformation_digest", self.transformation_digests))
        object.__setattr__(self, "quality_rule_digests", _unique_digests("quality_rule_digest", self.quality_rule_digests))
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportProductionObservation:
    institution_id: str
    observation_id: str
    report_digest: str
    period_id: str
    reporting_basis_digest: str
    due_at: str
    produced_at: str
    expected_record_count: int
    actual_record_count: int
    reconciliation_variance_basis_points: int
    source_system_id: str
    evidence_digest: str
    recorded_at: str
    schema_version: str = "datagovops.report-production-observation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "observation_id", "period_id", "source_system_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("report_digest", self.report_digest)
        _digest("reporting_basis_digest", self.reporting_basis_digest)
        object.__setattr__(self, "due_at", _timestamp("due_at", self.due_at))
        object.__setattr__(self, "produced_at", _timestamp("produced_at", self.produced_at))
        object.__setattr__(self, "recorded_at", _timestamp("recorded_at", self.recorded_at))
        _positive_int("expected_record_count", self.expected_record_count)
        _nonnegative_int("actual_record_count", self.actual_record_count)
        _basis_points("reconciliation_variance_basis_points", self.reconciliation_variance_basis_points)
        _digest("evidence_digest", self.evidence_digest)
        if _parse_time(self.recorded_at) < _parse_time(self.produced_at):
            raise GovernanceError("report observation cannot be recorded before production")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportingControlAssessment:
    metric: ReportingMetric
    state: ReportingMetricState
    observed_value: int | None
    threshold_value: int
    reason_code: str

    def __post_init__(self) -> None:
        _enum("metric", self.metric, ReportingMetric)
        _enum("state", self.state, ReportingMetricState)
        if self.observed_value is not None:
            _nonnegative_int("observed_value", self.observed_value)
        _nonnegative_int("threshold_value", self.threshold_value)
        object.__setattr__(self, "reason_code", _text("reason_code", self.reason_code))
        if self.state is ReportingMetricState.INCOMPLETE and self.observed_value is not None:
            raise GovernanceError("incomplete reporting control cannot carry observed value")
        if self.state is not ReportingMetricState.INCOMPLETE and self.observed_value is None:
            raise GovernanceError("met/breached reporting control requires observed value")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportAssuranceAssessment:
    institution_id: str
    report_digest: str
    period_id: str
    reporting_basis_digest: str
    observation_digest: str | None
    metric_definition_digests: tuple[str, ...]
    control_assessments: tuple[ReportingControlAssessment, ...]
    state: ReportingAssessmentState
    gaps: tuple[str, ...]
    assessed_at: str
    regulatory_compliance_determined: bool = False
    reporting_correctness_determined: bool = False
    schema_version: str = "datagovops.report-assurance-assessment.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "period_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("report_digest", self.report_digest)
        _digest("reporting_basis_digest", self.reporting_basis_digest)
        if self.observation_digest is not None:
            _digest("observation_digest", self.observation_digest)
        object.__setattr__(self, "metric_definition_digests", _unique_digests("metric_definition_digest", self.metric_definition_digests))
        controls = tuple(self.control_assessments)
        if {item.metric for item in controls} != set(ReportingMetric) or len(controls) != len(set(item.metric for item in controls)):
            raise GovernanceError("report assessment must cover every reporting control exactly once")
        object.__setattr__(self, "control_assessments", tuple(sorted(controls, key=lambda item: item.metric.value)))
        _enum("state", self.state, ReportingAssessmentState)
        gaps = tuple(self.gaps)
        if gaps != tuple(sorted(set(gaps))):
            raise GovernanceError("report assessment gaps must be sorted and unique")
        object.__setattr__(self, "assessed_at", _timestamp("assessed_at", self.assessed_at))
        if type(self.regulatory_compliance_determined) is not bool or self.regulatory_compliance_determined:
            raise GovernanceError("report assessment does not determine regulatory compliance")
        if type(self.reporting_correctness_determined) is not bool or self.reporting_correctness_determined:
            raise GovernanceError("report assessment does not determine reporting correctness")
        states = {item.state for item in controls}
        expected = ReportingAssessmentState.MET
        if ReportingMetricState.INCOMPLETE in states:
            expected = ReportingAssessmentState.INCOMPLETE
        elif ReportingMetricState.BREACHED in states:
            expected = ReportingAssessmentState.BREACHED
        if self.state is not expected:
            raise GovernanceError("report assessment state is inconsistent with controls")
        if self.state is ReportingAssessmentState.MET and gaps:
            raise GovernanceError("met report assessment cannot carry gaps")
        if self.state is ReportingAssessmentState.INCOMPLETE and not gaps:
            raise GovernanceError("incomplete report assessment must explain missing evidence")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportOwnerAttestation:
    institution_id: str
    attestation_id: str
    assessment_digest: str
    owner_id: str
    decision: AttestationDecision
    rationale: str
    attested_at: str
    evidence_digest: str
    regulatory_approval_determined: bool = False
    schema_version: str = "datagovops.report-owner-attestation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "attestation_id", "owner_id", "rationale", "schema_version"):
            limit = 2048 if field == "rationale" else 256
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=limit))
        _digest("assessment_digest", self.assessment_digest)
        _enum("decision", self.decision, AttestationDecision)
        object.__setattr__(self, "attested_at", _timestamp("attested_at", self.attested_at))
        _digest("evidence_digest", self.evidence_digest)
        if type(self.regulatory_approval_determined) is not bool or self.regulatory_approval_determined:
            raise GovernanceError("report attestation does not determine regulatory approval")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportingFinding:
    institution_id: str
    finding_id: str
    assessment_digest: str
    severity: ReportingFindingSeverity
    owner_id: str
    title: str
    identified_at: str
    evidence_digest: str
    schema_version: str = "datagovops.reporting-finding.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "finding_id", "owner_id", "title", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=512 if field == "title" else 256))
        _digest("assessment_digest", self.assessment_digest)
        _enum("severity", self.severity, ReportingFindingSeverity)
        object.__setattr__(self, "identified_at", _timestamp("identified_at", self.identified_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)

    @property
    def blocking(self) -> bool:
        return self.severity in {ReportingFindingSeverity.HIGH, ReportingFindingSeverity.CRITICAL}


@dataclass(frozen=True, slots=True)
class ReportingRemediationEvidence:
    institution_id: str
    remediation_id: str
    finding_digest: str
    owner_id: str
    summary: str
    completed_at: str
    evidence_digest: str
    schema_version: str = "datagovops.reporting-remediation-evidence.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "remediation_id", "owner_id", "summary", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=2048 if field == "summary" else 256))
        _digest("finding_digest", self.finding_digest)
        object.__setattr__(self, "completed_at", _timestamp("completed_at", self.completed_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportingRetestEvidence:
    institution_id: str
    retest_id: str
    finding_digest: str
    remediation_digest: str
    reviewer_id: str
    outcome: ReportingRetestOutcome
    tested_at: str
    evidence_digest: str
    schema_version: str = "datagovops.reporting-retest-evidence.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "retest_id", "reviewer_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("finding_digest", self.finding_digest)
        _digest("remediation_digest", self.remediation_digest)
        _enum("outcome", self.outcome, ReportingRetestOutcome)
        object.__setattr__(self, "tested_at", _timestamp("tested_at", self.tested_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ReportingFindingResolution:
    institution_id: str
    finding_digest: str
    status: ReportingFindingStatus
    remediation_digest: str | None
    retest_digest: str | None
    resolved_at: str
    schema_version: str = "datagovops.reporting-finding-resolution.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("finding_digest", self.finding_digest)
        _enum("status", self.status, ReportingFindingStatus)
        if self.remediation_digest is not None:
            _digest("remediation_digest", self.remediation_digest)
        if self.retest_digest is not None:
            _digest("retest_digest", self.retest_digest)
        object.__setattr__(self, "resolved_at", _timestamp("resolved_at", self.resolved_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class ReportingGovernanceRegistry:
    """Deterministic reporting-governance registry bound to current data/lineage/quality state."""

    def __init__(self, asset_registry: DataAssetRegistry, lineage_registry: LineageRegistry, quality_registry: QualityRegistry) -> None:
        if lineage_registry.asset_registry is not asset_registry or quality_registry.asset_registry is not asset_registry:
            raise GovernanceError("reporting registry must share the authoritative asset registry")
        if lineage_registry.semantic_registry is not quality_registry.semantic_registry:
            raise GovernanceError("reporting registry must share semantic governance state")
        self.asset_registry = asset_registry
        self.semantic_registry = lineage_registry.semantic_registry
        self.lineage_registry = lineage_registry
        self.quality_registry = quality_registry
        self._reports: dict[tuple[str, str, int], GovernedReport] = {}
        self._metrics: dict[tuple[str, str, int], ReportMetricDefinition] = {}
        self._observations: dict[tuple[str, str], ReportProductionObservation] = {}
        self._assessments: dict[str, ReportAssuranceAssessment] = {}
        self._attestations: dict[tuple[str, str], ReportOwnerAttestation] = {}
        self._findings: dict[tuple[str, str], ReportingFinding] = {}
        self._remediations: dict[tuple[str, str], ReportingRemediationEvidence] = {}
        self._retests: dict[tuple[str, str], ReportingRetestEvidence] = {}

    def _basis_digest(self, institution_id: str, report_digest: str) -> str:
        metrics = sorted(
            item.artifact_digest
            for item in self._metrics.values()
            if item.institution_id == institution_id and item.report_digest == report_digest
        )
        return digest_artifact({
            "institution_id": institution_id,
            "report_digest": report_digest,
            "metric_definition_digests": metrics,
            "asset_registry_snapshot_digest": self.asset_registry.snapshot_digest(institution_id),
            "semantic_registry_snapshot_digest": self.semantic_registry.snapshot_digest(institution_id),
            "lineage_registry_snapshot_digest": self.lineage_registry.snapshot_digest(institution_id),
            "quality_registry_snapshot_digest": self.quality_registry.snapshot_digest(institution_id),
        })

    def register_report(self, report: GovernedReport) -> str:
        self.asset_registry.principal(report.institution_id, report.owner_id)
        key = (report.institution_id, report.report_id, report.report_version)
        existing = self._reports.get(key)
        if existing is not None:
            if existing.artifact_digest != report.artifact_digest:
                raise GovernanceError("report identity/version already exists with different content")
            return existing.artifact_digest
        history = self.report_history(report.institution_id, report.report_id)
        expected = 1 if not history else history[-1].report_version + 1
        if report.report_version != expected:
            raise GovernanceError(f"report_version must be contiguous; expected version {expected}")
        self._reports[key] = report
        return report.artifact_digest

    def report_history(self, institution_id: str, report_id: str) -> tuple[GovernedReport, ...]:
        return tuple(sorted((item for (scope, current, _), item in self._reports.items() if scope == institution_id and current == report_id), key=lambda item: item.report_version))

    def latest_report(self, institution_id: str, report_id: str) -> GovernedReport:
        history = self.report_history(institution_id, report_id)
        if not history:
            raise GovernanceError("unknown governed report")
        return history[-1]

    def _assert_report_current(self, report: GovernedReport) -> None:
        registered = self._reports.get((report.institution_id, report.report_id, report.report_version))
        if registered is None or registered.artifact_digest != report.artifact_digest:
            raise GovernanceError("report is not exact registered evidence")
        if self.latest_report(report.institution_id, report.report_id).artifact_digest != report.artifact_digest:
            raise GovernanceError("report definition is stale")

    def register_metric(self, metric: ReportMetricDefinition) -> str:
        report = self._report_by_digest(metric.report_digest)
        if report.institution_id != metric.institution_id:
            raise GovernanceError("report metric uses different institution")
        self.asset_registry.principal(metric.institution_id, metric.owner_id)
        for source in metric.source_refs:
            asset = self.asset_registry.asset(source.institution_id, source.asset_id, source.asset_version)
            if asset.artifact_digest != source.asset_digest:
                raise GovernanceError("report metric source digest mismatch")
        transformation_digests = {item.artifact_digest for item in self.lineage_registry._transformations.values() if item.institution_id == metric.institution_id}
        if any(value not in transformation_digests for value in metric.transformation_digests):
            raise GovernanceError("report metric references unknown transformation evidence")
        quality_digests = {item.artifact_digest for item in self.quality_registry._rules.values() if item.institution_id == metric.institution_id}
        if any(value not in quality_digests for value in metric.quality_rule_digests):
            raise GovernanceError("report metric references unknown quality-rule evidence")
        key = (metric.institution_id, metric.metric_id, metric.metric_version)
        existing = self._metrics.get(key)
        if existing is not None:
            if existing.artifact_digest != metric.artifact_digest:
                raise GovernanceError("metric identity/version already exists with different content")
            return existing.artifact_digest
        history = tuple(sorted((item for (scope, current, _), item in self._metrics.items() if scope == metric.institution_id and current == metric.metric_id), key=lambda item: item.metric_version))
        expected = 1 if not history else history[-1].metric_version + 1
        if metric.metric_version != expected:
            raise GovernanceError(f"metric_version must be contiguous; expected version {expected}")
        self._metrics[key] = metric
        return metric.artifact_digest

    def metrics_for_report(self, report: GovernedReport) -> tuple[ReportMetricDefinition, ...]:
        latest: dict[str, ReportMetricDefinition] = {}
        for item in self._metrics.values():
            if item.institution_id == report.institution_id and item.report_digest == report.artifact_digest:
                current = latest.get(item.metric_id)
                if current is None or item.metric_version > current.metric_version:
                    latest[item.metric_id] = item
        return tuple(sorted(latest.values(), key=lambda item: item.metric_id))

    def assert_metric_current(self, metric: ReportMetricDefinition) -> None:
        report = self._report_by_digest(metric.report_digest)
        self._assert_report_current(report)
        current = {item.metric_id: item for item in self.metrics_for_report(report)}.get(metric.metric_id)
        if current is None or current.artifact_digest != metric.artifact_digest:
            raise GovernanceError("report metric definition is stale")
        for source in metric.source_refs:
            latest = self.asset_registry.latest_asset(source.institution_id, source.asset_id)
            if latest.asset_version != source.asset_version or latest.artifact_digest != source.asset_digest:
                raise GovernanceError("report metric source asset is stale")
        transformations = {item.artifact_digest for item in self.lineage_registry._transformations.values() if item.institution_id == metric.institution_id}
        if any(value not in transformations for value in metric.transformation_digests):
            raise GovernanceError("report metric transformation evidence is stale")
        rules = {item.artifact_digest for item in self.quality_registry._rules.values() if item.institution_id == metric.institution_id}
        if any(value not in rules for value in metric.quality_rule_digests):
            raise GovernanceError("report metric quality-rule evidence is stale")

    def register_observation(self, observation: ReportProductionObservation) -> str:
        report = self._report_by_digest(observation.report_digest)
        self._assert_report_current(report)
        if report.institution_id != observation.institution_id:
            raise GovernanceError("report observation uses different institution")
        self.asset_registry.system(observation.institution_id, observation.source_system_id)
        expected_basis = self._basis_digest(observation.institution_id, observation.report_digest)
        if observation.reporting_basis_digest != expected_basis:
            raise GovernanceError("report observation is stale for current reporting basis")
        key = (observation.institution_id, observation.observation_id)
        existing = self._observations.get(key)
        if existing is not None and existing.artifact_digest != observation.artifact_digest:
            raise GovernanceError("observation_id already exists with different content")
        self._observations.setdefault(key, observation)
        return observation.artifact_digest

    def reporting_basis_digest(self, report: GovernedReport) -> str:
        self._assert_report_current(report)
        metrics = self.metrics_for_report(report)
        if not metrics:
            raise GovernanceError("governed report has no metric definitions")
        for metric in metrics:
            self.assert_metric_current(metric)
        return self._basis_digest(report.institution_id, report.artifact_digest)

    def evaluate_report(self, report: GovernedReport, period_id: str, *, assessed_at: str) -> ReportAssuranceAssessment:
        self._assert_report_current(report)
        period_id = _text("period_id", period_id)
        assessed_at = _timestamp("assessed_at", assessed_at)
        metrics = self.metrics_for_report(report)
        if not metrics:
            basis = self._basis_digest(report.institution_id, report.artifact_digest)
            controls = tuple(
                ReportingControlAssessment(metric=item, state=ReportingMetricState.INCOMPLETE, observed_value=None, threshold_value=(report.minimum_completeness_basis_points if item is ReportingMetric.COMPLETENESS else report.maximum_reconciliation_variance_basis_points if item is ReportingMetric.RECONCILIATION else report.maximum_lateness_seconds), reason_code="metric_definition_missing")
                for item in ReportingMetric
            )
            assessment = ReportAssuranceAssessment(report.institution_id, report.artifact_digest, period_id, basis, None, (), controls, ReportingAssessmentState.INCOMPLETE, ("metric_definition_missing",), assessed_at)
            self._assessments[assessment.artifact_digest] = assessment
            return assessment
        for metric in metrics:
            self.assert_metric_current(metric)
        basis = self._basis_digest(report.institution_id, report.artifact_digest)
        candidates = tuple(item for item in self._observations.values() if item.institution_id == report.institution_id and item.report_digest == report.artifact_digest and item.period_id == period_id and _parse_time(item.recorded_at) <= _parse_time(assessed_at))
        if not candidates:
            controls = tuple(
                ReportingControlAssessment(metric=item, state=ReportingMetricState.INCOMPLETE, observed_value=None, threshold_value=(report.minimum_completeness_basis_points if item is ReportingMetric.COMPLETENESS else report.maximum_reconciliation_variance_basis_points if item is ReportingMetric.RECONCILIATION else report.maximum_lateness_seconds), reason_code="production_observation_missing")
                for item in ReportingMetric
            )
            assessment = ReportAssuranceAssessment(report.institution_id, report.artifact_digest, period_id, basis, None, tuple(item.artifact_digest for item in metrics), controls, ReportingAssessmentState.INCOMPLETE, ("production_observation_missing",), assessed_at)
            self._assessments[assessment.artifact_digest] = assessment
            return assessment
        latest_time = max(_parse_time(item.recorded_at) for item in candidates)
        latest = tuple(item for item in candidates if _parse_time(item.recorded_at) == latest_time)
        if len({item.artifact_digest for item in latest}) > 1:
            raise GovernanceError("conflicting latest report production observations fail closed")
        observation = latest[0]
        if observation.reporting_basis_digest != basis:
            raise GovernanceError("latest report observation is stale for current reporting basis")
        lateness = max(0, int((_parse_time(observation.produced_at) - _parse_time(observation.due_at)).total_seconds()))
        completeness = min(10_000, (observation.actual_record_count * 10_000) // observation.expected_record_count)
        values = {
            ReportingMetric.TIMELINESS: (lateness, report.maximum_lateness_seconds, lateness <= report.maximum_lateness_seconds),
            ReportingMetric.COMPLETENESS: (completeness, report.minimum_completeness_basis_points, completeness >= report.minimum_completeness_basis_points),
            ReportingMetric.RECONCILIATION: (observation.reconciliation_variance_basis_points, report.maximum_reconciliation_variance_basis_points, observation.reconciliation_variance_basis_points <= report.maximum_reconciliation_variance_basis_points),
        }
        controls = tuple(ReportingControlAssessment(metric=metric, state=ReportingMetricState.MET if met else ReportingMetricState.BREACHED, observed_value=value, threshold_value=threshold, reason_code="configured_control_satisfied" if met else "configured_control_breached") for metric, (value, threshold, met) in values.items())
        state = ReportingAssessmentState.BREACHED if any(item.state is ReportingMetricState.BREACHED for item in controls) else ReportingAssessmentState.MET
        assessment = ReportAssuranceAssessment(report.institution_id, report.artifact_digest, period_id, basis, observation.artifact_digest, tuple(item.artifact_digest for item in metrics), controls, state, (), assessed_at)
        self._assessments[assessment.artifact_digest] = assessment
        return assessment

    def assert_assessment_current(self, assessment: ReportAssuranceAssessment) -> None:
        report = self._report_by_digest(assessment.report_digest)
        current = self.evaluate_report(report, assessment.period_id, assessed_at=assessment.assessed_at)
        if current.artifact_digest != assessment.artifact_digest:
            raise GovernanceError("report assurance assessment is stale")

    def register_attestation(self, attestation: ReportOwnerAttestation) -> str:
        assessment = self._assessment(attestation.assessment_digest)
        self.assert_assessment_current(assessment)
        if assessment.institution_id != attestation.institution_id:
            raise GovernanceError("report attestation uses different institution")
        self.asset_registry.principal(attestation.institution_id, attestation.owner_id)
        report = self._report_by_digest(assessment.report_digest)
        if attestation.owner_id != report.owner_id:
            raise GovernanceError("report attestation must use the accountable report owner")
        if _parse_time(attestation.attested_at) < _parse_time(assessment.assessed_at):
            raise GovernanceError("report attestation cannot predate assessment")
        if attestation.decision is AttestationDecision.APPROVED and assessment.state is not ReportingAssessmentState.MET:
            raise GovernanceError("non-met report assessment cannot be approved")
        key = (attestation.institution_id, attestation.attestation_id)
        existing = self._attestations.get(key)
        if existing is not None and existing.artifact_digest != attestation.artifact_digest:
            raise GovernanceError("attestation_id already exists with different content")
        self._attestations.setdefault(key, attestation)
        return attestation.artifact_digest

    def create_finding(self, assessment: ReportAssuranceAssessment, *, finding_id: str, severity: ReportingFindingSeverity, owner_id: str, title: str, identified_at: str, evidence_digest: str) -> ReportingFinding:
        self.assert_assessment_current(assessment)
        if assessment.state is ReportingAssessmentState.MET:
            raise GovernanceError("met report assessment cannot create a reporting finding")
        self.asset_registry.principal(assessment.institution_id, owner_id)
        finding = ReportingFinding(assessment.institution_id, finding_id, assessment.artifact_digest, severity, owner_id, title, identified_at, evidence_digest)
        if _parse_time(finding.identified_at) < _parse_time(assessment.assessed_at):
            raise GovernanceError("reporting finding cannot predate assessment")
        key = (finding.institution_id, finding.finding_id)
        existing = self._findings.get(key)
        if existing is not None and existing.artifact_digest != finding.artifact_digest:
            raise GovernanceError("finding_id already exists with different content")
        self._findings.setdefault(key, finding)
        return finding

    def register_remediation(self, remediation: ReportingRemediationEvidence) -> str:
        finding = self._finding(remediation.finding_digest)
        if finding.institution_id != remediation.institution_id:
            raise GovernanceError("reporting remediation uses different institution")
        self.asset_registry.principal(remediation.institution_id, remediation.owner_id)
        if _parse_time(remediation.completed_at) < _parse_time(finding.identified_at):
            raise GovernanceError("reporting remediation cannot predate finding")
        key = (remediation.institution_id, remediation.remediation_id)
        existing = self._remediations.get(key)
        if existing is not None and existing.artifact_digest != remediation.artifact_digest:
            raise GovernanceError("remediation_id already exists with different content")
        self._remediations.setdefault(key, remediation)
        return remediation.artifact_digest

    def register_retest(self, retest: ReportingRetestEvidence) -> str:
        finding = self._finding(retest.finding_digest)
        remediation = self._remediation(retest.remediation_digest)
        if finding.institution_id != retest.institution_id or remediation.institution_id != retest.institution_id or remediation.finding_digest != finding.artifact_digest:
            raise GovernanceError("reporting retest lifecycle binding mismatch")
        self.asset_registry.principal(retest.institution_id, retest.reviewer_id)
        if _parse_time(retest.tested_at) < _parse_time(remediation.completed_at):
            raise GovernanceError("reporting retest cannot predate remediation")
        if finding.blocking and retest.reviewer_id == remediation.owner_id:
            raise GovernanceError("high/critical reporting finding requires independent retest")
        key = (retest.institution_id, retest.retest_id)
        existing = self._retests.get(key)
        if existing is not None and existing.artifact_digest != retest.artifact_digest:
            raise GovernanceError("retest_id already exists with different content")
        self._retests.setdefault(key, retest)
        return retest.artifact_digest

    def resolve_finding(self, finding: ReportingFinding, *, resolved_at: str) -> ReportingFindingResolution:
        registered = self._finding(finding.artifact_digest)
        resolved_at = _timestamp("resolved_at", resolved_at)
        remediations = tuple(item for item in self._remediations.values() if item.finding_digest == registered.artifact_digest)
        if not remediations:
            return ReportingFindingResolution(finding.institution_id, finding.artifact_digest, ReportingFindingStatus.OPEN, None, None, resolved_at)
        latest_time = max(_parse_time(item.completed_at) for item in remediations)
        latest = tuple(item for item in remediations if _parse_time(item.completed_at) == latest_time)
        if len({item.artifact_digest for item in latest}) > 1:
            raise GovernanceError("conflicting latest reporting remediation evidence fails closed")
        remediation = latest[0]
        retests = tuple(item for item in self._retests.values() if item.finding_digest == finding.artifact_digest and item.remediation_digest == remediation.artifact_digest)
        if not retests:
            return ReportingFindingResolution(finding.institution_id, finding.artifact_digest, ReportingFindingStatus.REMEDIATION_SUBMITTED, remediation.artifact_digest, None, resolved_at)
        latest_retest_time = max(_parse_time(item.tested_at) for item in retests)
        latest_retests = tuple(item for item in retests if _parse_time(item.tested_at) == latest_retest_time)
        if len({item.artifact_digest for item in latest_retests}) > 1:
            raise GovernanceError("conflicting latest reporting retest evidence fails closed")
        retest = latest_retests[0]
        status = ReportingFindingStatus.CLOSED if retest.outcome is ReportingRetestOutcome.PASSED else ReportingFindingStatus.RETEST_FAILED
        return ReportingFindingResolution(finding.institution_id, finding.artifact_digest, status, remediation.artifact_digest, retest.artifact_digest, resolved_at)

    def snapshot_digest(self, institution_id: str) -> str:
        self.asset_registry.snapshot_digest(institution_id)
        return digest_artifact({
            "institution_id": institution_id,
            "asset_registry_snapshot_digest": self.asset_registry.snapshot_digest(institution_id),
            "semantic_registry_snapshot_digest": self.semantic_registry.snapshot_digest(institution_id),
            "lineage_registry_snapshot_digest": self.lineage_registry.snapshot_digest(institution_id),
            "quality_registry_snapshot_digest": self.quality_registry.snapshot_digest(institution_id),
            "reports": sorted(item.artifact_digest for item in self._reports.values() if item.institution_id == institution_id),
            "metrics": sorted(item.artifact_digest for item in self._metrics.values() if item.institution_id == institution_id),
            "observations": sorted(item.artifact_digest for item in self._observations.values() if item.institution_id == institution_id),
            "assessments": sorted(item.artifact_digest for item in self._assessments.values() if item.institution_id == institution_id),
            "attestations": sorted(item.artifact_digest for item in self._attestations.values() if item.institution_id == institution_id),
            "findings": sorted(item.artifact_digest for item in self._findings.values() if item.institution_id == institution_id),
            "remediations": sorted(item.artifact_digest for item in self._remediations.values() if item.institution_id == institution_id),
            "retests": sorted(item.artifact_digest for item in self._retests.values() if item.institution_id == institution_id),
        })

    def _report_by_digest(self, digest: str) -> GovernedReport:
        for item in self._reports.values():
            if item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown governed report digest")

    def _assessment(self, digest: str) -> ReportAssuranceAssessment:
        try:
            return self._assessments[digest]
        except KeyError as exc:
            raise GovernanceError("unknown report assessment") from exc

    def _finding(self, digest: str) -> ReportingFinding:
        for item in self._findings.values():
            if item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown reporting finding")

    def _remediation(self, digest: str) -> ReportingRemediationEvidence:
        for item in self._remediations.values():
            if item.artifact_digest == digest:
                return item
        raise GovernanceError("unknown reporting remediation")
