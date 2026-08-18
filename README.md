# DataGovOps

**Evidence-backed data governance, lineage, quality, access, retention, privacy/security obligations, and deterministic governance evidence for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current code/package milestone: **DataGovOps v0.1.0 foundation release boundary** (`0.1.0`).

This repository is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, deletion engine, or substitute for accountable data owners, stewards, security/privacy teams, engineers, and legal review.

A `0.1.0` package version in the codebase does **not** by itself mean that a Git tag or GitHub Release has been published. Publication must be verified separately.

## v0.1.0 executable boundary

The foundation now connects six deterministic governance layers:

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
Deterministic governance dossier + offline verifier + CLI
```

The implemented boundary includes:

- institution-scoped accountable principals and authoritative systems;
- immutable, contiguous data-asset version history;
- exact classification, CDE and business-purpose evidence;
- asset- and data-element-level lineage with transformation provenance and explicit completeness requirements;
- deterministic quality rules, observations, findings, remediation, independent high-impact retest, and closure evidence;
- explicit access-purpose approvals and grants, retention schedules, legal holds/releases, deletion eligibility, location evidence, and privacy/security obligation mappings;
- canonical JSON and SHA-256 artifact binding throughout the governed state;
- a deterministic governance dossier that embeds exact domain artifacts and domain snapshot manifests;
- current-state gate findings for gaps, stale/revalidation-required evidence, and time-bounded explicit exceptions;
- offline dossier verification that recomputes embedded artifact digests, coverage, domain manifests, domain snapshot digests, artifact type/domain/schema contracts, exception state, and aggregate dossier state;
- strict Draft 2020-12 JSON Schemas;
- Python 3.11/3.12/3.13 CI, wheel build, clean-wheel import/CLI smoke, and an offline-capability guard.

Historical/versioned evidence remains part of the dossier without automatically becoming an error merely because a newer version exists. Current-state assertions fail closed only where represented evidence is expected to remain current.

## Governance dossier states

A dossier state is deterministic from represented evidence:

- `current` — no represented current-state findings;
- `with_gaps` — one or more represented gaps are not covered by an active explicit exception;
- `with_exceptions` — represented gaps exist but are exactly covered by active time-bounded exceptions;
- `revalidation_required` — stale or otherwise non-current represented evidence requires revalidation. Exceptions do not mask revalidation findings.

A complete/current dossier is internal governance evidence only. It is not a legal opinion, supervisory filing, certification, deletion receipt, proof of objective data quality, or proof that implemented IAM/runtime controls enforce the represented state.

## CLI

The installed wheel exposes the `datagovops` command:

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

`digest` computes the canonical-JSON SHA-256. `schema` validates a document with a Draft 2020-12 JSON Schema. `dossier verify` performs offline integrity and semantic cross-binding checks and exits non-zero on failure.

## v0.1 foundation sequence

`#3 inventory/accountability ✓ → #4 classification/CDE/purpose ✓ → #5 lineage/provenance ✓ → #6 quality/remediation ✓ → #7 access/retention/privacy ✓ → #8 dossier/CLI/release gate`

Completion of #3 through #8 constitutes the proposed **DataGovOps v0.1.0 foundation code/package boundary**.

## Standards posture

Design mappings are intended to support evidence/control alignment with:

- BCBS 239 risk-data aggregation and reporting governance principles;
- Basel Committee implementation observations on BCBS 239;
- GDPR and KVKK privacy/accountability concepts;
- ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts;
- DAMA-aligned governance concepts;
- relevant BDDK, SPK and institution-owned data-governance requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer data ownership, establish regulatory applicability, or prove that data is accurate simply because metadata or governance evidence is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE assignments;
- correctness of source-of-truth or authoritative-system declarations;
- semantic correctness or completeness of lineage beyond configured explicit requirements;
- correctness, security, or fitness of transformation code/configuration merely because digests are bound;
- objective data accuracy, completeness, consistency, timeliness, uniqueness, or fitness for regulatory reporting;
- sufficiency or runtime enforcement of an access authorization;
- deletion execution, deletion completion, or legal-hold legal sufficiency;
- legal/regulatory applicability of privacy/security obligation mappings;
- authenticity/non-repudiation of source evidence merely from SHA-256 integrity binding;
- regulator acceptance, supervisory filing acceptance, certification, or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
