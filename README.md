# DataGovOps

**Evidence-backed data governance, lineage, classification, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current development milestone: **v0.1.1 — authoritative data asset inventory and accountability contracts** (`0.1.0.dev1`).

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, or substitute for accountable data owners, stewards, security/privacy teams, and legal review.

## Current executable boundary

The first v0.1 tranche establishes the evidence substrate that later governance layers depend on:

- institution-scoped accountable-principal registry;
- institution-scoped source/system registry with explicit authoritative-state metadata;
- immutable, contiguous data-asset version history;
- exact owner, steward, quality-owner, classification-decision-owner, criticality-decision-owner and system-of-record references;
- explicit sensitivity classification and business criticality decisions with accountable owner and rationale;
- explicit personal-data and source-of-truth indicators without content inspection or inference;
- institution-owned structural completeness policy;
- deterministic canonical JSON and SHA-256 artifact/snapshot evidence;
- validation reports bound to the exact registry snapshot so later registry change makes prior evidence stale;
- strict Draft 2020-12 JSON Schemas;
- Python 3.11/3.12/3.13 CI, schema validation, offline-capability guard, wheel build and clean-wheel smoke.

```text
GovernancePrincipal ─┐
AuthoritativeSystem ─┼─> DataAssetRegistry ─> exact registry snapshot
DataAssetRecord ─────┘            |
                                  v
                         DataAssetValidator
                                  |
                                  v
                      DataAssetValidationReport
```

A structurally complete report means only that the configured institution-owned metadata controls are represented for that exact governed state. It is not a legal or regulatory compliance conclusion.

## v0.1 foundation sequence

`#3 inventory/accountability → #4 classification/CDE/purpose → #5 lineage/provenance → #6 quality/remediation → #7 access/retention/privacy → #8 dossier/release gate`

The package remains a development build until #8. Completion of #3 through #8 is the proposed **DataGovOps v0.1.0 foundation release**.

## Standards posture

Design mappings are intended to support evidence/control alignment with:

- BCBS 239 risk-data aggregation and reporting governance principles;
- Basel Committee implementation observations on BCBS 239;
- GDPR and KVKK privacy/accountability concepts;
- ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts;
- DAMA-aligned governance concepts;
- relevant BDDK, SPK and institution-owned data-governance requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer data ownership, establish regulatory applicability, or prove that data is accurate simply because metadata is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- lawful basis or permitted processing purpose;
- correctness of owner/steward assignments;
- correctness of source-of-truth or authoritative-system declarations;
- data quality, completeness, accuracy or fitness for regulatory reporting;
- deletion completion or legal-hold satisfaction;
- access authorization sufficiency;
- complete lineage or provenance before the relevant later tranche is implemented.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
