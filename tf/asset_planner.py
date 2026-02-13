"""Canonical asset planner for TF workflow asset routing and installation decisions.

This module provides a single, unified implementation for:
- Asset manifest parsing and planning
- Asset download and installation
- Local vs remote source resolution
- Bundle entry classification and routing

Used by init, sync, and update commands to ensure consistent behavior.
"""
from __future__ import annotations

import filecmp
import os
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

DEFAULT_UVX_SOURCE = "git+https://github.com/legout/pi-ticketflow"
DEFAULT_RAW_REPO_URL = "https://raw.githubusercontent.com/legout/pi-ticketflow/main"


class AssetAction(Enum):
    """Action to take for an asset."""

    INSTALL = "install"  # New file to install
    UPDATE = "update"  # Existing file with updates available
    SKIP = "skip"  # Skip (already exists, no changes)
    REMOVE = "remove"  # Remove (not used currently)


@dataclass(frozen=True)
class AssetEntry:
    """A single asset entry in the manifest."""

    rel_path: str  # Repository-relative path (e.g., "agents/test.md")
    source_url: Optional[str] = None  # Remote URL if downloading
    local_path: Optional[Path] = None  # Local path if copying from repo


@dataclass
class AssetPlan:
    """A planned asset operation."""

    entry: AssetEntry
    dest_path: Path
    action: AssetAction
    executable: bool = False
    current_content: Optional[bytes] = None  # For update comparison
    new_content: Optional[bytes] = None  # Downloaded/copied content


@dataclass
class PlanResult:
    """Result of planning operation."""

    to_install: List[AssetPlan] = field(default_factory=list)
    to_update: List[AssetPlan] = field(default_factory=list)
    skipped: List[AssetPlan] = field(default_factory=list)
    errors: List[Tuple[AssetPlan, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.to_install) + len(self.to_update) + len(self.skipped)


@dataclass
class ExecutionResult:
    """Result of executing a plan."""

    installed: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: List[str] = field(default_factory=list)


def _read_text(path: Path) -> str:
    """Read text file, return empty string on error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def find_repo_root() -> Optional[Path]:
    """Locate a checked-out pi-ticketflow repo root for offline/dev installs."""
    # Check environment variable
    env_root = os.environ.get("TF_REPO_ROOT", "").strip()
    if env_root:
        p = Path(env_root).expanduser()
        if p.exists():
            return p

    # Check .tf/cli-root marker files
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        root_file = parent / ".tf/cli-root"
        root_text = _read_text(root_file)
        if root_text:
            p = Path(root_text).expanduser()
            if p.exists():
                return p

    home_root_file = Path.home() / ".tf/cli-root"
    root_text = _read_text(home_root_file)
    if root_text:
        p = Path(root_text).expanduser()
        if p.exists():
            return p

    # Fallback: detect if we're running from within the repo itself
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").is_file() and (parent / "tf").is_dir():
            return parent

    return None


def raw_base_from_source(source: str) -> Optional[str]:
    """Convert a git URL to a raw GitHub content URL."""
    cleaned = source.strip()
    if cleaned.startswith("git+"):
        cleaned = cleaned[4:]
    if not cleaned.startswith("https://github.com/"):
        return None

    cleaned = cleaned.split("#", 1)[0].split("?", 1)[0]
    cleaned = cleaned[len("https://github.com/") :]
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    if "@" in cleaned:
        repo_part, ref = cleaned.split("@", 1)
    else:
        repo_part, ref = cleaned, "main"

    if "/" not in repo_part:
        return None

    owner, repo = repo_part.split("/", 1)
    ref = ref or "main"
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}"


def resolve_raw_base() -> str:
    """Resolve the raw content base URL from environment or default."""
    uvx_source = os.environ.get("TF_UVX_FROM") or DEFAULT_UVX_SOURCE
    return raw_base_from_source(uvx_source) or DEFAULT_RAW_REPO_URL


def _download(url: str, dest: Path, timeout: int = 30) -> None:
    """Download URL contents to destination path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def _make_executable(path: Path) -> None:
    """Make a file executable (best effort - non-fatal on failure)."""
    try:
        path.chmod(path.stat().st_mode | 0o111)
    except Exception:
        pass


def _download_bytes(url: str, timeout: int = 30) -> bytes:
    """Download URL contents and return as bytes."""
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def _parse_manifest(text: str) -> List[str]:
    """Parse manifest text into list of relative paths."""
    out: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append(stripped)
    return out


def load_manifest(repo_root: Optional[Path], raw_base: Optional[str] = None) -> List[str]:
    """Load config/install-manifest.txt from local repo or remote raw URL."""
    # Try local repo first
    if repo_root:
        mp = repo_root / "config/install-manifest.txt"
        if mp.exists():
            return _parse_manifest(mp.read_text(encoding="utf-8"))

    # Fall back to remote
    raw_base = raw_base or resolve_raw_base()
    url = f"{raw_base}/config/install-manifest.txt"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return _parse_manifest(resp.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Unable to download install manifest: {exc}") from exc


def classify_asset(rel_path: str, project_root: Path) -> Optional[Tuple[Path, bool]]:
    """Classify a manifest entry and return its destination path and executable flag.

    Returns None if the entry should be skipped (e.g., bin/tf).
    """
    # Skip CLI shim - projects don't install the CLI
    if rel_path == "bin/tf":
        return None

    # Skip manifest itself
    if rel_path == "config/install-manifest.txt":
        return None

    # Workflow assets go to project root directories.
    if rel_path.startswith(("agents/", "prompts/", "skills/")):
        return (project_root / rel_path, False)

    # Config files go to .tf/
    if rel_path == "config/settings.json":
        return (project_root / ".tf" / "config" / "settings.json", False)

    if rel_path.startswith("config/workflows/"):
        return (project_root / ".tf" / rel_path, False)

    # Scripts go to .tf/scripts/
    if rel_path.startswith("scripts/"):
        executable = rel_path.endswith(".py") or rel_path.endswith(".sh")
        return (project_root / ".tf" / rel_path, executable)

    return None


def create_asset_plan(
    rel_path: str,
    project_root: Path,
    repo_root: Optional[Path] = None,
    raw_base: Optional[str] = None,
) -> Optional[AssetPlan]:
    """Create an asset plan for a single manifest entry."""
    classified = classify_asset(rel_path, project_root)
    if classified is None:
        return None

    dest_path, executable = classified
    raw_base = raw_base or resolve_raw_base()

    # Determine source
    local_src = (repo_root / rel_path) if repo_root else None
    if local_src and local_src.exists():
        entry = AssetEntry(rel_path=rel_path, local_path=local_src)
    else:
        entry = AssetEntry(rel_path=rel_path, source_url=f"{raw_base}/{rel_path}")

    return AssetPlan(
        entry=entry,
        dest_path=dest_path,
        action=AssetAction.INSTALL,  # Will be refined during planning
        executable=executable,
    )


def plan_installation(
    project_root: Path,
    manifest: Iterable[str],
    *,
    repo_root: Optional[Path] = None,
    raw_base: Optional[str] = None,
    check_updates: bool = False,
    force: bool = False,
) -> PlanResult:
    """Plan asset installation without executing.

    Args:
        project_root: Root of the target project
        manifest: List of relative paths from manifest
        repo_root: Optional local repo root for offline installs
        raw_base: Optional raw URL base for remote downloads
        check_updates: Whether to check for updates to existing files
        force: Whether to force re-installation of existing files

    Returns:
        PlanResult with categorized asset plans
    """
    result = PlanResult()
    raw_base = raw_base or resolve_raw_base()
    repo_root = repo_root or find_repo_root()

    for rel_path in manifest:
        plan = create_asset_plan(rel_path, project_root, repo_root, raw_base)
        if plan is None:
            continue

        dest = plan.dest_path

        if not dest.exists():
            # New file to install
            plan.action = AssetAction.INSTALL
            result.to_install.append(plan)
        elif force:
            # Force re-installation
            plan.action = AssetAction.UPDATE
            result.to_update.append(plan)
        elif check_updates:
            # Check if content differs
            try:
                current_content = dest.read_bytes()
                if plan.entry.local_path and plan.entry.local_path.exists():
                    new_content = plan.entry.local_path.read_bytes()
                elif plan.entry.source_url:
                    new_content = _download_bytes(plan.entry.source_url)
                else:
                    new_content = current_content

                if current_content != new_content:
                    plan.action = AssetAction.UPDATE
                    plan.current_content = current_content
                    plan.new_content = new_content
                    result.to_update.append(plan)
                else:
                    plan.action = AssetAction.SKIP
                    result.skipped.append(plan)
            except Exception as exc:
                result.errors.append((plan, f"Failed to check for updates: {exc}"))
        else:
            # Skip existing files
            plan.action = AssetAction.SKIP
            result.skipped.append(plan)

    return result


def execute_plan(plan_result: PlanResult, *, dry_run: bool = False) -> ExecutionResult:
    """Execute a planned installation.

    Args:
        plan_result: The plan to execute
        dry_run: If True, don't actually write files

    Returns:
        ExecutionResult with counts and any errors
    """
    result = ExecutionResult()

    for plan in plan_result.to_install:
        try:
            if not dry_run:
                plan.dest_path.parent.mkdir(parents=True, exist_ok=True)
                if plan.entry.local_path and plan.entry.local_path.exists():
                    shutil.copy2(plan.entry.local_path, plan.dest_path)
                elif plan.entry.source_url:
                    _download(plan.entry.source_url, plan.dest_path)
                else:
                    raise RuntimeError("No source available for asset")

                if plan.executable:
                    _make_executable(plan.dest_path)
            result.installed += 1
        except Exception as exc:
            result.errors += 1
            result.error_details.append(f"{plan.entry.rel_path}: {exc}")

    for plan in plan_result.to_update:
        try:
            if not dry_run:
                plan.dest_path.parent.mkdir(parents=True, exist_ok=True)
                if plan.new_content is not None:
                    plan.dest_path.write_bytes(plan.new_content)
                elif plan.entry.local_path and plan.entry.local_path.exists():
                    shutil.copy2(plan.entry.local_path, plan.dest_path)
                elif plan.entry.source_url:
                    _download(plan.entry.source_url, plan.dest_path)

                if plan.executable:
                    _make_executable(plan.dest_path)
            result.updated += 1
        except Exception as exc:
            result.errors += 1
            result.error_details.append(f"{plan.entry.rel_path}: {exc}")

    result.skipped = len(plan_result.skipped)
    result.errors += len(plan_result.errors)
    for plan, err in plan_result.errors:
        result.error_details.append(f"{plan.entry.rel_path}: {err}")

    return result


def install_bundle(
    project_root: Path,
    *,
    overwrite: bool = False,
    repo_root: Optional[Path] = None,
) -> Tuple[int, int]:
    """Ensure TF workflow assets exist in the project (legacy compat wrapper).

    Returns: (installed_count, skipped_count)
    """
    repo_root = repo_root or find_repo_root()
    manifest = load_manifest(repo_root)
    if not manifest:
        raise RuntimeError("Empty manifest")

    plan_result = plan_installation(
        project_root,
        manifest,
        repo_root=repo_root,
        force=overwrite,
    )

    exec_result = execute_plan(plan_result)

    if exec_result.errors > 0:
        error_msg = "; ".join(exec_result.error_details)
        raise RuntimeError(f"Bundle installation failed: {error_msg}")

    # Return total changes (installed + updated) and skipped
    total_changed = exec_result.installed + exec_result.updated
    return (total_changed, exec_result.skipped)


def check_for_updates(
    project_root: Path,
    *,
    repo_root: Optional[Path] = None,
    raw_base: Optional[str] = None,
) -> Tuple[List[AssetPlan], List[str]]:
    """Check which assets have updates available.

    Returns:
        Tuple of (list of assets with updates, list of errors)
    """
    repo_root = repo_root or find_repo_root()
    raw_base = raw_base or resolve_raw_base()

    try:
        manifest = load_manifest(repo_root, raw_base)
    except RuntimeError as exc:
        return ([], [str(exc)])

    plan_result = plan_installation(
        project_root,
        manifest,
        repo_root=repo_root,
        raw_base=raw_base,
        check_updates=True,
    )

    errors = [err for _, err in plan_result.errors]
    return (plan_result.to_update, errors)


def update_assets(
    project_root: Path,
    *,
    repo_root: Optional[Path] = None,
    raw_base: Optional[str] = None,
    select: Optional[List[str]] = None,
) -> ExecutionResult:
    """Update assets in a project.

    Args:
        project_root: Root of the target project
        repo_root: Optional local repo root
        raw_base: Optional raw URL base
        select: Optional list of specific rel_paths to update (None = all)

    Returns:
        ExecutionResult with update counts
    """
    repo_root = repo_root or find_repo_root()
    raw_base = raw_base or resolve_raw_base()

    manifest = load_manifest(repo_root, raw_base)

    if select:
        manifest = [m for m in manifest if m in select]

    plan_result = plan_installation(
        project_root,
        manifest,
        repo_root=repo_root,
        raw_base=raw_base,
        check_updates=True,
    )

    # Only execute updates, not new installs (unless selected)
    filtered_result = PlanResult(
        to_install=[],  # Don't install new files during update
        to_update=plan_result.to_update,
        skipped=plan_result.skipped,
        errors=plan_result.errors,
    )

    return execute_plan(filtered_result)
