import unittest

from datagovops import (
    AuthoritativeSystem,
    DataAssetRecord,
    DataAssetRegistry,
    DataClassification,
    DataCriticality,
    DataElementRecord,
    GovernanceError,
    GovernancePrincipal,
    LineageCompletenessRequirement,
    LineageEdge,
    LineageEndpointKind,
    LineageEndpointRef,
    LineageRegistry,
    LineageRelationship,
    PrincipalType,
    SemanticGovernanceRegistry,
    TransformationRecord,
    digest_artifact,
)


class LineageGovernanceTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def principal(self, principal_id, institution="bank-a"):
        return GovernancePrincipal(
            institution_id=institution,
            principal_id=principal_id,
            display_name=principal_id,
            principal_type=PrincipalType.HUMAN,
            registered_at="2026-08-18T08:00:00Z",
        )

    def asset(self, asset_id, version, system_id, *, name=None):
        return DataAssetRecord(
            institution_id="bank-a",
            asset_id=asset_id,
            asset_version=version,
            name=name or asset_id,
            data_domain="risk-data",
            owner_id="owner",
            steward_id="steward",
            system_of_record_id=system_id,
            classification=DataClassification.RESTRICTED,
            classification_decision_owner_id="class-owner",
            classification_rationale="Governed financial data.",
            criticality=DataCriticality.HIGH,
            criticality_decision_owner_id="crit-owner",
            criticality_rationale="Required for controlled reporting.",
            contains_personal_data=False,
            source_of_truth=True,
            retention_policy_id="ret-7",
            quality_owner_id="quality-owner",
            registered_at=f"2026-08-18T08:{version:02d}:00Z",
        )

    def state(self):
        base = DataAssetRegistry()
        for principal_id in (
            "owner",
            "steward",
            "class-owner",
            "crit-owner",
            "quality-owner",
            "system-owner",
            "element-owner",
            "transform-owner",
            "lineage-owner",
        ):
            base.register_principal(self.principal(principal_id))
        for system_id in ("core", "warehouse", "etl"):
            base.register_system(
                AuthoritativeSystem(
                    institution_id="bank-a",
                    system_id=system_id,
                    name=system_id,
                    owner_id="system-owner",
                    system_type="data-platform",
                    authoritative=True,
                    registered_at="2026-08-18T08:01:00Z",
                )
            )
        source_asset = self.asset("customer-balance", 1, "core")
        target_asset = self.asset("risk-balance-report", 1, "warehouse")
        base.register_asset(source_asset)
        base.register_asset(target_asset)

        semantic = SemanticGovernanceRegistry(base)
        source_element = DataElementRecord(
            institution_id="bank-a",
            asset_id="customer-balance",
            asset_version=1,
            element_id="available-balance",
            name="Available Balance",
            data_type="decimal(18,2)",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T08:05:00Z",
        )
        target_element = DataElementRecord(
            institution_id="bank-a",
            asset_id="risk-balance-report",
            asset_version=1,
            element_id="reported-balance",
            name="Reported Balance",
            data_type="decimal(18,2)",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T08:06:00Z",
        )
        semantic.register_element(source_element)
        semantic.register_element(target_element)
        lineage = LineageRegistry(base, semantic)
        return base, semantic, lineage, source_asset, target_asset, source_element, target_element

    def transformation(self, version=1, *, code_label="code-v1"):
        return TransformationRecord(
            institution_id="bank-a",
            transformation_id="balance-to-risk-report",
            transformation_version=version,
            name="Balance to risk report",
            owner_id="transform-owner",
            execution_system_id="etl",
            code_digest=self.evidence(code_label),
            config_digest=self.evidence(f"config-v{version}"),
            evidence_digest=self.evidence(f"transform-evidence-v{version}"),
            registered_at=f"2026-08-18T08:1{version}:00Z",
        )

    def endpoints(self, source_element, target_element):
        source = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.DATA_ELEMENT,
            asset_id=source_element.asset_id,
            asset_version=source_element.asset_version,
            element_id=source_element.element_id,
            target_digest=source_element.artifact_digest,
        )
        target = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.DATA_ELEMENT,
            asset_id=target_element.asset_id,
            asset_version=target_element.asset_version,
            element_id=target_element.element_id,
            target_digest=target_element.artifact_digest,
        )
        return source, target

    def edge(self, transformation, source, target, *, edge_id="balance-lineage"):
        return LineageEdge(
            institution_id="bank-a",
            edge_id=edge_id,
            source=source,
            target=target,
            relationship=LineageRelationship.TRANSFORMED_FROM,
            transformation_id=transformation.transformation_id,
            transformation_version=transformation.transformation_version,
            transformation_digest=transformation.artifact_digest,
            producer_system_id="core",
            consumer_system_id="warehouse",
            evidence_digest=self.evidence(edge_id),
            recorded_at="2026-08-18T08:20:00Z",
        )

    def requirement(self, target):
        return LineageCompletenessRequirement(
            institution_id="bank-a",
            requirement_id="risk-report-balance-upstream",
            target=target,
            owner_id="lineage-owner",
            rationale="Risk reporting element requires explicit upstream lineage.",
            evidence_digest=self.evidence("lineage-requirement"),
            registered_at="2026-08-18T08:21:00Z",
        )

    def test_element_lineage_and_completeness_are_current_and_deterministic(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        transformation = self.transformation()
        lineage.register_transformation(transformation)
        source, target = self.endpoints(source_element, target_element)
        edge = self.edge(transformation, source, target)
        lineage.register_edge(edge)
        requirement = self.requirement(target)
        lineage.register_requirement(requirement)

        lineage.assert_edge_current(edge)
        report = lineage.evaluate_completeness(
            "bank-a", evaluated_at="2026-08-18T08:22:00Z"
        )
        self.assertTrue(report.complete)
        self.assertFalse(report.regulatory_compliance_determined)
        self.assertEqual(report.missing_requirement_ids, ())
        self.assertEqual(report.stale_requirement_ids, ())
        lineage.assert_report_current(report)
        self.assertEqual(lineage.snapshot_digest("bank-a"), lineage.snapshot_digest("bank-a"))

    def test_explicit_requirement_reports_missing_lineage(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        _, target = self.endpoints(source_element, target_element)
        lineage.register_requirement(self.requirement(target))
        report = lineage.evaluate_completeness(
            "bank-a", evaluated_at="2026-08-18T08:22:00Z"
        )
        self.assertFalse(report.complete)
        self.assertEqual(report.missing_requirement_ids, ("risk-report-balance-upstream",))

    def test_completeness_without_explicit_requirements_fails_closed(self):
        _, _, lineage, _, _, _, _ = self.state()
        with self.assertRaises(GovernanceError):
            lineage.evaluate_completeness(
                "bank-a", evaluated_at="2026-08-18T08:22:00Z"
            )

    def test_cycle_is_rejected(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        transformation = self.transformation()
        lineage.register_transformation(transformation)
        source, target = self.endpoints(source_element, target_element)
        lineage.register_edge(self.edge(transformation, source, target, edge_id="forward"))
        with self.assertRaises(GovernanceError):
            lineage.register_edge(self.edge(transformation, target, source, edge_id="reverse"))

    def test_dangling_digest_and_cross_institution_fail_closed(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        source, target = self.endpoints(source_element, target_element)
        bad_source = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.DATA_ELEMENT,
            asset_id=source.asset_id,
            asset_version=source.asset_version,
            element_id=source.element_id,
            target_digest=self.evidence("wrong-target"),
        )
        with self.assertRaises(GovernanceError):
            lineage.resolve_endpoint(bad_source)
        foreign = LineageEndpointRef(
            institution_id="bank-b",
            kind=LineageEndpointKind.ASSET,
            asset_id="foreign",
            asset_version=1,
            element_id=None,
            target_digest=self.evidence("foreign"),
        )
        transformation = self.transformation()
        with self.assertRaises(GovernanceError):
            LineageEdge(
                institution_id="bank-a",
                edge_id="cross-scope",
                source=foreign,
                target=target,
                relationship=LineageRelationship.DERIVED_FROM,
                transformation_id=transformation.transformation_id,
                transformation_version=1,
                transformation_digest=transformation.artifact_digest,
                producer_system_id="core",
                consumer_system_id="warehouse",
                evidence_digest=self.evidence("edge"),
                recorded_at="2026-08-18T08:20:00Z",
            )

    def test_new_asset_version_stales_edge_and_requirement(self):
        base, _, lineage, _, _, source_element, target_element = self.state()
        transformation = self.transformation()
        lineage.register_transformation(transformation)
        source, target = self.endpoints(source_element, target_element)
        edge = self.edge(transformation, source, target)
        lineage.register_edge(edge)
        lineage.register_requirement(self.requirement(target))
        base.register_asset(self.asset("risk-balance-report", 2, "warehouse", name="Risk report v2"))

        with self.assertRaises(GovernanceError):
            lineage.assert_edge_current(edge)
        report = lineage.evaluate_completeness(
            "bank-a", evaluated_at="2026-08-18T08:30:00Z"
        )
        self.assertFalse(report.complete)
        self.assertEqual(report.stale_requirement_ids, ("risk-report-balance-upstream",))

    def test_new_transformation_version_stales_edge(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        first = self.transformation(1)
        lineage.register_transformation(first)
        source, target = self.endpoints(source_element, target_element)
        edge = self.edge(first, source, target)
        lineage.register_edge(edge)
        lineage.register_transformation(self.transformation(2, code_label="code-v2"))
        with self.assertRaises(GovernanceError):
            lineage.assert_edge_current(edge)

    def test_unknown_system_and_transformation_fail_closed(self):
        _, _, lineage, _, _, source_element, target_element = self.state()
        source, target = self.endpoints(source_element, target_element)
        transformation = self.transformation()
        lineage.register_transformation(transformation)
        bad_edge = LineageEdge(
            institution_id="bank-a",
            edge_id="bad-system",
            source=source,
            target=target,
            relationship=LineageRelationship.DERIVED_FROM,
            transformation_id=transformation.transformation_id,
            transformation_version=1,
            transformation_digest=transformation.artifact_digest,
            producer_system_id="missing-system",
            consumer_system_id="warehouse",
            evidence_digest=self.evidence("bad-system"),
            recorded_at="2026-08-18T08:20:00Z",
        )
        with self.assertRaises(GovernanceError):
            lineage.register_edge(bad_edge)

    def test_governed_types_fail_closed(self):
        with self.assertRaises(GovernanceError):
            LineageEndpointRef(
                institution_id="bank-a",
                kind="asset",
                asset_id="a",
                asset_version=1,
                element_id=None,
                target_digest=self.evidence("a"),
            )
        with self.assertRaises(GovernanceError):
            TransformationRecord(
                institution_id="bank-a",
                transformation_id="t",
                transformation_version=True,
                name="T",
                owner_id="owner",
                execution_system_id="etl",
                code_digest=self.evidence("code"),
                config_digest=self.evidence("config"),
                evidence_digest=self.evidence("evidence"),
                registered_at="2026-08-18T08:10:00Z",
            )


if __name__ == "__main__":
    unittest.main()
