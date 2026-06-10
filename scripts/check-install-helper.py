#!/usr/bin/env python3
"""Validate the safe install helper."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_installer():
    if not INSTALLER.exists():
        fail("scripts/install.py is missing")
    spec = importlib.util.spec_from_file_location("install_helper", INSTALLER)
    if spec is None or spec.loader is None:
        fail("could not load scripts/install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALLER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


class FakeDestination:
    def __init__(self, *, exists: bool, is_symlink: bool) -> None:
        self._exists = exists
        self._is_symlink = is_symlink

    def exists(self) -> bool:
        return self._exists

    def is_symlink(self) -> bool:
        return self._is_symlink


def test_resolve_destinations() -> None:
    installer = load_installer()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        repo = base / "repo"
        require(
            installer.resolve_destination("codex", "user", repo_root=repo, home=home)
            == home / ".agents" / "skills" / "savepoint",
            "codex user destination is wrong",
        )
        require(
            installer.resolve_destination("codex", "repo", repo_root=repo, home=home)
            == repo / ".agents" / "skills" / "savepoint",
            "codex repo destination is wrong",
        )
        require(
            installer.resolve_destination("claude", "user", repo_root=repo, home=home)
            == home / ".claude" / "skills" / "savepoint",
            "claude user destination is wrong",
        )
        require(
            installer.resolve_destination("claude", "repo", repo_root=repo, home=home)
            == repo / ".claude" / "skills" / "savepoint",
            "claude repo destination is wrong",
        )


def test_destination_occupancy_includes_broken_symlink() -> None:
    installer = load_installer()
    require(
        installer.destination_is_occupied(FakeDestination(exists=False, is_symlink=True)),
        "broken symlink destination is not treated as occupied",
    )


def test_dry_run_writes_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        result = run_installer("--target", "codex", "--scope", "repo", "--repo-root", str(repo))
        destination = repo / ".agents" / "skills" / "savepoint"
        require(result.returncode == 0, result.stderr or result.stdout)
        require("Dry run: yes" in result.stdout, "dry run output missing")
        require("No files changed" in result.stdout, "dry run no-change message missing")
        require(not destination.exists(), "dry run created files")
        require(not any(repo.iterdir()), "dry run wrote repo files")


def test_apply_copies_skill() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        result = run_installer("--target", "codex", "--scope", "repo", "--repo-root", str(repo), "--apply")
        destination = repo / ".agents" / "skills" / "savepoint"
        require(result.returncode == 0, result.stderr or result.stdout)
        require((destination / "SKILL.md").exists(), "SKILL.md was not copied")
        require((destination / "references" / "savepoint-template.md").exists(), "references were not copied")
        require((destination / "scripts" / "validate_savepoint.py").exists(), "scripts were not copied")
        require((destination / "schemas" / "savepoint-v1.schema.json").exists(), "schemas were not copied")
        require(not list(destination.rglob("__pycache__")), "__pycache__ directories were copied")


def test_existing_destination_refused() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        destination = repo / ".agents" / "skills" / "savepoint"
        destination.mkdir(parents=True)
        result = run_installer("--target", "codex", "--scope", "repo", "--repo-root", str(repo), "--apply")
        require(result.returncode != 0, "existing destination was not refused")
        require("Destination already exists" in result.stderr, "missing existing destination error")


def test_broken_symlink_destination_refused() -> str | None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        missing_target = Path(tmp) / "missing-skill"
        destination = repo / ".agents" / "skills" / "savepoint"
        destination.parent.mkdir(parents=True)
        try:
            destination.symlink_to(missing_target, target_is_directory=True)
        except OSError as exc:
            return str(exc)

        result = run_installer("--target", "codex", "--scope", "repo", "--repo-root", str(repo), "--apply")
        require(result.returncode != 0, "broken symlink destination was not refused")
        require("Destination already exists" in result.stderr, "missing existing destination error")
    return None


def test_missing_repo_root_refused() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo-typo"
        result = run_installer("--target", "codex", "--scope", "repo", "--repo-root", str(repo), "--apply")
        require(result.returncode != 0, "missing repo root was not refused")
        require("repo root does not exist" in result.stderr, "missing repo root error")
        require(not repo.exists(), "missing repo root was created")


def test_gitignore_is_explicit_and_apply_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        dry_run = run_installer(
            "--target",
            "codex",
            "--scope",
            "repo",
            "--repo-root",
            str(repo),
            "--add-gitignore",
        )
        require(dry_run.returncode == 0, dry_run.stderr or dry_run.stdout)
        require(not (repo / ".gitignore").exists(), "dry run wrote .gitignore")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        existing = "node_modules/\r\n# keep\r\n"
        (repo / ".gitignore").write_text(existing, encoding="utf-8", newline="")
        applied = run_installer(
            "--target",
            "codex",
            "--scope",
            "repo",
            "--repo-root",
            str(repo),
            "--apply",
            "--add-gitignore",
        )
        require(applied.returncode == 0, applied.stderr or applied.stdout)
        gitignore = (repo / ".gitignore").read_text(encoding="utf-8", newline="")
        require(gitignore == f"{existing}.savepoint/\r\n", ".gitignore content was not preserved")

        repeat = run_installer(
            "--target",
            "claude",
            "--scope",
            "repo",
            "--repo-root",
            str(repo),
            "--apply",
            "--add-gitignore",
        )
        require(repeat.returncode == 0, repeat.stderr or repeat.stdout)
        gitignore = (repo / ".gitignore").read_text(encoding="utf-8", newline="")
        require(gitignore.count(".savepoint/") == 1, ".gitignore entry was duplicated")


def test_invalid_argument_combinations() -> None:
    apply_and_dry_run = run_installer("--target", "codex", "--scope", "repo", "--apply", "--dry-run")
    require(apply_and_dry_run.returncode != 0, "--apply and --dry-run were accepted together")
    require("--apply and --dry-run cannot be used together" in apply_and_dry_run.stderr, "missing apply/dry-run error")

    user_gitignore = run_installer("--target", "codex", "--scope", "user", "--add-gitignore")
    require(user_gitignore.returncode != 0, "--add-gitignore was accepted with user scope")
    require("--add-gitignore is only valid with --scope repo" in user_gitignore.stderr, "missing gitignore scope error")


def main() -> int:
    tests = [
        test_resolve_destinations,
        test_destination_occupancy_includes_broken_symlink,
        test_dry_run_writes_nothing,
        test_apply_copies_skill,
        test_existing_destination_refused,
        test_broken_symlink_destination_refused,
        test_missing_repo_root_refused,
        test_gitignore_is_explicit_and_apply_only,
        test_invalid_argument_combinations,
    ]
    for test in tests:
        result = test()
        if result:
            print(f"skip: {test.__name__} ({result})")
        else:
            print(f"ok: {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
