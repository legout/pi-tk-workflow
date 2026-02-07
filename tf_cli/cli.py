from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from tf_cli.version import get_version

DEFAULT_UVX_SOURCE = "git+https://github.com/legout/pi-ticketflow"


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


def render_uvx_shim(uvx_source: str, local_install: bool = False) -> str:
    if local_install:
        return """#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


def read_root_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def find_repo_root():
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

    return None


def can_import_tf_cli(python, env=None) -> bool:
    try:
        result = subprocess.run(
            [python, "-c", "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('tf_cli.cli') else 1)"],
            env=env,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main() -> None:
    args = sys.argv[1:]
    python = shutil.which("python3") or shutil.which("python")
    repo_root = find_repo_root()

    if python and repo_root:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(repo_root) + (os.pathsep + existing if existing else "")
        if can_import_tf_cli(python, env):
            os.execvpe(python, [python, "-m", "tf_cli.cli", *args], env)

    if python and can_import_tf_cli(python):
        os.execvpe(python, [python, "-m", "tf_cli.cli", *args], os.environ.copy())

    uvx = shutil.which("uvx")
    if uvx:
        os.execvpe("uvx", ["uvx", "--from", "{uvx_source}", "tf", *args], os.environ.copy())

    print("ERROR: Neither Python module nor uvx available", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
""".format(uvx_source=uvx_source)
    return """#!/usr/bin/env python3
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
""".format(uvx_source=uvx_source)


def install_local_package(repo_root: Optional[Path], uvx_source: str) -> bool:
    python = sys.executable

    def run_pip_install():
        if repo_root:
            cmd = [python, "-m", "pip", "install", "-e", str(repo_root)]
        else:
            cmd = [python, "-m", "pip", "install", str(uvx_source)]
        return subprocess.run(cmd, capture_output=True, text=True)

    result = run_pip_install()
    if result.returncode == 0:
        print("Installed locally via pip for offline use")
        return True

    output = (result.stderr or "").strip() or (result.stdout or "").strip()
    if "No module named pip" in output:
        ensure = subprocess.run(
            [python, "-m", "ensurepip", "--upgrade"],
            capture_output=True,
            text=True,
        )
        if ensure.returncode == 0:
            result = run_pip_install()
            if result.returncode == 0:
                print("Installed locally via pip for offline use")
                return True
            output = (result.stderr or "").strip() or (result.stdout or "").strip()
        else:
            ensure_output = (ensure.stderr or "").strip() or (
                ensure.stdout or ""
            ).strip()
            if ensure_output:
                output = f"{output}\n{ensure_output}" if output else ensure_output

    if output:
        print(f"WARNING: Local pip install failed: {output}", file=sys.stderr)
    else:
        print("WARNING: Local pip install failed.", file=sys.stderr)
    return False


def install_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="tf install",
        description="Install the Ticketflow CLI shim.",
    )
    parser.add_argument(
        "--repo", help="Path to the repo root (defaults to current directory)"
    )
    parser.add_argument("--source", help="uvx --from source (git URL or path)")
    parser.add_argument(
        "--project",
        help="DEPRECATED (tf is installed globally). Use 'tf init' in projects instead.",
    )
    parser.add_argument("--path", help="Install shim to an explicit path")
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Install to ~/.local/bin (default)",
    )
    parser.add_argument(
        "--force-local",
        action="store_true",
        help="Also install locally via pip for offline use",
    )

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
    else:
        # TF is always installed globally.
        if args.project:
            print(
                "WARNING: --project is deprecated. Installing tf globally; "
                "use 'tf init' inside the project instead.",
                file=sys.stderr,
            )
        dest = Path.home() / ".local/bin/tf"

    cli_root_file = Path.home() / ".tf/cli-root"
    cli_source_file = Path.home() / ".tf/cli-source"

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
        dest.write_text(
            render_uvx_shim(str(uvx_source), local_install=local_install),
            encoding="utf-8",
        )
        dest.chmod(dest.stat().st_mode | 0o111)

        print(f"Installed shim to: {dest}")

    cli_source_file.parent.mkdir(parents=True, exist_ok=True)
    cli_source_file.write_text(str(uvx_source) + "\n", encoding="utf-8")
    print(f"Recorded uvx source: {cli_source_file}")

    # Install locally via pip for offline use if requested
    if local_install and not shim_source:
        try:
            install_local_package(repo_root, uvx_source)
        except Exception as e:
            print(f"WARNING: Could not install locally: {e}", file=sys.stderr)

    if dest.parent == Path.home() / ".local/bin":
        path_env = os.environ.get("PATH", "")
        if str(dest.parent) not in path_env.split(os.pathsep):
            print("")
            print("WARNING: ~/.local/bin is not in your PATH")
            print("Add this to your shell profile:")
            print('  export PATH="$HOME/.local/bin:$PATH"')

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(
            """Ticketflow CLI\n\nUsage:\n  tf --version | -v | -V\n  tf install [--global] [--force-local]\n  tf setup\n  tf login\n  tf init [--project <path>]\n  tf sync [--project <path>]\n  tf doctor [--project <path>] [--fix]\n  tf update\n  tf next\n  tf backlog-ls [topic-id-or-path]\n  tf track <path>\n  tf priority-reclassify [--apply] [--ids ...] [--ready] [--status ...] [--tag ...]\n  tf ralph <subcommand> ...\n  tf agentsmd <subcommand> ...\n  tf seed ...\n  tf kb ...\n\n(You can also use: tf new <command> ... for the old subcommand namespace.)\n"""
        )
        return 0

    # Handle --version/-v/-V before other commands
    if argv and argv[0] in ("--version", "-v", "-V"):
        print(get_version())
        return 0

    command = argv[0]
    rest = argv[1:]

    if command == "install":
        return install_main(rest)

    # Back-compat namespace
    if command == "new":
        from . import new_cli

        return new_cli.main(rest)

    if command == "setup":
        from . import setup

        return setup.main(rest)

    if command == "login":
        from . import login

        return login.main(rest)

    if command == "init":
        from . import init

        return init.main(rest)

    if command == "sync":
        from . import sync

        return sync.main(rest)

    if command == "update":
        from . import update

        return update.main(rest)

    if command == "doctor":
        from . import doctor

        return doctor.main(rest)

    if command == "next":
        from . import next

        return next.main(rest)

    if command == "backlog-ls":
        from . import backlog_ls

        return backlog_ls.main(rest)

    if command == "track":
        from . import track

        return track.main(rest)

    if command == "priority-reclassify":
        from . import priority_reclassify

        return priority_reclassify.main(rest)

    if command == "ralph":
        from . import ralph

        return ralph.main(rest)

    if command == "agentsmd":
        from . import agentsmd

        return agentsmd.main(rest)

    if command == "tags-suggest":
        from . import tags_suggest

        return tags_suggest.suggest_main(rest)

    if command == "tags-classify":
        from . import tags_suggest

        return tags_suggest.classify_main(rest)

    if command == "tags-keywords":
        from . import tags_suggest

        return tags_suggest.keywords_main(rest)

    if command == "seed":
        from . import seed_cli

        return seed_cli.main(rest)

    if command == "kb":
        from . import kb_cli

        return kb_cli.main(rest)

    print(f"Unknown command: {command}", file=sys.stderr)
    print("Run: tf --help", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
