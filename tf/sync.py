from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .frontmatter import sync_models_to_files
from .utils import find_project_root, read_json


def resolve_project_root(args: argparse.Namespace) -> Path:
    if getattr(args, "global_install", False):
        print("tf sync is project-local; do not use --global.", file=sys.stderr)
        raise SystemExit(1)

    if args.project:
        return Path(args.project).expanduser()

    root = find_project_root()
    if root is None:
        return Path.cwd()
    return root


def load_project_config(project_root: Path) -> dict:
    return read_json(project_root / ".tf" / "config" / "settings.json")


def sync_models(project_root: Path, config: dict) -> dict:
    """Sync models from config to all agents and prompts in the project.

    Canonical locations are project-root `agents/` and `prompts/`.
    Legacy `.pi/{agents,prompts}` are still supported as fallback.
    """
    agents_dir = project_root / "agents"
    prompts_dir = project_root / "prompts"

    if not agents_dir.exists():
        legacy_agents = project_root / ".pi" / "agents"
        agents_dir = legacy_agents if legacy_agents.exists() else agents_dir

    if not prompts_dir.exists():
        legacy_prompts = project_root / ".pi" / "prompts"
        prompts_dir = legacy_prompts if legacy_prompts.exists() else prompts_dir

    return sync_models_to_files(
        config,
        agents_dir if agents_dir.exists() else None,
        prompts_dir if prompts_dir.exists() else None,
    )


def run_sync(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args)

    # Ensure the workflow bundle exists in the project.
    from . import project_bundle

    project_bundle.install_bundle(project_root)

    config = load_project_config(project_root)
    if not config:
        print(
            f"ERROR: Missing or invalid project config: {project_root / '.tf/config/settings.json'}\n"
            "Run: tf init",
            file=sys.stderr,
        )
        return 1

    print("Syncing models from project meta-model configuration...")
    results = sync_models(project_root, config)

    if results["agents"]:
        print(f"Updated agents: {', '.join(results['agents'])}")
    if results["prompts"]:
        print(f"Updated prompts: {', '.join(results['prompts'])}")

    if results["errors"]:
        print("Errors:", file=sys.stderr)
        for err in results["errors"]:
            print(f"  {err}", file=sys.stderr)
        return 1

    if not results["agents"] and not results["prompts"]:
        print("No changes.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf sync")
    parser.add_argument("--project", help="Operate on project at <path> (default: auto-detect or cwd)")
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Not supported (sync is project-local)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_sync(args)


if __name__ == "__main__":
    raise SystemExit(main())
