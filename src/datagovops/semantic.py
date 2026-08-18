from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    DataClassification,
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


class ClassificationScope(str, Enum):
    ASSET = "asset"
    DATA_ELEMENT = "data_element"


@dataclass(frozen=True, slots=True)
class DataElementRecord:
    institution_id: str
    asset_id: str
    asset_version: int
    element_id: str
    name: str
    data_type: str
    owner_id: str
    nullable: bool
    registered_at: str
    schema_version: str = "datagovops.data-element-record.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "asset_id",
            "element_id",
            "name",
            "data_type",
            "owner_id",
            "schema_version",
        ):
            limit = 512 if field == "name" else 256
            object.__setattr__(self, field, _text(field, getattr(self, field), limit=limit))
        _positive_int("asset_version", self.asset_version)
        _bool("nullable", self.nullable)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class ClassificationDecision:
    institution_id: str
    asset_id: str
    asset_version: int
    scope: ClassificationScope
    element_id: str | None
    target_digest: str
    classification: DataClassification
    decision_owner_id: str
    rationale: str
    evidence_digest: str
    decided_at: str
    schema_version: str = "datagovops.classification-decision.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "decision_owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _enum("scope", self.scope, ClassificationScope)
        _enum("classification", self.classification, DataClassification)
        object.__setattr__(self, "element_id", _optional_text("element_id", self.element_id))
        if self.scope is ClassificationScope.ASSET and self.element_id is not None:
            raise GovernanceError("asset classification decision cannot include element_id")
        if self.scope is ClassificationScope.DATA_ELEMENT and self.element_id is None:
            raise GovernanceError("data-element classification decision requires element_id")
        _digest("target_digest", self.target_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=1024))
        object.__setattr__(self, "decided_at", _timestamp("decided_at", self.decided_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class CriticalDataElementDesignation:
    institution_id: str
    asset_id: str
    asset_version: int
    element_id: str
    element_digest: str
    cde_owner_id: str
    decision_owner_id: str
    rationale: str
    evidence_digest: str
    designated_at: str
    schema_version: str = "datagovops.critical-data-element-designation.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "asset_id",
            "element_id",
            "cde_owner_id",
            "decision_owner_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _digest("element_digest", self.element_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=1024))
        object.__setattr__(self, "designated_at", _timestamp("designated_at", self.designated_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class BusinessPurpose:
    institution_id: str
    purpose_id: str
    purpose_version: int
    name: str
    description: str
    owner_id: str
    registered_at: str
    schema_version: str = "datagovops.business-purpose.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "purpose_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("purpose_version", self.purpose_version)
        object.__setattr__(self, "name", _text("name", self.name, limit=512))
        object.__setattr__(self, "description", _text("description", self.description, limit=2048))
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class AssetPurposeBinding:
    institution_id: str
    binding_id: str
    asset_id: str
    asset_version: int
    asset_digest: str
    purpose_id: str
    purpose_version: int
    purpose_digest: str
    approval_owner_id: str
    rationale: str
    evidence_digest: str
    bound_at: str
    schema_version: str = "datagovops.asset-purpose-binding.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "binding_id",
            "asset_id",
            "purpose_id",
            "approval_owner_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("asset_version", self.asset_version)
        _positive_int("purpose_version", self.purpose_version)
        _digest("asset_digest", self.asset_digest)
        _digest("purpose_digest", self.purpose_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=1024))
        object.__setattr__(self, "bound_at", _timestamp("bound_at", self.bound_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class SemanticGovernanceRegistry:
    """Semantic governance evidence bound to an authoritative DataAssetRegistry."""

    def __init__(self, asset_registry: DataAssetRegistry) -> None:
        self.asset_registry = asset_registry
        self._elements: dict[tuple[str, str, int, str], DataElementRecord] = {}
        self._classifications: dict[tuple[str, str, int, str | None], ClassificationDecision] = {}
        self._cde_designations: dict[tuple[str, str, int, str], CriticalDataElementDesignation] = {}
        self._purposes: dict[tuple[str, str, int], BusinessPurpose] = {}
        self._purpose_bindings: dict[tuple[str, str], AssetPurposeBinding] = {}

    def register_element(self, element: DataElementRecord) -> str:
        self.asset_registry.asset(element.institution_id, element.asset_id, element.asset_version)
        self.asset_registry.principal(element.institution_id, element.owner_id)
        key = (element.institution_id, element.asset_id, element.asset_version, element.element_id)
        existing = self._elements.get(key)
        if existing is not None and existing.artifact_digest != element.artifact_digest:
            raise GovernanceError("data element identity is already registered with different content")
        self._elements.setdefault(key, element)
        return element.artifact_digest

    def element(
        self,
        institution_id: str,
        asset_id: str,
        asset_version: int,
        element_id: str,
    ) -> DataElementRecord:
        try:
            return self._elements[(institution_id, asset_id, asset_version, element_id)]
        except KeyError as exc:
            raise GovernanceError("unknown data element") from exc

    def register_classification(self, decision: ClassificationDecision) -> str:
        self.asset_registry.principal(decision.institution_id, decision.decision_owner_id)
        asset = self.asset_registry.asset(
            decision.institution_id,
            decision.asset_id,
            decision.asset_version,
        )
        if decision.scope is ClassificationScope.ASSET:
            if decision.target_digest != asset.artifact_digest:
                raise GovernanceError("asset classification decision is bound to different asset content")
            if decision.classification is not asset.classification:
                raise GovernanceError("asset classification decision conflicts with registered asset classification")
            target_key: str | None = None
        else:
            element = self.element(
                decision.institution_id,
                decision.asset_id,
                decision.asset_version,
                decision.element_id or "",
            )
            if decision.target_digest != element.artifact_digest:
                raise GovernanceError("data-element classification decision is bound to different element content")
            target_key = element.element_id

        key = (decision.institution_id, decision.asset_id, decision.asset_version, target_key)
        existing = self._classifications.get(key)
        if existing is not None and existing.artifact_digest != decision.artifact_digest:
            raise GovernanceError("classification target already has different decision evidence")
        self._classifications.setdefault(key, decision)
        return decision.artifact_digest

    def register_cde(self, designation: CriticalDataElementDesignation) -> str:
        self.asset_registry.principal(designation.institution_id, designation.cde_owner_id)
        self.asset_registry.principal(designation.institution_id, designation.decision_owner_id)
        element = self.element(
            designation.institution_id,
            designation.asset_id,
            designation.asset_version,
            designation.element_id,
        )
        if designation.element_digest != element.artifact_digest:
            raise GovernanceError("CDE designation is bound to different element content")
        key = (
            designation.institution_id,
            designation.asset_id,
            designation.asset_version,
            designation.element_id,
        )
        existing = self._cde_designations.get(key)
        if existing is not None and existing.artifact_digest != designation.artifact_digest:
            raise GovernanceError("data element already has different CDE designation evidence")
        self._cde_designations.setdefault(key, designation)
        return designation.artifact_digest

    def register_purpose(self, purpose: BusinessPurpose) -> str:
        self.asset_registry.principal(purpose.institution_id, purpose.owner_id)
        key = (purpose.institution_id, purpose.purpose_id, purpose.purpose_version)
        existing = self._purposes.get(key)
        if existing is not None:
            if existing.artifact_digest != purpose.artifact_digest:
                raise GovernanceError("business purpose identity/version has different content")
            return existing.artifact_digest
        history = self.purpose_history(purpose.institution_id, purpose.purpose_id)
        expected = 1 if not history else history[-1].purpose_version + 1
        if purpose.purpose_version != expected:
            raise GovernanceError(f"purpose_version must be contiguous; expected version {expected}")
        self._purposes[key] = purpose
        return purpose.artifact_digest

    def purpose(self, institution_id: str, purpose_id: str, purpose_version: int) -> BusinessPurpose:
        try:
            return self._purposes[(institution_id, purpose_id, purpose_version)]
        except KeyError as exc:
            raise GovernanceError("unknown business purpose version") from exc

    def purpose_history(self, institution_id: str, purpose_id: str) -> tuple[BusinessPurpose, ...]:
        return tuple(
            sorted(
                (
                    purpose
                    for (scope, current_id, _), purpose in self._purposes.items()
                    if scope == institution_id and current_id == purpose_id
                ),
                key=lambda item: item.purpose_version,
            )
        )

    def latest_purpose(self, institution_id: str, purpose_id: str) -> BusinessPurpose:
        history = self.purpose_history(institution_id, purpose_id)
        if not history:
            raise GovernanceError("unknown business purpose")
        return history[-1]

    def register_purpose_binding(self, binding: AssetPurposeBinding) -> str:
        self.asset_registry.principal(binding.institution_id, binding.approval_owner_id)
        asset = self.asset_registry.asset(binding.institution_id, binding.asset_id, binding.asset_version)
        if binding.asset_digest != asset.artifact_digest:
            raise GovernanceError("purpose binding is bound to different asset content")
        purpose = self.purpose(binding.institution_id, binding.purpose_id, binding.purpose_version)
        if binding.purpose_digest != purpose.artifact_digest:
            raise GovernanceError("purpose binding is bound to different purpose content")
        key = (binding.institution_id, binding.binding_id)
        existing = self._purpose_bindings.get(key)
        if existing is not None and existing.artifact_digest != binding.artifact_digest:
            raise GovernanceError("binding_id is already registered with different content")
        self._purpose_bindings.setdefault(key, binding)
        return binding.artifact_digest

    def assert_classification_current(self, decision: ClassificationDecision) -> None:
        current_asset = self.asset_registry.latest_asset(decision.institution_id, decision.asset_id)
        if current_asset.asset_version != decision.asset_version:
            raise GovernanceError("classification decision is stale for latest asset version")
        key = (
            decision.institution_id,
            decision.asset_id,
            decision.asset_version,
            decision.element_id if decision.scope is ClassificationScope.DATA_ELEMENT else None,
        )
        registered = self._classifications.get(key)
        if registered is None or registered.artifact_digest != decision.artifact_digest:
            raise GovernanceError("classification decision is not the registered exact decision")
        if decision.scope is ClassificationScope.DATA_ELEMENT:
            element = self.element(
                decision.institution_id,
                decision.asset_id,
                decision.asset_version,
                decision.element_id or "",
            )
            if decision.target_digest != element.artifact_digest:
                raise GovernanceError("classification decision target content changed")
        elif decision.target_digest != current_asset.artifact_digest:
            raise GovernanceError("classification decision target content changed")

    def assert_cde_current(self, designation: CriticalDataElementDesignation) -> None:
        current_asset = self.asset_registry.latest_asset(designation.institution_id, designation.asset_id)
        if current_asset.asset_version != designation.asset_version:
            raise GovernanceError("CDE designation is stale for latest asset version")
        key = (
            designation.institution_id,
            designation.asset_id,
            designation.asset_version,
            designation.element_id,
        )
        registered = self._cde_designations.get(key)
        if registered is None or registered.artifact_digest != designation.artifact_digest:
            raise GovernanceError("CDE designation is not the registered exact designation")
        element = self.element(*key)
        if designation.element_digest != element.artifact_digest:
            raise GovernanceError("CDE designation element content changed")

    def assert_purpose_binding_current(self, binding: AssetPurposeBinding) -> None:
        current_asset = self.asset_registry.latest_asset(binding.institution_id, binding.asset_id)
        if current_asset.asset_version != binding.asset_version:
            raise GovernanceError("purpose binding is stale for latest asset version")
        current_purpose = self.latest_purpose(binding.institution_id, binding.purpose_id)
        if current_purpose.purpose_version != binding.purpose_version:
            raise GovernanceError("purpose binding is stale for latest purpose version")
        registered = self._purpose_bindings.get((binding.institution_id, binding.binding_id))
        if registered is None or registered.artifact_digest != binding.artifact_digest:
            raise GovernanceError("purpose binding is not the registered exact binding")
        if binding.asset_digest != current_asset.artifact_digest:
            raise GovernanceError("purpose binding asset content changed")
        if binding.purpose_digest != current_purpose.artifact_digest:
            raise GovernanceError("purpose binding purpose content changed")

    def snapshot_digest(self, institution_id: str) -> str:
        base_digest = self.asset_registry.snapshot_digest(institution_id)
        elements = sorted(
            item.artifact_digest
            for (scope, _, _, _), item in self._elements.items()
            if scope == institution_id
        )
        classifications = sorted(
            item.artifact_digest
            for (scope, _, _, _), item in self._classifications.items()
            if scope == institution_id
        )
        cdes = sorted(
            item.artifact_digest
            for (scope, _, _, _), item in self._cde_designations.items()
            if scope == institution_id
        )
        purposes = sorted(
            item.artifact_digest
            for (scope, _, _), item in self._purposes.items()
            if scope == institution_id
        )
        bindings = sorted(
            item.artifact_digest
            for (scope, _), item in self._purpose_bindings.items()
            if scope == institution_id
        )
        return digest_artifact(
            {
                "institution_id": institution_id,
                "asset_registry_snapshot_digest": base_digest,
                "data_elements": elements,
                "classification_decisions": classifications,
                "critical_data_element_designations": cdes,
                "business_purposes": purposes,
                "asset_purpose_bindings": bindings,
            }
        )
