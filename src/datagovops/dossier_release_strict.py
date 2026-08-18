from __future__ import annotations

from .dossier import DossierException, GovernanceDossier, dossier_document
from .dossier_release import GovernanceDossierBuilder as _ReleaseGovernanceDossierBuilder
from .dossier_verify import verify_dossier_document
from .models import GovernanceError


class GovernanceDossierBuilder(_ReleaseGovernanceDossierBuilder):
    """Final public v0.1 builder: fail closed on exception identity and self-verification."""

    def build(
        self,
        institution_id: str,
        *,
        generated_at: str,
        source_revision: str,
        quality_policy_id: str | None = None,
        control_policy_id: str | None = None,
        exceptions: tuple[DossierException, ...] = (),
    ) -> GovernanceDossier:
        if len({item.exception_id for item in exceptions}) != len(exceptions):
            raise GovernanceError("dossier exception identities must be unique")
        if len({item.artifact_digest for item in exceptions}) != len(exceptions):
            raise GovernanceError("dossier exception digests must be unique")
        dossier = super().build(
            institution_id,
            generated_at=generated_at,
            source_revision=source_revision,
            quality_policy_id=quality_policy_id,
            control_policy_id=control_policy_id,
            exceptions=exceptions,
        )
        verify_dossier_document(dossier_document(dossier))
        return dossier
