# DataGovOps

**Evidence-backed data governance, lineage, quality, reporting assurance, security, release integrity, recovery evidence and deployment-control references for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, verifiable governance evidence and deterministic operational assurance.

Current code/package milestone: **DataGovOps v0.7.0 deployment and runtime hardening boundary** (`0.7.0`).

A package version in the codebase does **not** by itself mean that a Git tag, GitHub Release, container image or production deployment has been published. Those facts must be verified separately.

## v0.7.0 deployment and runtime hardening boundary

v0.7 retains the v0.1-v0.6 governance, BCBS 239 assurance, institution-security, signed-evidence and recovery boundaries and adds a deterministic deployment-control evidence layer:

```text
Verified package / release evidence
              |
              v
Immutable image reference
repository@sha256:<digest>
              |
              v
Runtime security profile
non-root / read-only / no privilege escalation
capability drop / seccomp / no host namespaces
              |
              +-------------------+
              |                   |
              v                   v
Default-deny network        External secret refs
              |                   |
              +---------+---------+
                        v
             Deployment evidence
                        |
                        v
        represented / incomplete assessment
```

The v0.7 boundary includes:

- SHA-256 digest-bound image references and rejection of mutable tag-bearing repository references;
- non-root, read-only-root-filesystem, no-privilege-escalation, non-privileged, drop-all-capabilities and RuntimeDefault-seccomp expectations;
- explicit disabled host network/PID/IPC namespaces and service-account-token automount;
- default-deny ingress and egress evidence;
- external secret references containing provider/key/version metadata only;
- metadata-only runtime observations with raw-content and secret-material logging structurally disabled;
- validator identity plus explicit negative-path confirmation;
- deterministic `represented` / `incomplete` deployment assessment;
- a reference Dockerfile that requires caller-supplied digest-pinned `BASE_IMAGE`;
- a Kubernetes workload template with hardened security context and external-secrets CSI reference;
- explicit default-deny NetworkPolicy references;
- four strict Draft 2020-12 schemas, adversarial tests, offline capability enforcement and clean-wheel CI.

A represented deployment assessment is **not** a production security conclusion. See [`docs/DEPLOYMENT_HARDENING.md`](docs/DEPLOYMENT_HARDENING.md).

## Retained boundaries

- **v0.6 audit/recovery:** hash-chained metadata-only audit events, checkpoints, RPO/RTO/backup-age/retention policy evidence, exact-byte backup integrity, restore verification and historical-state verification.
- **v0.5 signed evidence/provenance:** verified-dossier-bound Ed25519 evidence, external key references, anchor/timestamp receipt contracts, build provenance, SBOM and exact-byte release manifests.
- **v0.4 institution security:** offline Ed25519 OIDC/JWT verification, institution/RBAC/MFA guards, AES-256-GCM evidence protection with external key references and PostgreSQL RLS reference.
- **v0.3 BCBS 239 assurance:** report taxonomy, risk-data portfolios, multi-report aggregation evidence and accountable attestations.
- **v0.2 reporting governance:** governed reports, exact source/transformation/quality bindings, timeliness/completeness/reconciliation controls, findings/remediation/retest.
- **v0.1 foundation:** institution-scoped inventory/accountability, classification/CDE/business-purpose evidence, lineage, quality, access/retention/privacy-security obligations and deterministic governance dossiers.

Historical/versioned evidence remains preserved without silently becoming current after governed state changes.

## Governance dossier states

Governance dossiers retain deterministic states `current`, `with_gaps`, `with_exceptions` and `revalidation_required`. Security, signed-evidence, recovery and deployment layers remain separate reference boundaries rather than being treated as automatic legal-compliance domains.

## CLI

```bash
datagovops --version
datagovops digest document.json
datagovops schema schema.json document.json
datagovops dossier verify governance-dossier.json
```

## Standards posture

Design mappings are intended to support evidence/control alignment with BCBS 239, Basel Committee implementation observations, GDPR/KVKK accountability concepts, ISO/IEC 27001, ISO/IEC 27701 and ISO 22301 control/evidence concepts, DAMA-aligned governance concepts, and relevant institution-owned BDDK/SPK requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, prove data/report correctness, or establish production resilience/security merely because evidence is represented.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK or ISO compliance;
- production identity-provider/JWKS or PostgreSQL institution-isolation effectiveness;
- production KMS/HSM signing/encryption key custody or effectiveness;
- signer authority, external timestamp/anchor validity or complete SBOM/vulnerability coverage;
- SLSA certification or production build provenance;
- production audit-log immutability, backup durability, restore success or objective RPO/RTO achievement;
- Kubernetes admission/enforcement, registry/base-image trust, image vulnerability absence or runtime sandbox effectiveness;
- NetworkPolicy effectiveness in a real CNI implementation;
- external-secret provider effectiveness or production observability coverage;
- regulatory-report correctness, supervisory acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
