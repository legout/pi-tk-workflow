"""Init command using the canonical asset planner.

This module provides the 'tf init' command for initializing a TF project.
It uses the asset_planner module for all asset routing and installation decisions.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import asset_planner


def init_project(project_root: Path) -> int:
    """Initialize a project-local TF installation.

    After the refactor, TF workflow assets are *always* project-local:
      - <project>/.pi/{agents,prompts,skills}/...
      - <project>/.tf/config/settings.json
      - <project>/.tf/knowledge, <project>/.tf/ralph

    Global state is limited to the CLI + Pi extension/MCP setup (tf setup).
    """
    tf_base = project_root / ".tf"
    tf_base.mkdir(parents=True, exist_ok=True)

    # State/scaffolding dirs
    (tf_base / "knowledge").mkdir(parents=True, exist_ok=True)
    (tf_base / "ralph").mkdir(parents=True, exist_ok=True)

    # Install/ensure the workflow bundle into the project using the canonical planner
    print("Installing workflow bundle...")
    try:
        installed, skipped = asset_planner.install_bundle(project_root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Initialized TF project at: {project_root}")
    print(f"  - Installed workflow files: {installed}")
    if skipped:
        print(f"  - Skipped existing files: {skipped}")
    print(f"  - TF state dir: {tf_base}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for init command."""
    parser = argparse.ArgumentParser(description="Initialize a TF project")
    parser.add_argument("--project", help="Project path (default: current directory)")
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Not supported (tf init is always project-local)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for init command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.global_install:
        print("tf init is project-local; do not use --global.", file=sys.stderr)
        return 1

    project_root = Path(args.project).expanduser() if args.project else Path.cwd()
    return init_project(project_root)


if __name__ == "__main__":
    raise SystemExit(main())
