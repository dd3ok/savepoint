#!/usr/bin/env python3
"""Validate evals/output-contract.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "evals" / "output-contract.json"
REQUIRED_CATEGORIES = {
    "artifact-contract",
    "security-redaction",
    "resume-ready-semantics",
    "token-budget",
    "no-unwanted-files",
    "least-permission",
}
REQUIRED_CASE_IDS = {
    "artifact-file-mode-01",
    "text-mode-no-recovery-01",
    "redaction-secret-01",
    "resume-ready-not-run-justified-01",
    "resume-ready-failed-expected-01",
    "resume-ready-failed-blocking-01",
    "least-permission-01",
}


def validate_contract(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    if data.get("skill_name") != "savepoint":
        errors.append(f"{path}: skill_name must be savepoint")
    if data.get("version") != 1:
        errors.append(f"{path}: version must be 1")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{path}: cases must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    categories: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"{path}: case #{index} must be an object")
            continue
        errors.extend(validate_case(path, index, case))
        case_id = case.get("id")
        category = case.get("category")
        if isinstance(case_id, str):
            if case_id in seen_ids:
                errors.append(f"{path}: duplicate case id: {case_id}")
            seen_ids.add(case_id)
        if isinstance(category, str):
            categories.add(category)

    for category in sorted(REQUIRED_CATEGORIES - categories):
        errors.append(f"{path}: missing category: {category}")
    for case_id in sorted(REQUIRED_CASE_IDS - seen_ids):
        errors.append(f"{path}: missing case id: {case_id}")
    return errors


def validate_case(path: Path, index: int, case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["id", "category", "scenario"]:
        value = case.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path}: case #{index} has invalid {field}")
    must = case.get("must")
    if not isinstance(must, list) or not must:
        errors.append(f"{path}: case #{index} must be a non-empty list")
    elif any(not isinstance(item, str) or not item.strip() for item in must):
        errors.append(f"{path}: case #{index} must entries must be non-empty strings")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)

    errors = validate_contract(args.path)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: output contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
