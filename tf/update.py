"""Update command using the canonical asset planner.

This module provides the 'tf update' command for updating assets in a project.
It uses the asset_planner module for all asset routing and installation decisions.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import asset_planner
from .asset_planner import DEFAULT_RAW_REPO_URL


def resolve_target_base(args: argparse.Namespace) -> Path:
    """Resolve the target base directory from args."""
    if args.project:
        return Path(args.project).expanduser() / ".pi"
    if args.global_install:
        return Path.home() / ".pi/agent"
    if (Path.cwd() / ".pi").is_dir():
        return Path.cwd() / ".pi"
    return Path.home() / ".pi/agent"


def prompt_yes_no(message: str, default_yes: bool) -> bool:
    """Prompt user for yes/no input."""
    suffix = "(Y/n)" if default_yes else "(y/N)"
    reply = input(f"{message} {suffix} ")
    if not reply.strip():
        return default_yes
    return reply.strip().lower().startswith("y")


def run_update(args: argparse.Namespace) -> int:
    """Run the update command.

    Uses asset_planner for all asset decisions.
    """
    # Determine project root (parent of .pi directory)
    target_base = resolve_target_base(args)
    project_root = target_base.parent

    if not project_root.exists():
        print(f"ERROR: Project directory does not exist: {project_root}", file=sys.stderr)
        return 1

    # Find local repo root for offline installs
    repo_root = asset_planner.find_repo_root()
    raw_base = asset_planner.resolve_raw_base()

    print("Checking for updates...")

    try:
        # Use the planner to check for available updates
        updates_available, errors = asset_planner.check_for_updates(
            project_root,
            repo_root=repo_root,
            raw_base=raw_base,
        )
    except Exception as exc:
        print(f"ERROR: Failed to check for updates: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Errors:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    if not updates_available:
        print("No updates available.")
        return 0

    # Group updates by type for display
    by_category = {}
    for plan in updates_available:
        category = plan.entry.rel_path.split("/")[0] if "/" in plan.entry.rel_path else "other"
        by_category.setdefault(category, []).append(plan)

    print(f"\nUpdates available ({len(updates_available)} files):")
    for category in sorted(by_category.keys()):
        print(f"\n  {category}:")
        for plan in sorted(by_category[category], key=lambda p: p.entry.rel_path):
            print(f"    - {plan.entry.rel_path}")

    # Prompt for confirmation
    if not prompt_yes_no(f"\nUpdate {len(updates_available)} files?", default_yes=True):
        print("Update cancelled.")
        return 0

    # Execute the updates
    print("\nUpdating...")
    result = asset_planner.update_assets(
        project_root,
        repo_root=repo_root,
        raw_base=raw_base,
    )

    # Report results
    if result.updated > 0:
        print(f"\nUpdated {result.updated} files.")
    if result.skipped > 0:
        print(f"Skipped {result.skipped} files (no changes).")
    if result.errors > 0:
        print(f"\nErrors ({result.errors}):", file=sys.stderr)
        for detail in result.error_details:
            print(f"  {detail}", file=sys.stderr)
        return 1

    print("\nUpdate complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for update command."""
    parser = argparse.ArgumentParser(description="Update TF workflow assets")
    parser.add_argument("--project", help="Operate on project at <path>")
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Use ~/.pi/agent (default if no project)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for update command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_update(args)


if __name__ == "__main__":
    raise SystemExit(main())
