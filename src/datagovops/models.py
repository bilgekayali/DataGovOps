from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_artifact(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: str, *, limit: int = 256) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be non-empty bounded text")


def _optional_text(name: str, value: str | None) -> None:
    if value is not None:
        _text(name, value)


def _timestamp(name: str, value: str) -> None:
    _text(name, value, limit=64)
    if not value.endswith("Z"):
        raise ValueError(f"{name} must be RFC3339 UTC")
    datetime.fromisoformat(value[:-1] + "+00:00")


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
class DataAssetRecord:
    institution_id: str
    asset_id: str
    name: str
    data_domain: str
    owner_id: str
    steward_id: str
    system_of_record: str
    classification: DataClassification
    criticality: DataCriticality
    contains_personal_data: bool
    source_of_truth: bool
    retention_policy_id: str | None
    quality_owner_id: str | None
    registered_at: str
    schema_version: str = "datagovops.data-asset-record.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "name", "data_domain", "owner_id", "steward_id", "system_of_record", "schema_version"):
            _text(field, getattr(self, field), limit=512 if field == "name" else 256)
        _optional_text("retention_policy_id", self.retention_policy_id)
        _optional_text("quality_owner_id", self.quality_owner_id)
        _timestamp("registered_at", self.registered_at)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    institution_id: str
    personal_data_requires_retention_policy: bool = True
    high_criticality_requires_quality_owner: bool = True
    restricted_requires_retention_policy: bool = True
    schema_version: str = "datagovops.governance-policy.v1"

    def __post_init__(self) -> None:
        _text("institution_id", self.institution_id)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class DataAssetValidationReport:
    institution_id: str
    asset_id: str
    asset_digest: str
    policy_digest: str
    structurally_complete: bool
    error_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    validated_at: str
    regulatory_compliance_determined: bool = False
    schema_version: str = "datagovops.data-asset-validation-report.v1"

    def __post_init__(self) -> None:
        _text("institution_id", self.institution_id)
        _text("asset_id", self.asset_id)
        for field in ("asset_digest", "policy_digest"):
            value = getattr(self, field)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"{field} must be lowercase SHA-256")
        if len(set(self.error_codes)) != len(self.error_codes) or len(set(self.warning_codes)) != len(self.warning_codes):
            raise ValueError("validation codes must be unique")
        _timestamp("validated_at", self.validated_at)
        if self.regulatory_compliance_determined:
            raise ValueError("v0.1 does not determine regulatory compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)
