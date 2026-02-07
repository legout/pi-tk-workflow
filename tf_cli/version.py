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
3. Git tag (for git checkouts with tags, strips 'v' prefix)
4. "unknown" (if VERSION cannot be found)

Release validation:
- verify_package_json_version(): Verifies package.json version matches git tag
"""

from __future__ import annotations

import json
import os
import subprocess
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


def _get_git_tag_version(repo_root: Optional[Path] = None) -> Optional[str]:
    """Get version from git tag.
    
    Attempts to get the current git tag (if on a tagged commit) or the
    latest tag. Strips the 'v' prefix commonly used in git tags.
    
    Args:
        repo_root: Optional path to git repository root. If not provided,
                  searches from current working directory.
    
    Returns:
        Version string with 'v' prefix stripped (e.g., "1.0.0" from "v1.0.0"),
        or None if git is not available or no tags exist.
    
    Example:
        >>> version = _get_git_tag_version()
        >>> print(version)  # "1.0.0" (from tag "v1.0.0")
    """
    try:
        # Determine git cwd
        git_cwd = str(repo_root) if repo_root else "."
        
        # First, try to get the exact tag for current commit
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            cwd=git_cwd,
            check=False,
        )
        
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Strip 'v' prefix if present
            return tag[1:] if tag.startswith("v") else tag
        
        # If no exact match, try to get the latest tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=git_cwd,
            check=False,
        )
        
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Strip 'v' prefix if present
            return tag[1:] if tag.startswith("v") else tag
            
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    
    return None


def verify_package_json_version(repo_root: Optional[Path] = None) -> dict:
    """Verify that package.json version matches the git tag version.
    
    This is useful for release validation to ensure the package.json
    version is synchronized with the git tag.
    
    Args:
        repo_root: Optional path to repository root. If not provided,
                  attempts to resolve from module location.
    
    Returns:
        Dictionary with verification results:
        - ok: bool - True if versions match or verification passed
        - package_version: str|None - version from package.json
        - git_version: str|None - version from git tag
        - error: str|None - error message if verification failed
    
    Example:
        >>> result = verify_package_json_version()
        >>> if not result["ok"]:
        ...     print(f"Version mismatch: {result['error']}")
    """
    # Resolve repo root if not provided
    if repo_root is None:
        repo_root = _resolve_repo_root()
    
    result: dict = {
        "ok": False,
        "package_version": None,
        "git_version": None,
        "error": None,
    }
    
    # Check if we're in a git repo
    if repo_root is None:
        result["error"] = "Not in a git repository"
        return result
    
    # Read package.json
    package_json_path = repo_root / "package.json"
    if not package_json_path.is_file():
        result["error"] = f"package.json not found at {package_json_path}"
        return result
    
    try:
        package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
        package_version = package_data.get("version")
        result["package_version"] = package_version
        
        if not package_version:
            result["error"] = "No version field in package.json"
            return result
    except (json.JSONDecodeError, OSError) as e:
        result["error"] = f"Error reading package.json: {e}"
        return result
    
    # Get git tag version
    git_version = _get_git_tag_version(repo_root)
    result["git_version"] = git_version
    
    if git_version is None:
        result["error"] = "No git tag found for version comparison"
        return result
    
    # Compare versions
    if package_version != git_version:
        result["error"] = (
            f"Version mismatch: package.json has {package_version}, "
            f"git tag has {git_version}"
        )
        return result
    
    result["ok"] = True
    return result


def get_version() -> str:
    """Return the current Ticketflow version.

    This function works across different installation modes:
    - Git checkout: finds VERSION in repo root
    - Pip install: finds VERSION relative to installed package
    - Uvx install: same as pip install
    - Git tag: falls back to git tag if VERSION file not found

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

    # Try git tag as third fallback (for git checkouts without VERSION file)
    if repo_root:
        git_version = _get_git_tag_version(repo_root)
        if git_version:
            return git_version

    return "unknown"


def __getattr__(name: str) -> str:
    """Lazy loading for __version__ to avoid caching issues at import time."""
    if name == "__version__":
        return get_version()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Public API
__all__ = [
    "get_version",
    "verify_package_json_version",
    "__version__",
]
