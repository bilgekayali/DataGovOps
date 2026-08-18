# DataGovOps Architecture

## v0.1.1 boundary — authoritative inventory and accountability

The first executable boundary is an offline, institution-scoped governance registry. It deliberately separates authoritative references from later governance decisions and evidence.

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

`DataElementRecord` creates exact element-level targets. Classification, CDE designation and business purpose are explicit accountable inputs, not metadata inference. Historical evidence is preserved and later asset/purpose versions make prior current-state evidence stale.

## v0.1.3 boundary — lineage, transformation and provenance

v0.1.3 adds an append-only provenance graph over the authoritative and semantic foundations:

```text
DataAssetRegistry ───────────────┐
                                ├─> LineageRegistry ──> lineage snapshot
SemanticGovernanceRegistry ─────┘       |       |
                                        |       └─ CompletenessRequirement/Report
                                        └─ TransformationRecord + LineageEdge
```

### Exact endpoints

`LineageEndpointRef` addresses an exact governed asset or data element by institution, asset identity, asset version, optional element identity and target digest. Endpoint resolution fails closed on dangling references or digest mismatch.

Current-state verification also requires the referenced asset version to remain the latest registered version. Historical lineage is retained, but it is not silently represented as current after a new asset version is introduced.

### Transformations

`TransformationRecord` is independently versioned and binds:

- accountable owner;
- execution-system identity;
- code digest;
- configuration digest;
- source-evidence digest.

Transformation versions are contiguous and immutable. A later transformation version makes edges bound to the earlier version non-current for current-state checks.

A bound digest proves integrity association only. It does not prove that the code/configuration is semantically correct, secure, or regulator-approved.

### Lineage edges

Each `LineageEdge` binds an exact source endpoint, exact target endpoint, relationship type, transformation version/digest, producer system, consumer system and evidence digest.

The graph supports asset-level, data-element-level and mixed-granularity edges. Source/target/system/transformation references must resolve in the same institution. Directed cycles are rejected when an edge is registered.

Cycle rejection is a governance invariant for this reference graph; it is not a claim that every real-world processing topology must be acyclic outside the represented governed lineage scope.

### Completeness requirements

DataGovOps does not infer that every asset or CDE automatically requires upstream lineage. An accountable principal records a `LineageCompletenessRequirement` for each target where explicit upstream lineage is required.

`LineageCompletenessReport` evaluates only those configured requirements and returns deterministic missing/stale requirement identifiers. Evaluation without any explicit requirement fails closed rather than reporting a vacuous success.

### Snapshot binding

`LineageRegistry.snapshot_digest` binds:

- the exact `DataAssetRegistry` snapshot;
- the exact `SemanticGovernanceRegistry` snapshot;
- all transformation versions;
- all lineage edges;
- all lineage completeness requirements.

A lineage completeness report binds to that exact lineage snapshot and becomes stale when any of those governed inputs change.

## Planned v0.1 layers

1. v0.1.1 — authoritative inventory/accountability;
2. v0.1.2 — classification, critical data elements and business purpose;
3. v0.1.3 — lineage, transformations and provenance;
4. v0.1.4 — data quality, findings and remediation;
5. v0.1.5 — access-purpose, retention, legal hold and privacy/security obligations;
6. v0.1.6 — deterministic governance dossier, CLI and release gate.

Only completion of the full sequence establishes the proposed v0.1.0 foundation code boundary.
