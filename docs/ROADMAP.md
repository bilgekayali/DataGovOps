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
- [x] exact asset-version data-element identity and ownership;
- [x] governed asset/data-element classification-decision artifacts;
- [x] critical data element designation, accountable owner and evidence;
- [x] versioned business-purpose registry and exact asset-version bindings;
- [x] stale asset/purpose validation and conflicting-decision failure paths;
- [x] deterministic semantic snapshot and strict schemas.

### v0.1.3 — Lineage, transformation and provenance (#5)
- [x] source/target asset- and data-element-version lineage;
- [x] mixed-granularity exact endpoint references and digest binding;
- [x] versioned transformation identity, owner, execution system and code/config/evidence digests;
- [x] producer/consumer/system relationships;
- [x] directed-cycle, dangling, cross-institution and stale-reference controls;
- [x] deterministic lineage snapshot and explicit completeness gap reports;
- [x] strict schemas and Python 3.11/3.12/3.13 CI boundary.

### v0.1.4 — Data quality and remediation evidence (#6)
- [x] exact asset/CDE quality targets and versioned rule identities;
- [x] quality dimensions, integer metric/unit contracts, comparison operators and thresholds;
- [x] institution-owned missing/stale observation policy and freshness windows;
- [x] immutable observations and deterministic pass/breach/incomplete evaluation;
- [x] fail-closed conflicting-latest evidence controls;
- [x] findings with severity anti-downgrade controls;
- [x] remediation, independent HIGH/CRITICAL retest and deterministic closure evidence;
- [x] evidence-history preservation, strict schemas and dev4 CI boundary.

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
