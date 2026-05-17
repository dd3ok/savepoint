#!/usr/bin/env python3
"""Validate generated HANDOFF.md artifacts.

Usage:
  python3 scripts/validate_handoff.py HANDOFF.md [more/HANDOFF.md ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from handoff_contract import (
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


def validate_handoff(path: Path) -> list[str]:
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
    if values.get("SECRET_REDACTION_CHECKED") == "yes" and "Secret redaction check:" not in text:
        errors.append(f"{path}: SECRET_REDACTION_CHECKED=yes requires a Secret redaction check entry")
    if values.get("NEW_SESSION_PROMPT_READY") == "yes" and not has_resume_prompt_evidence(text):
        errors.append(
            f"{path}: NEW_SESSION_PROMPT_READY=yes requires "
            "an embedded ## Resume Prompt"
        )

    details = values.get("DETAIL_ARTIFACTS_READY")
    detail_refs = sorted(set(re.findall(r"`(details/[^`]+\.md)`", text)))
    if values.get("HANDOFF_MODE") in {"compact", "prompt-only"} and detail_refs:
        errors.append(f"{path}: {values.get('HANDOFF_MODE')} mode must not reference detail artifacts")
    if values.get("HANDOFF_MODE") == "expanded" and (
        details == "yes" or values.get("SAFE_FOR_NEW_SESSION") == "yes"
    ):
        if details == "yes" and not detail_refs:
            errors.append(
                f"{path}: expanded mode with DETAIL_ARTIFACTS_READY=yes "
                "requires at least one detail artifact reference"
            )
        for rel in detail_refs:
            if not (path.parent / rel).exists():
                errors.append(f"{path}: referenced detail artifact is missing: {rel}")

    for field in ["- Goal:", "- Current state:", "- Next action:", "- Blocker:"]:
        if text.count(field) != 1:
            errors.append(f"{path}: expected exactly one TL;DR field {field}")
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            errors.append(f"{path}: possible unredacted secret matching {pattern}")
    return errors


def has_resume_prompt_evidence(text: str) -> bool:
    return re.search(r"(?m)^## Resume Prompt\s*$", text) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoffs", nargs="+", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.handoffs:
        if not path.exists():
            errors.append(f"{path}: file does not exist")
            continue
        errors.extend(validate_handoff(path))

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    for path in args.handoffs:
        print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
