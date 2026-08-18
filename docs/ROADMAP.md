# DataGovOps Roadmap

## v0.1 foundation train

### v0.1.1 — Authoritative inventory and accountability (#3)
- [x] accountable-principal registry;
- [x] authoritative-system registry;
- [x] immutable contiguous data-asset versions;
- [x] exact owner/steward/system/decision-owner references;
- [x] explicit classification/criticality owner and rationale;
- [x] institution-owned structural completeness policy;
- [x] deterministic registry snapshot and stale-report detection;
- [x] strict schemas and Python 3.11/3.12/3.13 CI.

### v0.1.2 — Classification, CDE and business-purpose evidence (#4)
- [ ] governed classification-decision artifacts;
- [ ] critical data element designation and ownership;
- [ ] business-purpose registry and exact asset-version bindings;
- [ ] stale-decision validation and strict schemas.

### v0.1.3 — Lineage, transformation and provenance (#5)
- [ ] source/target asset-version lineage;
- [ ] transformation identity, owner and code/config digest;
- [ ] producer/consumer/system relationships;
- [ ] lineage snapshot and completeness gaps.

### v0.1.4 — Data quality and remediation evidence (#6)
- [ ] quality rules, dimensions and thresholds;
- [ ] observations and deterministic breach/incomplete evaluation;
- [ ] findings, remediation and retest/closure evidence;
- [ ] freshness and conflicting-latest evidence controls.

### v0.1.5 — Access, retention and privacy/security obligations (#7)
- [ ] access-purpose bindings and accountable approval evidence;
- [ ] retention schedules and deletion-eligibility evidence;
- [ ] legal-hold override state;
- [ ] privacy/security obligation mappings and location evidence.

### v0.1.6 — Governance dossier, CLI and release gate (#8)
- [ ] deterministic dossier over the complete governed state;
- [ ] gaps/exceptions/revalidation-required state;
- [ ] offline integrity/tamper verification;
- [ ] digest/schema/dossier CLI;
- [ ] wheel/release evidence and v0.1.0 package boundary.

Completion of #3 through #8 constitutes the proposed **DataGovOps v0.1.0 foundation release**.

## Later hardening toward v1

- BCBS 239 risk-data aggregation assurance mappings and evidence;
- PostgreSQL tenant isolation/RLS and institution-owned cryptographic boundaries;
- immutable audit/recovery evidence;
- deployment, supply-chain and release hardening;
- stable API/data compatibility policy and v1 production reference.
