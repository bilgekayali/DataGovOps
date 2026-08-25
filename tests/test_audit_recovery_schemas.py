import json
from pathlib import Path
import unittest

import jsonschema

from datagovops.audit_recovery import (
    append_audit_event,
    assess_recovery,
    build_audit_checkpoint,
    build_backup_evidence,
    build_historical_state_verification,
    build_restore_verification,
    RecoveryPolicy,
    sha256_bytes,
)
from datagovops.models import canonical_json


ROOT = Path(__file__).resolve().parents[1]


class AuditRecoverySchemaTests(unittest.TestCase):
    def _schema(self, name):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        self.assertFalse(schema["additionalProperties"])
        return schema

    def test_strict_schemas_accept_runtime_contracts(self):
        event = append_audit_event(
            (), institution_id="bank-a", event_type="snapshot", actor_id="owner",
            subject_type="GovernanceDossier", subject_digest="a" * 64,
            occurred_at=100, metadata_digest="b" * 64,
        )
        checkpoint = build_audit_checkpoint((event,), institution_id="bank-a", captured_at=101)
        policy = RecoveryPolicy(
            institution_id="bank-a", policy_id="recovery", policy_version=1,
            owner_id="owner", maximum_rpo_seconds=60, maximum_rto_seconds=120,
            maximum_backup_age_seconds=600, minimum_retention_seconds=3600,
            approved_at=90,
        )
        state = b"historical-state"
        backup = build_backup_evidence(
            policy=policy, backup_id="backup-1", source_state_digest=sha256_bytes(state),
            source_state_recorded_at=100, started_at=110, completed_at=120,
            backup_content=b"backup-bytes", storage_reference="vault://backup-1",
        )
        restore = build_restore_verification(
            backup=backup, restore_id="restore-1", recovered_state_content=state,
            started_at=130, completed_at=150, verifier_id="reviewer",
            verification_evidence_digest="c" * 64,
        )
        history = build_historical_state_verification(
            backup=backup, restore=restore, state_id="state-1", verified_at=151,
        )
        assessment = assess_recovery(policy=policy, assessed_at=160, backup=backup, restore=restore)
        fixtures = {
            "audit-event.schema.json": event,
            "audit-chain-checkpoint.schema.json": checkpoint,
            "recovery-policy.schema.json": policy,
            "backup-evidence.schema.json": backup,
            "restore-verification.schema.json": restore,
            "historical-state-verification.schema.json": history,
            "recovery-assessment.schema.json": assessment,
        }
        for schema_name, artifact in fixtures.items():
            with self.subTest(schema=schema_name):
                schema = self._schema(schema_name)
                payload = json.loads(canonical_json(artifact))
                jsonschema.Draft202012Validator(schema).validate(payload)

    def test_recovery_schema_rejects_unknown_properties(self):
        schema = self._schema("recovery-assessment.schema.json")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["production_recovery_effectiveness_determined"]["const"], False)
        self.assertEqual(schema["properties"]["regulatory_compliance_determined"]["const"], False)


if __name__ == "__main__":
    unittest.main()
