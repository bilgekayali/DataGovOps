from __future__ import annotations

from typing import Any

from .dossier import DossierState, DomainSnapshot, GovernanceDossier, _artifact, _parse_time
from .dossier_release_strict import GovernanceDossierBuilder as _V01Builder
from .models import GovernanceError, digest_artifact
from .reporting import AttestationDecision, ReportingAssessmentState, ReportingFindingStatus
from .reporting_strict import ReportingGovernanceRegistry


REPORTING_TYPES = {
    "reports": "GovernedReport",
    "metrics": "ReportMetricDefinition",
    "observations": "ReportProductionObservation",
    "assessments": "ReportAssuranceAssessment",
    "attestations": "ReportOwnerAttestation",
    "findings": "ReportingFinding",
    "remediations": "ReportingRemediationEvidence",
    "retests": "ReportingRetestEvidence",
}


def reporting_snapshot_digest(institution_id: str, artifacts, snapshots) -> str:
    by_domain = {item.domain: item.source_snapshot_digest for item in snapshots}
    payload = {
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": by_domain["inventory"],
        "semantic_registry_snapshot_digest": by_domain["semantic"],
        "lineage_registry_snapshot_digest": by_domain["lineage"],
        "quality_registry_snapshot_digest": by_domain["quality"],
    }
    items = list(artifacts)
    for key, artifact_type in REPORTING_TYPES.items():
        payload[key] = sorted(item.digest for item in items if item.artifact_type == artifact_type)
    return digest_artifact(payload)


class GovernanceDossierBuilder(_V01Builder):
    """v0.2 builder that appends reporting evidence after the v0.1 strict gate."""

    def __init__(self, *args: Any, reporting_registry: ReportingGovernanceRegistry | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if reporting_registry is not None:
            if not isinstance(reporting_registry, ReportingGovernanceRegistry):
                raise GovernanceError("dossier requires strict public ReportingGovernanceRegistry")
            if reporting_registry.asset_registry is not self.asset_registry:
                raise GovernanceError("reporting registry must use dossier asset registry")
            if reporting_registry.semantic_registry is not self.semantic_registry:
                raise GovernanceError("reporting registry must use dossier semantic registry")
            if reporting_registry.lineage_registry is not self.lineage_registry:
                raise GovernanceError("reporting registry must use dossier lineage registry")
            if reporting_registry.quality_registry is not self.quality_registry:
                raise GovernanceError("reporting registry must use dossier quality registry")
        self.reporting_registry = reporting_registry

    def _reporting_artifacts(self, institution_id: str):
        if self.reporting_registry is None:
            return ()
        artifacts = []
        for mapping in (
            self.reporting_registry._reports,
            self.reporting_registry._metrics,
            self.reporting_registry._observations,
            self.reporting_registry._assessments,
            self.reporting_registry._attestations,
            self.reporting_registry._findings,
            self.reporting_registry._remediations,
            self.reporting_registry._retests,
        ):
            artifacts.extend(
                _artifact("reporting", value)
                for value in mapping.values()
                if getattr(value, "institution_id", None) == institution_id
            )
        return tuple(
            sorted(
                artifacts,
                key=lambda item: (item.domain, item.artifact_type, item.artifact_id),
            )
        )

    def _reporting_findings(self, institution_id: str, generated_at: str) -> tuple[set[str], set[str]]:
        if self.reporting_registry is None:
            return set(), set()
        gaps: set[str] = set()
        revalidation: set[str] = set()
        latest_reports: dict[str, Any] = {}
        for report in self.reporting_registry._reports.values():
            if report.institution_id != institution_id:
                continue
            current = latest_reports.get(report.report_id)
            if current is None or report.report_version > current.report_version:
                latest_reports[report.report_id] = report
        if not latest_reports:
            gaps.add("reporting:no_reports_configured")
            return gaps, revalidation

        for report_id, report in sorted(latest_reports.items()):
            metrics = self.reporting_registry.metrics_for_report(report)
            if not metrics:
                gaps.add(f"reporting:no_metric_definitions:{report_id}")
            else:
                for metric in metrics:
                    try:
                        self.reporting_registry.assert_metric_current(metric)
                    except GovernanceError as exc:
                        revalidation.add(f"reporting:metric:{report_id}:{metric.metric_id}:{exc}")

            assessments = [
                item
                for item in self.reporting_registry._assessments.values()
                if item.institution_id == institution_id and item.report_digest == report.artifact_digest
            ]
            if not assessments:
                gaps.add(f"reporting:no_assessment:{report_id}")
                continue
            latest_by_period: dict[str, Any] = {}
            for assessment in assessments:
                current = latest_by_period.get(assessment.period_id)
                if current is None or _parse_time(assessment.assessed_at) > _parse_time(current.assessed_at):
                    latest_by_period[assessment.period_id] = assessment
            for period_id, assessment in sorted(latest_by_period.items()):
                try:
                    self.reporting_registry.assert_assessment_current(assessment)
                except GovernanceError as exc:
                    revalidation.add(f"reporting:assessment:{report_id}:{period_id}:{exc}")
                    continue
                if assessment.state is ReportingAssessmentState.BREACHED:
                    gaps.add(f"reporting:breached:{report_id}:{period_id}")
                elif assessment.state is ReportingAssessmentState.INCOMPLETE:
                    gaps.add(f"reporting:incomplete:{report_id}:{period_id}")

                attestations = [
                    item
                    for item in self.reporting_registry._attestations.values()
                    if item.institution_id == institution_id
                    and item.assessment_digest == assessment.artifact_digest
                    and _parse_time(item.attested_at) <= _parse_time(generated_at)
                ]
                if not attestations:
                    gaps.add(f"reporting:attestation_missing:{report_id}:{period_id}")
                else:
                    latest_time = max(_parse_time(item.attested_at) for item in attestations)
                    latest = tuple(item for item in attestations if _parse_time(item.attested_at) == latest_time)
                    if len({item.artifact_digest for item in latest}) > 1:
                        revalidation.add(f"reporting:attestation_conflict:{report_id}:{period_id}")
                    else:
                        decision = latest[0].decision
                        if decision is AttestationDecision.REJECTED:
                            gaps.add(f"reporting:attestation_rejected:{report_id}:{period_id}")
                        elif decision is AttestationDecision.ESCALATED:
                            gaps.add(f"reporting:attestation_escalated:{report_id}:{period_id}")

        for finding in sorted(
            (
                item
                for item in self.reporting_registry._findings.values()
                if item.institution_id == institution_id
            ),
            key=lambda item: item.finding_id,
        ):
            try:
                resolution = self.reporting_registry.resolve_finding(
                    finding,
                    resolved_at=generated_at,
                )
                if resolution.status is not ReportingFindingStatus.CLOSED:
                    gaps.add(
                        f"reporting:finding_open:{finding.finding_id}:{resolution.status.value}"
                    )
            except GovernanceError as exc:
                revalidation.add(f"reporting:finding:{finding.finding_id}:{exc}")
        return gaps, revalidation

    def build(self, institution_id: str, **kwargs: Any) -> GovernanceDossier:
        dossier = super().build(institution_id, **kwargs)
        if self.reporting_registry is None:
            return dossier

        reporting_artifacts = self._reporting_artifacts(institution_id)
        reporting_digest = reporting_snapshot_digest(
            institution_id,
            reporting_artifacts,
            dossier.domain_snapshots,
        )
        if reporting_digest != self.reporting_registry.snapshot_digest(institution_id):
            raise GovernanceError("embedded reporting artifacts do not reproduce reporting registry snapshot")
        snapshots = tuple(
            sorted(
                dossier.domain_snapshots
                + (
                    DomainSnapshot(
                        "reporting",
                        reporting_digest,
                        tuple(sorted(item.digest for item in reporting_artifacts)),
                    ),
                ),
                key=lambda item: item.domain,
            )
        )
        artifacts = tuple(
            sorted(
                dossier.artifacts + reporting_artifacts,
                key=lambda item: (item.domain, item.artifact_type, item.artifact_id),
            )
        )
        coverage = dict(dossier.coverage)
        if reporting_artifacts:
            coverage["reporting"] = len(reporting_artifacts)

        reporting_gaps, reporting_revalidation = self._reporting_findings(
            institution_id,
            dossier.generated_at,
        )
        findings = set(dossier.findings) | reporting_gaps | reporting_revalidation
        revalidation = set(dossier.revalidation_findings) | reporting_revalidation
        covered: set[str] = set()
        for exception in dossier.exceptions:
            if exception.artifact_digest in dossier.active_exception_digests:
                covered.update(exception.finding_codes)
        gaps = findings - revalidation
        uncovered = gaps - covered
        if revalidation:
            state = DossierState.REVALIDATION_REQUIRED
        elif uncovered:
            state = DossierState.WITH_GAPS
        elif gaps:
            state = DossierState.WITH_EXCEPTIONS
        else:
            state = DossierState.CURRENT

        return GovernanceDossier(
            schema_version=dossier.schema_version,
            release_version=dossier.release_version,
            institution_id=dossier.institution_id,
            generated_at=dossier.generated_at,
            source_revision=dossier.source_revision,
            state=state,
            findings=tuple(sorted(findings)),
            revalidation_findings=tuple(sorted(revalidation)),
            active_exception_digests=dossier.active_exception_digests,
            coverage=coverage,
            domain_snapshots=snapshots,
            artifacts=artifacts,
            exceptions=dossier.exceptions,
        )
