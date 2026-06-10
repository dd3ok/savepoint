#!/usr/bin/env python3
"""Validate example savepoint artifacts."""

from pathlib import Path
import runpy
import sys

sys.argv = [
    sys.argv[0],
    "--check",
    "examples",
    "--check",
    "schema",
    "--check",
    "markers",
    "--check",
    "text-example",
    "--check",
    "detail-artifacts",
    "--check",
    "secrets",
]
runpy.run_path(str(Path(__file__).with_name("validate-repo.py")), run_name="__main__")
