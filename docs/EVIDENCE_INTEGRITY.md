# DataGovOps Evidence Integrity Boundary

DataGovOps v0.5 adds an offline evidence-integrity and release-provenance reference boundary over verified governance dossiers.

## Signed governance evidence

The runtime does not own or persist an Ed25519 private signing key. A governance dossier is first verified with the existing offline dossier verifier. DataGovOps then produces a canonical signing statement bound to the exact institution, dossier digest, package release version and dossier source revision. An external institution-controlled signer signs those canonical bytes. Verification requires a separately supplied trusted Ed25519 public key.

The signed statement carries a key reference (`provider`, `key_id`, `key_version`) rather than secret key material. It structurally keeps `legal_compliance_determined=false` and `supervisory_acceptance_determined=false`.

## External immutable anchor and timestamp contract

`ExternalAnchorReceipt` records an institution scope, the exact signed-evidence digest, an external provider/anchor identifier, anchor time and SHA-256 digest of a timestamp token. The reference artifact deliberately keeps both `external_anchor_validated=false` and `trusted_timestamp_validated=false`.

Those flags mean DataGovOps can cross-bind an external receipt without pretending that an external ledger, TSA, notarisation service or timestamp authority has actually been contacted or trusted. Production integration must validate the external service independently.

## Build provenance and SBOM

`BuildProvenance` binds package/version/source revision to exact build subjects and source materials. Reference provenance cannot claim a production build attestation.

The dependency SBOM uses a deterministic CycloneDX-shaped 1.6 profile. It records package identity and explicitly supplied dependency name/version pairs. It does not claim complete transitive dependency inventory or vulnerability assessment.

## Release evidence manifest

`ReleaseEvidenceManifest` binds exact bytes for all represented artifacts using SHA-256 and size. The manifest requires distinct paths for:

- build provenance;
- dependency SBOM;
- signed governance evidence;
- external anchor receipt.

Additional artifacts such as the wheel can be included in the same exact-byte manifest. Verification recomputes every artifact digest/size and cross-checks package/version/source-revision identity between the manifest and provenance plus package identity in the SBOM.

The manifest cannot claim formal release attestation, production readiness or regulatory compliance.

## Security boundary

The evidence-integrity module is intentionally offline. Runtime source contains no Ed25519 private-key API and no network, subprocess or socket capability. CI uses an ephemeral private key only inside tests to demonstrate the external-signature round trip.

## Non-claims

This boundary does not establish:

- authenticity or authority of a signer merely because a signature verifies;
- production custody, rotation or protection of signing keys;
- external immutable-ledger anchoring or trusted timestamp validity;
- completeness of an SBOM or absence of vulnerabilities;
- SLSA certification or production build provenance;
- BCBS 239, GDPR, KVKK, BDDK, SPK or ISO compliance;
- production readiness, regulatory acceptance or supervisory acceptance.
