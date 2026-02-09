from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .utils import find_project_root, merge, read_json

DEFAULT_MCP_SERVERS = [
    "context7",
    "exa",
    "grep_app",
    "zai-web-search",
    "zai-web-reader",
    "zai-vision",
]

REQUIRED_EXTENSIONS = [
    "pi-subagents",
    "pi-model-switch",
    "pi-prompt-template-model",
]

OPTIONAL_EXTENSIONS = [
    "pi-mcp-adapter",
    "pi-review-loop",
    "pi-web-access",
]


def read_toml(path: Path) -> Dict:
    """Parse a TOML file and return as dict.

    Handles basic TOML syntax including:
    - [section] headers
    - key = "value" string values
    - key = true/false booleans
    - Comments (lines starting with #)

    Args:
        path: Path to TOML file

    Returns:
        Dict with nested structure matching TOML sections
    """
    if not path.exists():
        return {}
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return {}

    result: Dict = {}
    current_section = result

    for line in content.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Section header: [section] or [section.subsection]
        if line.startswith("[") and line.endswith("]"):
            section_path = line[1:-1].strip()
            # Navigate/create nested sections
            parts = section_path.split(".")
            current = result
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current_section = current
            continue

        # Key-value pair
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Strip inline comments (while respecting quotes)
            # Find first # that is not inside quotes
            in_quotes = None
            comment_pos = -1
            for i, char in enumerate(value):
                if char in ('"', "'"):
                    if in_quotes is None:
                        in_quotes = char
                    elif in_quotes == char:
                        in_quotes = None
                elif char == '#' and in_quotes is None:
                    comment_pos = i
                    break
            if comment_pos >= 0:
                value = value[:comment_pos].strip()

            # Handle string values (remove quotes)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # Handle booleans
            elif value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            # Handle integers
            elif re.match(r'^-?\d+$', value):
                value = int(value)

            current_section[key] = value

    return result


def resolve_target_base(args: argparse.Namespace) -> tuple[Path, bool, Path]:
    if args.project:
        project_root = Path(args.project).expanduser()
    else:
        project_root = find_project_root()
        if project_root is None:
            print(
                "No .tf directory found. Run in a project with .tf/.", file=sys.stderr
            )
            raise SystemExit(1)
    tf_base = project_root / ".tf"
    if not tf_base.is_dir():
        print(f"Project .tf directory not found: {tf_base}", file=sys.stderr)
        raise SystemExit(1)

    target_base = project_root / ".pi"
    return target_base, False, project_root


def load_workflow_config(project_root: Path) -> Dict:
    """Load TF workflow configuration for this project.

    After the install/init refactor, configuration is project-local.
    """

    project_config = project_root / ".tf/config/settings.json"
    return read_json(project_config)


def get_checker_tools(config: Dict) -> List[str]:
    checkers = config.get("checkers", {}) or {}
    cmds: set = set()
    for spec in checkers.values():
        for key in ("lint", "format", "typecheck"):
            cmd = spec.get(key)
            if not cmd:
                continue
            parts = cmd.split()
            if parts:
                cmds.add(parts[0])
    return sorted(cmds)


def get_mcp_servers(config: Dict) -> List[str]:
    mcp_servers = config.get("workflow", {}).get("mcpServers")
    if mcp_servers is None:
        return DEFAULT_MCP_SERVERS
    if isinstance(mcp_servers, list):
        return [str(s) for s in mcp_servers]
    return [str(mcp_servers)]


def check_cmd(name: str, failed: List[bool]) -> None:
    if shutil.which(name):
        print(f"[ok] {name}")
    else:
        print(f"[missing] {name}")
        failed.append(True)


def get_pi_list_cache() -> str:
    try:
        result = subprocess.run(["pi", "list"], capture_output=True, text=True)
        return result.stdout or ""
    except Exception:
        return ""


def check_extension(
    name: str, target_base: Path, list_out: str, optional: bool, failed: List[bool]
) -> None:
    global_path = Path.home() / ".pi/agent/extensions" / name
    project_path = target_base / "extensions" / name

    if global_path.is_dir() or project_path.is_dir():
        scope = "project" if project_path.is_dir() else "global"
        suffix = " (optional)" if optional else ""
        print(f"[ok] extension {name} ({scope}{suffix})")
        return

    if list_out and f"npm:{name}" in list_out:
        suffix = " (optional)" if optional else ""
        print(f"[ok] extension {name} (pi user package{suffix})")
        return

    if optional:
        print(f"[info] extension {name} (optional, not installed)")
        return

    print(f"[missing] extension {name}")
    failed.append(True)


def check_mcp_config(config: Dict, target_base: Path) -> None:
    mcp_servers = get_mcp_servers(config)
    if not mcp_servers:
        return

    # MCP config is global Pi config (not project-local).
    mcp_file = (Path.home() / ".pi" / "agent") / "mcp.json"

    if not mcp_file.exists():
        print(
            f"[info] mcp.json not found at {mcp_file} (MCP research optional; run 'tf login')"
        )
        return

    try:
        mcp_config = json.loads(mcp_file.read_text(encoding="utf-8"))
    except Exception:
        print(f"[warn] mcp.json unreadable at {mcp_file}")
        return

    servers = set((mcp_config.get("mcpServers") or {}).keys())
    missing = [s for s in mcp_servers if s not in servers]
    if missing:
        print(f"[warn] mcp.json ({mcp_file}) missing servers: {' '.join(missing)}")
    else:
        print(f"[ok] mcp.json ({mcp_file})")


def get_package_version(project_root: Path) -> Optional[str]:
    """Read version from package.json if it exists.

    Returns the version string if found and valid, None otherwise.
    Validates that the version is a non-empty string.
    """
    package_file = project_root / "package.json"
    if not package_file.exists():
        return None
    package_data = read_json(package_file)
    if not package_data:
        return None
    version = package_data.get("version")
    # Validate version is a non-empty string
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def get_pyproject_version(project_root: Path) -> Optional[str]:
    """Read version from pyproject.toml if it exists.

    Returns the version string if found and valid, None otherwise.
    Looks for version in [project] section per PEP 621.
    Validates that the version is a non-empty string.
    """
    pyproject_file = project_root / "pyproject.toml"
    if not pyproject_file.exists():
        return None
    data = read_toml(pyproject_file)
    if not data:
        return None
    # PEP 621: version is in [project] section
    project = data.get("project", {})
    version = project.get("version")
    # Validate version is a non-empty string
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def get_cargo_version(project_root: Path) -> Optional[str]:
    """Read version from Cargo.toml if it exists.

    Returns the version string if found and valid, None otherwise.
    Looks for version in [package] section.
    Validates that the version is a non-empty string.
    """
    cargo_file = project_root / "Cargo.toml"
    if not cargo_file.exists():
        return None
    data = read_toml(cargo_file)
    if not data:
        return None
    # Cargo.toml: version is in [package] section
    package = data.get("package", {})
    version = package.get("version")
    # Validate version is a non-empty string
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


# Priority order for manifest files (first match wins for canonical version)
MANIFEST_CHECKS = [
    ("pyproject.toml", get_pyproject_version),
    ("Cargo.toml", get_cargo_version),
    ("package.json", get_package_version),
]


def detect_manifest_versions(project_root: Path) -> Tuple[Optional[str], Optional[str], List[str], Dict[str, str]]:
    """Detect and return versions from all available package manifests.

    Args:
        project_root: Path to the project root

    Returns:
        Tuple of (canonical_version, canonical_manifest, found_manifests, all_versions)
        - canonical_version: The version from the highest priority manifest, or None
        - canonical_manifest: The name of the manifest that provided canonical_version, or None
        - found_manifests: List of manifest filenames that exist
        - all_versions: Dict mapping manifest name to its version (or "invalid" if unreadable)
    """
    found_manifests: List[str] = []
    all_versions: Dict[str, str] = {}
    canonical_version: Optional[str] = None
    canonical_manifest: Optional[str] = None

    for manifest_name, version_func in MANIFEST_CHECKS:
        version = version_func(project_root)
        manifest_path = project_root / manifest_name

        if manifest_path.exists():
            found_manifests.append(manifest_name)
            if version is not None:
                all_versions[manifest_name] = version
                # First valid version becomes canonical
                if canonical_version is None:
                    canonical_version = version
                    canonical_manifest = manifest_name
            else:
                all_versions[manifest_name] = "invalid"

    return canonical_version, canonical_manifest, found_manifests, all_versions


def get_version_file_version(project_root: Path) -> Optional[str]:
    """Read version from VERSION file if it exists.

    Returns the version string if found and non-empty, None otherwise.
    Prints a warning if the file exists but cannot be read (e.g., due to
    permission errors or encoding issues).
    """
    version_file = project_root / "VERSION"
    if not version_file.exists():
        return None
    try:
        content = version_file.read_text(encoding="utf-8").strip()
        return content if content else None
    except PermissionError as e:
        print(f"[warn] VERSION file exists but cannot be read: {e}")
        return None
    except UnicodeDecodeError as e:
        print(f"[warn] VERSION file has encoding issues: {e}")
        return None
    except OSError as e:
        print(f"[warn] VERSION file exists but cannot be read: {e}")
        return None
    except Exception as e:
        print(f"[warn] VERSION file exists but cannot be read: {e}")
        return None


def normalize_version(version: str) -> str:
    """Normalize a version string by stripping leading 'v' or 'V' prefix.

    Args:
        version: The version string to normalize

    Returns:
        Normalized version string (no v prefix)
    """
    if version.startswith(("v", "V")):
        return version[1:]
    return version


def get_git_tag_version(project_root: Path) -> Optional[str]:
    """Read version from current git tag if on a tagged commit.

    Uses `git describe --tags --exact-match` to check if the current
    commit has an exact tag match. Returns the tag name if found,
    None otherwise. Tags are normalized (v prefix stripped).

    Args:
        project_root: Path to the project root (must be in a git repo)

    Returns:
        Tag name string if on a tagged commit, None otherwise
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Normalize tag (strip v prefix) for consistent comparison
            return normalize_version(tag)
        return None
    except FileNotFoundError:
        # git not installed
        return None
    except Exception:
        # Any other error (not a git repo, etc.)
        return None


def sync_version_file(project_root: Path, canonical_version: str) -> bool:
    """Sync VERSION file to match the canonical manifest version.

    Args:
        project_root: Path to the project root
        canonical_version: The version string from the canonical manifest

    Returns:
        True if the file was created/updated/unchanged, False on error
    """
    version_file = project_root / "VERSION"
    try:
        # Avoid unnecessary writes by checking current content
        expected_content = canonical_version + "\n"
        if version_file.exists():
            try:
                current_content = version_file.read_text(encoding="utf-8")
                if current_content == expected_content:
                    return True  # No change needed
            except Exception:
                pass  # Continue with write if read fails
        version_file.write_text(expected_content, encoding="utf-8")
        return True
    except Exception as exc:
        print(f"[error] Failed to write VERSION file at {version_file}: {exc}")
        return False


def check_version_consistency(
    project_root: Path, fix: bool = False, dry_run: bool = False
) -> bool:
    """Check that version is consistent across version sources.

    Checks all supported package manifests:
    - pyproject.toml (Python, highest priority)
    - Cargo.toml (Rust)
    - package.json (Node.js)
    - VERSION file (optional, should match if present)
    - Git tag (optional, validates release version matches tag)

    Warns if multiple manifests exist with different versions.
    Version strings are normalized (v prefix stripped) before comparison.
    Prints warnings on mismatch. Safe to run offline.

    Args:
        project_root: Path to the project root
        fix: If True, auto-fix VERSION file to match canonical manifest version
        dry_run: If True, show what would be changed without writing files

    Returns:
        True if consistent (or would be fixed), False if mismatch and not fixed
    """
    canonical_version, canonical_manifest, found_manifests, all_versions = detect_manifest_versions(project_root)
    version_file_version = get_version_file_version(project_root)
    git_tag_version = get_git_tag_version(project_root)

    # If no package manifests found, nothing to check
    if not found_manifests:
        print("[info] No package manifests found (pyproject.toml, Cargo.toml, package.json), skipping version check")
        return True

    # If manifests exist but none have valid versions
    if canonical_version is None:
        print("[info] Package manifest(s) found but no valid version field")
        for manifest in found_manifests:
            print(f"       - {manifest}: {all_versions.get(manifest, 'invalid')}")
        return True

    # Report found manifests and their versions
    for manifest in found_manifests:
        version = all_versions.get(manifest, "invalid")
        if version == "invalid":
            print(f"[info] {manifest}: version field missing or invalid")
        else:
            print(f"[ok] {manifest} version: {version}")

    # Check for version mismatches between manifests
    if len(found_manifests) > 1:
        mismatches = []
        normalized_canonical = normalize_version(canonical_version)
        for manifest, version in all_versions.items():
            if version != "invalid" and normalize_version(version) != normalized_canonical:
                mismatches.append((manifest, version))

        if mismatches:
            print(f"[warn] Version mismatch between package manifests:")
            print(f"       Canonical (first valid): {canonical_manifest} = {canonical_version}")
            for manifest, version in mismatches:
                print(f"       Mismatch: {manifest} = {version}")
            print("       Consider aligning versions across all manifests")
            # Don't fail the check for manifest mismatches, just warn

    # Check git tag consistency if on a tagged commit
    if git_tag_version is not None:
        normalized_canonical = normalize_version(canonical_version)
        if git_tag_version != normalized_canonical:
            print(f"[warn] Git tag ({git_tag_version}) does not match {canonical_manifest} ({canonical_version})")
            print("       This may indicate a version mismatch in the release")
            # Don't fail the check for git tag mismatch, just warn
        else:
            print(f"[ok] Git tag matches: {git_tag_version}")

    # Check VERSION file consistency if it exists
    if version_file_version is not None:
        # Normalize versions for comparison (strip v prefix)
        normalized_canonical = normalize_version(canonical_version)
        normalized_file = normalize_version(version_file_version)

        if normalized_file != normalized_canonical:
            if dry_run:
                print(
                    f"[dry-run] Would update VERSION file from {version_file_version} to {canonical_version}"
                )
                return False
            elif fix:
                if sync_version_file(project_root, canonical_version):
                    print(
                        f"[fixed] VERSION file updated from {version_file_version} to {canonical_version}"
                    )
                    return True
                return False
            else:
                print(
                    f"[warn] VERSION file ({version_file_version}) does not match {canonical_manifest} ({canonical_version})"
                )
                print(
                    "       To fix: run 'tf doctor --fix' or update VERSION file manually"
                )
                return False
        else:
            print(f"[ok] VERSION file matches: {version_file_version}")
            return True
    else:
        # VERSION file doesn't exist
        if dry_run:
            print(
                f"[dry-run] Would create VERSION file with version {canonical_version}"
            )
            return False
        elif fix:
            if sync_version_file(project_root, canonical_version):
                print(f"[fixed] VERSION file created with version {canonical_version}")
                return True
            return False
        else:
            print("[info] No VERSION file found (optional)")
            return True


def run_doctor(args: argparse.Namespace) -> int:
    target_base, _, project_root = resolve_target_base(args)

    failed: List[bool] = []

    print("Ticketflow doctor")

    check_cmd("tk", failed)
    check_cmd("pi", failed)

    list_out = get_pi_list_cache() if shutil.which("pi") else ""

    for name in REQUIRED_EXTENSIONS:
        check_extension(name, target_base, list_out, False, failed)

    for name in OPTIONAL_EXTENSIONS:
        check_extension(name, target_base, list_out, True, failed)

    config = load_workflow_config(project_root)
    checker_cmds = get_checker_tools(config)
    if checker_cmds:
        print("Checker tools:")
        for cmd in checker_cmds:
            check_cmd(cmd, failed)
    else:
        print("[info] No checkers configured")

    check_mcp_config(config, target_base)

    print("Version consistency:")
    version_ok = check_version_consistency(
        project_root, fix=args.fix, dry_run=args.dry_run
    )
    if not version_ok:
        failed.append(True)

    if failed:
        print("Ticketflow doctor: failed")
        return 1

    print("Ticketflow doctor: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new doctor")
    parser.add_argument("--project", help="Operate on project at <path>")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix VERSION file to match canonical manifest (pyproject.toml, Cargo.toml, or package.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what --fix would change without writing files",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_doctor(args)


if __name__ == "__main__":
    raise SystemExit(main())
