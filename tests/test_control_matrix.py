import hashlib
import unittest

from datagovops.control_matrix import (
    ControlAssessmentState,
    ControlDefinition,
    ControlDomain,
    ControlEvidenceReference,
    ControlEvidenceRegistry,
    EvidenceRequirement,
    EvidenceSourceBoundary,
    FrameworkReference,
    MatrixState,
)
from datagovops.models import GovernanceError


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def control(
    control_id: str,
    *,
    version: int = 1,
    domain: ControlDomain = ControlDomain.BCBS239_ASSURANCE,
    evidence_type: str = "aggregation_assessment",
    source: EvidenceSourceBoundary = EvidenceSourceBoundary.BCBS239,
) -> ControlDefinition:
    return ControlDefinition(
        institution_id="bank-a",
        control_id=control_id,
        control_version=version,
        title=f"Control {control_id}",
        domain=domain,
        owner_id="owner-1",
        objective=f"Represent current evidence for {control_id}",
        evidence_requirements=(EvidenceRequirement(evidence_type, (source,)),),
        framework_references=(
            FrameworkReference(
                framework="BCBS 239" if domain is ControlDomain.BCBS239_ASSURANCE else "institution policy",
                reference=f"REF-{control_id}",
                mapping_rationale="Design mapping only; applicability remains institution-owned.",
            ),
        ),
        registered_at=100,
    )


def evidence(
    item_id: str,
    definition: ControlDefinition,
    *,
    evidence_type: str = "aggregation_assessment",
    source: EvidenceSourceBoundary = EvidenceSourceBoundary.BCBS239,
    observed_at: int = 120,
    revalidate_after: int = 220,
    institution_id: str = "bank-a",
) -> ControlEvidenceReference:
    return ControlEvidenceReference(
        institution_id=institution_id,
        evidence_id=item_id,
        control_digest=definition.artifact_digest,
        evidence_type=evidence_type,
        source_boundary=source,
        artifact_type="datagovops.assessment",
        source_artifact_digest=digest(f"artifact:{item_id}"),
        source_snapshot_digest=digest(f"snapshot:{item_id}"),
        observed_at=observed_at,
        revalidate_after=revalidate_after,
        verifier_id="validator-1",
        verification_evidence_digest=digest(f"verify:{item_id}"),
    )


class ControlEvidenceMatrixTests(unittest.TestCase):
    def test_represented_matrix_has_no_compliance_score(self):
        registry = ControlEvidenceRegistry()
        bcbs = control("bcbs-aggregation")
        deployment = control(
            "deployment-runtime",
            domain=ControlDomain.DEPLOYMENT_RUNTIME,
            evidence_type="deployment_assessment",
            source=EvidenceSourceBoundary.DEPLOYMENT,
        )
        registry.register_control(bcbs)
        registry.register_control(deployment)
        registry.register_evidence(evidence("ev-bcbs", bcbs))
        registry.register_evidence(
            evidence(
                "ev-deploy",
                deployment,
                evidence_type="deployment_assessment",
                source=EvidenceSourceBoundary.DEPLOYMENT,
            )
        )

        matrix = registry.build_matrix(
            institution_id="bank-a",
            matrix_id="enterprise-controls",
            matrix_version=1,
            control_ids=("deployment-runtime", "bcbs-aggregation"),
            assessed_at=180,
        )

        self.assertEqual(matrix.state, MatrixState.REPRESENTED)
        self.assertEqual(matrix.represented_control_count, 2)
        self.assertEqual(matrix.gap_control_count, 0)
        self.assertEqual(matrix.revalidation_required_control_count, 0)
        self.assertFalse(matrix.automated_compliance_scoring_enabled)
        self.assertFalse(matrix.regulatory_compliance_determined)
        self.assertFalse(matrix.supervisory_acceptance_determined)
        self.assertFalse(hasattr(matrix, "compliance_score"))

    def test_missing_evidence_is_gap(self):
        registry = ControlEvidenceRegistry()
        definition = control("privacy-obligation", domain=ControlDomain.PRIVACY_SECURITY, evidence_type="obligation_control_report", source=EvidenceSourceBoundary.ACCESS_RETENTION_PRIVACY)
        registry.register_control(definition)

        assessment = registry.assess_control("bank-a", "privacy-obligation", assessed_at=150)
        self.assertEqual(assessment.state, ControlAssessmentState.GAP)
        self.assertEqual(assessment.missing_evidence_types, ("obligation_control_report",))

        matrix = registry.build_matrix(
            institution_id="bank-a",
            matrix_id="privacy-matrix",
            matrix_version=1,
            control_ids=("privacy-obligation",),
            assessed_at=150,
        )
        self.assertEqual(matrix.state, MatrixState.WITH_GAPS)
        self.assertEqual(matrix.gap_control_count, 1)

    def test_stale_evidence_requires_revalidation_and_has_matrix_precedence(self):
        registry = ControlEvidenceRegistry()
        stale_control = control("recovery", domain=ControlDomain.RECOVERY_RESILIENCE, evidence_type="recovery_assessment", source=EvidenceSourceBoundary.RECOVERY)
        missing_control = control("security", domain=ControlDomain.PRIVACY_SECURITY, evidence_type="security_observation", source=EvidenceSourceBoundary.SECURITY)
        registry.register_control(stale_control)
        registry.register_control(missing_control)
        registry.register_evidence(
            evidence(
                "ev-recovery",
                stale_control,
                evidence_type="recovery_assessment",
                source=EvidenceSourceBoundary.RECOVERY,
                observed_at=120,
                revalidate_after=130,
            )
        )

        assessment = registry.assess_control("bank-a", "recovery", assessed_at=150)
        self.assertEqual(assessment.state, ControlAssessmentState.REVALIDATION_REQUIRED)
        self.assertEqual(assessment.stale_evidence_types, ("recovery_assessment",))

        matrix = registry.build_matrix(
            institution_id="bank-a",
            matrix_id="ops-matrix",
            matrix_version=1,
            control_ids=("security", "recovery"),
            assessed_at=150,
        )
        self.assertEqual(matrix.state, MatrixState.REVALIDATION_REQUIRED)
        self.assertEqual(matrix.revalidation_required_control_count, 1)
        self.assertEqual(matrix.gap_control_count, 1)

    def test_new_control_version_does_not_reuse_old_evidence(self):
        registry = ControlEvidenceRegistry()
        first = control("aggregation", version=1)
        registry.register_control(first)
        registry.register_evidence(evidence("ev-v1", first))
        self.assertEqual(
            registry.assess_control("bank-a", "aggregation", assessed_at=150).state,
            ControlAssessmentState.REPRESENTED,
        )

        second = control("aggregation", version=2)
        registry.register_control(second)
        assessment = registry.assess_control("bank-a", "aggregation", assessed_at=150)
        self.assertEqual(assessment.state, ControlAssessmentState.GAP)
        self.assertEqual(assessment.evidence_reference_digests, ())

    def test_wrong_source_and_cross_institution_fail_closed(self):
        registry = ControlEvidenceRegistry()
        definition = control("aggregation")
        registry.register_control(definition)
        with self.assertRaises(GovernanceError):
            registry.register_evidence(evidence("wrong-source", definition, source=EvidenceSourceBoundary.SECURITY))
        with self.assertRaises(GovernanceError):
            registry.register_evidence(evidence("cross-bank", definition, institution_id="bank-b"))

    def test_ambiguous_latest_evidence_fails_closed(self):
        registry = ControlEvidenceRegistry()
        definition = control("aggregation")
        registry.register_control(definition)
        registry.register_evidence(evidence("latest-a", definition, observed_at=140))
        registry.register_evidence(evidence("latest-b", definition, observed_at=140))
        with self.assertRaisesRegex(GovernanceError, "ambiguous latest"):
            registry.assess_control("bank-a", "aggregation", assessed_at=150)

    def test_claim_inflation_is_rejected(self):
        with self.assertRaises(GovernanceError):
            FrameworkReference(
                framework="BCBS 239",
                reference="P1",
                mapping_rationale="test",
                applicability_determined=True,
            )

        definition = control("aggregation")
        with self.assertRaises(GovernanceError):
            ControlEvidenceReference(
                institution_id="bank-a",
                evidence_id="inflated",
                control_digest=definition.artifact_digest,
                evidence_type="aggregation_assessment",
                source_boundary=EvidenceSourceBoundary.BCBS239,
                artifact_type="assessment",
                source_artifact_digest=digest("source"),
                source_snapshot_digest=digest("snapshot"),
                observed_at=1,
                revalidate_after=2,
                verifier_id="validator",
                verification_evidence_digest=digest("verification"),
                evidence_effectiveness_determined=True,
            )


if __name__ == "__main__":
    unittest.main()
