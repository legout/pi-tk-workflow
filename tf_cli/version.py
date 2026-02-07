"""Version retrieval helper for Ticketflow CLI.

This module provides a centralized function to retrieve the current version
regardless of how the CLI is installed or executed.

Supported install modes:
- Running from a git checkout (development)
- Installed as a Python package via pip
- Installed via uvx from git

Fallback order:
1. VERSION file in git repo root (for development/git checkouts)
2. VERSION file at package root (for pip/uvx installs)
3. "unknown" (if VERSION cannot be found)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _resolve_repo_root() -> Optional[Path]:
    """Find the repository root by looking for markers.
    
    Searches upward from the location of this module to find the repo root,
    ensuring we find the correct project even when run from a different
ticketflow-based project directory.
    """
    # Start from this module's location and walk up
    module_dir = Path(__file__).resolve().parent
    for parent in [module_dir, *module_dir.parents]:
        # Look for .tf directory as a marker of repo root
        if (parent / ".tf").is_dir() and (parent / "VERSION").is_file():
            return parent
        # Also check for pyproject.toml + tf_cli combination
        if (parent / "pyproject.toml").is_file() and (parent / "tf_cli").is_dir():
            return parent
    return None


def _read_version_file(path: Path) -> Optional[str]:
    """Safely read version from a file."""
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return None


def get_version() -> str:
    """Return the current Ticketflow version.

    This function works across different installation modes:
    - Git checkout: finds VERSION in repo root
    - Pip install: finds VERSION relative to installed package
    - Uvx install: same as pip install

    Returns:
        Version string (e.g., "0.1.0") or "unknown" if version
        cannot be determined.

    Example:
        >>> from tf_cli.version import get_version
        >>> print(get_version())
        0.1.0
    """
    # Try repo root first (for git checkouts/development)
    repo_root = _resolve_repo_root()
    if repo_root:
        version = _read_version_file(repo_root / "VERSION")
        if version:
            return version

    # Try relative to this module (for pip/uvx installs)
    # This file is in tf_cli/, so VERSION is at package root (parent of tf_cli/)
    package_root = Path(__file__).resolve().parent.parent
    version = _read_version_file(package_root / "VERSION")
    if version:
        return version

    return "unknown"


def __getattr__(name: str) -> str:
    """Lazy loading for __version__ to avoid caching issues at import time."""
    if name == "__version__":
        return get_version()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
