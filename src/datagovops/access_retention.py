from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .models import (
    GovernanceError,
    _bool,
    _digest,
    _enum,
    _optional_text,
    _positive_int,
    _text,
    _timestamp,
    digest_artifact,
)
from .registry import DataAssetRegistry
from .semantic import AssetPurposeBinding, SemanticGovernanceRegistry


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _country_code(name: str, value: str) -> str:
    value = _text(name, value, limit=2).upper()
    if len(value) != 2 or not value.isalpha():
        raise GovernanceError(f"{name} must be a two-letter country code")
    return value


def _string_tuple(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise GovernanceError(f"{name} must be a tuple")
    normalized = tuple(_text(name, value) for value in values)
    if not allow_empty and not normalized:
        raise GovernanceError(f"{name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise GovernanceError(f"{name} must contain unique values")
    return normalized


def _digest_tuple(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise GovernanceError(f"{name} must be a tuple")
    if len(set(values)) != len(values):
        raise GovernanceError(f"{name} must contain unique digests")
    for value in values:
        _digest(name, value)
    return values


class AccessSubjectKind(str, Enum):
    PRINCIPAL = "principal"
    ROLE = "role"


class AccessApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class DeletionEligibilityState(str, Enum):
    ELIGIBLE = "eligible"
    NOT_DUE = "not_due"
    BLOCKED_BY_LEGAL_HOLD = "blocked_by_legal_hold"


class ObligationCategory(str, Enum):
    PRIVACY = "privacy"
    SECURITY = "security"
    DATA_RESIDENCY = "data_residency"
    CROSS_BORDER = "cross_border"
    OTHER = "other"


class ObligationMappingStatus(str, Enum):
    MAPPED = "mapped"
    EXPLICITLY_NOT_MAPPED = "explicitly_not_mapped"
    REVIEW_REQUIRED = "review_required"


class DataLocationKind(str, Enum):
    STORAGE = "storage"
    PROCESSING = "processing"
    BACKUP = "backup"
    TRANSFER_DESTINATION = "transfer_destination"
    OTHER = "other"


class GovernanceGapCode(str, Enum):
    STALE_ACCESS_GRANT = "stale_access_grant"
    MISSING_RETENTION_SCHEDULE = "missing_retention_schedule"
    STALE_RETENTION_SCHEDULE = "stale_retention_schedule"
    MISSING_OBLIGATION_MAPPING = "missing_obligation_mapping"
    STALE_OBLIGATION_MAPPING = "stale_obligation_mapping"
    MISSING_LOCATION_EVIDENCE = "missing_location_evidence"
    STALE_LOCATION_EVIDENCE = "stale_location_evidence"


@dataclass(frozen=True, slots=True)
class AccessRole:
    institution_id: str
    role_id: str
    role_version: int
    name: str
    owner_id: str
    member_principal_ids: tuple[str, ...]
    permissions: tuple[str, ...]
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.access-role.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "role_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        object.__setattr__(self, "name", _text("name", self.name, limit=512))
        _positive_int("role_version", self.role_version)
        object.__setattr__(self, "member_principal_ids", _string_tuple("member_principal_ids", self.member_principal_ids))
        object.__setattr__(self, "permissions", _string_tuple("permissions", self.permissions))
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class AccessPurposeApproval:
    institution_id: str
    approval_id: str
    subject_kind: AccessSubjectKind
    subject_id: str
    subject_role_version: int | None
    subject_digest: str
    asset_id: str
    asset_version: int
    asset_digest: str
    purpose_id: str
    purpose_version: int
    purpose_digest: str
    purpose_binding_id: str
    purpose_binding_digest: str
    decision: AccessApprovalDecision
    reviewer_id: str
    rationale: str
    evidence_digest: str
    decided_at: str
    schema_version: str = "datagovops.access-purpose-approval.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "approval_id",
            "subject_id",
            "asset_id",
            "purpose_id",
            "purpose_binding_id",
            "reviewer_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _enum("subject_kind", self.subject_kind, AccessSubjectKind)
        _enum("decision", self.decision, AccessApprovalDecision)
        if self.subject_kind is AccessSubjectKind.PRINCIPAL:
            if self.subject_role_version is not None:
                raise GovernanceError("principal access subject cannot include subject_role_version")
        else:
            if self.subject_role_version is None:
                raise GovernanceError("role access subject requires subject_role_version")
            _positive_int("subject_role_version", self.subject_role_version)
        _positive_int("asset_version", self.asset_version)
        _positive_int("purpose_version", self.purpose_version)
        for field in (
            "subject_digest",
            "asset_digest",
            "purpose_digest",
            "purpose_binding_digest",
            "evidence_digest",
        ):
            _digest(field, getattr(self, field))
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        object.__setattr__(self, "decided_at", _timestamp("decided_at", self.decided_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class AccessGrant:
    institution_id: str
    grant_id: str
    approval_digest: str
    subject_kind: AccessSubjectKind
    subject_id: str
    subject_role_version: int | None
    subject_digest: str
    asset_id: str
    asset_version: int
    asset_digest: str
    purpose_id: str
    purpose_version: int
    purpose_digest: str
    permissions: tuple[str, ...]
    granted_by_id: str
    valid_from: str
    expires_at: str | None
    evidence_digest: str
    granted_at: str
    schema_version: str = "datagovops.access-grant.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "grant_id",
            "subject_id",
            "asset_id",
            "purpose_id",
            "granted_by_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _enum("subject_kind", self.subject_kind, AccessSubjectKind)
        if self.subject_kind is AccessSubjectKind.PRINCIPAL:
            if self.subject_role_version is not None:
                raise GovernanceError("principal access grant cannot include subject_role_version")
        else:
            if self.subject_role_version is None:
                raise GovernanceError("role access grant requires subject_role_version")
            _positive_int("subject_role_version", self.subject_role_version)
        _positive_int("asset_version", self.asset_version)
        _positive_int("purpose_version", self.purpose_version)
        for field in ("approval_digest", "subject_digest", "asset_digest", "purpose_digest", "evidence_digest"):
            _digest(field, getattr(self, field))
        object.__setattr__(self, "permissions", _string_tuple("permissions", self.permissions))
        object.__setattr__(self, "valid_from", _timestamp("valid_from", self.valid_from))
        if self.expires_at is not None:
            object.__setattr__(self, "expires_at", _timestamp("expires_at", self.expires_at))
            if _parse_timestamp(self.expires_at) <= _parse_timestamp(self.valid_from):
                raise GovernanceError("expires_at must be after valid_from")
        object.__setattr__(self, "granted_at", _timestamp("granted_at", self.granted_at))
        if _parse_timestamp(self.valid_from) < _parse_timestamp(self.granted_at):
            raise GovernanceError("valid_from cannot precede granted_at")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class RetentionSchedule:
    institution_id: str
    schedule_id: str
    schedule_version: int
    asset_id: str
    asset_version: int
    asset_digest: str
    owner_id: str
    retention_trigger_at: str
    retention_days: int
    rationale: str
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.retention-schedule.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "schedule_id", "asset_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("schedule_version", self.schedule_version)
        _positive_int("asset_version", self.asset_version)
        _positive_int("retention_days", self.retention_days)
        _digest("asset_digest", self.asset_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "retention_trigger_at", _timestamp("retention_trigger_at", self.retention_trigger_at))
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class LegalHold:
    institution_id: str
    hold_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    owner_id: str
    rationale: str
    evidence_digest: str
    starts_at: str
    recorded_at: str
    schema_version: str = "datagovops.legal-hold.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "hold_id", "asset_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("asset_digest", self.asset_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        object.__setattr__(self, "starts_at", _timestamp("starts_at", self.starts_at))
        object.__setattr__(self, "recorded_at", _timestamp("recorded_at", self.recorded_at))
        if _parse_timestamp(self.recorded_at) < _parse_timestamp(self.starts_at):
            raise GovernanceError("legal hold recorded_at cannot precede starts_at")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class LegalHoldRelease:
    institution_id: str
    release_id: str
    hold_id: str
    hold_digest: str
    released_by_id: str
    rationale: str
    evidence_digest: str
    released_at: str
    schema_version: str = "datagovops.legal-hold-release.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "release_id", "hold_id", "released_by_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _digest("hold_digest", self.hold_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        object.__setattr__(self, "released_at", _timestamp("released_at", self.released_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class DeletionEligibilityEvaluation:
    institution_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    schedule_digest: str
    retention_deadline: str
    active_hold_digests: tuple[str, ...]
    state: DeletionEligibilityState
    reason_code: str
    evaluated_at: str
    deletion_executed: bool = False
    legal_compliance_determined: bool = False
    schema_version: str = "datagovops.deletion-eligibility-evaluation.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "reason_code", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("asset_digest", self.asset_digest)
        _digest("schedule_digest", self.schedule_digest)
        object.__setattr__(self, "active_hold_digests", _digest_tuple("active_hold_digests", self.active_hold_digests))
        _enum("state", self.state, DeletionEligibilityState)
        object.__setattr__(self, "retention_deadline", _timestamp("retention_deadline", self.retention_deadline))
        object.__setattr__(self, "evaluated_at", _timestamp("evaluated_at", self.evaluated_at))
        _bool("deletion_executed", self.deletion_executed)
        _bool("legal_compliance_determined", self.legal_compliance_determined)
        if self.deletion_executed:
            raise GovernanceError("deletion eligibility evidence does not establish deletion execution")
        if self.legal_compliance_determined:
            raise GovernanceError("deletion eligibility evidence does not determine legal compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class DataLocationEvidence:
    institution_id: str
    location_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    location_kind: DataLocationKind
    country_code: str
    region: str | None
    cross_border: bool
    reviewer_id: str
    evidence_digest: str
    observed_at: str
    schema_version: str = "datagovops.data-location-evidence.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "location_id", "asset_id", "reviewer_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("asset_digest", self.asset_digest)
        _enum("location_kind", self.location_kind, DataLocationKind)
        object.__setattr__(self, "country_code", _country_code("country_code", self.country_code))
        object.__setattr__(self, "region", _optional_text("region", self.region))
        _bool("cross_border", self.cross_border)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "observed_at", _timestamp("observed_at", self.observed_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class PrivacySecurityObligationMapping:
    institution_id: str
    mapping_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    category: ObligationCategory
    obligation_reference: str
    status: ObligationMappingStatus
    reviewer_id: str
    rationale: str
    location_evidence_digests: tuple[str, ...]
    evidence_digest: str
    reviewed_at: str
    legal_applicability_determined: bool = False
    schema_version: str = "datagovops.privacy-security-obligation-mapping.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "mapping_id", "asset_id", "reviewer_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("asset_digest", self.asset_digest)
        _enum("category", self.category, ObligationCategory)
        _enum("status", self.status, ObligationMappingStatus)
        object.__setattr__(
            self,
            "obligation_reference",
            _text("obligation_reference", self.obligation_reference, limit=1024),
        )
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        object.__setattr__(
            self,
            "location_evidence_digests",
            _digest_tuple("location_evidence_digests", self.location_evidence_digests),
        )
        if (
            self.status is ObligationMappingStatus.MAPPED
            and self.category in (ObligationCategory.DATA_RESIDENCY, ObligationCategory.CROSS_BORDER)
            and not self.location_evidence_digests
        ):
            raise GovernanceError("mapped residency/cross-border obligation requires location evidence")
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "reviewed_at", _timestamp("reviewed_at", self.reviewed_at))
        _bool("legal_applicability_determined", self.legal_applicability_determined)
        if self.legal_applicability_determined:
            raise GovernanceError("obligation mapping does not determine legal applicability")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernanceControlPolicy:
    institution_id: str
    policy_id: str
    policy_version: int
    owner_id: str
    require_retention_schedule: bool
    require_obligation_mapping_for_personal_data: bool
    require_location_evidence_for_personal_data: bool
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.governance-control-policy.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "policy_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("policy_version", self.policy_version)
        for field in (
            "require_retention_schedule",
            "require_obligation_mapping_for_personal_data",
            "require_location_evidence_for_personal_data",
        ):
            _bool(field, getattr(self, field))
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernanceGap:
    code: GovernanceGapCode
    asset_id: str
    reference_id: str | None

    def __post_init__(self) -> None:
        _enum("code", self.code, GovernanceGapCode)
        object.__setattr__(self, "asset_id", _text("asset_id", self.asset_id))
        object.__setattr__(self, "reference_id", _optional_text("reference_id", self.reference_id))


@dataclass(frozen=True, slots=True)
class GovernanceControlReport:
    institution_id: str
    policy_digest: str
    asset_registry_snapshot_digest: str
    semantic_governance_snapshot_digest: str
    control_snapshot_digest: str
    gaps: tuple[GovernanceGap, ...]
    complete: bool
    evaluated_at: str
    legal_compliance_determined: bool = False
    schema_version: str = "datagovops.governance-control-report.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        for field in (
            "policy_digest",
            "asset_registry_snapshot_digest",
            "semantic_governance_snapshot_digest",
            "control_snapshot_digest",
        ):
            _digest(field, getattr(self, field))
        if not isinstance(self.gaps, tuple) or any(not isinstance(item, GovernanceGap) for item in self.gaps):
            raise GovernanceError("gaps must be a tuple of GovernanceGap")
        _bool("complete", self.complete)
        if self.complete != (len(self.gaps) == 0):
            raise GovernanceError("complete must match represented gap state")
        object.__setattr__(self, "evaluated_at", _timestamp("evaluated_at", self.evaluated_at))
        _bool("legal_compliance_determined", self.legal_compliance_determined)
        if self.legal_compliance_determined:
            raise GovernanceError("control report does not determine legal compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class AccessRetentionPrivacyRegistry:
    """Explicit access, retention and obligation evidence bound to governed state."""

    def __init__(self, asset_registry: DataAssetRegistry, semantic_registry: SemanticGovernanceRegistry) -> None:
        self.asset_registry = asset_registry
        self.semantic_registry = semantic_registry
        self._roles: dict[tuple[str, str, int], AccessRole] = {}
        self._approvals: dict[tuple[str, str], AccessPurposeApproval] = {}
        self._grants: dict[tuple[str, str], AccessGrant] = {}
        self._schedules: dict[tuple[str, str, int], RetentionSchedule] = {}
        self._schedule_ids: dict[tuple[str, str], str] = {}
        self._holds: dict[tuple[str, str], LegalHold] = {}
        self._hold_releases: dict[tuple[str, str], LegalHoldRelease] = {}
        self._locations: dict[tuple[str, str], DataLocationEvidence] = {}
        self._mappings: dict[tuple[str, str], PrivacySecurityObligationMapping] = {}
        self._policies: dict[tuple[str, str, int], GovernanceControlPolicy] = {}

    def _purpose_binding(self, institution_id: str, binding_id: str) -> AssetPurposeBinding:
        binding = self.semantic_registry._purpose_bindings.get((institution_id, binding_id))
        if binding is None:
            raise GovernanceError("unknown asset-purpose binding")
        return binding

    def register_role(self, role: AccessRole) -> str:
        self.asset_registry.principal(role.institution_id, role.owner_id)
        for principal_id in role.member_principal_ids:
            self.asset_registry.principal(role.institution_id, principal_id)
        key = (role.institution_id, role.role_id, role.role_version)
        existing = self._roles.get(key)
        if existing is not None:
            if existing.artifact_digest != role.artifact_digest:
                raise GovernanceError("access role identity/version has different content")
            return existing.artifact_digest
        history = self.role_history(role.institution_id, role.role_id)
        expected = 1 if not history else history[-1].role_version + 1
        if role.role_version != expected:
            raise GovernanceError(f"role_version must be contiguous; expected version {expected}")
        self._roles[key] = role
        return role.artifact_digest

    def role_history(self, institution_id: str, role_id: str) -> tuple[AccessRole, ...]:
        return tuple(
            sorted(
                (
                    role
                    for (scope, current_id, _), role in self._roles.items()
                    if scope == institution_id and current_id == role_id
                ),
                key=lambda item: item.role_version,
            )
        )

    def role(self, institution_id: str, role_id: str, role_version: int) -> AccessRole:
        try:
            return self._roles[(institution_id, role_id, role_version)]
        except KeyError as exc:
            raise GovernanceError("unknown access role version") from exc

    def latest_role(self, institution_id: str, role_id: str) -> AccessRole:
        history = self.role_history(institution_id, role_id)
        if not history:
            raise GovernanceError("unknown access role")
        return history[-1]

    def _resolve_subject(
        self,
        institution_id: str,
        kind: AccessSubjectKind,
        subject_id: str,
        role_version: int | None,
        digest: str,
    ):
        if kind is AccessSubjectKind.PRINCIPAL:
            principal = self.asset_registry.principal(institution_id, subject_id)
            if principal.artifact_digest != digest:
                raise GovernanceError("access subject is bound to different principal content")
            return principal
        role = self.role(institution_id, subject_id, role_version or 0)
        if role.artifact_digest != digest:
            raise GovernanceError("access subject is bound to different role content")
        return role

    def _validate_asset_purpose(
        self,
        *,
        institution_id: str,
        asset_id: str,
        asset_version: int,
        asset_digest: str,
        purpose_id: str,
        purpose_version: int,
        purpose_digest: str,
        purpose_binding_id: str,
        purpose_binding_digest: str,
    ) -> AssetPurposeBinding:
        asset = self.asset_registry.asset(institution_id, asset_id, asset_version)
        if asset.artifact_digest != asset_digest:
            raise GovernanceError("access evidence is bound to different asset content")
        purpose = self.semantic_registry.purpose(institution_id, purpose_id, purpose_version)
        if purpose.artifact_digest != purpose_digest:
            raise GovernanceError("access evidence is bound to different purpose content")
        binding = self._purpose_binding(institution_id, purpose_binding_id)
        if binding.artifact_digest != purpose_binding_digest:
            raise GovernanceError("access evidence is bound to different purpose-binding content")
        expected = (
            binding.asset_id,
            binding.asset_version,
            binding.asset_digest,
            binding.purpose_id,
            binding.purpose_version,
            binding.purpose_digest,
        )
        actual = (asset_id, asset_version, asset_digest, purpose_id, purpose_version, purpose_digest)
        if expected != actual:
            raise GovernanceError("purpose binding does not match access asset/purpose scope")
        return binding

    def register_access_approval(self, approval: AccessPurposeApproval) -> str:
        self.asset_registry.principal(approval.institution_id, approval.reviewer_id)
        self._resolve_subject(
            approval.institution_id,
            approval.subject_kind,
            approval.subject_id,
            approval.subject_role_version,
            approval.subject_digest,
        )
        self._validate_asset_purpose(
            institution_id=approval.institution_id,
            asset_id=approval.asset_id,
            asset_version=approval.asset_version,
            asset_digest=approval.asset_digest,
            purpose_id=approval.purpose_id,
            purpose_version=approval.purpose_version,
            purpose_digest=approval.purpose_digest,
            purpose_binding_id=approval.purpose_binding_id,
            purpose_binding_digest=approval.purpose_binding_digest,
        )
        key = (approval.institution_id, approval.approval_id)
        existing = self._approvals.get(key)
        if existing is not None and existing.artifact_digest != approval.artifact_digest:
            raise GovernanceError("approval_id is already registered with different content")
        self._approvals.setdefault(key, approval)
        return approval.artifact_digest

    def _approval_by_digest(self, institution_id: str, digest: str) -> AccessPurposeApproval:
        matches = [
            item
            for (scope, _), item in self._approvals.items()
            if scope == institution_id and item.artifact_digest == digest
        ]
        if len(matches) != 1:
            raise GovernanceError("access approval digest must resolve exactly once")
        return matches[0]

    def latest_access_approval(
        self,
        *,
        institution_id: str,
        subject_kind: AccessSubjectKind,
        subject_id: str,
        asset_id: str,
        purpose_id: str,
    ) -> AccessPurposeApproval:
        candidates = [
            item
            for (scope, _), item in self._approvals.items()
            if scope == institution_id
            and item.subject_kind is subject_kind
            and item.subject_id == subject_id
            and item.asset_id == asset_id
            and item.purpose_id == purpose_id
        ]
        if not candidates:
            raise GovernanceError("no access-purpose approval for scope")
        latest_time = max(_parse_timestamp(item.decided_at) for item in candidates)
        latest = [item for item in candidates if _parse_timestamp(item.decided_at) == latest_time]
        if len({item.decision for item in latest}) != 1:
            raise GovernanceError("conflicting latest access-purpose approval evidence")
        if len({item.artifact_digest for item in latest}) != 1:
            raise GovernanceError("ambiguous latest access-purpose approval evidence")
        return latest[0]

    def register_grant(self, grant: AccessGrant) -> str:
        self.asset_registry.principal(grant.institution_id, grant.granted_by_id)
        subject = self._resolve_subject(
            grant.institution_id,
            grant.subject_kind,
            grant.subject_id,
            grant.subject_role_version,
            grant.subject_digest,
        )
        if grant.subject_kind is AccessSubjectKind.ROLE and not set(grant.permissions).issubset(set(subject.permissions)):
            raise GovernanceError("grant permissions exceed governed role permissions")
        approval = self._approval_by_digest(grant.institution_id, grant.approval_digest)
        if approval.decision is not AccessApprovalDecision.APPROVED:
            raise GovernanceError("access grant requires approved purpose evidence")
        expected = (
            approval.subject_kind,
            approval.subject_id,
            approval.subject_role_version,
            approval.subject_digest,
            approval.asset_id,
            approval.asset_version,
            approval.asset_digest,
            approval.purpose_id,
            approval.purpose_version,
            approval.purpose_digest,
        )
        actual = (
            grant.subject_kind,
            grant.subject_id,
            grant.subject_role_version,
            grant.subject_digest,
            grant.asset_id,
            grant.asset_version,
            grant.asset_digest,
            grant.purpose_id,
            grant.purpose_version,
            grant.purpose_digest,
        )
        if expected != actual:
            raise GovernanceError("grant scope does not match approved access-purpose evidence")
        if _parse_timestamp(grant.granted_at) < _parse_timestamp(approval.decided_at):
            raise GovernanceError("grant cannot predate its approval")
        key = (grant.institution_id, grant.grant_id)
        existing = self._grants.get(key)
        if existing is not None and existing.artifact_digest != grant.artifact_digest:
            raise GovernanceError("grant_id is already registered with different content")
        self._grants.setdefault(key, grant)
        return grant.artifact_digest

    def assert_grant_current(self, grant: AccessGrant, *, as_of: str) -> None:
        as_of = _timestamp("as_of", as_of)
        registered = self._grants.get((grant.institution_id, grant.grant_id))
        if registered is None or registered.artifact_digest != grant.artifact_digest:
            raise GovernanceError("access grant is not the registered exact grant")
        latest_approval = self.latest_access_approval(
            institution_id=grant.institution_id,
            subject_kind=grant.subject_kind,
            subject_id=grant.subject_id,
            asset_id=grant.asset_id,
            purpose_id=grant.purpose_id,
        )
        if latest_approval.artifact_digest != grant.approval_digest:
            raise GovernanceError("access grant is stale for latest access-purpose approval")
        if latest_approval.decision is not AccessApprovalDecision.APPROVED:
            raise GovernanceError("latest access-purpose decision does not approve grant")
        subject = self._resolve_subject(
            grant.institution_id,
            grant.subject_kind,
            grant.subject_id,
            grant.subject_role_version,
            grant.subject_digest,
        )
        if grant.subject_kind is AccessSubjectKind.ROLE:
            if not set(grant.permissions).issubset(set(subject.permissions)):
                raise GovernanceError("grant permissions exceed governed role permissions")
            current_role = self.latest_role(grant.institution_id, grant.subject_id)
            if current_role.role_version != grant.subject_role_version:
                raise GovernanceError("access grant is stale for latest role version")
        current_asset = self.asset_registry.latest_asset(grant.institution_id, grant.asset_id)
        if current_asset.asset_version != grant.asset_version or current_asset.artifact_digest != grant.asset_digest:
            raise GovernanceError("access grant is stale for latest asset version")
        current_purpose = self.semantic_registry.latest_purpose(grant.institution_id, grant.purpose_id)
        if (
            current_purpose.purpose_version != grant.purpose_version
            or current_purpose.artifact_digest != grant.purpose_digest
        ):
            raise GovernanceError("access grant is stale for latest purpose version")
        if _parse_timestamp(as_of) < _parse_timestamp(grant.valid_from):
            raise GovernanceError("access grant is not active yet")
        if grant.expires_at is not None and _parse_timestamp(as_of) >= _parse_timestamp(grant.expires_at):
            raise GovernanceError("access grant has expired")

    def register_retention_schedule(self, schedule: RetentionSchedule) -> str:
        self.asset_registry.principal(schedule.institution_id, schedule.owner_id)
        asset = self.asset_registry.asset(schedule.institution_id, schedule.asset_id, schedule.asset_version)
        if asset.artifact_digest != schedule.asset_digest:
            raise GovernanceError("retention schedule is bound to different asset content")
        asset_key = (schedule.institution_id, schedule.asset_id)
        configured_id = self._schedule_ids.get(asset_key)
        if configured_id is not None and configured_id != schedule.schedule_id:
            raise GovernanceError("asset already uses a different retention schedule identity")
        self._schedule_ids.setdefault(asset_key, schedule.schedule_id)
        key = (schedule.institution_id, schedule.schedule_id, schedule.schedule_version)
        existing = self._schedules.get(key)
        if existing is not None:
            if existing.artifact_digest != schedule.artifact_digest:
                raise GovernanceError("retention schedule identity/version has different content")
            return existing.artifact_digest
        history = self.schedule_history(schedule.institution_id, schedule.schedule_id)
        expected = 1 if not history else history[-1].schedule_version + 1
        if schedule.schedule_version != expected:
            raise GovernanceError(f"schedule_version must be contiguous; expected version {expected}")
        self._schedules[key] = schedule
        return schedule.artifact_digest

    def schedule_history(self, institution_id: str, schedule_id: str) -> tuple[RetentionSchedule, ...]:
        return tuple(
            sorted(
                (
                    schedule
                    for (scope, current_id, _), schedule in self._schedules.items()
                    if scope == institution_id and current_id == schedule_id
                ),
                key=lambda item: item.schedule_version,
            )
        )

    def latest_schedule_for_asset(self, institution_id: str, asset_id: str) -> RetentionSchedule:
        schedule_id = self._schedule_ids.get((institution_id, asset_id))
        if schedule_id is None:
            raise GovernanceError("asset has no retention schedule")
        history = self.schedule_history(institution_id, schedule_id)
        if not history:
            raise GovernanceError("retention schedule identity has no versions")
        return history[-1]

    def register_legal_hold(self, hold: LegalHold) -> str:
        self.asset_registry.principal(hold.institution_id, hold.owner_id)
        asset = self.asset_registry.asset(hold.institution_id, hold.asset_id, hold.asset_version)
        if asset.artifact_digest != hold.asset_digest:
            raise GovernanceError("legal hold is bound to different asset content")
        key = (hold.institution_id, hold.hold_id)
        existing = self._holds.get(key)
        if existing is not None and existing.artifact_digest != hold.artifact_digest:
            raise GovernanceError("hold_id is already registered with different content")
        self._holds.setdefault(key, hold)
        return hold.artifact_digest

    def register_legal_hold_release(self, release: LegalHoldRelease) -> str:
        self.asset_registry.principal(release.institution_id, release.released_by_id)
        hold = self._holds.get((release.institution_id, release.hold_id))
        if hold is None:
            raise GovernanceError("unknown legal hold")
        if hold.artifact_digest != release.hold_digest:
            raise GovernanceError("legal hold release is bound to different hold content")
        if _parse_timestamp(release.released_at) < _parse_timestamp(hold.starts_at):
            raise GovernanceError("legal hold release cannot predate hold start")
        existing = self._hold_releases.get((release.institution_id, release.hold_id))
        if existing is not None and existing.artifact_digest != release.artifact_digest:
            raise GovernanceError("legal hold already has different release evidence")
        self._hold_releases.setdefault((release.institution_id, release.hold_id), release)
        return release.artifact_digest

    def active_holds(self, institution_id: str, asset_id: str, *, as_of: str) -> tuple[LegalHold, ...]:
        as_of = _timestamp("as_of", as_of)
        when = _parse_timestamp(as_of)
        active: list[LegalHold] = []
        for (scope, _), hold in self._holds.items():
            if scope != institution_id or hold.asset_id != asset_id:
                continue
            if _parse_timestamp(hold.starts_at) > when:
                continue
            release = self._hold_releases.get((institution_id, hold.hold_id))
            if release is not None and _parse_timestamp(release.released_at) <= when:
                continue
            active.append(hold)
        return tuple(sorted(active, key=lambda item: item.hold_id))

    def evaluate_deletion_eligibility(
        self,
        institution_id: str,
        asset_id: str,
        *,
        evaluated_at: str,
    ) -> DeletionEligibilityEvaluation:
        evaluated_at = _timestamp("evaluated_at", evaluated_at)
        schedule = self.latest_schedule_for_asset(institution_id, asset_id)
        current_asset = self.asset_registry.latest_asset(institution_id, asset_id)
        if schedule.asset_version != current_asset.asset_version or schedule.asset_digest != current_asset.artifact_digest:
            raise GovernanceError("retention schedule is stale for latest asset version")
        deadline_dt = _parse_timestamp(schedule.retention_trigger_at) + timedelta(days=schedule.retention_days)
        deadline = deadline_dt.isoformat().replace("+00:00", "Z")
        holds = self.active_holds(institution_id, asset_id, as_of=evaluated_at)
        if holds:
            state = DeletionEligibilityState.BLOCKED_BY_LEGAL_HOLD
            reason = "active_legal_hold"
        elif _parse_timestamp(evaluated_at) < deadline_dt:
            state = DeletionEligibilityState.NOT_DUE
            reason = "retention_period_not_elapsed"
        else:
            state = DeletionEligibilityState.ELIGIBLE
            reason = "retention_period_elapsed_no_active_hold"
        return DeletionEligibilityEvaluation(
            institution_id=institution_id,
            asset_id=asset_id,
            asset_version=current_asset.asset_version,
            asset_digest=current_asset.artifact_digest,
            schedule_digest=schedule.artifact_digest,
            retention_deadline=deadline,
            active_hold_digests=tuple(item.artifact_digest for item in holds),
            state=state,
            reason_code=reason,
            evaluated_at=evaluated_at,
        )

    def register_location(self, evidence: DataLocationEvidence) -> str:
        self.asset_registry.principal(evidence.institution_id, evidence.reviewer_id)
        asset = self.asset_registry.asset(evidence.institution_id, evidence.asset_id, evidence.asset_version)
        if asset.artifact_digest != evidence.asset_digest:
            raise GovernanceError("location evidence is bound to different asset content")
        key = (evidence.institution_id, evidence.location_id)
        existing = self._locations.get(key)
        if existing is not None and existing.artifact_digest != evidence.artifact_digest:
            raise GovernanceError("location_id is already registered with different content")
        self._locations.setdefault(key, evidence)
        return evidence.artifact_digest

    def register_obligation_mapping(self, mapping: PrivacySecurityObligationMapping) -> str:
        self.asset_registry.principal(mapping.institution_id, mapping.reviewer_id)
        asset = self.asset_registry.asset(mapping.institution_id, mapping.asset_id, mapping.asset_version)
        if asset.artifact_digest != mapping.asset_digest:
            raise GovernanceError("obligation mapping is bound to different asset content")
        for digest in mapping.location_evidence_digests:
            matches = [
                item
                for (scope, _), item in self._locations.items()
                if scope == mapping.institution_id and item.artifact_digest == digest
            ]
            if len(matches) != 1:
                raise GovernanceError("obligation location digest must resolve exactly once")
            if matches[0].asset_id != mapping.asset_id or matches[0].asset_version != mapping.asset_version:
                raise GovernanceError("obligation location evidence uses different asset scope")
        if (
            mapping.status is ObligationMappingStatus.MAPPED
            and mapping.category is ObligationCategory.CROSS_BORDER
        ):
            mapped_locations = [
                item
                for (scope, _), item in self._locations.items()
                if scope == mapping.institution_id
                and item.artifact_digest in mapping.location_evidence_digests
            ]
            if not any(item.cross_border for item in mapped_locations):
                raise GovernanceError("mapped cross-border obligation requires explicit cross-border location evidence")
        key = (mapping.institution_id, mapping.mapping_id)
        existing = self._mappings.get(key)
        if existing is not None and existing.artifact_digest != mapping.artifact_digest:
            raise GovernanceError("mapping_id is already registered with different content")
        self._mappings.setdefault(key, mapping)
        return mapping.artifact_digest

    def register_policy(self, policy: GovernanceControlPolicy) -> str:
        self.asset_registry.principal(policy.institution_id, policy.owner_id)
        key = (policy.institution_id, policy.policy_id, policy.policy_version)
        existing = self._policies.get(key)
        if existing is not None:
            if existing.artifact_digest != policy.artifact_digest:
                raise GovernanceError("control policy identity/version has different content")
            return existing.artifact_digest
        history = self.policy_history(policy.institution_id, policy.policy_id)
        expected = 1 if not history else history[-1].policy_version + 1
        if policy.policy_version != expected:
            raise GovernanceError(f"policy_version must be contiguous; expected version {expected}")
        self._policies[key] = policy
        return policy.artifact_digest

    def policy_history(self, institution_id: str, policy_id: str) -> tuple[GovernanceControlPolicy, ...]:
        return tuple(
            sorted(
                (
                    policy
                    for (scope, current_id, _), policy in self._policies.items()
                    if scope == institution_id and current_id == policy_id
                ),
                key=lambda item: item.policy_version,
            )
        )

    def latest_policy(self, institution_id: str, policy_id: str) -> GovernanceControlPolicy:
        history = self.policy_history(institution_id, policy_id)
        if not history:
            raise GovernanceError("unknown governance control policy")
        return history[-1]

    def snapshot_digest(self, institution_id: str) -> str:
        return digest_artifact(
            {
                "institution_id": institution_id,
                "asset_registry_snapshot_digest": self.asset_registry.snapshot_digest(institution_id),
                "semantic_governance_snapshot_digest": self.semantic_registry.snapshot_digest(institution_id),
                "access_roles": sorted(
                    item.artifact_digest for (scope, _, _), item in self._roles.items() if scope == institution_id
                ),
                "access_approvals": sorted(
                    item.artifact_digest for (scope, _), item in self._approvals.items() if scope == institution_id
                ),
                "access_grants": sorted(
                    item.artifact_digest for (scope, _), item in self._grants.items() if scope == institution_id
                ),
                "retention_schedules": sorted(
                    item.artifact_digest for (scope, _, _), item in self._schedules.items() if scope == institution_id
                ),
                "legal_holds": sorted(
                    item.artifact_digest for (scope, _), item in self._holds.items() if scope == institution_id
                ),
                "legal_hold_releases": sorted(
                    item.artifact_digest for (scope, _), item in self._hold_releases.items() if scope == institution_id
                ),
                "location_evidence": sorted(
                    item.artifact_digest for (scope, _), item in self._locations.items() if scope == institution_id
                ),
                "obligation_mappings": sorted(
                    item.artifact_digest for (scope, _), item in self._mappings.items() if scope == institution_id
                ),
                "control_policies": sorted(
                    item.artifact_digest for (scope, _, _), item in self._policies.items() if scope == institution_id
                ),
            }
        )

    def evaluate_control_gaps(
        self,
        institution_id: str,
        policy_id: str,
        *,
        evaluated_at: str,
    ) -> GovernanceControlReport:
        evaluated_at = _timestamp("evaluated_at", evaluated_at)
        policy = self.latest_policy(institution_id, policy_id)
        gaps: list[GovernanceGap] = []
        latest_by_id = {
            asset.asset_id: asset
            for asset in self.asset_registry.assets_for_institution(institution_id)
        }
        latest_assets = tuple(latest_by_id[asset_id] for asset_id in sorted(latest_by_id))

        for asset in latest_assets:
            if policy.require_retention_schedule:
                try:
                    schedule = self.latest_schedule_for_asset(institution_id, asset.asset_id)
                except GovernanceError:
                    gaps.append(GovernanceGap(GovernanceGapCode.MISSING_RETENTION_SCHEDULE, asset.asset_id, None))
                else:
                    if schedule.asset_version != asset.asset_version or schedule.asset_digest != asset.artifact_digest:
                        gaps.append(
                            GovernanceGap(
                                GovernanceGapCode.STALE_RETENTION_SCHEDULE,
                                asset.asset_id,
                                schedule.schedule_id,
                            )
                        )

            if asset.contains_personal_data and policy.require_obligation_mapping_for_personal_data:
                all_mappings = [
                    item
                    for (scope, _), item in self._mappings.items()
                    if scope == institution_id and item.asset_id == asset.asset_id
                ]
                mappings = [
                    item
                    for item in all_mappings
                    if item.asset_version == asset.asset_version
                    and item.asset_digest == asset.artifact_digest
                ]
                if not all_mappings:
                    gaps.append(GovernanceGap(GovernanceGapCode.MISSING_OBLIGATION_MAPPING, asset.asset_id, None))
                elif not mappings:
                    gaps.append(
                        GovernanceGap(
                            GovernanceGapCode.STALE_OBLIGATION_MAPPING,
                            asset.asset_id,
                            ",".join(sorted(item.mapping_id for item in all_mappings)),
                        )
                    )

            if asset.contains_personal_data and policy.require_location_evidence_for_personal_data:
                locations = [
                    item
                    for (scope, _), item in self._locations.items()
                    if scope == institution_id and item.asset_id == asset.asset_id
                ]
                current_locations = [
                    item
                    for item in locations
                    if item.asset_version == asset.asset_version and item.asset_digest == asset.artifact_digest
                ]
                if not locations:
                    gaps.append(GovernanceGap(GovernanceGapCode.MISSING_LOCATION_EVIDENCE, asset.asset_id, None))
                elif not current_locations:
                    gaps.append(
                        GovernanceGap(
                            GovernanceGapCode.STALE_LOCATION_EVIDENCE,
                            asset.asset_id,
                            ",".join(sorted(item.location_id for item in locations)),
                        )
                    )

        evaluation_time = _parse_timestamp(evaluated_at)
        for (scope, grant_id), grant in self._grants.items():
            if scope != institution_id:
                continue
            if evaluation_time < _parse_timestamp(grant.valid_from):
                continue
            if grant.expires_at is not None and evaluation_time >= _parse_timestamp(grant.expires_at):
                continue
            try:
                self.assert_grant_current(grant, as_of=evaluated_at)
            except GovernanceError:
                gaps.append(GovernanceGap(GovernanceGapCode.STALE_ACCESS_GRANT, grant.asset_id, grant_id))

        gaps.sort(key=lambda item: (item.code.value, item.asset_id, item.reference_id or ""))
        return GovernanceControlReport(
            institution_id=institution_id,
            policy_digest=policy.artifact_digest,
            asset_registry_snapshot_digest=self.asset_registry.snapshot_digest(institution_id),
            semantic_governance_snapshot_digest=self.semantic_registry.snapshot_digest(institution_id),
            control_snapshot_digest=self.snapshot_digest(institution_id),
            gaps=tuple(gaps),
            complete=not gaps,
            evaluated_at=evaluated_at,
        )

    def assert_report_current(self, report: GovernanceControlReport, policy_id: str) -> None:
        if report.policy_digest != self.latest_policy(report.institution_id, policy_id).artifact_digest:
            raise GovernanceError("governance control report is stale for latest policy")
        if report.asset_registry_snapshot_digest != self.asset_registry.snapshot_digest(report.institution_id):
            raise GovernanceError("governance control report is stale for asset registry")
        if report.semantic_governance_snapshot_digest != self.semantic_registry.snapshot_digest(report.institution_id):
            raise GovernanceError("governance control report is stale for semantic governance")
        if report.control_snapshot_digest != self.snapshot_digest(report.institution_id):
            raise GovernanceError("governance control report is stale for access/retention/obligation state")
