import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

DEFAULT_UVX_SOURCE = "git+https://github.com/legout/pi-ticketflow"
DEFAULT_RAW_REPO_URL = "https://raw.githubusercontent.com/legout/pi-ticketflow/main"


def read_root_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def resolve_repo_root(repo_arg: Optional[str] = None) -> Optional[Path]:
    if repo_arg:
        path = Path(repo_arg).expanduser()
        if path.exists():
            return path

    env_root = os.environ.get("TF_REPO_ROOT", "").strip()
    if env_root:
        path = Path(env_root).expanduser()
        if path.exists():
            return path

    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        cli_root_file = parent / ".tf/cli-root"
        root_text = read_root_file(cli_root_file)
        if root_text:
            path = Path(root_text).expanduser()
            if path.exists():
                return path

    home_root_file = Path.home() / ".tf/cli-root"
    root_text = read_root_file(home_root_file)
    if root_text:
        path = Path(root_text).expanduser()
        if path.exists():
            return path

    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").is_file() and (parent / "tf_cli").is_dir():
            return parent

    return None


def find_legacy_script() -> Optional[Path]:
    env_path = os.environ.get("TF_LEGACY_SCRIPT", "").strip()
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_file():
            return path

    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".tf/scripts/tf_legacy.sh"
        if candidate.is_file():
            return candidate

    global_legacy = Path.home() / ".tf/scripts/tf_legacy.sh"
    if global_legacy.is_file():
        return global_legacy

    repo_root = resolve_repo_root()
    if repo_root:
        candidate = repo_root / "scripts/tf_legacy.sh"
        if candidate.is_file():
            return candidate

    return None


def raw_base_from_source(source: str) -> Optional[str]:
    cleaned = source.strip()
    if cleaned.startswith("git+"):
        cleaned = cleaned[4:]
    if not cleaned.startswith("https://github.com/"):
        return None

    cleaned = cleaned.split("#", 1)[0].split("?", 1)[0]
    cleaned = cleaned[len("https://github.com/"):]
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


def ensure_tf_assets(base: Path, repo_root: Optional[Path], uvx_source: str) -> None:
    config_dest = base / "config/settings.json"
    helper_dest = base / "scripts/tf_config.py"
    legacy_dest = base / "scripts/tf_legacy.sh"

    raw_base = raw_base_from_source(uvx_source) or DEFAULT_RAW_REPO_URL

    def ensure_file(dest: Path, rel_path: str, executable: bool = False) -> None:
        if dest.exists():
            return

        source_path = None
        if repo_root:
            candidate = repo_root / rel_path
            if candidate.is_file():
                source_path = candidate

        dest.parent.mkdir(parents=True, exist_ok=True)

        if source_path:
            shutil.copy2(source_path, dest)
        else:
            url = f"{raw_base}/{rel_path}"
            try:
                with urllib.request.urlopen(url) as resp:
                    dest.write_bytes(resp.read())
            except Exception as exc:
                print(f"WARNING: Failed to install {rel_path}: {exc}", file=sys.stderr)
                return

        if executable:
            dest.chmod(dest.stat().st_mode | 0o111)

    ensure_file(config_dest, "config/settings.json")
    ensure_file(helper_dest, "scripts/tf_config.py", executable=True)
    ensure_file(legacy_dest, "scripts/tf_legacy.sh", executable=True)


def run_legacy(args: list[str]) -> int:
    legacy = find_legacy_script()
    if not legacy:
        print("ERROR: Legacy shell CLI not found.", file=sys.stderr)
        print("Run 'tf install' from the repo, or reinstall using install.sh.", file=sys.stderr)
        return 1
    return subprocess.call(["bash", str(legacy), *args])


def render_uvx_shim(uvx_source: str, local_install: bool = False) -> str:
    if local_install:
        return f"""#!/usr/bin/env python3
import os
import shutil
import sys


def main() -> None:
    # Try local Python module first (works offline)
    python = shutil.which("python3") or shutil.which("python")
    if python:
        try:
            os.execvpe(python, [python, "-m", "tf_cli.cli", *sys.argv[1:]], os.environ.copy())
        except FileNotFoundError:
            pass

    # Fallback to uvx (requires internet)
    uvx = shutil.which("uvx")
    if uvx:
        os.execvpe("uvx", ["uvx", "--from", "{uvx_source}", "tf", *sys.argv[1:]], os.environ.copy())

    print("ERROR: Neither Python module nor uvx available", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
"""
    return f"""#!/usr/bin/env python3
import os
import shutil
import sys


def main() -> None:
    uvx = shutil.which("uvx")
    if not uvx:
        print("ERROR: uvx not found in PATH.", file=sys.stderr)
        raise SystemExit(1)
    os.execvpe("uvx", ["uvx", "--from", "{uvx_source}", "tf", *sys.argv[1:]], os.environ.copy())


if __name__ == "__main__":
    main()
"""


def install_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="tf install",
        description="Install the Ticketflow CLI shim.",
    )
    parser.add_argument("--repo", help="Path to the repo root (defaults to current directory)")
    parser.add_argument("--source", help="uvx --from source (git URL or path)")
    parser.add_argument("--project", help="Install into <path>/.tf/bin/tf")
    parser.add_argument("--path", help="Install shim to an explicit path")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Install to ~/.local/bin (default)")
    parser.add_argument("--force-local", action="store_true", help="Also install locally via pip for offline use")

    args = parser.parse_args(argv)

    if args.path and args.project:
        parser.error("--path and --project are mutually exclusive")
    if args.path and args.global_install:
        parser.error("--path and --global cannot be combined")
    if args.project and args.global_install:
        parser.error("--project and --global cannot be combined")

    uvx_source = args.source or os.environ.get("TF_UVX_FROM") or DEFAULT_UVX_SOURCE

    repo_root = resolve_repo_root(args.repo)

    if args.path:
        dest = Path(args.path).expanduser()
        cli_root_file = Path.home() / ".tf/cli-root"
        cli_source_file = Path.home() / ".tf/cli-source"
        tf_base = Path.home() / ".tf"
    elif args.project:
        project_root = Path(args.project).expanduser()
        dest = project_root / ".tf/bin/tf"
        cli_root_file = project_root / ".tf/cli-root"
        cli_source_file = project_root / ".tf/cli-source"
        tf_base = project_root / ".tf"
    else:
        dest = Path.home() / ".local/bin/tf"
        cli_root_file = Path.home() / ".tf/cli-root"
        cli_source_file = Path.home() / ".tf/cli-source"
        tf_base = Path.home() / ".tf"

    dest.parent.mkdir(parents=True, exist_ok=True)

    shim_source = None
    if repo_root:
        candidate = repo_root / "bin/tf"
        if candidate.is_file():
            shim_source = candidate

    local_install = args.force_local or bool(repo_root)
    
    if shim_source:
        shutil.copy2(shim_source, dest)
        dest.chmod(dest.stat().st_mode | 0o111)

        cli_root_file.parent.mkdir(parents=True, exist_ok=True)
        cli_root_file.write_text(str(repo_root) + "\n", encoding="utf-8")

        print(f"Installed shim to: {dest}")
        print(f"Recorded repo root: {cli_root_file}")
    else:
        dest.write_text(render_uvx_shim(str(uvx_source), local_install=local_install), encoding="utf-8")
        dest.chmod(dest.stat().st_mode | 0o111)

        print(f"Installed shim to: {dest}")

    cli_source_file.parent.mkdir(parents=True, exist_ok=True)
    cli_source_file.write_text(str(uvx_source) + "\n", encoding="utf-8")
    print(f"Recorded uvx source: {cli_source_file}")

    # Install locally via pip for offline use if requested
    if local_install and not shim_source:
        try:
            import subprocess
            if repo_root:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", str(repo_root)],
                    capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", str(uvx_source)],
                    capture_output=True, text=True
                )
            if result.returncode == 0:
                print("Installed locally via pip for offline use")
            else:
                print(f"WARNING: Local pip install failed: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"WARNING: Could not install locally: {e}", file=sys.stderr)

    ensure_tf_assets(tf_base, repo_root, uvx_source)

    if dest.parent == Path.home() / ".local/bin":
        path_env = os.environ.get("PATH", "")
        if str(dest.parent) not in path_env.split(os.pathsep):
            print("")
            print("WARNING: ~/.local/bin is not in your PATH")
            print("Add this to your shell profile:")
            print("  export PATH=\"$HOME/.local/bin:$PATH\"")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "install":
        return install_main(argv[1:])

    return run_legacy(argv)


if __name__ == "__main__":
    raise SystemExit(main())
