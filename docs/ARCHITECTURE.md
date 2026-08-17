# DataGovOps Architecture

## v0.1 boundary

v0.1 is an offline governed data-asset registry. It records accountable ownership/stewardship, system of record, sensitivity classification, business criticality, personal-data indicator, source-of-truth status, retention-policy binding, and quality ownership.

A configurable governance policy checks structural completeness. It does not determine GDPR legal basis, prove BCBS 239 compliance, perform data discovery, inspect records, or construct lineage.

```text
DataAssetRecord + GovernancePolicy
              |
              v
       DataAssetValidator
              |
              v
 DataAssetValidationReport
```

Lineage and transformations are intentionally deferred to v0.2 so inventory completeness and lineage evidence remain separate control boundaries.
