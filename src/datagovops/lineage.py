from __future__ import annotations

from dataclasses import dataclass
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
from .semantic import SemanticGovernanceRegistry


class LineageEndpointKind(str, Enum):
    ASSET = "asset"
    DATA_ELEMENT = "data_element"


class LineageRelationship(str, Enum):
    DERIVED_FROM = "derived_from"
    COPIED_FROM = "copied_from"
    AGGREGATED_FROM = "aggregated_from"
    JOINED_FROM = "joined_from"
    FILTERED_FROM = "filtered_from"
    TRANSFORMED_FROM = "transformed_from"
    REPLICATED_FROM = "replicated_from"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class LineageEndpointRef:
    institution_id: str
    kind: LineageEndpointKind
    asset_id: str
    asset_version: int
    element_id: str | None
    target_digest: str
    schema_version: str = "datagovops.lineage-endpoint-ref.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "asset_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _enum("kind", self.kind, LineageEndpointKind)
        _positive_int("asset_version", self.asset_version)
        object.__setattr__(self, "element_id", _optional_text("element_id", self.element_id))
        if self.kind is LineageEndpointKind.ASSET and self.element_id is not None:
            raise GovernanceError("asset lineage endpoint cannot include element_id")
        if self.kind is LineageEndpointKind.DATA_ELEMENT and self.element_id is None:
            raise GovernanceError("data-element lineage endpoint requires element_id")
        _digest("target_digest", self.target_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class TransformationRecord:
    institution_id: str
    transformation_id: str
    transformation_version: int
    name: str
    owner_id: str
    execution_system_id: str
    code_digest: str
    config_digest: str
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.transformation-record.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "transformation_id",
            "owner_id",
            "execution_system_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        _positive_int("transformation_version", self.transformation_version)
        object.__setattr__(self, "name", _text("name", self.name, limit=512))
        for field in ("code_digest", "config_digest", "evidence_digest"):
            _digest(field, getattr(self, field))
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class LineageEdge:
    institution_id: str
    edge_id: str
    source: LineageEndpointRef
    target: LineageEndpointRef
    relationship: LineageRelationship
    transformation_id: str
    transformation_version: int
    transformation_digest: str
    producer_system_id: str
    consumer_system_id: str
    evidence_digest: str
    recorded_at: str
    schema_version: str = "datagovops.lineage-edge.v1"

    def __post_init__(self) -> None:
        for field in (
            "institution_id",
            "edge_id",
            "transformation_id",
            "producer_system_id",
            "consumer_system_id",
            "schema_version",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if not isinstance(self.source, LineageEndpointRef) or not isinstance(
            self.target, LineageEndpointRef
        ):
            raise GovernanceError("source and target must be governed lineage endpoint references")
        if self.source.institution_id != self.institution_id:
            raise GovernanceError("source endpoint institution must match lineage edge institution")
        if self.target.institution_id != self.institution_id:
            raise GovernanceError("target endpoint institution must match lineage edge institution")
        _enum("relationship", self.relationship, LineageRelationship)
        _positive_int("transformation_version", self.transformation_version)
        _digest("transformation_digest", self.transformation_digest)
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "recorded_at", _timestamp("recorded_at", self.recorded_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class LineageCompletenessRequirement:
    institution_id: str
    requirement_id: str
    target: LineageEndpointRef
    owner_id: str
    rationale: str
    evidence_digest: str
    registered_at: str
    schema_version: str = "datagovops.lineage-completeness-requirement.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "requirement_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if not isinstance(self.target, LineageEndpointRef):
            raise GovernanceError("lineage completeness target must be a governed endpoint reference")
        if self.target.institution_id != self.institution_id:
            raise GovernanceError("lineage completeness target institution must match requirement")
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=1024))
        _digest("evidence_digest", self.evidence_digest)
        object.__setattr__(self, "registered_at", _timestamp("registered_at", self.registered_at))

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class LineageCompletenessReport:
    institution_id: str
    lineage_snapshot_digest: str
    requirement_digests: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]
    stale_requirement_ids: tuple[str, ...]
    complete: bool
    evaluated_at: str
    regulatory_compliance_determined: bool = False
    schema_version: str = "datagovops.lineage-completeness-report.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "schema_version", _text("schema_version", self.schema_version))
        _digest("lineage_snapshot_digest", self.lineage_snapshot_digest)
        if not self.requirement_digests:
            raise GovernanceError("lineage completeness report requires explicit requirements")
        if tuple(sorted(set(self.requirement_digests))) != self.requirement_digests:
            raise GovernanceError("requirement_digests must be sorted and unique")
        for value in self.requirement_digests:
            _digest("requirement digest", value)
        if tuple(sorted(set(self.missing_requirement_ids))) != self.missing_requirement_ids:
            raise GovernanceError("missing_requirement_ids must be sorted and unique")
        if tuple(sorted(set(self.stale_requirement_ids))) != self.stale_requirement_ids:
            raise GovernanceError("stale_requirement_ids must be sorted and unique")
        if set(self.missing_requirement_ids) & set(self.stale_requirement_ids):
            raise GovernanceError("a requirement cannot be both missing and stale")
        for requirement_id in self.missing_requirement_ids + self.stale_requirement_ids:
            _text("requirement_id", requirement_id)
        _bool("complete", self.complete)
        expected_complete = not self.missing_requirement_ids and not self.stale_requirement_ids
        if self.complete != expected_complete:
            raise GovernanceError("complete is inconsistent with lineage completeness gaps")
        object.__setattr__(self, "evaluated_at", _timestamp("evaluated_at", self.evaluated_at))
        _bool("regulatory_compliance_determined", self.regulatory_compliance_determined)
        if self.regulatory_compliance_determined:
            raise GovernanceError("lineage evidence does not determine regulatory compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


class LineageRegistry:
    """Append-only lineage and transformation evidence over exact governed data versions."""

    def __init__(
        self,
        asset_registry: DataAssetRegistry,
        semantic_registry: SemanticGovernanceRegistry,
    ) -> None:
        if semantic_registry.asset_registry is not asset_registry:
            raise GovernanceError("semantic and lineage registries must share the same asset registry")
        self.asset_registry = asset_registry
        self.semantic_registry = semantic_registry
        self._transformations: dict[tuple[str, str, int], TransformationRecord] = {}
        self._edges: dict[tuple[str, str], LineageEdge] = {}
        self._requirements: dict[tuple[str, str], LineageCompletenessRequirement] = {}

    def resolve_endpoint(self, endpoint: LineageEndpointRef) -> str:
        if endpoint.kind is LineageEndpointKind.ASSET:
            target = self.asset_registry.asset(
                endpoint.institution_id,
                endpoint.asset_id,
                endpoint.asset_version,
            )
        else:
            target = self.semantic_registry.element(
                endpoint.institution_id,
                endpoint.asset_id,
                endpoint.asset_version,
                endpoint.element_id or "",
            )
        if endpoint.target_digest != target.artifact_digest:
            raise GovernanceError("lineage endpoint is bound to different governed content")
        return target.artifact_digest

    def assert_endpoint_current(self, endpoint: LineageEndpointRef) -> None:
        latest = self.asset_registry.latest_asset(endpoint.institution_id, endpoint.asset_id)
        if latest.asset_version != endpoint.asset_version:
            raise GovernanceError("lineage endpoint is stale for latest asset version")
        self.resolve_endpoint(endpoint)

    def register_transformation(self, transformation: TransformationRecord) -> str:
        self.asset_registry.principal(transformation.institution_id, transformation.owner_id)
        self.asset_registry.system(
            transformation.institution_id,
            transformation.execution_system_id,
        )
        key = (
            transformation.institution_id,
            transformation.transformation_id,
            transformation.transformation_version,
        )
        existing = self._transformations.get(key)
        if existing is not None:
            if existing.artifact_digest != transformation.artifact_digest:
                raise GovernanceError(
                    "transformation identity/version is already registered with different content"
                )
            return existing.artifact_digest
        history = self.transformation_history(
            transformation.institution_id,
            transformation.transformation_id,
        )
        expected = 1 if not history else history[-1].transformation_version + 1
        if transformation.transformation_version != expected:
            raise GovernanceError(
                f"transformation_version must be contiguous; expected version {expected}"
            )
        self._transformations[key] = transformation
        return transformation.artifact_digest

    def transformation(
        self,
        institution_id: str,
        transformation_id: str,
        transformation_version: int,
    ) -> TransformationRecord:
        try:
            return self._transformations[
                (institution_id, transformation_id, transformation_version)
            ]
        except KeyError as exc:
            raise GovernanceError("unknown transformation version") from exc

    def transformation_history(
        self,
        institution_id: str,
        transformation_id: str,
    ) -> tuple[TransformationRecord, ...]:
        return tuple(
            sorted(
                (
                    transformation
                    for (scope, current_id, _), transformation in self._transformations.items()
                    if scope == institution_id and current_id == transformation_id
                ),
                key=lambda item: item.transformation_version,
            )
        )

    def latest_transformation(
        self,
        institution_id: str,
        transformation_id: str,
    ) -> TransformationRecord:
        history = self.transformation_history(institution_id, transformation_id)
        if not history:
            raise GovernanceError("unknown transformation")
        return history[-1]

    @staticmethod
    def _endpoint_key(endpoint: LineageEndpointRef) -> tuple[str, str, str, int, str | None]:
        return (
            endpoint.institution_id,
            endpoint.kind.value,
            endpoint.asset_id,
            endpoint.asset_version,
            endpoint.element_id,
        )

    def _would_create_cycle(self, proposed: LineageEdge) -> bool:
        source_key = self._endpoint_key(proposed.source)
        target_key = self._endpoint_key(proposed.target)
        if source_key == target_key:
            return True
        adjacency: dict[
            tuple[str, str, str, int, str | None],
            set[tuple[str, str, str, int, str | None]],
        ] = {}
        for edge in tuple(self._edges.values()) + (proposed,):
            adjacency.setdefault(self._endpoint_key(edge.source), set()).add(
                self._endpoint_key(edge.target)
            )
        pending = [target_key]
        seen: set[tuple[str, str, str, int, str | None]] = set()
        while pending:
            node = pending.pop()
            if node == source_key:
                return True
            if node in seen:
                continue
            seen.add(node)
            pending.extend(adjacency.get(node, ()))
        return False

    def register_edge(self, edge: LineageEdge) -> str:
        self.resolve_endpoint(edge.source)
        self.resolve_endpoint(edge.target)
        self.asset_registry.system(edge.institution_id, edge.producer_system_id)
        self.asset_registry.system(edge.institution_id, edge.consumer_system_id)
        transformation = self.transformation(
            edge.institution_id,
            edge.transformation_id,
            edge.transformation_version,
        )
        if edge.transformation_digest != transformation.artifact_digest:
            raise GovernanceError("lineage edge is bound to different transformation content")
        key = (edge.institution_id, edge.edge_id)
        existing = self._edges.get(key)
        if existing is not None:
            if existing.artifact_digest != edge.artifact_digest:
                raise GovernanceError("edge_id is already registered with different content")
            return existing.artifact_digest
        if self._would_create_cycle(edge):
            raise GovernanceError("lineage edge would create a directed cycle")
        self._edges[key] = edge
        return edge.artifact_digest

    def edge(self, institution_id: str, edge_id: str) -> LineageEdge:
        try:
            return self._edges[(institution_id, edge_id)]
        except KeyError as exc:
            raise GovernanceError("unknown lineage edge") from exc

    def edges_for_institution(self, institution_id: str) -> tuple[LineageEdge, ...]:
        return tuple(
            sorted(
                (
                    edge
                    for (scope, _), edge in self._edges.items()
                    if scope == institution_id
                ),
                key=lambda item: item.edge_id,
            )
        )

    def assert_edge_current(self, edge: LineageEdge) -> None:
        registered = self.edge(edge.institution_id, edge.edge_id)
        if registered.artifact_digest != edge.artifact_digest:
            raise GovernanceError("lineage edge is not the registered exact edge")
        self.assert_endpoint_current(edge.source)
        self.assert_endpoint_current(edge.target)
        latest_transformation = self.latest_transformation(
            edge.institution_id,
            edge.transformation_id,
        )
        if latest_transformation.transformation_version != edge.transformation_version:
            raise GovernanceError("lineage edge is stale for latest transformation version")
        if latest_transformation.artifact_digest != edge.transformation_digest:
            raise GovernanceError("lineage edge transformation content changed")
        self.asset_registry.system(edge.institution_id, edge.producer_system_id)
        self.asset_registry.system(edge.institution_id, edge.consumer_system_id)

    def register_requirement(self, requirement: LineageCompletenessRequirement) -> str:
        self.asset_registry.principal(requirement.institution_id, requirement.owner_id)
        self.resolve_endpoint(requirement.target)
        key = (requirement.institution_id, requirement.requirement_id)
        existing = self._requirements.get(key)
        if existing is not None and existing.artifact_digest != requirement.artifact_digest:
            raise GovernanceError(
                "requirement_id is already registered with different content"
            )
        self._requirements.setdefault(key, requirement)
        return requirement.artifact_digest

    def requirements_for_institution(
        self,
        institution_id: str,
    ) -> tuple[LineageCompletenessRequirement, ...]:
        return tuple(
            sorted(
                (
                    requirement
                    for (scope, _), requirement in self._requirements.items()
                    if scope == institution_id
                ),
                key=lambda item: item.requirement_id,
            )
        )

    def snapshot_digest(self, institution_id: str) -> str:
        base_digest = self.asset_registry.snapshot_digest(institution_id)
        semantic_digest = self.semantic_registry.snapshot_digest(institution_id)
        transformations = sorted(
            transformation.artifact_digest
            for (scope, _, _), transformation in self._transformations.items()
            if scope == institution_id
        )
        edges = sorted(
            edge.artifact_digest
            for (scope, _), edge in self._edges.items()
            if scope == institution_id
        )
        requirements = sorted(
            requirement.artifact_digest
            for (scope, _), requirement in self._requirements.items()
            if scope == institution_id
        )
        return digest_artifact(
            {
                "institution_id": institution_id,
                "asset_registry_snapshot_digest": base_digest,
                "semantic_registry_snapshot_digest": semantic_digest,
                "transformations": transformations,
                "edges": edges,
                "requirements": requirements,
            }
        )

    def evaluate_completeness(
        self,
        institution_id: str,
        *,
        evaluated_at: str,
    ) -> LineageCompletenessReport:
        requirements = self.requirements_for_institution(institution_id)
        if not requirements:
            raise GovernanceError(
                "lineage completeness cannot be evaluated without explicit requirements"
            )
        current_edges: list[LineageEdge] = []
        for edge in self.edges_for_institution(institution_id):
            try:
                self.assert_edge_current(edge)
            except GovernanceError:
                continue
            current_edges.append(edge)
        missing: list[str] = []
        stale: list[str] = []
        for requirement in requirements:
            try:
                self.assert_endpoint_current(requirement.target)
            except GovernanceError:
                stale.append(requirement.requirement_id)
                continue
            target_key = self._endpoint_key(requirement.target)
            if not any(self._endpoint_key(edge.target) == target_key for edge in current_edges):
                missing.append(requirement.requirement_id)
        return LineageCompletenessReport(
            institution_id=institution_id,
            lineage_snapshot_digest=self.snapshot_digest(institution_id),
            requirement_digests=tuple(
                sorted(requirement.artifact_digest for requirement in requirements)
            ),
            missing_requirement_ids=tuple(sorted(missing)),
            stale_requirement_ids=tuple(sorted(stale)),
            complete=not missing and not stale,
            evaluated_at=evaluated_at,
        )

    def assert_report_current(self, report: LineageCompletenessReport) -> None:
        if report.lineage_snapshot_digest != self.snapshot_digest(report.institution_id):
            raise GovernanceError("lineage completeness report is stale")
        current_requirement_digests = tuple(
            sorted(
                requirement.artifact_digest
                for requirement in self.requirements_for_institution(report.institution_id)
            )
        )
        if report.requirement_digests != current_requirement_digests:
            raise GovernanceError("lineage completeness requirement set changed")
