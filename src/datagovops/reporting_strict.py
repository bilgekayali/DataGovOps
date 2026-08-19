from __future__ import annotations

from dataclasses import dataclass

from .models import GovernanceError, _digest, _enum, _text, _timestamp, digest_artifact
from .reporting import (
    ReportMetricDefinition,
    ReportingAssessmentState,
    ReportingFinding,
    ReportingFindingResolution,
    ReportingGovernanceRegistry as _ReportingGovernanceRegistry,
    ReportingRetestOutcome,
    _parse_time,
)


@dataclass(frozen=True, slots=True)
class ReportingRetestEvidence:
    institution_id: str
    retest_id: str
    finding_digest: str
    remediation_digest: str
    reassessment_digest: str
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
        _digest("reassessment_digest", self.reassessment_digest)
        _enum("outcome", self.outcome, ReportingRetestOutcome)
        object.__setattr__(self, "tested_at", _timestamp("tested_at", self.tested_at))
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class ReportingGovernanceRegistry(_ReportingGovernanceRegistry):
    """Public v0.2 reporting registry with strict currentness and closure evidence."""

    def _basis_digest(self, institution_id: str, report_digest: str) -> str:
        latest: dict[str, ReportMetricDefinition] = {}
        for item in self._metrics.values():
            if item.institution_id != institution_id or item.report_digest != report_digest:
                continue
            current = latest.get(item.metric_id)
            if current is None or item.metric_version > current.metric_version:
                latest[item.metric_id] = item
        return digest_artifact({
            "institution_id": institution_id,
            "report_digest": report_digest,
            "metric_definition_digests": sorted(item.artifact_digest for item in latest.values()),
            "asset_registry_snapshot_digest": self.asset_registry.snapshot_digest(institution_id),
            "semantic_registry_snapshot_digest": self.semantic_registry.snapshot_digest(institution_id),
            "lineage_registry_snapshot_digest": self.lineage_registry.snapshot_digest(institution_id),
            "quality_registry_snapshot_digest": self.quality_registry.snapshot_digest(institution_id),
        })

    def assert_metric_current(self, metric: ReportMetricDefinition) -> None:
        super().assert_metric_current(metric)
        transformations = {
            item.artifact_digest: item
            for item in self.lineage_registry._transformations.values()
            if item.institution_id == metric.institution_id
        }
        for digest in metric.transformation_digests:
            transformation = transformations.get(digest)
            if transformation is None:
                raise GovernanceError("report metric transformation evidence is stale")
            latest = self.lineage_registry.latest_transformation(
                metric.institution_id,
                transformation.transformation_id,
            )
            if latest.artifact_digest != digest:
                raise GovernanceError("report metric transformation evidence is stale for latest version")

        rules = {
            item.artifact_digest: item
            for item in self.quality_registry._rules.values()
            if item.institution_id == metric.institution_id
        }
        for digest in metric.quality_rule_digests:
            rule = rules.get(digest)
            if rule is None:
                raise GovernanceError("report metric quality-rule evidence is stale")
            latest = self.quality_registry.latest_rule(metric.institution_id, rule.rule_id)
            if latest.artifact_digest != digest:
                raise GovernanceError("report metric quality-rule evidence is stale for latest version")

    def register_retest(self, retest: ReportingRetestEvidence) -> str:
        if not isinstance(retest, ReportingRetestEvidence):
            raise GovernanceError("public reporting retest requires reassessment-bound evidence")
        finding = self._finding(retest.finding_digest)
        remediation = self._remediation(retest.remediation_digest)
        reassessment = self._assessment(retest.reassessment_digest)
        original_assessment = self._assessment(finding.assessment_digest)
        self.assert_assessment_current(reassessment)
        if (
            finding.institution_id != retest.institution_id
            or remediation.institution_id != retest.institution_id
            or reassessment.institution_id != retest.institution_id
        ):
            raise GovernanceError("reporting retest uses different institution")
        if remediation.finding_digest != finding.artifact_digest:
            raise GovernanceError("reporting retest remediation is bound to different finding")
        if (
            reassessment.report_digest != original_assessment.report_digest
            or reassessment.period_id != original_assessment.period_id
        ):
            raise GovernanceError("reporting retest reassessment must cover the same report and period")
        if _parse_time(reassessment.assessed_at) < _parse_time(remediation.completed_at):
            raise GovernanceError("reporting retest reassessment cannot predate remediation")
        if _parse_time(retest.tested_at) < _parse_time(reassessment.assessed_at):
            raise GovernanceError("reporting retest cannot predate bound reassessment")
        expected = (
            ReportingRetestOutcome.PASSED
            if reassessment.state is ReportingAssessmentState.MET
            else ReportingRetestOutcome.FAILED
        )
        if retest.outcome is not expected:
            raise GovernanceError("reporting retest outcome must match bound reassessment state")
        return super().register_retest(retest)

    def resolve_finding(
        self,
        finding: ReportingFinding,
        *,
        resolved_at: str,
    ) -> ReportingFindingResolution:
        resolution = super().resolve_finding(finding, resolved_at=resolved_at)
        latest_time = _parse_time(finding.identified_at)
        if resolution.remediation_digest is not None:
            remediation = self._remediation(resolution.remediation_digest)
            latest_time = max(latest_time, _parse_time(remediation.completed_at))
        if resolution.retest_digest is not None:
            retest = next(
                (
                    item
                    for item in self._retests.values()
                    if item.artifact_digest == resolution.retest_digest
                ),
                None,
            )
            if not isinstance(retest, ReportingRetestEvidence):
                raise GovernanceError("reporting finding resolution requires reassessment-bound retest evidence")
            reassessment = self._assessment(retest.reassessment_digest)
            latest_time = max(
                latest_time,
                _parse_time(reassessment.assessed_at),
                _parse_time(retest.tested_at),
            )
        if _parse_time(resolution.resolved_at) < latest_time:
            raise GovernanceError("reporting finding resolution cannot predate lifecycle evidence")
        return resolution
