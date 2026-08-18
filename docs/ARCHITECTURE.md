# DataGovOps Architecture

## v0.1.1 boundary — authoritative inventory and accountability

The first executable boundary is an offline, institution-scoped governance registry. It deliberately separates **authoritative references** from later governance decisions and evidence.

```text
GovernancePrincipal ─┐
                     ├─> DataAssetRegistry ──> deterministic snapshot digest
AuthoritativeSystem ─┤            |
                     │            v
DataAssetRecord ─────┘    DataAssetValidator + GovernancePolicy
                                  |
                                  v
                      DataAssetValidationReport
```

Asset versions are immutable, contiguous and exact-reference bound. The registry snapshot covers principal, system and full asset-version history.

## v0.1.2 boundary — semantic classification, CDE and purpose governance

v0.1.2 adds a separate semantic layer rather than mutating the authoritative registry model:

```text
DataAssetRegistry
      |
      v
SemanticGovernanceRegistry
  |          |          |             |
DataElement  Classification  CDE Designation  BusinessPurpose
                                            |
                                            v
                                   AssetPurposeBinding
```

### Data elements

`DataElementRecord` identifies a governed element underneath an exact `institution_id + asset_id + asset_version`. The element owner must resolve to an accountable principal in the same institution. This creates an exact target for later lineage and data-quality rules instead of forcing those controls to operate only at whole-asset granularity.

### Classification decisions

`ClassificationDecision` is explicit evidence for either an asset or data element. Asset-scoped decisions must agree with the classification already recorded on the authoritative asset version; semantic evidence cannot silently rewrite the authoritative inventory. Element-scoped decisions bind to the exact element digest.

Historical classification decisions remain immutable. `assert_classification_current` fails closed when a newer asset version supersedes the decision target.

### Critical data elements

`CriticalDataElementDesignation` binds a CDE owner, accountable decision owner, rationale and source-evidence digest to an exact governed data-element digest. The designation does not infer criticality from names, schemas or content.

A newer asset version makes the historical CDE designation non-current until corresponding semantic evidence is established for the new version.

### Business purposes

`BusinessPurpose` is independently versioned and owned. `AssetPurposeBinding` explicitly binds an exact asset version to an exact purpose version with approval owner, rationale and evidence digest.

A newer asset version or purpose version makes the prior binding stale. Business-purpose evidence is not a GDPR/KVKK lawful-basis determination and does not by itself establish processing permissibility.

### Semantic snapshot

`SemanticGovernanceRegistry.snapshot_digest` binds the exact underlying `DataAssetRegistry.snapshot_digest` plus data-element, classification, CDE, purpose and purpose-binding artifact digests. The semantic layer therefore cannot be represented as current independently of the authoritative registry evidence it references.

## Planned v0.1 layers

1. v0.1.1 — authoritative inventory/accountability;
2. v0.1.2 — classification, critical data elements and business purpose;
3. v0.1.3 — lineage, transformations and provenance;
4. v0.1.4 — data quality, findings and remediation;
5. v0.1.5 — access-purpose, retention, legal hold and privacy/security obligations;
6. v0.1.6 — deterministic governance dossier, CLI and release gate.

Only completion of the full sequence establishes the proposed v0.1.0 foundation code boundary.
