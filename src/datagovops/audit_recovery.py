from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from .models import GovernanceError, digest_artifact


AUDIT_EVENT_SCHEMA_VERSION = "datagovops.audit-event.v1"
AUDIT_CHECKPOINT_SCHEMA_VERSION = "datagovops.audit-chain-checkpoint.v1"
RECOVERY_POLICY_SCHEMA_VERSION = "datagovops.recovery-policy.v1"
BACKUP_EVIDENCE_SCHEMA_VERSION = "datagovops.backup-evidence.v1"
RESTORE_VERIFICATION_SCHEMA_VERSION = "datagovops.restore-verification.v1"
HISTORICAL_STATE_SCHEMA_VERSION = "datagovops.historical-state-verification.v1"
RECOVERY_ASSESSMENT_SCHEMA_VERSION = "datagovops.recovery-assessment.v1"


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceError(f"{name} must be non-empty text")
    return value.strip()


def _timestamp(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceError(f"{name} must be a non-negative integer timestamp")
    return value


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GovernanceError(f"{name} must be a positive integer")
    return value


def _digest(name: str, value: Any) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise GovernanceError(f"{name} must be a lowercase SHA-256 digest")
    return value


def sha256_bytes(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise GovernanceError("content must be bytes")
    return hashlib.sha256(content).hexdigest()


class RecoveryAssessmentState(str, Enum):
    MET = "met"
    BREACHED = "breached"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    institution_id: str
    sequence: int
    event_type: str
    actor_id: str
    subject_type: str
    subject_digest: str
    occurred_at: int
    previous_event_digest: str | None
    metadata_digest: str
    schema_version: str = AUDIT_EVENT_SCHEMA_VERSION
    raw_content_logged: bool = False
    secret_material_logged: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != AUDIT_EVENT_SCHEMA_VERSION:
            raise GovernanceError("unsupported audit-event schema version")
        for name in ("institution_id", "event_type", "actor_id", "subject_type"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        _positive_int("sequence", self.sequence)
        _digest("subject_digest", self.subject_digest)
        _timestamp("occurred_at", self.occurred_at)
        if self.previous_event_digest is not None:
            _digest("previous_event_digest", self.previous_event_digest)
        _digest("metadata_digest", self.metadata_digest)
        if self.raw_content_logged is not False or self.secret_material_logged is not False:
            raise GovernanceError("audit events must remain metadata-only")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


def append_audit_event(
    events: Sequence[AuditEvent],
    *,
    institution_id: str,
    event_type: str,
    actor_id: str,
    subject_type: str,
    subject_digest: str,
    occurred_at: int,
    metadata_digest: str,
) -> AuditEvent:
    institution_id = _text("institution_id", institution_id)
    existing = tuple(events)
    if existing:
        verify_audit_chain(existing, expected_institution_id=institution_id)
        previous = existing[-1]
        if occurred_at < previous.occurred_at:
            raise GovernanceError("audit event timestamp cannot move backwards")
        sequence = previous.sequence + 1
        previous_digest = previous.artifact_digest
    else:
        sequence = 1
        previous_digest = None
    return AuditEvent(
        institution_id=institution_id,
        sequence=sequence,
        event_type=event_type,
        actor_id=actor_id,
        subject_type=subject_type,
        subject_digest=subject_digest,
        occurred_at=occurred_at,
        previous_event_digest=previous_digest,
        metadata_digest=metadata_digest,
    )


def verify_audit_chain(
    events: Sequence[AuditEvent],
    *,
    expected_institution_id: str | None = None,
) -> str:
    if not events:
        raise GovernanceError("audit chain must contain at least one event")
    expected = _text("expected_institution_id", expected_institution_id) if expected_institution_id is not None else events[0].institution_id
    previous_digest: str | None = None
    previous_time: int | None = None
    for index, event in enumerate(events, start=1):
        if not isinstance(event, AuditEvent):
            raise GovernanceError("audit chain contains unsupported event")
        if event.institution_id != expected:
            raise GovernanceError("audit chain crosses institution boundary")
        if event.sequence != index:
            raise GovernanceError("audit chain sequence is not contiguous")
        if event.previous_event_digest != previous_digest:
            raise GovernanceError("audit chain previous-event digest mismatch")
        if previous_time is not None and event.occurred_at < previous_time:
            raise GovernanceError("audit chain timestamps move backwards")
        previous_digest = event.artifact_digest
        previous_time = event.occurred_at
    assert previous_digest is not None
    return previous_digest


@dataclass(frozen=True, slots=True)
class AuditChainCheckpoint:
    institution_id: str
    through_sequence: int
    event_count: int
    head_event_digest: str
    captured_at: int
    schema_version: str = AUDIT_CHECKPOINT_SCHEMA_VERSION
    external_immutability_verified: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != AUDIT_CHECKPOINT_SCHEMA_VERSION:
            raise GovernanceError("unsupported audit-chain-checkpoint schema version")
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        _positive_int("through_sequence", self.through_sequence)
        _positive_int("event_count", self.event_count)
        if self.through_sequence != self.event_count:
            raise GovernanceError("checkpoint sequence must equal represented event count")
        _digest("head_event_digest", self.head_event_digest)
        _timestamp("captured_at", self.captured_at)
        if self.external_immutability_verified is not False:
            raise GovernanceError("reference checkpoint cannot claim external immutability")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


def build_audit_checkpoint(events: Sequence[AuditEvent], *, institution_id: str, captured_at: int) -> AuditChainCheckpoint:
    head = verify_audit_chain(events, expected_institution_id=institution_id)
    if captured_at < events[-1].occurred_at:
        raise GovernanceError("checkpoint cannot predate its audit-chain head")
    return AuditChainCheckpoint(
        institution_id=institution_id,
        through_sequence=events[-1].sequence,
        event_count=len(events),
        head_event_digest=head,
        captured_at=captured_at,
    )


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    institution_id: str
    policy_id: str
    policy_version: int
    owner_id: str
    maximum_rpo_seconds: int
    maximum_rto_seconds: int
    maximum_backup_age_seconds: int
    minimum_retention_seconds: int
    approved_at: int
    schema_version: str = RECOVERY_POLICY_SCHEMA_VERSION
    production_effectiveness_determined: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RECOVERY_POLICY_SCHEMA_VERSION:
            raise GovernanceError("unsupported recovery-policy schema version")
        for name in ("institution_id", "policy_id", "owner_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        _positive_int("policy_version", self.policy_version)
        _positive_int("maximum_rpo_seconds", self.maximum_rpo_seconds)
        _positive_int("maximum_rto_seconds", self.maximum_rto_seconds)
        _positive_int("maximum_backup_age_seconds", self.maximum_backup_age_seconds)
        _positive_int("minimum_retention_seconds", self.minimum_retention_seconds)
        _timestamp("approved_at", self.approved_at)
        if self.production_effectiveness_determined is not False:
            raise GovernanceError("recovery policy cannot determine production effectiveness")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


@dataclass(frozen=True, slots=True)
class BackupEvidence:
    institution_id: str
    backup_id: str
    policy_digest: str
    source_state_digest: str
    source_state_recorded_at: int
    started_at: int
    completed_at: int
    backup_artifact_sha256: str
    backup_size_bytes: int
    storage_reference: str
    retention_expires_at: int
    schema_version: str = BACKUP_EVIDENCE_SCHEMA_VERSION
    production_backup_verified: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BACKUP_EVIDENCE_SCHEMA_VERSION:
            raise GovernanceError("unsupported backup-evidence schema version")
        for name in ("institution_id", "backup_id", "storage_reference"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        _digest("policy_digest", self.policy_digest)
        _digest("source_state_digest", self.source_state_digest)
        _timestamp("source_state_recorded_at", self.source_state_recorded_at)
        _timestamp("started_at", self.started_at)
        _timestamp("completed_at", self.completed_at)
        if self.started_at < self.source_state_recorded_at:
            raise GovernanceError("backup cannot start before represented source state")
        if self.completed_at < self.started_at:
            raise GovernanceError("backup completion cannot predate start")
        _digest("backup_artifact_sha256", self.backup_artifact_sha256)
        _positive_int("backup_size_bytes", self.backup_size_bytes)
        _timestamp("retention_expires_at", self.retention_expires_at)
        if self.retention_expires_at < self.completed_at:
            raise GovernanceError("backup retention cannot expire before completion")
        if self.production_backup_verified is not False:
            raise GovernanceError("reference backup evidence cannot claim production verification")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


def build_backup_evidence(
    *,
    policy: RecoveryPolicy,
    backup_id: str,
    source_state_digest: str,
    source_state_recorded_at: int,
    started_at: int,
    completed_at: int,
    backup_content: bytes,
    storage_reference: str,
) -> BackupEvidence:
    return BackupEvidence(
        institution_id=policy.institution_id,
        backup_id=backup_id,
        policy_digest=policy.artifact_digest,
        source_state_digest=source_state_digest,
        source_state_recorded_at=source_state_recorded_at,
        started_at=started_at,
        completed_at=completed_at,
        backup_artifact_sha256=sha256_bytes(backup_content),
        backup_size_bytes=len(backup_content),
        storage_reference=storage_reference,
        retention_expires_at=completed_at + policy.minimum_retention_seconds,
    )


def verify_backup_content(backup: BackupEvidence, content: bytes) -> str:
    if not isinstance(backup, BackupEvidence):
        raise GovernanceError("backup evidence is required")
    if not isinstance(content, bytes):
        raise GovernanceError("backup content must be bytes")
    if len(content) != backup.backup_size_bytes or sha256_bytes(content) != backup.backup_artifact_sha256:
        raise GovernanceError("backup artifact bytes do not match represented evidence")
    return backup.backup_artifact_sha256


@dataclass(frozen=True, slots=True)
class RestoreVerification:
    institution_id: str
    restore_id: str
    backup_digest: str
    expected_state_digest: str
    recovered_state_digest: str
    started_at: int
    completed_at: int
    verifier_id: str
    verification_evidence_digest: str
    schema_version: str = RESTORE_VERIFICATION_SCHEMA_VERSION
    production_restore_verified: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RESTORE_VERIFICATION_SCHEMA_VERSION:
            raise GovernanceError("unsupported restore-verification schema version")
        for name in ("institution_id", "restore_id", "verifier_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        for name in ("backup_digest", "expected_state_digest", "recovered_state_digest", "verification_evidence_digest"):
            _digest(name, getattr(self, name))
        _timestamp("started_at", self.started_at)
        _timestamp("completed_at", self.completed_at)
        if self.completed_at < self.started_at:
            raise GovernanceError("restore completion cannot predate start")
        if self.production_restore_verified is not False:
            raise GovernanceError("reference restore verification cannot claim production verification")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)

    @property
    def integrity_matches(self) -> bool:
        return self.expected_state_digest == self.recovered_state_digest


def build_restore_verification(
    *,
    backup: BackupEvidence,
    restore_id: str,
    recovered_state_content: bytes,
    started_at: int,
    completed_at: int,
    verifier_id: str,
    verification_evidence_digest: str,
) -> RestoreVerification:
    return RestoreVerification(
        institution_id=backup.institution_id,
        restore_id=restore_id,
        backup_digest=backup.artifact_digest,
        expected_state_digest=backup.source_state_digest,
        recovered_state_digest=sha256_bytes(recovered_state_content),
        started_at=started_at,
        completed_at=completed_at,
        verifier_id=verifier_id,
        verification_evidence_digest=verification_evidence_digest,
    )


@dataclass(frozen=True, slots=True)
class HistoricalStateVerification:
    institution_id: str
    state_id: str
    backup_digest: str
    restore_verification_digest: str
    expected_state_digest: str
    recovered_state_digest: str
    verified_at: int
    state: RecoveryAssessmentState
    schema_version: str = HISTORICAL_STATE_SCHEMA_VERSION
    production_history_reconstruction_verified: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != HISTORICAL_STATE_SCHEMA_VERSION:
            raise GovernanceError("unsupported historical-state-verification schema version")
        for name in ("institution_id", "state_id"):
            object.__setattr__(self, name, _text(name, getattr(self, name)))
        for name in ("backup_digest", "restore_verification_digest", "expected_state_digest", "recovered_state_digest"):
            _digest(name, getattr(self, name))
        _timestamp("verified_at", self.verified_at)
        expected = RecoveryAssessmentState.MET if self.expected_state_digest == self.recovered_state_digest else RecoveryAssessmentState.BREACHED
        if self.state is not expected:
            raise GovernanceError("historical-state verification state does not match represented digests")
        if self.production_history_reconstruction_verified is not False:
            raise GovernanceError("historical-state evidence cannot claim production reconstruction verification")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


def build_historical_state_verification(
    *,
    backup: BackupEvidence,
    restore: RestoreVerification,
    state_id: str,
    verified_at: int,
) -> HistoricalStateVerification:
    if restore.institution_id != backup.institution_id:
        raise GovernanceError("historical-state verification crosses institution boundary")
    if restore.backup_digest != backup.artifact_digest:
        raise GovernanceError("restore verification does not reference supplied backup")
    if restore.expected_state_digest != backup.source_state_digest:
        raise GovernanceError("restore expected state does not match backup source state")
    if verified_at < restore.completed_at:
        raise GovernanceError("historical-state verification cannot predate restore completion")
    state = RecoveryAssessmentState.MET if restore.integrity_matches else RecoveryAssessmentState.BREACHED
    return HistoricalStateVerification(
        institution_id=backup.institution_id,
        state_id=state_id,
        backup_digest=backup.artifact_digest,
        restore_verification_digest=restore.artifact_digest,
        expected_state_digest=backup.source_state_digest,
        recovered_state_digest=restore.recovered_state_digest,
        verified_at=verified_at,
        state=state,
    )


@dataclass(frozen=True, slots=True)
class RecoveryControlAssessment:
    control: str
    state: RecoveryAssessmentState
    observed_value: int | bool | None
    threshold_value: int | bool | None
    reason_code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "control", _text("control", self.control))
        object.__setattr__(self, "reason_code", _text("reason_code", self.reason_code))
        if isinstance(self.observed_value, int) and not isinstance(self.observed_value, bool) and self.observed_value < 0:
            raise GovernanceError("recovery observed values cannot be negative")
        if isinstance(self.threshold_value, int) and not isinstance(self.threshold_value, bool) and self.threshold_value < 0:
            raise GovernanceError("recovery threshold values cannot be negative")


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    institution_id: str
    policy_digest: str
    backup_digest: str | None
    restore_verification_digest: str | None
    assessed_at: int
    controls: tuple[RecoveryControlAssessment, ...]
    state: RecoveryAssessmentState
    schema_version: str = RECOVERY_ASSESSMENT_SCHEMA_VERSION
    production_recovery_effectiveness_determined: bool = False
    regulatory_compliance_determined: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RECOVERY_ASSESSMENT_SCHEMA_VERSION:
            raise GovernanceError("unsupported recovery-assessment schema version")
        object.__setattr__(self, "institution_id", _text("institution_id", self.institution_id))
        _digest("policy_digest", self.policy_digest)
        if self.backup_digest is not None:
            _digest("backup_digest", self.backup_digest)
        if self.restore_verification_digest is not None:
            _digest("restore_verification_digest", self.restore_verification_digest)
        _timestamp("assessed_at", self.assessed_at)
        names = [item.control for item in self.controls]
        if names != sorted(names) or len(names) != len(set(names)):
            raise GovernanceError("recovery controls must be sorted and unique")
        expected = RecoveryAssessmentState.MET
        if any(item.state is RecoveryAssessmentState.BREACHED for item in self.controls):
            expected = RecoveryAssessmentState.BREACHED
        elif any(item.state is RecoveryAssessmentState.INCOMPLETE for item in self.controls):
            expected = RecoveryAssessmentState.INCOMPLETE
        if self.state is not expected:
            raise GovernanceError("recovery assessment state does not match control precedence")
        if self.production_recovery_effectiveness_determined is not False:
            raise GovernanceError("recovery assessment cannot determine production effectiveness")
        if self.regulatory_compliance_determined is not False:
            raise GovernanceError("recovery assessment cannot determine regulatory compliance")

    @property
    def artifact_digest(self) -> str:
        return digest_artifact(self)


def assess_recovery(
    *,
    policy: RecoveryPolicy,
    assessed_at: int,
    backup: BackupEvidence | None,
    restore: RestoreVerification | None,
) -> RecoveryAssessment:
    _timestamp("assessed_at", assessed_at)
    controls: list[RecoveryControlAssessment] = []
    if backup is None:
        controls.extend([
            RecoveryControlAssessment("backup_freshness", RecoveryAssessmentState.INCOMPLETE, None, policy.maximum_backup_age_seconds, "backup_missing"),
            RecoveryControlAssessment("rpo", RecoveryAssessmentState.INCOMPLETE, None, policy.maximum_rpo_seconds, "backup_missing"),
            RecoveryControlAssessment("retention_schedule", RecoveryAssessmentState.INCOMPLETE, None, policy.minimum_retention_seconds, "backup_missing"),
            RecoveryControlAssessment("restore_integrity", RecoveryAssessmentState.INCOMPLETE, None, True, "restore_missing"),
            RecoveryControlAssessment("rto", RecoveryAssessmentState.INCOMPLETE, None, policy.maximum_rto_seconds, "restore_missing"),
        ])
        backup_digest = None
        restore_digest = None
    else:
        if backup.institution_id != policy.institution_id:
            raise GovernanceError("recovery assessment crosses institution boundary")
        if backup.policy_digest != policy.artifact_digest:
            raise GovernanceError("backup evidence is not bound to supplied recovery policy")
        if assessed_at < backup.completed_at:
            raise GovernanceError("recovery assessment cannot predate backup completion")
        age = assessed_at - backup.completed_at
        rpo = backup.completed_at - backup.source_state_recorded_at
        retention = backup.retention_expires_at - backup.completed_at
        controls.extend([
            RecoveryControlAssessment("backup_freshness", RecoveryAssessmentState.MET if age <= policy.maximum_backup_age_seconds else RecoveryAssessmentState.BREACHED, age, policy.maximum_backup_age_seconds, "backup_age_within_policy" if age <= policy.maximum_backup_age_seconds else "backup_age_exceeds_policy"),
            RecoveryControlAssessment("rpo", RecoveryAssessmentState.MET if rpo <= policy.maximum_rpo_seconds else RecoveryAssessmentState.BREACHED, rpo, policy.maximum_rpo_seconds, "represented_rpo_within_policy" if rpo <= policy.maximum_rpo_seconds else "represented_rpo_exceeds_policy"),
            RecoveryControlAssessment("retention_schedule", RecoveryAssessmentState.MET if retention >= policy.minimum_retention_seconds else RecoveryAssessmentState.BREACHED, retention, policy.minimum_retention_seconds, "retention_schedule_meets_policy" if retention >= policy.minimum_retention_seconds else "retention_schedule_below_policy"),
        ])
        backup_digest = backup.artifact_digest
        if restore is None:
            controls.extend([
                RecoveryControlAssessment("restore_integrity", RecoveryAssessmentState.INCOMPLETE, None, True, "restore_missing"),
                RecoveryControlAssessment("rto", RecoveryAssessmentState.INCOMPLETE, None, policy.maximum_rto_seconds, "restore_missing"),
            ])
            restore_digest = None
        else:
            if restore.institution_id != policy.institution_id:
                raise GovernanceError("restore verification crosses institution boundary")
            if restore.backup_digest != backup.artifact_digest:
                raise GovernanceError("restore verification does not reference supplied backup")
            if restore.expected_state_digest != backup.source_state_digest:
                raise GovernanceError("restore expected state does not match backup source state")
            if assessed_at < restore.completed_at:
                raise GovernanceError("recovery assessment cannot predate restore verification")
            duration = restore.completed_at - restore.started_at
            controls.extend([
                RecoveryControlAssessment("restore_integrity", RecoveryAssessmentState.MET if restore.integrity_matches else RecoveryAssessmentState.BREACHED, restore.integrity_matches, True, "restored_state_digest_matches" if restore.integrity_matches else "restored_state_digest_mismatch"),
                RecoveryControlAssessment("rto", RecoveryAssessmentState.MET if duration <= policy.maximum_rto_seconds else RecoveryAssessmentState.BREACHED, duration, policy.maximum_rto_seconds, "represented_rto_within_policy" if duration <= policy.maximum_rto_seconds else "represented_rto_exceeds_policy"),
            ])
            restore_digest = restore.artifact_digest
    controls_tuple = tuple(sorted(controls, key=lambda item: item.control))
    state = RecoveryAssessmentState.MET
    if any(item.state is RecoveryAssessmentState.BREACHED for item in controls_tuple):
        state = RecoveryAssessmentState.BREACHED
    elif any(item.state is RecoveryAssessmentState.INCOMPLETE for item in controls_tuple):
        state = RecoveryAssessmentState.INCOMPLETE
    return RecoveryAssessment(
        institution_id=policy.institution_id,
        policy_digest=policy.artifact_digest,
        backup_digest=backup_digest,
        restore_verification_digest=restore_digest,
        assessed_at=assessed_at,
        controls=controls_tuple,
        state=state,
    )
