from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

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


def read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def merge(a: Dict, b: Dict) -> Dict:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def find_project_root() -> Optional[Path]:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return None


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
    global_config = Path.home() / ".tf/config/settings.json"
    project_config = project_root / ".tf/config/settings.json"
    return merge(read_json(global_config), read_json(project_config))


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
    mcp_file = target_base / "mcp.json"
    if not mcp_file.exists():
        print(
            f"[info] mcp.json not found at {mcp_file} (MCP research optional; run 'tf new login')"
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


def sync_version_file(project_root: Path, package_version: str) -> bool:
    """Sync VERSION file to match package.json version.

    Args:
        project_root: Path to the project root
        package_version: The version string from package.json

    Returns:
        True if the file was created/updated/unchanged, False on error
    """
    version_file = project_root / "VERSION"
    try:
        # Avoid unnecessary writes by checking current content
        expected_content = package_version + "\n"
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

    Currently checks:
    - package.json (canonical source)
    - VERSION file (optional, should match if present)

    Version strings are normalized (v prefix stripped) before comparison.
    Prints warnings on mismatch. Safe to run offline.

    Args:
        project_root: Path to the project root
        fix: If True, auto-fix VERSION file to match package.json
        dry_run: If True, show what would be changed without writing files

    Returns:
        True if consistent (or would be fixed), False if mismatch and not fixed
    """
    package_file = project_root / "package.json"
    package_version = get_package_version(project_root)
    version_file_version = get_version_file_version(project_root)

    # If no package.json, nothing to check
    if not package_file.exists():
        print("[info] No package.json found, skipping version check")
        return True

    # If package.json exists but version is invalid/missing
    if package_version is None:
        print("[info] package.json found but version field is missing or invalid")
        return True

    print(f"[ok] package.json version: {package_version}")

    # Check VERSION file consistency if it exists
    if version_file_version is not None:
        # Normalize versions for comparison (strip v prefix)
        normalized_package = normalize_version(package_version)
        normalized_file = normalize_version(version_file_version)

        if normalized_file != normalized_package:
            if dry_run:
                print(
                    f"[dry-run] Would update VERSION file from {version_file_version} to {package_version}"
                )
                return False
            elif fix:
                if sync_version_file(project_root, package_version):
                    print(
                        f"[fixed] VERSION file updated from {version_file_version} to {package_version}"
                    )
                    return True
                return False
            else:
                print(
                    f"[warn] VERSION file ({version_file_version}) does not match package.json ({package_version})"
                )
                print(
                    "       To fix: run 'tf doctor --fix' or update VERSION file manually"
                )
                return False
        else:
            print(f"[ok] VERSION file matches package.json: {version_file_version}")
            return True
    else:
        # VERSION file doesn't exist
        if dry_run:
            print(
                f"[dry-run] Would create VERSION file with version {package_version}"
            )
            return False
        elif fix:
            if sync_version_file(project_root, package_version):
                print(f"[fixed] VERSION file created with version {package_version}")
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
        "--fix", action="store_true", help="Auto-fix VERSION file to match package.json"
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
