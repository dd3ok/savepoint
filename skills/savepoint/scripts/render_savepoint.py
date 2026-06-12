#!/usr/bin/env python3
"""Render and finalize a deterministic SAVEPOINT.md from compact JSON input."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from savepoint_contract import DEFAULT_OUTPUT, collect_snapshot, extract_marker_values, find_git_root, render_marker_block
from validate_savepoint import SECRET_PATTERNS, is_redacted_secret_match, scan_secret_patterns


REQUIRED_TEXT_FIELDS = [
    "goal",
    "current_state",
    "next_action",
]
MAX_VALUE_CHARS = 600
PROJECT_VALIDATION_STATUSES = {
    "passed",
    "failed-expected",
    "failed-blocking",
    "not-run-justified",
    "not-run-unknown",
}
PROJECT_VALIDATION_NEXT_REQUIRED = {"failed-expected", "not-run-justified"}
CLEAR_BLOCKER_VALUES = {"none", "no", "not-needed", "not needed"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON file with semantic savepoint input.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Savepoint path to write (default: .savepoint/SAVEPOINT.md).",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    parser.add_argument(
        "--assert-no-active-commands",
        action="store_true",
        help="Assert no active shell/process output needs to be captured before resume.",
    )
    parser.add_argument(
        "--scan-redaction",
        action="store_true",
        help="Scan rendered text for secret patterns before marking redaction checked.",
    )
    parser.add_argument(
        "--run-savepoint-validation",
        action="store_true",
        help="Run validate_savepoint.py after writing the final artifact.",
    )
    return parser.parse_args(argv)


def read_input(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"failed to read input JSON: {exc}"
    if not isinstance(data, dict):
        return None, "input JSON must be an object"
    return data, None


def clean_text(value: Any, *, fallback: str = "not recorded") -> str:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split())
    if not text:
        return fallback
    if len(text) > MAX_VALUE_CHARS:
        return f"{text[:MAX_VALUE_CHARS].rstrip()}..."
    return text


def list_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item, fallback="").strip() for item in value if clean_text(item, fallback="").strip()]
    text = clean_text(value, fallback="")
    return [text] if text else []


def unresolved_blockers_text(data: dict[str, Any]) -> str:
    values = [clean_text(data.get(key), fallback="") for key in ("unresolved_blockers", "blockers")]
    recorded = [value for value in values if value]
    blocking = [value for value in recorded if value.lower() not in CLEAR_BLOCKER_VALUES]
    if blocking:
        return "; ".join(blocking)
    return "none"


def project_validation_command_entries(value: Any) -> list[str]:
    entries: list[str] = []
    if not isinstance(value, list):
        return entries
    for item in value:
        if not isinstance(item, dict):
            continue
        command = clean_text(item.get("command"), fallback="unrecorded command")
        result = clean_text(item.get("result"), fallback="unrecorded result")
        summary = clean_text(item.get("summary"), fallback="no summary")
        entries.append(f"{result}: `{command}` - {summary}")
    return entries


def project_validation_passed(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            continue
        result = clean_text(item.get("result"), fallback="").lower()
        summary = clean_text(item.get("summary"), fallback="").lower()
        combined = f"{result} {summary}"
        if re.search(r"\b(pass|passed|ok|success|succeeded)\b", combined) and not re.search(
            r"\b(fail|failed|error|not-run|not run|skipped)\b",
            combined,
        ):
            return True
    return False


def normalize_project_validation_status(value: Any) -> str:
    status = clean_text(value, fallback="").lower().replace("_", "-")
    if status in PROJECT_VALIDATION_STATUSES:
        return status
    if re.search(r"\b(pass|passed|ok|success|succeeded)\b", status) and not re.search(
        r"\b(fail|failed|error|not-run|not run|skipped)\b",
        status,
    ):
        return "passed"
    if re.search(r"\b(fail|failed|error)\b", status):
        return "failed-blocking"
    if re.search(r"\b(not-run|not run|skipped)\b", status):
        return "not-run-unknown"
    return "not-run-unknown"


def project_validation_posture(data: dict[str, Any]) -> dict[str, Any]:
    validation = data.get("validation")
    project = validation.get("project") if isinstance(validation, dict) else None
    if isinstance(project, dict):
        status = normalize_project_validation_status(project.get("status"))
        commands = project_validation_command_entries(project.get("commands"))
        reason = clean_text(project.get("reason"), fallback="")
        next_validation = clean_text(
            project.get("next_validation", project.get("next_command", project.get("next"))),
            fallback="",
        )
        return {
            "status": status,
            "commands": commands,
            "reason": reason,
            "next_validation": next_validation,
            "source": "validation.project",
        }

    legacy = data.get("project_validation")
    commands = project_validation_command_entries(legacy)
    next_validation = clean_text(data.get("skipped_checks_next_validation"), fallback="")
    if not commands:
        return {
            "status": "not-run-unknown",
            "commands": [],
            "reason": "",
            "next_validation": next_validation,
            "source": "legacy",
        }
    if project_validation_passed(legacy):
        return {
            "status": "passed",
            "commands": commands,
            "reason": "",
            "next_validation": next_validation,
            "source": "legacy",
        }

    combined = " ".join(commands).lower()
    if re.search(r"\b(not-run|not run|skipped)\b", combined):
        reason = clean_text(commands[0], fallback="")
        return {
            "status": "not-run-justified" if reason and next_validation else "not-run-unknown",
            "commands": commands,
            "reason": reason,
            "next_validation": next_validation,
            "source": "legacy",
        }
    return {
        "status": "failed-blocking",
        "commands": commands,
        "reason": clean_text(commands[0], fallback="project validation failed"),
        "next_validation": next_validation,
        "source": "legacy",
    }


def project_validation_entries(data: dict[str, Any]) -> list[str]:
    posture = project_validation_posture(data)
    status = posture["status"]
    commands = posture["commands"]
    reason = posture["reason"]
    if status == "passed":
        return commands
    if commands:
        return [f"{status}: {entry}" for entry in commands]
    if reason:
        return [f"{status}: {reason}"]
    if status == "not-run-unknown":
        return ["not-run-unknown: no project validation reason or next validation recorded"]
    return [f"{status}: project validation status recorded without command details"]


def project_validation_recorded(posture: dict[str, Any]) -> bool:
    status = posture["status"]
    if status == "passed":
        return bool(posture["commands"])
    if status == "failed-blocking":
        return bool(posture["commands"] or posture["reason"])
    if status == "failed-expected":
        return bool(posture["reason"] and posture["next_validation"])
    if status == "not-run-justified":
        return bool(posture["reason"] and posture["next_validation"])
    return False


def observable_completion(data: dict[str, Any]) -> str:
    explicit = clean_text(data.get("observable_completion"), fallback="")
    if explicit:
        return explicit
    return "next action completed and recorded validation remains passing"


def next_action_text(data: dict[str, Any]) -> str:
    return clean_text(data.get("smallest_next_step"), fallback=clean_text(data.get("next_action")))


def git_status_lines(cwd: Path) -> list[str]:
    git_root = find_git_root(cwd)
    if not git_root:
        return []
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=git_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0 or not result.stdout:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def status_path(line: str) -> str:
    if len(line) > 2 and line[2] == " ":
        path = line[3:].strip()
    elif len(line) > 2:
        path = line[2:].strip()
    else:
        path = line.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path


def derive_change_manifest(cwd: Path, data: dict[str, Any], ignored_paths: set[str] | None = None) -> dict[str, list[str]]:
    ignored_paths = ignored_paths or set()
    changed: list[str] = []
    created: list[str] = []
    deleted: list[str] = []
    moved: list[str] = []
    staged: list[str] = []
    for line in git_status_lines(cwd):
        code = line[:2]
        path = status_path(line)
        if not path or path.replace("\\", "/") in ignored_paths:
            continue
        index_status, worktree_status = code[0], code[1]
        if "R" in code:
            moved.append(f"{path} - renamed")
        elif "D" in code:
            deleted.append(f"{path} - deleted")
        elif "A" in code or code == "??":
            created.append(f"{path} - {'untracked' if code == '??' else 'added'}")
        elif any(status in {"M", "T", "U"} for status in code):
            changed.append(f"{path} - modified")
        if index_status not in {" ", "?"}:
            staged.append(f"{path} - staged {index_status}")
        if worktree_status not in {" ", "?"} and code != "??" and index_status not in {" ", worktree_status}:
            changed.append(f"{path} - worktree {worktree_status}")

    return {
        "changed": unique_or_input(changed, data.get("changed_files")),
        "created": unique_or_input(created, data.get("created_files")),
        "deleted": unique_or_input(deleted, data.get("deleted_files")),
        "moved": unique_or_input(moved, data.get("moved_files")),
        "staged": unique_or_input(staged, data.get("staged_files")),
        "inspected": list_items(data.get("inspected_without_change")),
    }


def unique_or_input(derived: list[str], fallback_value: Any) -> list[str]:
    items = derived or list_items(fallback_value)
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def inline_or_block(items: list[str], *, empty: str = "none") -> str:
    if not items:
        return empty
    if len(items) == 1 and len(items[0]) <= 120:
        return items[0]
    return "\n" + "\n".join(f"  - {item}" for item in items)


def ignored_status_paths(cwd: Path, *paths: Path) -> set[str]:
    git_root = find_git_root(cwd)
    if not git_root:
        return set()
    ignored: set[str] = set()
    for path in paths:
        absolute = path if path.is_absolute() else cwd / path
        try:
            relative = absolute.resolve().relative_to(git_root.resolve())
        except ValueError:
            continue
        ignored.add(relative.as_posix())
    return ignored


def blockers_for(data: dict[str, Any], args: argparse.Namespace, redaction_ok: bool) -> list[str]:
    blockers: list[str] = []
    for field in REQUIRED_TEXT_FIELDS:
        if clean_text(data.get(field), fallback="") == "":
            blockers.append(f"missing-{field.replace('_', '-')}")
    unresolved = unresolved_blockers_text(data).lower()
    if unresolved not in CLEAR_BLOCKER_VALUES:
        blockers.append("unresolved-blockers-recorded")
    if not args.assert_no_active_commands:
        blockers.append("active-commands-not-asserted")
    if not args.scan_redaction:
        blockers.append("redaction-check-not-run")
    elif not redaction_ok:
        blockers.append("redaction-check-failed")
    posture = project_validation_posture(data)
    if posture["status"] == "not-run-unknown":
        blockers.append("validation-not-run-unknown")
    elif posture["status"] == "failed-blocking":
        blockers.append("validation-failed-blocking")
    elif posture["status"] in PROJECT_VALIDATION_NEXT_REQUIRED:
        if not posture["reason"]:
            blockers.append("validation-reason-missing")
        if not posture["next_validation"]:
            blockers.append("validation-next-command-missing")
    elif posture["status"] == "passed" and not posture["commands"]:
        blockers.append("validation-command-missing")
    if not args.run_savepoint_validation:
        blockers.append("savepoint-validation-not-run")
    return unique_or_input(blockers, None)


def marker_block(output_path: Path, values: dict[str, str]) -> str:
    return render_marker_block({
        "SAVEPOINT_PATH": str(output_path.resolve()),
        "SAVEPOINT_MODE": "file",
        "DETAILS_READY": values.get("DETAILS_READY", "not-needed"),
        "PROMPT_READY": "yes",
        "DISK_RECORDED": values.get("DISK_RECORDED", "yes"),
        "VALIDATION_RECORDED": values.get("VALIDATION_RECORDED", "no"),
        "REDACTION_CHECKED": values.get("REDACTION_CHECKED", "no"),
        "RESUME_READY": values.get("RESUME_READY", "no"),
        "BLOCKERS": values.get("BLOCKERS", "not-ready"),
    })


def build_savepoint(
    output_path: Path,
    data: dict[str, Any],
    args: argparse.Namespace,
    *,
    redaction_ok: bool,
    validation_status: str,
    force_unsafe_blocker: str | None = None,
) -> str:
    cwd = Path.cwd()
    snapshot = collect_snapshot(cwd)
    changes = derive_change_manifest(cwd, data, ignored_status_paths(cwd, output_path, args.input))
    project_posture = project_validation_posture(data)
    project_entries = project_validation_entries(data)
    blockers = blockers_for(data, args, redaction_ok)
    if force_unsafe_blocker:
        blockers = unique_or_input([force_unsafe_blocker, *blockers], None)
    resume_ready = not blockers
    marker_values = {
        "DETAILS_READY": "not-needed",
        "DISK_RECORDED": "yes" if snapshot["git_root"] != "not a git repository" else "no",
        "VALIDATION_RECORDED": "yes" if args.run_savepoint_validation and project_validation_recorded(project_posture) else "no",
        "REDACTION_CHECKED": "yes" if args.scan_redaction and redaction_ok else "no",
        "RESUME_READY": "yes" if resume_ready else "no",
        "BLOCKERS": "none" if resume_ready else ",".join(blockers),
    }
    instruction_files = list_items(data.get("instruction_files_loaded")) or discover_instruction_files(cwd)
    durable_files = list_items(data.get("durable_state_files_checked"))
    files_first = list_items(data.get("files_to_inspect_first")) or first_paths(changes)
    skipped = clean_text(
        project_posture["next_validation"] or data.get("skipped_checks_next_validation"),
        fallback="no skipped checks; rerun recorded project validation if state changes",
    )
    expected_drift = clean_text(data.get("expected_drift"), fallback="none")
    unknown_unverified = clean_text(data.get("unknown_unverified"), fallback="none")
    if not resume_ready and force_unsafe_blocker:
        validation_status = validation_status or "not-run: renderer marked artifact unsafe before final validation"

    return f"""# Savepoint Manifest

Generated deterministic final savepoint.

## TL;DR / Operational Summary

- Goal: {clean_text(data.get("goal"))}
- Current state: {clean_text(data.get("current_state"))}
- Next action: {next_action_text(data)}
- Blocker: {"none" if resume_ready else ", ".join(blockers)}

## Repo Snapshot

- Captured at: {snapshot["captured_at"]}
- Working directory: {snapshot["working_directory"]}
- Git root: {snapshot["git_root"]}
- Branch: {snapshot["branch"]}
- Short HEAD: {snapshot["short_head"]}
- `git status --short`: {snapshot["status"]}
- `git diff --stat`: {snapshot["diff_stat"]}
- `git diff --name-status`: {snapshot["diff_name_status"]}
- `git diff --cached --stat`: {snapshot["cached_stat"]}
- `git diff --cached --name-status`: {snapshot["cached_name_status"]}
- Latest commit: {snapshot["latest_commit"]}
- Instruction files loaded: {inline_or_block(instruction_files)}
- Durable state files checked: {inline_or_block(durable_files)}
- Expected drift from captured state: {expected_drift}

## Required Reading

1. Instruction files: {inline_or_block(instruction_files)}
2. Durable state files: {inline_or_block(durable_files)}
3. `SAVEPOINT.md` sections: all
4. Focused detail artifacts, if any: none
5. Files to inspect first: {inline_or_block(files_first)}

Relative detail paths resolve from this file.

## Change Manifest

- Changed: {inline_or_block(changes["changed"])}
- Created: {inline_or_block(changes["created"])}
- Deleted: {inline_or_block(changes["deleted"])}
- Moved: {inline_or_block(changes["moved"])}
- Staged: {inline_or_block(changes["staged"])}
- Inspected without change: {inline_or_block(changes["inspected"])}
- Unknown or unverified: {unknown_unverified}

## Recovery Notes

- Decisions/rationale: {inline_or_block(list_items(data.get("decisions")), empty="no extra decisions recorded")}
- Risks/pitfalls: {inline_or_block([*list_items(data.get("risks")), "disk state wins if savepoint claims conflict"])}
- Failed approaches: {clean_text(data.get("failed_approaches"), fallback="none")}
- Unresolved questions or approval blockers: {unresolved_blockers_text(data)}
- State-file conflicts: {clean_text(data.get("state_file_conflicts"), fallback="none")}

## Validation Manifest

- Savepoint validation: {validation_status}
- Project validation: {inline_or_block(project_entries, empty="not-run: record project validation or skipped reason")}
- Skipped checks / next validation: {skipped}
- Secret redaction check: {redaction_status(args, redaction_ok)}
- Observable completion criteria: {observable_completion(data)}

## Resume Prompt

```text
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, and compare all claims with disk state. Do not rely on prior chat context unless the user explicitly provides it. Report consistency or conflicts, and continue only if the user requested continuation and RESUME_READY is yes.
```

## Markers

```text
{marker_block(output_path, marker_values)}
```
"""


def discover_instruction_files(cwd: Path) -> list[str]:
    git_root = find_git_root(cwd) or cwd
    names = ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]
    found = [name for name in names if (git_root / name).exists()]
    return found or ["not found after checking AGENTS.md, CLAUDE.md, GEMINI.md"]


def first_paths(changes: dict[str, list[str]]) -> list[str]:
    paths: list[str] = []
    for key in ["changed", "created", "staged"]:
        for item in changes[key]:
            paths.append(item.split(" - ", 1)[0])
    return paths[:5] or ["none"]


def redaction_status(args: argparse.Namespace, redaction_ok: bool) -> str:
    if not args.scan_redaction:
        return "not-run: rerun renderer with --scan-redaction before marking ready"
    if redaction_ok:
        return "passed: rendered SAVEPOINT.md scanned for built-in secret patterns; no matches"
    return "failed: possible secret was redacted; review source input before resume"


def redact_secret_patterns(text: str) -> tuple[str, bool]:
    had_secret = False

    def replace(match: re.Match[str]) -> str:
        nonlocal had_secret
        value = match.group(0)
        if is_redacted_secret_match(value):
            return value
        had_secret = True
        return "<redacted>"

    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, replace, redacted)
    return redacted, not had_secret


def write_output(output_path: Path, text: str) -> tuple[bool, str | None]:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        return False, f"failed to write output: {exc}"
    return True, None


def validate_output(output_path: Path) -> tuple[bool, str]:
    validator = Path(__file__).resolve().parent / "validate_savepoint.py"
    result = subprocess.run(
        [sys.executable, str(validator), str(output_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout.strip() or result.stderr.strip()).replace("\n", "; ")
    return result.returncode == 0, output or "validator produced no output"


def output_path_from_args(args: argparse.Namespace) -> Path:
    output_path = args.output
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    return output_path


def preflight_output(output_path: Path, force: bool) -> str | None:
    if output_path.exists() and output_path.is_dir():
        return f"output path is a directory: {output_path}"
    if output_path.name != "SAVEPOINT.md":
        return "output path must end with SAVEPOINT.md"
    if output_path.exists() and not force:
        return f"output already exists: {output_path}\nRe-run with --force to overwrite."
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_path = output_path_from_args(args)
    preflight_error = preflight_output(output_path, args.force)
    if preflight_error:
        print(f"error: {preflight_error}", file=sys.stderr)
        return 1

    data, input_error = read_input(args.input)
    if input_error or data is None:
        print(f"error: {input_error}", file=sys.stderr)
        return 1

    pending_validation_status = (
        "pending: renderer will run final savepoint validation"
        if args.run_savepoint_validation
        else "not-run: renderer was not asked to run savepoint validation"
    )
    initial = build_savepoint(
        output_path,
        data,
        args,
        redaction_ok=True,
        validation_status=pending_validation_status,
    )
    _redacted_initial, no_secret_patterns = redact_secret_patterns(initial)
    redaction_ok = args.scan_redaction and no_secret_patterns
    if args.scan_redaction and not redaction_ok:
        rendered = build_savepoint(
            output_path,
            data,
            args,
            redaction_ok=False,
            validation_status="not-run: redaction check failed before ready finalization",
        )
        rendered, _ = redact_secret_patterns(rendered)
    else:
        rendered = build_savepoint(
            output_path,
            data,
            args,
            redaction_ok=redaction_ok,
            validation_status=pending_validation_status,
        )
        rendered, _ = redact_secret_patterns(rendered)

    wrote, write_error = write_output(output_path, rendered)
    if not wrote:
        print(f"error: {write_error}", file=sys.stderr)
        return 1

    validation_ok = True
    validation_output = "not-run: renderer was not asked to run savepoint validation"
    if args.run_savepoint_validation:
        validation_ok, validation_output = validate_output(output_path)
        if not validation_ok:
            safe_text = build_savepoint(
                output_path,
                data,
                args,
                redaction_ok=redaction_ok,
                validation_status=f"failed: {validation_output}",
                force_unsafe_blocker="savepoint-validation-failed",
            )
            safe_text, _ = redact_secret_patterns(safe_text)
            write_output(output_path, safe_text)

    if args.run_savepoint_validation and validation_ok:
        final_text = build_savepoint(
            output_path,
            data,
            args,
            redaction_ok=redaction_ok,
            validation_status=f"passed: {validation_output}",
        )
        final_text, _ = redact_secret_patterns(final_text)
        write_output(output_path, final_text)
        final_validation_ok, final_validation_output = validate_output(output_path)
        if not final_validation_ok:
            safe_text = build_savepoint(
                output_path,
                data,
                args,
                redaction_ok=redaction_ok,
                validation_status=f"failed: {final_validation_output}",
                force_unsafe_blocker="savepoint-validation-failed",
            )
            safe_text, _ = redact_secret_patterns(safe_text)
            write_output(output_path, safe_text)

    final_text = output_path.read_text(encoding="utf-8")
    final_errors: list[str] = []
    scan_secret_patterns(output_path, final_text, final_errors)
    marker_values, marker_errors = extract_marker_values(output_path, final_text)
    final_errors.extend(marker_errors)
    final_ready = marker_values.get("RESUME_READY") == "yes" and not final_errors
    print(f"wrote: {output_path}")
    if final_ready:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
