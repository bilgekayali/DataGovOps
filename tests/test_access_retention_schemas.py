import json
from pathlib import Path
import unittest

import jsonschema

from datagovops import (
    AccessApprovalDecision,
    AccessGrant,
    AccessPurposeApproval,
    AccessRole,
    AccessSubjectKind,
    DataLocationEvidence,
    DataLocationKind,
    DeletionEligibilityEvaluation,
    DeletionEligibilityState,
    GovernanceControlPolicy,
    GovernanceControlReport,
    LegalHold,
    LegalHoldRelease,
    ObligationCategory,
    ObligationMappingStatus,
    PrivacySecurityObligationMapping,
    RetentionSchedule,
    canonical_json,
    digest_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


class AccessRetentionSchemaTests(unittest.TestCase):
    def evidence(self, label):
        return digest_artifact({"evidence": label})

    def schema(self, name):
        value = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(value)
        self.assertFalse(value["additionalProperties"])
        return value

    def test_runtime_control_artifacts_validate_strict_schemas(self):
        asset_digest = self.evidence("asset")
        purpose_digest = self.evidence("purpose")
        binding_digest = self.evidence("binding")
        role = AccessRole(
            institution_id="bank-a",
            role_id="analyst",
            role_version=1,
            name="Analyst",
            owner_id="owner",
            member_principal_ids=("user-1",),
            permissions=("read",),
            evidence_digest=self.evidence("role"),
            registered_at="2026-08-18T08:00:00Z",
        )
        approval = AccessPurposeApproval(
            institution_id="bank-a",
            approval_id="approval",
            subject_kind=AccessSubjectKind.ROLE,
            subject_id=role.role_id,
            subject_role_version=1,
            subject_digest=role.artifact_digest,
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            purpose_id="purpose",
            purpose_version=1,
            purpose_digest=purpose_digest,
            purpose_binding_id="binding",
            purpose_binding_digest=binding_digest,
            decision=AccessApprovalDecision.APPROVED,
            reviewer_id="reviewer",
            rationale="Explicit governed approval.",
            evidence_digest=self.evidence("approval"),
            decided_at="2026-08-18T08:01:00Z",
        )
        grant = AccessGrant(
            institution_id="bank-a",
            grant_id="grant",
            approval_digest=approval.artifact_digest,
            subject_kind=AccessSubjectKind.ROLE,
            subject_id=role.role_id,
            subject_role_version=1,
            subject_digest=role.artifact_digest,
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            purpose_id="purpose",
            purpose_version=1,
            purpose_digest=purpose_digest,
            permissions=("read",),
            granted_by_id="grantor",
            valid_from="2026-08-18T08:02:00Z",
            expires_at=None,
            evidence_digest=self.evidence("grant"),
            granted_at="2026-08-18T08:02:00Z",
        )
        schedule = RetentionSchedule(
            institution_id="bank-a",
            schedule_id="retention",
            schedule_version=1,
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            owner_id="retention-owner",
            retention_trigger_at="2026-08-01T00:00:00Z",
            retention_days=30,
            rationale="Institution-owned retention input.",
            evidence_digest=self.evidence("retention"),
            registered_at="2026-08-18T08:03:00Z",
        )
        hold = LegalHold(
            institution_id="bank-a",
            hold_id="hold",
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            owner_id="legal-owner",
            rationale="Explicit hold.",
            evidence_digest=self.evidence("hold"),
            starts_at="2026-08-10T00:00:00Z",
            recorded_at="2026-08-10T01:00:00Z",
        )
        release = LegalHoldRelease(
            institution_id="bank-a",
            release_id="release",
            hold_id=hold.hold_id,
            hold_digest=hold.artifact_digest,
            released_by_id="legal-owner",
            rationale="Explicit release.",
            evidence_digest=self.evidence("release"),
            released_at="2026-08-18T09:00:00Z",
        )
        deletion = DeletionEligibilityEvaluation(
            institution_id="bank-a",
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            schedule_digest=schedule.artifact_digest,
            retention_deadline="2026-08-31T00:00:00Z",
            active_hold_digests=(),
            state=DeletionEligibilityState.NOT_DUE,
            reason_code="retention_period_not_elapsed",
            evaluated_at="2026-08-18T10:00:00Z",
        )
        location = DataLocationEvidence(
            institution_id="bank-a",
            location_id="loc",
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            location_kind=DataLocationKind.STORAGE,
            country_code="TR",
            region=None,
            cross_border=False,
            reviewer_id="reviewer",
            evidence_digest=self.evidence("location"),
            observed_at="2026-08-18T08:04:00Z",
        )
        mapping = PrivacySecurityObligationMapping(
            institution_id="bank-a",
            mapping_id="mapping",
            asset_id="asset",
            asset_version=1,
            asset_digest=asset_digest,
            category=ObligationCategory.PRIVACY,
            obligation_reference="institution-review",
            status=ObligationMappingStatus.REVIEW_REQUIRED,
            reviewer_id="reviewer",
            rationale="Legal applicability remains external.",
            location_evidence_digests=(location.artifact_digest,),
            evidence_digest=self.evidence("mapping"),
            reviewed_at="2026-08-18T08:05:00Z",
        )
        policy = GovernanceControlPolicy(
            institution_id="bank-a",
            policy_id="policy",
            policy_version=1,
            owner_id="owner",
            require_retention_schedule=True,
            require_obligation_mapping_for_personal_data=True,
            require_location_evidence_for_personal_data=True,
            evidence_digest=self.evidence("policy"),
            registered_at="2026-08-18T08:06:00Z",
        )
        report = GovernanceControlReport(
            institution_id="bank-a",
            policy_digest=policy.artifact_digest,
            asset_registry_snapshot_digest=self.evidence("asset-snapshot"),
            semantic_governance_snapshot_digest=self.evidence("semantic-snapshot"),
            control_snapshot_digest=self.evidence("control-snapshot"),
            gaps=(),
            complete=True,
            evaluated_at="2026-08-18T10:00:00Z",
        )

        fixtures = {
            "access-role.schema.json": role,
            "access-purpose-approval.schema.json": approval,
            "access-grant.schema.json": grant,
            "retention-schedule.schema.json": schedule,
            "legal-hold.schema.json": hold,
            "legal-hold-release.schema.json": release,
            "deletion-eligibility-evaluation.schema.json": deletion,
            "data-location-evidence.schema.json": location,
            "privacy-security-obligation-mapping.schema.json": mapping,
            "governance-control-policy.schema.json": policy,
            "governance-control-report.schema.json": report,
        }
        for schema_name, artifact in fixtures.items():
            with self.subTest(schema=schema_name):
                jsonschema.Draft202012Validator(self.schema(schema_name)).validate(
                    json.loads(canonical_json(artifact))
                )

    def test_schema_rejects_unknown_property_and_legal_overclaim(self):
        schema = self.schema("privacy-security-obligation-mapping.schema.json")
        payload = {
            "institution_id":"bank-a",
            "mapping_id":"m",
            "asset_id":"a",
            "asset_version":1,
            "asset_digest":"a"*64,
            "category":"privacy",
            "obligation_reference":"review",
            "status":"review_required",
            "reviewer_id":"reviewer",
            "rationale":"review",
            "location_evidence_digests":[],
            "evidence_digest":"b"*64,
            "reviewed_at":"2026-08-18T08:00:00Z",
            "legal_applicability_determined":True,
            "schema_version":"datagovops.privacy-security-obligation-mapping.v1",
            "unknown":True,
        }
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(payload)


if __name__ == "__main__":
    unittest.main()
