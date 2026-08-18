from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema

from . import __version__
from .dossier_verify import verify_dossier_document
from .models import GovernanceError, digest_artifact


def _load_json(path: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"cannot read valid JSON from {path}: {exc}") from exc


def _cmd_digest(args: argparse.Namespace) -> int:
    document = _load_json(args.document)
    print(digest_artifact(document))
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    schema = _load_json(args.schema)
    document = _load_json(args.document)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(document)
    except jsonschema.exceptions.SchemaError as exc:
        raise GovernanceError(f"invalid Draft 2020-12 schema: {exc.message}") from exc
    except jsonschema.exceptions.ValidationError as exc:
        path = ".".join(str(item) for item in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise GovernanceError(f"schema validation failed{location}: {exc.message}") from exc
    print("valid")
    return 0


def _cmd_dossier_verify(args: argparse.Namespace) -> int:
    document = _load_json(args.document)
    digest = verify_dossier_document(document)
    print(digest)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datagovops")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    digest_parser = subparsers.add_parser("digest", help="compute canonical JSON SHA-256")
    digest_parser.add_argument("document")
    digest_parser.set_defaults(func=_cmd_digest)

    schema_parser = subparsers.add_parser("schema", help="validate JSON with a Draft 2020-12 schema")
    schema_parser.add_argument("schema")
    schema_parser.add_argument("document")
    schema_parser.set_defaults(func=_cmd_schema)

    dossier_parser = subparsers.add_parser("dossier", help="governance dossier operations")
    dossier_subparsers = dossier_parser.add_subparsers(dest="dossier_command", required=True)
    verify_parser = dossier_subparsers.add_parser("verify", help="verify dossier integrity offline")
    verify_parser.add_argument("document")
    verify_parser.set_defaults(func=_cmd_dossier_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (GovernanceError, OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
