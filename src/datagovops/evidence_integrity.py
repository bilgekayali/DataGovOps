from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .dossier_verify_v02 import verify_dossier_document
from .models import GovernanceError, canonical_json, digest_artifact


SIGNED_EVIDENCE_SCHEMA_VERSION = "datagovops.signed-governance-evidence.v1"
ANCHOR_SCHEMA_VERSION = "datagovops.external-anchor-receipt.v1"
PROVENANCE_SCHEMA_VERSION = "datagovops.build-provenance.v1"
RELEASE_MANIFEST_SCHEMA_VERSION = "datagovops.release-evidence-manifest.v1"
SIGNATURE_ALGORITHM = "Ed25519"
SIGNATURE_SCOPE = "canonical-json-v1"


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceError(f"{name} must be non-empty text")
    return value.strip()


def _digest(name: str, value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise GovernanceError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _git_revision(value: Any) -> str:
    value = _text("source_revision", value)
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise GovernanceError("source_revision must be a full lowercase Git SHA-1")
    return value


def _timestamp(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceError(f"{name} must be a non-negative integer timestamp")
    return value


def _safe_path(value: Any) -> str:
    value = _text("artifact path", value)
    if "\\" in value:
        raise GovernanceError("artifact path must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise GovernanceError("artifact path must be a normalized relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise GovernanceError("artifact path cannot contain empty, dot, or parent segments")
    return value


def _canonical_object(value: Any) -> dict[str, Any]:
    normalized = json.loads(canonical_json(value))
    if not isinstance(normalized, dict):
        raise GovernanceError("canonical value must be an object")
    return normalized


def _sha256_bytes(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise GovernanceError("artifact content must be bytes")
    return hashlib.sha256(content).hexdigest()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: Any) -> bytes:
    if not isinstance(value, str) or not value:
        raise GovernanceError("signature must be non-empty base64url text")
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except Exception as exc:
        raise GovernanceError("signature is not valid base64url") from exc


@dataclass(frozen=True, slots=True)
class SigningKeyReference:
    provider: str
    key_id: str
    key_version: str

    def __post_init__(self) -> None:
        for name in ("provider", "key_id", "key_version"):
            value = _text(name, getattr(self, name))
            lowered = value.lower()
            if any(marker in lowered for marker in ("-----begin", "private key", "secret=", "password=")):
                raise GovernanceError(f"{name} must be a key reference, not secret material")
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceStatement:
    schema_version: str
    institution_id: str
    dossier_digest: str
    release_version: str
    source_revision: str
    signer_id: str
    key_reference: SigningKeyReference
    signed_at: int
    legal_compliance_determined: bool = False
    supervisory_acceptance_determined: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SIGNED_EVIDENCE_SCHEMA_VERSION:
            raise GovernanceError("unsupported signed-governance-evidence schema version")
        for name in ("institution_id", "release_version", "source_revision", "signer_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        _digest("dossier_digest", self.dossier_digest)
        if not isinstance(self.key_reference, SigningKeyReference):
            raise GovernanceError("key_reference must be a SigningKeyReference")
        _timestamp("signed_at", self.signed_at)
        if self.legal_compliance_determined is not False:
            raise GovernanceError("signed governance evidence cannot determine legal compliance")
        if self.supervisory_acceptance_determined is not False:
            raise GovernanceError("signed governance evidence cannot determine supervisory acceptance")

    @property
    def statement_digest(self) -> str:
        return digest_artifact(self)


def governance_evidence_statement(
    dossier_document: dict[str, Any],
    *,
    signer_id: str,
    key_reference: SigningKeyReference,
    signed_at: int,
) -> GovernanceEvidenceStatement:
    dossier_digest = verify_dossier_document(dossier_document)
    dossier = dossier_document["dossier"]
    return GovernanceEvidenceStatement(
        schema_version=SIGNED_EVIDENCE_SCHEMA_VERSION,
        institution_id=dossier["institution_id"],
        dossier_digest=dossier_digest,
        release_version=dossier["release_version"],
        source_revision=dossier["source_revision"],
        signer_id=signer_id,
        key_reference=key_reference,
        signed_at=signed_at,
    )


def signing_bytes(statement: GovernanceEvidenceStatement) -> bytes:
    if not isinstance(statement, GovernanceEvidenceStatement):
        raise GovernanceError("statement must be GovernanceEvidenceStatement")
    return canonical_json(_canonical_object(statement)).encode("utf-8")


def signed_governance_evidence_document(
    statement: GovernanceEvidenceStatement,
    signature: bytes,
) -> dict[str, Any]:
    if not isinstance(signature, bytes) or len(signature) != 64:
        raise GovernanceError("Ed25519 signature must be exactly 64 bytes")
    payload = _canonical_object(statement)
    return {
        "statement": payload,
        "statement_digest": digest_artifact(payload),
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signature_scope": SIGNATURE_SCOPE,
        "signature_b64url": _b64url_encode(signature),
    }


def _key_reference_from_payload(value: Any) -> SigningKeyReference:
    if not isinstance(value, dict) or set(value) != {"provider", "key_id", "key_version"}:
        raise GovernanceError("signing key reference has unexpected fields")
    return SigningKeyReference(
        provider=value["provider"],
        key_id=value["key_id"],
        key_version=value["key_version"],
    )


def _statement_from_payload(payload: Any) -> GovernanceEvidenceStatement:
    required = {
        "schema_version",
        "institution_id",
        "dossier_digest",
        "release_version",
        "source_revision",
        "signer_id",
        "key_reference",
        "signed_at",
        "legal_compliance_determined",
        "supervisory_acceptance_determined",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise GovernanceError("signed governance statement has unexpected fields")
    return GovernanceEvidenceStatement(
        schema_version=payload["schema_version"],
        institution_id=payload["institution_id"],
        dossier_digest=payload["dossier_digest"],
        release_version=payload["release_version"],
        source_revision=payload["source_revision"],
        signer_id=payload["signer_id"],
        key_reference=_key_reference_from_payload(payload["key_reference"]),
        signed_at=payload["signed_at"],
        legal_compliance_determined=payload["legal_compliance_determined"],
        supervisory_acceptance_determined=payload["supervisory_acceptance_determined"],
    )


def verify_signed_governance_evidence_document(
    document: Any,
    public_key: Ed25519PublicKey,
    dossier_document: dict[str, Any],
) -> str:
    required = {
        "statement",
        "statement_digest",
        "signature_algorithm",
        "signature_scope",
        "signature_b64url",
    }
    if not isinstance(document, dict) or set(document) != required:
        raise GovernanceError("signed governance evidence document has unexpected fields")
    if document["signature_algorithm"] != SIGNATURE_ALGORITHM or document["signature_scope"] != SIGNATURE_SCOPE:
        raise GovernanceError("unsupported governance-evidence signature profile")
    payload = document["statement"]
    statement = _statement_from_payload(payload)
    expected_digest = digest_artifact(payload)
    if document["statement_digest"] != expected_digest:
        raise GovernanceError("signed governance statement digest mismatch")
    if not isinstance(public_key, Ed25519PublicKey):
        raise GovernanceError("public_key must be an Ed25519 public key")

    dossier_digest = verify_dossier_document(dossier_document)
    dossier = dossier_document["dossier"]
    if statement.dossier_digest != dossier_digest:
        raise GovernanceError("signed statement is bound to a different dossier")
    for field in ("institution_id", "release_version", "source_revision"):
        if getattr(statement, field) != dossier[field]:
            raise GovernanceError(f"signed statement {field} does not match dossier")
    try:
        public_key.verify(_b64url_decode(document["signature_b64url"]), canonical_json(payload).encode("utf-8"))
    except (InvalidSignature, ValueError) as exc:
        raise GovernanceError("signed governance evidence signature verification failed") from exc
    return expected_digest


@dataclass(frozen=True, slots=True)
class ExternalAnchorReceipt:
    schema_version: str
    institution_id: str
    evidence_digest: str
    provider: str
    anchor_id: str
    anchored_at: int
    timestamp_token_sha256: str
    external_anchor_validated: bool = False
    trusted_timestamp_validated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != ANCHOR_SCHEMA_VERSION:
            raise GovernanceError("unsupported external-anchor schema version")
        for name in ("institution_id", "provider", "anchor_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        _digest("evidence_digest", self.evidence_digest)
        _timestamp("anchored_at", self.anchored_at)
        _digest("timestamp_token_sha256", self.timestamp_token_sha256)
        if self.external_anchor_validated is not False or self.trusted_timestamp_validated is not False:
            raise GovernanceError("reference anchor receipt cannot claim external validation")

    @property
    def receipt_digest(self) -> str:
        return digest_artifact(self)


def external_anchor_receipt_document(receipt: ExternalAnchorReceipt) -> dict[str, Any]:
    payload = _canonical_object(receipt)
    return {"anchor": payload, "anchor_digest": digest_artifact(payload)}


def verify_external_anchor_receipt_document(document: Any, *, expected_evidence_digest: str) -> str:
    if not isinstance(document, dict) or set(document) != {"anchor", "anchor_digest"}:
        raise GovernanceError("external anchor receipt document has unexpected fields")
    payload = document["anchor"]
    if not isinstance(payload, dict) or document["anchor_digest"] != digest_artifact(payload):
        raise GovernanceError("external anchor receipt digest mismatch")
    required = {
        "schema_version",
        "institution_id",
        "evidence_digest",
        "provider",
        "anchor_id",
        "anchored_at",
        "timestamp_token_sha256",
        "external_anchor_validated",
        "trusted_timestamp_validated",
    }
    if set(payload) != required:
        raise GovernanceError("external anchor receipt has unexpected fields")
    receipt = ExternalAnchorReceipt(**payload)
    if receipt.evidence_digest != _digest("expected_evidence_digest", expected_evidence_digest):
        raise GovernanceError("external anchor receipt is bound to different evidence")
    return document["anchor_digest"]


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    path: str
    sha256: str
    size: int
    media_type: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _safe_path(self.path))
        _digest("artifact sha256", self.sha256)
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size < 0:
            raise GovernanceError("artifact size must be a non-negative integer")
        object.__setattr__(self, "media_type", _text("media_type", self.media_type))


def descriptor_from_bytes(path: str, content: bytes, media_type: str) -> ArtifactDescriptor:
    return ArtifactDescriptor(path=path, sha256=_sha256_bytes(content), size=len(content), media_type=media_type)


@dataclass(frozen=True, slots=True)
class SourceMaterial:
    uri: str
    revision: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "uri", _text("material uri", self.uri))
        object.__setattr__(self, "revision", _git_revision(self.revision))


@dataclass(frozen=True, slots=True)
class BuildProvenance:
    schema_version: str
    package_name: str
    package_version: str
    source_revision: str
    builder_id: str
    build_type: str
    invocation_id: str
    started_at: int
    finished_at: int
    subjects: tuple[ArtifactDescriptor, ...]
    materials: tuple[SourceMaterial, ...]
    production_build_attested: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != PROVENANCE_SCHEMA_VERSION:
            raise GovernanceError("unsupported build-provenance schema version")
        for name in ("package_name", "package_version", "builder_id", "build_type", "invocation_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        object.__setattr__(self, "source_revision", _git_revision(self.source_revision))
        _timestamp("started_at", self.started_at)
        _timestamp("finished_at", self.finished_at)
        if self.finished_at < self.started_at:
            raise GovernanceError("provenance finished_at cannot precede started_at")
        if not self.subjects:
            raise GovernanceError("provenance must contain at least one subject")
        paths = [item.path for item in self.subjects]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise GovernanceError("provenance subjects must be sorted by unique path")
        if not self.materials:
            raise GovernanceError("provenance must contain at least one material")
        keys = [(item.uri, item.revision) for item in self.materials]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise GovernanceError("provenance materials must be sorted and unique")
        if self.production_build_attested is not False:
            raise GovernanceError("reference provenance cannot claim production build attestation")

    @property
    def provenance_digest(self) -> str:
        return digest_artifact(self)


def provenance_document(provenance: BuildProvenance) -> dict[str, Any]:
    payload = _canonical_object(provenance)
    return {"provenance": payload, "provenance_digest": digest_artifact(payload)}


def _descriptor_from_payload(value: Any) -> ArtifactDescriptor:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "size", "media_type"}:
        raise GovernanceError("artifact descriptor has unexpected fields")
    return ArtifactDescriptor(**value)


def _source_material_from_payload(value: Any) -> SourceMaterial:
    if not isinstance(value, dict) or set(value) != {"uri", "revision"}:
        raise GovernanceError("source material has unexpected fields")
    return SourceMaterial(**value)


def verify_provenance_document(document: Any) -> str:
    if not isinstance(document, dict) or set(document) != {"provenance", "provenance_digest"}:
        raise GovernanceError("provenance document has unexpected fields")
    payload = document["provenance"]
    if not isinstance(payload, dict) or document["provenance_digest"] != digest_artifact(payload):
        raise GovernanceError("provenance digest mismatch")
    required = {
        "schema_version",
        "package_name",
        "package_version",
        "source_revision",
        "builder_id",
        "build_type",
        "invocation_id",
        "started_at",
        "finished_at",
        "subjects",
        "materials",
        "production_build_attested",
    }
    if set(payload) != required or not isinstance(payload["subjects"], list) or not isinstance(payload["materials"], list):
        raise GovernanceError("provenance payload has unexpected fields")
    BuildProvenance(
        schema_version=payload["schema_version"],
        package_name=payload["package_name"],
        package_version=payload["package_version"],
        source_revision=payload["source_revision"],
        builder_id=payload["builder_id"],
        build_type=payload["build_type"],
        invocation_id=payload["invocation_id"],
        started_at=payload["started_at"],
        finished_at=payload["finished_at"],
        subjects=tuple(_descriptor_from_payload(item) for item in payload["subjects"]),
        materials=tuple(_source_material_from_payload(item) for item in payload["materials"]),
        production_build_attested=payload["production_build_attested"],
    )
    return document["provenance_digest"]


def build_dependency_sbom(
    package_name: str,
    package_version: str,
    dependencies: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    name = _text("package_name", package_name)
    version = _text("package_version", package_version)
    normalized = sorted(
        set(
            (
                _text("dependency name", dep_name).lower().replace("_", "-"),
                _text("dependency version", dep_version),
            )
            for dep_name, dep_version in dependencies
        )
    )
    components = [
        {"type": "library", "name": dep_name, "version": dep_version, "purl": f"pkg:pypi/{dep_name}@{dep_version}"}
        for dep_name, dep_version in normalized
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {"component": {"type": "application", "name": name, "version": version}},
        "components": components,
        "datagovops_nonclaims": {
            "complete_transitive_inventory": False,
            "vulnerability_assessment_performed": False,
        },
    }


def verify_dependency_sbom(
    sbom: Any,
    *,
    expected_package_name: str,
    expected_package_version: str,
) -> str:
    if not isinstance(sbom, dict) or set(sbom) != {
        "bomFormat",
        "specVersion",
        "version",
        "metadata",
        "components",
        "datagovops_nonclaims",
    }:
        raise GovernanceError("dependency SBOM has unexpected fields")
    if sbom["bomFormat"] != "CycloneDX" or sbom["specVersion"] != "1.6" or sbom["version"] != 1:
        raise GovernanceError("unsupported dependency SBOM profile")
    metadata = sbom["metadata"]
    expected_component = {
        "type": "application",
        "name": _text("expected_package_name", expected_package_name),
        "version": _text("expected_package_version", expected_package_version),
    }
    if not isinstance(metadata, dict) or metadata != {"component": expected_component}:
        raise GovernanceError("dependency SBOM package identity mismatch")
    if not isinstance(sbom["components"], list):
        raise GovernanceError("dependency SBOM components must be an array")
    keys: list[tuple[str, str]] = []
    for item in sbom["components"]:
        if not isinstance(item, dict) or set(item) != {"type", "name", "version", "purl"} or item["type"] != "library":
            raise GovernanceError("dependency SBOM component is malformed")
        dep_name = _text("dependency name", item["name"]).lower().replace("_", "-")
        dep_version = _text("dependency version", item["version"])
        if item["purl"] != f"pkg:pypi/{dep_name}@{dep_version}":
            raise GovernanceError("dependency SBOM purl is inconsistent")
        keys.append((dep_name, dep_version))
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise GovernanceError("dependency SBOM components must be sorted and unique")
    if sbom["datagovops_nonclaims"] != {
        "complete_transitive_inventory": False,
        "vulnerability_assessment_performed": False,
    }:
        raise GovernanceError("dependency SBOM non-claims are invalid")
    return digest_artifact(sbom)


@dataclass(frozen=True, slots=True)
class ReleaseEvidenceManifest:
    schema_version: str
    package_name: str
    package_version: str
    source_revision: str
    artifacts: tuple[ArtifactDescriptor, ...]
    provenance_path: str
    sbom_path: str
    signed_governance_evidence_path: str
    anchor_receipt_path: str
    formal_release_attested: bool = False
    production_readiness_determined: bool = False
    regulatory_compliance_determined: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RELEASE_MANIFEST_SCHEMA_VERSION:
            raise GovernanceError("unsupported release-evidence-manifest schema version")
        for name in ("package_name", "package_version"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        object.__setattr__(self, "source_revision", _git_revision(self.source_revision))
        if not self.artifacts:
            raise GovernanceError("release evidence manifest must contain artifacts")
        paths = [item.path for item in self.artifacts]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise GovernanceError("release evidence artifacts must be sorted by unique path")
        special_paths = []
        for name in (
            "provenance_path",
            "sbom_path",
            "signed_governance_evidence_path",
            "anchor_receipt_path",
        ):
            value = _safe_path(getattr(self, name))
            object.__setattr__(self, name, value)
            special_paths.append(value)
        if len(set(special_paths)) != len(special_paths):
            raise GovernanceError("release evidence special artifact paths must be distinct")
        if not set(special_paths).issubset(set(paths)):
            raise GovernanceError("release evidence manifest is missing a required evidence artifact")
        if self.formal_release_attested is not False:
            raise GovernanceError("preview manifest cannot claim formal release attestation")
        if self.production_readiness_determined is not False:
            raise GovernanceError("release evidence cannot determine production readiness")
        if self.regulatory_compliance_determined is not False:
            raise GovernanceError("release evidence cannot determine regulatory compliance")

    @property
    def manifest_digest(self) -> str:
        return digest_artifact(self)


def release_manifest_document(manifest: ReleaseEvidenceManifest) -> dict[str, Any]:
    payload = _canonical_object(manifest)
    return {"manifest": payload, "manifest_digest": digest_artifact(payload)}


def _manifest_from_payload(payload: Any) -> ReleaseEvidenceManifest:
    required = {
        "schema_version",
        "package_name",
        "package_version",
        "source_revision",
        "artifacts",
        "provenance_path",
        "sbom_path",
        "signed_governance_evidence_path",
        "anchor_receipt_path",
        "formal_release_attested",
        "production_readiness_determined",
        "regulatory_compliance_determined",
    }
    if not isinstance(payload, dict) or set(payload) != required or not isinstance(payload["artifacts"], list):
        raise GovernanceError("release evidence manifest has unexpected fields")
    return ReleaseEvidenceManifest(
        schema_version=payload["schema_version"],
        package_name=payload["package_name"],
        package_version=payload["package_version"],
        source_revision=payload["source_revision"],
        artifacts=tuple(_descriptor_from_payload(item) for item in payload["artifacts"]),
        provenance_path=payload["provenance_path"],
        sbom_path=payload["sbom_path"],
        signed_governance_evidence_path=payload["signed_governance_evidence_path"],
        anchor_receipt_path=payload["anchor_receipt_path"],
        formal_release_attested=payload["formal_release_attested"],
        production_readiness_determined=payload["production_readiness_determined"],
        regulatory_compliance_determined=payload["regulatory_compliance_determined"],
    )


def verify_release_manifest_document(document: Any, artifact_contents: Mapping[str, bytes]) -> str:
    if not isinstance(document, dict) or set(document) != {"manifest", "manifest_digest"}:
        raise GovernanceError("release evidence manifest document has unexpected fields")
    payload = document["manifest"]
    if not isinstance(payload, dict) or document["manifest_digest"] != digest_artifact(payload):
        raise GovernanceError("release evidence manifest digest mismatch")
    manifest = _manifest_from_payload(payload)
    expected_paths = {item.path for item in manifest.artifacts}
    if set(artifact_contents) != expected_paths:
        raise GovernanceError("release evidence artifact set differs from manifest")
    by_path = {item.path: item for item in manifest.artifacts}
    for path, content in artifact_contents.items():
        descriptor = by_path[path]
        if not isinstance(content, bytes):
            raise GovernanceError("release evidence artifact content must be bytes")
        if len(content) != descriptor.size or _sha256_bytes(content) != descriptor.sha256:
            raise GovernanceError(f"release evidence artifact integrity mismatch: {path}")

    try:
        provenance = json.loads(artifact_contents[manifest.provenance_path].decode("utf-8"))
        sbom = json.loads(artifact_contents[manifest.sbom_path].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GovernanceError("release evidence provenance/SBOM must be UTF-8 JSON") from exc
    verify_provenance_document(provenance)
    provenance_payload = provenance["provenance"]
    if (
        provenance_payload["package_name"] != manifest.package_name
        or provenance_payload["package_version"] != manifest.package_version
        or provenance_payload["source_revision"] != manifest.source_revision
    ):
        raise GovernanceError("release manifest and provenance identity mismatch")
    verify_dependency_sbom(
        sbom,
        expected_package_name=manifest.package_name,
        expected_package_version=manifest.package_version,
    )
    return document["manifest_digest"]
