# DataGovOps

**Evidence-backed data governance, lineage, classification, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, lineage, purpose, quality, access, retention, and evidence controls.

The project is intended for regulated and high-assurance environments. It is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, or substitute for accountable data owners and stewards.

## Purpose

Financial institutions need to prove not only where data is stored, but where it came from, who owns it, what purpose it serves, how sensitive and critical it is, which transformations affect it, who may use it, and how long it should be retained.

DataGovOps will model those governance relationships as deterministic, machine-readable evidence.

## Initial standards posture

Design inputs include:

- BCBS 239 — Principles for effective risk data aggregation and risk reporting: https://www.bis.org/publ/bcbs239.htm
- Basel Committee 2026 implementation observations on BCBS 239: https://www.bis.org/publ/bcbs_nl36.htm
- Regulation (EU) 2016/679 — General Data Protection Regulation: https://eur-lex.europa.eu/eli/reg/2016/679/oj?locale=EN

These references inform the architecture; DataGovOps does not certify regulatory compliance or determine legal basis automatically.

## Roadmap direction

`v0.1 governed data asset registry → v0.2 lineage & transformations → v0.3 purpose/access governance → v0.4 quality & critical data elements → v0.5 retention & privacy evidence → v0.6 risk-data aggregation assurance → v0.7 tenant/crypto hardening → v0.8 production reference → v1.0 stable release`

## License

Apache License 2.0.
