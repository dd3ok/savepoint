#!/usr/bin/env python3
"""Unified savepoint CLI for create, validate, inspect, and text handoff."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
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
    save.add_argument("--input", type=Path, help="JSON file with semantic savepoint input.")
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
        "--delete-input-on-success",
        action="store_true",
        help="After a resume-ready save, delete --input only when it is under .savepoint/.",
    )
    save.add_argument("--goal", help="Direct save input: current goal.")
    save.add_argument("--current-state", help="Direct save input: current state.")
    save.add_argument("--next-action", help="Direct save input: next action.")
    save.add_argument(
        "--project-status",
        choices=sorted(render_savepoint.PROJECT_VALIDATION_STATUSES),
        help="Direct save input: validation.project.status.",
    )
    save.add_argument("--reason", help="Direct save input: project validation reason.")
    save.add_argument("--next-validation", help="Direct save input: next validation command.")
    save.add_argument("--validation-command", help="Direct save input: recorded validation command.")
    save.add_argument("--validation-result", help="Direct save input: recorded validation result.")
    save.add_argument("--validation-summary", help="Direct save input: recorded validation summary.")
    save.add_argument(
        "--files-to-inspect-first",
        nargs="*",
        default=None,
        help="Direct save input: focused paths for the next agent to inspect first.",
    )
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


def render_save_argv(args: argparse.Namespace, input_path: Path) -> list[str]:
    argv = ["--input", str(input_path)]
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


DIRECT_SAVE_FLAG_ATTRS = [
    ("goal", "--goal"),
    ("current_state", "--current-state"),
    ("next_action", "--next-action"),
    ("project_status", "--project-status"),
    ("reason", "--reason"),
    ("next_validation", "--next-validation"),
    ("validation_command", "--validation-command"),
    ("validation_result", "--validation-result"),
    ("validation_summary", "--validation-summary"),
    ("files_to_inspect_first", "--files-to-inspect-first"),
]


def direct_save_flags_present(args: argparse.Namespace) -> list[str]:
    present: list[str] = []
    for attr, flag in DIRECT_SAVE_FLAG_ATTRS:
        if getattr(args, attr) is not None:
            present.append(flag)
    return present


def direct_save_validation_error(args: argparse.Namespace) -> str | None:
    required = [
        ("goal", "--goal"),
        ("current_state", "--current-state"),
        ("next_action", "--next-action"),
        ("project_status", "--project-status"),
    ]
    missing = [flag for attr, flag in required if not clean_text(getattr(args, attr), fallback="").strip()]
    if missing:
        return f"missing required direct save field(s): {', '.join(missing)}"

    validation_fields = [
        ("validation_command", "--validation-command"),
        ("validation_result", "--validation-result"),
        ("validation_summary", "--validation-summary"),
    ]
    validation_present = any(clean_text(getattr(args, attr), fallback="").strip() for attr, _flag in validation_fields)
    validation_missing = [flag for attr, flag in validation_fields if not clean_text(getattr(args, attr), fallback="").strip()]
    status = args.project_status
    if status in {"passed", "failed-expected"} or validation_present:
        if validation_missing:
            return f"missing required direct save field(s): {', '.join(validation_missing)}"
    if status in {"failed-expected", "not-run-justified"}:
        missing_reason = []
        if not clean_text(args.reason, fallback="").strip():
            missing_reason.append("--reason")
        if not clean_text(args.next_validation, fallback="").strip():
            missing_reason.append("--next-validation")
        if missing_reason:
            return f"missing required direct save field(s): {', '.join(missing_reason)}"
    if status == "failed-blocking" and not validation_present and not clean_text(args.reason, fallback="").strip():
        return "missing required direct save field(s): --reason or validation command fields"
    return None


def direct_save_data(args: argparse.Namespace) -> dict[str, object]:
    project: dict[str, object] = {
        "status": args.project_status,
        "reason": args.reason or "",
        "commands": [],
        "next_validation": args.next_validation or "",
    }
    if args.validation_command or args.validation_result or args.validation_summary:
        project["commands"] = [
            {
                "command": args.validation_command or "",
                "result": args.validation_result or "",
                "summary": args.validation_summary or "",
            }
        ]
    return {
        "goal": args.goal,
        "current_state": args.current_state,
        "next_action": args.next_action,
        "unresolved_blockers": "none",
        "files_to_inspect_first": args.files_to_inspect_first or [],
        "validation": {"project": project},
    }


def write_direct_input(args: argparse.Namespace) -> Path:
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".json",
        prefix="savepoint-direct-",
        delete=False,
    )
    with handle:
        json.dump(direct_save_data(args), handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    return Path(handle.name)


def is_under_savepoint_dir(path: Path) -> bool:
    try:
        base = (Path.cwd() / ".savepoint").resolve()
        absolute = path if path.is_absolute() else Path.cwd() / path
        absolute.parent.resolve().relative_to(base)
        resolved = absolute.resolve()
        resolved.relative_to(base)
        return resolved.is_file()
    except (ValueError, OSError, RuntimeError):
        return False


def delete_input_on_success(args: argparse.Namespace, exit_code: int) -> None:
    if not args.delete_input_on_success or args.input is None or exit_code != 0:
        return
    if not is_under_savepoint_dir(args.input):
        return
    input_path = args.input if args.input.is_absolute() else Path.cwd() / args.input
    try:
        input_path.unlink()
    except OSError as exc:
        print(f"warning: failed to delete input JSON: {exc}", file=sys.stderr)


def run_save(args: argparse.Namespace) -> int:
    direct_flags = direct_save_flags_present(args)
    if args.input is not None and direct_flags:
        print(f"error: cannot combine --input with direct save flags: {', '.join(direct_flags)}", file=sys.stderr)
        return 1
    if args.input is None and not direct_flags:
        print("error: save requires --input or direct save flags", file=sys.stderr)
        return 1

    temporary_input: Path | None = None
    input_path = args.input
    if input_path is None:
        direct_error = direct_save_validation_error(args)
        if direct_error:
            print(f"error: {direct_error}", file=sys.stderr)
            return 1
        try:
            input_path = write_direct_input(args)
        except OSError as exc:
            print(f"error: failed to write direct save input: {exc}", file=sys.stderr)
            return 1
        temporary_input = input_path

    try:
        exit_code = render_savepoint.main(render_save_argv(args, input_path))
    finally:
        if temporary_input is not None:
            try:
                temporary_input.unlink()
            except OSError:
                pass

    delete_input_on_success(args, exit_code)
    return exit_code


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
        return run_save(args)
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
