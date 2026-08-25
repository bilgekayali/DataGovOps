from dataclasses import asdict
import unittest

from datagovops.deployment_hardening import (
    DeploymentAssuranceState,
    DeploymentControlState,
    DeploymentEvidence,
    ImmutableImageReference,
    NetworkBoundary,
    RuntimeObservation,
    RuntimeSecurityProfile,
    SecretInjectionReference,
    assess_deployment,
    assert_same_institution,
    deployment_evidence_digest,
)


class DeploymentHardeningTests(unittest.TestCase):
    def _profile(self, **overrides):
        values = dict(
            run_as_non_root=True,
            read_only_root_filesystem=True,
            allow_privilege_escalation=False,
            privileged=False,
            drop_all_capabilities=True,
            seccomp_runtime_default=True,
            host_network=False,
            host_pid=False,
            host_ipc=False,
            automount_service_account_token=False,
        )
        values.update(overrides)
        return RuntimeSecurityProfile(**values)

    def _evidence(self, **overrides):
        values = dict(
            institution_id="bank-a",
            environment_id="prod-eu-reference",
            workload_id="datagovops-api",
            image=ImmutableImageReference("registry.example/datagovops", "a" * 64),
            runtime_security=self._profile(),
            network_boundary=NetworkBoundary(True, True, ()),
            secret_references=(SecretInjectionReference("external-kms", "db-credential", "7"),),
            manifest_sha256="b" * 64,
            validator_id="policy-validator-v1",
            observed_at=100,
            negative_path_confirmed=True,
        )
        values.update(overrides)
        return DeploymentEvidence(**values)

    def test_immutable_image_requires_digest_and_rejects_tag(self):
        with self.assertRaises(ValueError):
            ImmutableImageReference("registry.example/datagovops:latest", "a" * 64)
        with self.assertRaises(ValueError):
            ImmutableImageReference("registry.example/datagovops", "not-a-digest")

    def test_hardened_evidence_is_represented_without_claim_inflation(self):
        evidence = self._evidence()
        assessment = assess_deployment(evidence, assessed_at=110)
        self.assertEqual(assessment.state, DeploymentAssuranceState.REPRESENTED)
        self.assertTrue(all(c.state is DeploymentControlState.REPRESENTED for c in assessment.controls))
        self.assertFalse(assessment.production_effectiveness_determined)
        self.assertFalse(assessment.supply_chain_security_determined)
        self.assertFalse(assessment.regulatory_compliance_determined)
        self.assertTrue(assessment.requires_human_review)
        self.assertEqual(assessment.evidence_sha256, deployment_evidence_digest(evidence))

    def test_insecure_runtime_is_incomplete(self):
        evidence = self._evidence(runtime_security=self._profile(read_only_root_filesystem=False, privileged=True))
        assessment = assess_deployment(evidence, assessed_at=110)
        self.assertEqual(assessment.state, DeploymentAssuranceState.INCOMPLETE)
        gaps = {c.control_id for c in assessment.controls if c.state is DeploymentControlState.GAP}
        self.assertEqual(gaps, {"read_only_root_filesystem", "privileged_mode_disabled"})

    def test_missing_negative_path_is_incomplete(self):
        assessment = assess_deployment(self._evidence(negative_path_confirmed=False), assessed_at=110)
        self.assertEqual(assessment.state, DeploymentAssuranceState.INCOMPLETE)
        self.assertIn("validator_negative_path", {c.control_id for c in assessment.controls if c.state is DeploymentControlState.GAP})

    def test_runtime_observation_is_metadata_only(self):
        observation = RuntimeObservation(
            institution_id="bank-a",
            environment_id="prod-eu-reference",
            workload_id="datagovops-api",
            observation_type="container_restart_count",
            status="observed",
            evidence_sha256="c" * 64,
            observed_at=100,
        )
        self.assertFalse(observation.raw_content_logged)
        with self.assertRaises(ValueError):
            RuntimeObservation(
                institution_id="bank-a", environment_id="env", workload_id="workload",
                observation_type="log", status="observed", evidence_sha256="c" * 64,
                observed_at=100, secret_material_logged=True,
            )

    def test_cross_institution_evidence_fails_closed(self):
        with self.assertRaises(ValueError):
            assert_same_institution("bank-b", (self._evidence(),))

    def test_secret_reference_contains_metadata_only(self):
        reference = SecretInjectionReference("vault", "credential/path", "v3")
        self.assertEqual(asdict(reference), {"provider": "vault", "secret_id": "credential/path", "version": "v3"})


if __name__ == "__main__":
    unittest.main()
