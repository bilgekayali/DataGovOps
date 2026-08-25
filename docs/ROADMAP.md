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

## v0.2 reporting-governance and assurance train

### v0.2.0 — Regulatory reporting lineage, reconciliation and assurance evidence (#15)
- [x] governed report identity, accountable owner, report family, purpose and frequency;
- [x] institution-owned timeliness, completeness and reconciliation thresholds;
- [x] exact source/transformation/quality-rule bindings and currentness;
- [x] production observations bound to exact governed reporting-basis snapshots;
- [x] deterministic `met` / `breached` / `incomplete` reporting assessments;
- [x] accountable owner attestation, findings, remediation and independent retest;
- [x] reporting dossier snapshot and offline semantic verification;
- [x] `0.2.0` package/code boundary with explicit non-claims.

## v0.3 BCBS 239 multi-report assurance train

### v0.3.0 — Report taxonomy, risk-data portfolio and accountable aggregation assurance (#17)
- [x] institution-scoped report taxonomy with contiguous immutable versions;
- [x] exact current report binding to institution-owned risk domains/aggregation levels;
- [x] versioned risk-data portfolios bound to exact report/taxonomy digests;
- [x] deterministic multi-report aggregation over current reporting assessments;
- [x] fail-closed missing/incomplete evidence and owner attestations;
- [x] accountable portfolio-owner executive attestation;
- [x] strict schemas, offline guard, clean-wheel smoke and structural non-claims;
- [x] `0.3.0` package/code boundary.

## v0.4 institution security train

### v0.4.0 — Identity, institution isolation and evidence cryptography (#18)
- [x] caller-supplied trusted Ed25519 public-key verification for OIDC/JWT evidence;
- [x] issuer, audience, expiration/not-before, institution-scope, role and MFA checks;
- [x] immutable `InstitutionContext` with explicit cross-institution and RBAC guards;
- [x] AES-256-GCM evidence protection bound to institution, artifact type and external key reference;
- [x] external KMS/HSM reference semantics with no embedded private keys/secrets;
- [x] metadata-only security observations and production-observability non-claims;
- [x] PostgreSQL `FORCE ROW LEVEL SECURITY` + `NOBYPASSRLS` institution-isolation reference;
- [x] strict Draft 2020-12 security schema, adversarial tests and dedicated security CI gate;
- [x] `0.4.0` package/code boundary while retaining Alpha maturity.

## v0.5 signed governance evidence and provenance train

### v0.5.0 — External signatures, anchor receipts and release evidence (#19)
- [x] canonical governance-evidence statement bound to an already verified dossier, institution, release and source revision;
- [x] external Ed25519 signature verification with no runtime private-signing-key API/material;
- [x] institution/external signing-key reference semantics;
- [x] immutable-anchor and timestamp-token receipt contracts with validation non-claims;
- [x] deterministic build provenance bound to package/version/source and exact subjects/materials;
- [x] CycloneDX-shaped dependency SBOM with explicit completeness/vulnerability non-claims;
- [x] exact-byte release-evidence manifest using SHA-256 and artifact sizes;
- [x] provenance/SBOM/manifest identity cross-checks and tamper-failure paths;
- [x] five strict Draft 2020-12 evidence schemas and dedicated Release Evidence Integrity CI;
- [x] `0.5.0` package/code boundary while retaining Alpha maturity.

## v0.6 immutable audit and recovery evidence train

### v0.6.0 — Audit chains, backup/restore evidence and historical-state verification (#20)
- [x] institution-scoped metadata-only audit events with contiguous sequence and predecessor-digest binding;
- [x] monotonic timestamp and cross-institution fail-closed chain verification;
- [x] audit-chain checkpoints with explicit external-immutability non-claim;
- [x] institution-owned RPO/RTO/backup-age/minimum-retention policy evidence;
- [x] backup evidence bound to exact historical-state digest, policy digest, storage reference, SHA-256 and byte size;
- [x] exact-byte backup verification and deterministic retention-expiry binding;
- [x] restore verification bound to exact backup and expected/recovered state digests;
- [x] historical-state verification with deterministic match/breach evidence;
- [x] deterministic `met` / `breached` / `incomplete` recovery assessment over freshness, RPO, retention, restore integrity and RTO;
- [x] seven strict Draft 2020-12 schemas, offline guard and clean-wheel audit/recovery CI;
- [x] `0.6.0` package/code boundary while retaining Alpha maturity.

## Later hardening toward v1

- deployment, supply-chain and runtime operational hardening;
- BCBS 239 / privacy / security control-evidence mapping without automated compliance scoring;
- release-candidate CodeQL/governance gates and compatibility freeze;
- stable API/data compatibility policy and v1 stable reference.
