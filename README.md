# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, regulatory-reporting governance, and deterministic assurance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, verifiable governance evidence, release integrity, and operational audit/recovery evidence.

Current code/package milestone: **DataGovOps v0.6.0 immutable audit and recovery evidence boundary** (`0.6.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, production KMS/HSM, production tenant-isolation proof, trusted timestamp authority, production build-attestation service, WORM/audit-log platform, backup product, disaster-recovery controller, deletion engine, or substitute for accountable data owners, stewards, report owners, security/privacy teams, resilience teams, engineers, legal/regulatory review and supervisory judgement.

A `0.6.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.6.0 immutable audit and recovery evidence boundary

v0.6 retains the v0.1-v0.5 governance, assurance, security and evidence-integrity boundaries and adds an offline operational-evidence chain:

```text
Governed / signed evidence digest
              |
              v
Metadata-only AuditEvent #1
              |
      previous-event digest
              v
Metadata-only AuditEvent #2 ... N
              |
              v
Audit-chain checkpoint

Historical governed state digest
              |
              v
Institution recovery policy
     |        |        |
     v        v        v
    RPO      RTO    retention
              |
              v
Backup evidence -- exact backup bytes
              |
              v
Restore verification
              |
              v
Historical-state verification
              |
              v
met / breached / incomplete assessment
```

The v0.6 boundary includes:

- institution-scoped append-only audit events with contiguous sequence numbers, predecessor digests and monotonic timestamps;
- metadata-only audit observations with structural `raw_content_logged=false` and `secret_material_logged=false`;
- deterministic audit-chain verification that fails closed on sequence gaps, predecessor tamper, time reversal or cross-institution evidence;
- audit-chain checkpoints bound to exact event count/head digest while keeping `external_immutability_verified=false`;
- institution-owned recovery policy evidence for maximum RPO, maximum RTO, maximum backup age and minimum retention;
- backup evidence bound to exact policy digest, historical source-state digest, represented times, storage reference, SHA-256 and byte size;
- exact-byte backup verification and deterministic retention-expiry binding;
- restore verification bound to exact backup evidence and expected/recovered historical-state digests;
- historical-state verification that deterministically records digest match or breach;
- deterministic recovery assessment over backup freshness, represented RPO, retention schedule, restore integrity and represented RTO;
- fail-closed precedence: `breached` before `incomplete`, with `met` only when every represented control is complete and within policy;
- seven strict Draft 2020-12 schemas, adversarial tests, offline capability enforcement and clean-wheel CI.

Passing these checks does not prove production WORM immutability, backup durability, successful disaster recovery, or objective production RPO/RTO achievement. See [`docs/AUDIT_RECOVERY_BOUNDARY.md`](docs/AUDIT_RECOVERY_BOUNDARY.md).

## Retained v0.5 signed governance evidence and provenance boundary

The v0.5 layer provides canonical governance-evidence statements bound to verified dossiers, external Ed25519 signature verification without runtime private signing keys, external signing-key references, immutable-anchor/timestamp receipt contracts, build provenance, CycloneDX-shaped dependency SBOMs and exact-byte release manifests. External anchor/TSA validity, signer authority, production key custody, complete SBOM coverage and production provenance remain explicit non-claims.

See [`docs/EVIDENCE_INTEGRITY.md`](docs/EVIDENCE_INTEGRITY.md).

## Retained v0.4 institution security boundary

The v0.4 layer provides offline Ed25519 JWT/OIDC verification, issuer/audience/time/institution/role/MFA checks, cross-institution/RBAC guards, AES-256-GCM evidence protection with external key references, metadata-only security observations and a PostgreSQL `FORCE ROW LEVEL SECURITY` + `NOBYPASSRLS` reference.

See [`docs/SECURITY_BOUNDARY.md`](docs/SECURITY_BOUNDARY.md).

## Retained v0.3 BCBS 239 assurance boundary

The v0.3 layer provides institution-scoped report taxonomy, risk-data portfolios, deterministic multi-report aggregation over current reporting evidence, fail-closed missing/incomplete evidence, accountable owner attestations and structural non-claims for BCBS 239 compliance, risk-data accuracy and supervisory acceptance.

## Retained v0.2 reporting-governance boundary

The v0.2 layer provides versioned governed reports, exact source/transformation/quality-rule bindings, production observations, deterministic timeliness/completeness/reconciliation controls, accountable report-owner attestations, findings/remediation/retest and offline reporting-domain dossier verification.

## Retained v0.1 foundation

The foundation provides institution-scoped accountability and authoritative systems, immutable data-asset versions, classification/CDE/business-purpose evidence, lineage and transformation provenance, data-quality evidence, access/retention/legal-hold/privacy-security obligations, canonical JSON/SHA-256 binding, deterministic governance dossiers and offline integrity/semantic verification.

Historical/versioned evidence remains preserved without silently becoming current after a governed source, transformation, policy or rule changes.

## Governance dossier states

A dossier state remains deterministic from represented governance evidence:

- `current` — no represented current-state findings;
- `with_gaps` — one or more represented gaps are not covered by an active explicit exception;
- `with_exceptions` — represented gaps exist but are exactly covered by active time-bounded exceptions;
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation.

The BCBS portfolio, institution-security, evidence-integrity and audit/recovery layers remain separate reference boundaries rather than new governance-dossier domains in v0.6.

## CLI

The installed wheel exposes:

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

## Standards posture

Design mappings are intended to support evidence/control alignment with BCBS 239, Basel Committee implementation observations, GDPR/KVKK accountability concepts, ISO/IEC 27001, ISO/IEC 27701 and ISO 22301 control/evidence concepts, DAMA-aligned governance concepts, and relevant institution-owned BDDK/SPK requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, prove data/report correctness, or establish production resilience merely because evidence is represented.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001, ISO/IEC 27701 or ISO 22301 compliance;
- production identity-provider/JWKS configuration or validation;
- production PostgreSQL institution isolation or connection-pool isolation;
- production KMS/HSM signing/encryption key custody, rotation, revocation or access-control effectiveness;
- authority of a signer merely because an Ed25519 signature verifies;
- external immutable-ledger anchoring or trusted timestamp validity;
- complete transitive SBOM coverage or absence of vulnerabilities;
- SLSA certification, production build provenance or formal release attestation;
- production audit-log immutability or WORM enforcement;
- production backup completion, durability, encryption effectiveness or restore success;
- objective RPO/RTO achievement beyond represented evidence;
- production observability effectiveness;
- objective enterprise risk-data accuracy or completeness;
- regulatory-reporting correctness, filing status or supervisory acceptance;
- lawful basis or legal permissibility of a represented business purpose;
- deletion execution/completion or legal-hold legal sufficiency;
- regulator acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
