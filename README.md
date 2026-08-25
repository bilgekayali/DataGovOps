# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, regulatory-reporting governance, and deterministic assurance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, verifiable governance evidence and deterministic release integrity.

Current code/package milestone: **DataGovOps v0.5.0 signed governance evidence and release provenance boundary** (`0.5.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, production KMS/HSM, production tenant-isolation proof, trusted timestamp authority, production build-attestation service, deletion engine, or substitute for accountable data owners, stewards, report owners, security/privacy teams, engineers, legal/regulatory review and supervisory judgement.

A `0.5.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.5.0 signed governance evidence and provenance boundary

v0.5 retains the v0.1-v0.4 governance, assurance and institution-security boundaries and adds an offline evidence-integrity chain:

```text
Verified governance dossier
          |
          v
Canonical institution/dossier/release/source statement
          |
          v
External institution-controlled Ed25519 signature
          |
          v
Public-key-only offline verification
          |
          +----------------------+
          |                      |
          v                      v
External anchor receipt     Build provenance
+ timestamp-token digest         |
          |                      v
          |                 Dependency SBOM
          |                      |
          +----------+-----------+
                     v
          Exact-byte release manifest
```

The v0.5 boundary includes:

- canonical signed-governance statements bound to an already verified governance dossier, institution, release version and source revision;
- external Ed25519 signing with **no private-signing-key API or key material in DataGovOps runtime code**;
- institution/external signing-key references (`provider`, `key_id`, `key_version`) instead of embedded secrets;
- offline verification with a separately supplied trusted Ed25519 public key;
- external immutable-anchor and timestamp receipt contracts bound to the signed-evidence digest;
- structural `external_anchor_validated=false` and `trusted_timestamp_validated=false` until a real external service is independently validated;
- deterministic build provenance bound to package/version/source revision, exact subjects and source materials;
- deterministic CycloneDX-shaped dependency SBOM with explicit non-claims for complete transitive inventory and vulnerability assessment;
- exact-byte release manifests using SHA-256 + size for provenance, SBOM, signed governance evidence, anchor receipts and package artifacts;
- manifest/provenance/SBOM identity cross-checks and tamper-failure paths;
- strict Draft 2020-12 schemas, public-key-only offline guards and clean-wheel release-evidence CI.

The signed evidence layer does not make a governance dossier legally sufficient merely because a signature verifies. Signer authority, key custody, external anchor validity, trusted timestamp validity and production provenance remain external responsibilities.

See [`docs/EVIDENCE_INTEGRITY.md`](docs/EVIDENCE_INTEGRITY.md).

## Retained v0.4 institution security boundary

The v0.4 layer provides:

- offline Ed25519 JWT/OIDC verification against a caller-supplied trusted public key;
- issuer, audience, expiration/not-before, institution-scope, role and MFA checks;
- explicit cross-institution scope and RBAC guards;
- AES-256-GCM evidence protection bound to institution, artifact type and external KMS/HSM key references;
- metadata-only security observations;
- PostgreSQL `FORCE ROW LEVEL SECURITY` + `NOBYPASSRLS` institution-isolation reference;
- structural production-security non-claims.

See [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md).

## Retained v0.3 BCBS 239 assurance boundary

The v0.3 layer provides institution-scoped report taxonomy, risk-data portfolios, deterministic multi-report aggregation over current reporting evidence, fail-closed missing/incomplete evidence, accountable owner attestations and structural non-claims for BCBS 239 compliance, risk-data accuracy and supervisory acceptance.

## Retained v0.2 reporting-governance boundary

The v0.2 layer provides versioned governed reports, exact source/transformation/quality-rule bindings, production observations, deterministic timeliness/completeness/reconciliation controls, accountable report-owner attestations, findings/remediation/retest and offline reporting-domain dossier verification.

## Retained v0.1 foundation

The foundation provides institution-scoped accountability and authoritative systems, immutable data-asset versions, classification/CDE/business-purpose evidence, lineage and transformation provenance, data-quality evidence, access/retention/legal-hold/privacy-security obligations, canonical JSON/SHA-256 binding, deterministic governance dossiers and offline integrity/semantic verification.

Historical/versioned evidence remains preserved without silently becoming current after a governed source, transformation, policy or rule changes.

## Governance dossier states

A dossier state is deterministic from represented evidence:

- `current` — no represented current-state findings;
- `with_gaps` — one or more represented gaps are not covered by an active explicit exception;
- `with_exceptions` — represented gaps exist but are exactly covered by active time-bounded exceptions;
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation.

The BCBS portfolio, institution-security and evidence-integrity layers remain separate reference boundaries rather than new governance-dossier domains in v0.5.

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
- production KMS/HSM signing/encryption key custody, rotation, revocation or access-control effectiveness;
- authority of a signer merely because an Ed25519 signature verifies;
- external immutable-ledger anchoring or trusted timestamp validity;
- complete transitive SBOM coverage or absence of vulnerabilities;
- SLSA certification, production build provenance or formal release attestation;
- production observability effectiveness;
- objective enterprise risk-data accuracy or completeness;
- regulatory-reporting correctness, filing status or supervisory acceptance;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of governance assignments or source-of-truth declarations;
- semantic correctness/completeness of lineage beyond configured requirements;
- deletion execution/completion or legal-hold legal sufficiency;
- regulator acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
