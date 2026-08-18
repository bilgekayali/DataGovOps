# Lineage Governance Invariants

DataGovOps v0.1.3 represents explicit governance evidence for provenance relationships. It does not infer lineage from naming, SQL text, schemas, runtime traffic, or model output.

## Exact binding

- every source and target is an exact governed asset or data-element version plus content digest;
- every lineage edge binds an exact transformation version/digest;
- producer, consumer, transformation-execution systems and accountable owners must resolve in the same institution;
- transformation code/configuration are represented by SHA-256 digests and evidence references.

## Append-only history and current state

Historical endpoints, transformation versions and edges remain evidence. Current-state checks fail closed if a newer asset or transformation version supersedes a referenced version.

## Graph integrity

- dangling and cross-institution references are rejected;
- target-content or transformation-content digest mismatch is rejected;
- self-edges and directed cycles are rejected at edge registration;
- immutable edge identifiers cannot be reused for conflicting content.

## Completeness

Lineage completeness is evaluated only against explicit `LineageCompletenessRequirement` artifacts owned by accountable principals. No requirements means the system refuses to produce a completeness result rather than returning a vacuous success.

A requirement can be:

- satisfied by a current incoming governed edge;
- missing when its current target has no current incoming edge;
- stale when its target no longer represents the latest governed asset version.

## Assurance boundary

Lineage integrity evidence does not establish transformation correctness, semantic correctness, data quality, BCBS 239 compliance, legal applicability, security, or regulator acceptance. Bound code/configuration digests prove only integrity association to the represented evidence.
