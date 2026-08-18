# DataGovOps

**Evidence-backed data governance, lineage, classification, quality, access, retention, and accountability for regulated financial institutions.**

## Summary

DataGovOps is an open-source reference architecture for governing enterprise data assets through explicit ownership, classification, criticality, lineage, purpose, quality, access, retention, privacy/security obligations, and verifiable evidence.

Current development milestone: **v0.1.5 — access-purpose, retention, legal-hold and privacy/security obligation evidence** (`0.1.0.dev5`).

The project is not a data catalog replacement, privacy-law decision engine, automatic BCBS 239 compliance product, regulatory filing service, IAM/PAM replacement, deletion engine, or substitute for accountable data owners, stewards, security/privacy teams, engineers, and legal review.

## Current executable boundary

The authoritative, semantic, lineage and quality layers remain intact. v0.1.5 adds explicit access/retention/obligation governance:

- versioned `AccessRole` evidence bound to governed principals and permissions;
- explicit `AccessPurposeApproval` evidence bound to an exact subject, asset version, business-purpose version and approved asset-purpose binding;
- `AccessGrant` evidence that cannot exceed governed role permissions and becomes non-current when role, asset, purpose or latest access-purpose decision changes;
- deterministic conflict detection for equally-latest contradictory access-purpose approvals;
- versioned `RetentionSchedule` evidence bound to exact asset versions;
- immutable `LegalHold` plus separate release evidence;
- deterministic deletion-eligibility evaluation where an active hold blocks eligibility;
- deletion eligibility explicitly does **not** represent deletion execution or legal compliance;
- `DataLocationEvidence` with explicit storage/processing/backup/transfer location and cross-border flag;
- privacy/security/data-residency/cross-border obligation mappings with accountable review and exact location-evidence binding;
- cross-border mappings that require explicit represented cross-border location evidence;
- institution-owned `GovernanceControlPolicy` and deterministic missing/stale gap reports;
- stale access grants, retention schedules, obligation mappings and location evidence fail closed in current-state reporting;
- strict Draft 2020-12 JSON Schemas and Python 3.11/3.12/3.13 CI;
- offline-capability guard, wheel build and clean-wheel smoke.

```text
DataAssetRegistry ────────────────┐
                                 ├─> AccessRetentionPrivacyRegistry
SemanticGovernanceRegistry ──────┘          |
                                            ├─ Role -> Purpose Approval -> Grant
                                            ├─ Retention -> Hold/Release -> Eligibility
                                            ├─ Location -> Obligation Mapping
                                            └─ Institution Policy -> Deterministic Gap Report
```

Business-purpose, obligation and location metadata are accountable institutional inputs. They are deliberately **not** converted into GDPR/KVKK lawful-basis determinations or automatic legal/regulatory applicability conclusions.

## v0.1 foundation sequence

`#3 inventory/accountability ✓ → #4 classification/CDE/purpose ✓ → #5 lineage/provenance ✓ → #6 quality/remediation ✓ → #7 access/retention/privacy → #8 dossier/release gate`

The package remains a development build until #8. Completion of #3 through #8 is the proposed **DataGovOps v0.1.0 foundation release**.

## Standards posture

Design mappings are intended to support evidence/control alignment with:

- BCBS 239 risk-data aggregation and reporting governance principles;
- Basel Committee implementation observations on BCBS 239;
- GDPR and KVKK privacy/accountability concepts;
- ISO/IEC 27001 and ISO/IEC 27701 control/evidence concepts;
- DAMA-aligned governance concepts;
- relevant BDDK, SPK and institution-owned data-governance requirements.

These are architecture/design inputs. DataGovOps does not certify compliance, determine lawful basis, infer data ownership, establish regulatory applicability, or prove that data is accurate simply because metadata or governance evidence is present.

## Explicit non-claims

DataGovOps does **not** by itself establish:

- BCBS 239, GDPR, KVKK, BDDK, SPK, ISO/IEC 27001 or ISO/IEC 27701 compliance;
- lawful basis or legal permissibility of a represented business purpose;
- correctness of owner/steward/classification/CDE assignments;
- correctness of source-of-truth or authoritative-system declarations;
- semantic correctness or completeness of lineage beyond configured explicit requirements;
- correctness of transformation code or configuration merely because digests are bound;
- objective data accuracy, completeness, consistency, timeliness, uniqueness or fitness for regulatory reporting;
- sufficiency of an access authorization or IAM enforcement;
- deletion execution, deletion completion, or legal-hold legal sufficiency;
- legal/regulatory applicability of privacy/security obligation mappings;
- regulator acceptance or production fitness.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## License

Apache License 2.0.
