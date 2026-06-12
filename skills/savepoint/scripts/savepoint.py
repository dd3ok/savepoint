#!/usr/bin/env python3
"""Unified savepoint CLI for create, validate, inspect, and text handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import render_savepoint
import validate_savepoint
from render_savepoint import clean_text, next_action_text, read_input, redact_secret_patterns
from savepoint_contract import extract_marker_values


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    save = subcommands.add_parser("save", help="Create or refresh a file savepoint.")
    save.add_argument("--input", required=True, type=Path, help="JSON file with semantic savepoint input.")
    save.add_argument("--output", type=Path, help="Savepoint path to write.")
    save.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    save.add_argument(
        "--assert-no-active-commands",
        action="store_true",
        help="Assert no active shell/process output needs to be captured before resume.",
    )
    save.add_argument("--scan-redaction", action="store_true", help="Scan generated text for secret patterns.")
    save.add_argument("--validate", action="store_true", help="Run bundled savepoint validation after writing.")
    save.add_argument(
        "--run-savepoint-validation",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    validate = subcommands.add_parser("validate", help="Validate SAVEPOINT.md artifacts.")
    validate.add_argument(
        "--allow-example-paths",
        action="store_true",
        help="Allow example SAVEPOINT_PATH values that do not exist on this machine.",
    )
    validate.add_argument("savepoints", nargs="+", type=Path)

    inspect = subcommands.add_parser("inspect", help="Inspect the final SAVEPOINT_V1 marker.")
    inspect.add_argument("savepoint", type=Path)
    inspect.add_argument("--json", action="store_true", help="Emit marker values as JSON.")

    text = subcommands.add_parser("text", help="Print response-only handoff text without writing SAVEPOINT.md.")
    text.add_argument("--input", required=True, type=Path, help="JSON file with semantic savepoint input.")

    return parser.parse_args(argv)


def render_save_argv(args: argparse.Namespace) -> list[str]:
    argv = ["--input", str(args.input)]
    if args.output is not None:
        argv.extend(["--output", str(args.output)])
    if args.force:
        argv.append("--force")
    if args.assert_no_active_commands:
        argv.append("--assert-no-active-commands")
    if args.scan_redaction:
        argv.append("--scan-redaction")
    if args.validate or args.run_savepoint_validation:
        argv.append("--run-savepoint-validation")
    return argv


def run_validate(args: argparse.Namespace) -> int:
    argv: list[str] = []
    if args.allow_example_paths:
        argv.append("--allow-example-paths")
    argv.extend(str(path) for path in args.savepoints)
    return validate_savepoint.main(argv)


def run_inspect(args: argparse.Namespace) -> int:
    if not args.savepoint.exists():
        print(f"error: file does not exist: {args.savepoint}", file=sys.stderr)
        return 1
    text = args.savepoint.read_text(encoding="utf-8")
    values, errors = extract_marker_values(args.savepoint, text)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(values, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    for key, value in values.items():
        print(f"{key}: {value}")
    return 0


def run_text(args: argparse.Namespace) -> int:
    data, error = read_input(args.input)
    if error or data is None:
        print(f"error: {error}", file=sys.stderr)
        return 1
    handoff = f"""# Savepoint Text Handoff

Goal: {clean_text(data.get("goal"))}
Current state: {clean_text(data.get("current_state"))}
Next action: {next_action_text(data)}

No file was written.
Repo recovery is not guaranteed.
Use file mode when the next agent must verify disk/Git state from `.savepoint/SAVEPOINT.md`.
"""
    redacted, _ = redact_secret_patterns(handoff)
    print(redacted, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "save":
        return render_savepoint.main(render_save_argv(args))
    if args.command == "validate":
        return run_validate(args)
    if args.command == "inspect":
        return run_inspect(args)
    if args.command == "text":
        return run_text(args)
    print(f"error: unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
