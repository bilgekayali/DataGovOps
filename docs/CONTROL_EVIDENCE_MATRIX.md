# Control / Evidence Matrix Boundary

DataGovOps v0.8 adds a machine-readable, institution-owned control/evidence matrix across governed-data, BCBS 239 assurance, privacy/security, recovery/resilience, deployment/runtime and release-integrity evidence boundaries.

The matrix is an evidence-index and currentness boundary. It is not a compliance engine.

## Design

A `ControlDefinition` is versioned and institution-scoped. Each control declares:

- an accountable owner and control objective;
- one or more required evidence types;
- the DataGovOps source boundaries accepted for each evidence type;
- optional framework references and mapping rationale.

Framework references are design mappings only. `applicability_determined` and the control-level framework/legal applicability flags are structurally fixed to `false`.

A `ControlEvidenceReference` binds one exact control version to:

- an evidence type;
- a source boundary;
- an exact source artifact SHA-256 digest;
- an exact source snapshot SHA-256 digest;
- a verification-evidence SHA-256 digest;
- an observation time and explicit revalidation deadline.

The reference contains metadata only. It does not establish that the represented control is effective, legally sufficient, regulatorily applicable or compliant.

## Deterministic assessment

For each required evidence type, the registry selects the unique latest observation bound to the exact latest control-definition digest.

- no evidence -> `gap`;
- unique current evidence -> `represented`;
- latest evidence beyond its revalidation deadline -> `revalidation_required`;
- multiple latest observations at the same timestamp -> fail closed as ambiguous;
- evidence from an unaccepted source boundary -> registration fails closed;
- evidence crossing institution scope -> registration fails closed.

When a control advances from version N to N+1, evidence bound to version N is preserved historically but is not silently reused for version N+1. The current control therefore remains a gap until new evidence is explicitly bound to the new control digest.

## Matrix state

The matrix aggregates explicit control assessments without producing a score:

- `represented` — every selected control has current represented evidence;
- `with_gaps` — at least one selected control is missing required evidence and none requires revalidation;
- `revalidation_required` — at least one selected control has stale evidence; this state takes precedence over `with_gaps`.

The matrix exposes integer counts only. It deliberately has no percentage, maturity score, compliance score, pass rate or inferred legal/regulatory result.

## Example source boundaries

A control may require an evidence type from one or more explicitly accepted boundaries, for example:

- BCBS 239 aggregation-assessment evidence from the `bcbs239` boundary;
- obligation/control-report evidence from `access_retention_privacy`;
- identity/security observation evidence from `security`;
- recovery-assessment evidence from `recovery`;
- deployment-assessment evidence from `deployment`;
- signed release/provenance evidence from `release_evidence`.

The matrix does not infer that a named framework applies merely because a control carries a reference to it.

## Explicit non-claims

A represented matrix does not by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001, ISO/IEC 27701, ISO 22301 or other regulatory/standards compliance;
- legal applicability, lawful basis or legal sufficiency;
- objective control effectiveness or production enforcement;
- production data/report accuracy, completeness or regulatory-report correctness;
- production identity, cryptographic, recovery, network, container or Kubernetes effectiveness;
- supervisory acceptance, certification, attestation or production readiness.

Every control assessment and matrix requires human review, and automated compliance scoring remains structurally disabled.
