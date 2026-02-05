#!/usr/bin/env python3
"""Minimal smoke test for `tf --version`.

This script runs `tf --version` and validates:
- Exit code is 0
- Output is non-empty
- Output matches basic SemVer format (e.g., 0.1.0 or 1.2.3-alpha.1)

Usage:
    python tests/smoke_test_version.py

Returns:
    Exit code 0 if all checks pass, 1 otherwise.
"""

from __future__ import annotations

import re
import subprocess
import sys


def run_tf_version() -> tuple[int, str]:
    """Run `tf --version` and return (exit_code, stdout)."""
    try:
        result = subprocess.run(
            ["tf", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        print("ERROR: 'tf' command not found in PATH", file=sys.stderr)
        return -1, ""
    except subprocess.TimeoutExpired:
        print("ERROR: 'tf --version' timed out after 30s", file=sys.stderr)
        return -1, ""


def is_valid_semver(version: str) -> bool:
    """Check if version matches basic SemVer format.
    
    Supports:
    - 0.1.0
    - 1.2.3
    - 1.2.3-alpha.1
    - 1.2.3+build.123
    - 1.2.3-alpha.1+build.123
    """
    # Basic SemVer pattern: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
    return bool(re.match(pattern, version))


def main() -> int:
    """Run smoke test and return exit code."""
    print("Running smoke test: tf --version")
    print("-" * 40)
    
    exit_code, output = run_tf_version()
    
    # Check 1: Exit code is 0
    if exit_code != 0:
        print(f"FAIL: Exit code is {exit_code}, expected 0", file=sys.stderr)
        return 1
    print("✓ Exit code is 0")
    
    # Check 2: Output is non-empty
    if not output:
        print("FAIL: Output is empty", file=sys.stderr)
        return 1
    print(f"✓ Output is non-empty: '{output}'")
    
    # Check 3: Matches SemVer format
    if not is_valid_semver(output):
        print(f"FAIL: Output '{output}' does not match SemVer format", file=sys.stderr)
        return 1
    print(f"✓ Output matches SemVer format")
    
    print("-" * 40)
    print("All smoke tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
