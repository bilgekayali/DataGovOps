# DataGovOps

**Evidence-backed data governance, lineage, quality, reporting assurance, security, release integrity, recovery evidence, deployment-control references and cross-boundary control/evidence assurance for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, verifiable governance evidence and deterministic operational assurance.

Current code/package milestone: **DataGovOps v0.9.0 release-candidate boundary** (`0.9.0`).

A package version in the codebase does **not** by itself mean that a Git tag, GitHub Release, container image or production deployment has been published. Those facts must be verified separately.

## v0.9.0 release-candidate boundary

v0.9 retains the v0.1-v0.8 governance and assurance boundaries and freezes the intentional public contract for the v1.0 stable-reference promotion.

The release-candidate boundary includes:

- a deterministic fingerprint of the sorted Python symbols exported through `datagovops.__all__`;
- a deterministic exact-byte fingerprint of every public `schemas/*.schema.json` document;
- a committed `release/release-contract.json` used by the release-candidate gate;
- a compatibility policy defining the v0.9 -> v1 freeze and post-v1 semantic-versioning expectations;
- governance-dossier `release_version` decoupled from one package version so the schema can remain frozen across the v1 promotion while runtime verification still binds evidence to the evaluated package release;
- all third-party GitHub Actions references pinned to exact commit SHAs;
- CodeQL analysis for Python;
- a dedicated Release Candidate workflow that verifies the public-API/schema fingerprints, package/dossier version alignment, Beta classifier, exact action pins, governance-policy non-claims, contract tests and a clean-wheel installation;
- a machine-readable repository-governance expectation file with PR/workflow/no-force-push/no-delete expectations;
- explicit `enforcement_verified=false` because live branch protection/ruleset enforcement is not inferred from the reference policy;
- removal of the stale v0.1 publication workflow from the active workflow surface.

Passing the v0.9 release-candidate gate means the repository matches its frozen represented contract. It does **not** establish production readiness, regulatory compliance, certification or supervisory acceptance.

See [`COMPATIBILITY.md`](COMPATIBILITY.md) and the files under [`release/`](release/).

## Retained boundaries

- **v0.8 control/evidence matrix:** versioned institution-owned controls, exact source/snapshot/evidence bindings and deterministic `represented` / `gap` / `revalidation_required` currentness without compliance scoring.
- **v0.7 deployment/runtime hardening:** digest-bound immutable image references, hardened Docker/Kubernetes references, non-root/read-only/no-privilege-escalation runtime controls, default-deny network evidence and external-secret references.
- **v0.6 audit/recovery:** hash-chained metadata-only audit events, checkpoints, RPO/RTO/backup-age/retention policy evidence, exact-byte backup integrity, restore verification and historical-state verification.
- **v0.5 signed evidence/provenance:** verified-dossier-bound Ed25519 evidence, external key references, anchor/timestamp receipt contracts, build provenance, SBOM and exact-byte release manifests.
- **v0.4 institution security:** offline Ed25519 OIDC/JWT verification, institution/RBAC/MFA guards, AES-256-GCM evidence protection with external key references and PostgreSQL RLS reference.
- **v0.3 BCBS 239 assurance:** report taxonomy, risk-data portfolios, multi-report aggregation evidence and accountable attestations.
- **v0.2 reporting governance:** governed reports, exact source/transformation/quality bindings, timeliness/completeness/reconciliation controls, findings/remediation/retest.
- **v0.1 foundation:** institution-scoped inventory/accountability, classification/CDE/business-purpose evidence, lineage, quality, access/retention/privacy-security obligations and deterministic governance dossiers.

Historical/versioned evidence remains preserved without silently becoming current after governed state changes.

## Governance dossier states

Governance dossiers retain deterministic states `current`, `with_gaps`, `with_exceptions` and `revalidation_required`. Security, signed-evidence, recovery, deployment and control/evidence-matrix layers remain separate reference boundaries rather than being treated as automatic legal-compliance domains.

## CLI

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

## Standards posture

Design mappings are intended to support evidence/control alignment with BCBS 239, Basel Committee implementation observations, GDPR/KVKK accountability concepts, ISO/IEC 27001, ISO/IEC 27701 and ISO 22301 control/evidence concepts, DAMA-aligned governance concepts, and relevant institution-owned BDDK/SPK requirements.

These are architecture/design inputs. A framework reference in the control/evidence matrix is a mapping aid, not a determination that the framework applies. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, prove data/report correctness, or establish production resilience/security merely because evidence is represented.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK or ISO compliance;
- framework, legal or regulatory applicability merely because a control is mapped to a reference;
- objective control effectiveness or a compliance/maturity percentage;
- production identity-provider/JWKS or PostgreSQL institution-isolation effectiveness;
- production KMS/HSM signing/encryption key custody or effectiveness;
- signer authority, external timestamp/anchor validity or complete SBOM/vulnerability coverage;
- SLSA certification or production build provenance;
- production audit-log immutability, backup durability, restore success or objective RPO/RTO achievement;
- Kubernetes admission/enforcement, registry/base-image trust, image vulnerability absence or runtime sandbox effectiveness;
- NetworkPolicy effectiveness in a real CNI implementation;
- external-secret provider effectiveness or production observability coverage;
- live GitHub branch/ruleset enforcement merely because a repository-governance policy is committed;
- regulatory-report correctness, supervisory acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
