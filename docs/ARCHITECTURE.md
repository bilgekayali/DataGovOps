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

`LineageEndpointRef` addresses exact governed asset/data-element versions and content digests. `TransformationRecord` binds owner, execution system and code/config/evidence digests. Lineage edges are append-only, reject dangling/cross-institution references and directed cycles, and current-state checks fail closed when asset/transformation versions advance.

Lineage completeness is evaluated only against explicit institution-owned requirements; no requirements does not produce a vacuous success.

## v0.1.4 boundary — data quality and remediation evidence

v0.1.4 adds deterministic quality governance over exact authoritative/semantic targets:

```text
DataAssetRegistry ───────────────┐
                                ├─> QualityRegistry ──> quality snapshot
SemanticGovernanceRegistry ─────┘       |
                                        ├─ QualityRule + EvaluationPolicy
                                        ├─ Observation -> RuleEvaluation
                                        └─ Finding -> Remediation -> Retest -> Resolution
```

### Exact quality targets

`QualityTargetRef` addresses either an exact asset version or an exact registered `CriticalDataElementDesignation`. A CDE rule cannot be attached merely to an arbitrary element name; the designation artifact must exist and its digest must match.

Current-state evaluation fails closed when a newer asset/CDE version supersedes the target.

### Rules and thresholds

`QualityRule` is independently versioned and binds:

- accountable rule owner;
- quality dimension;
- explicit metric name and measurement unit;
- integer threshold and comparison operator;
- maximum observation age;
- finding severity;
- source-evidence digest.

Metric values are intentionally represented as governed integers with an explicit unit. Institutions can use counts, basis points, milliseconds or other documented units without hidden floating-point threshold semantics.

### Observation policy and evaluation

`QualityObservation` binds an immutable observed value to an exact rule digest, target digest and source-system identity.

`QualityEvaluationPolicy` is institution-owned and controls whether missing/stale evidence is treated as `incomplete` or `breached`. Neither treatment may produce PASS. Multiple distinct observations at the same latest measurement timestamp fail closed as `conflicting_latest_observation`.

A rule evaluation is one of:

- `passed` — fresh selected observation satisfies the configured threshold;
- `breached` — threshold failed or institution policy treats missing/stale evidence as breach;
- `incomplete` — evidence is missing, stale under incomplete policy, or conflicting.

`regulatory_compliance_determined` is fixed to `false`.

### Findings, remediation and retest

A passed evaluation cannot create a finding. Finding severity must match the governed rule severity, preventing downstream severity downgrade.

Remediation evidence is immutable and accountable. Retest evidence must bind a post-remediation evaluation for the same rule. HIGH/CRITICAL findings require a reviewer distinct from the remediation owner before a passed retest can close the finding.

`QualityFindingResolution` deterministically represents `open`, `remediation_submitted`, `retest_failed` or `closed` and retains all remediation/retest artifact digests in evidence history.

### Assurance boundary

A quality PASS proves only that represented governance inputs satisfied the represented threshold at the represented time. It does not prove objective accuracy/completeness, fitness for regulatory reporting, BCBS 239 compliance, legal applicability, security or regulator acceptance.

## Planned v0.1 layers

1. v0.1.1 — authoritative inventory/accountability;
2. v0.1.2 — classification, critical data elements and business purpose;
3. v0.1.3 — lineage, transformations and provenance;
4. v0.1.4 — data quality, findings and remediation;
5. v0.1.5 — access-purpose, retention, legal hold and privacy/security obligations;
6. v0.1.6 — deterministic governance dossier, CLI and release gate.

Only completion of the full sequence establishes the proposed v0.1.0 foundation code boundary.
