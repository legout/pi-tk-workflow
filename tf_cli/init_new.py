from __future__ import annotations

import argparse
import os
import shutil
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


def find_repo_root() -> Optional[Path]:
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


def resolve_raw_base() -> str:
    uvx_source = os.environ.get("TF_UVX_FROM") or DEFAULT_UVX_SOURCE
    return raw_base_from_source(uvx_source) or DEFAULT_RAW_REPO_URL


def ensure_file(dest: Path, rel_path: str, repo_root: Optional[Path]) -> None:
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
        return

    raw_base = resolve_raw_base()
    url = f"{raw_base}/{rel_path}"
    try:
        with urllib.request.urlopen(url) as resp:
            dest.write_bytes(resp.read())
    except Exception as exc:
        print(f"WARNING: Failed to install {rel_path}: {exc}")


def init_project(project_root: Path) -> int:
    tf_base = project_root / ".tf"
    tf_base.mkdir(parents=True, exist_ok=True)

    (tf_base / "config").mkdir(parents=True, exist_ok=True)
    (tf_base / "scripts").mkdir(parents=True, exist_ok=True)
    (tf_base / "knowledge").mkdir(parents=True, exist_ok=True)
    (tf_base / "ralph").mkdir(parents=True, exist_ok=True)

    repo_root = find_repo_root()
    ensure_file(tf_base / "config/settings.json", "config/settings.json", repo_root)
    ensure_file(tf_base / "scripts/tf_config.py", "scripts/tf_config.py", repo_root)

    config_path = tf_base / "scripts/tf_config.py"
    if config_path.exists():
        config_path.chmod(config_path.stat().st_mode | 0o111)

    print(f"Initialized .tf directory at: {tf_base}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new init")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Not supported for init")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.global_install:
        print("tf init is project-local; do not use --global.", file=sys.stderr)
        return 1

    project_root = Path(args.project).expanduser() if args.project else Path.cwd()
    return init_project(project_root)


if __name__ == "__main__":
    raise SystemExit(main())
