from __future__ import annotations

import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import canonical_json
from datagovops.evidence_integrity import (
    ANCHOR_SCHEMA_VERSION,
    PROVENANCE_SCHEMA_VERSION,
    RELEASE_MANIFEST_SCHEMA_VERSION,
    ArtifactDescriptor,
    BuildProvenance,
    ExternalAnchorReceipt,
    GovernanceEvidenceStatement,
    ReleaseEvidenceManifest,
    SIGNED_EVIDENCE_SCHEMA_VERSION,
    SigningKeyReference,
    SourceMaterial,
    build_dependency_sbom,
    external_anchor_receipt_document,
    provenance_document,
    release_manifest_document,
    signed_governance_evidence_document,
)


ROOT = Path(__file__).resolve().parents[1]
REV = "a" * 40


class EvidenceIntegritySchemaTests(unittest.TestCase):
    def _schema(self, name: str):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        self.assertFalse(schema["additionalProperties"])
        return schema

    def test_runtime_artifacts_validate_against_strict_schemas(self):
        key_ref = SigningKeyReference("institution-kms", "key-1", "v1")
        statement = GovernanceEvidenceStatement(
            schema_version=SIGNED_EVIDENCE_SCHEMA_VERSION,
            institution_id="bank-a",
            dossier_digest="1" * 64,
            release_version="0.4.0",
            source_revision=REV,
            signer_id="chief-data-officer",
            key_reference=key_ref,
            signed_at=1787649300,
        )
        signed = signed_governance_evidence_document(statement, b"s" * 64)
        anchor = external_anchor_receipt_document(
            ExternalAnchorReceipt(
                schema_version=ANCHOR_SCHEMA_VERSION,
                institution_id="bank-a",
                evidence_digest=statement.statement_digest,
                provider="external-anchor",
                anchor_id="anchor-1",
                anchored_at=1787649400,
                timestamp_token_sha256="2" * 64,
            )
        )
        wheel = ArtifactDescriptor("dist/datagovops.whl", "3" * 64, 10, "application/zip")
        provenance = provenance_document(
            BuildProvenance(
                schema_version=PROVENANCE_SCHEMA_VERSION,
                package_name="datagovops",
                package_version="0.4.0",
                source_revision=REV,
                builder_id="github-actions/reference",
                build_type="python-wheel",
                invocation_id="fixture",
                started_at=1,
                finished_at=2,
                subjects=(wheel,),
                materials=(SourceMaterial("https://github.com/bilgekayali/DataGovOps", REV),),
            )
        )
        sbom = build_dependency_sbom("datagovops", "0.4.0", (("cryptography", "46.0.0"),))
        artifacts = tuple(
            sorted(
                (
                    ArtifactDescriptor("dist/datagovops.whl", "3" * 64, 10, "application/zip"),
                    ArtifactDescriptor("evidence/anchor.json", "4" * 64, 10, "application/json"),
                    ArtifactDescriptor("evidence/provenance.json", "5" * 64, 10, "application/json"),
                    ArtifactDescriptor("evidence/sbom.json", "6" * 64, 10, "application/json"),
                    ArtifactDescriptor("evidence/signed.json", "7" * 64, 10, "application/json"),
                ),
                key=lambda item: item.path,
            )
        )
        manifest = release_manifest_document(
            ReleaseEvidenceManifest(
                schema_version=RELEASE_MANIFEST_SCHEMA_VERSION,
                package_name="datagovops",
                package_version="0.4.0",
                source_revision=REV,
                artifacts=artifacts,
                provenance_path="evidence/provenance.json",
                sbom_path="evidence/sbom.json",
                signed_governance_evidence_path="evidence/signed.json",
                anchor_receipt_path="evidence/anchor.json",
            )
        )

        fixtures = {
            "signed-governance-evidence.schema.json": signed,
            "external-anchor-receipt.schema.json": anchor,
            "build-provenance.schema.json": provenance,
            "dependency-sbom.schema.json": sbom,
            "release-evidence-manifest.schema.json": manifest,
        }
        for name, document in fixtures.items():
            with self.subTest(schema=name):
                jsonschema.Draft202012Validator(self._schema(name)).validate(
                    json.loads(canonical_json(document))
                )

    def test_nonclaims_are_structurally_false(self):
        signed = self._schema("signed-governance-evidence.schema.json")
        statement = signed["$defs"]["statement"]["properties"]
        self.assertFalse(statement["legal_compliance_determined"]["const"])
        self.assertFalse(statement["supervisory_acceptance_determined"]["const"])

        anchor = self._schema("external-anchor-receipt.schema.json")
        anchor_props = anchor["$defs"]["anchor"]["properties"]
        self.assertFalse(anchor_props["external_anchor_validated"]["const"])
        self.assertFalse(anchor_props["trusted_timestamp_validated"]["const"])

        manifest = self._schema("release-evidence-manifest.schema.json")
        manifest_props = manifest["$defs"]["manifest"]["properties"]
        self.assertFalse(manifest_props["formal_release_attested"]["const"])
        self.assertFalse(manifest_props["production_readiness_determined"]["const"])
        self.assertFalse(manifest_props["regulatory_compliance_determined"]["const"])


if __name__ == "__main__":
    unittest.main()
