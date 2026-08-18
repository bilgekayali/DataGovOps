import copy
import json
from pathlib import Path
import tempfile
import unittest

import jsonschema

from datagovops import (
    AccessRetentionPrivacyRegistry,
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    DossierException,
    DossierState,
    GovernanceDossierBuilder,
    GovernanceError,
    GovernancePrincipal,
    LineageCompletenessRequirement,
    LineageEndpointKind,
    LineageEndpointRef,
    LineageRegistry,
    PrincipalType,
    QualityRegistry,
    SemanticGovernanceRegistry,
    dossier_document,
    digest_artifact,
    verify_dossier_document,
)
from datagovops.cli import main as cli_main


ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-08-18T10:00:00Z"


class DossierReleaseTests(unittest.TestCase):
    def _stack(self):
        assets = DataAssetRegistry()
        owner = GovernancePrincipal(
            institution_id="bank-a",
            principal_id="owner-1",
            display_name="Owner One",
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-18T08:00:00Z",
        )
        assets.register_principal(owner)
        system = AuthoritativeSystem(
            institution_id="bank-a",
            system_id="core",
            name="Core Banking",
            owner_id="owner-1",
            system_type="core-banking",
            authoritative=True,
            registered_at="2026-08-18T08:01:00Z",
        )
        assets.register_system(system)
        asset = DataAssetRecord(
            institution_id="bank-a",
            asset_id="balance",
            asset_version=1,
            name="Balance",
            data_domain="customer",
            owner_id="owner-1",
            steward_id="owner-1",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="owner-1",
            classification_rationale="Sensitive financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="owner-1",
            criticality_rationale="Required for customer servicing.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="retention-1",
            quality_owner_id="owner-1",
            registered_at="2026-08-18T08:02:00Z",
        )
        assets.register_asset(asset)
        semantic = SemanticGovernanceRegistry(assets)
        lineage = LineageRegistry(assets, semantic)
        quality = QualityRegistry(assets, semantic)
        controls = AccessRetentionPrivacyRegistry(assets, semantic)
        return assets, semantic, lineage, quality, controls, asset

    def _build(self, *, exceptions=()):
        assets, semantic, lineage, quality, controls, asset = self._stack()
        builder = GovernanceDossierBuilder(assets, semantic, lineage, quality, controls)
        dossier = builder.build(
            "bank-a",
            generated_at=NOW,
            source_revision="release-candidate",
            exceptions=exceptions,
        )
        return dossier, dossier_document(dossier), (assets, semantic, lineage, quality, controls, asset)

    def test_dossier_is_deterministic_schema_valid_and_offline_verifiable(self):
        first, first_document, _ = self._build()
        second, second_document, _ = self._build()
        self.assertEqual(first, second)
        self.assertEqual(first_document, second_document)
        self.assertEqual(first.state, DossierState.WITH_GAPS)
        self.assertEqual(
            first.findings,
            (
                "control:no_governance_control_policy",
                "lineage:no_completeness_requirements",
                "quality:no_rules_configured",
            ),
        )
        schema = json.loads((ROOT / "schemas" / "governance-dossier.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(first_document)
        self.assertEqual(verify_dossier_document(first_document), first_document["dossier_digest"])

    def test_outer_hash_recomputation_cannot_hide_artifact_tampering(self):
        _, document, _ = self._build()
        tampered = copy.deepcopy(document)
        asset_artifact = next(
            item for item in tampered["dossier"]["artifacts"] if item["artifact_type"] == "DataAssetRecord"
        )
        asset_artifact["payload"]["name"] = "Tampered Balance"
        tampered["dossier_digest"] = digest_artifact(tampered["dossier"])
        with self.assertRaises(GovernanceError):
            verify_dossier_document(tampered)

    def test_outer_hash_recomputation_cannot_hide_coverage_or_snapshot_forgery(self):
        _, document, _ = self._build()
        coverage = copy.deepcopy(document)
        coverage["dossier"]["coverage"]["inventory"] += 1
        coverage["dossier_digest"] = digest_artifact(coverage["dossier"])
        with self.assertRaises(GovernanceError):
            verify_dossier_document(coverage)

        snapshot = copy.deepcopy(document)
        inventory = next(item for item in snapshot["dossier"]["domain_snapshots"] if item["domain"] == "inventory")
        inventory["source_snapshot_digest"] = "f" * 64
        snapshot["dossier_digest"] = digest_artifact(snapshot["dossier"])
        with self.assertRaises(GovernanceError):
            verify_dossier_document(snapshot)

    def test_artifact_type_relabeling_is_rejected(self):
        _, document, _ = self._build()
        tampered = copy.deepcopy(document)
        asset_artifact = next(
            item for item in tampered["dossier"]["artifacts"] if item["artifact_type"] == "DataAssetRecord"
        )
        asset_artifact["artifact_type"] = "GovernancePrincipal"
        tampered["dossier_digest"] = digest_artifact(tampered["dossier"])
        with self.assertRaises(GovernanceError):
            verify_dossier_document(tampered)

    def test_active_exception_produces_with_exceptions_without_masking_findings(self):
        assets, semantic, lineage, quality, controls, _ = self._stack()
        exception = DossierException(
            institution_id="bank-a",
            exception_id="exc-1",
            owner_id="owner-1",
            finding_codes=(
                "control:no_governance_control_policy",
                "lineage:no_completeness_requirements",
                "quality:no_rules_configured",
            ),
            rationale="Time-bounded release exception for fixture coverage.",
            approved_at="2026-08-18T09:00:00Z",
            expires_at="2026-08-18T11:00:00Z",
            evidence_digest="a" * 64,
        )
        dossier = GovernanceDossierBuilder(assets, semantic, lineage, quality, controls).build(
            "bank-a",
            generated_at=NOW,
            source_revision="release-candidate",
            exceptions=(exception,),
        )
        self.assertEqual(dossier.state, DossierState.WITH_EXCEPTIONS)
        self.assertEqual(len(dossier.active_exception_digests), 1)
        self.assertEqual(len(dossier.findings), 3)
        verify_dossier_document(dossier_document(dossier))

    def test_stale_lineage_requirement_forces_revalidation_required(self):
        assets, semantic, lineage, quality, controls, asset_v1 = self._stack()
        target = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.ASSET,
            asset_id="balance",
            asset_version=1,
            element_id=None,
            target_digest=asset_v1.artifact_digest,
        )
        lineage.register_requirement(
            LineageCompletenessRequirement(
                institution_id="bank-a",
                requirement_id="req-1",
                target=target,
                owner_id="owner-1",
                rationale="Current upstream lineage required.",
                evidence_digest="b" * 64,
                registered_at="2026-08-18T08:10:00Z",
            )
        )
        assets.register_asset(
            DataAssetRecord(
                institution_id="bank-a",
                asset_id="balance",
                asset_version=2,
                name="Balance v2",
                data_domain="customer",
                owner_id="owner-1",
                steward_id="owner-1",
                system_of_record_id="core",
                classification=DataClassification.RESTRICTED,
                classification_decision_owner_id="owner-1",
                classification_rationale="Sensitive financial data.",
                criticality=DataCriticality.HIGH,
                criticality_decision_owner_id="owner-1",
                criticality_rationale="Required for customer servicing.",
                contains_personal_data=True,
                source_of_truth=True,
                retention_policy_id="retention-1",
                quality_owner_id="owner-1",
                registered_at="2026-08-18T09:00:00Z",
            )
        )
        dossier = GovernanceDossierBuilder(assets, semantic, lineage, quality, controls).build(
            "bank-a", generated_at=NOW, source_revision="release-candidate"
        )
        self.assertEqual(dossier.state, DossierState.REVALIDATION_REQUIRED)
        self.assertIn("lineage:stale:req-1", dossier.revalidation_findings)
        verify_dossier_document(dossier_document(dossier))

    def test_cli_verifies_dossier_and_rejects_tampering(self):
        _, document, _ = self._build()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dossier.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(cli_main(["dossier", "verify", str(path)]), 0)

            tampered = copy.deepcopy(document)
            tampered["dossier"]["coverage"]["inventory"] += 1
            tampered["dossier_digest"] = digest_artifact(tampered["dossier"])
            path.write_text(json.dumps(tampered), encoding="utf-8")
            self.assertEqual(cli_main(["dossier", "verify", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
