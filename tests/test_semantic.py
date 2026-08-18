import unittest

from datagovops import (
    AssetPurposeBinding,
    AuthoritativeSystem,
    BusinessPurpose,
    ClassificationDecision,
    ClassificationScope,
    CriticalDataElementDesignation,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    DataElementRecord,
    GovernanceError,
    GovernancePrincipal,
    PrincipalType,
    SemanticGovernanceRegistry,
    digest_artifact,
)


class SemanticGovernanceTests(unittest.TestCase):
    def base_registry(self):
        registry = DataAssetRegistry()
        for principal_id in (
            "owner",
            "steward",
            "class-owner",
            "crit-owner",
            "system-owner",
            "element-owner",
            "cde-owner",
            "purpose-owner",
            "approver",
        ):
            registry.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-18T07:00:00Z",
                )
            )
        registry.register_system(
            AuthoritativeSystem(
                institution_id="bank-a",
                system_id="core",
                name="Core",
                owner_id="system-owner",
                system_type="core",
                authoritative=True,
                registered_at="2026-08-18T07:01:00Z",
            )
        )
        registry.register_asset(self.asset(1))
        return registry

    def asset(self, version, name="Customer Balance"):
        return DataAssetRecord(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=version,
            name=name,
            data_domain="customer",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id="core",
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="class-owner",
            classification_rationale="Sensitive financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="crit-owner",
            criticality_rationale="Required for servicing.",
            contains_personal_data=True,
            source_of_truth=True,
            retention_policy_id="ret-7",
            quality_owner_id=None,
            registered_at=f"2026-08-18T07:0{version + 1}:00Z",
        )

    def element(self):
        return DataElementRecord(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            element_id="available-balance",
            name="Available Balance",
            data_type="decimal(18,2)",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T07:03:00Z",
        )

    def purpose(self, version=1, description="Serve customer balance enquiries."):
        return BusinessPurpose(
            institution_id="bank-a",
            purpose_id="customer-servicing",
            purpose_version=version,
            name="Customer servicing",
            description=description,
            owner_id="purpose-owner",
            registered_at=f"2026-08-18T07:1{version}:00Z",
        )

    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def full_semantic_state(self):
        base = self.base_registry()
        semantic = SemanticGovernanceRegistry(base)
        element = self.element()
        semantic.register_element(element)
        asset = base.asset("bank-a", "customer-balance", 1)
        asset_decision = ClassificationDecision(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            scope=ClassificationScope.ASSET,
            element_id=None,
            target_digest=asset.artifact_digest,
            classification=DataClassification.RESTRICTED,
            decision_owner_id="class-owner",
            rationale="Asset classification confirmed.",
            evidence_digest=self.evidence("asset-classification"),
            decided_at="2026-08-18T07:04:00Z",
        )
        element_decision = ClassificationDecision(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            scope=ClassificationScope.DATA_ELEMENT,
            element_id="available-balance",
            target_digest=element.artifact_digest,
            classification=DataClassification.CONFIDENTIAL,
            decision_owner_id="class-owner",
            rationale="Element contains customer financial state.",
            evidence_digest=self.evidence("element-classification"),
            decided_at="2026-08-18T07:05:00Z",
        )
        semantic.register_classification(asset_decision)
        semantic.register_classification(element_decision)
        cde = CriticalDataElementDesignation(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            element_id="available-balance",
            element_digest=element.artifact_digest,
            cde_owner_id="cde-owner",
            decision_owner_id="crit-owner",
            rationale="Balance is material to customer and risk reporting processes.",
            evidence_digest=self.evidence("cde-designation"),
            designated_at="2026-08-18T07:06:00Z",
        )
        semantic.register_cde(cde)
        purpose = self.purpose()
        semantic.register_purpose(purpose)
        binding = AssetPurposeBinding(
            institution_id="bank-a",
            binding_id="customer-balance:customer-servicing",
            asset_id="customer-balance",
            asset_version=1,
            asset_digest=asset.artifact_digest,
            purpose_id=purpose.purpose_id,
            purpose_version=purpose.purpose_version,
            purpose_digest=purpose.artifact_digest,
            approval_owner_id="approver",
            rationale="Approved operational use of governed asset.",
            evidence_digest=self.evidence("purpose-approval"),
            bound_at="2026-08-18T07:12:00Z",
        )
        semantic.register_purpose_binding(binding)
        return base, semantic, asset_decision, element_decision, cde, binding

    def test_full_state_is_current_and_deterministic(self):
        _, semantic, asset_decision, element_decision, cde, binding = self.full_semantic_state()
        semantic.assert_classification_current(asset_decision)
        semantic.assert_classification_current(element_decision)
        semantic.assert_cde_current(cde)
        semantic.assert_purpose_binding_current(binding)
        self.assertEqual(semantic.snapshot_digest("bank-a"), semantic.snapshot_digest("bank-a"))

    def test_asset_classification_cannot_conflict_with_registered_asset(self):
        base = self.base_registry()
        semantic = SemanticGovernanceRegistry(base)
        asset = base.asset("bank-a", "customer-balance", 1)
        with self.assertRaises(GovernanceError):
            semantic.register_classification(
                ClassificationDecision(
                    institution_id="bank-a",
                    asset_id="customer-balance",
                    asset_version=1,
                    scope=ClassificationScope.ASSET,
                    element_id=None,
                    target_digest=asset.artifact_digest,
                    classification=DataClassification.PUBLIC,
                    decision_owner_id="class-owner",
                    rationale="Invalid downgrade.",
                    evidence_digest=self.evidence("bad"),
                    decided_at="2026-08-18T07:04:00Z",
                )
            )

    def test_dangling_and_digest_mismatch_fail_closed(self):
        base = self.base_registry()
        semantic = SemanticGovernanceRegistry(base)
        with self.assertRaises(GovernanceError):
            semantic.register_element(
                DataElementRecord(
                    institution_id="bank-a",
                    asset_id="customer-balance",
                    asset_version=1,
                    element_id="x",
                    name="X",
                    data_type="text",
                    owner_id="missing",
                    nullable=True,
                    registered_at="2026-08-18T07:03:00Z",
                )
            )
        element = self.element()
        semantic.register_element(element)
        with self.assertRaises(GovernanceError):
            semantic.register_cde(
                CriticalDataElementDesignation(
                    institution_id="bank-a",
                    asset_id="customer-balance",
                    asset_version=1,
                    element_id=element.element_id,
                    element_digest=self.evidence("wrong-element"),
                    cde_owner_id="cde-owner",
                    decision_owner_id="crit-owner",
                    rationale="Mismatch.",
                    evidence_digest=self.evidence("cde"),
                    designated_at="2026-08-18T07:06:00Z",
                )
            )

    def test_governed_types_fail_closed(self):
        with self.assertRaises(GovernanceError):
            DataElementRecord(
                institution_id="bank-a",
                asset_id="a",
                asset_version=1,
                element_id="e",
                name="E",
                data_type="text",
                owner_id="owner",
                nullable=1,
                registered_at="2026-08-18T07:03:00Z",
            )
        with self.assertRaises(GovernanceError):
            ClassificationDecision(
                institution_id="bank-a",
                asset_id="a",
                asset_version=1,
                scope="asset",
                element_id=None,
                target_digest=self.evidence("target"),
                classification=DataClassification.INTERNAL,
                decision_owner_id="owner",
                rationale="R",
                evidence_digest=self.evidence("evidence"),
                decided_at="2026-08-18T07:04:00Z",
            )
        with self.assertRaises(GovernanceError):
            self.purpose(version=True)

    def test_new_asset_version_stales_semantic_decisions(self):
        base, semantic, asset_decision, element_decision, cde, binding = self.full_semantic_state()
        base.register_asset(self.asset(2, "Customer Balance v2"))
        for artifact, checker in (
            (asset_decision, semantic.assert_classification_current),
            (element_decision, semantic.assert_classification_current),
            (cde, semantic.assert_cde_current),
            (binding, semantic.assert_purpose_binding_current),
        ):
            with self.assertRaises(GovernanceError):
                checker(artifact)

    def test_new_purpose_version_stales_binding(self):
        _, semantic, _, _, _, binding = self.full_semantic_state()
        semantic.register_purpose(self.purpose(2, "Updated servicing purpose."))
        with self.assertRaises(GovernanceError):
            semantic.assert_purpose_binding_current(binding)

    def test_duplicate_target_with_conflicting_decision_fails(self):
        base = self.base_registry()
        semantic = SemanticGovernanceRegistry(base)
        asset = base.asset("bank-a", "customer-balance", 1)
        first = ClassificationDecision(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            scope=ClassificationScope.ASSET,
            element_id=None,
            target_digest=asset.artifact_digest,
            classification=DataClassification.RESTRICTED,
            decision_owner_id="class-owner",
            rationale="First.",
            evidence_digest=self.evidence("first"),
            decided_at="2026-08-18T07:04:00Z",
        )
        semantic.register_classification(first)
        with self.assertRaises(GovernanceError):
            semantic.register_classification(
                ClassificationDecision(
                    institution_id="bank-a",
                    asset_id="customer-balance",
                    asset_version=1,
                    scope=ClassificationScope.ASSET,
                    element_id=None,
                    target_digest=asset.artifact_digest,
                    classification=DataClassification.RESTRICTED,
                    decision_owner_id="class-owner",
                    rationale="Conflicting replacement.",
                    evidence_digest=self.evidence("second"),
                    decided_at="2026-08-18T07:05:00Z",
                )
            )


if __name__ == "__main__":
    unittest.main()
