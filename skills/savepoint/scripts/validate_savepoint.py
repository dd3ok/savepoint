#!/usr/bin/env python3
"""Validate generated SAVEPOINT.md artifacts.

Usage:
  python3 scripts/validate_savepoint.py SAVEPOINT.md [more/SAVEPOINT.md ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from savepoint_contract import (
    extract_marker_values,
    marker_allowed_values,
    marker_field_order,
    validate_marker_semantics,
)


MARKER_ENUMS = marker_allowed_values()
REQUIRED_FIELDS = marker_field_order()
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"ghp_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN .*PRIVATE KEY",
    r"(?i)(api[_-]?key|token|password|secret)\s*=\s*['\"][^'\"]+['\"]",
]
REQUIRED_VERIFIED_SECTIONS = [
    "## TL;DR / Operational Summary",
    "## Recovery Contract",
    "## Session Target",
    "## Repo Snapshot",
    "## Required Reading",
    "## Change Manifest",
    "## Recovery Notes",
    "## Validation Manifest",
    "## Remaining Work",
    "## Resume Prompt",
    "## Markers",
]
REQUIRED_REPO_SNAPSHOT_FIELDS = [
    "- Working directory:",
    "- Git root:",
    "- Branch:",
    "- Short HEAD:",
    "- `git status --short`:",
    "- `git diff --stat`:",
    "- `git diff --name-status`:",
    "- `git diff --cached --stat`:",
    "- Latest commit:",
    "- Instruction files loaded:",
    "- Durable state files checked:",
    "- Expected drift from captured state:",
]
REQUIRED_CHANGE_FIELDS = [
    "- Changed:",
    "- Created:",
    "- Deleted:",
    "- Moved:",
    "- Staged:",
    "- Inspected without change:",
    "- Unknown or unverified:",
]
REQUIRED_VALIDATION_FIELDS = [
    "- Savepoint validation:",
    "- Project validation:",
    "- Skipped checks / next validation:",
    "- Secret redaction check:",
    "- Observable completion criteria:",
]
REQUIRED_RECOVERY_NOTE_FIELDS = [
    "- Decisions/rationale:",
    "- Risks/pitfalls:",
    "- Failed approaches:",
    "- Unresolved questions or approval blockers:",
]
EMPTY_VALUES = {"", "unknown", "tbd", "todo", "n/a?", "?"}


def validate_savepoint(path: Path, allow_example_paths: bool = False) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    values, marker_errors = extract_marker_values(path, text)
    errors.extend(marker_errors)
    if not values:
        return errors

    for field in REQUIRED_FIELDS:
        if field not in values:
            errors.append(f"{path}: missing marker {field}")
    for field, allowed in MARKER_ENUMS.items():
        value = values.get(field)
        if value is not None and value not in allowed:
            errors.append(f"{path}: marker {field} has invalid value {value!r}")

    for error in validate_marker_semantics(values):
        errors.append(f"{path}: {error}")
    marker_path = values.get("SAVEPOINT_PATH")
    mode = values.get("SAVEPOINT_MODE")
    resume_ready = values.get("RESUME_READY")
    if marker_path and marker_path != "not-written":
        marker_file = Path(marker_path)
        if mode == "verified" and not allow_example_paths:
            if not marker_file.exists():
                errors.append(f"{path}: SAVEPOINT_PATH does not exist: {marker_path}")
            elif marker_file.resolve() != path.resolve():
                errors.append(f"{path}: SAVEPOINT_PATH points to a different file: {marker_path}")
        elif marker_file.exists() and marker_file.resolve() != path.resolve():
            errors.append(f"{path}: SAVEPOINT_PATH points to a different file: {marker_path}")
    if values.get("REDACTION_CHECKED") == "yes" and "Secret redaction check:" not in text:
        errors.append(f"{path}: REDACTION_CHECKED=yes requires a Secret redaction check entry")
    if (
        values.get("SAVEPOINT_MODE") == "verified"
        and values.get("PROMPT_READY") == "yes"
        and not has_resume_prompt_evidence(text)
    ):
        errors.append(
            f"{path}: PROMPT_READY=yes requires "
            "an embedded ## Resume Prompt"
        )

    if mode == "verified":
        for section in REQUIRED_VERIFIED_SECTIONS:
            if section not in text:
                errors.append(f"{path}: verified savepoint missing section {section}")
        for field in REQUIRED_REPO_SNAPSHOT_FIELDS:
            if field not in text:
                errors.append(f"{path}: verified savepoint missing repo snapshot field {field}")
        for field in REQUIRED_CHANGE_FIELDS:
            if field not in text:
                errors.append(f"{path}: verified savepoint missing change field {field}")
        for field in REQUIRED_VALIDATION_FIELDS:
            if field not in text:
                errors.append(f"{path}: verified savepoint missing validation field {field}")
        for field in REQUIRED_RECOVERY_NOTE_FIELDS:
            if field not in text:
                errors.append(f"{path}: verified savepoint missing recovery note field {field}")
        if resume_ready == "yes":
            errors.extend(validate_resume_ready_content(path, text))

    details = values.get("DETAILS_READY")
    detail_refs = sorted(set(re.findall(r"`(details/[^`]+\.md)`", text)))
    if mode == "lightweight" and detail_refs:
        errors.append(f"{path}: lightweight mode must not reference detail artifacts")
    if mode == "verified":
        if details == "not-needed" and detail_refs:
            errors.append(f"{path}: DETAILS_READY=not-needed must not reference detail artifacts")
        if details == "yes" and not detail_refs:
            errors.append(
                f"{path}: verified mode with DETAILS_READY=yes "
                "requires at least one detail artifact reference"
            )
        for rel in detail_refs:
            detail_path = path.parent / rel
            if not detail_path.exists():
                errors.append(f"{path}: referenced detail artifact is missing: {rel}")
            elif values.get("REDACTION_CHECKED") == "yes":
                scan_secret_patterns(detail_path, detail_path.read_text(encoding="utf-8"), errors)

    for field in ["- Goal:", "- Current state:", "- Next action:", "- Blocker:"]:
        if text.count(field) != 1:
            errors.append(f"{path}: expected exactly one TL;DR field {field}")
    scan_secret_patterns(path, text, errors)
    return errors


def validate_resume_ready_content(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    labels = [
        "- Goal:",
        "- Current state:",
        "- Next action:",
        "- Blocker:",
        "- Next-session focus:",
        "- Done when:",
        "- Smallest executable next step:",
        *REQUIRED_REPO_SNAPSHOT_FIELDS,
        *REQUIRED_CHANGE_FIELDS,
        *REQUIRED_VALIDATION_FIELDS,
        *REQUIRED_RECOVERY_NOTE_FIELDS,
    ]
    for label in labels:
        value = field_value_or_block(text, label)
        if is_placeholder_value(value):
            errors.append(f"{path}: RESUME_READY=yes requires substantive value for {label}")
    if not re.search(r"(?is)(trust (the )?(current )?(working tree|disk state|disk)|disk state wins)", text):
        errors.append(f"{path}: RESUME_READY=yes requires explicit disk-state-wins conflict handling")
    return errors


def field_value_or_block(text: str, label: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(label):
            continue
        value_parts = [line[len(label):].strip()]
        for following in lines[index + 1 :]:
            if following.startswith("- ") and not following.startswith("  "):
                break
            if following.startswith("## "):
                break
            if following.strip():
                value_parts.append(following.strip())
        return "\n".join(value_parts).strip()
    return ""


def is_placeholder_value(value: str) -> bool:
    normalized = value.strip().strip("`").lower()
    if normalized in EMPTY_VALUES:
        return True
    if "<" in value:
        return True
    return False


def scan_secret_patterns(path: Path, text: str, errors: list[str]) -> None:
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            errors.append(f"{path}: possible unredacted secret matching {pattern}")


def has_resume_prompt_evidence(text: str) -> bool:
    return re.search(r"(?m)^## Resume Prompt\s*$", text) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-example-paths",
        action="store_true",
        help="Allow example SAVEPOINT_PATH values that do not exist on this machine.",
    )
    parser.add_argument("savepoints", nargs="+", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.savepoints:
        if not path.exists():
            errors.append(f"{path}: file does not exist")
            continue
        errors.extend(validate_savepoint(path, allow_example_paths=args.allow_example_paths))

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    for path in args.savepoints:
        print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
