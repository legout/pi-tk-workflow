from __future__ import annotations

import argparse
import filecmp
import tempfile
import urllib.request
from pathlib import Path
from typing import List, Optional

DEFAULT_RAW_REPO_URL = "https://raw.githubusercontent.com/legout/pi-ticketflow/main"


def download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as exc:
        print(f"WARNING: Failed to download {url}: {exc}")
        return False


def parse_manifest(manifest_path: Path) -> List[str]:
    entries: List[str] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("agents/") or stripped.startswith("skills/") or stripped.startswith("prompts/"):
            entries.append(stripped)
    return entries


def resolve_target_base(args: argparse.Namespace) -> Path:
    if args.project:
        return Path(args.project).expanduser() / ".pi"
    if args.global_install:
        return Path.home() / ".pi/agent"
    if (Path.cwd() / ".pi").is_dir():
        return Path.cwd() / ".pi"
    return Path.home() / ".pi/agent"


def prompt_yes_no(message: str, default_yes: bool) -> bool:
    suffix = "(Y/n)" if default_yes else "(y/N)"
    reply = input(f"{message} {suffix} ")
    if not reply.strip():
        return default_yes
    return reply.strip().lower().startswith("y")


def update_assets(target_base: Path) -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        manifest_file = temp_root / "install-manifest.txt"
        manifest_url = f"{DEFAULT_RAW_REPO_URL}/config/install-manifest.txt"

        if not download(manifest_url, manifest_file):
            print(f"Failed to download manifest from {manifest_url}")
            return 1

        entries = parse_manifest(manifest_file)
        if not entries:
            print("No agent/skill/prompt entries found in manifest.")
            return 0

        new_files: List[str] = []
        existing_files: List[str] = []
        for entry in entries:
            dest = target_base / entry
            if dest.exists():
                existing_files.append(entry)
            else:
                new_files.append(entry)

        downloaded = 0
        updated = 0
        errors = 0

        if new_files:
            print("New files available:")
            for entry in new_files:
                print(f"  - {entry}")
            if prompt_yes_no(f"Download {len(new_files)} new files into {target_base}?", True):
                for entry in new_files:
                    url = f"{DEFAULT_RAW_REPO_URL}/{entry}"
                    if download(url, target_base / entry):
                        downloaded += 1
                    else:
                        errors += 1
        else:
            print("No new files to download.")

        if existing_files and prompt_yes_no("Check for updates to existing files?", False):
            update_files: List[str] = []
            for entry in existing_files:
                temp_file = temp_root / entry
                url = f"{DEFAULT_RAW_REPO_URL}/{entry}"
                if download(url, temp_file):
                    dest = target_base / entry
                    if not dest.exists() or not filecmp.cmp(temp_file, dest, shallow=False):
                        update_files.append(entry)
                else:
                    errors += 1

            if update_files:
                print("Updates available:")
                for entry in update_files:
                    print(f"  - {entry}")
                if prompt_yes_no(f"Overwrite {len(update_files)} existing files?", False):
                    for entry in update_files:
                        temp_file = temp_root / entry
                        dest = target_base / entry
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            dest.write_bytes(temp_file.read_bytes())
                            updated += 1
                        except Exception as exc:
                            print(f"WARNING: Failed to overwrite {entry}: {exc}")
                            errors += 1
            else:
                print("No updates found for existing files.")

        print("Update complete.")
        print(f"  New files downloaded: {downloaded}")
        print(f"  Existing files updated: {updated}")
        if errors:
            print(f"  Warnings: {errors}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new update")
    parser.add_argument("--project", help="Operate on project at <path>")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Use ~/.pi/agent (default)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target_base = resolve_target_base(args)
    if not target_base.exists():
        target_base.mkdir(parents=True, exist_ok=True)
    return update_assets(target_base)


if __name__ == "__main__":
    raise SystemExit(main())
