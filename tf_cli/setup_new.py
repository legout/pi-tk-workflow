from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import List, Optional

DEFAULT_UVX_SOURCE = "git+https://github.com/legout/pi-ticketflow"
DEFAULT_RAW_REPO_URL = "https://raw.githubusercontent.com/legout/pi-ticketflow/main"

FALLBACK_MANIFEST = """# CLI tool
bin/tf

# Needed so `tf setup` can be run from an already-installed workflow
config/install-manifest.txt

# Helper scripts for CLI
scripts/tf_config.py
scripts/tf_legacy.sh

agents/reviewer-general.md
agents/reviewer-spec-audit.md
agents/reviewer-second-opinion.md
agents/review-merge.md
agents/researcher.md
agents/researcher-fetch.md
agents/fixer.md
agents/closer.md

skills/tf-workflow/SKILL.md
skills/tf-planning/SKILL.md
skills/tf-config/SKILL.md
skills/ralph/SKILL.md

prompts/tf.md
prompts/tf-next.md
prompts/tf-plan.md
prompts/tf-plan-consult.md
prompts/tf-plan-revise.md
prompts/tf-plan-review.md
prompts/tf-seed.md
prompts/tf-backlog.md
prompts/tf-backlog-ls.md
prompts/tf-spike.md
prompts/tf-backlog-from-openspec.md
prompts/tf-baseline.md
prompts/tf-followups.md
prompts/tf-sync.md
prompts/ralph-start.md

config/settings.json
config/workflows/tf/README.md
"""


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


def download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as exc:
        print(f"WARNING: Failed to download {url}: {exc}", file=sys.stderr)
        return False


def parse_manifest(content: str) -> List[str]:
    entries: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped)
    return entries


def load_manifest(repo_root: Optional[Path]) -> List[str]:
    manifest_path = repo_root / "config/install-manifest.txt" if repo_root else None
    if manifest_path and manifest_path.exists():
        return parse_manifest(manifest_path.read_text(encoding="utf-8"))

    raw_base = resolve_raw_base()
    manifest_url = f"{raw_base}/config/install-manifest.txt"
    try:
        with urllib.request.urlopen(manifest_url) as resp:
            content = resp.read().decode("utf-8")
        return parse_manifest(content)
    except Exception:
        print("[warn] Install manifest not found; using built-in manifest.", file=sys.stderr)
        return parse_manifest(FALLBACK_MANIFEST)


def route_dest_base(rel: str, target_base: Path, tf_base: Optional[Path], is_global: bool) -> Optional[Path]:
    if rel.startswith("agents/") or rel.startswith("skills/") or rel.startswith("prompts/"):
        return target_base
    if is_global:
        return None
    return tf_base


def install_files(
    manifest: List[str],
    repo_root: Optional[Path],
    target_base: Path,
    tf_base: Optional[Path],
    is_global: bool,
) -> None:
    raw_base = resolve_raw_base()
    pi_count = 0
    tf_count = 0

    for rel in manifest:
        dest_base = route_dest_base(rel, target_base, tf_base, is_global)
        if dest_base is None:
            continue

        dest = dest_base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        src = repo_root / rel if repo_root else None
        if src and src.exists():
            shutil.copy2(src, dest)
        else:
            url = f"{raw_base}/{rel}"
            if not download(url, dest):
                print(f"Missing install file: {rel}", file=sys.stderr)
                raise SystemExit(1)

        if dest_base == target_base:
            pi_count += 1
        else:
            tf_count += 1

    print(f"Installed Pi workflow files to: {target_base}")
    if is_global:
        print(f"Installed files: {pi_count} (pi assets)")
    else:
        print(f"Installed TF runtime/config files to: {tf_base}")
        print(f"Installed files: {pi_count + tf_count} (pi: {pi_count}, tf: {tf_count})")


def ensure_global_settings(repo_root: Optional[Path]) -> None:
    dest = Path.home() / ".tf/config/settings.json"
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = repo_root / "config/settings.json" if repo_root else None
    if src and src.exists():
        shutil.copy2(src, dest)
        return
    raw_base = resolve_raw_base()
    url = f"{raw_base}/config/settings.json"
    if not download(url, dest):
        print("WARNING: Failed to install settings.json", file=sys.stderr)


def install_extensions(scope_flag: List[str], install_optional: bool) -> None:
    if shutil.which("pi") is None:
        print("pi not found in PATH; skipping extension installs.", file=sys.stderr)
        return

    required = ["pi-subagents", "pi-model-switch", "pi-prompt-template-model"]
    optional = ["pi-review-loop", "pi-mcp-adapter", "pi-web-access"]

    for name in required:
        subprocess.run(["pi", "install", *scope_flag, f"npm:{name}"])
    if install_optional:
        for name in optional:
            subprocess.run(["pi", "install", *scope_flag, f"npm:{name}"])


def prompt_yes_no(message: str, default_yes: bool) -> bool:
    suffix = "(Y/n)" if default_yes else "(y/N)"
    reply = input(f"{message} {suffix} ").strip().lower()
    if not reply:
        return default_yes
    return reply.startswith("y")


def run_setup(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()

    is_global = False
    project_root: Optional[Path] = None

    if args.global_install:
        is_global = True
    elif args.project:
        project_root = Path(args.project).expanduser()
    else:
        if prompt_yes_no("Install Pi assets globally?", True):
            is_global = True
        else:
            project_input = input("Project path (default: current dir): ").strip()
            project_root = Path(project_input).expanduser() if project_input else Path.cwd()

    if not is_global and project_root is None:
        project_root = Path.cwd()

    target_base = Path.home() / ".pi/agent" if is_global else project_root / ".pi"
    tf_base = None if is_global else project_root / ".tf"

    manifest = load_manifest(repo_root)
    if not manifest:
        print("No install entries found; aborting.", file=sys.stderr)
        return 1

    install_files(manifest, repo_root, target_base, tf_base, is_global)

    if is_global:
        ensure_global_settings(repo_root)
        print("\nNext: run 'tf new init' in each project to scaffold .tf/.")
    else:
        from . import init_new

        init_new.init_project(project_root)

    install_deps = prompt_yes_no("Install required Pi extensions (subagents, model-switch, prompt-template-model)?", True)
    install_optional = prompt_yes_no("Install optional Pi extensions (review-loop, mcp-adapter, web-access)?", False)

    if install_deps:
        scope_flag = ["-l"] if not is_global else []
        install_extensions(scope_flag, install_optional)

    if prompt_yes_no("Configure API keys for MCP servers and web search?", False):
        from . import login_new

        login_args: List[str] = []
        if is_global:
            login_args.append("--global")
        else:
            login_args += ["--project", str(project_root)]
        login_new.main(login_args)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new setup")
    parser.add_argument("--project", help="Install into project at <path>")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Install globally")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_setup(args)


if __name__ == "__main__":
    raise SystemExit(main())
