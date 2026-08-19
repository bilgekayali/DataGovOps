# DataGovOps v0.2 Reporting Governance

## Purpose

The v0.2 reporting layer represents institution-owned reporting governance and assurance evidence over the DataGovOps inventory, semantic, lineage and quality foundations.

It is designed to make reporting-control evidence deterministic and reviewable. It does not determine regulatory applicability, BCBS 239 compliance, legal sufficiency, report correctness, financial-statement accuracy or supervisory acceptance.

## Evidence chain

```text
Governed report
  -> latest governed metric definitions
  -> exact source asset/version references
  -> explicit transformation / quality-rule evidence
  -> current reporting-basis digest
  -> period production observation
  -> timeliness / completeness / reconciliation assessment
  -> accountable-owner attestation
  -> finding / remediation / post-remediation reassessment / independent retest
  -> governance dossier
```

## Reporting basis

A current reporting basis binds:

- the exact governed report digest;
- the latest metric definition for each metric identity bound to that report version;
- the current authoritative inventory snapshot;
- the current semantic-governance snapshot;
- the current lineage snapshot;
- the current quality-governance snapshot.

Metric history remains preserved in the reporting registry snapshot, but historical metric versions are not silently treated as the current reporting basis.

## Control assessment

The reference implementation evaluates three explicit institution-owned controls:

- **timeliness** — represented lateness in integer seconds must not exceed the report threshold;
- **completeness** — represented actual/expected record-count ratio is evaluated in integer basis points;
- **reconciliation** — represented variance in integer basis points must not exceed the report threshold.

The deterministic aggregate state is `met`, `breached` or `incomplete`. Missing metric definitions or missing production observations produce `incomplete`. Conflicting latest production observations fail closed.

A `met` result means only that the supplied current evidence satisfies the configured controls. It does not prove the real-world report or underlying data is correct.

## Currentness

Current reporting evidence fails closed when, among other cases:

- a referenced source asset is no longer the latest governed asset version;
- a referenced transformation is no longer the latest version for its transformation identity;
- a referenced quality rule is no longer the latest rule version;
- the reporting-basis digest no longer matches current governed snapshots;
- the latest eligible production observation conflicts or belongs to an older reporting basis.

Historical artifacts remain immutable audit evidence. Offline verification checks their exact cross-bindings and represented control semantics without pretending that a historical artifact is current after the governed environment changes.

## Attestation

A report-owner attestation binds the exact assessment digest. The accountable report owner may explicitly approve, reject or escalate the represented evidence. `approved` is permitted only for a `met` assessment.

Attestation is an institution-owned review artifact. It is not regulatory approval or a supervisory acceptance receipt.

## Finding closure and post-remediation reassessment

A reporting finding can arise only from a non-`met` assessment. HIGH/CRITICAL findings require an independent retest reviewer distinct from the remediation owner.

A `passed` retest is not a free-form status label. It must bind an exact **post-remediation reassessment** that:

- covers the same report and reporting period as the original finding assessment;
- was assessed after the bound remediation completed;
- is current when the retest is registered;
- has deterministic state `met`;
- precedes the retest timestamp.

A `breached` or `incomplete` post-remediation reassessment can bind only a `failed` retest.

Once valid closure evidence has been registered, that closure remains immutable historical evidence. A later report, source-asset, transformation, quality-rule or other governed change may make the **current reporting state** require revalidation, but it does not retroactively erase a valid historical remediation/retest closure.

## Dossier semantics

The v0.2 dossier adds a `reporting` domain snapshot over all reporting artifacts while preserving the six v0.1 foundation domains.

The dossier propagates current reporting conditions including:

- missing report metrics;
- missing assessments;
- breached or incomplete current assessments;
- stale current metric/assessment evidence;
- missing, rejected, escalated or conflicting latest owner attestations;
- open remediation/retest findings.

The offline verifier separately validates historical evidence and current-state assertions. It recomputes timeliness, completeness and reconciliation controls from embedded report thresholds and production observations and rejects rehashed forged `met` evidence.

## Non-claims

DataGovOps v0.2 does not by itself establish:

- BCBS 239 compliance;
- regulatory-report correctness or filing status;
- legal/regulatory applicability of a report;
- financial-statement accuracy;
- objective real-world data accuracy or completeness;
- adequacy of institution-selected thresholds;
- regulator or supervisor acceptance;
- production fitness.
