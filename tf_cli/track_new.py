import argparse
import os
from pathlib import Path
from typing import Optional


def resolve_files_changed(path_arg: Optional[str]) -> Path:
    if path_arg:
        path = Path(path_arg)
    elif os.environ.get("TF_FILES_CHANGED"):
        path = Path(os.environ["TF_FILES_CHANGED"])
    elif os.environ.get("TF_CHAIN_DIR"):
        path = Path(os.environ["TF_CHAIN_DIR"]) / "files_changed.txt"
    else:
        path = Path.cwd() / "files_changed.txt"

    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="tf new track")
    parser.add_argument("path", help="File path to track")
    parser.add_argument("--file", dest="files_changed", help="Output files_changed.txt path")
    args = parser.parse_args(argv)

    tracked_path = Path(args.path)
    if not tracked_path.is_absolute():
        tracked_path = Path.cwd() / tracked_path

    files_changed = resolve_files_changed(args.files_changed)
    files_changed.parent.mkdir(parents=True, exist_ok=True)
    files_changed.touch(exist_ok=True)

    existing = set(p.strip() for p in files_changed.read_text(encoding="utf-8").splitlines() if p.strip())
    if str(tracked_path) not in existing:
        with files_changed.open("a", encoding="utf-8") as handle:
            handle.write(f"{tracked_path}\n")

    print(f"Tracked: {tracked_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
