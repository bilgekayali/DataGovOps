# DataGovOps

**Evidence-backed data governance, lineage, classification, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, and evidence controls.

Current development milestone: **v0.1.0 — Governed Data Asset Registry**.

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, or substitute for accountable data owners and stewards.

## Purpose

Financial institutions need evidence not only of where data is stored but who owns it, how sensitive and critical it is, which system is authoritative, which retention policy applies, and who is accountable for quality.

v0.1 starts with those foundational controls. It deliberately does not inspect data contents or infer GDPR legal basis.

## v0.1 control flow

```text
DataAssetRecord + GovernancePolicy
              |
              v
       DataAssetValidator
              |
              v
 DataAssetValidationReport
```

## Governance baseline

- institution-scoped registry;
- explicit owner, steward, classification, criticality and system-of-record fields;
- configurable completeness rules for personal/restricted and high-criticality data;
- canonical JSON + SHA-256 evidence bindings;
- no data scanning, data movement, network access or deletion capability;
- `regulatory_compliance_determined=false` is enforced;
- purpose/legal-basis, lineage, data quality measurements and retention execution remain later boundaries.

## Standards posture

Design inputs include:

- BCBS 239: https://www.bis.org/publ/bcbs239.htm
- Basel Committee 2026 BCBS 239 implementation observations: https://www.bis.org/publ/bcbs_nl36.htm
- Regulation (EU) 2016/679 — GDPR: https://eur-lex.europa.eu/eli/reg/2016/679/oj?locale=EN

These are design inputs, not certification claims.

## Roadmap

`v0.1 asset registry → v0.2 lineage → v0.3 purpose/access → v0.4 quality/CDE → v0.5 retention/privacy → BCBS 239 assurance/hardening → v1.0`

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
