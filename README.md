# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, regulatory-reporting governance, and deterministic assurance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, and verifiable evidence.

Current code/package milestone: **DataGovOps v0.2.0 reporting-governance and assurance-evidence boundary** (`0.2.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, deletion engine, or substitute for accountable data owners, stewards, report owners, security/privacy teams, engineers, and legal/regulatory review.

A `0.2.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.2.0 executable boundary

The v0.1 foundation remains intact and v0.2 adds an explicit reporting-governance layer:

```text
Authoritative inventory/accountability
              |
              v
Classification / CDE / business purpose
              |
              v
Lineage / transformation / provenance
              |
              v
Data quality / findings / remediation
              |
              v
Access / retention / legal hold / obligations
              |
              v
Report registry / source + transformation + metric evidence
              |
              v
Production observation / reporting-control assessment
              |
              v
Accountable-owner attestation / finding / remediation / retest
              |
              v
Deterministic governance dossier + offline verifier + CLI
```

The v0.2 reporting boundary includes:

- versioned governed reports with explicit accountable owner, report family, purpose, frequency and institution-owned thresholds;
- exact report metrics bound to governed source asset/version digests and optional explicit transformation and quality-rule evidence;
- currentness checks for source assets and the latest referenced transformation/quality-rule versions;
- production observations bound to an exact reporting-basis digest that includes current inventory, semantic, lineage and quality snapshots;
- deterministic timeliness, completeness and reconciliation controls using integer seconds, counts and basis points rather than floating-point comparisons;
- deterministic `met`, `breached` and `incomplete` reporting-assurance states;
- fail-closed missing evidence and conflicting latest observations;
- accountable report-owner attestation with explicit `approved`, `rejected` and `escalated` decisions;
- HIGH/CRITICAL reporting findings requiring an independent remediation retest before closure;
- a reporting domain snapshot embedded in the governance dossier;
- reporting breach/incomplete, missing/rejected/escalated attestation, stale evidence and unresolved finding state propagated into dossier findings;
- offline verification of report → metric → source/transformation/quality-rule, observation → basis and assessment/lifecycle cross-bindings;
- offline recomputation of timeliness/completeness/reconciliation assessment semantics so rehashed forged `met` evidence fails closed;
- strict Draft 2020-12 schemas, Python 3.11/3.12/3.13 CI, wheel/clean-wheel smoke and offline-capability guards.

A `met` report assessment means only that the supplied current evidence satisfies the configured institution-owned reporting controls for the represented period. It does not establish report correctness, real-world data accuracy, regulatory fitness or compliance.

## v0.1.0 foundation retained

The underlying foundation continues to provide:

- institution-scoped accountable principals and authoritative systems;
- immutable contiguous data-asset version history;
- exact classification, CDE and business-purpose evidence;
- asset- and data-element-level lineage with transformation provenance and explicit completeness requirements;
- deterministic quality rules, observations, findings, remediation, independent high-impact retest and closure evidence;
- explicit access-purpose approvals and grants, retention schedules, legal holds/releases, deletion eligibility, location evidence and privacy/security obligation mappings;
- canonical JSON and SHA-256 artifact binding;
- deterministic governance dossier state for gaps, exceptions and revalidation-required evidence;
- offline integrity/semantic verification and CLI tooling.

Historical/versioned evidence remains preserved without silently becoming current after a governed source, transformation, policy or rule changes.

## Governance dossier states

A dossier state is deterministic from represented evidence:

- `current` — no represented current-state findings;
- `with_gaps` — one or more represented gaps are not covered by an active explicit exception;
- `with_exceptions` — represented gaps exist but are exactly covered by active time-bounded exceptions;
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation. Exceptions do not mask revalidation findings.

A complete/current dossier is internal governance evidence only. It is not a legal opinion, supervisory filing, certification, deletion receipt, proof of objective data quality, proof of reporting correctness, or proof that implemented runtime controls enforce the represented state.

## CLI

The installed wheel exposes:

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

`digest` computes canonical-JSON SHA-256. `schema` validates Draft 2020-12 JSON Schema. `dossier verify` performs offline integrity and semantic cross-binding checks and exits non-zero on failure.

## Standards posture

Design mappings are intended to support evidence/control alignment with:

- BCBS 239 risk-data aggregation and reporting governance principles;
- Basel Committee implementation observations on BCBS 239;
- GDPR and KVKK privacy/accountability concepts;
- ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts;
- DAMA-aligned governance concepts;
- relevant BDDK, SPK and institution-owned data-governance/reporting requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, or prove data/report correctness because governance metadata or evidence is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- regulatory-reporting correctness, completeness, filing status or supervisory acceptance;
- financial-statement accuracy or legal/regulatory applicability of a report;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE/report-family assignments;
- correctness of source-of-truth or authoritative-system declarations;
- semantic correctness or completeness of lineage beyond configured explicit requirements;
- correctness, security or fitness of transformation code/configuration merely because digests are bound;
- objective data accuracy, completeness, consistency, timeliness, uniqueness or fitness for regulatory reporting;
- sufficiency or runtime enforcement of an access authorization;
- deletion execution, deletion completion or legal-hold legal sufficiency;
- legal/regulatory applicability of privacy/security obligation mappings;
- authenticity/non-repudiation of source evidence merely from SHA-256 integrity binding;
- regulator acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
