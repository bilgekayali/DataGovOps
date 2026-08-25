# DataGovOps Roadmap

## v0.1 foundation train

### v0.1.1 — Authoritative inventory and accountability (#3)
- [x] accountable-principal and authoritative-system registries;
- [x] immutable contiguous data-asset versions and exact accountable references;
- [x] classification/criticality decisions, deterministic snapshots and strict schemas.

### v0.1.2 — Classification, CDE and business-purpose evidence (#4)
- [x] data-element identity/ownership, classification decisions and CDE designations;
- [x] versioned business-purpose registry and exact asset-version bindings.

### v0.1.3 — Lineage, transformation and provenance (#5)
- [x] exact asset/data-element lineage and transformation evidence;
- [x] cycle/dangling/cross-institution/stale-reference controls and completeness reporting.

### v0.1.4 — Data quality and remediation evidence (#6)
- [x] versioned rules, deterministic quality assessment, findings/remediation/retest and evidence history.

### v0.1.5 — Access, retention and privacy/security obligations (#7)
- [x] access approvals/grants, retention, legal hold, privacy/security/residency mappings and gap reports.

### v0.1.6 — Governance dossier, CLI and release gate (#8)
- [x] deterministic dossier, exceptions/revalidation, offline tamper verification, CLI, schemas and `0.1.0` boundary.

## v0.2 reporting-governance and assurance train

### v0.2.0 — Regulatory reporting lineage, reconciliation and assurance evidence (#15)
- [x] governed report identity, exact basis bindings and deterministic timeliness/completeness/reconciliation controls;
- [x] owner attestation, findings/remediation/retest and reporting-domain dossier verification;
- [x] `0.2.0` package/code boundary.

## v0.3 BCBS 239 multi-report assurance train

### v0.3.0 — Report taxonomy, risk-data portfolio and accountable aggregation assurance (#17)
- [x] report taxonomy, versioned risk-data portfolios and multi-report aggregation assurance;
- [x] fail-closed missing/incomplete evidence and accountable executive attestation;
- [x] `0.3.0` package/code boundary.

## v0.4 institution security train

### v0.4.0 — Identity, institution isolation and evidence cryptography (#18)
- [x] offline Ed25519 OIDC/JWT verification, institution/RBAC/MFA controls;
- [x] AES-256-GCM evidence envelopes with external KMS/HSM references;
- [x] metadata-only security observations and PostgreSQL `FORCE RLS` + `NOBYPASSRLS` reference;
- [x] `0.4.0` package/code boundary.

## v0.5 signed governance evidence and provenance train

### v0.5.0 — External signatures, anchor receipts and release evidence (#19)
- [x] verified-dossier-bound Ed25519 evidence and external signing-key references;
- [x] anchor/timestamp receipt contracts, build provenance, CycloneDX-shaped SBOM and exact-byte release manifests;
- [x] `0.5.0` package/code boundary.

## v0.6 immutable audit and recovery evidence train

### v0.6.0 — Audit chains, backup/restore evidence and historical-state verification (#20)
- [x] metadata-only hash-chained audit events and checkpoints;
- [x] RPO/RTO/backup-age/minimum-retention policy evidence;
- [x] exact-byte backup integrity, restore verification and historical-state comparison;
- [x] deterministic `met` / `breached` / `incomplete` recovery assessment;
- [x] `0.6.0` package/code boundary.

## v0.7 deployment and runtime operational hardening train

### v0.7.0 — Immutable deployment identity and runtime-control evidence (#21)
- [x] digest-bound immutable image references and mutable-tag rejection;
- [x] non-root/read-only/no-privilege-escalation/non-privileged/drop-all-capabilities/seccomp evidence;
- [x] host namespace and service-account-token automount disablement evidence;
- [x] default-deny ingress/egress boundary and external-secret references;
- [x] metadata-only runtime observations and validator negative-path evidence;
- [x] deterministic `represented` / `incomplete` deployment assessment with production/security/compliance non-claims;
- [x] hardened Dockerfile reference, Kubernetes workload template and default-deny NetworkPolicy reference;
- [x] four strict Draft 2020-12 schemas, offline guard and clean-wheel deployment CI;
- [x] `0.7.0` package/code boundary while retaining Alpha maturity.

## v0.8 control/evidence matrix

- [ ] map BCBS 239 / privacy / security / recovery / deployment controls to expected evidence and accountable roles;
- [ ] deterministic coverage/gap output without automated compliance scoring;
- [ ] machine-readable control matrix and management assurance export.

## v0.9 release candidate

- [ ] freeze intentional public Python API and public schema surfaces;
- [ ] add compatibility policy, CodeQL and release-candidate gates;
- [ ] pin schema snapshots and repository-governance expectations without inventing enforcement evidence.

## v1.0 stable reference

- [ ] promote package/API/schema contract to `1.0.0` after all RC gates are green;
- [ ] retain explicit production-readiness, regulatory-compliance and supervisory-acceptance non-claims unless external evidence exists.
