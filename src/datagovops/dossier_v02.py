from __future__ import annotations

from typing import Any

from .dossier import DomainSnapshot, GovernanceDossier, _artifact
from .dossier_release_strict import GovernanceDossierBuilder as _V01Builder
from .models import GovernanceError, digest_artifact
from .reporting import ReportingGovernanceRegistry


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
    """v0.2 builder that optionally packages reporting-governance state."""

    def __init__(self, *args: Any, reporting_registry: ReportingGovernanceRegistry | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if reporting_registry is not None:
            if reporting_registry.asset_registry is not self.asset_registry:
                raise GovernanceError("reporting registry must use dossier asset registry")
            if reporting_registry.semantic_registry is not self.semantic_registry:
                raise GovernanceError("reporting registry must use dossier semantic registry")
            if reporting_registry.lineage_registry is not self.lineage_registry:
                raise GovernanceError("reporting registry must use dossier lineage registry")
            if reporting_registry.quality_registry is not self.quality_registry:
                raise GovernanceError("reporting registry must use dossier quality registry")
        self.reporting_registry = reporting_registry

    def _collect_registry_artifacts(self, institution_id: str):
        artifacts = super()._collect_registry_artifacts(institution_id)
        if self.reporting_registry is None:
            return artifacts
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
        return artifacts

    def build(self, institution_id: str, **kwargs: Any) -> GovernanceDossier:
        dossier = super().build(institution_id, **kwargs)
        if self.reporting_registry is None:
            return dossier
        reporting_artifacts = tuple(item for item in dossier.artifacts if item.domain == "reporting")
        reporting_digest = reporting_snapshot_digest(
            institution_id,
            reporting_artifacts,
            dossier.domain_snapshots,
        )
        if reporting_digest != self.reporting_registry.snapshot_digest(institution_id):
            raise GovernanceError("embedded reporting artifacts do not reproduce reporting registry snapshot")
        snapshots = tuple(sorted(
            dossier.domain_snapshots + (
                DomainSnapshot(
                    "reporting",
                    reporting_digest,
                    tuple(sorted(item.digest for item in reporting_artifacts)),
                ),
            ),
            key=lambda item: item.domain,
        ))
        return GovernanceDossier(
            schema_version=dossier.schema_version,
            release_version=dossier.release_version,
            institution_id=dossier.institution_id,
            generated_at=dossier.generated_at,
            source_revision=dossier.source_revision,
            state=dossier.state,
            findings=dossier.findings,
            revalidation_findings=dossier.revalidation_findings,
            active_exception_digests=dossier.active_exception_digests,
            coverage=dossier.coverage,
            domain_snapshots=snapshots,
            artifacts=dossier.artifacts,
            exceptions=dossier.exceptions,
        )
