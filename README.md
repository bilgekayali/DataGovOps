# DataGovOps

**Evidence-backed data governance, lineage, quality, reporting assurance, security, release integrity, recovery evidence, deployment-control references and cross-boundary control/evidence assurance for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, business purpose, quality, access, retention, privacy/security obligations, reporting controls, verifiable governance evidence and deterministic operational assurance.

Current code/package milestone: **DataGovOps v0.8.0 control/evidence matrix boundary** (`0.8.0`).

A package version in the codebase does **not** by itself mean that a Git tag, GitHub Release, container image or production deployment has been published. Those facts must be verified separately.

## v0.8.0 control/evidence matrix boundary

v0.8 retains the v0.1-v0.7 governance, BCBS 239 assurance, institution-security, signed-evidence, recovery and deployment boundaries and adds a machine-readable cross-boundary evidence index:

```text
Institution-owned versioned control
              |
              +--> evidence requirement(s)
              |         |
              |         +--> accepted source boundary
              |
              +--> optional framework reference
                        applicability remains undetermined

Exact source artifact digest
Exact source snapshot digest
Verification-evidence digest
              |
              v
Control evidence reference
              |
      currentness evaluation
              |
              v
represented / gap / revalidation_required
              |
              v
Control / Evidence Matrix
(integer counts only; no compliance score)
```

The v0.8 boundary includes:

- versioned, institution-scoped `ControlDefinition` records with accountable owners and explicit objectives;
- required evidence types with explicitly accepted source boundaries including BCBS 239, access/retention/privacy, security, recovery, deployment, release evidence, governance dossiers and institution-owned external evidence;
- optional framework/reference mappings whose applicability remains structurally undetermined;
- exact SHA-256 binding to source artifact, source snapshot and verification evidence;
- explicit observation and revalidation timestamps;
- deterministic currentness: missing evidence -> `gap`, unique current evidence -> `represented`, stale evidence -> `revalidation_required`;
- ambiguous latest evidence fails closed rather than selecting one silently;
- evidence bound to an older control version remains historical and is not silently reused after the control advances;
- matrix state precedence `revalidation_required` > `with_gaps` > `represented`;
- integer control counts only, with no percentage, maturity score, pass rate or compliance score;
- mandatory human review and structural non-claims for framework applicability, control effectiveness, legal/regulatory compliance and supervisory acceptance;
- four strict Draft 2020-12 schemas, adversarial tests, offline capability enforcement and clean-wheel CI.

A represented matrix means only that the configured evidence requirements are represented by current evidence references. It does **not** establish compliance or production control effectiveness. See [`docs/CONTROL_EVIDENCE_MATRIX.md`](docs/CONTROL_EVIDENCE_MATRIX.md).

## Retained boundaries

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

These are architecture/design inputs. A framework reference in the v0.8 matrix is a mapping aid, not a determination that the framework applies. DataGovOps does not certify compliance, determine lawful basis, infer regulatory applicability, prove data/report correctness, or establish production resilience/security merely because evidence is represented.

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
- regulatory-report correctness, supervisory acceptance, certification or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
