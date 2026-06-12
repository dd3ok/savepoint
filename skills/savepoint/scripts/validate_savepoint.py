#!/usr/bin/env python3
"""Validate generated SAVEPOINT.md artifacts.

Usage:
  python3 scripts/savepoint.py validate SAVEPOINT.md [more/SAVEPOINT.md ...]
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
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"gh[ousr]_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN .*PRIVATE KEY",
    r"xox[baprs]-[A-Za-z0-9-]+",
    r"ya29\.[A-Za-z0-9_-]+",
    r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._~+/=-]{16,}",
    r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    r"(?i)(api[_-]?key|token|password|secret)\s*=\s*['\"][^'\"]+['\"]",
]
REQUIRED_FILE_SECTIONS = [
    "## TL;DR / Operational Summary",
    "## Repo Snapshot",
    "## Required Reading",
    "## Change Manifest",
    "## Recovery Notes",
    "## Validation Manifest",
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
    "- `git diff --cached --name-status`:",
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
    "- Unresolved questions or approval blockers:",
]
EMPTY_VALUES = {"", "unknown", "tbd", "todo", "n/a?", "?"}
ABSENCE_ONLY_VALUES = {"none", "no", "not-needed", "not needed"}
ABSENCE_ALLOWED_LABELS = {
    "- Blocker:",
    "- `git diff --cached --stat`:",
    "- `git diff --cached --name-status`:",
    "- Durable state files checked:",
    "- Expected drift from captured state:",
    "- Changed:",
    "- Created:",
    "- Deleted:",
    "- Moved:",
    "- Staged:",
    "- Inspected without change:",
    "- Unknown or unverified:",
    "- Failed approaches:",
    "- Unresolved questions or approval blockers:",
    "- State-file conflicts:",
}
PROJECT_VALIDATION_STATUSES = {
    "passed",
    "failed-expected",
    "failed-blocking",
    "not-run-justified",
    "not-run-unknown",
}
PROJECT_VALIDATION_STATUS_ORDER = [
    "failed-expected",
    "failed-blocking",
    "not-run-justified",
    "not-run-unknown",
    "passed",
]
PROJECT_VALIDATION_NEXT_REQUIRED = {"failed-expected", "not-run-justified"}
VALIDATION_FAILURE_RE = re.compile(r"\b(fail|fails|failed|failing|failure|error|errors|not-run|not run|skipped)\b")
NEGATED_FAILURE_RE = re.compile(r"\b(no|zero|0)\s+(failures?|errors?)\b")


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
        if mode == "file" and not allow_example_paths:
            if not marker_file.exists():
                errors.append(f"{path}: SAVEPOINT_PATH does not exist: {marker_path}")
            elif marker_file.resolve() != path.resolve():
                errors.append(f"{path}: SAVEPOINT_PATH points to a different file: {marker_path}")
        elif marker_file.exists() and marker_file.resolve() != path.resolve():
            errors.append(f"{path}: SAVEPOINT_PATH points to a different file: {marker_path}")
    if values.get("REDACTION_CHECKED") == "yes" and "Secret redaction check:" not in text:
        errors.append(f"{path}: REDACTION_CHECKED=yes requires a Secret redaction check entry")
    if (
        values.get("SAVEPOINT_MODE") == "file"
        and values.get("PROMPT_READY") == "yes"
        and not has_resume_prompt_evidence(text)
    ):
        errors.append(
            f"{path}: PROMPT_READY=yes requires "
            "an embedded ## Resume Prompt"
        )

    if mode == "file":
        for section in REQUIRED_FILE_SECTIONS:
            if section not in text:
                errors.append(f"{path}: Savepoint missing section {section}")
        for field in REQUIRED_REPO_SNAPSHOT_FIELDS:
            if field not in text:
                errors.append(f"{path}: Savepoint missing repo snapshot field {field}")
        for field in REQUIRED_CHANGE_FIELDS:
            if field not in text:
                errors.append(f"{path}: Savepoint missing change field {field}")
        for field in REQUIRED_VALIDATION_FIELDS:
            if field not in text:
                errors.append(f"{path}: Savepoint missing validation field {field}")
        for field in REQUIRED_RECOVERY_NOTE_FIELDS:
            if field not in text:
                errors.append(f"{path}: Savepoint missing recovery note field {field}")
        if resume_ready == "yes":
            errors.extend(validate_resume_ready_content(path, text))

    details = values.get("DETAILS_READY")
    detail_refs = sorted(set(re.findall(r"`(details/[^`]+\.md)`", text)))
    if mode == "text" and detail_refs:
        errors.append(f"{path}: text mode must not reference detail artifacts")
    if mode == "file":
        if details == "not-needed" and detail_refs:
            errors.append(f"{path}: DETAILS_READY=not-needed must not reference detail artifacts")
        if details == "yes" and not detail_refs:
            errors.append(
                f"{path}: file mode with DETAILS_READY=yes "
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
        *REQUIRED_REPO_SNAPSHOT_FIELDS,
        *REQUIRED_CHANGE_FIELDS,
        *REQUIRED_VALIDATION_FIELDS,
        *REQUIRED_RECOVERY_NOTE_FIELDS,
    ]
    for label in labels:
        value = field_value_or_block(text, label)
        allow_absence = label in ABSENCE_ALLOWED_LABELS
        if label == "- Skipped checks / next validation:":
            allow_absence = project_validation_status(text) == "passed"
        if is_placeholder_value(value, allow_absence=allow_absence):
            errors.append(f"{path}: RESUME_READY=yes requires substantive value for {label}")
    errors.extend(validate_validation_status(path, text))
    if not re.search(r"(?is)(trust (the )?(current )?(working tree|disk state|disk)|disk state wins)", text):
        errors.append(f"{path}: RESUME_READY=yes requires explicit disk-state-wins conflict handling")
    return errors


def validate_validation_status(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    skipped = field_value_or_block(text, "- Skipped checks / next validation:")
    skipped_absent = skipped.strip().strip("`").lower().strip(" .") in ABSENCE_ONLY_VALUES
    status = project_validation_status(text)
    if status == "not-run-unknown":
        errors.append(f"{path}: RESUME_READY=yes cannot use Project validation status not-run-unknown")
    elif status == "failed-blocking":
        errors.append(f"{path}: RESUME_READY=yes cannot use Project validation status failed-blocking")
    elif status == "passed" and passed_validation_has_failure_terms(text):
        errors.append(f"{path}: Project validation status passed cannot include failure terms")
    elif status in PROJECT_VALIDATION_NEXT_REQUIRED:
        if not project_validation_reason_present(text, status):
            errors.append(f"{path}: Project validation status {status} requires a reason")
        if skipped_absent:
            errors.append(
                f"{path}: Project validation status {status} requires a next validation command"
            )
        if status == "failed-expected" and not project_validation_command_evidence_present(text):
            errors.append(
                f"{path}: Project validation status failed-expected requires command evidence"
            )
    return errors


def passed_validation_has_failure_terms(text: str) -> bool:
    value = project_validation_value(text).lower().replace("_", "-")
    if "passed" not in value:
        return False
    return contains_blocking_failure(value)


def contains_blocking_failure(text: str) -> bool:
    return bool(VALIDATION_FAILURE_RE.search(NEGATED_FAILURE_RE.sub("", text.lower())))


def project_validation_value(text: str) -> str:
    value = field_value_or_block(text, "- Project validation:")
    lines = [re.sub(r"^\s*-\s*", "", line.strip()) for line in value.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def project_validation_body(text: str, status: str) -> str:
    value = project_validation_value(text)
    return re.sub(rf"(?is)^\s*`?{re.escape(status)}`?\s*[:\-]?\s*", "", value, count=1).strip()


def project_validation_command_evidence_present(text: str) -> bool:
    value = NEGATED_FAILURE_RE.sub("", project_validation_body(text, "failed-expected").lower())
    return bool(
        re.search(
            r"\b(fail|fails|failed|failing|failure|error|errors)\b\s*:\s*`[^`]+`\s+-\s*\S",
            value,
        )
    )


def project_validation_reason_present(text: str, status: str) -> bool:
    body = project_validation_body(text, status)
    if status == "failed-expected":
        match = re.search(r"(?is)(?:^|[;\n])\s*reason\s*:\s*(.+)", body)
        if not match:
            return False
        reason = match.group(1).strip(" :-`\n\t")
        return not is_placeholder_value(reason, allow_absence=False)
    reason = body.strip(" :-`\n\t")
    return not is_placeholder_value(reason, allow_absence=False)


def project_validation_status(text: str) -> str:
    value = project_validation_value(text).lower().replace("_", "-")
    lead = value.strip().splitlines()[0] if value.strip() else ""
    for status in PROJECT_VALIDATION_STATUS_ORDER:
        if re.match(rf"^`?{re.escape(status)}\b", lead):
            return status
    if re.search(r"\b(pass|passed|ok|success|succeeded)\b", lead) and not contains_blocking_failure(lead):
        return "passed"
    if re.search(r"\b(fail|fails|failed|failing|failure|error|errors)\b", NEGATED_FAILURE_RE.sub("", lead)):
        return "failed-blocking"
    if re.search(r"\b(not-run|not run|skipped)\b", lead):
        return "not-run-unknown"
    return "not-run-unknown"


def project_validation_passed(text: str) -> bool:
    return project_validation_status(text) == "passed"


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
            if following.strip() and not following.startswith((" ", "\t")):
                break
            if following.strip():
                value_parts.append(following.strip())
        return "\n".join(value_parts).strip()
    return ""


def is_placeholder_value(value: str, *, allow_absence: bool = False) -> bool:
    normalized = value.strip().strip("`").lower()
    normalized_plain = normalized.strip(" .")
    if normalized in EMPTY_VALUES:
        return True
    if normalized_plain in EMPTY_VALUES:
        return True
    if normalized_plain in ABSENCE_ONLY_VALUES:
        return not allow_absence
    if "<" in value:
        return True
    return False


def scan_secret_patterns(path: Path, text: str, errors: list[str]) -> None:
    for pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            if is_redacted_secret_match(match.group(0)):
                continue
            errors.append(f"{path}: possible unredacted secret matching {pattern}")
            break


def is_redacted_secret_match(value: str) -> bool:
    placeholders = {"<redacted>", "redacted", "***"}
    stripped = value.strip()
    assignment = re.fullmatch(
        r"(?i)(api[_-]?key|token|password|secret)\s*=\s*(['\"])(.*?)\2",
        stripped,
    )
    if assignment:
        return assignment.group(3).strip().lower() in placeholders
    bearer = re.fullmatch(r"(?i)authorization:\s*bearer\s+(.+)", stripped)
    if bearer:
        return bearer.group(1).strip().lower() in placeholders
    return stripped.lower() in placeholders


def has_resume_prompt_evidence(text: str) -> bool:
    return re.search(r"(?m)^## Resume Prompt\s*$", text) is not None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-example-paths",
        action="store_true",
        help="Allow example SAVEPOINT_PATH values that do not exist on this machine.",
    )
    parser.add_argument("savepoints", nargs="+", type=Path)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    errors: list[str] = []
    for path in args.savepoints:
        if not path.is_file():
            errors.append(f"{path}: file does not exist or is not a file")
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
