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
- [x] versioned access roles bound to governed principals and permissions;
- [x] exact asset/purpose access approvals and grants with stale/revocation checks;
- [x] retention schedules and deterministic deletion-eligibility evidence;
- [x] legal-hold and separate release evidence that blocks eligibility while active;
- [x] privacy/security/residency/cross-border mappings and exact location evidence;
- [x] institution-owned missing/stale control policy and deterministic gap reports;
- [x] strict schemas and dev5 CI boundary.

### v0.1.6 — Governance dossier, CLI and release gate (#8)
- [x] deterministic dossier over the complete governed state;
- [x] explicit gaps, exceptions and revalidation-required state;
- [x] embedded artifact/domain snapshot cross-binding and offline tamper verification;
- [x] strict artifact type/domain/schema semantic verification;
- [x] canonical digest, Draft 2020-12 schema and dossier-verification CLI;
- [x] Python 3.11/3.12/3.13 CI, wheel and clean-wheel CLI smoke;
- [x] `0.1.0` package/code boundary and explicit publication non-claim.

Completion of #3 through #8 constitutes the proposed **DataGovOps v0.1.0 foundation code/package release boundary**. A Git tag or GitHub Release is a separate publication action and must be verified independently.

## Later hardening toward v1

- BCBS 239 risk-data aggregation assurance mappings and evidence;
- PostgreSQL tenant isolation/RLS and institution-owned cryptographic boundaries;
- institution-owned signing keys, external immutable anchors and trusted timestamping;
- immutable audit/recovery evidence;
- deployment, supply-chain and release hardening;
- stable API/data compatibility policy and v1 production reference.
