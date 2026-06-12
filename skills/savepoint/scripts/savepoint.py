#!/usr/bin/env python3
"""Unified savepoint CLI for create, validate, inspect, and text handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import render_savepoint
import validate_savepoint
from render_savepoint import (
    clean_text,
    inline_or_block,
    list_items,
    next_action_text,
    project_validation_entries,
    read_input,
    redact_secret_patterns,
    unresolved_blockers_text,
)
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

    init_input = subcommands.add_parser("init-input", help="Write a sample semantic input JSON file.")
    init_input.add_argument(
        "--output",
        type=Path,
        default=Path(".savepoint") / "input.json",
        help="Input JSON path to write.",
    )
    init_input.add_argument("--force", action="store_true", help="Overwrite an existing input file.")

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
    if not args.savepoint.is_file():
        if args.json:
            print(json.dumps(inspect_payload(args.savepoint, {}, [f"file does not exist or is not a file: {args.savepoint}"], []), ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(f"error: file does not exist or is not a file: {args.savepoint}", file=sys.stderr)
        return 2
    try:
        text = args.savepoint.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        if args.json:
            print(json.dumps(inspect_payload(args.savepoint, {}, [f"failed to read file: {exc}"], []), ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(f"error: failed to read file: {exc}", file=sys.stderr)
        return 2
    values, errors = extract_marker_values(args.savepoint, text)
    if not values and any("found 0" in error for error in errors):
        if args.json:
            print(json.dumps(inspect_payload(args.savepoint, values, errors, [], text=text), ensure_ascii=True, indent=2, sort_keys=True))
        else:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
        return 2
    validation_errors = [] if errors else validate_savepoint.validate_savepoint(args.savepoint)
    exit_code = 0 if not errors and not validation_errors else 1
    if args.json:
        print(json.dumps(inspect_payload(args.savepoint, values, errors, validation_errors, text=text), ensure_ascii=True, indent=2, sort_keys=True))
        return exit_code
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
    if validation_errors:
        for error in validation_errors:
            print(f"error: {error}", file=sys.stderr)
    if exit_code != 0:
        return exit_code
    for key, value in values.items():
        print(f"{key}: {value}")
    return 0


def inspect_payload(
    path: Path,
    values: dict[str, str],
    marker_errors: list[str],
    validation_errors: list[str],
    *,
    text: str = "",
) -> dict[str, object]:
    blocker_text = values.get("BLOCKERS", "")
    blockers = [] if blocker_text in {"", "none"} else [item for item in blocker_text.split(",") if item]
    errors = [*marker_errors, *validation_errors]
    marker_valid = bool(values) and not marker_errors
    savepoint_valid = marker_valid and not validation_errors
    project_status = validate_savepoint.project_validation_status(text) if text and marker_valid else "unknown"
    next_validation = validate_savepoint.field_value_or_block(text, "- Skipped checks / next validation:") if text and marker_valid else ""
    return {
        **values,
        "path": str(path),
        "mode": values.get("SAVEPOINT_MODE"),
        "resume_ready": savepoint_valid and values.get("RESUME_READY") == "yes",
        "blockers": blockers or (["marker-invalid"] if marker_errors else []),
        "marker_valid": marker_valid,
        "savepoint_valid": savepoint_valid,
        "details_ready": values.get("DETAILS_READY"),
        "savepoint_validation": "passed" if savepoint_valid else "failed",
        "validation": {
            "project": {
                "status": project_status,
                "next_validation": next_validation,
            }
        },
        "validation_recorded": values.get("VALIDATION_RECORDED") == "yes",
        "redaction_checked": values.get("REDACTION_CHECKED") == "yes",
        "errors": errors,
    }


def run_init_input(args: argparse.Namespace) -> int:
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    if output.exists() and not args.force:
        print(f"error: output already exists: {output}\nRe-run with --force to overwrite.", file=sys.stderr)
        return 1
    sample = {
        "goal": "",
        "current_state": "",
        "next_action": "",
        "focus": "",
        "unresolved_blockers": "none",
        "files_to_inspect_first": [],
        "decisions": [],
        "risks": [],
        "validation": {
            "project": {
                "status": "not-run-unknown",
                "reason": "",
                "commands": [],
                "next_validation": "",
            }
        },
    }
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(sample, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"error: failed to write input JSON: {exc}", file=sys.stderr)
        return 1
    print(f"wrote: {output}")
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
Blockers: {unresolved_blockers_text(data)}
Risks: {inline_or_block(list_items(data.get("risks")), empty="none")}
Files to inspect first: {inline_or_block(list_items(data.get("files_to_inspect_first")), empty="none")}
Relevant artifacts: {inline_or_block(list_items(data.get("relevant_artifacts", data.get("artifacts"))), empty="none")}
Validation: {inline_or_block(project_validation_entries(data), empty="not-run-unknown: no project validation reason or next validation recorded")}

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
    if args.command == "init-input":
        return run_init_input(args)
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
