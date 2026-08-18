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

### Authoritative references

`GovernancePrincipal` records a governed principal identity. It does not grant permissions or prove that the principal is the legally correct owner.

`AuthoritativeSystem` records a governed system identity and an explicit institution-provided `authoritative` state. DataGovOps does not infer that state from technology names or data contents.

`DataAssetRecord` is versioned. Owner, steward, optional quality owner, classification/criticality decision owners and system-of-record references must resolve exactly in the same institution before the version can be registered.

### Immutability and versioning

Asset versions are contiguous positive integers. Re-registering the exact same version/content is idempotent; different content under an existing identity/version fails closed. New versions preserve prior evidence rather than overwriting it.

The institution registry snapshot is a deterministic SHA-256 digest over the registered principal, system and full asset-version history. Validation reports bind to that exact snapshot and become stale if the governed registry later changes.

### Structural policy

`GovernancePolicy` controls institution-owned metadata requirements such as retention-policy presence for personal/restricted data, quality ownership for high-criticality data, authoritative-system requirements for source-of-truth declarations, and optional owner/steward separation.

A successful structural validation means only that the configured metadata requirements are represented. It does not determine lawful basis, privacy compliance, BCBS 239 compliance, data quality, regulatory applicability or semantic correctness.

## Planned v0.1 layers

1. v0.1.1 — authoritative inventory/accountability;
2. v0.1.2 — classification, critical data elements and business purpose;
3. v0.1.3 — lineage, transformations and provenance;
4. v0.1.4 — data quality, findings and remediation;
5. v0.1.5 — access-purpose, retention, legal hold and privacy/security obligations;
6. v0.1.6 — deterministic governance dossier, CLI and release gate.

Only completion of the full sequence establishes the proposed v0.1.0 foundation code boundary.
