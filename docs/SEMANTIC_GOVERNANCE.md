# Semantic Governance Invariants

DataGovOps v0.1.2 keeps semantic decisions separate from authoritative asset registration.

## Exact binding

- data elements bind to an exact institution, asset and asset version;
- classification decisions bind to an exact asset or data-element digest;
- CDE designations bind to an exact data-element digest;
- purpose bindings bind to exact asset and purpose versions/digests.

## Human/accountable inputs

Classification, CDE designation and business purpose are explicit accountable inputs. They are not inferred from names, schemas, content, model output or regulatory mappings.

## History and staleness

Artifacts are immutable under their governed identity. New asset or purpose versions preserve old evidence but make earlier current-state classification/CDE/purpose bindings stale until corresponding evidence exists for the new version.

## Legal and assurance boundary

Business-purpose metadata is not lawful-basis evidence. Classification and CDE metadata do not establish privacy compliance, BCBS 239 compliance, data quality, legal applicability, processing permissibility or regulator acceptance.
