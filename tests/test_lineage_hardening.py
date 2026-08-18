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


class LineageHardeningTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

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
        ):
            base.register_principal(
                GovernancePrincipal(
                    institution_id="bank-a",
                    principal_id=principal_id,
                    display_name=principal_id,
                    principal_type=PrincipalType.HUMAN,
                    registered_at="2026-08-18T08:00:00Z",
                )
            )
        for system_id in ("source-system", "target-system", "etl"):
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
        def asset(asset_id, system_id):
            return DataAssetRecord(
                institution_id="bank-a",
                asset_id=asset_id,
                asset_version=1,
                name=asset_id,
                data_domain="risk-data",
                owner_id="owner",
                steward_id="steward",
                system_of_record_id=system_id,
                classification=DataClassification.RESTRICTED,
                classification_decision_owner_id="class-owner",
                classification_rationale="Governed financial data.",
                criticality=DataCriticality.HIGH,
                criticality_decision_owner_id="crit-owner",
                criticality_rationale="Required for reporting.",
                contains_personal_data=False,
                source_of_truth=True,
                retention_policy_id="ret-7",
                quality_owner_id="quality-owner",
                registered_at="2026-08-18T08:02:00Z",
            )
        source_asset = asset("source-asset", "source-system")
        target_asset = asset("target-asset", "target-system")
        base.register_asset(source_asset)
        base.register_asset(target_asset)
        semantic = SemanticGovernanceRegistry(base)
        element = DataElementRecord(
            institution_id="bank-a",
            asset_id="target-asset",
            asset_version=1,
            element_id="target-element",
            name="Target Element",
            data_type="decimal",
            owner_id="element-owner",
            nullable=False,
            registered_at="2026-08-18T08:03:00Z",
        )
        semantic.register_element(element)
        lineage = LineageRegistry(base, semantic)
        transformation = TransformationRecord(
            institution_id="bank-a",
            transformation_id="mixed-transform",
            transformation_version=1,
            name="Mixed transform",
            owner_id="transform-owner",
            execution_system_id="etl",
            code_digest=self.evidence("code"),
            config_digest=self.evidence("config"),
            evidence_digest=self.evidence("transform"),
            registered_at="2026-08-18T08:04:00Z",
        )
        return base, lineage, source_asset, target_asset, element, transformation

    def test_mixed_asset_to_element_lineage_is_supported(self):
        _, lineage, source_asset, _, element, transformation = self.state()
        lineage.register_transformation(transformation)
        source = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.ASSET,
            asset_id=source_asset.asset_id,
            asset_version=1,
            element_id=None,
            target_digest=source_asset.artifact_digest,
        )
        target = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.DATA_ELEMENT,
            asset_id=element.asset_id,
            asset_version=1,
            element_id=element.element_id,
            target_digest=element.artifact_digest,
        )
        edge = LineageEdge(
            institution_id="bank-a",
            edge_id="mixed-edge",
            source=source,
            target=target,
            relationship=LineageRelationship.DERIVED_FROM,
            transformation_id=transformation.transformation_id,
            transformation_version=1,
            transformation_digest=transformation.artifact_digest,
            producer_system_id="source-system",
            consumer_system_id="target-system",
            evidence_digest=self.evidence("edge"),
            recorded_at="2026-08-18T08:05:00Z",
        )
        lineage.register_edge(edge)
        lineage.assert_edge_current(edge)

    def test_unregistered_transformation_reference_fails_closed(self):
        _, lineage, source_asset, target_asset, _, transformation = self.state()
        source = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.ASSET,
            asset_id=source_asset.asset_id,
            asset_version=1,
            element_id=None,
            target_digest=source_asset.artifact_digest,
        )
        target = LineageEndpointRef(
            institution_id="bank-a",
            kind=LineageEndpointKind.ASSET,
            asset_id=target_asset.asset_id,
            asset_version=1,
            element_id=None,
            target_digest=target_asset.artifact_digest,
        )
        edge = LineageEdge(
            institution_id="bank-a",
            edge_id="unregistered-transform-edge",
            source=source,
            target=target,
            relationship=LineageRelationship.TRANSFORMED_FROM,
            transformation_id=transformation.transformation_id,
            transformation_version=1,
            transformation_digest=transformation.artifact_digest,
            producer_system_id="source-system",
            consumer_system_id="target-system",
            evidence_digest=self.evidence("edge"),
            recorded_at="2026-08-18T08:05:00Z",
        )
        with self.assertRaises(GovernanceError):
            lineage.register_edge(edge)


if __name__ == "__main__":
    unittest.main()
