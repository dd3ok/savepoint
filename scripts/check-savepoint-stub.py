#!/usr/bin/env python3
"""Validate deterministic savepoint stub generation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUB_HELPER = ROOT / "skills" / "savepoint" / "scripts" / "create_savepoint_stub.py"
ROOT_HELPER = ROOT / "scripts" / "create_savepoint_stub.py"
VALIDATOR = ROOT / "skills" / "savepoint" / "scripts" / "validate_savepoint.py"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def git(repo: Path, *args: str) -> None:
    result = run(["git", *args], repo)
    require(result.returncode == 0, result.stderr or result.stdout)


def make_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "savepoint@example.invalid")
    git(repo, "config", "user.name", "Savepoint Test")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    (repo / "app.py").write_text("print('draft')\n", encoding="utf-8")
    return repo


def test_portable_helper_writes_valid_draft() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run([sys.executable, str(STUB_HELPER), "--focus", "review the draft"], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "stub helper did not write .savepoint/SAVEPOINT.md")

        text = output.read_text(encoding="utf-8")
        require("Generated deterministic draft." in text, "draft origin note missing")
        require("- Next-session focus: review the draft" in text, "focus was not written")
        require("- `git status --short`: ?? app.py" in text, "git status snapshot missing")
        require("SAVEPOINT_MODE: file" in text, "file marker missing")
        require("RESUME_READY: no" in text, "draft must not be resume-ready")
        require("BLOCKERS: draft-needs-agent-review" in text, "draft blocker missing")
        require(text.rstrip().endswith("END_SAVEPOINT_V1\n```"), "marker block must be final")

        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_refuses_overwrite_without_force() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        first = run([sys.executable, str(STUB_HELPER)], repo)
        require(first.returncode == 0, first.stderr or first.stdout)
        second = run([sys.executable, str(STUB_HELPER)], repo)
        require(second.returncode != 0, "stub helper overwrote without --force")
        require("output already exists" in second.stderr, "overwrite refusal message missing")

        forced = run([sys.executable, str(STUB_HELPER), "--force"], repo)
        require(forced.returncode == 0, forced.stderr or forced.stdout)
        require(output.exists(), "forced write removed output")


def test_root_wrapper_forwards_to_portable_helper() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / "custom" / "SAVEPOINT.md"
        result = run([sys.executable, str(ROOT_HELPER), "--output", str(output)], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "root wrapper did not write requested output")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def main() -> int:
    tests = [
        test_portable_helper_writes_valid_draft,
        test_refuses_overwrite_without_force,
        test_root_wrapper_forwards_to_portable_helper,
    ]
    for test in tests:
        test()
        print(f"ok: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
