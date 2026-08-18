# DataGovOps

**Evidence-backed data governance, lineage, classification, quality, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current development milestone: **v0.1.4 — data quality rules, observations, findings and remediation evidence** (`0.1.0.dev4`).

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, or substitute for accountable data owners, stewards, security/privacy teams, engineers, and legal review.

## Current executable boundary

The authoritative, semantic and lineage layers remain intact. v0.1.4 adds deterministic data-quality governance:

- exact quality targets bound to a governed asset version or explicit Critical Data Element designation;
- versioned `QualityRule` artifacts with accountable owner, dimension, metric/unit, comparison operator, threshold, freshness window and finding severity;
- versioned institution-owned `QualityEvaluationPolicy` controlling missing/stale observation treatment without allowing missing/stale evidence to become PASS;
- immutable `QualityObservation` evidence bound to exact rule/target digests and source-system identity;
- deterministic `passed / breached / incomplete` evaluation with explicit reason codes;
- fail-closed conflicting-latest observation handling;
- findings whose severity cannot silently downgrade the configured rule severity;
- remediation evidence and retest evidence bound to exact finding/evaluation history;
- independent reviewer requirement for HIGH/CRITICAL retest closure;
- deterministic finding resolution with retained remediation/retest evidence history;
- current-state failure when a newer asset/CDE or quality-rule/policy version supersedes the represented state;
- quality snapshots bound to exact authoritative and semantic governance snapshots;
- strict Draft 2020-12 JSON Schemas and Python 3.11/3.12/3.13 CI;
- offline-capability guard, wheel build and clean-wheel smoke.

```text
DataAssetRegistry ───────────┐
                            ├─> QualityRegistry
SemanticGovernanceRegistry ─┘      |
                                   ├─ Rule + EvaluationPolicy
                                   ├─ Observation -> Evaluation
                                   └─ Finding -> Remediation -> Retest -> Resolution
```

A `passed` quality evaluation means only that the selected fresh governed observation satisfied the exact configured rule/threshold at the represented time. It does **not** prove that the data is objectively accurate, complete, fit for regulatory reporting, or BCBS 239 compliant.

## v0.1 foundation sequence

`#3 inventory/accountability ✓ → #4 classification/CDE/purpose ✓ → #5 lineage/provenance ✓ → #6 quality/remediation → #7 access/retention/privacy → #8 dossier/release gate`

The package remains a development build until #8. Completion of #3 through #8 is the proposed **DataGovOps v0.1.0 foundation release**.

## Standards posture

Design mappings are intended to support evidence/control alignment with:

- BCBS 239 risk-data aggregation and reporting governance principles;
- Basel Committee implementation observations on BCBS 239;
- GDPR and KVKK privacy/accountability concepts;
- ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts;
- DAMA-aligned governance concepts;
- relevant BDDK, SPK and institution-owned data-governance requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer data ownership, establish regulatory applicability, or prove that data is accurate simply because metadata or quality evidence is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE assignments;
- correctness of source-of-truth or authoritative-system declarations;
- semantic correctness or completeness of lineage beyond configured explicit requirements;
- correctness of transformation code or configuration merely because digests are bound;
- objective data accuracy, completeness, consistency, timeliness, uniqueness or fitness for regulatory reporting;
- deletion completion or legal-hold satisfaction;
- access authorization sufficiency;
- regulator acceptance or legal applicability.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
