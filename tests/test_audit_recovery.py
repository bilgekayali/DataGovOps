import unittest

from datagovops.audit_recovery import (
    AuditEvent,
    RecoveryAssessmentState,
    RecoveryPolicy,
    append_audit_event,
    assess_recovery,
    build_audit_checkpoint,
    build_backup_evidence,
    build_historical_state_verification,
    build_restore_verification,
    sha256_bytes,
    verify_audit_chain,
    verify_backup_content,
)
from datagovops.models import GovernanceError


class AuditRecoveryTests(unittest.TestCase):
    def _policy(self, institution_id="bank-a"):
        return RecoveryPolicy(
            institution_id=institution_id,
            policy_id="recovery-main",
            policy_version=1,
            owner_id="ops-owner",
            maximum_rpo_seconds=60,
            maximum_rto_seconds=120,
            maximum_backup_age_seconds=600,
            minimum_retention_seconds=3600,
            approved_at=90,
        )

    def _backup(self, policy=None, source=b"historical-state"):
        policy = policy or self._policy()
        return build_backup_evidence(
            policy=policy,
            backup_id="backup-1",
            source_state_digest=sha256_bytes(source),
            source_state_recorded_at=100,
            started_at=110,
            completed_at=120,
            backup_content=b"encrypted-backup-bytes",
            storage_reference="vault://backup-1",
        )

    def test_append_only_audit_chain_and_checkpoint(self):
        first = append_audit_event(
            (),
            institution_id="bank-a",
            event_type="governance_dossier_created",
            actor_id="principal-1",
            subject_type="GovernanceDossier",
            subject_digest="a" * 64,
            occurred_at=100,
            metadata_digest="b" * 64,
        )
        second = append_audit_event(
            (first,),
            institution_id="bank-a",
            event_type="governance_dossier_signed",
            actor_id="principal-1",
            subject_type="SignedGovernanceEvidence",
            subject_digest="c" * 64,
            occurred_at=101,
            metadata_digest="d" * 64,
        )
        self.assertEqual(second.sequence, 2)
        self.assertEqual(second.previous_event_digest, first.artifact_digest)
        self.assertEqual(verify_audit_chain((first, second)), second.artifact_digest)
        checkpoint = build_audit_checkpoint((first, second), institution_id="bank-a", captured_at=102)
        self.assertEqual(checkpoint.head_event_digest, second.artifact_digest)
        self.assertFalse(checkpoint.external_immutability_verified)

    def test_audit_chain_tamper_and_cross_institution_fail_closed(self):
        first = AuditEvent(
            institution_id="bank-a",
            sequence=1,
            event_type="created",
            actor_id="actor",
            subject_type="artifact",
            subject_digest="a" * 64,
            occurred_at=100,
            previous_event_digest=None,
            metadata_digest="b" * 64,
        )
        tampered = AuditEvent(
            institution_id="bank-a",
            sequence=2,
            event_type="changed",
            actor_id="actor",
            subject_type="artifact",
            subject_digest="c" * 64,
            occurred_at=101,
            previous_event_digest="f" * 64,
            metadata_digest="d" * 64,
        )
        with self.assertRaises(GovernanceError):
            verify_audit_chain((first, tampered))
        with self.assertRaises(GovernanceError):
            append_audit_event(
                (first,),
                institution_id="bank-b",
                event_type="changed",
                actor_id="actor",
                subject_type="artifact",
                subject_digest="c" * 64,
                occurred_at=101,
                metadata_digest="d" * 64,
            )

    def test_backup_bytes_restore_history_and_assessment_met(self):
        policy = self._policy()
        source = b"historical-state"
        backup = self._backup(policy, source)
        self.assertEqual(verify_backup_content(backup, b"encrypted-backup-bytes"), backup.backup_artifact_sha256)
        self.assertEqual(backup.retention_expires_at, 3720)
        restore = build_restore_verification(
            backup=backup,
            restore_id="restore-1",
            recovered_state_content=source,
            started_at=130,
            completed_at=150,
            verifier_id="resilience-reviewer",
            verification_evidence_digest="e" * 64,
        )
        history = build_historical_state_verification(
            backup=backup,
            restore=restore,
            state_id="state-2026-08-25",
            verified_at=151,
        )
        self.assertEqual(history.state, RecoveryAssessmentState.MET)
        assessment = assess_recovery(policy=policy, assessed_at=160, backup=backup, restore=restore)
        self.assertEqual(assessment.state, RecoveryAssessmentState.MET)
        self.assertEqual([item.control for item in assessment.controls], sorted(item.control for item in assessment.controls))
        self.assertFalse(assessment.production_recovery_effectiveness_determined)
        self.assertFalse(assessment.regulatory_compliance_determined)

    def test_backup_and_restore_tamper_fail_or_breach(self):
        policy = self._policy()
        backup = self._backup(policy)
        with self.assertRaises(GovernanceError):
            verify_backup_content(backup, b"tampered")
        restore = build_restore_verification(
            backup=backup,
            restore_id="restore-bad",
            recovered_state_content=b"different-state",
            started_at=130,
            completed_at=150,
            verifier_id="reviewer",
            verification_evidence_digest="e" * 64,
        )
        history = build_historical_state_verification(
            backup=backup,
            restore=restore,
            state_id="state-bad",
            verified_at=151,
        )
        self.assertEqual(history.state, RecoveryAssessmentState.BREACHED)
        assessment = assess_recovery(policy=policy, assessed_at=160, backup=backup, restore=restore)
        self.assertEqual(assessment.state, RecoveryAssessmentState.BREACHED)

    def test_missing_restore_is_incomplete_and_stale_backup_is_breached(self):
        policy = self._policy()
        backup = self._backup(policy)
        incomplete = assess_recovery(policy=policy, assessed_at=160, backup=backup, restore=None)
        self.assertEqual(incomplete.state, RecoveryAssessmentState.INCOMPLETE)
        stale = assess_recovery(policy=policy, assessed_at=1000, backup=backup, restore=None)
        self.assertEqual(stale.state, RecoveryAssessmentState.BREACHED)

    def test_policy_binding_and_institution_boundary_fail_closed(self):
        backup = self._backup(self._policy("bank-a"))
        other_policy = self._policy("bank-b")
        with self.assertRaises(GovernanceError):
            assess_recovery(policy=other_policy, assessed_at=160, backup=backup, restore=None)


if __name__ == "__main__":
    unittest.main()
