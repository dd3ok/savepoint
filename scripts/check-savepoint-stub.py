#!/usr/bin/env python3
"""Validate deterministic savepoint stub generation."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUB_HELPER = ROOT / "skills" / "savepoint" / "scripts" / "create_savepoint_stub.py"
ROOT_HELPER = ROOT / "scripts" / "create_savepoint_stub.py"
VALIDATOR = ROOT / "skills" / "savepoint" / "scripts" / "validate_savepoint.py"
HELPER_SCRIPT_DIR = STUB_HELPER.parent
if str(HELPER_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_SCRIPT_DIR))


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def load_stub_helper():
    spec = importlib.util.spec_from_file_location("create_savepoint_stub_under_test", STUB_HELPER)
    require(spec is not None and spec.loader is not None, "could not load stub helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_run_command_handles_oserror() -> None:
    helper = load_stub_helper()
    original_run = helper.subprocess.run

    def raise_oserror(*_args, **_kwargs):
        raise PermissionError("blocked")

    try:
        helper.subprocess.run = raise_oserror
        code, output = helper.run_command(["git", "--version"], ROOT)
    finally:
        helper.subprocess.run = original_run
    require(code == 127, "OSError should be reported as command failure")
    require("command failed:" in output, "OSError failure message missing")


def test_find_git_root_handles_empty_output() -> None:
    helper = load_stub_helper()
    helper.git_output = lambda _args, _cwd: ""
    require(helper.find_git_root(ROOT) is None, "empty git root output should not crash")


def test_refuses_directory_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint"
        output.mkdir()
        result = run([sys.executable, str(STUB_HELPER), "--output", str(output), "--force"], repo)
        require(result.returncode != 0, "stub helper wrote to directory output")
        require("output path is a directory" in result.stderr, "directory refusal message missing")


def test_refuses_savepoint_named_directory_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        output.mkdir(parents=True)
        result = run([sys.executable, str(STUB_HELPER), "--output", str(output), "--force"], repo)
        require(result.returncode != 0, "stub helper wrote to SAVEPOINT.md directory output")
        require("output path is a directory" in result.stderr, "SAVEPOINT.md directory refusal message missing")


def test_refuses_non_savepoint_output_name() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / "foo.md"
        result = run([sys.executable, str(STUB_HELPER), "--output", str(output)], repo)
        require(result.returncode != 0, "stub helper wrote non-SAVEPOINT.md output")
        require("output path must end with SAVEPOINT.md" in result.stderr, "output name refusal message missing")
        require(not output.exists(), "invalid output path should not be written")


def test_reports_parent_mkdir_oserror() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        parent = repo / "not-a-directory"
        parent.write_text("file blocks mkdir\n", encoding="utf-8")
        output = parent / "SAVEPOINT.md"
        result = run([sys.executable, str(STUB_HELPER), "--output", str(output)], repo)
        require(result.returncode != 0, "stub helper wrote through file parent")
        require("failed to write output" in result.stderr, "mkdir failure message missing")
        require("Traceback" not in result.stderr, "mkdir failure should not print traceback")


def test_reports_write_text_oserror() -> None:
    helper = load_stub_helper()

    class Parent:
        def mkdir(self, *, parents: bool, exist_ok: bool) -> None:
            require(parents and exist_ok, "write_output should create parent directories safely")

    class Output:
        parent = Parent()

        def write_text(self, _text: str, *, encoding: str, newline: str) -> None:
            require(encoding == "utf-8", "write_output should use utf-8")
            require(newline == "\n", "write_output should preserve lf newlines")
            raise PermissionError("blocked")

        def __str__(self) -> str:
            return "failing-output"

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        wrote = helper.write_output(Output(), "draft")
    require(not wrote, "write_output should report write_text failure")
    require("failed to write output" in stderr.getvalue(), "write_text failure message missing")


def test_compacts_focus_to_single_line() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        focus = "line one\n## Injected heading\tline three"
        result = run([sys.executable, str(STUB_HELPER), "--focus", focus], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require("- Next-session focus: line one ## Injected heading line three" in text, "focus was not compacted")
        require("\n## Injected heading" not in text, "focus inserted raw markdown heading")


def test_truncates_long_focus() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run([sys.executable, str(STUB_HELPER), "--focus", "x" * 501], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require(f"- Next-session focus: {'x' * 500}..." in text, "long focus was not truncated")


def main() -> int:
    tests = [
        test_portable_helper_writes_valid_draft,
        test_refuses_overwrite_without_force,
        test_root_wrapper_forwards_to_portable_helper,
        test_run_command_handles_oserror,
        test_find_git_root_handles_empty_output,
        test_refuses_directory_output,
        test_refuses_savepoint_named_directory_output,
        test_refuses_non_savepoint_output_name,
        test_reports_parent_mkdir_oserror,
        test_reports_write_text_oserror,
        test_compacts_focus_to_single_line,
        test_truncates_long_focus,
    ]
    for test in tests:
        test()
        print(f"ok: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
