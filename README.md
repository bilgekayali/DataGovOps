# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, regulatory-reporting governance, and deterministic assurance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, and verifiable evidence.

Current code/package milestone: **DataGovOps v0.3.0 BCBS 239 multi-report assurance boundary** (`0.3.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, deletion engine, or substitute for accountable data owners, stewards, report owners, security/privacy teams, engineers, and legal/regulatory review.

A `0.3.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.3.0 BCBS 239 assurance boundary

v0.3 retains the full v0.2 reporting-governance boundary and adds a deterministic multi-report assurance layer:

```text
Current governed reports
        |
        v
Exact report taxonomy / risk domain / aggregation level
        |
        v
Versioned risk-data portfolio
        |
        v
Current per-report assurance assessments
        |
        v
Latest accountable report-owner attestations
        |
        v
Deterministic portfolio aggregation assessment
        |
        v
Accountable portfolio-owner executive attestation
```

The v0.3 boundary includes:

- institution-scoped, immutable and contiguous report-taxonomy history;
- exact binding of a current governed report to an institution-owned risk domain and aggregation level;
- versioned risk-data portfolios bound to exact report and taxonomy digests;
- required risk-domain coverage checks without inferring regulatory applicability;
- deterministic multi-report aggregation over the existing strict v0.2 report-assurance evidence;
- fail-closed `incomplete` state for missing report assessments, incomplete report assessments, or missing accountable report-owner attestations;
- deterministic `breached` state for breached report controls or rejected/escalated owner attestations;
- `met` only when every represented report assessment is met and each required report has an approved accountable-owner attestation;
- exact report-assessment and report-attestation digest manifests plus deterministic evidence counts and gap codes;
- portfolio-owner executive attestation that cannot approve a non-`met` aggregation assessment;
- strict Draft 2020-12 schemas, offline-capability guards, adversarial currentness tests and clean-wheel validation.

`bcbs239_compliance_determined`, `risk_data_accuracy_determined` and `supervisory_acceptance_determined` remain structurally false. A `met` portfolio assessment means only that the represented current DataGovOps evidence satisfies the configured deterministic assurance contract.

See [`docs/BCBS239_ASSURANCE.md`](docs/BCBS239_ASSURANCE.md).

## Retained v0.2 reporting-governance boundary

The retained v0.2 layer provides:

- versioned governed reports with explicit accountable owner, report family, purpose, frequency and institution-owned thresholds;
- exact report metrics bound to governed source asset/version digests and explicit transformation/quality-rule evidence;
- currentness checks for source assets and latest referenced transformation/quality-rule versions;
- production observations bound to exact inventory, semantic, lineage and quality reporting-basis snapshots;
- deterministic timeliness, completeness and reconciliation controls using integer units/basis points;
- deterministic `met`, `breached` and `incomplete` report-assurance states;
- fail-closed missing evidence and conflicting-latest observations;
- accountable report-owner attestation with `approved`, `rejected` and `escalated` decisions;
- reporting findings, remediation and reassessment-bound independent HIGH/CRITICAL retest evidence;
- reporting-domain governance dossier snapshot and offline recomputation of reporting semantics.

A `met` report assessment does not establish report correctness, real-world data accuracy, regulatory fitness or compliance.

## Retained v0.1 foundation

The foundation continues to provide:

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
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation.

The v0.3 BCBS 239 portfolio layer is currently a separate assurance boundary over the strict reporting registry; it is not represented as a new dossier domain in this milestone. A complete/current dossier or `met` BCBS portfolio assessment remains internal governance evidence only.

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
- BCBS 239 legal applicability or supervisory acceptance;
- objective enterprise risk-data accuracy or completeness;
- regulatory-reporting correctness, completeness, filing status or supervisory acceptance;
- financial-statement accuracy or legal/regulatory applicability of a report;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE/report-family or risk-domain assignments;
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
