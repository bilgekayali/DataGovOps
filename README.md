# DataGovOps

**Evidence-backed data governance, lineage, classification, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current development milestone: **v0.1.3 — data lineage, transformation and provenance evidence** (`0.1.0.dev3`).

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, or substitute for accountable data owners, stewards, security/privacy teams, engineers, and legal review.

## Current executable boundary

The v0.1.1 authoritative registry and v0.1.2 semantic layer remain intact. v0.1.3 adds deterministic lineage/provenance governance:

- institution-scoped accountable principals, authoritative systems and immutable data-asset versions;
- exact data-element identities and semantic classification/CDE/business-purpose evidence;
- `LineageEndpointRef` for exact asset- or data-element-version targets with digest binding;
- versioned `TransformationRecord` with accountable owner, execution system, code digest, config digest and source-evidence digest;
- `LineageEdge` with exact source/target endpoints, transformation version/digest, producer system, consumer system and evidence digest;
- asset-to-asset, data-element-to-data-element and mixed-granularity lineage;
- directed-cycle rejection at registration time;
- fail-closed dangling, cross-institution, digest-mismatch and stale endpoint/transformation state;
- explicit `LineageCompletenessRequirement` artifacts rather than inferred completeness criteria;
- deterministic `LineageCompletenessReport` with missing/stale requirement sets;
- lineage snapshots bound to both the authoritative asset-registry snapshot and semantic-governance snapshot;
- strict Draft 2020-12 JSON Schemas and Python 3.11/3.12/3.13 CI;
- offline-capability guard, wheel build and clean-wheel smoke.

```text
DataAssetRegistry ───────┐
                        ├─> LineageRegistry
SemanticGovernance ─────┘       |
                                ├─ TransformationRecord
                                ├─ LineageEdge
                                ├─ CompletenessRequirement
                                └─ CompletenessReport
```

Lineage completeness is evaluated only against explicit institution-owned requirements. An empty requirement set is **not** treated as proof that lineage is complete.

## v0.1 foundation sequence

`#3 inventory/accountability ✓ → #4 classification/CDE/purpose ✓ → #5 lineage/provenance → #6 quality/remediation → #7 access/retention/privacy → #8 dossier/release gate`

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
- semantic correctness or completeness of lineage beyond configured explicit requirements;
- correctness of transformation code or configuration merely because digests are bound;
- data quality, completeness, accuracy or fitness for regulatory reporting;
- deletion completion or legal-hold satisfaction;
- access authorization sufficiency;
- regulator acceptance or legal applicability.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
