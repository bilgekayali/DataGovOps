# DataGovOps

**Evidence-backed data governance, lineage, classification, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current development milestone: **v0.1.2 — classification, critical data element and business-purpose evidence** (`0.1.0.dev2`).

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, or substitute for accountable data owners, stewards, security/privacy teams, and legal review.

## Current executable boundary

The v0.1.1 foundation remains intact and v0.1.2 adds a semantic governance layer bound to exact governed versions:

- institution-scoped accountable principals and authoritative systems;
- immutable, contiguous data-asset version history;
- exact owner/steward/system-of-record references and deterministic asset-registry snapshots;
- governed `DataElementRecord` identity under an exact asset version;
- explicit asset- or data-element-scoped `ClassificationDecision` artifacts;
- asset-level classification decisions that must agree with the registered asset classification instead of silently overriding it;
- explicit `CriticalDataElementDesignation` evidence bound to an exact data-element digest;
- versioned `BusinessPurpose` artifacts with accountable owner;
- explicit `AssetPurposeBinding` approval evidence bound to exact asset and purpose versions;
- current-state checks that fail closed when a newer asset or purpose version makes historical semantic evidence stale;
- deterministic semantic snapshot digest over the exact underlying asset-registry snapshot and semantic artifacts;
- strict runtime enum/boolean/integer/digest contracts;
- strict Draft 2020-12 JSON Schemas for data element, classification, CDE, business purpose and purpose binding artifacts;
- Python 3.11/3.12/3.13 CI, schema validation, offline-capability guard, wheel build and clean-wheel smoke.

```text
DataAssetRegistry (exact asset versions)
             |
             v
SemanticGovernanceRegistry
   |        |        |        |
 elements  class.   CDEs   purposes/bindings
             |
             v
 exact semantic governance snapshot
```

Business-purpose metadata is an accountable institutional-purpose record. It is deliberately **not** treated as GDPR/KVKK lawful-basis evidence or an automatic legal-permissibility conclusion.

## v0.1 foundation sequence

`#3 inventory/accountability ✓ → #4 classification/CDE/purpose → #5 lineage/provenance → #6 quality/remediation → #7 access/retention/privacy → #8 dossier/release gate`

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
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE assignments;
- correctness of source-of-truth or authoritative-system declarations;
- data quality, completeness, accuracy or fitness for regulatory reporting;
- deletion completion or legal-hold satisfaction;
- access authorization sufficiency;
- complete lineage or provenance before the relevant later tranche is implemented.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
