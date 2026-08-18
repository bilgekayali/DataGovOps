from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any


class GovernanceError(ValueError):
    """Raised when a DataGovOps governance contract fails closed."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest_artifact(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: str, *, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise GovernanceError(f"{name} must be non-empty bounded text")
    return value.strip()


def _optional_text(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    return _text(name, value)


def _timestamp(name: str, value: str) -> str:
    raw = _text(name, value, limit=64)
    if not raw.endswith("Z"):
        raise GovernanceError(f"{name} must be RFC3339 UTC")
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00")
    except ValueError as exc:
        raise GovernanceError(f"{name} must be RFC3339 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise GovernanceError(f"{name} must be RFC3339 UTC")
    return raw


def _bool(name: str, value: bool) -> bool:
    if type(value) is not bool:
        raise GovernanceError(f"{name} must be a boolean")
    return value


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GovernanceError(f"{name} must be a positive integer")
    return value


def _enum(name: str, value: Any, enum_type: type[Enum]) -> Any:
    if not isinstance(value, enum_type):
        raise GovernanceError(f"{name} must use the governed enum type")
    return value


def _digest(name: str, value: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise GovernanceError(f"{name} must be lowercase SHA-256")
    return value


class PrincipalType(str, Enum):
    HUMAN = "human"
    TEAM = "team"
    SERVICE = "service"


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DataCriticality(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class GovernancePrincipal:
    institution_id: str
    principal_id: str
    display_name: str
    principal_type: PrincipalType
    registered_at: str
    schema_version: str = "datagovops.governance-principal.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "principal_id", "display_name", "schema_version"):
            object.__setattr__(
                self,
                field,
                _text(field, getattr(self, field), limit=512 if field == "display_name" else 256),
            )
        _enum("principal_type", self.principal_type, PrincipalType)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class AuthoritativeSystem:
    institution_id: str
    system_id: str
    name: str
    owner_id: str
    system_type: str
    authoritative: bool
    registered_at: str
    schema_version: str = "datagovops.authoritative-system.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "system_id",
            "name",
            "owner_id",
            "system_type",
            "schema_version",
        ):
            object.__setattr__(
                self,
                field,
                _text(field, getattr(self, field), limit=512 if field == "name" else 256),
            )
        _bool("authoritative", self.authoritative)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class DataAssetRecord:
    institution_id: str
    asset_id: str
    asset_version: int
    name: str
    data_domain: str
    owner_id: str
    steward_id: str
    system_of_record_id: str
    classification: DataClassification
    classification_decision_owner_id: str
    classification_rationale: str
    criticality: DataCriticality
    criticality_decision_owner_id: str
    criticality_rationale: str
    contains_personal_data: bool
    source_of_truth: bool
    retention_policy_id: str | None
    quality_owner_id: str | None
    registered_at: str
    schema_version: str = "datagovops.data-asset-record.v1"

    def __post_init__(self) -> None:
        rationale_fields = {"classification_rationale", "criticality_rationale"}
        for field in (
            "institution_id",
            "asset_id",
            "name",
            "data_domain",
            "owner_id",
            "steward_id",
            "system_of_record_id",
            "classification_decision_owner_id",
            "classification_rationale",
            "criticality_decision_owner_id",
            "criticality_rationale",
            "schema_version",
        ):
            if field == "name":
                limit = 512
            elif field in rationale_fields:
                limit = 1024
            else:
                limit = 256
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=limit))
        _positive_int("asset_version", self.asset_version)
        _enum("classification", self.classification, DataClassification)
        _enum("criticality", self.criticality, DataCriticality)
        _bool("contains_personal_data", self.contains_personal_data)
        _bool("source_of_truth", self.source_of_truth)
        object.__setattr__(
            self,
            "retention_policy_id",
            _optional_text("retention_policy_id", self.retention_policy_id),
        )
        object.__setattr__(
            self,
            "quality_owner_id",
            _optional_text("quality_owner_id", self.quality_owner_id),
        )
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    institution_id: str
    personal_data_requires_retention_policy: bool = True
    high_criticality_requires_quality_owner: bool = True
    restricted_requires_retention_policy: bool = True
    source_of_truth_requires_authoritative_system: bool = True
    owner_steward_separation_required: bool = False
    schema_version: str = "datagovops.governance-policy.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        for field in (
            "personal_data_requires_retention_policy",
            "high_criticality_requires_quality_owner",
            "restricted_requires_retention_policy",
            "source_of_truth_requires_authoritative_system",
            "owner_steward_separation_required",
        ):
            _bool(field, getattr(self, field))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class DataAssetValidationReport:
    institution_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    policy_digest: str
    registry_snapshot_digest: str
    structurally_complete: bool
    error_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    validated_at: str
    regulatory_compliance_determined: bool = False
    schema_version: str = "datagovops.data-asset-validation-report.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "asset_id", _text("asset_id", self.asset_id))
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        _positive_int("asset_version", self.asset_version)
        for field in ("asset_digest", "policy_digest", "registry_snapshot_digest"):
            _digest(field, getattr(self, field))
        _bool("structurally_complete", self.structurally_complete)
        if len(set(self.error_codes)) != len(self.error_codes):
            raise GovernanceError("error_codes must be unique")
        if len(set(self.warning_codes)) != len(self.warning_codes):
            raise GovernanceError("warning_codes must be unique")
        if set(self.error_codes) & set(self.warning_codes):
            raise GovernanceError("validation code cannot be both error and warning")
        for code in self.error_codes + self.warning_codes:
            _text("validation code", code)
        object.__setattr__(self, "validated_at", _timestamp("validated_at", self.validated_at))
        _bool("regulatory_compliance_determined", self.regulatory_compliance_determined)
        if self.regulatory_compliance_determined:
            raise GovernanceError("v0.1 does not determine regulatory compliance")
        if self.structurally_complete != (not self.error_codes):
            raise GovernanceError("structurally_complete is inconsistent with error_codes")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)
