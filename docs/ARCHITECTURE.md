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

`QualityTargetRef` addresses either an exact asset version or an exact registered `CriticalDataElementDesignation`. Rules bind explicit dimensions, units, thresholds, freshness windows and severity. Missing/stale evidence cannot produce PASS, conflicting latest observations fail closed, and HIGH/CRITICAL findings require independent retest evidence before deterministic closure.

A quality PASS proves only that represented governance inputs satisfied the represented threshold at the represented time. It does not prove objective accuracy/completeness, fitness for regulatory reporting, BCBS 239 compliance, legal applicability, security or regulator acceptance.

## v0.1.5 boundary — access, retention and privacy/security obligations

v0.1.5 adds an explicit control-evidence layer:

```text
DataAssetRegistry ────────────────┐
                                 ├─> AccessRetentionPrivacyRegistry
SemanticGovernanceRegistry ──────┘          |
                                            ├─ Role -> Purpose Approval -> Grant
                                            ├─ Retention -> Hold/Release -> Eligibility
                                            ├─ Location -> Obligation Mapping
                                            └─ Institution Policy -> Gap Report
```

Access grants are exact-purpose and exact-version evidence rather than an IAM enforcement engine. Retention/deletion evaluation separates eligibility from execution. Legal hold blocks represented eligibility while active. Privacy/security/residency/cross-border mappings remain accountable institutional inputs and do not establish lawful basis or regulatory applicability.

## v0.1.0 boundary — deterministic governance dossier and release gate

The final foundation boundary packages the complete represented governed state without flattening historical evidence into current-state assertions:

```text
Inventory snapshot ──────────────┐
Semantic snapshot ───────────────┤
Lineage snapshot ────────────────┤
Quality snapshot ────────────────┼─> GovernanceDossierBuilder
Access/retention/privacy snapshot┤          |
Current-state assurance reports ─┘          v
                                  deterministic dossier document
                                             |
                                             v
                           offline verifier + Draft 2020-12 schema + CLI
```

### Artifact ownership and manifests

Every embedded artifact is canonicalized and SHA-256 bound. Registry-owned artifacts remain in their native domain (`inventory`, `semantic`, `lineage`, `quality`, `access_retention_privacy`). Generated current-state validation/completeness/resolution/gap reports belong to a separate `assurance` domain.

Each domain snapshot contains the exact sorted artifact-digest manifest and a source snapshot digest. The offline verifier reconstructs the authoritative, semantic, lineage, quality, access/retention/privacy and assurance snapshot formulas from embedded artifacts instead of trusting supplied digest strings.

The public release builder is intentionally exposed from `dossier_release.py`; the lower-level base builder is an internal implementation detail. This preserves a fail-closed public boundary when release-specific hardening is required.

### Current-state gate

The dossier distinguishes historical evidence from evidence expected to be current. Current-state checks include:

- latest authoritative asset structural validation;
- current semantic classification/CDE/purpose-binding assertions where applicable;
- explicit lineage completeness requirements;
- latest quality rule/policy evaluation and unresolved finding state;
- institution-owned access/retention/privacy control-gap policy;
- time-active access grants against latest approval/role/asset/purpose state.

The aggregate state is `current`, `with_gaps`, `with_exceptions`, or `revalidation_required`. Time-bounded explicit exceptions may cover represented gaps but never mask revalidation findings.

### Offline tamper model

`dossier verify` checks more than the outer dossier SHA-256. It revalidates:

- every embedded artifact digest;
- artifact type/domain/schema-version contracts;
- institution scope;
- deterministic artifact ordering and uniqueness;
- domain artifact manifests;
- recomputed domain snapshot digests;
- coverage counts;
- exception activity and aggregate dossier-state consistency.

Therefore recomputing only the outer hash after changing an embedded artifact, coverage value, domain snapshot or artifact type is insufficient to pass verification.

### Trust boundary and non-claims

SHA-256 binding establishes deterministic integrity association for the represented bytes. It does **not** establish source authenticity, non-repudiation, trusted time, institution-owned signing authority, external immutable anchoring, legal validity, regulatory acceptance, or proof that runtime controls match the represented evidence.

Those capabilities are later hardening targets together with tenant isolation, cryptographic signing/anchoring, immutable audit/recovery evidence and production deployment controls.

## v0.1 foundation sequence

1. v0.1.1 — authoritative inventory/accountability;
2. v0.1.2 — classification, critical data elements and business purpose;
3. v0.1.3 — lineage, transformations and provenance;
4. v0.1.4 — data quality, findings and remediation;
5. v0.1.5 — access-purpose, retention, legal hold and privacy/security obligations;
6. v0.1.6 — deterministic governance dossier, CLI and release gate.

Completion of the full sequence establishes the proposed **DataGovOps v0.1.0 foundation code/package boundary**. Git tag/GitHub Release publication is a separate action.
