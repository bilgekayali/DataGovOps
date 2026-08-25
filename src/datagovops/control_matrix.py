from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import GovernanceError, _bool, _digest, _enum, _positive_int, _text, digest_artifact

CONTROL_DEFINITION_SCHEMA_VERSION = "datagovops.control-definition.v1"
CONTROL_EVIDENCE_REFERENCE_SCHEMA_VERSION = "datagovops.control-evidence-reference.v1"
CONTROL_ASSESSMENT_SCHEMA_VERSION = "datagovops.control-assessment.v1"
CONTROL_EVIDENCE_MATRIX_SCHEMA_VERSION = "datagovops.control-evidence-matrix.v1"


class ControlDomain(str, Enum):
    DATA_GOVERNANCE = "data_governance"
    BCBS239_ASSURANCE = "bcbs239_assurance"
    PRIVACY_SECURITY = "privacy_security"
    RECOVERY_RESILIENCE = "recovery_resilience"
    DEPLOYMENT_RUNTIME = "deployment_runtime"
    RELEASE_INTEGRITY = "release_integrity"


class EvidenceSourceBoundary(str, Enum):
    BCBS239 = "bcbs239"
    ACCESS_RETENTION_PRIVACY = "access_retention_privacy"
    SECURITY = "security"
    RECOVERY = "recovery"
    DEPLOYMENT = "deployment"
    RELEASE_EVIDENCE = "release_evidence"
    GOVERNANCE_DOSSIER = "governance_dossier"
    EXTERNAL = "external"


class ControlAssessmentState(str, Enum):
    REPRESENTED = "represented"
    GAP = "gap"
    REVALIDATION_REQUIRED = "revalidation_required"


class MatrixState(str, Enum):
    REPRESENTED = "represented"
    WITH_GAPS = "with_gaps"
    REVALIDATION_REQUIRED = "revalidation_required"


def _timestamp(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceError(f"{name} must be a non-negative integer timestamp")
    return value


def _sorted_unique_texts(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise GovernanceError(f"{name} must be a tuple")
    normalized = tuple(_text(name, value, limit=512) for value in values)
    if not allow_empty and not normalized:
        raise GovernanceError(f"{name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise GovernanceError(f"{name} must contain unique values")
    return tuple(sorted(normalized))


def _sorted_unique_digests(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise GovernanceError(f"{name} must be a tuple")
    for value in values:
        _digest(name, value)
    if len(values) != len(set(values)):
        raise GovernanceError(f"{name} must contain unique digests")
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class FrameworkReference:
    framework: str
    reference: str
    mapping_rationale: str
    applicability_determined: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "framework", _text("framework", self.framework, limit=256))
        object.__setattr__(self, "reference", _text("reference", self.reference, limit=512))
        object.__setattr__(self, "mapping_rationale", _text("mapping_rationale", self.mapping_rationale, limit=2048))
        if _bool("applicability_determined", self.applicability_determined):
            raise GovernanceError("framework reference does not determine regulatory applicability")


@dataclass(frozen=True, slots=True)
class EvidenceRequirement:
    evidence_type: str
    accepted_sources: tuple[EvidenceSourceBoundary, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_type", _text("evidence_type", self.evidence_type, limit=256))
        if not isinstance(self.accepted_sources, tuple) or not self.accepted_sources:
            raise GovernanceError("accepted_sources must be a non-empty tuple")
        for value in self.accepted_sources:
            _enum("accepted_source", value, EvidenceSourceBoundary)
        if len(self.accepted_sources) != len(set(self.accepted_sources)):
            raise GovernanceError("accepted_sources must be unique")
        object.__setattr__(self, "accepted_sources", tuple(sorted(self.accepted_sources, key=lambda item: item.value)))


@dataclass(frozen=True, slots=True)
class ControlDefinition:
    institution_id: str
    control_id: str
    control_version: int
    title: str
    domain: ControlDomain
    owner_id: str
    objective: str
    evidence_requirements: tuple[EvidenceRequirement, ...]
    framework_references: tuple[FrameworkReference, ...]
    registered_at: int
    framework_applicability_determined: bool = False
    legal_compliance_determined: bool = False
    schema_version: str = CONTROL_DEFINITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in ("institution_id", "control_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=256))
        object.__setattr__(self, "title", _text("title", self.title, limit=512))
        object.__setattr__(self, "objective", _text("objective", self.objective, limit=2048))
        _positive_int("control_version", self.control_version)
        _enum("domain", self.domain, ControlDomain)
        if not isinstance(self.evidence_requirements, tuple) or not self.evidence_requirements:
            raise GovernanceError("evidence_requirements must be a non-empty tuple")
        if any(not isinstance(item, EvidenceRequirement) for item in self.evidence_requirements):
            raise GovernanceError("evidence_requirements contains unsupported values")
        requirement_types = [item.evidence_type for item in self.evidence_requirements]
        if len(requirement_types) != len(set(requirement_types)):
            raise GovernanceError("evidence requirement types must be unique")
        object.__setattr__(
            self,
            "evidence_requirements",
            tuple(sorted(self.evidence_requirements, key=lambda item: item.evidence_type)),
        )
        if not isinstance(self.framework_references, tuple):
            raise GovernanceError("framework_references must be a tuple")
        if any(not isinstance(item, FrameworkReference) for item in self.framework_references):
            raise GovernanceError("framework_references contains unsupported values")
        mapping_keys = [(item.framework, item.reference) for item in self.framework_references]
        if len(mapping_keys) != len(set(mapping_keys)):
            raise GovernanceError("framework references must be unique")
        object.__setattr__(
            self,
            "framework_references",
            tuple(sorted(self.framework_references, key=lambda item: (item.framework, item.reference))),
        )
        _timestamp("registered_at", self.registered_at)
        if _bool("framework_applicability_determined", self.framework_applicability_determined):
            raise GovernanceError("control definition does not determine framework applicability")
        if _bool("legal_compliance_determined", self.legal_compliance_determined):
            raise GovernanceError("control definition does not determine legal compliance")
        if self.schema_version != CONTROL_DEFINITION_SCHEMA_VERSION:
            raise GovernanceError("unsupported control-definition schema version")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ControlEvidenceReference:
    institution_id: str
    evidence_id: str
    control_digest: str
    evidence_type: str
    source_boundary: EvidenceSourceBoundary
    artifact_type: str
    source_artifact_digest: str
    source_snapshot_digest: str
    observed_at: int
    revalidate_after: int
    verifier_id: str
    verification_evidence_digest: str
    evidence_effectiveness_determined: bool = False
    legal_compliance_determined: bool = False
    schema_version: str = CONTROL_EVIDENCE_REFERENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in ("institution_id", "evidence_id", "evidence_type", "artifact_type", "verifier_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=512))
        _digest("control_digest", self.control_digest)
        _enum("source_boundary", self.source_boundary, EvidenceSourceBoundary)
        for field in ("source_artifact_digest", "source_snapshot_digest", "verification_evidence_digest"):
            _digest(field, getattr(self, field))
        _timestamp("observed_at", self.observed_at)
        _timestamp("revalidate_after", self.revalidate_after)
        if self.revalidate_after < self.observed_at:
            raise GovernanceError("revalidate_after cannot predate observed_at")
        if _bool("evidence_effectiveness_determined", self.evidence_effectiveness_determined):
            raise GovernanceError("evidence reference cannot determine control effectiveness")
        if _bool("legal_compliance_determined", self.legal_compliance_determined):
            raise GovernanceError("evidence reference cannot determine legal compliance")
        if self.schema_version != CONTROL_EVIDENCE_REFERENCE_SCHEMA_VERSION:
            raise GovernanceError("unsupported control-evidence-reference schema version")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ControlAssessment:
    institution_id: str
    control_digest: str
    evidence_reference_digests: tuple[str, ...]
    represented_evidence_types: tuple[str, ...]
    missing_evidence_types: tuple[str, ...]
    stale_evidence_types: tuple[str, ...]
    state: ControlAssessmentState
    assessed_at: int
    requires_human_review: bool = True
    framework_applicability_determined: bool = False
    control_effectiveness_determined: bool = False
    legal_compliance_determined: bool = False
    regulatory_compliance_determined: bool = False
    schema_version: str = CONTROL_ASSESSMENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id, limit=256))
        _digest("control_digest", self.control_digest)
        object.__setattr__(
            self,
            "evidence_reference_digests",
            _sorted_unique_digests("evidence_reference_digest", self.evidence_reference_digests),
        )
        for field in ("represented_evidence_types", "missing_evidence_types", "stale_evidence_types"):
            object.__setattr__(self, field, _sorted_unique_texts(field, getattr(self, field), allow_empty=True))
        represented = set(self.represented_evidence_types)
        missing = set(self.missing_evidence_types)
        stale = set(self.stale_evidence_types)
        if represented & missing or represented & stale or missing & stale:
            raise GovernanceError("control assessment evidence-type states must be disjoint")
        if len(self.evidence_reference_digests) != len(represented) + len(stale):
            raise GovernanceError("control assessment evidence-reference count is inconsistent")
        _enum("state", self.state, ControlAssessmentState)
        expected = ControlAssessmentState.REPRESENTED
        if stale:
            expected = ControlAssessmentState.REVALIDATION_REQUIRED
        elif missing:
            expected = ControlAssessmentState.GAP
        if self.state is not expected:
            raise GovernanceError("control assessment state is inconsistent with evidence currentness")
        _timestamp("assessed_at", self.assessed_at)
        if _bool("requires_human_review", self.requires_human_review) is not True:
            raise GovernanceError("control assessment must require human review")
        for field in (
            "framework_applicability_determined",
            "control_effectiveness_determined",
            "legal_compliance_determined",
            "regulatory_compliance_determined",
        ):
            if _bool(field, getattr(self, field)):
                raise GovernanceError(f"control assessment cannot set {field}=true")
        if self.schema_version != CONTROL_ASSESSMENT_SCHEMA_VERSION:
            raise GovernanceError("unsupported control-assessment schema version")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ControlMatrixRow:
    control_id: str
    control_version: int
    domain: ControlDomain
    control_digest: str
    assessment_digest: str
    state: ControlAssessmentState
    evidence_reference_digests: tuple[str, ...]
    missing_evidence_types: tuple[str, ...]
    stale_evidence_types: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "control_id", _text("control_id", self.control_id, limit=256))
        _positive_int("control_version", self.control_version)
        _enum("domain", self.domain, ControlDomain)
        _digest("control_digest", self.control_digest)
        _digest("assessment_digest", self.assessment_digest)
        _enum("state", self.state, ControlAssessmentState)
        object.__setattr__(
            self,
            "evidence_reference_digests",
            _sorted_unique_digests("evidence_reference_digest", self.evidence_reference_digests),
        )
        object.__setattr__(self, "missing_evidence_types", _sorted_unique_texts("missing_evidence_types", self.missing_evidence_types, allow_empty=True))
        object.__setattr__(self, "stale_evidence_types", _sorted_unique_texts("stale_evidence_types", self.stale_evidence_types, allow_empty=True))


@dataclass(frozen=True, slots=True)
class ControlEvidenceMatrix:
    institution_id: str
    matrix_id: str
    matrix_version: int
    rows: tuple[ControlMatrixRow, ...]
    represented_control_count: int
    gap_control_count: int
    revalidation_required_control_count: int
    state: MatrixState
    generated_at: int
    requires_human_review: bool = True
    automated_compliance_scoring_enabled: bool = False
    framework_applicability_determined: bool = False
    control_effectiveness_determined: bool = False
    legal_compliance_determined: bool = False
    regulatory_compliance_determined: bool = False
    supervisory_acceptance_determined: bool = False
    schema_version: str = CONTROL_EVIDENCE_MATRIX_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in ("institution_id", "matrix_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=256))
        _positive_int("matrix_version", self.matrix_version)
        if not isinstance(self.rows, tuple) or not self.rows:
            raise GovernanceError("matrix rows must be a non-empty tuple")
        if any(not isinstance(row, ControlMatrixRow) for row in self.rows):
            raise GovernanceError("matrix rows contain unsupported values")
        ids = [row.control_id for row in self.rows]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise GovernanceError("matrix rows must be sorted and unique by control_id")
        for field in ("represented_control_count", "gap_control_count", "revalidation_required_control_count"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise GovernanceError(f"{field} must be a non-negative integer")
        represented = sum(row.state is ControlAssessmentState.REPRESENTED for row in self.rows)
        gaps = sum(row.state is ControlAssessmentState.GAP for row in self.rows)
        stale = sum(row.state is ControlAssessmentState.REVALIDATION_REQUIRED for row in self.rows)
        if (represented, gaps, stale) != (
            self.represented_control_count,
            self.gap_control_count,
            self.revalidation_required_control_count,
        ):
            raise GovernanceError("matrix control-state counts are inconsistent")
        _enum("state", self.state, MatrixState)
        expected = MatrixState.REPRESENTED
        if stale:
            expected = MatrixState.REVALIDATION_REQUIRED
        elif gaps:
            expected = MatrixState.WITH_GAPS
        if self.state is not expected:
            raise GovernanceError("matrix state is inconsistent with control rows")
        _timestamp("generated_at", self.generated_at)
        if _bool("requires_human_review", self.requires_human_review) is not True:
            raise GovernanceError("control/evidence matrix must require human review")
        if _bool("automated_compliance_scoring_enabled", self.automated_compliance_scoring_enabled):
            raise GovernanceError("automated compliance scoring is not supported")
        for field in (
            "framework_applicability_determined",
            "control_effectiveness_determined",
            "legal_compliance_determined",
            "regulatory_compliance_determined",
            "supervisory_acceptance_determined",
        ):
            if _bool(field, getattr(self, field)):
                raise GovernanceError(f"control/evidence matrix cannot set {field}=true")
        if self.schema_version != CONTROL_EVIDENCE_MATRIX_SCHEMA_VERSION:
            raise GovernanceError("unsupported control-evidence-matrix schema version")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class ControlEvidenceRegistry:
    """Versioned institution-owned controls with exact, currentness-aware evidence references."""

    def __init__(self) -> None:
        self._controls: dict[tuple[str, str, int], ControlDefinition] = {}
        self._evidence: dict[tuple[str, str], ControlEvidenceReference] = {}

    def register_control(self, control: ControlDefinition) -> str:
        key = (control.institution_id, control.control_id, control.control_version)
        existing = self._controls.get(key)
        if existing is not None:
            if existing.artifact_digest != control.artifact_digest:
                raise GovernanceError("control identity/version is already registered with different content")
            return existing.artifact_digest
        history = self.control_history(control.institution_id, control.control_id)
        expected = 1 if not history else history[-1].control_version + 1
        if control.control_version != expected:
            raise GovernanceError(f"control_version must be contiguous; expected version {expected}")
        self._controls[key] = control
        return control.artifact_digest

    def control_history(self, institution_id: str, control_id: str) -> tuple[ControlDefinition, ...]:
        return tuple(
            sorted(
                (
                    control
                    for (scope, current_id, _), control in self._controls.items()
                    if scope == institution_id and current_id == control_id
                ),
                key=lambda item: item.control_version,
            )
        )

    def latest_control(self, institution_id: str, control_id: str) -> ControlDefinition:
        history = self.control_history(institution_id, control_id)
        if not history:
            raise GovernanceError("unknown control")
        return history[-1]

    def _control_by_digest(self, institution_id: str, control_digest: str) -> ControlDefinition:
        _digest("control_digest", control_digest)
        matches = [
            control
            for (scope, _, _), control in self._controls.items()
            if scope == institution_id and control.artifact_digest == control_digest
        ]
        if len(matches) != 1:
            raise GovernanceError("control digest must resolve exactly once within institution")
        return matches[0]

    def register_evidence(self, evidence: ControlEvidenceReference) -> str:
        control = self._control_by_digest(evidence.institution_id, evidence.control_digest)
        requirements = {item.evidence_type: item for item in control.evidence_requirements}
        requirement = requirements.get(evidence.evidence_type)
        if requirement is None:
            raise GovernanceError("evidence type is not declared by referenced control")
        if evidence.source_boundary not in requirement.accepted_sources:
            raise GovernanceError("evidence source boundary is not accepted by referenced control")
        key = (evidence.institution_id, evidence.evidence_id)
        existing = self._evidence.get(key)
        if existing is not None:
            if existing.artifact_digest != evidence.artifact_digest:
                raise GovernanceError("evidence_id is already registered with different content")
            return existing.artifact_digest
        self._evidence[key] = evidence
        return evidence.artifact_digest

    def evidence_for_control(
        self,
        institution_id: str,
        control_digest: str,
        *,
        evidence_type: str | None = None,
    ) -> tuple[ControlEvidenceReference, ...]:
        self._control_by_digest(institution_id, control_digest)
        if evidence_type is not None:
            evidence_type = _text("evidence_type", evidence_type, limit=256)
        return tuple(
            sorted(
                (
                    item
                    for (scope, _), item in self._evidence.items()
                    if scope == institution_id
                    and item.control_digest == control_digest
                    and (evidence_type is None or item.evidence_type == evidence_type)
                ),
                key=lambda item: (item.evidence_type, item.observed_at, item.evidence_id),
            )
        )

    def assess_control(self, institution_id: str, control_id: str, *, assessed_at: int) -> ControlAssessment:
        _timestamp("assessed_at", assessed_at)
        control = self.latest_control(institution_id, control_id)
        reference_digests: list[str] = []
        represented: list[str] = []
        missing: list[str] = []
        stale: list[str] = []
        for requirement in control.evidence_requirements:
            candidates = self.evidence_for_control(
                institution_id,
                control.artifact_digest,
                evidence_type=requirement.evidence_type,
            )
            if not candidates:
                missing.append(requirement.evidence_type)
                continue
            latest_observed_at = max(item.observed_at for item in candidates)
            latest = [item for item in candidates if item.observed_at == latest_observed_at]
            if len(latest) != 1:
                raise GovernanceError("ambiguous latest control evidence fails closed")
            selected = latest[0]
            reference_digests.append(selected.artifact_digest)
            if assessed_at > selected.revalidate_after:
                stale.append(requirement.evidence_type)
            else:
                represented.append(requirement.evidence_type)
        state = ControlAssessmentState.REPRESENTED
        if stale:
            state = ControlAssessmentState.REVALIDATION_REQUIRED
        elif missing:
            state = ControlAssessmentState.GAP
        return ControlAssessment(
            institution_id=institution_id,
            control_digest=control.artifact_digest,
            evidence_reference_digests=tuple(reference_digests),
            represented_evidence_types=tuple(represented),
            missing_evidence_types=tuple(missing),
            stale_evidence_types=tuple(stale),
            state=state,
            assessed_at=assessed_at,
        )

    def build_matrix(
        self,
        *,
        institution_id: str,
        matrix_id: str,
        matrix_version: int,
        control_ids: tuple[str, ...],
        assessed_at: int,
    ) -> ControlEvidenceMatrix:
        _positive_int("matrix_version", matrix_version)
        _timestamp("assessed_at", assessed_at)
        normalized_ids = _sorted_unique_texts("control_ids", control_ids)
        rows: list[ControlMatrixRow] = []
        for control_id in normalized_ids:
            control = self.latest_control(institution_id, control_id)
            assessment = self.assess_control(institution_id, control_id, assessed_at=assessed_at)
            rows.append(
                ControlMatrixRow(
                    control_id=control.control_id,
                    control_version=control.control_version,
                    domain=control.domain,
                    control_digest=control.artifact_digest,
                    assessment_digest=assessment.artifact_digest,
                    state=assessment.state,
                    evidence_reference_digests=assessment.evidence_reference_digests,
                    missing_evidence_types=assessment.missing_evidence_types,
                    stale_evidence_types=assessment.stale_evidence_types,
                )
            )
        rows_tuple = tuple(sorted(rows, key=lambda row: row.control_id))
        represented = sum(row.state is ControlAssessmentState.REPRESENTED for row in rows_tuple)
        gaps = sum(row.state is ControlAssessmentState.GAP for row in rows_tuple)
        stale = sum(row.state is ControlAssessmentState.REVALIDATION_REQUIRED for row in rows_tuple)
        state = MatrixState.REPRESENTED
        if stale:
            state = MatrixState.REVALIDATION_REQUIRED
        elif gaps:
            state = MatrixState.WITH_GAPS
        return ControlEvidenceMatrix(
            institution_id=institution_id,
            matrix_id=matrix_id,
            matrix_version=matrix_version,
            rows=rows_tuple,
            represented_control_count=represented,
            gap_control_count=gaps,
            revalidation_required_control_count=stale,
            state=state,
            generated_at=assessed_at,
        )
