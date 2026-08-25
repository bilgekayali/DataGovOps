import base64
import json
from pathlib import Path
import unittest

import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from datagovops import (
    EvidenceKeyReference,
    IdentityPolicy,
    InstitutionContext,
    SecurityBoundaryError,
    SecurityObservation,
    assert_institution_scope,
    assert_role,
    canonical_json,
    decrypt_evidence,
    encrypt_evidence,
    verify_ed25519_oidc_token,
)

ROOT = Path(__file__).resolve().parents[1]


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def token(private_key, claims, *, alg="EdDSA"):
    header = b64url(json.dumps({"alg": alg, "typ": "JWT"}, separators=(",", ":"), sort_keys=True).encode())
    payload = b64url(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode())
    signature = private_key.sign(f"{header}.{payload}".encode("ascii"))
    return f"{header}.{payload}.{b64url(signature)}"


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.policy = IdentityPolicy(
            issuer="https://id.example.test",
            audience="datagovops",
            required_roles=("data-governance",),
            require_mfa=True,
        )
        self.claims = {
            "iss": "https://id.example.test",
            "aud": "datagovops",
            "sub": "principal-1",
            "institution_id": "bank-a",
            "roles": ["data-governance", "reader"],
            "mfa": True,
            "nbf": 100,
            "exp": 1000,
        }

    def test_verified_context_and_rbac_are_institution_bound(self):
        context = verify_ed25519_oidc_token(
            token(self.private_key, self.claims),
            self.public_key,
            self.policy,
            expected_institution_id="bank-a",
            now=500,
        )
        self.assertEqual(context.institution_id, "bank-a")
        self.assertEqual(context.principal_id, "principal-1")
        assert_institution_scope(context, "bank-a")
        assert_role(context, "data-governance")
        with self.assertRaisesRegex(SecurityBoundaryError, "cross-institution"):
            assert_institution_scope(context, "bank-b")
        with self.assertRaisesRegex(SecurityBoundaryError, "missing required role"):
            assert_role(context, "admin")

    def test_oidc_verification_fails_closed(self):
        cases = []
        wrong_scope = dict(self.claims, institution_id="bank-b")
        cases.append((token(self.private_key, wrong_scope), "institution scope"))
        missing_mfa = dict(self.claims, mfa=False)
        cases.append((token(self.private_key, missing_mfa), "MFA"))
        wrong_issuer = dict(self.claims, iss="https://attacker.example")
        cases.append((token(self.private_key, wrong_issuer), "issuer"))
        expired = dict(self.claims, exp=300)
        cases.append((token(self.private_key, expired), "expired"))
        for value, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(SecurityBoundaryError, message):
                    verify_ed25519_oidc_token(value, self.public_key, self.policy, expected_institution_id="bank-a", now=500)
        other_key = Ed25519PrivateKey.generate().public_key()
        with self.assertRaisesRegex(SecurityBoundaryError, "signature"):
            verify_ed25519_oidc_token(token(self.private_key, self.claims), other_key, self.policy, expected_institution_id="bank-a", now=500)

    def test_aes_gcm_envelope_is_cross_bound_and_authenticated(self):
        context = InstitutionContext("bank-a", "principal-1", ("data-governance",), "issuer", "aud", 1000, True)
        key_reference = EvidenceKeyReference("external-kms", "governance-evidence", "42")
        key = bytes(range(32))
        envelope = encrypt_evidence(b"governance-evidence", context, key_reference, key, artifact_type="GovernanceDossier", nonce=b"0" * 12)
        self.assertEqual(decrypt_evidence(envelope, context, key), b"governance-evidence")
        other = InstitutionContext("bank-b", "principal-2", ("data-governance",), "issuer", "aud", 1000, True)
        with self.assertRaisesRegex(SecurityBoundaryError, "cross-institution"):
            decrypt_evidence(envelope, other, key)
        with self.assertRaisesRegex(SecurityBoundaryError, "authentication failed"):
            decrypt_evidence(envelope, context, b"x" * 32)
        self.assertFalse(envelope.production_key_management_validated)
        self.assertFalse(envelope.raw_content_logged)
        self.assertFalse(envelope.secrets_logged)

    def test_key_reference_rejects_embedded_secret_material(self):
        with self.assertRaisesRegex(SecurityBoundaryError, "reference"):
            EvidenceKeyReference("external-kms", "secret=password=example", "1")

    def test_security_observation_is_metadata_only(self):
        observation = SecurityObservation(
            observed_at="2026-08-25T09:00:00Z",
            event_type="evidence.decrypt",
            institution_id="bank-a",
            principal_id="principal-1",
            outcome="allowed",
            correlation_id="corr-1",
            artifact_type="GovernanceDossier",
        )
        self.assertFalse(observation.raw_content_logged)
        self.assertFalse(observation.secrets_logged)
        with self.assertRaisesRegex(SecurityBoundaryError, "metadata-only"):
            SecurityObservation(
                observed_at="2026-08-25T09:00:00Z",
                event_type="evidence.decrypt",
                institution_id="bank-a",
                principal_id="principal-1",
                outcome="allowed",
                correlation_id="corr-1",
                raw_content_logged=True,
            )

    def test_runtime_artifacts_validate_strict_schema(self):
        schema = json.loads((ROOT / "schemas" / "security-boundary.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        context = InstitutionContext("bank-a", "principal-1", ("data-governance",), "issuer", "aud", 1000, True)
        policy = IdentityPolicy("issuer", "aud", ("data-governance",))
        envelope = encrypt_evidence(
            b"evidence",
            context,
            EvidenceKeyReference("external-kms", "key-1", "1"),
            b"k" * 32,
            artifact_type="GovernanceDossier",
            nonce=b"1" * 12,
        )
        observation = SecurityObservation("2026-08-25T09:00:00Z", "evidence.encrypt", "bank-a", "principal-1", "allowed", "corr-1")
        validator = jsonschema.Draft202012Validator(schema)
        for artifact in (context, policy, envelope, observation):
            with self.subTest(artifact=type(artifact).__name__):
                validator.validate(json.loads(canonical_json(artifact)))

    def test_postgresql_rls_reference_is_fail_closed(self):
        sql = (ROOT / "deployment" / "postgresql-institution-rls.sql").read_text(encoding="utf-8")
        for marker in (
            "NOBYPASSRLS",
            "ENABLE ROW LEVEL SECURITY",
            "FORCE ROW LEVEL SECURITY",
            "current_setting('datagovops.institution_id', true)",
            "WITH CHECK",
            "REVOKE ALL ON datagovops_evidence FROM PUBLIC",
            "SET LOCAL datagovops.institution_id",
        ):
            self.assertIn(marker, sql)


if __name__ == "__main__":
    unittest.main()
