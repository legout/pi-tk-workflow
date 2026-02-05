import argparse
import json
import os
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
            print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
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


def check_extension(name: str, target_base: Path, list_out: str, optional: bool, failed: List[bool]) -> None:
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
        print(f"[info] mcp.json not found at {mcp_file} (MCP research optional; run 'tf new login')")
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
    """
    version_file = project_root / "VERSION"
    if not version_file.exists():
        return None
    try:
        content = version_file.read_text(encoding="utf-8").strip()
        return content if content else None
    except Exception:
        return None


def check_version_consistency(project_root: Path) -> None:
    """Check that version is consistent across version sources.
    
    Currently checks:
    - package.json (canonical source)
    - VERSION file (optional, should match if present)
    
    Prints warnings on mismatch. Safe to run offline.
    """
    package_file = project_root / "package.json"
    package_version = get_package_version(project_root)
    version_file_version = get_version_file_version(project_root)
    
    # If no package.json, nothing to check
    if not package_file.exists():
        print("[info] No package.json found, skipping version check")
        return
    
    # If package.json exists but version is invalid/missing
    if package_version is None:
        print("[info] package.json found but version field is missing or invalid")
        return
    
    print(f"[ok] package.json version: {package_version}")
    
    # Check VERSION file consistency if it exists
    if version_file_version is not None:
        if version_file_version != package_version:
            print(f"[warn] VERSION file ({version_file_version}) does not match package.json ({package_version})")
            print("       To fix: update VERSION file to match package.json, or remove VERSION file")
        else:
            print(f"[ok] VERSION file matches package.json: {version_file_version}")


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
    check_version_consistency(project_root)

    if failed:
        print("Ticketflow doctor: failed")
        return 1

    print("Ticketflow doctor: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new doctor")
    parser.add_argument("--project", help="Operate on project at <path>")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_doctor(args)


if __name__ == "__main__":
    raise SystemExit(main())
