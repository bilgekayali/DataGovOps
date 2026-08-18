# Access, Retention and Obligation Governance Invariants

DataGovOps v0.1.5 models explicit institution-owned governance evidence. It does not infer legal permission, lawful basis, deletion completion, privacy compliance, or regulatory applicability.

## Access-purpose governance

- access roles are versioned and bound to exact governed principals and permissions;
- purpose approvals bind an exact principal/role, asset version, purpose version and `AssetPurposeBinding` digest;
- grants require an explicit approved purpose decision and cannot exceed governed role permissions;
- newer role, asset, purpose or access-purpose decisions make historical grants non-current;
- contradictory equally-latest approvals fail closed.

## Retention and legal hold

- retention schedules are versioned and bound to exact asset versions;
- deletion eligibility is computed only from the represented retention trigger, retention duration and active hold evidence;
- active legal hold evidence blocks deletion eligibility until explicit release evidence becomes effective;
- deletion eligibility never represents deletion execution or legal compliance.

## Location and obligation mappings

- location evidence is explicit and bound to exact asset versions;
- cross-border status is an authoritative input, not inferred from law or network telemetry;
- privacy/security/residency/cross-border obligation mappings bind accountable review and evidence;
- a represented mapped cross-border obligation requires explicit cross-border location evidence;
- obligation mapping never determines legal/regulatory applicability.

## Gap reporting

Institution-owned `GovernanceControlPolicy` selects which represented controls are required. Deterministic reports surface missing/stale retention, obligation and location evidence plus stale active access grants. A complete report means only that the configured represented governance gaps are absent for that exact snapshot.
