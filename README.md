# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, regulatory-reporting governance, and deterministic assurance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, and verifiable evidence.

Current code/package milestone: **DataGovOps v0.4.0 institution security boundary** (`0.4.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, production KMS/HSM, production tenant-isolation proof, deletion engine, or substitute for accountable data owners, stewards, report owners, security/privacy teams, engineers, and legal/regulatory review.

A `0.4.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.4.0 institution security boundary

v0.4 retains the v0.1-v0.3 governance and assurance boundaries and adds an explicit institution-scoped security reference:

```text
Trusted external Ed25519 public key
             |
             v
OIDC/JWT signature + issuer/audience/time verification
             |
             v
Institution claim + roles + MFA
             |
             v
Immutable InstitutionContext
      |                    |
      v                    v
scope/RBAC guards     AES-256-GCM evidence envelope
                           |
                           v
                 external KMS key reference

PostgreSQL reference: FORCE RLS + NOBYPASSRLS + transaction-local institution scope
Observability reference: metadata only, no raw evidence or secrets
```

The v0.4 boundary includes:

- offline Ed25519 JWT/OIDC verification against a caller-supplied trusted public key;
- fail-closed issuer, audience, expiration/not-before, institution scope, role and MFA checks;
- explicit cross-institution scope guard and role guard;
- AES-256-GCM evidence encryption with AAD binding to institution, artifact type and external key reference;
- external KMS/HSM key-reference semantics that reject obvious embedded secret/private-key material;
- metadata-only security observations with structural non-claims for production observability;
- PostgreSQL RLS reference using `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, `NOBYPASSRLS`, `USING`, `WITH CHECK`, revoked PUBLIC access and transaction-local institution context;
- strict Draft 2020-12 security schema, adversarial cryptographic/scope tests, offline capability guard and clean-wheel security smoke.

Passing these reference checks does not prove that a production identity provider, database, key manager, connection pool or observability stack has been configured or validated correctly. See [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md).

## Retained v0.3 BCBS 239 assurance boundary

The v0.3 layer provides:

- institution-scoped immutable report taxonomy;
- current report bindings to risk-data domains and aggregation levels;
- versioned risk-data portfolios bound to exact report/taxonomy digests;
- deterministic multi-report aggregation over strict v0.2 report-assurance evidence;
- fail-closed missing/incomplete report evidence and owner attestations;
- portfolio-owner executive attestation;
- structural non-claims for BCBS 239 compliance, risk-data accuracy and supervisory acceptance.

## Retained v0.2 reporting-governance boundary

The v0.2 layer provides:

- versioned governed reports, explicit accountable owners and institution-owned thresholds;
- exact metrics bound to governed source asset/version, transformation and quality-rule evidence;
- production observations bound to current inventory, semantic, lineage and quality snapshots;
- deterministic timeliness, completeness and reconciliation controls;
- accountable report-owner attestations, findings, remediation and reassessment-bound independent retest evidence;
- reporting-domain governance-dossier evidence and offline semantic verification.

## Retained v0.1 foundation

The foundation provides:

- institution-scoped accountable principals and authoritative systems;
- immutable contiguous data-asset version history;
- classification, critical-data-element and business-purpose evidence;
- asset/data-element lineage and transformation provenance;
- data-quality rules, observations, findings, remediation and independent high-impact retest;
- access approvals/grants, retention, legal hold, deletion eligibility, location and privacy/security obligation mappings;
- canonical JSON and SHA-256 artifact binding;
- deterministic governance dossier state for gaps, exceptions and revalidation-required evidence;
- offline integrity/semantic verification and CLI tooling.

Historical/versioned evidence remains preserved without silently becoming current after a governed source, transformation, policy or rule changes.

## Governance dossier states

A dossier state is deterministic from represented evidence:

- `current` — no represented current-state findings;
- `with_gaps` — one or more represented gaps are not covered by an active explicit exception;
- `with_exceptions` — represented gaps exist but are exactly covered by active time-bounded exceptions;
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation.

The v0.3 BCBS portfolio and v0.4 security boundary remain separate assurance/security reference layers rather than new dossier domains at this milestone.

## CLI

The installed wheel exposes:

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

## Standards posture

Design mappings are intended to support evidence/control alignment with BCBS 239, Basel Committee implementation observations, GDPR/KVKK accountability concepts, ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts, DAMA-aligned governance concepts, and relevant institution-owned BDDK/SPK data-governance requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, or prove data/report correctness because governance metadata or evidence is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- production identity-provider/JWKS configuration or validation;
- production PostgreSQL institution isolation or connection-pool isolation;
- production KMS/HSM key custody, rotation, revocation or access-control effectiveness;
- production observability effectiveness;
- objective enterprise risk-data accuracy or completeness;
- regulatory-reporting correctness, filing status or supervisory acceptance;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of governance assignments or source-of-truth declarations;
- semantic correctness/completeness of lineage beyond configured requirements;
- correctness or security of transformation code/configuration merely because digests are bound;
- deletion execution/completion or legal-hold legal sufficiency;
- authenticity/non-repudiation of source evidence merely from SHA-256 integrity binding;
- regulator acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
