from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Iterable

IMAGE_REFERENCE_SCHEMA_VERSION = "datagovops.image-reference.v1"
DEPLOYMENT_EVIDENCE_SCHEMA_VERSION = "datagovops.deployment-evidence.v1"
RUNTIME_OBSERVATION_SCHEMA_VERSION = "datagovops.runtime-observation.v1"
DEPLOYMENT_ASSESSMENT_SCHEMA_VERSION = "datagovops.deployment-assessment.v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _digest(value: str, field: str) -> str:
    value = _text(value, field)
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True, slots=True)
class ImmutableImageReference:
    repository: str
    digest: str
    schema_version: str = IMAGE_REFERENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "digest", _digest(self.digest, "digest"))
        if ":" in self.repository.rsplit("/", 1)[-1]:
            raise ValueError("repository must not include a mutable image tag")

    @property
    def canonical(self) -> str:
        return f"{self.repository}@sha256:{self.digest}"


@dataclass(frozen=True, slots=True)
class SecretInjectionReference:
    provider: str
    secret_id: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _text(self.provider, "provider"))
        object.__setattr__(self, "secret_id", _text(self.secret_id, "secret_id"))
        object.__setattr__(self, "version", _text(self.version, "version"))


@dataclass(frozen=True, slots=True)
class RuntimeSecurityProfile:
    run_as_non_root: bool
    read_only_root_filesystem: bool
    allow_privilege_escalation: bool
    privileged: bool
    drop_all_capabilities: bool
    seccomp_runtime_default: bool
    host_network: bool
    host_pid: bool
    host_ipc: bool
    automount_service_account_token: bool


@dataclass(frozen=True, slots=True)
class NetworkBoundary:
    default_deny_ingress: bool
    default_deny_egress: bool
    allowed_egress_destinations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(sorted({_text(v, "allowed_egress_destination") for v in self.allowed_egress_destinations}))
        object.__setattr__(self, "allowed_egress_destinations", normalized)


@dataclass(frozen=True, slots=True)
class DeploymentEvidence:
    institution_id: str
    environment_id: str
    workload_id: str
    image: ImmutableImageReference
    runtime_security: RuntimeSecurityProfile
    network_boundary: NetworkBoundary
    secret_references: tuple[SecretInjectionReference, ...]
    manifest_sha256: str
    validator_id: str
    observed_at: int
    negative_path_confirmed: bool
    schema_version: str = DEPLOYMENT_EVIDENCE_SCHEMA_VERSION
    production_deployment_validated: bool = False

    def __post_init__(self) -> None:
        for field in ("institution_id", "environment_id", "workload_id", "validator_id"):
            object.__setattr__(self, field, _text(getattr(self, field), field))
        object.__setattr__(self, "manifest_sha256", _digest(self.manifest_sha256, "manifest_sha256"))
        if not isinstance(self.observed_at, int) or isinstance(self.observed_at, bool) or self.observed_at < 0:
            raise ValueError("observed_at must be a non-negative integer")
        refs = tuple(sorted(self.secret_references, key=lambda r: (r.provider, r.secret_id, r.version)))
        if len({(r.provider, r.secret_id, r.version) for r in refs}) != len(refs):
            raise ValueError("secret references must be unique")
        object.__setattr__(self, "secret_references", refs)
        if self.production_deployment_validated is not False:
            raise ValueError("reference evidence cannot claim production deployment validation")


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    institution_id: str
    environment_id: str
    workload_id: str
    observation_type: str
    status: str
    evidence_sha256: str
    observed_at: int
    raw_content_logged: bool = False
    secret_material_logged: bool = False
    production_observability_validated: bool = False
    schema_version: str = RUNTIME_OBSERVATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in ("institution_id", "environment_id", "workload_id", "observation_type", "status"):
            object.__setattr__(self, field, _text(getattr(self, field), field))
        object.__setattr__(self, "evidence_sha256", _digest(self.evidence_sha256, "evidence_sha256"))
        if not isinstance(self.observed_at, int) or isinstance(self.observed_at, bool) or self.observed_at < 0:
            raise ValueError("observed_at must be a non-negative integer")
        if self.raw_content_logged or self.secret_material_logged or self.production_observability_validated:
            raise ValueError("runtime observations are metadata-only reference evidence")


class DeploymentControlState(str, Enum):
    REPRESENTED = "represented"
    GAP = "gap"


class DeploymentAssuranceState(str, Enum):
    REPRESENTED = "represented"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class DeploymentControlAssessment:
    control_id: str
    state: DeploymentControlState
    rationale: str


@dataclass(frozen=True, slots=True)
class DeploymentAssessment:
    institution_id: str
    environment_id: str
    workload_id: str
    evidence_sha256: str
    state: DeploymentAssuranceState
    controls: tuple[DeploymentControlAssessment, ...]
    assessed_at: int
    requires_human_review: bool = True
    production_effectiveness_determined: bool = False
    supply_chain_security_determined: bool = False
    regulatory_compliance_determined: bool = False
    schema_version: str = DEPLOYMENT_ASSESSMENT_SCHEMA_VERSION


def deployment_evidence_document(evidence: DeploymentEvidence) -> dict[str, object]:
    payload = asdict(evidence)
    payload["image"]["canonical"] = evidence.image.canonical
    return payload


def deployment_evidence_digest(evidence: DeploymentEvidence) -> str:
    return hashlib.sha256(canonical_json(deployment_evidence_document(evidence)).encode("utf-8")).hexdigest()


def assess_deployment(evidence: DeploymentEvidence, *, assessed_at: int) -> DeploymentAssessment:
    if not isinstance(assessed_at, int) or isinstance(assessed_at, bool) or assessed_at < 0:
        raise ValueError("assessed_at must be a non-negative integer")
    if assessed_at < evidence.observed_at:
        raise ValueError("assessed_at cannot precede observed_at")

    profile = evidence.runtime_security
    network = evidence.network_boundary
    checks: tuple[tuple[str, bool, str], ...] = (
        ("immutable_image_digest", bool(evidence.image.digest), "workload image is bound to a SHA-256 digest"),
        ("run_as_non_root", profile.run_as_non_root, "runtime requires a non-root identity"),
        ("read_only_root_filesystem", profile.read_only_root_filesystem, "root filesystem is represented read-only"),
        ("privilege_escalation_disabled", not profile.allow_privilege_escalation, "privilege escalation is disabled"),
        ("privileged_mode_disabled", not profile.privileged, "privileged container mode is disabled"),
        ("linux_capabilities_dropped", profile.drop_all_capabilities, "all Linux capabilities are dropped"),
        ("seccomp_runtime_default", profile.seccomp_runtime_default, "RuntimeDefault seccomp is represented"),
        ("host_namespaces_disabled", not (profile.host_network or profile.host_pid or profile.host_ipc), "host network/PID/IPC namespaces are disabled"),
        ("service_account_token_disabled", not profile.automount_service_account_token, "service-account token automount is disabled"),
        ("default_deny_ingress", network.default_deny_ingress, "default-deny ingress is represented"),
        ("default_deny_egress", network.default_deny_egress, "default-deny egress is represented"),
        ("external_secret_references", all(isinstance(r, SecretInjectionReference) for r in evidence.secret_references), "secrets are represented only by external references"),
        ("validator_negative_path", evidence.negative_path_confirmed, "validator negative path was represented as exercised"),
    )
    controls = tuple(
        DeploymentControlAssessment(
            control_id=control_id,
            state=DeploymentControlState.REPRESENTED if passed else DeploymentControlState.GAP,
            rationale=rationale,
        )
        for control_id, passed, rationale in checks
    )
    state = (
        DeploymentAssuranceState.REPRESENTED
        if all(item.state is DeploymentControlState.REPRESENTED for item in controls)
        else DeploymentAssuranceState.INCOMPLETE
    )
    return DeploymentAssessment(
        institution_id=evidence.institution_id,
        environment_id=evidence.environment_id,
        workload_id=evidence.workload_id,
        evidence_sha256=deployment_evidence_digest(evidence),
        state=state,
        controls=controls,
        assessed_at=assessed_at,
    )


def assert_same_institution(institution_id: str, artifacts: Iterable[object]) -> None:
    institution_id = _text(institution_id, "institution_id")
    for artifact in artifacts:
        if getattr(artifact, "institution_id", None) != institution_id:
            raise ValueError("cross-institution deployment evidence is not allowed")
