from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from datagovops import (
    AccessRetentionPrivacyRegistry,
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    GovernanceDossierBuilder,
    GovernanceError,
    GovernancePrincipal,
    LineageRegistry,
    PrincipalType,
    QualityRegistry,
    SemanticGovernanceRegistry,
    canonical_json,
    dossier_document,
)
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
    descriptor_from_bytes,
    external_anchor_receipt_document,
    governance_evidence_statement,
    provenance_document,
    release_manifest_document,
    signed_governance_evidence_document,
    signing_bytes,
    verify_dependency_sbom,
    verify_external_anchor_receipt_document,
    verify_provenance_document,
    verify_release_manifest_document,
    verify_signed_governance_evidence_document,
)


SOURCE_REVISION = "a" * 40
NOW = "2026-08-25T09:00:00Z"


class EvidenceIntegrityTests(unittest.TestCase):
    def _dossier(self, *, source_revision: str = SOURCE_REVISION):
        assets = DataAssetRegistry()
        owner = GovernancePrincipal(
            institution_id="bank-a",
            principal_id="owner-1",
            display_name="Owner One",
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-25T08:00:00Z",
        )
        assets.register_principal(owner)
        system = AuthoritativeSystem(
            institution_id="bank-a",
            system_id="core",
            name="Core Banking",
            owner_id="owner-1",
            system_type="core-banking",
            authoritative=True,
            registered_at="2026-08-25T08:01:00Z",
        )
        assets.register_system(system)
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            name="Balance",
            data_domain="risk",
            owner_id="owner-1",
            steward_id="owner-1",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="owner-1",
            classification_rationale="Sensitive governed risk data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="owner-1",
            criticality_rationale="Required for risk reporting.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="retention-1",
            quality_owner_id="owner-1",
            registered_at="2026-08-25T08:02:00Z",
        )
        assets.register_asset(asset)
        semantic = SemanticGovernanceRegistry(assets)
        lineage = LineageRegistry(assets, semantic)
        quality = QualityRegistry(assets, semantic)
        controls = AccessRetentionPrivacyRegistry(assets, semantic)
        dossier = GovernanceDossierBuilder(assets, semantic, lineage, quality, controls).build(
            "bank-a",
            generated_at=NOW,
            source_revision=source_revision,
        )
        return dossier_document(dossier)

    def _signed(self):
        dossier = self._dossier()
        key_reference = SigningKeyReference(
            provider="institution-kms",
            key_id="governance-signing-key",
            key_version="2026-08-25",
        )
        statement = governance_evidence_statement(
            dossier,
            signer_id="chief-data-officer",
            key_reference=key_reference,
            signed_at=1787649300,
        )
        private_key = Ed25519PrivateKey.generate()
        signature = private_key.sign(signing_bytes(statement))
        document = signed_governance_evidence_document(statement, signature)
        return dossier, statement, document, private_key

    def test_external_ed25519_signature_round_trip_and_tamper_failure(self):
        dossier, statement, document, private_key = self._signed()
        self.assertEqual(
            verify_signed_governance_evidence_document(document, private_key.public_key(), dossier),
            statement.statement_digest,
        )

        tampered = copy.deepcopy(document)
        tampered["statement"]["signer_id"] = "different-signer"
        tampered["statement_digest"] = __import__("datagovops").digest_artifact(tampered["statement"])
        with self.assertRaises(GovernanceError):
            verify_signed_governance_evidence_document(tampered, private_key.public_key(), dossier)

        with self.assertRaises(GovernanceError):
            verify_signed_governance_evidence_document(
                document,
                Ed25519PrivateKey.generate().public_key(),
                dossier,
            )

    def test_signature_is_bound_to_exact_verified_dossier(self):
        dossier, _, document, private_key = self._signed()
        other_dossier = self._dossier(source_revision="b" * 40)
        self.assertNotEqual(dossier["dossier_digest"], other_dossier["dossier_digest"])
        with self.assertRaises(GovernanceError):
            verify_signed_governance_evidence_document(
                document,
                private_key.public_key(),
                other_dossier,
            )

    def test_signed_statement_cannot_claim_compliance_or_supervisory_acceptance(self):
        dossier = self._dossier()
        key_reference = SigningKeyReference("institution-kms", "key", "v1")
        with self.assertRaises(GovernanceError):
            GovernanceEvidenceStatement(
                schema_version=SIGNED_EVIDENCE_SCHEMA_VERSION,
                institution_id="bank-a",
                dossier_digest=dossier["dossier_digest"],
                release_version=dossier["dossier"]["release_version"],
                source_revision=SOURCE_REVISION,
                signer_id="owner",
                key_reference=key_reference,
                signed_at=1,
                legal_compliance_determined=True,
            )

    def test_anchor_receipt_is_digest_bound_but_does_not_claim_external_trust(self):
        _, statement, _, _ = self._signed()
        receipt = ExternalAnchorReceipt(
            schema_version=ANCHOR_SCHEMA_VERSION,
            institution_id="bank-a",
            evidence_digest=statement.statement_digest,
            provider="external-immutable-ledger",
            anchor_id="anchor-123",
            anchored_at=1787649400,
            timestamp_token_sha256="f" * 64,
        )
        document = external_anchor_receipt_document(receipt)
        self.assertEqual(
            verify_external_anchor_receipt_document(
                document,
                expected_evidence_digest=statement.statement_digest,
            ),
            receipt.receipt_digest,
        )
        with self.assertRaises(GovernanceError):
            verify_external_anchor_receipt_document(document, expected_evidence_digest="0" * 64)
        with self.assertRaises(GovernanceError):
            ExternalAnchorReceipt(
                schema_version=ANCHOR_SCHEMA_VERSION,
                institution_id="bank-a",
                evidence_digest=statement.statement_digest,
                provider="external-immutable-ledger",
                anchor_id="anchor-123",
                anchored_at=1787649400,
                timestamp_token_sha256="f" * 64,
                trusted_timestamp_validated=True,
            )

    def test_provenance_sbom_and_release_manifest_cross_bind_exact_bytes(self):
        dossier, statement, signed_document, _ = self._signed()
        anchor = ExternalAnchorReceipt(
            schema_version=ANCHOR_SCHEMA_VERSION,
            institution_id="bank-a",
            evidence_digest=statement.statement_digest,
            provider="external-immutable-ledger",
            anchor_id="anchor-123",
            anchored_at=1787649400,
            timestamp_token_sha256="f" * 64,
        )
        signed_bytes = canonical_json(signed_document).encode("utf-8")
        anchor_bytes = canonical_json(external_anchor_receipt_document(anchor)).encode("utf-8")
        wheel_bytes = b"deterministic-wheel-fixture"
        wheel = descriptor_from_bytes(
            "dist/datagovops-0.4.0-py3-none-any.whl",
            wheel_bytes,
            "application/zip",
        )
        provenance = BuildProvenance(
            schema_version=PROVENANCE_SCHEMA_VERSION,
            package_name="datagovops",
            package_version="0.4.0",
            source_revision=SOURCE_REVISION,
            builder_id="github-actions/reference",
            build_type="python-wheel",
            invocation_id="fixture-1",
            started_at=1787649000,
            finished_at=1787649100,
            subjects=(wheel,),
            materials=(SourceMaterial("https://github.com/bilgekayali/DataGovOps", SOURCE_REVISION),),
        )
        provenance_doc = provenance_document(provenance)
        self.assertEqual(verify_provenance_document(provenance_doc), provenance.provenance_digest)
        provenance_bytes = canonical_json(provenance_doc).encode("utf-8")

        sbom = build_dependency_sbom(
            "datagovops",
            "0.4.0",
            (("jsonschema", "4.25.1"), ("cryptography", "46.0.0")),
        )
        verify_dependency_sbom(
            sbom,
            expected_package_name="datagovops",
            expected_package_version="0.4.0",
        )
        sbom_bytes = canonical_json(sbom).encode("utf-8")

        artifact_contents = {
            "evidence/anchor.json": anchor_bytes,
            "evidence/governance-signed.json": signed_bytes,
            "evidence/provenance.json": provenance_bytes,
            "evidence/sbom.json": sbom_bytes,
            "dist/datagovops-0.4.0-py3-none-any.whl": wheel_bytes,
        }
        descriptors = tuple(
            descriptor_from_bytes(
                path,
                content,
                "application/json" if path.endswith(".json") else "application/zip",
            )
            for path, content in sorted(artifact_contents.items())
        )
        manifest = ReleaseEvidenceManifest(
            schema_version=RELEASE_MANIFEST_SCHEMA_VERSION,
            package_name="datagovops",
            package_version="0.4.0",
            source_revision=SOURCE_REVISION,
            artifacts=descriptors,
            provenance_path="evidence/provenance.json",
            sbom_path="evidence/sbom.json",
            signed_governance_evidence_path="evidence/governance-signed.json",
            anchor_receipt_path="evidence/anchor.json",
        )
        manifest_doc = release_manifest_document(manifest)
        self.assertEqual(
            verify_release_manifest_document(manifest_doc, artifact_contents),
            manifest.manifest_digest,
        )

        tampered = dict(artifact_contents)
        tampered["dist/datagovops-0.4.0-py3-none-any.whl"] += b"tampered"
        with self.assertRaises(GovernanceError):
            verify_release_manifest_document(manifest_doc, tampered)

    def test_release_contract_rejects_path_traversal_and_production_claims(self):
        with self.assertRaises(GovernanceError):
            ArtifactDescriptor("../escape", "a" * 64, 1, "application/octet-stream")
        wheel = ArtifactDescriptor("dist/x.whl", "a" * 64, 1, "application/zip")
        evidence = ArtifactDescriptor("evidence/a.json", "b" * 64, 1, "application/json")
        provenance = ArtifactDescriptor("evidence/p.json", "c" * 64, 1, "application/json")
        sbom = ArtifactDescriptor("evidence/s.json", "d" * 64, 1, "application/json")
        with self.assertRaises(GovernanceError):
            ReleaseEvidenceManifest(
                schema_version=RELEASE_MANIFEST_SCHEMA_VERSION,
                package_name="datagovops",
                package_version="0.4.0",
                source_revision=SOURCE_REVISION,
                artifacts=tuple(sorted((wheel, evidence, provenance, sbom), key=lambda x: x.path)),
                provenance_path="evidence/p.json",
                sbom_path="evidence/s.json",
                signed_governance_evidence_path="evidence/a.json",
                anchor_receipt_path="dist/x.whl",
                production_readiness_determined=True,
            )

    def test_runtime_source_contains_no_private_signing_key_api(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "datagovops" / "evidence_integrity.py").read_text(encoding="utf-8")
        self.assertNotIn("Ed25519PrivateKey", source)
        self.assertNotIn("BEGIN PRIVATE KEY", source)


if __name__ == "__main__":
    unittest.main()
