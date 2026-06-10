#!/usr/bin/env python3
"""Validate marker block shape."""

from pathlib import Path
import runpy
import sys

sys.argv = [sys.argv[0], "--check", "markers"]
runpy.run_path(str(Path(__file__).with_name("validate-repo.py")), run_name="__main__")
