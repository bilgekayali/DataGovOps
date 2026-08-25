# DataGovOps Institution Security Boundary

DataGovOps v0.4 adds a reference security boundary around the existing institution-scoped governance model.

## Identity and authorization

`IdentityPolicy` verifies pre-resolved Ed25519-signed JWT/OIDC tokens without network or JWKS access. Verification is fail-closed for signature, issuer, audience, expiry/not-before, institution scope, required roles and MFA evidence. A verified token yields an immutable `InstitutionContext`.

The runtime intentionally accepts a trusted `Ed25519PublicKey` supplied by the embedding application. It does not fetch identity-provider metadata, resolve JWKS, store private signing keys or claim that an external identity provider has been production-validated.

`assert_institution_scope` prevents a verified context from being reused across institution boundaries. `assert_role` provides a small explicit RBAC primitive; application-specific authorization remains institution-owned.

## Evidence encryption

`encrypt_evidence` and `decrypt_evidence` use AES-256-GCM. Additional authenticated data binds ciphertext to:

- `institution_id`;
- artifact type;
- external key provider reference;
- external key identifier and version.

The envelope never claims that production KMS/HSM controls have been validated. `EvidenceKeyReference` accepts references only and rejects obvious embedded secret/private-key material. Raw evidence and key material are not included in `SecurityObservation`.

## PostgreSQL RLS reference

`deployment/postgresql-institution-rls.sql` provides a PostgreSQL reference contract using:

- `ENABLE ROW LEVEL SECURITY`;
- `FORCE ROW LEVEL SECURITY`;
- an application role with `NOBYPASSRLS` and no superuser privileges;
- `USING` and `WITH CHECK` predicates bound to `current_setting('datagovops.institution_id', true)`;
- revoked public table access;
- transaction-local institution context.

Static validation of this file is not production RLS validation. A real deployment must prove role attributes, connection-pool isolation, negative cross-institution CRUD paths and governance of migration/backup/break-glass roles.

## Observability

`SecurityObservation` is deliberately metadata-only and fails closed if raw-content logging, secret logging or production-observability validation is claimed.

## Explicit non-claims

This boundary does not by itself establish production identity-provider validation, production PostgreSQL tenant isolation, production key-management effectiveness, production observability effectiveness, BCBS 239 compliance, GDPR/KVKK compliance, data correctness or supervisory acceptance.
