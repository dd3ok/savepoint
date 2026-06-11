#!/usr/bin/env python3
"""Validate deterministic savepoint stub generation."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUB_HELPER = ROOT / "skills" / "savepoint" / "scripts" / "create_savepoint_stub.py"
RENDER_HELPER = ROOT / "skills" / "savepoint" / "scripts" / "render_savepoint.py"
ROOT_HELPER = ROOT / "scripts" / "create_savepoint_stub.py"
ROOT_RENDERER = ROOT / "scripts" / "render_savepoint.py"
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


def load_render_helper():
    spec = importlib.util.spec_from_file_location("render_savepoint_under_test", RENDER_HELPER)
    require(spec is not None and spec.loader is not None, "could not load render helper module")
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


def make_repo_with_modified_app(base: Path) -> Path:
    repo = make_repo(base)
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "add app")
    (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
    return repo


def semantic_input(repo: Path) -> Path:
    path = repo / "savepoint-input.json"
    path.write_text(
        """{
  "goal": "finish deterministic savepoint rendering",
  "current_state": "renderer input has enough semantic fields for a recoverable savepoint",
  "next_action": "run the focused validation commands",
  "done_when": "savepoint validation and project validation are both recorded",
  "out_of_scope": "marker schema changes",
  "smallest_next_step": "run python scripts/check-savepoint-stub.py",
  "decisions": ["keep SAVEPOINT_V1 marker fields and order unchanged"],
  "risks": ["disk state can drift after the snapshot is captured"],
  "failed_approaches": "none",
  "unresolved_blockers": "none",
  "project_validation": [
    {
      "command": "python scripts/check-savepoint-stub.py",
      "result": "passed",
      "summary": "renderer fixture validation recorded"
    }
  ],
  "observable_completion": "check-savepoint-stub exits 0",
  "inspected_without_change": ["README.md"],
  "files_to_inspect_first": ["app.py"]
}
""",
        encoding="utf-8",
    )
    return path


def minimal_semantic_input(
    repo: Path,
    *,
    include_project_validation: bool = True,
    validation_result: str = "passed",
    include_next_action: bool = True,
    unresolved_blockers: str | None = None,
) -> Path:
    path = repo / "minimal-savepoint-input.json"
    project_validation = "" if not include_project_validation else """,
  "project_validation": [
    {
      "command": "python scripts/check-savepoint-stub.py",
      "result": "%s",
      "summary": "minimal renderer fixture validation recorded"
    }
  ]""" % validation_result
    next_action = "" if not include_next_action else """,
  "next_action": "run the focused minimal renderer check\""""
    blocker_line = "" if unresolved_blockers is None else f""",
  "unresolved_blockers": "{unresolved_blockers}" """
    path.write_text(
        f"""{{
  "goal": "finish minimal deterministic rendering",
  "current_state": "minimal semantic input should still render recoverable facts"{next_action}{project_validation}{blocker_line}
}}
""",
        encoding="utf-8",
    )
    return path


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
        require(
            "Do not rely on prior chat context unless the user explicitly provides it." in text,
            "draft resume prompt should warn against relying on prior chat",
        )
        require(text.rstrip().endswith("END_SAVEPOINT_V1\n```"), "marker block must be final")
        require(len(text) <= 3400, "stub draft should stay compact")

        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_truncates_large_git_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        src = repo / "src"
        src.mkdir()
        for index in range(50):
            (src / f"file_{index:02}.py").write_text("print('old')\n", encoding="utf-8")
        git(repo, "add", "src")
        git(repo, "commit", "-m", "add many files")
        for index in range(50):
            (src / f"file_{index:02}.py").write_text("print('new')\n", encoding="utf-8")

        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run([sys.executable, str(STUB_HELPER)], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require("truncated, rerun command for full output" in text, "large snapshot was not truncated")
        require(len(text) <= 5600, "large fixture stub draft should stay compact")

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


def test_renderer_writes_resume_ready_savepoint_from_json_input() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require("Generated deterministic final savepoint." in text, "renderer origin note missing")
        require("<agent-fill>" not in text, "renderer should not leave stub placeholders")
        require("- Next action: run python scripts/check-savepoint-stub.py" in text, "smallest next step should drive rendered next action")
        require("- Changed:" in text and "app.py - modified" in text, "changed file was not derived")
        require("- Created: none" in text, "renderer-generated files should not be listed as created work")
        require("- Inspected without change: README.md" in text, "semantic inspected file missing")
        require("SAVEPOINT_MODE: file" in text, "file marker missing")
        require("VALIDATION_RECORDED: yes" in text, "savepoint validation marker missing")
        require("REDACTION_CHECKED: yes" in text, "redaction marker missing")
        require("RESUME_READY: yes" in text, "resume-ready marker missing")
        require("BLOCKERS: none" in text, "ready renderer output should have no marker blockers")
        require(text.rstrip().endswith("END_SAVEPOINT_V1\n```"), "marker block must be final")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_does_not_mark_first_unstaged_file_as_staged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("app.py - modified" in text, "unstaged modified file should be recorded as changed")
        require("app.py - worktree M" not in text, "ordinary unstaged modification should not be duplicated")
        require("app.py - staged M" not in text, "first unstaged status line was misclassified as staged")


def test_renderer_classifies_status_codes_without_losing_columns() -> None:
    helper = load_render_helper()
    original_git_status_lines = helper.git_status_lines
    try:
        helper.git_status_lines = lambda _cwd: [
            " M app.py",
            "M  staged.py",
            "?? new.py",
            "R  old.py -> renamed.py",
            "RM old2.py -> renamed2.py",
        ]
        changes = helper.derive_change_manifest(ROOT, {})
    finally:
        helper.git_status_lines = original_git_status_lines
    require("app.py - modified" in changes["changed"], "unstaged status should be a single modified entry")
    require("app.py - worktree M" not in changes["changed"], "unstaged status should not duplicate worktree detail")
    require("app.py - staged M" not in changes["staged"], "unstaged status should not be staged")
    require("staged.py - staged M" in changes["staged"], "staged status should be staged")
    require("new.py - untracked" in changes["created"], "untracked status should be created")
    require("renamed.py - renamed" in changes["moved"], "rename status should be moved")
    require("renamed.py - staged R" in changes["staged"], "staged rename should be staged")
    require("renamed2.py - renamed" in changes["moved"], "rename with worktree edit should be moved")
    require("renamed2.py - worktree M" in changes["changed"], "rename with worktree edit should keep worktree status")


def test_renderer_default_output_stays_compact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        for heading in ["## Recovery Contract", "## Session Target", "## Remaining Work"]:
            require(heading not in text, f"default renderer output should omit repeated section {heading}")
        require(".savepoint/SAVEPOINT.md - untracked" not in text, "renderer output should not list generated savepoint as created work")
        require("savepoint-input.json - untracked" not in text, "renderer output should not list semantic input file as created work")
        require("disk state wins" in text, "compact renderer output must retain disk-state-wins safety language")
        require(len(text) <= 3200, "default renderer output should stay compact")


def test_renderer_accepts_minimal_ready_json_input() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("RESUME_READY: yes" in text, "minimal ready input should render resume-ready")
        require("BLOCKERS: none" in text, "minimal ready input should have no blockers")
        for forbidden in ["missing-done-when", "missing-out-of-scope", "missing-smallest-next-step", "not recorded"]:
            require(forbidden not in text, f"minimal input should not emit removed optional placeholder {forbidden}")
        require("disk state wins" in text, "minimal input must retain disk-state-wins safety language")
        require("minimal-savepoint-input.json - untracked" not in text, "minimal input file should not be listed as created work")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_records_recovery_uncertainty_inputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "uncertain-savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "preserve recovery state after automatic context compaction",
  "current_state": "disk facts are verified but prior chat may be lossy",
  "next_action": "reload nested instructions before editing app.py",
  "expected_drift": "validation is from before session reset; rerun focused check if files changed",
  "unknown_unverified": "nested CLAUDE.md for app.py was not read after compaction",
  "project_validation": [
    {
      "command": "python scripts/check-savepoint-stub.py",
      "result": "passed",
      "summary": "uncertainty renderer fixture validation recorded"
    }
  ]
}
""",
            encoding="utf-8",
        )
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require(
            "- Expected drift from captured state: validation is from before session reset; rerun focused check if files changed" in text,
            "renderer should record optional expected drift",
        )
        require(
            "- Unknown or unverified: nested CLAUDE.md for app.py was not read after compaction" in text,
            "renderer should record optional unknown/unverified facts",
        )
        require(
            "Do not rely on prior chat context unless the user explicitly provides it." in text,
            "resume prompt should warn against relying on prior chat",
        )
        require("CONTEXT_TRANSFER_REASON" not in text, "renderer must not add new marker-style compaction fields")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_records_not_run_when_savepoint_validation_is_omitted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
            ],
            repo,
        )
        require(result.returncode == 2, "missing savepoint validation should keep artifact unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require(
            "- Savepoint validation: not-run: renderer was not asked to run savepoint validation" in text,
            "omitted savepoint validation should be recorded as not-run",
        )
        require("passed: renderer final validation command recorded" not in text, "omitted validation must not be marked passed")
        require("VALIDATION_RECORDED: no" in text, "marker should not record savepoint validation when omitted")
        require("savepoint-validation-not-run" in text, "missing validation blocker should be recorded")


def test_renderer_minimal_json_without_project_validation_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo, include_project_validation=False)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "missing project validation should keep minimal input unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("RESUME_READY: no" in text, "missing project validation must block resume-ready")
        require("project-validation-not-recorded" in text, "project validation blocker missing")
        require("missing-done-when" not in text, "removed optional done_when should not block readiness")
        require("missing-out-of-scope" not in text, "removed optional out_of_scope should not block readiness")
        require("missing-smallest-next-step" not in text, "removed optional smallest_next_step should not block readiness")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_failed_project_validation_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo, validation_result="failed")
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "failed project validation should keep output unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("RESUME_READY: no" in text, "failed project validation must block resume-ready")
        require("project-validation-not-passing" in text, "failed project validation blocker missing")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_missing_next_action_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo, include_next_action=False)
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "missing next action should keep output unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("missing-next-action" in text, "missing next action blocker missing")
        require("RESUME_READY: no" in text, "missing next action must block resume-ready")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_unresolved_blocker_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo, unresolved_blockers="needs user approval")
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "unresolved blocker should keep output unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("unresolved-blockers-recorded" in text, "unresolved blocker marker missing")
        require("RESUME_READY: no" in text, "unresolved blocker must block resume-ready")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_keeps_savepoint_unsafe_without_active_command_assertion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "renderer should write unsafe artifact and return 2")
        text = output.read_text(encoding="utf-8")
        require("RESUME_READY: no" in text, "unsafe render should not be resume-ready")
        require("BLOCKERS: active-commands-not-asserted" in text, "active command blocker missing")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_secret_scan_blocks_resume_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        payload = input_path.read_text(encoding="utf-8")
        input_path.write_text(
            payload.replace(
                "disk state can drift after the snapshot is captured",
                "token='sk-abcdefghijklmnopqrstuvwxyz123456'",
            ),
            encoding="utf-8",
        )
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 2, "secret-bearing render should return unsafe status")
        text = output.read_text(encoding="utf-8")
        require("REDACTION_CHECKED: no" in text, "secret scan failure should not mark redaction checked")
        require("RESUME_READY: no" in text, "secret scan failure should block resume-ready")
        require("BLOCKERS: redaction-check-failed" in text, "secret scan blocker missing")


def test_renderer_redacts_secret_even_when_scan_flag_is_omitted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        payload = input_path.read_text(encoding="utf-8")
        input_path.write_text(
            payload.replace(
                "disk state can drift after the snapshot is captured",
                "token='sk-abcdefghijklmnopqrstuvwxyz123456'",
            ),
            encoding="utf-8",
        )
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--assert-no-active-commands",
            ],
            repo,
        )
        require(result.returncode == 2, "omitted scan flag should keep output unsafe")
        text = output.read_text(encoding="utf-8")
        require("sk-abcdefghijklmnopqrstuvwxyz123456" not in text, "raw secret leaked into rendered output")
        require("<redacted>" in text, "secret should be redacted even when scan flag is omitted")
        require("REDACTION_CHECKED: no" in text, "omitted scan flag should not mark redaction checked")
        require("RESUME_READY: no" in text, "omitted scan flag should block resume-ready")


def test_root_renderer_forwards_to_portable_renderer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / "custom" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(ROOT_RENDERER),
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "root renderer did not write requested output")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def compact_resume_ready_text(
    repo: Path,
    output: Path,
    *,
    include_short_head: bool = True,
    next_action: str = "run the focused validator relaxation check",
    project_validation: str = "passed: focused compact validator fixture",
    skipped_checks: str = "none",
    redaction_check: str = "passed: no secrets in compact fixture",
    include_disk_wins: bool = True,
) -> str:
    short_head = "- Short HEAD: abc1234\n" if include_short_head else ""
    disk_wins = " because disk state wins when claims conflict" if include_disk_wins else ""
    return f"""# Savepoint Manifest

Compact savepoint fixture.

## TL;DR / Operational Summary

- Goal: finish compact validator support
- Current state: compact file has all safety-critical recovery facts
- Next action: {next_action}
- Blocker: none

## Repo Snapshot

- Captured at: 2026-06-11T00:00:00+00:00
- Working directory: {repo.resolve()}
- Git root: {repo.resolve()}
- Branch: main
{short_head}- `git status --short`: M app.py
- `git diff --stat`: app.py | 1 +
- `git diff --name-status`: M app.py
- `git diff --cached --stat`: none
- `git diff --cached --name-status`: none
- Latest commit: abc1234 initial
- Instruction files loaded: AGENTS.md
- Durable state files checked: none
- Expected drift from captured state: none

## Required Reading

1. Instruction files: AGENTS.md
2. Durable state files: none
3. `SAVEPOINT.md` sections: all
4. Focused detail artifacts, if any: none
5. Files to inspect first: app.py

Relative detail paths resolve from this file.

## Change Manifest

- Changed: app.py - compact validation fixture
- Created: none
- Deleted: none
- Moved: none
- Staged: none
- Inspected without change: README.md
- Unknown or unverified: none

## Recovery Notes

- Decisions/rationale: keep v1 marker schema unchanged while allowing compact prose
- Risks/pitfalls: verify disk state{disk_wins}
- Unresolved questions or approval blockers: none

## Validation Manifest

- Savepoint validation: passed: python scripts/validate_savepoint.py .savepoint/SAVEPOINT.md
- Project validation: {project_validation}
- Skipped checks / next validation: {skipped_checks}
- Secret redaction check: {redaction_check}
- Observable completion criteria: validator exits 0

## Resume Prompt

```text
Read this savepoint, verify cwd/Git state/status/diff, read listed instruction/state files, and compare all claims with disk state. Do not rely on prior chat context unless the user explicitly provides it. Report consistency or conflicts, and continue only if the user requested continuation and RESUME_READY is yes.
```

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: {output.resolve()}
SAVEPOINT_MODE: file
DETAILS_READY: not-needed
PROMPT_READY: yes
DISK_RECORDED: yes
VALIDATION_RECORDED: yes
REDACTION_CHECKED: yes
RESUME_READY: yes
BLOCKERS: none
END_SAVEPOINT_V1
```
"""


def write_compact_resume_ready_savepoint(repo: Path, **kwargs) -> Path:
    output = repo / ".savepoint" / "SAVEPOINT.md"
    output.parent.mkdir()
    output.write_text(compact_resume_ready_text(repo, output, **kwargs), encoding="utf-8")
    return output


def test_validator_accepts_compact_resume_ready_file_without_repetitive_sections() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo)
        text = output.read_text(encoding="utf-8")
        require(
            "Do not rely on prior chat context unless the user explicitly provides it." in text,
            "compact fixture resume prompt should warn against relying on prior chat",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_compact_validator_still_requires_disk_snapshot_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo, include_short_head=False)
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted missing Short HEAD")
        require("missing repo snapshot field - Short HEAD:" in validation.stderr, "missing snapshot error not reported")


def test_compact_validator_rejects_skipped_none_without_project_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo, project_validation="not-run: no project check recorded")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted skipped none without passed project validation")
        require("Skipped checks / next validation" in validation.stderr, "skipped validation error not reported")


def test_compact_validator_requires_redaction_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo, redaction_check="")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted blank redaction evidence")
        require("Secret redaction check" in validation.stderr, "redaction evidence error not reported")


def test_compact_validator_requires_next_action_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo, next_action="")
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted blank next action")
        require("RESUME_READY=yes requires substantive value for - Next action:" in validation.stderr, "next action error not reported")


def test_compact_validator_requires_disk_state_wins_language() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(repo, include_disk_wins=False)
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted missing disk-state-wins language")
        require("disk-state-wins" in validation.stderr, "disk-state-wins error not reported")


def test_renderer_revalidates_final_rewrite_before_success() -> None:
    helper = load_render_helper()
    original_validate_output = helper.validate_output

    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        calls: list[str] = []

        def fake_validate(path: Path) -> tuple[bool, str]:
            calls.append(path.read_text(encoding="utf-8"))
            if len(calls) == 1:
                return True, "first validation passed"
            return False, "second validation failed after final rewrite"

        original_cwd = Path.cwd()
        try:
            helper.validate_output = fake_validate
            os.chdir(repo)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = helper.main([
                    "--input",
                    str(input_path),
                    "--assert-no-active-commands",
                    "--scan-redaction",
                    "--run-savepoint-validation",
                ])
        finally:
            os.chdir(original_cwd)
            helper.validate_output = original_validate_output

        text = output.read_text(encoding="utf-8")
        require(len(calls) == 2, "renderer should validate again after embedding validation output")
        require(code == 2, "renderer should not return success when final rewrite validation fails")
        require("RESUME_READY: no" in text, "failed final validation should leave an unsafe savepoint")
        require("savepoint-validation-failed" in text, "failed final validation blocker missing")


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


def test_write_output_uses_portable_lf_open() -> None:
    helpers = [load_stub_helper(), load_render_helper()]

    for helper in helpers:
        original_open = getattr(helper, "open", None)
        calls: list[tuple[str, str, str, str]] = []

        def fake_open(path: Path, mode: str, *, encoding: str, newline: str):
            calls.append((str(path), mode, encoding, newline))
            raise PermissionError("blocked")

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "SAVEPOINT.md"
            stderr = io.StringIO()
            try:
                helper.open = fake_open
                with contextlib.redirect_stderr(stderr):
                    result = helper.write_output(output, "draft")
            finally:
                if original_open is None:
                    del helper.open
                else:
                    helper.open = original_open

        wrote = result[0] if isinstance(result, tuple) else result
        error = result[1] if isinstance(result, tuple) else ""
        require(not wrote, "write_output should report open failure")
        require(calls == [(str(output), "w", "utf-8", "\n")], "write_output should use portable open with LF newlines")
        if isinstance(result, tuple):
            require("failed to write output" in (error or ""), "render write failure message missing")
        else:
            require("failed to write output" in stderr.getvalue(), "stub write failure message missing")


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
        test_truncates_large_git_snapshot,
        test_refuses_overwrite_without_force,
        test_root_wrapper_forwards_to_portable_helper,
        test_renderer_writes_resume_ready_savepoint_from_json_input,
        test_renderer_does_not_mark_first_unstaged_file_as_staged,
        test_renderer_classifies_status_codes_without_losing_columns,
        test_renderer_default_output_stays_compact,
        test_renderer_accepts_minimal_ready_json_input,
        test_renderer_records_recovery_uncertainty_inputs,
        test_renderer_records_not_run_when_savepoint_validation_is_omitted,
        test_renderer_minimal_json_without_project_validation_stays_unsafe,
        test_renderer_failed_project_validation_stays_unsafe,
        test_renderer_missing_next_action_stays_unsafe,
        test_renderer_unresolved_blocker_stays_unsafe,
        test_renderer_keeps_savepoint_unsafe_without_active_command_assertion,
        test_renderer_secret_scan_blocks_resume_ready,
        test_renderer_redacts_secret_even_when_scan_flag_is_omitted,
        test_root_renderer_forwards_to_portable_renderer,
        test_validator_accepts_compact_resume_ready_file_without_repetitive_sections,
        test_compact_validator_still_requires_disk_snapshot_fields,
        test_compact_validator_rejects_skipped_none_without_project_pass,
        test_compact_validator_requires_redaction_evidence,
        test_compact_validator_requires_next_action_evidence,
        test_compact_validator_requires_disk_state_wins_language,
        test_renderer_revalidates_final_rewrite_before_success,
        test_run_command_handles_oserror,
        test_find_git_root_handles_empty_output,
        test_refuses_directory_output,
        test_refuses_savepoint_named_directory_output,
        test_refuses_non_savepoint_output_name,
        test_reports_parent_mkdir_oserror,
        test_write_output_uses_portable_lf_open,
        test_compacts_focus_to_single_line,
        test_truncates_long_focus,
    ]
    for test in tests:
        test()
        print(f"ok: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
