from __future__ import annotations

from .models import GovernanceError
from .reporting import ReportMetricDefinition, ReportingGovernanceRegistry as _ReportingGovernanceRegistry


class ReportingGovernanceRegistry(_ReportingGovernanceRegistry):
    """Public v0.2 reporting registry with strict latest-evidence currentness."""

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
