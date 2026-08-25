from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "release" / "release-contract.json"
REPOSITORY_POLICY_PATH = ROOT / "release" / "repository-governance.json"
SCHEMA_DIR = ROOT / "schemas"
WORKFLOW_DIR = ROOT / ".github" / "workflows"
SEMVER_PATTERN = r"^[0-9]+\.[0-9]+\.[0-9]+$"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return payload


def _public_api_fingerprint() -> dict[str, object]:
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    import datagovops

    symbols = list(datagovops.__all__)
    if len(symbols) != len(set(symbols)):
        raise SystemExit("datagovops.__all__ contains duplicate public symbols")
    ordered = sorted(symbols)
    return {"symbol_count": len(ordered), "sha256": _sha256(ordered)}


def _schema_set_fingerprint() -> dict[str, object]:
    entries: list[dict[str, str]] = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    if not entries:
        raise SystemExit("public schema set is empty")
    return {"file_count": len(entries), "sha256": _sha256(entries)}


def compute_fingerprints() -> dict[str, dict[str, object]]:
    return {
        "public_api": _public_api_fingerprint(),
        "schema_set": _schema_set_fingerprint(),
    }


def _verify_action_pins() -> None:
    failures: list[str] = []
    for path in sorted(WORKFLOW_DIR.glob("*.y*ml")):
        source = path.read_text(encoding="utf-8")
        for spec in _USES.findall(source):
            if spec.startswith("./"):
                continue
            if "@" not in spec:
                failures.append(f"{path.relative_to(ROOT)}: action without ref: {spec}")
                continue
            ref = spec.rsplit("@", 1)[1]
            if not _SHA40.fullmatch(ref):
                failures.append(f"{path.relative_to(ROOT)}: action ref is not an exact commit SHA: {spec}")
    if failures:
        raise SystemExit("\n".join(failures))


def _verify_candidate_metadata(manifest: dict) -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    candidate = manifest.get("candidate_version")
    if project.get("version") != candidate:
        raise SystemExit("pyproject version does not match release-contract candidate_version")
    classifiers = project.get("classifiers", [])
    if "Development Status :: 4 - Beta" not in classifiers:
        raise SystemExit("v0.9 release candidate must use the Beta package classifier")

    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    import datagovops

    if datagovops.__version__ != candidate or datagovops.RELEASE_VERSION != candidate:
        raise SystemExit("package and dossier runtime release versions are not aligned with candidate_version")

    dossier_schema = _load_json(SCHEMA_DIR / "governance-dossier.schema.json")
    release_property = dossier_schema["$defs"]["dossier"]["properties"]["release_version"]
    if "const" in release_property or release_property.get("pattern") != SEMVER_PATTERN:
        raise SystemExit("governance-dossier release_version must be package-decoupled before schema freeze")


def _verify_repository_policy(manifest: dict) -> None:
    policy = _load_json(REPOSITORY_POLICY_PATH)
    if policy.get("default_branch") != "main":
        raise SystemExit("repository governance policy must target main")
    if policy.get("enforcement_verified") is not False:
        raise SystemExit("reference governance policy must not claim live enforcement without external evidence")
    if manifest.get("repository_governance_enforcement_verified") is not False:
        raise SystemExit("release contract must preserve unverified repository-governance enforcement state")
    if (WORKFLOW_DIR / "publish-v0.1.0.yml").exists():
        raise SystemExit("stale v0.1 publication workflow must not remain in the release-candidate surface")


def verify() -> dict[str, dict[str, object]]:
    manifest = _load_json(MANIFEST_PATH)
    computed = compute_fingerprints()
    for key in ("public_api", "schema_set"):
        expected = manifest.get(key)
        if not isinstance(expected, dict):
            raise SystemExit(f"release contract is missing {key}")
        if expected.get("sha256") == "PENDING" or expected.get(next(iter(computed[key]))) == 0:
            print(json.dumps(computed, indent=2, sort_keys=True))
            raise SystemExit("release-contract fingerprints are not pinned")
        if expected != computed[key]:
            raise SystemExit(
                f"{key} freeze mismatch: expected {json.dumps(expected, sort_keys=True)}, "
                f"computed {json.dumps(computed[key], sort_keys=True)}"
            )

    if manifest.get("schema_version") != "datagovops.release-contract.v1":
        raise SystemExit("unsupported release-contract schema version")
    if manifest.get("target_stable_version") != "1.0.0":
        raise SystemExit("release contract must target stable version 1.0.0")
    if manifest.get("requires_human_release_decision") is not True:
        raise SystemExit("release candidate must require an explicit human release decision")
    non_claims = manifest.get("non_claims")
    if not isinstance(non_claims, dict) or not non_claims or any(value is not False for value in non_claims.values()):
        raise SystemExit("release-contract non-claims must be explicit false booleans")

    _verify_candidate_metadata(manifest)
    _verify_repository_policy(manifest)
    _verify_action_pins()
    return computed


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit or verify the DataGovOps release-contract freeze.")
    parser.add_argument("--emit", action="store_true", help="print current public-API and schema-set fingerprints")
    parser.add_argument("--verify", action="store_true", help="verify the committed release-contract pins")
    args = parser.parse_args()

    computed = compute_fingerprints()
    if args.emit:
        print(json.dumps(computed, indent=2, sort_keys=True))
        print(f"PUBLIC_API_SYMBOL_COUNT={computed['public_api']['symbol_count']}")
        print(f"PUBLIC_API_SHA256={computed['public_api']['sha256']}")
        print(f"SCHEMA_FILE_COUNT={computed['schema_set']['file_count']}")
        print(f"SCHEMA_SET_SHA256={computed['schema_set']['sha256']}")
        if not args.verify:
            return 0
    verify()
    print(json.dumps(computed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
