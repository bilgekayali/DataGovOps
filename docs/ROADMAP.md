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
- [x] evidence-history preservation and strict schemas.

### v0.1.5 — Access, retention and privacy/security obligations (#7)
- [x] versioned access roles bound to governed principals and permissions;
- [x] exact asset/purpose access approvals and grants with stale/revocation checks;
- [x] retention schedules and deterministic deletion-eligibility evidence;
- [x] legal-hold and separate release evidence that blocks eligibility while active;
- [x] privacy/security/residency/cross-border mappings and exact location evidence;
- [x] institution-owned missing/stale control policy and deterministic gap reports;
- [x] strict schemas and release CI boundary.

### v0.1.6 — Governance dossier, CLI and release gate (#8)
- [x] deterministic dossier over the complete governed state;
- [x] explicit gaps, exceptions and revalidation-required state;
- [x] embedded artifact/domain snapshot cross-binding and offline tamper verification;
- [x] strict artifact type/domain/schema semantic verification;
- [x] canonical digest, Draft 2020-12 schema and dossier-verification CLI;
- [x] Python 3.11/3.12/3.13 CI, wheel and clean-wheel CLI smoke;
- [x] `0.1.0` package/code boundary and explicit publication non-claim.

Completion of #3 through #8 constitutes the **DataGovOps v0.1.0 foundation code/package boundary**. A Git tag or GitHub Release is a separate publication action and must be verified independently.

## v0.2 reporting-governance and assurance train

### v0.2.0 — Regulatory reporting lineage, reconciliation and assurance evidence (#15)
- [x] versioned governed-report identity, accountable owner, report family, purpose and frequency;
- [x] institution-owned timeliness, completeness and reconciliation thresholds;
- [x] report metrics bound to exact governed source asset versions and explicit transformation/quality-rule evidence;
- [x] strict latest-version currentness for source assets, transformations and quality rules;
- [x] production observations bound to exact inventory/semantic/lineage/quality reporting-basis snapshots;
- [x] deterministic `met` / `breached` / `incomplete` reporting-control assessments using integer units/basis points;
- [x] fail-closed missing and conflicting-latest reporting evidence;
- [x] accountable report-owner attestation with approved/rejected/escalated decisions;
- [x] reporting findings, remediation and independent HIGH/CRITICAL retest evidence;
- [x] reporting-domain dossier snapshot and aggregate gap/revalidation propagation;
- [x] offline semantic verification that recomputes assessment controls and rejects rehashed forged `met` evidence;
- [x] strict Draft 2020-12 reporting schemas and Python 3.11/3.12/3.13 release gates;
- [x] `0.2.0` package/code boundary with explicit BCBS 239/regulatory-reporting non-claims.

## v0.3 BCBS 239 multi-report assurance train

### v0.3.0 — Report taxonomy, risk-data portfolio and accountable aggregation assurance (#17)
- [x] institution-scoped report taxonomy with contiguous immutable version history;
- [x] exact current governed-report binding to institution-owned risk domains and aggregation levels;
- [x] versioned risk-data portfolios bound to exact report and taxonomy digests;
- [x] configured required risk-domain coverage without automated legal-applicability inference;
- [x] deterministic multi-report aggregation over current v0.2 report-assurance assessments;
- [x] fail-closed missing/incomplete report evidence and missing accountable report-owner attestations;
- [x] breached-state propagation for breached reports and rejected/escalated owner attestations;
- [x] exact report-assessment and report-attestation digest manifests with deterministic counts/gaps;
- [x] accountable portfolio-owner executive attestation with approval blocked for non-met aggregation state;
- [x] strict Draft 2020-12 BCBS assurance schemas, offline-capability guard and clean-wheel smoke;
- [x] structural non-claims for BCBS 239 compliance, risk-data accuracy and supervisory acceptance;
- [x] `0.3.0` package/code boundary.

## Later hardening toward v1

- PostgreSQL tenant isolation/RLS and institution-owned cryptographic boundaries;
- institution-owned signing keys, external immutable anchors and trusted timestamping;
- immutable audit/recovery evidence;
- deployment, supply-chain and release hardening;
- BCBS 239 / privacy / security control-evidence mapping without automated compliance scoring;
- stable API/data compatibility policy and v1 stable reference.
