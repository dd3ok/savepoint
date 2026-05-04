#!/usr/bin/env python3
"""Validate cross-field automation marker semantics."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills" / "new-session-handoff" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from handoff_contract import validate_marker_semantics  # noqa: E402


BASE_VALUES = {
    "HANDOFF_MODE": "compact",
    "DETAIL_ARTIFACTS_READY": "not-needed",
    "DISK_STATE_RECORDED": "yes",
    "VALIDATION_RECORDED": "yes",
    "SECRET_REDACTION_CHECKED": "yes",
    "SAFE_FOR_NEW_SESSION": "yes",
    "BLOCKERS": "none",
}


def expect(name: str, values: dict[str, str], should_pass: bool) -> list[str]:
    merged = {**BASE_VALUES, **values}
    errors = validate_marker_semantics(merged)
    if bool(errors) == should_pass:
        return [f"{name}: expected pass={should_pass}, got errors={errors}"]
    return []


def main() -> int:
    errors: list[str] = []
    errors.extend(expect("safe compact", {}, True))
    errors.extend(
        expect(
            "unsafe expanded with details not ready",
            {
                "HANDOFF_MODE": "expanded",
                "DETAIL_ARTIFACTS_READY": "no",
                "SAFE_FOR_NEW_SESSION": "no",
            },
            True,
        )
    )
    errors.extend(
        expect(
            "safe expanded requires details ready",
            {"HANDOFF_MODE": "expanded", "DETAIL_ARTIFACTS_READY": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe compact still requires not-needed details",
            {"DETAIL_ARTIFACTS_READY": "yes", "SAFE_FOR_NEW_SESSION": "no"},
            False,
        )
    )
    errors.extend(
        expect(
            "unsafe prompt-only still requires not-needed details",
            {
                "HANDOFF_MODE": "prompt-only",
                "DETAIL_ARTIFACTS_READY": "no",
                "SAFE_FOR_NEW_SESSION": "no",
            },
            False,
        )
    )
    errors.extend(
        expect(
            "safe requires no blockers",
            {"BLOCKERS": "waiting-for-user"},
            False,
        )
    )

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: marker semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
