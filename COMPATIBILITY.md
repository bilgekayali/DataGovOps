# DataGovOps Compatibility Policy

## Frozen v1.0 public contract

DataGovOps v0.9.0 established the release-candidate freeze for the v1.0 stable reference. DataGovOps v1.0.0 promotes that candidate without changing either frozen intentional public contract:

1. the sorted symbol set exported through `datagovops.__all__`;
2. the exact-byte set of public JSON Schemas under `schemas/*.schema.json`.

The committed fingerprints are recorded in `release/release-contract.json` and verified by `tools/release_contract.py`. The stable promotion preserves the v0.9.0 candidate provenance and records `1.0.0` as the current stable release version. A fingerprint change is therefore not an incidental patch to the stable promotion; it is a public-contract evolution that must follow the compatibility rules below.

The governance-dossier schema validates `release_version` as semantic-version metadata rather than hard-coding one package version. Offline/runtime verification remains responsible for binding evidence to the package release being evaluated.

## Stable compatibility after v1.0

DataGovOps follows semantic-versioning principles for its intentional public surface:

- removing or renaming a public Python symbol, changing required call semantics incompatibly, or making a public schema reject documents valid under the prior stable contract requires a new major version;
- backward-compatible additive capabilities belong in a minor version;
- defect fixes that do not intentionally change the public contract belong in a patch version;
- internal modules, underscored helpers, tests, CI implementation details and reference deployment internals are not public API unless separately documented as such.

Schema evolution must preserve explicit non-claims. A schema or API addition must not silently convert represented governance evidence into proof of legal applicability, regulatory compliance, production effectiveness, supervisory acceptance, certification or production fitness.

## CLI

The `datagovops` executable and the current `--version`, `digest`, `schema`, and `dossier verify` command families are supported release surfaces. Their exact textual output is not frozen, but documented command intent and successful machine operation must remain compatible across the v1 stable line unless a new major release states otherwise.

## Release and publication decisions

Passing the stable release gate establishes repository-level consistency with the represented frozen v1.0 contract. The `Production/Stable` package classifier is an ecosystem maturity signal for that contract; it is not proof of production deployment readiness.

Git tags, GitHub Releases, package-registry publication, container publication and production deployment remain separate explicit decisions. None of them is implied by the source-tree version alone. Likewise, stable promotion does not establish regulatory compliance, certification, supervisory acceptance or real-world control effectiveness.
