# Data Quality Governance Invariants

DataGovOps v0.1.4 represents explicit, evidence-backed quality controls. It does not inspect datasets or infer that data is correct from metadata alone.

## Exact targets

- every quality rule binds an exact governed asset version or exact registered CDE designation digest;
- arbitrary data elements cannot be represented as CDE quality targets without a CDE designation;
- newer governed target versions make historical rules non-current for current-state evaluation.

## Rules and observations

- rule versions are contiguous and immutable;
- thresholds, comparison operators, metric names, units, freshness windows and finding severity are explicit institution-owned inputs;
- observations bind exact rule/target digests and a registered source system;
- future observations are not used for earlier evaluation timestamps;
- missing or stale evidence can be `incomplete` or `breached`, never `passed`;
- conflicting observations at the same latest measurement time fail closed as incomplete.

## Findings and closure

- passed evaluations cannot create findings;
- finding severity cannot downgrade or override rule severity;
- remediation cannot predate the finding;
- retest evaluation cannot predate remediation;
- retest outcome must match the bound evaluation state;
- HIGH/CRITICAL findings require a retest reviewer different from the remediation owner;
- finding resolution preserves all remediation/retest digests rather than overwriting history;
- conflicting latest lifecycle evidence fails closed.

## Assurance boundary

Quality state is a deterministic result of represented rules, policies and observations. It does not establish objective accuracy, completeness, fitness for regulatory reporting, BCBS 239 compliance, privacy compliance, security, legal applicability or regulator acceptance.
