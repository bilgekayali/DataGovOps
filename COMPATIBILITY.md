# DataGovOps Compatibility Policy

## Release-candidate freeze

DataGovOps v0.9.0 is the release-candidate boundary for the v1.0 stable reference. The candidate freezes two intentional public contracts:

1. the sorted symbol set exported through `datagovops.__all__`;
2. the exact-byte set of public JSON Schemas under `schemas/*.schema.json`.

The committed fingerprints are recorded in `release/release-contract.json` and verified by `tools/release_contract.py`. A change to either fingerprint after the v0.9.0 freeze requires an explicit release-candidate reset and is not treated as an incidental v1.0 promotion change.

`__version__`, package metadata, release notes and other release metadata may advance from `0.9.0` to `1.0.0` without changing the frozen public symbol set. The governance-dossier schema therefore validates `release_version` as semantic-version metadata rather than hard-coding one package version; offline/runtime verification remains responsible for binding evidence to the package release being evaluated.

## Stable compatibility after v1.0

After v1.0.0, DataGovOps follows semantic-versioning principles for its intentional public surface:

- removing or renaming a public Python symbol, changing required call semantics incompatibly, or making a public schema reject documents valid under the prior stable contract requires a new major version;
- backward-compatible additive capabilities belong in a minor version;
- defect fixes that do not intentionally change the public contract belong in a patch version;
- internal modules, underscored helpers, tests, CI implementation details and reference deployment internals are not public API unless separately documented as such.

Schema evolution must preserve explicit non-claims. A schema or API addition must not silently convert represented governance evidence into proof of legal applicability, regulatory compliance, production effectiveness, supervisory acceptance, certification or production fitness.

## CLI

The `datagovops` executable and the current `--version`, `digest`, `schema`, and `dossier verify` command families are supported release surfaces. Their exact textual output is not frozen, but documented command intent and successful machine operation must remain compatible across the v1 stable line unless a major release states otherwise.

## Release decision

Passing the release-candidate gate establishes only repository-level contract consistency for the represented reference implementation. Promotion to v1.0.0 remains an explicit human decision. It does not establish production readiness or regulatory acceptance.
