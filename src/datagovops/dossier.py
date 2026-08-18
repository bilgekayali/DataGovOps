from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from .access_retention import AccessRetentionPrivacyRegistry
from .lineage import LineageRegistry
from .models import GovernanceError, GovernancePolicy, _digest, _text, _timestamp, canonical_json, digest_artifact
from .quality import FindingResolutionState, QualityEvaluationState, QualityRegistry
from .registry import DataAssetRegistry
from .semantic import SemanticGovernanceRegistry
from .validation import DataAssetValidator


DOSSIER_SCHEMA_VERSION = "datagovops.governance-dossier.v1"
RELEASE_VERSION = "0.1.0"


class DossierState(str, Enum):
    CURRENT = "current"
    WITH_GAPS = "with_gaps"
    WITH_EXCEPTIONS = "with_exceptions"
    REVALIDATION_REQUIRED = "revalidation_required"


@dataclass(frozen=True, slots=True)
class GovernanceArtifact:
    domain: str
    artifact_type: str
    artifact_id: str
    payload: dict[str, Any]
    digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _text("domain", self.domain))
        object.__setattr__(self, "artifact_type", _text("artifact_type", self.artifact_type))
        object.__setattr__(self, "artifact_id", _text("artifact_id", self.artifact_id))
        if not isinstance(self.payload, dict):
            raise GovernanceError("governance artifact payload must be an object")
        _digest("digest", self.digest)
        if digest_artifact(self.payload) != self.digest:
            raise GovernanceError("governance artifact digest does not match payload")
        if self.artifact_id != self.digest:
            raise GovernanceError("governance artifact identity must equal exact payload digest")


@dataclass(frozen=True, slots=True)
class DomainSnapshot:
    domain: str
    source_snapshot_digest: str
    artifact_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain", _text("domain", self.domain))
        _digest("source_snapshot_digest", self.source_snapshot_digest)
        if tuple(sorted(self.artifact_digests)) != self.artifact_digests:
            raise GovernanceError("domain artifact digests must be sorted")
        if len(set(self.artifact_digests)) != len(self.artifact_digests):
            raise GovernanceError("domain artifact digests must be unique")
        for value in self.artifact_digests:
            _digest("artifact_digest", value)


@dataclass(frozen=True, slots=True)
class DossierException:
    institution_id: str
    exception_id: str
    owner_id: str
    finding_codes: tuple[str, ...]
    rationale: str
    approved_at: str
    expires_at: str
    evidence_digest: str
    schema_version: str = "datagovops.dossier-exception.v1"

    def __post_init__(self) -> None:
        for field in ("institution_id", "exception_id", "owner_id", "schema_version"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if not self.finding_codes or len(set(self.finding_codes)) != len(self.finding_codes):
            raise GovernanceError("dossier exception finding_codes must be non-empty and unique")
        for code in self.finding_codes:
            _text("finding_code", code, limit=1024)
        object.__setattr__(self, "rationale", _text("rationale", self.rationale, limit=2048))
        object.__setattr__(self, "approved_at", _timestamp("approved_at", self.approved_at))
        object.__setattr__(self, "expires_at", _timestamp("expires_at", self.expires_at))
        if _parse_time(self.expires_at) <= _parse_time(self.approved_at):
            raise GovernanceError("dossier exception must expire after approval")
        _digest("evidence_digest", self.evidence_digest)

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class GovernanceDossier:
    schema_version: str
    release_version: str
    institution_id: str
    generated_at: str
    source_revision: str
    state: DossierState
    findings: tuple[str, ...]
    revalidation_findings: tuple[str, ...]
    active_exception_digests: tuple[str, ...]
    coverage: dict[str, int]
    domain_snapshots: tuple[DomainSnapshot, ...]
    artifacts: tuple[GovernanceArtifact, ...]
    exceptions: tuple[DossierException, ...]
    legal_compliance_determined: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != DOSSIER_SCHEMA_VERSION:
            raise GovernanceError("unsupported dossier schema version")
        if self.release_version != RELEASE_VERSION:
            raise GovernanceError("unsupported DataGovOps release version")
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        object.__setattr__(self, "generated_at", _timestamp("generated_at", self.generated_at))
        object.__setattr__(self, "source_revision", _text("source_revision", self.source_revision, limit=256))
        if not isinstance(self.state, DossierState):
            raise GovernanceError("state must use DossierState")
        if tuple(sorted(set(self.findings))) != self.findings:
            raise GovernanceError("findings must be sorted and unique")
        if tuple(sorted(set(self.revalidation_findings))) != self.revalidation_findings:
            raise GovernanceError("revalidation_findings must be sorted and unique")
        if not set(self.revalidation_findings).issubset(set(self.findings)):
            raise GovernanceError("revalidation findings must be included in findings")
        for finding in self.findings:
            _text("finding", finding, limit=1024)
        if tuple(sorted(self.active_exception_digests)) != self.active_exception_digests:
            raise GovernanceError("active exception digests must be sorted")
        for value in self.active_exception_digests:
            _digest("active_exception_digest", value)
        if type(self.legal_compliance_determined) is not bool or self.legal_compliance_determined:
            raise GovernanceError("governance dossier does not determine legal compliance")

        artifact_order = tuple(sorted(self.artifacts, key=lambda item: (item.domain, item.artifact_type, item.artifact_id)))
        if artifact_order != self.artifacts:
            raise GovernanceError("dossier artifacts must be deterministically sorted")
        if len({item.artifact_id for item in self.artifacts}) != len(self.artifacts):
            raise GovernanceError("dossier artifact identities must be unique")
        snapshot_order = tuple(sorted(self.domain_snapshots, key=lambda item: item.domain))
        if snapshot_order != self.domain_snapshots:
            raise GovernanceError("domain snapshots must be sorted")
        if len({item.domain for item in self.domain_snapshots}) != len(self.domain_snapshots):
            raise GovernanceError("domain snapshots must be unique")

        expected_coverage: dict[str, int] = {}
        for artifact in self.artifacts:
            expected_coverage[artifact.domain] = expected_coverage.get(artifact.domain, 0) + 1
        if self.coverage != dict(sorted(expected_coverage.items())):
            raise GovernanceError("dossier coverage does not match embedded artifacts")

        by_domain: dict[str, list[str]] = {}
        for artifact in self.artifacts:
            by_domain.setdefault(artifact.domain, []).append(artifact.digest)
        for snapshot in self.domain_snapshots:
            expected = tuple(sorted(by_domain.get(snapshot.domain, [])))
            if snapshot.artifact_digests != expected:
                raise GovernanceError("domain snapshot manifest does not match embedded artifacts")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _payload(value: Any) -> dict[str, Any]:
    import json

    payload = json.loads(canonical_json(value))
    if not isinstance(payload, dict):
        raise GovernanceError("artifact payload must canonicalize to an object")
    return payload


def _artifact(domain: str, value: Any) -> GovernanceArtifact:
    payload = _payload(value)
    digest = digest_artifact(payload)
    return GovernanceArtifact(
        domain=domain,
        artifact_type=value.__class__.__name__,
        artifact_id=digest,
        payload=payload,
        digest=digest,
    )


def _institution_values(mapping: dict[Any, Any], institution_id: str) -> list[Any]:
    values: list[Any] = []
    for value in mapping.values():
        if getattr(value, "institution_id", None) == institution_id:
            values.append(value)
    return values


def _inventory_snapshot(institution_id: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    items = list(artifacts)
    principals = sorted((x for x in items if x.artifact_type == "GovernancePrincipal"), key=lambda x: x.payload["principal_id"])
    systems = sorted((x for x in items if x.artifact_type == "AuthoritativeSystem"), key=lambda x: x.payload["system_id"])
    assets = sorted((x for x in items if x.artifact_type == "DataAssetRecord"), key=lambda x: (x.payload["asset_id"], x.payload["asset_version"]))
    return digest_artifact({
        "institution_id": institution_id,
        "principals": [x.digest for x in principals],
        "systems": [x.digest for x in systems],
        "assets": [x.digest for x in assets],
    })


def _semantic_snapshot(institution_id: str, inventory_digest: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    groups = {
        "data_elements": "DataElementRecord",
        "classification_decisions": "ClassificationDecision",
        "critical_data_element_designations": "CriticalDataElementDesignation",
        "business_purposes": "BusinessPurpose",
        "asset_purpose_bindings": "AssetPurposeBinding",
    }
    items = list(artifacts)
    payload: dict[str, Any] = {
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": inventory_digest,
    }
    for key, artifact_type in groups.items():
        payload[key] = sorted(x.digest for x in items if x.artifact_type == artifact_type)
    return digest_artifact(payload)


def _lineage_snapshot(institution_id: str, inventory_digest: str, semantic_digest: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    items = list(artifacts)
    return digest_artifact({
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": inventory_digest,
        "semantic_registry_snapshot_digest": semantic_digest,
        "transformations": sorted(x.digest for x in items if x.artifact_type == "TransformationRecord"),
        "edges": sorted(x.digest for x in items if x.artifact_type == "LineageEdge"),
        "requirements": sorted(x.digest for x in items if x.artifact_type == "LineageCompletenessRequirement"),
    })


def _quality_snapshot(institution_id: str, inventory_digest: str, semantic_digest: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    items = list(artifacts)
    groups = {
        "quality_rules": "QualityRule",
        "quality_policies": "QualityEvaluationPolicy",
        "quality_observations": "QualityObservation",
        "quality_evaluations": "QualityRuleEvaluation",
        "quality_findings": "QualityFinding",
        "quality_remediations": "QualityRemediationEvidence",
        "quality_retests": "QualityRetestEvidence",
    }
    payload: dict[str, Any] = {
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": inventory_digest,
        "semantic_registry_snapshot_digest": semantic_digest,
    }
    for key, artifact_type in groups.items():
        payload[key] = sorted(x.digest for x in items if x.artifact_type == artifact_type)
    return digest_artifact(payload)


def _control_snapshot(institution_id: str, inventory_digest: str, semantic_digest: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    items = list(artifacts)
    groups = {
        "access_roles": "AccessRole",
        "access_approvals": "AccessPurposeApproval",
        "access_grants": "AccessGrant",
        "retention_schedules": "RetentionSchedule",
        "legal_holds": "LegalHold",
        "legal_hold_releases": "LegalHoldRelease",
        "location_evidence": "DataLocationEvidence",
        "obligation_mappings": "PrivacySecurityObligationMapping",
        "control_policies": "GovernanceControlPolicy",
    }
    payload: dict[str, Any] = {
        "institution_id": institution_id,
        "asset_registry_snapshot_digest": inventory_digest,
        "semantic_governance_snapshot_digest": semantic_digest,
    }
    for key, artifact_type in groups.items():
        payload[key] = sorted(x.digest for x in items if x.artifact_type == artifact_type)
    return digest_artifact(payload)


def _assurance_snapshot(institution_id: str, artifacts: Iterable[GovernanceArtifact]) -> str:
    return digest_artifact({
        "institution_id": institution_id,
        "artifacts": sorted(x.digest for x in artifacts),
    })


class GovernanceDossierBuilder:
    """Build a deterministic dossier from the complete DataGovOps v0.1 governed state."""

    def __init__(
        self,
        asset_registry: DataAssetRegistry,
        semantic_registry: SemanticGovernanceRegistry,
        lineage_registry: LineageRegistry,
        quality_registry: QualityRegistry,
        control_registry: AccessRetentionPrivacyRegistry,
        *,
        governance_policy: GovernancePolicy | None = None,
    ) -> None:
        if semantic_registry.asset_registry is not asset_registry:
            raise GovernanceError("semantic registry must use the supplied asset registry")
        if lineage_registry.asset_registry is not asset_registry or lineage_registry.semantic_registry is not semantic_registry:
            raise GovernanceError("lineage registry must use the supplied authoritative/semantic registries")
        if quality_registry.asset_registry is not asset_registry or quality_registry.semantic_registry is not semantic_registry:
            raise GovernanceError("quality registry must use the supplied authoritative/semantic registries")
        if control_registry.asset_registry is not asset_registry or control_registry.semantic_registry is not semantic_registry:
            raise GovernanceError("control registry must use the supplied authoritative/semantic registries")
        self.asset_registry = asset_registry
        self.semantic_registry = semantic_registry
        self.lineage_registry = lineage_registry
        self.quality_registry = quality_registry
        self.control_registry = control_registry
        self.governance_policy = governance_policy

    @staticmethod
    def _select_latest(mapping: dict[Any, Any], institution_id: str, id_field: str, version_field: str, requested_id: str | None):
        values = _institution_values(mapping, institution_id)
        ids = sorted({getattr(item, id_field) for item in values})
        if requested_id is None:
            if not ids:
                return None, "missing"
            if len(ids) != 1:
                return None, "ambiguous"
            requested_id = ids[0]
        matches = [item for item in values if getattr(item, id_field) == requested_id]
        if not matches:
            return None, "missing"
        return max(matches, key=lambda item: getattr(item, version_field)), None

    def _collect_registry_artifacts(self, institution_id: str) -> list[GovernanceArtifact]:
        artifacts: list[GovernanceArtifact] = []
        mappings = (
            ("inventory", self.asset_registry._principals),
            ("inventory", self.asset_registry._systems),
            ("inventory", self.asset_registry._assets),
            ("semantic", self.semantic_registry._elements),
            ("semantic", self.semantic_registry._classifications),
            ("semantic", self.semantic_registry._cde_designations),
            ("semantic", self.semantic_registry._purposes),
            ("semantic", self.semantic_registry._purpose_bindings),
            ("lineage", self.lineage_registry._transformations),
            ("lineage", self.lineage_registry._edges),
            ("lineage", self.lineage_registry._requirements),
            ("quality", self.quality_registry._rules),
            ("quality", self.quality_registry._policies),
            ("quality", self.quality_registry._observations),
            ("quality", self.quality_registry._evaluations),
            ("quality", self.quality_registry._findings),
            ("quality", self.quality_registry._remediations),
            ("quality", self.quality_registry._retests),
            ("access_retention_privacy", self.control_registry._roles),
            ("access_retention_privacy", self.control_registry._approvals),
            ("access_retention_privacy", self.control_registry._grants),
            ("access_retention_privacy", self.control_registry._schedules),
            ("access_retention_privacy", self.control_registry._holds),
            ("access_retention_privacy", self.control_registry._hold_releases),
            ("access_retention_privacy", self.control_registry._locations),
            ("access_retention_privacy", self.control_registry._mappings),
            ("access_retention_privacy", self.control_registry._policies),
        )
        for domain, mapping in mappings:
            artifacts.extend(_artifact(domain, value) for value in _institution_values(mapping, institution_id))
        return artifacts

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
        institution_id = _text("institution_id", institution_id)
        generated_at = _timestamp("generated_at", generated_at)
        _text("source_revision", source_revision, limit=256)
        self.asset_registry.snapshot_digest(institution_id)

        gap_findings: set[str] = set()
        revalidation: set[str] = set()
        assurance: list[GovernanceArtifact] = []

        policy = self.governance_policy or GovernancePolicy(institution_id=institution_id)
        if policy.institution_id != institution_id:
            raise GovernanceError("governance policy uses different institution")
        validator = DataAssetValidator()
        latest_assets: dict[str, Any] = {}
        for asset in self.asset_registry.assets_for_institution(institution_id):
            latest_assets[asset.asset_id] = asset
        for asset_id in sorted(latest_assets):
            report = validator.validate(latest_assets[asset_id], policy, self.asset_registry, validated_at=generated_at)
            assurance.append(_artifact("assurance", report))
            for code in report.error_codes:
                gap_findings.add(f"inventory:{asset_id}:{code}")

        for decision in _institution_values(self.semantic_registry._classifications, institution_id):
            latest = latest_assets.get(decision.asset_id)
            if latest is not None and decision.asset_version == latest.asset_version:
                try:
                    self.semantic_registry.assert_classification_current(decision)
                except GovernanceError as exc:
                    revalidation.add(f"semantic:classification:{decision.artifact_digest}:{exc}")
        for designation in _institution_values(self.semantic_registry._cde_designations, institution_id):
            latest = latest_assets.get(designation.asset_id)
            if latest is not None and designation.asset_version == latest.asset_version:
                try:
                    self.semantic_registry.assert_cde_current(designation)
                except GovernanceError as exc:
                    revalidation.add(f"semantic:cde:{designation.artifact_digest}:{exc}")
        for binding in _institution_values(self.semantic_registry._purpose_bindings, institution_id):
            latest = latest_assets.get(binding.asset_id)
            if latest is None or binding.asset_version != latest.asset_version:
                continue
            try:
                latest_purpose = self.semantic_registry.latest_purpose(institution_id, binding.purpose_id)
                if binding.purpose_version == latest_purpose.purpose_version:
                    self.semantic_registry.assert_purpose_binding_current(binding)
            except GovernanceError as exc:
                revalidation.add(f"semantic:purpose_binding:{binding.artifact_digest}:{exc}")

        requirements = self.lineage_registry.requirements_for_institution(institution_id)
        if requirements:
            try:
                report = self.lineage_registry.evaluate_completeness(institution_id, evaluated_at=generated_at)
                assurance.append(_artifact("assurance", report))
                for requirement_id in report.missing_requirement_ids:
                    gap_findings.add(f"lineage:missing:{requirement_id}")
                for requirement_id in report.stale_requirement_ids:
                    revalidation.add(f"lineage:stale:{requirement_id}")
            except GovernanceError as exc:
                revalidation.add(f"lineage:revalidation:{exc}")
        else:
            gap_findings.add("lineage:no_completeness_requirements")

        latest_rules: dict[str, Any] = {}
        for rule in _institution_values(self.quality_registry._rules, institution_id):
            current = latest_rules.get(rule.rule_id)
            if current is None or rule.rule_version > current.rule_version:
                latest_rules[rule.rule_id] = rule
        quality_policy, quality_policy_error = self._select_latest(
            self.quality_registry._policies,
            institution_id,
            "policy_id",
            "policy_version",
            quality_policy_id,
        )
        if not latest_rules:
            gap_findings.add("quality:no_rules_configured")
        elif quality_policy_error == "missing":
            gap_findings.add("quality:no_evaluation_policy")
        elif quality_policy_error == "ambiguous":
            gap_findings.add("quality:policy_selection_required")
        else:
            for rule_id in sorted(latest_rules):
                try:
                    evaluation = self.quality_registry.evaluate_rule(
                        latest_rules[rule_id], quality_policy, evaluated_at=generated_at
                    )
                    assurance.append(_artifact("assurance", evaluation))
                    if evaluation.state is QualityEvaluationState.BREACHED:
                        gap_findings.add(f"quality:breached:{rule_id}")
                    elif evaluation.state is QualityEvaluationState.INCOMPLETE:
                        gap_findings.add(f"quality:incomplete:{rule_id}:{evaluation.reason_code}")
                except GovernanceError as exc:
                    revalidation.add(f"quality:rule:{rule_id}:{exc}")

        for finding in sorted(_institution_values(self.quality_registry._findings, institution_id), key=lambda x: x.finding_id):
            try:
                resolution = self.quality_registry.resolve_finding(finding, resolved_at=generated_at)
                assurance.append(_artifact("assurance", resolution))
                if resolution.state is not FindingResolutionState.CLOSED:
                    gap_findings.add(f"quality:finding_open:{finding.finding_id}:{resolution.state.value}")
            except GovernanceError as exc:
                revalidation.add(f"quality:finding:{finding.finding_id}:{exc}")

        control_policy, control_policy_error = self._select_latest(
            self.control_registry._policies,
            institution_id,
            "policy_id",
            "policy_version",
            control_policy_id,
        )
        if control_policy_error == "missing":
            gap_findings.add("control:no_governance_control_policy")
        elif control_policy_error == "ambiguous":
            gap_findings.add("control:policy_selection_required")
        else:
            try:
                report = self.control_registry.evaluate_control_gaps(
                    institution_id, control_policy.policy_id, evaluated_at=generated_at
                )
                assurance.append(_artifact("assurance", report))
                for gap in report.gaps:
                    suffix = f":{gap.reference_id}" if gap.reference_id is not None else ""
                    gap_findings.add(f"control:{gap.code.value}:{gap.asset_id}{suffix}")
            except GovernanceError as exc:
                revalidation.add(f"control:revalidation:{exc}")

        when = _parse_time(generated_at)
        for grant in _institution_values(self.control_registry._grants, institution_id):
            if _parse_time(grant.valid_from) > when:
                continue
            if grant.expires_at is not None and _parse_time(grant.expires_at) <= when:
                continue
            try:
                self.control_registry.assert_grant_current(grant, as_of=generated_at)
            except GovernanceError as exc:
                revalidation.add(f"access:grant:{grant.grant_id}:{exc}")

        for exception in exceptions:
            if exception.institution_id != institution_id:
                raise GovernanceError("dossier exception uses different institution")
            self.asset_registry.principal(institution_id, exception.owner_id)

        registry_artifacts = self._collect_registry_artifacts(institution_id)
        artifacts = registry_artifacts + assurance
        artifacts = sorted({item.artifact_id: item for item in artifacts}.values(), key=lambda x: (x.domain, x.artifact_type, x.artifact_id))

        inventory_artifacts = [x for x in artifacts if x.domain == "inventory"]
        semantic_artifacts = [x for x in artifacts if x.domain == "semantic"]
        lineage_artifacts = [x for x in artifacts if x.domain == "lineage"]
        quality_artifacts = [x for x in artifacts if x.domain == "quality"]
        control_artifacts = [x for x in artifacts if x.domain == "access_retention_privacy"]
        assurance_artifacts = [x for x in artifacts if x.domain == "assurance"]

        inventory_digest = _inventory_snapshot(institution_id, inventory_artifacts)
        semantic_digest = _semantic_snapshot(institution_id, inventory_digest, semantic_artifacts)
        lineage_digest = _lineage_snapshot(institution_id, inventory_digest, semantic_digest, lineage_artifacts)
        quality_digest = _quality_snapshot(institution_id, inventory_digest, semantic_digest, quality_artifacts)
        control_digest = _control_snapshot(institution_id, inventory_digest, semantic_digest, control_artifacts)
        assurance_digest = _assurance_snapshot(institution_id, assurance_artifacts)

        expected_runtime = {
            "inventory": self.asset_registry.snapshot_digest(institution_id),
            "semantic": self.semantic_registry.snapshot_digest(institution_id),
            "lineage": self.lineage_registry.snapshot_digest(institution_id),
            "quality": self.quality_registry.snapshot_digest(institution_id),
            "access_retention_privacy": self.control_registry.snapshot_digest(institution_id),
        }
        recomputed = {
            "inventory": inventory_digest,
            "semantic": semantic_digest,
            "lineage": lineage_digest,
            "quality": quality_digest,
            "access_retention_privacy": control_digest,
        }
        if expected_runtime != recomputed:
            raise GovernanceError("embedded dossier artifacts do not reproduce governed registry snapshots")

        domain_snapshots = tuple(sorted((
            DomainSnapshot("inventory", inventory_digest, tuple(sorted(x.digest for x in inventory_artifacts))),
            DomainSnapshot("semantic", semantic_digest, tuple(sorted(x.digest for x in semantic_artifacts))),
            DomainSnapshot("lineage", lineage_digest, tuple(sorted(x.digest for x in lineage_artifacts))),
            DomainSnapshot("quality", quality_digest, tuple(sorted(x.digest for x in quality_artifacts))),
            DomainSnapshot("access_retention_privacy", control_digest, tuple(sorted(x.digest for x in control_artifacts))),
            DomainSnapshot("assurance", assurance_digest, tuple(sorted(x.digest for x in assurance_artifacts))),
        ), key=lambda x: x.domain))

        active_exceptions = tuple(sorted(
            exception.artifact_digest
            for exception in exceptions
            if _parse_time(exception.approved_at) <= when < _parse_time(exception.expires_at)
        ))
        covered: set[str] = set()
        for exception in exceptions:
            if exception.artifact_digest in active_exceptions:
                covered.update(exception.finding_codes)

        all_findings = tuple(sorted(gap_findings | revalidation))
        revalidation_findings = tuple(sorted(revalidation))
        uncovered_gaps = gap_findings - covered
        if revalidation:
            state = DossierState.REVALIDATION_REQUIRED
        elif uncovered_gaps:
            state = DossierState.WITH_GAPS
        elif gap_findings:
            state = DossierState.WITH_EXCEPTIONS
        else:
            state = DossierState.CURRENT

        coverage: dict[str, int] = {}
        for artifact in artifacts:
            coverage[artifact.domain] = coverage.get(artifact.domain, 0) + 1

        return GovernanceDossier(
            schema_version=DOSSIER_SCHEMA_VERSION,
            release_version=RELEASE_VERSION,
            institution_id=institution_id,
            generated_at=generated_at,
            source_revision=source_revision,
            state=state,
            findings=all_findings,
            revalidation_findings=revalidation_findings,
            active_exception_digests=active_exceptions,
            coverage=dict(sorted(coverage.items())),
            domain_snapshots=domain_snapshots,
            artifacts=tuple(artifacts),
            exceptions=tuple(sorted(exceptions, key=lambda x: x.exception_id)),
        )


def dossier_document(dossier: GovernanceDossier) -> dict[str, Any]:
    import json

    payload = json.loads(canonical_json(dossier))
    return {"dossier": payload, "dossier_digest": digest_artifact(payload)}


def _artifact_from_document(value: dict[str, Any]) -> GovernanceArtifact:
    return GovernanceArtifact(
        domain=value["domain"],
        artifact_type=value["artifact_type"],
        artifact_id=value["artifact_id"],
        payload=value["payload"],
        digest=value["digest"],
    )


def _domain_snapshot_from_document(value: dict[str, Any]) -> DomainSnapshot:
    return DomainSnapshot(
        domain=value["domain"],
        source_snapshot_digest=value["source_snapshot_digest"],
        artifact_digests=tuple(value["artifact_digests"]),
    )


def verify_dossier_document(document: dict[str, Any]) -> str:
    if not isinstance(document, dict) or set(document) != {"dossier", "dossier_digest"}:
        raise GovernanceError("dossier document must contain only dossier and dossier_digest")
    dossier = document["dossier"]
    if not isinstance(dossier, dict):
        raise GovernanceError("dossier must be an object")
    _digest("dossier_digest", document["dossier_digest"])
    if digest_artifact(dossier) != document["dossier_digest"]:
        raise GovernanceError("dossier document digest mismatch")
    required = {
        "schema_version", "release_version", "institution_id", "generated_at", "source_revision",
        "state", "findings", "revalidation_findings", "active_exception_digests", "coverage",
        "domain_snapshots", "artifacts", "exceptions", "legal_compliance_determined",
    }
    if set(dossier) != required:
        raise GovernanceError("dossier has unexpected or missing fields")
    if dossier["schema_version"] != DOSSIER_SCHEMA_VERSION or dossier["release_version"] != RELEASE_VERSION:
        raise GovernanceError("unsupported dossier/release version")
    if dossier["legal_compliance_determined"] is not False:
        raise GovernanceError("dossier cannot claim legal compliance")
    institution_id = _text("institution_id", dossier["institution_id"])
    _timestamp("generated_at", dossier["generated_at"])
    _text("source_revision", dossier["source_revision"], limit=256)
    try:
        DossierState(dossier["state"])
    except (TypeError, ValueError) as exc:
        raise GovernanceError("invalid dossier state") from exc

    artifacts = tuple(_artifact_from_document(item) for item in dossier["artifacts"])
    if tuple(sorted(artifacts, key=lambda x: (x.domain, x.artifact_type, x.artifact_id))) != artifacts:
        raise GovernanceError("dossier artifacts are not deterministically sorted")
    if len({item.artifact_id for item in artifacts}) != len(artifacts):
        raise GovernanceError("duplicate dossier artifact identity")

    snapshots = tuple(_domain_snapshot_from_document(item) for item in dossier["domain_snapshots"])
    if tuple(sorted(snapshots, key=lambda x: x.domain)) != snapshots:
        raise GovernanceError("domain snapshots are not sorted")
    by_domain = {domain: [x for x in artifacts if x.domain == domain] for domain in {
        "inventory", "semantic", "lineage", "quality", "access_retention_privacy", "assurance"
    }}
    expected_snapshot_digests = {
        "inventory": _inventory_snapshot(institution_id, by_domain["inventory"]),
    }
    expected_snapshot_digests["semantic"] = _semantic_snapshot(
        institution_id, expected_snapshot_digests["inventory"], by_domain["semantic"]
    )
    expected_snapshot_digests["lineage"] = _lineage_snapshot(
        institution_id, expected_snapshot_digests["inventory"], expected_snapshot_digests["semantic"], by_domain["lineage"]
    )
    expected_snapshot_digests["quality"] = _quality_snapshot(
        institution_id, expected_snapshot_digests["inventory"], expected_snapshot_digests["semantic"], by_domain["quality"]
    )
    expected_snapshot_digests["access_retention_privacy"] = _control_snapshot(
        institution_id, expected_snapshot_digests["inventory"], expected_snapshot_digests["semantic"], by_domain["access_retention_privacy"]
    )
    expected_snapshot_digests["assurance"] = _assurance_snapshot(institution_id, by_domain["assurance"])

    if {item.domain for item in snapshots} != set(expected_snapshot_digests):
        raise GovernanceError("dossier domain snapshot set is incomplete")
    for snapshot in snapshots:
        expected_manifest = tuple(sorted(x.digest for x in by_domain[snapshot.domain]))
        if snapshot.artifact_digests != expected_manifest:
            raise GovernanceError("domain artifact manifest mismatch")
        if snapshot.source_snapshot_digest != expected_snapshot_digests[snapshot.domain]:
            raise GovernanceError("domain source snapshot digest mismatch")

    expected_coverage = {domain: len(items) for domain, items in by_domain.items() if items}
    if dossier["coverage"] != dict(sorted(expected_coverage.items())):
        raise GovernanceError("dossier coverage mismatch")

    findings = dossier["findings"]
    revalidation = dossier["revalidation_findings"]
    if findings != sorted(set(findings)) or revalidation != sorted(set(revalidation)):
        raise GovernanceError("dossier findings must be sorted and unique")
    if not set(revalidation).issubset(set(findings)):
        raise GovernanceError("revalidation findings must be included in findings")

    exception_digests: set[str] = set()
    active_exception_codes: set[str] = set()
    generated = _parse_time(dossier["generated_at"])
    for item in dossier["exceptions"]:
        exception = DossierException(
            institution_id=item["institution_id"],
            exception_id=item["exception_id"],
            owner_id=item["owner_id"],
            finding_codes=tuple(item["finding_codes"]),
            rationale=item["rationale"],
            approved_at=item["approved_at"],
            expires_at=item["expires_at"],
            evidence_digest=item["evidence_digest"],
            schema_version=item["schema_version"],
        )
        if exception.institution_id != institution_id:
            raise GovernanceError("dossier exception institution mismatch")
        exception_digests.add(exception.artifact_digest)
        if _parse_time(exception.approved_at) <= generated < _parse_time(exception.expires_at):
            active_exception_codes.update(exception.finding_codes)
    expected_active = sorted(
        item.artifact_digest
        for item in (
            DossierException(
                institution_id=x["institution_id"], exception_id=x["exception_id"], owner_id=x["owner_id"],
                finding_codes=tuple(x["finding_codes"]), rationale=x["rationale"], approved_at=x["approved_at"],
                expires_at=x["expires_at"], evidence_digest=x["evidence_digest"], schema_version=x["schema_version"]
            ) for x in dossier["exceptions"]
        )
        if _parse_time(item.approved_at) <= generated < _parse_time(item.expires_at)
    )
    if dossier["active_exception_digests"] != expected_active:
        raise GovernanceError("active exception digest set mismatch")

    gaps = set(findings) - set(revalidation)
    uncovered = gaps - active_exception_codes
    expected_state = (
        DossierState.REVALIDATION_REQUIRED.value if revalidation else
        DossierState.WITH_GAPS.value if uncovered else
        DossierState.WITH_EXCEPTIONS.value if gaps else
        DossierState.CURRENT.value
    )
    if dossier["state"] != expected_state:
        raise GovernanceError("dossier aggregate state is inconsistent")
    return document["dossier_digest"]
