# BCBS 239 assurance boundary

DataGovOps v0.3 adds deterministic multi-report risk-data aggregation assurance on top of the v0.2 reporting-governance registry.

The boundary is intentionally evidence-oriented. It helps an institution represent and verify its own report taxonomy, aggregation portfolio, report-level assurance state, accountable owner attestations and portfolio-level executive attestation. It does not decide whether BCBS 239 legally applies and does not certify BCBS 239 compliance.

## Model

```text
current governed reports
  -> exact report taxonomy entries
  -> versioned risk-data portfolio
  -> current report assurance assessments
  -> latest accountable report-owner attestations
  -> deterministic portfolio aggregation assessment
  -> accountable portfolio-owner attestation
```

### Report taxonomy

`ReportTaxonomyEntry` binds an exact current governed-report digest to an institution-owned risk domain and aggregation level. Taxonomy history is contiguous and immutable. A newer governed-report version makes taxonomy bound to the old report fail currentness checks.

### Risk-data portfolio

`RiskDataPortfolio` binds exact report digests and exact taxonomy digests. Every report must have exactly one current taxonomy entry and the configured required risk domains must be represented. Portfolio versions are contiguous and immutable.

### Aggregation assessment

`BCBS239AssuranceRegistry.evaluate_portfolio()` selects the latest current report assurance assessment for each report and period and the latest accountable report-owner attestation available by the aggregation assessment timestamp.

The state is fail-closed:

- `incomplete` if a required report assessment is absent, a report assessment is incomplete, or an accountable report-owner attestation is missing;
- `breached` if represented report controls are breached or the latest owner attestation is rejected/escalated;
- `met` only when every represented report assessment is met and every report has an approved accountable-owner attestation.

The artifact records exact report-assessment and report-attestation digests plus deterministic counts and gap codes.

### Executive assurance

`ExecutiveAssuranceAttestation` is bound to one exact aggregation-assessment digest and must use the accountable portfolio owner. An `approved` executive decision is rejected unless the underlying aggregation assessment is `met`.

## Explicit non-claims

The v0.3 BCBS 239 assurance layer always keeps these conclusions false:

- `bcbs239_compliance_determined`
- `risk_data_accuracy_determined`
- `supervisory_acceptance_determined`

A `met` aggregation assessment means only that the represented current DataGovOps evidence satisfies the configured deterministic assurance contract. It does not establish legal applicability, objective data accuracy, completeness of all enterprise risk data, regulatory-report correctness, BCBS 239 compliance, or supervisory acceptance.

## Security and runtime boundary

The module is offline and performs no network, database, filing, messaging or external control execution. Institution/tenant runtime isolation, cryptographic signing, immutable anchoring and deployment hardening are later milestones toward v1.
