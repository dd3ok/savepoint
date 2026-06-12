#!/usr/bin/env python3
"""Validate deterministic savepoint renderer generation."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDER_HELPER = ROOT / "skills" / "savepoint" / "scripts" / "render_savepoint.py"
SAVEPOINT_CLI = ROOT / "skills" / "savepoint" / "scripts" / "savepoint.py"
ROOT_SAVEPOINT_CLI = ROOT / "scripts" / "savepoint.py"
VALIDATOR = ROOT / "skills" / "savepoint" / "scripts" / "validate_savepoint.py"
OUTPUT_CONTRACT_CHECKER = ROOT / "scripts" / "check-output-contract.py"
HELPER_SCRIPT_DIR = RENDER_HELPER.parent
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


def load_render_helper():
    spec = importlib.util.spec_from_file_location("render_savepoint_under_test", RENDER_HELPER)
    require(spec is not None and spec.loader is not None, "could not load render helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract_helper():
    spec = importlib.util.spec_from_file_location(
        "savepoint_contract_under_test",
        HELPER_SCRIPT_DIR / "savepoint_contract.py",
    )
    require(spec is not None and spec.loader is not None, "could not load savepoint contract module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator_helper():
    spec = importlib.util.spec_from_file_location("validate_savepoint_under_test", VALIDATOR)
    require(spec is not None and spec.loader is not None, "could not load validator module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_savepoint_helper():
    spec = importlib.util.spec_from_file_location("savepoint_under_test", SAVEPOINT_CLI)
    require(spec is not None and spec.loader is not None, "could not load savepoint CLI module")
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
  "decisions": ["keep SAVEPOINT_V1 marker fields and order unchanged"],
  "risks": ["disk state can drift after the snapshot is captured"],
  "failed_approaches": "none",
  "unresolved_blockers": "none",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "command": "python scripts/check-savepoint-renderer.py",
          "result": "passed",
          "summary": "renderer fixture validation recorded"
        }
      ]
    }
  },
  "observable_completion": "check-savepoint-renderer exits 0",
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
  "validation": {
    "project": {
      "status": "%s",
      "commands": [
        {
          "command": "python scripts/check-savepoint-renderer.py",
          "result": "%s",
          "summary": "minimal renderer fixture validation recorded"
        }
      ]
    }
  }""" % (validation_result, validation_result)
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


def lite_validation_semantic_input(
    repo: Path,
    *,
    status: str,
    reason: str = "",
    next_validation: str = "",
) -> Path:
    path = repo / "lite-savepoint-input.json"
    data: dict[str, object] = {
        "goal": "finish minimal deterministic rendering",
        "current_state": "project validation posture should not be confused with resume safety",
        "next_action": "run the focused minimal renderer check",
        "validation": {
            "project": {
                "status": status,
                "reason": reason,
                "commands": [],
                "next_validation": next_validation,
            }
        },
    }
    if status == "passed":
        data["validation"] = {
            "project": {
                "status": status,
                "reason": reason,
                "commands": [
                    {
                        "command": "python scripts/check-savepoint-renderer.py",
                        "result": "passed",
                        "summary": "focused renderer check passed",
                    }
                ],
                "next_validation": next_validation,
            }
        }
    elif status.startswith("failed"):
        data["validation"] = {
            "project": {
                "status": status,
                "reason": reason,
                "commands": [
                    {
                        "command": "python -m pytest tests/auth",
                        "result": "failed",
                        "summary": reason or "project validation failed",
                    }
                ],
                "next_validation": next_validation,
            }
        }
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return path


def resume_ready_literal_semantic_input(repo: Path) -> Path:
    path = repo / "resume-ready-literal-input.json"
    data = {
        "goal": "prove renderer exit status comes from the marker",
        "current_state": "body text can mention RESUME_READY: yes without making the artifact ready",
        "next_action": "report the blocker instead of treating body prose as readiness",
    }
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return path


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
        require("truncated, rerun command for full output" in text, "large snapshot was not truncated")
        require(len(text) <= 5600, "large fixture renderer output should stay compact")

        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_refuses_overwrite_without_force() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        first = run(
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
        require("wrote:" in first.stdout, first.stderr or first.stdout)
        second = run([sys.executable, str(RENDER_HELPER), "--input", str(input_path)], repo)
        require(second.returncode != 0, "renderer overwrote without --force")
        require("output already exists" in second.stderr, "overwrite refusal message missing")

        forced = run(
            [
                sys.executable,
                str(RENDER_HELPER),
                "--input",
                str(input_path),
                "--force",
                "--assert-no-active-commands",
                "--scan-redaction",
                "--run-savepoint-validation",
            ],
            repo,
        )
        require("wrote:" in forced.stdout, forced.stderr or forced.stdout)
        require(output.exists(), "forced write removed output")


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
        require("<agent-fill>" not in text, "renderer should not leave placeholders")
        require("- Next action: run the focused validation commands" in text, "next_action should drive rendered next action")
        require("- Changed:" in text and "app.py - modified" in text, "changed file was not derived")
        require("- Created: none" in text, "renderer-generated files should not be listed as created work")
        require("- Inspected without change: README.md" in text, "semantic inspected file missing")
        require("SAVEPOINT_MODE: file" in text, "file marker missing")
        require("VALIDATION_RECORDED: yes" in text, "savepoint validation marker missing")
        require("REDACTION_CHECKED: yes" in text, "redaction marker missing")
        require(
            "- Secret redaction check: passed: rendered SAVEPOINT.md scanned for built-in secret patterns; no matches" in text,
            "redaction evidence should state scan scope and result",
        )
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
        for forbidden in ["missing-done-when", "missing-out-of-scope", "not recorded"]:
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
  "instruction_files_loaded": [
    "nested CLAUDE.md for app.py - not-read - reload before editing app.py"
  ],
  "expected_drift": "validation is from before session reset; rerun focused check if files changed",
  "unknown_unverified": "nested CLAUDE.md for app.py was not read after compaction",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "command": "python scripts/check-savepoint-renderer.py",
          "result": "passed",
          "summary": "uncertainty renderer fixture validation recorded"
        }
      ]
    }
  }
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
        required_reading = text.split("## Required Reading", 1)[1].split("## Change Manifest", 1)[0]
        require(
            "nested CLAUDE.md for app.py - not-read - reload before editing app.py" in required_reading,
            "renderer should carry path-scoped instruction reload into Required Reading",
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
        require("validation-not-run-unknown" in text, "unknown project validation blocker missing")
        require("missing-done-when" not in text, "removed optional done_when should not block readiness")
        require("missing-out-of-scope" not in text, "removed optional out_of_scope should not block readiness")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_exit_code_uses_marker_not_body_resume_ready_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = resume_ready_literal_semantic_input(repo)
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
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("Current state: body text can mention RESUME_READY: yes" in text, "test fixture body literal missing")
        require("RESUME_READY: no" in text, "marker should remain unsafe")
        require(result.returncode == 2, "renderer exit code must follow marker RESUME_READY, not body prose")


def test_renderer_failed_project_validation_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = minimal_semantic_input(repo, validation_result="failed-blocking")
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
        require("validation-failed-blocking" in text, "failed project validation blocker missing")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_validation_status_token_matrix_is_consistent() -> None:
    renderer = load_render_helper()
    validator = load_validator_helper()
    for status in ["passed", "failed-expected", "failed-blocking", "not-run-justified", "not-run-unknown"]:
        require(
            renderer.normalize_project_validation_status(status) == status,
            f"renderer did not accept exact status {status!r}",
        )
    blocking_tokens = ["fail", "fails", "failed", "failing", "failure", "error", "errors"]
    for token in blocking_tokens:
        require(
            renderer.normalize_project_validation_status(f"tests are {token}") == "not-run-unknown",
            f"renderer should not upgrade free-form status {token!r}",
        )
        validator_text = f"- Project validation: tests are {token}\n"
        require(
            validator.project_validation_status(validator_text) == "failed-blocking",
            f"validator did not classify {token!r} as failed-blocking",
        )
        passed_text = f"- Project validation: passed: `npm test` - tests are {token}\n"
        require(
            validator.passed_validation_has_failure_terms(passed_text),
            f"validator did not detect failure token {token!r} under passed status",
        )
    for token in ["not-run", "not run", "skipped"]:
        require(
            renderer.normalize_project_validation_status(token) == "not-run-unknown",
            f"renderer did not classify {token!r} as not-run-unknown",
        )
        require(
            validator.project_validation_status(f"- Project validation: {token}\n") == "not-run-unknown",
            f"validator did not classify {token!r} as not-run-unknown",
        )
    reason_with_passed = "- Project validation: failed-expected: known failure; previous lint passed\n"
    require(
        validator.project_validation_status(reason_with_passed) == "failed-expected",
        "validator should parse canonical status before reason text containing passed",
    )
    for phrase in ["0 errors", "zero errors", "no errors", "0 failures", "zero failures", "no failures"]:
        commands = [
            {
                "command": "npm run lint",
                "result": "passed",
                "summary": phrase,
            }
        ]
        require(
            renderer.project_validation_passed(commands),
            f"renderer treated negated failure phrase {phrase!r} as blocking",
        )
        passed_text = f"- Project validation: passed: `npm run lint` - {phrase}\n"
        require(
            not validator.passed_validation_has_failure_terms(passed_text),
            f"validator treated negated failure phrase {phrase!r} as blocking",
        )
        require(
            validator.project_validation_status(passed_text) == "passed",
            f"validator did not classify negated failure phrase {phrase!r} as passed",
        )


def test_renderer_rejects_removed_project_validation_input() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish canonical validation handling",
  "current_state": "top-level project_validation is no longer a supported input shape",
  "next_action": "rewrite input to validation.project before continuing",
  "project_validation": [
    {
      "command": "npm run lint",
      "result": "passed",
      "summary": "lint passed"
    },
    {
      "command": "npm test",
      "result": "failed",
      "summary": "auth tests failed"
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
        require(result.returncode == 1, "removed project_validation input should be rejected before render")
        require("unsupported input key: project_validation" in result.stderr, "removed project_validation error missing")
        require(not (repo / ".savepoint" / "SAVEPOINT.md").exists(), "removed project_validation input should not write an artifact")


def test_renderer_rejects_removed_input_aliases() -> None:
    for key, value in [
        ("smallest_next_step", "run an old next-step alias"),
        ("skipped_checks_next_validation", "run an old validation alias"),
    ]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_repo_with_modified_app(Path(tmp))
            input_path = repo / "savepoint-input.json"
            data = {
                "goal": "reject removed aliases",
                "current_state": "canonical input shape is required",
                "next_action": "rewrite input before rendering",
                "validation": {
                    "project": {
                        "status": "passed",
                        "commands": [
                            {
                                "command": "python scripts/check-savepoint-renderer.py",
                                "result": "passed",
                                "summary": "canonical validation recorded",
                            }
                        ],
                    }
                },
                key: value,
            }
            input_path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
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
            require(result.returncode == 1, f"{key} should be rejected before render")
            require(f"unsupported input key: {key}" in result.stderr, f"{key} error missing")
            require(not (repo / ".savepoint" / "SAVEPOINT.md").exists(), f"{key} should not write an artifact")


def test_renderer_passed_project_validation_requires_complete_command_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish complete validation command enforcement",
  "current_state": "structured validation is marked passed but omits command details",
  "next_action": "record the exact validation command before continuing",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "result": "passed"
        }
      ]
    }
  }
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
        require(result.returncode == 2, "passed validation without command fields should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-command-missing" in text, "incomplete passed validation blocker missing")
        require("RESUME_READY: no" in text, "incomplete passed validation must block resume-ready")


def test_renderer_structured_passed_validation_with_failure_text_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish structured validation consistency",
  "current_state": "structured validation status says passed but summary records failure",
  "next_action": "report validation failure before continuing",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "command": "npm test",
          "result": "passed",
          "summary": "auth tests failed"
        }
      ]
    }
  }
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
        require(result.returncode == 2, "passed validation with failure text should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-failed-blocking" in text, "structured pass/fail contradiction blocker missing")
        require("RESUME_READY: no" in text, "structured pass/fail contradiction must block resume-ready")


def test_renderer_structured_passed_validation_with_failing_text_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish structured validation consistency",
  "current_state": "structured validation status says passed but summary records failing tests",
  "next_action": "report validation failure before continuing",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "command": "npm test",
          "result": "passed",
          "summary": "auth tests are failing"
        }
      ]
    }
  }
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
        require(result.returncode == 2, "passed validation with failing text should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-failed-blocking" in text, "structured passed/failing contradiction blocker missing")
        require("RESUME_READY: no" in text, "structured passed/failing contradiction must block resume-ready")


def test_renderer_not_run_justified_project_validation_can_resume_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="not-run-justified",
            reason="handoff requested before tests could run",
            next_validation="python scripts/check-savepoint-renderer.py",
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
        require("Project validation: not-run-justified" in text, "justified not-run status missing")
        require("Skipped checks / next validation: python scripts/check-savepoint-renderer.py" in text, "next validation missing")
        require("RESUME_READY: yes" in text, "justified not-run project validation should allow resume-ready")
        require("VALIDATION_RECORDED: yes" in text, "project validation posture should count as recorded")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_failed_expected_project_validation_can_resume_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="failed-expected",
            reason="known failing auth edge case is the next task",
            next_validation="python -m pytest tests/auth",
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
        require("failed-expected" in text, "expected failure status missing")
        require("reason: known failing auth edge case is the next task" in text, "expected failure reason missing")
        require("RESUME_READY: yes" in text, "expected project validation failure should allow resume-ready")
        require("validation-failed-blocking" not in text, "expected failure must not be marked blocking")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_failed_expected_without_command_fields_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish expected failure evidence",
  "current_state": "expected project failure is documented but no command evidence was recorded",
  "next_action": "record the exact failing command before continuing",
  "validation": {
    "project": {
      "status": "failed-expected",
      "reason": "known failing auth edge case is the next task",
      "commands": [],
      "next_validation": "python -m pytest tests/auth"
    }
  }
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
        require(result.returncode == 2, "expected failure without command evidence should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-command-missing" in text, "missing command evidence blocker missing")
        require("RESUME_READY: no" in text, "expected failure without command evidence must block resume-ready")
        require("VALIDATION_RECORDED: no" in text, "missing command evidence should not count as validation recorded")
        validation = run([sys.executable, str(VALIDATOR), str(repo / ".savepoint" / "SAVEPOINT.md")], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_renderer_failed_expected_with_passed_command_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish expected failure evidence",
  "current_state": "expected project failure is documented with a non-failing command",
  "next_action": "record the exact failing command before continuing",
  "validation": {
    "project": {
      "status": "failed-expected",
      "reason": "known failing auth edge case is the next task",
      "commands": [
        {
          "command": "python -m pytest tests/auth",
          "result": "passed",
          "summary": "0 errors"
        }
      ],
      "next_validation": "python -m pytest tests/auth"
    }
  }
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
        require(result.returncode == 2, "expected failure with passed command evidence should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-failed-evidence-missing" in text, "missing failed evidence blocker missing")
        require("RESUME_READY: no" in text, "passed command cannot satisfy expected failure evidence")
        require("VALIDATION_RECORDED: no" in text, "passed command should not count as failed-expected validation recorded")


def test_renderer_failed_expected_with_passed_result_failure_word_summary_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish expected failure evidence",
  "current_state": "expected project failure is documented with only historical failure wording",
  "next_action": "record the exact failing command before continuing",
  "validation": {
    "project": {
      "status": "failed-expected",
      "reason": "known failing auth edge case is the next task",
      "commands": [
        {
          "command": "python -m pytest tests/auth",
          "result": "passed",
          "summary": "previous failure is now fixed"
        }
      ],
      "next_validation": "python -m pytest tests/auth"
    }
  }
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
        require(result.returncode == 2, "expected failure with passed result should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-failed-evidence-missing" in text, "passed result with historical failure summary should get failed-evidence blocker")
        require("savepoint-validation-failed" not in text, "renderer should report the specific failed-evidence blocker before validation fallback")
        require("RESUME_READY: no" in text, "passed result cannot satisfy expected failure evidence")


def test_renderer_failed_expected_with_next_validation_none_stays_unsafe_with_specific_blocker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="failed-expected",
            reason="known failing auth edge case is the next task",
            next_validation="none",
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
        require(result.returncode == 2, "expected failure with placeholder next validation should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-next-command-missing" in text, "placeholder next validation should get specific blocker")
        require("savepoint-validation-failed" not in text, "renderer should report next-command blocker before validation fallback")


def test_renderer_not_run_justified_with_reason_none_stays_unsafe_with_specific_blocker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="not-run-justified",
            reason="none",
            next_validation="python scripts/check-savepoint-renderer.py",
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
        require(result.returncode == 2, "justified not-run with placeholder reason should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-reason-missing" in text, "placeholder reason should get specific blocker")
        require("savepoint-validation-failed" not in text, "renderer should report reason blocker before validation fallback")


def test_renderer_not_run_justified_without_next_validation_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="not-run-justified",
            reason="handoff requested before tests could run",
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
        require(result.returncode == 2, "justified not-run without next validation should stay unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-next-command-missing" in text, "missing next validation blocker missing")
        require("RESUME_READY: no" in text, "missing next validation must block resume-ready")


def test_renderer_failed_blocking_project_validation_stays_unsafe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = lite_validation_semantic_input(
            repo,
            status="failed-blocking",
            reason="test failure cause is unknown",
            next_validation="python -m pytest tests/auth",
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
        require(result.returncode == 2, "blocking project validation failure should keep output unsafe")
        text = (repo / ".savepoint" / "SAVEPOINT.md").read_text(encoding="utf-8")
        require("validation-failed-blocking" in text, "blocking failure blocker missing")
        require("RESUME_READY: no" in text, "blocking failure must block resume-ready")


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


def test_renderer_rejects_removed_blockers_alias() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = repo / "savepoint-input.json"
        input_path.write_text(
            """{
  "goal": "finish blocker alias handling",
  "current_state": "renderer should not drop intuitive blocker input",
  "next_action": "report blocker before continuing",
  "blockers": "needs user approval",
  "validation": {
    "project": {
      "status": "passed",
      "commands": [
        {
          "command": "python scripts/check-savepoint-renderer.py",
          "result": "passed",
          "summary": "blocker alias fixture validation recorded"
        }
      ]
    }
  }
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
        require(result.returncode == 1, "blockers alias should be rejected before render")
        require("unsupported input key: blockers" in result.stderr, "blockers alias error missing")
        require(not (repo / ".savepoint" / "SAVEPOINT.md").exists(), "removed blockers alias should not write an artifact")


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
        secret_name = "sk-abcdefghijklmnopqrstuvwxyz123456"
        (repo / f"{secret_name}.txt").write_text("do not include raw secret-like paths\n", encoding="utf-8")
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
        require(secret_name not in text, "raw secret-like path leaked into rendered output")
        require("<redacted>" in text, "secret-like path should be redacted in rendered output")


def test_renderer_rejects_secret_bearing_input_before_render() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        secret_value = "sk-abcdefghijklmnopqrstuvwxyz123456"
        payload = input_path.read_text(encoding="utf-8")
        input_path.write_text(
            payload.replace(
                "disk state can drift after the snapshot is captured",
                f"token='{secret_value}'",
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
        combined = f"{result.stdout}\n{result.stderr}"
        require(result.returncode == 1, "secret-bearing input should fail before render")
        require(not output.exists(), "secret-bearing input should not write SAVEPOINT.md")
        require("input JSON failed redaction scan" in result.stderr, "input redaction scan error missing")
        require(secret_value not in combined, "input redaction scan must not print raw secret values")


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


def test_savepoint_cli_save_validate_and_inspect() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        saved = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
            ],
            repo,
        )
        require(saved.returncode == 0, saved.stderr or saved.stdout)
        require(output.exists(), "savepoint CLI did not write SAVEPOINT.md")

        validated = run([sys.executable, str(SAVEPOINT_CLI), "validate", str(output)], repo)
        require(validated.returncode == 0, validated.stderr or validated.stdout)

        inspected = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(output), "--json"], repo)
        require(inspected.returncode == 0, inspected.stderr or inspected.stdout)
        parsed = json.loads(inspected.stdout)
        require(parsed["RESUME_READY"] == "yes", "inspect JSON should report resume-ready")
        require(parsed["SAVEPOINT_MODE"] == "file", "inspect JSON should report file mode")
        require(parsed["savepoint_validation"] == "passed", "inspect JSON should include savepoint validation status")
        require(parsed["validation"]["project"]["status"] == "passed", "inspect JSON should include project validation status")
        require("next_validation" in parsed["validation"]["project"], "inspect JSON should include project validation next command")


def test_savepoint_cli_deletes_input_on_success_only_under_savepoint_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        original_input = semantic_input(repo)
        input_path = repo / ".savepoint" / "input.json"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(original_input.read_text(encoding="utf-8"), encoding="utf-8")
        original_input.unlink()
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
                "--delete-input-on-success",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "savepoint CLI did not write SAVEPOINT.md")
        require(not input_path.exists(), "successful save should delete .savepoint input when requested")


def test_savepoint_cli_does_not_delete_input_outside_savepoint_dir() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
                "--delete-input-on-success",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "savepoint CLI did not write SAVEPOINT.md")
        require(input_path.exists(), "input outside .savepoint should not be deleted")


def test_savepoint_cli_does_not_delete_outside_symlink_to_savepoint_input() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        original_input = semantic_input(repo)
        target = repo / ".savepoint" / "input.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(original_input.read_text(encoding="utf-8"), encoding="utf-8")
        original_input.unlink()
        outside = repo / "outside-input.json"
        try:
            outside.symlink_to(target)
        except OSError as exc:
            print(f"skip: test_savepoint_cli_does_not_delete_outside_symlink_to_savepoint_input ({exc})")
            return
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(outside),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
                "--delete-input-on-success",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "savepoint CLI did not write SAVEPOINT.md")
        require(outside.exists() or outside.is_symlink(), "input symlink outside .savepoint should not be deleted")


def test_delete_input_on_success_requires_path_itself_under_savepoint_dir() -> None:
    helper = load_savepoint_helper()
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        (repo / ".savepoint").mkdir()
        original_cwd = Path.cwd()

        class OutsideParent:
            def resolve(self):
                return repo.resolve()

        class OutsideAlias:
            parent = OutsideParent()

            def is_absolute(self):
                return True

            def resolve(self):
                return (repo / ".savepoint" / "input.json").resolve()

        try:
            os.chdir(repo)
            allowed = helper.is_under_savepoint_dir(OutsideAlias())
        finally:
            os.chdir(original_cwd)
        require(allowed is False, "path itself must be under .savepoint before deletion is allowed")


def test_delete_input_on_success_handles_path_resolution_error() -> None:
    helper = load_savepoint_helper()
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        (repo / ".savepoint").mkdir()
        original_cwd = Path.cwd()

        class RaisingParent:
            def resolve(self):
                raise OSError("blocked")

        class RaisingPath:
            parent = RaisingParent()

            def is_absolute(self):
                return True

            def resolve(self):
                raise OSError("blocked")

        try:
            os.chdir(repo)
            allowed = helper.is_under_savepoint_dir(RaisingPath())
        finally:
            os.chdir(original_cwd)
        require(allowed is False, "path resolution errors should deny deletion without traceback")


def test_savepoint_cli_keeps_input_when_save_is_not_resume_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        original_input = semantic_input(repo)
        input_path = repo / ".savepoint" / "input.json"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(original_input.read_text(encoding="utf-8"), encoding="utf-8")
        original_input.unlink()
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--scan-redaction",
                "--validate",
                "--delete-input-on-success",
            ],
            repo,
        )
        require(result.returncode == 2, "unsafe savepoint should return not-ready status")
        require(output.exists(), "unsafe save should still write SAVEPOINT.md")
        require(input_path.exists(), "input should remain when save is not resume-ready")


def test_savepoint_cli_direct_flags_can_render_passed_savepoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
                "--goal",
                "finish direct flag savepoint",
                "--current-state",
                "simple savepoint fields are supplied directly on the CLI",
                "--next-action",
                "inspect the generated savepoint",
                "--project-status",
                "passed",
                "--validation-command",
                "python scripts/check-savepoint-renderer.py",
                "--validation-result",
                "passed",
                "--validation-summary",
                "focused renderer check passed",
                "--files-to-inspect-first",
                "app.py",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require("RESUME_READY: yes" in text, "direct passed savepoint should be resume-ready")
        require("finish direct flag savepoint" in text, "direct goal missing from savepoint")
        require("app.py" in text, "direct files-to-inspect-first missing from savepoint")


def test_savepoint_cli_direct_flags_can_render_not_run_justified_savepoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
                "--goal",
                "finish direct flag savepoint",
                "--current-state",
                "only documentation changed since the last validated state",
                "--next-action",
                "rerun the focused documentation validation",
                "--project-status",
                "not-run-justified",
                "--reason",
                "current change only updates savepoint documentation",
                "--next-validation",
                "python scripts/check-savepoint-renderer.py",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        text = output.read_text(encoding="utf-8")
        require("RESUME_READY: yes" in text, "direct not-run-justified savepoint should be resume-ready")
        require("current change only updates savepoint documentation" in text, "direct reason missing from savepoint")


def test_savepoint_cli_rejects_input_and_direct_flags_together() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--goal",
                "do not mix input modes",
            ],
            repo,
        )
        require(result.returncode == 1, "CLI should reject mixed input and direct flag modes")
        require("cannot combine --input with direct save flags" in result.stderr, "mixed mode error missing")
        require(not output.exists(), "mixed input mode should not write SAVEPOINT.md")


def test_savepoint_cli_rejects_incomplete_direct_flags() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(SAVEPOINT_CLI),
                "save",
                "--output",
                str(output),
                "--goal",
                "missing required direct fields",
                "--current-state",
                "not enough direct fields were supplied",
            ],
            repo,
        )
        require(result.returncode == 1, "CLI should reject incomplete direct flag mode")
        require("missing required direct save field" in result.stderr, "direct flag required-field error missing")
        require(not output.exists(), "incomplete direct input should not write SAVEPOINT.md")


def test_savepoint_cli_init_input_defaults_to_unknown_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        output = repo / ".savepoint" / "input.json"
        result = run([sys.executable, str(SAVEPOINT_CLI), "init-input", "--output", str(output)], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "init-input did not write sample input")
        data = json.loads(output.read_text(encoding="utf-8"))
        project = data["validation"]["project"]
        require(project["status"] == "not-run-unknown", "init-input should default to honest unknown validation")
        require(project["reason"] == "", "init-input should not prefill a justification")
        require(project["next_validation"] == "", "init-input should not prefill next validation")
        require(not (repo / ".savepoint" / "SAVEPOINT.md").exists(), "init-input should not write SAVEPOINT.md")


def test_savepoint_cli_inspect_json_reports_invalid_marker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        output.parent.mkdir()
        output.write_text(
            """# Invalid Savepoint

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_MODE: file
SAVEPOINT_PATH: C:/tmp/SAVEPOINT.md
END_SAVEPOINT_V1
```
""",
            encoding="utf-8",
        )
        result = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(output), "--json"], repo)
        require(result.returncode == 1, "invalid marker should return inspect exit code 1")
        parsed = json.loads(result.stdout)
        require(parsed["marker_valid"] is False, "invalid marker JSON should set marker_valid=false")
        require(parsed["resume_ready"] is False, "invalid marker JSON should not be resume-ready")
        require("errors" in parsed and parsed["errors"], "invalid marker JSON should include errors")


def test_savepoint_cli_inspect_json_requires_valid_savepoint_for_resume_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = repo / ".savepoint" / "SAVEPOINT.md"
        output.parent.mkdir()
        output.write_text(
            f"""# Incomplete Savepoint

## Markers

```text
SAVEPOINT_V1
SAVEPOINT_PATH: {output}
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
""",
            encoding="utf-8",
        )
        result = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(output), "--json"], repo)
        require(result.returncode == 1, "invalid savepoint body should return inspect exit code 1")
        parsed = json.loads(result.stdout)
        require(parsed["marker_valid"] is True, "valid marker should remain marker_valid=true")
        require(parsed["savepoint_valid"] is False, "invalid savepoint body should set savepoint_valid=false")
        require(parsed["resume_ready"] is False, "invalid savepoint body should not be resume-ready")


def test_savepoint_cli_inspect_missing_or_not_savepoint_returns_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        missing = repo / ".savepoint" / "SAVEPOINT.md"
        missing_result = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(missing), "--json"], repo)
        require(missing_result.returncode == 2, "missing file should return inspect exit code 2")

        note = repo / "note.md"
        note.write_text("# Not a savepoint\n", encoding="utf-8")
        note_result = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(note), "--json"], repo)
        require(note_result.returncode == 2, "non-savepoint file should return inspect exit code 2")

        invalid_utf8 = repo / "invalid-savepoint.md"
        invalid_utf8.write_bytes(b"\xff\xfe\xff")
        invalid_result = run([sys.executable, str(SAVEPOINT_CLI), "inspect", str(invalid_utf8), "--json"], repo)
        require(invalid_result.returncode == 2, "unreadable UTF-8 file should return inspect exit code 2")
        parsed = json.loads(invalid_result.stdout)
        require(parsed["marker_valid"] is False, "unreadable UTF-8 file should not be marker-valid")
        require(parsed["errors"], "unreadable UTF-8 JSON should include errors")


def test_savepoint_cli_validate_directory_returns_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        directory = repo / ".savepoint"
        directory.mkdir()
        result = run([sys.executable, str(SAVEPOINT_CLI), "validate", str(directory)], repo)
        require(result.returncode != 0, "validate should reject directory paths")
        require("not a file" in result.stderr, "validate directory error should name non-file path")
        require("Traceback" not in result.stderr, "validate directory error should not print traceback")


def test_root_savepoint_cli_forwards_to_portable_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        result = run(
            [
                sys.executable,
                str(ROOT_SAVEPOINT_CLI),
                "save",
                "--input",
                str(input_path),
                "--output",
                str(output),
                "--assert-no-active-commands",
                "--scan-redaction",
                "--validate",
            ],
            repo,
        )
        require(result.returncode == 0, result.stderr or result.stdout)
        require(output.exists(), "root savepoint CLI did not write SAVEPOINT.md")


def test_savepoint_cli_text_mode_does_not_write_recovery_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo_with_modified_app(Path(tmp))
        input_path = semantic_input(repo)
        result = run([sys.executable, str(SAVEPOINT_CLI), "text", "--input", str(input_path)], repo)
        require(result.returncode == 0, result.stderr or result.stdout)
        require("No file was written." in result.stdout, "text mode should say no file was written")
        require("Repo recovery is not guaranteed." in result.stdout, "text mode should avoid recovery guarantees")
        require("Blockers:" in result.stdout, "text mode should include blockers")
        require("Risks:" in result.stdout, "text mode should include risks")
        require("Files to inspect first:" in result.stdout, "text mode should include first files")
        require("Validation:" in result.stdout, "text mode should include validation posture")
        require("SAVEPOINT_V1" not in result.stdout, "text mode should not emit machine marker by default")
        require("RESUME_READY: yes" not in result.stdout, "text mode must not claim resume-ready")
        require(not (repo / ".savepoint" / "SAVEPOINT.md").exists(), "text mode wrote a recovery artifact")


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

- Savepoint validation: passed: python scripts/savepoint.py validate .savepoint/SAVEPOINT.md
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


def test_compact_validator_accepts_not_run_justified_project_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="not-run-justified: handoff requested before tests could run",
            skipped_checks="python scripts/check-savepoint-renderer.py",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_compact_validator_accepts_failed_expected_project_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: failed: `python -m pytest tests/auth` - auth edge case failed; reason: known failing auth edge case is the next task",
            skipped_checks="python -m pytest tests/auth",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode == 0, validation.stderr or validation.stdout)


def test_compact_validator_rejects_not_run_unknown_project_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="not-run-unknown: no reason or next validation recorded",
            skipped_checks="none",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted unknown not-run project validation")
        require("not-run-unknown" in validation.stderr, "unknown not-run validation error not reported")


def test_compact_validator_rejects_failed_blocking_project_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-blocking: test failure cause is unknown",
            skipped_checks="python -m pytest tests/auth",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted blocking project validation failure")
        require("failed-blocking" in validation.stderr, "blocking project validation error not reported")


def test_compact_validator_rejects_expected_failure_without_next_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: failed: `python -m pytest tests/auth` - auth edge case failed; reason: known failing auth edge case is the next task",
            skipped_checks="none",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted expected failure without next validation")
        require("next validation" in validation.stderr, "missing next validation error not reported")


def test_compact_validator_rejects_expected_failure_without_command_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: `python -m pytest tests/auth` - known failing auth edge case; reason: known failing auth edge case is the next task",
            skipped_checks="python -m pytest tests/auth",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted expected failure without result evidence")
        require("command evidence" in validation.stderr, "missing result evidence error not reported")


def test_compact_validator_rejects_expected_failure_with_passed_command_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: passed: `python -m pytest tests/auth` - 0 errors; reason: known failing auth edge case is the next task",
            skipped_checks="python -m pytest tests/auth",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted passed command as expected failure evidence")
        require("command evidence" in validation.stderr, "passed command evidence error not reported")


def test_compact_validator_rejects_not_run_justified_without_reason() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="not-run-justified",
            skipped_checks="python scripts/check-savepoint-renderer.py",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted justified not-run without reason")
        require("requires a reason" in validation.stderr, "missing reason error not reported")


def test_compact_validator_rejects_expected_failure_without_reason() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: failed: `python -m pytest tests/auth` - known failing auth edge case is the next task",
            skipped_checks="python -m pytest tests/auth",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted expected failure without reason")
        require("requires a reason" in validation.stderr, "missing expected-failure reason error not reported")


def test_compact_validator_rejects_passed_validation_with_failure_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="passed: `npm test` - auth tests failed",
            skipped_checks="none",
        )
        validation = run([sys.executable, str(VALIDATOR), str(output)], repo)
        require(validation.returncode != 0, "compact validator accepted passed validation with failure text")
        require("cannot include failure terms" in validation.stderr, "passed validation failure-text error not reported")


def test_compact_validator_status_parsing_is_hash_seed_stable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        output = write_compact_resume_ready_savepoint(
            repo,
            project_validation="failed-expected: failed: `python -m pytest tests/auth` - known failure; reason: known failure; previous lint passed",
            skipped_checks="python -m pytest tests/auth",
        )
        for seed in ["0", "3", "42"]:
            env = {**os.environ, "PYTHONHASHSEED": seed}
            validation = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            require(validation.returncode == 0, f"validator status parsing changed under PYTHONHASHSEED={seed}: {validation.stderr or validation.stdout}")


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
    helper = load_contract_helper()
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
    helper = load_contract_helper()
    helper.git_output = lambda _args, _cwd: ""
    require(helper.find_git_root(ROOT) is None, "empty git root output should not crash")


def test_output_contract_checker_rejects_directory_path_without_traceback() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / "contract-dir"
        directory.mkdir()
        result = run([sys.executable, str(OUTPUT_CONTRACT_CHECKER), "--path", str(directory)], ROOT)
        combined = f"{result.stdout}\n{result.stderr}"
        require(result.returncode == 1, "output contract checker should reject directory path")
        require("failed to read file" in result.stderr, "directory path should produce clean read error")
        require("Traceback" not in combined, "directory path should not produce traceback")


def test_refuses_directory_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint"
        output.mkdir()
        result = run([sys.executable, str(RENDER_HELPER), "--input", str(input_path), "--output", str(output), "--force"], repo)
        require(result.returncode != 0, "renderer wrote to directory output")
        require("output path is a directory" in result.stderr, "directory refusal message missing")


def test_refuses_savepoint_named_directory_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / ".savepoint" / "SAVEPOINT.md"
        output.mkdir(parents=True)
        result = run([sys.executable, str(RENDER_HELPER), "--input", str(input_path), "--output", str(output), "--force"], repo)
        require(result.returncode != 0, "renderer wrote to SAVEPOINT.md directory output")
        require("output path is a directory" in result.stderr, "SAVEPOINT.md directory refusal message missing")


def test_refuses_non_savepoint_output_name() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        input_path = semantic_input(repo)
        output = repo / "foo.md"
        result = run([sys.executable, str(RENDER_HELPER), "--input", str(input_path), "--output", str(output)], repo)
        require(result.returncode != 0, "renderer wrote non-SAVEPOINT.md output")
        require("output path must end with SAVEPOINT.md" in result.stderr, "output name refusal message missing")
        require(not output.exists(), "invalid output path should not be written")


def test_reports_parent_mkdir_oserror() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_repo(Path(tmp))
        input_path = semantic_input(repo)
        parent = repo / "not-a-directory"
        parent.write_text("file blocks mkdir\n", encoding="utf-8")
        output = parent / "SAVEPOINT.md"
        result = run([sys.executable, str(RENDER_HELPER), "--input", str(input_path), "--output", str(output)], repo)
        require(result.returncode != 0, "renderer wrote through file parent")
        require("failed to write output" in result.stderr, "mkdir failure message missing")
        require("Traceback" not in result.stderr, "mkdir failure should not print traceback")


def test_write_output_uses_portable_lf_open() -> None:
    helper = load_render_helper()
    original_open = getattr(helper, "open", None)
    calls: list[tuple[str, str, str, str]] = []

    def fake_open(path: Path, mode: str, *, encoding: str, newline: str):
        calls.append((str(path), mode, encoding, newline))
        raise PermissionError("blocked")

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "SAVEPOINT.md"
        try:
            helper.open = fake_open
            result = helper.write_output(output, "draft")
        finally:
            if original_open is None:
                del helper.open
            else:
                helper.open = original_open

    wrote, error = result
    require(not wrote, "write_output should report open failure")
    require(calls == [(str(output), "w", "utf-8", "\n")], "write_output should use portable open with LF newlines")
    require("failed to write output" in (error or ""), "render write failure message missing")


def main() -> int:
    tests = [
        test_truncates_large_git_snapshot,
        test_refuses_overwrite_without_force,
        test_renderer_writes_resume_ready_savepoint_from_json_input,
        test_renderer_does_not_mark_first_unstaged_file_as_staged,
        test_renderer_classifies_status_codes_without_losing_columns,
        test_renderer_default_output_stays_compact,
        test_renderer_accepts_minimal_ready_json_input,
        test_renderer_records_recovery_uncertainty_inputs,
        test_renderer_records_not_run_when_savepoint_validation_is_omitted,
        test_renderer_minimal_json_without_project_validation_stays_unsafe,
        test_renderer_exit_code_uses_marker_not_body_resume_ready_text,
        test_renderer_failed_project_validation_stays_unsafe,
        test_validation_status_token_matrix_is_consistent,
        test_renderer_rejects_removed_project_validation_input,
        test_renderer_rejects_removed_input_aliases,
        test_renderer_passed_project_validation_requires_complete_command_fields,
        test_renderer_structured_passed_validation_with_failure_text_stays_unsafe,
        test_renderer_structured_passed_validation_with_failing_text_stays_unsafe,
        test_renderer_not_run_justified_project_validation_can_resume_ready,
        test_renderer_failed_expected_project_validation_can_resume_ready,
        test_renderer_failed_expected_without_command_fields_stays_unsafe,
        test_renderer_failed_expected_with_passed_command_stays_unsafe,
        test_renderer_failed_expected_with_passed_result_failure_word_summary_stays_unsafe,
        test_renderer_failed_expected_with_next_validation_none_stays_unsafe_with_specific_blocker,
        test_renderer_not_run_justified_with_reason_none_stays_unsafe_with_specific_blocker,
        test_renderer_not_run_justified_without_next_validation_stays_unsafe,
        test_renderer_failed_blocking_project_validation_stays_unsafe,
        test_renderer_missing_next_action_stays_unsafe,
        test_renderer_unresolved_blocker_stays_unsafe,
        test_renderer_rejects_removed_blockers_alias,
        test_renderer_keeps_savepoint_unsafe_without_active_command_assertion,
        test_renderer_secret_scan_blocks_resume_ready,
        test_renderer_rejects_secret_bearing_input_before_render,
        test_renderer_redacts_secret_even_when_scan_flag_is_omitted,
        test_savepoint_cli_save_validate_and_inspect,
        test_savepoint_cli_deletes_input_on_success_only_under_savepoint_dir,
        test_savepoint_cli_does_not_delete_input_outside_savepoint_dir,
        test_savepoint_cli_does_not_delete_outside_symlink_to_savepoint_input,
        test_delete_input_on_success_requires_path_itself_under_savepoint_dir,
        test_delete_input_on_success_handles_path_resolution_error,
        test_savepoint_cli_keeps_input_when_save_is_not_resume_ready,
        test_savepoint_cli_direct_flags_can_render_passed_savepoint,
        test_savepoint_cli_direct_flags_can_render_not_run_justified_savepoint,
        test_savepoint_cli_rejects_input_and_direct_flags_together,
        test_savepoint_cli_rejects_incomplete_direct_flags,
        test_savepoint_cli_init_input_defaults_to_unknown_validation,
        test_savepoint_cli_inspect_json_reports_invalid_marker,
        test_savepoint_cli_inspect_json_requires_valid_savepoint_for_resume_ready,
        test_savepoint_cli_inspect_missing_or_not_savepoint_returns_2,
        test_savepoint_cli_validate_directory_returns_error,
        test_root_savepoint_cli_forwards_to_portable_cli,
        test_savepoint_cli_text_mode_does_not_write_recovery_artifact,
        test_validator_accepts_compact_resume_ready_file_without_repetitive_sections,
        test_compact_validator_accepts_not_run_justified_project_validation,
        test_compact_validator_accepts_failed_expected_project_validation,
        test_compact_validator_rejects_not_run_unknown_project_validation,
        test_compact_validator_rejects_failed_blocking_project_validation,
        test_compact_validator_rejects_expected_failure_without_next_validation,
        test_compact_validator_rejects_expected_failure_without_command_evidence,
        test_compact_validator_rejects_expected_failure_with_passed_command_evidence,
        test_compact_validator_rejects_not_run_justified_without_reason,
        test_compact_validator_rejects_expected_failure_without_reason,
        test_compact_validator_rejects_passed_validation_with_failure_text,
        test_compact_validator_status_parsing_is_hash_seed_stable,
        test_compact_validator_still_requires_disk_snapshot_fields,
        test_compact_validator_rejects_skipped_none_without_project_pass,
        test_compact_validator_requires_redaction_evidence,
        test_compact_validator_requires_next_action_evidence,
        test_compact_validator_requires_disk_state_wins_language,
        test_renderer_revalidates_final_rewrite_before_success,
        test_run_command_handles_oserror,
        test_find_git_root_handles_empty_output,
        test_output_contract_checker_rejects_directory_path_without_traceback,
        test_refuses_directory_output,
        test_refuses_savepoint_named_directory_output,
        test_refuses_non_savepoint_output_name,
        test_reports_parent_mkdir_oserror,
        test_write_output_uses_portable_lf_open,
    ]
    for test in tests:
        test()
        print(f"ok: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
