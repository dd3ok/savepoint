#!/usr/bin/env python3
"""Create a deterministic draft .savepoint/SAVEPOINT.md.

The stub captures mechanical repo facts and fixed savepoint structure so the
agent only has to fill judgment-heavy fields before validation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from savepoint_contract import (
    render_marker_block,
)


DEFAULT_OUTPUT = Path(".savepoint") / "SAVEPOINT.md"
MAX_COMMAND_LINES = 10
MAX_COMMAND_CHARS = 600
MAX_FOCUS_CHARS = 500


def run_command(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return 127, f"command failed: {exc}"
    output = result.stdout.strip() or result.stderr.strip()
    return result.returncode, output


def git_output(args: list[str], cwd: Path) -> str | None:
    code, output = run_command(["git", *args], cwd)
    if code != 0:
        return None
    return output


def compact_output(output: str | None) -> str:
    if output is None:
        return "not available"
    if not output.strip():
        return "none"
    lines = output.splitlines()
    truncated = False
    if len(lines) > MAX_COMMAND_LINES:
        lines = lines[:MAX_COMMAND_LINES]
        truncated = True
    text = "; ".join(line.strip() for line in lines if line.strip())
    if len(text) > MAX_COMMAND_CHARS:
        text = text[:MAX_COMMAND_CHARS].rstrip()
        truncated = True
    if truncated:
        text = f"{text}; ... truncated, rerun command for full output"
    return text or "none"


def find_git_root(cwd: Path) -> Path | None:
    output = git_output(["rev-parse", "--show-toplevel"], cwd)
    if not output:
        return None
    lines = output.splitlines()
    return Path(lines[0]).resolve() if lines else None


def compact_focus(value: str | None) -> str:
    if not value:
        return "<agent-fill>"
    text = " ".join(value.split())
    if not text:
        return "<agent-fill>"
    if len(text) > MAX_FOCUS_CHARS:
        return f"{text[:MAX_FOCUS_CHARS]}..."
    return text


def current_branch(git_cwd: Path) -> str:
    branch = git_output(["branch", "--show-current"], git_cwd)
    if branch and branch.strip():
        return compact_output(branch)
    return compact_output(git_output(["rev-parse", "--abbrev-ref", "HEAD"], git_cwd))


def collect_snapshot(cwd: Path) -> dict[str, str]:
    git_root = find_git_root(cwd)
    git_cwd = git_root or cwd
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "working_directory": str(cwd.resolve()),
        "git_root": str(git_root) if git_root else "not a git repository",
        "branch": current_branch(git_cwd) if git_root else "not available",
        "short_head": compact_output(git_output(["rev-parse", "--short", "HEAD"], git_cwd)) if git_root else "not available",
        "status": compact_output(git_output(["status", "--short"], git_cwd)) if git_root else "not available",
        "diff_stat": compact_output(git_output(["diff", "--stat"], git_cwd)) if git_root else "not available",
        "diff_name_status": compact_output(git_output(["diff", "--name-status"], git_cwd)) if git_root else "not available",
        "cached_stat": compact_output(git_output(["diff", "--cached", "--stat"], git_cwd)) if git_root else "not available",
        "cached_name_status": compact_output(git_output(["diff", "--cached", "--name-status"], git_cwd)) if git_root else "not available",
        "latest_commit": compact_output(git_output(["log", "-1", "--oneline"], git_cwd)) if git_root else "not available",
    }


def marker_block(output_path: Path, *, disk_recorded: bool) -> str:
    return render_marker_block({
        "SAVEPOINT_PATH": str(output_path.resolve()),
        "SAVEPOINT_MODE": "file",
        "DETAILS_READY": "not-needed",
        "PROMPT_READY": "yes",
        "DISK_RECORDED": "yes" if disk_recorded else "no",
        "VALIDATION_RECORDED": "no",
        "REDACTION_CHECKED": "no",
        "RESUME_READY": "no",
        "BLOCKERS": "draft-needs-agent-review",
    })


def build_savepoint(output_path: Path, focus: str | None) -> str:
    cwd = Path.cwd()
    snapshot = collect_snapshot(cwd)
    disk_recorded = snapshot["git_root"] != "not a git repository"
    focus_text = compact_focus(focus)
    return f"""# Savepoint Manifest

Generated deterministic draft. Fill placeholders before `RESUME_READY: yes`.

## TL;DR / Operational Summary

- Goal: <agent-fill>
- Current state: <agent-fill>
- Next action: <agent-fill>
- Blocker: draft-needs-agent-review

## Recovery Contract

- Mode: `file`; resume ready: `no`; blockers: `draft-needs-agent-review`
- Trust order: user instruction, working tree/Git state, repo instructions/state files, `SAVEPOINT.md`, details, explicit prior chat.
- If this savepoint conflicts with disk state, trust disk state and report mismatch before editing.

## Session Target

- Next-session focus: {focus_text}
- Done when: <agent-fill>
- Out of scope: <agent-fill>
- Smallest executable next step: <agent-fill>

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
- Instruction files loaded: not-read by stub; update after reading instructions
- Durable state files checked:
  - none - not-read - update if relevant
- Expected drift from captured state: none

## Required Reading

1. Instruction files: <agent-fill>
2. Durable state files: none - update if relevant
3. `SAVEPOINT.md` sections: all
4. Focused detail artifacts, if any: none
5. Files to inspect first: <agent-fill>

Relative detail paths resolve from this file.

## Change Manifest

- Changed: <agent-fill>
- Created: <agent-fill>
- Deleted: none
- Moved: none
- Staged: <agent-fill>
- Inspected without change: <agent-fill>
- Unknown or unverified: stub placeholders remain

## Recovery Notes

- Decisions/rationale: <agent-fill>
- Risks/pitfalls: <agent-fill>
- Failed approaches: none
- Unresolved questions or approval blockers: draft-needs-agent-review
- State-file conflicts: none

## Validation Manifest

- Savepoint validation: not-run; run `python3 scripts/validate_savepoint.py {output_path}`
- Project validation: not-run; record checks or skipped reason
- Skipped checks / next validation: final artifact review and validation required
- Secret redaction check: not-run; scan generated artifacts before `REDACTION_CHECKED: yes`
- Observable completion criteria: <agent-fill>

## Remaining Work

1. Smallest next step: <agent-fill>
2. Next implementation step: <agent-fill>
3. Validation/cleanup: run savepoint validation after final edits
4. Optional later work: none

## Resume Prompt

```text
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, and compare all claims with disk state. Do not rely on prior chat context unless the user explicitly provides it. Report consistency or conflicts, and continue only if the user requested continuation and RESUME_READY is yes.
```

## Markers

```text
{marker_block(output_path, disk_recorded=disk_recorded)}
```
"""


def write_output(output_path: Path, text: str) -> bool:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        print(f"error: failed to write output: {exc}", file=sys.stderr)
        return False
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Savepoint path to write (default: .savepoint/SAVEPOINT.md).",
    )
    parser.add_argument("--focus", help="Optional next-session focus text to prefill.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_path = args.output
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    if output_path.exists() and output_path.is_dir():
        print(f"error: output path is a directory: {output_path}", file=sys.stderr)
        return 1
    if output_path.name != "SAVEPOINT.md":
        print("error: output path must end with SAVEPOINT.md", file=sys.stderr)
        return 1
    if output_path.exists() and not args.force:
        print(f"error: output already exists: {output_path}", file=sys.stderr)
        print("Re-run with --force to overwrite.", file=sys.stderr)
        return 1
    text = build_savepoint(output_path, args.focus)
    if not write_output(output_path, text):
        return 1
    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
