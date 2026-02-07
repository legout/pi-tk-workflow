from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

import shutil

from .utils import find_project_root

DEFAULT_QUERY = "tk ready | head -1 | awk '{print $1}'"


def load_ticket_query(ralph_config: Path) -> Optional[str]:
    if not ralph_config.exists():
        return None
    try:
        import json

        data = json.loads(ralph_config.read_text(encoding="utf-8"))
    except Exception:
        return None
    query = str(data.get("ticketQuery", "")).strip()
    return query or None


def resolve_query(project_root: Optional[Path]) -> str:
    if project_root:
        ralph_config = project_root / ".tf/ralph/config.json"
        config_query = load_ticket_query(ralph_config)
        if config_query:
            return config_query
    return DEFAULT_QUERY


def run_query(query: str) -> Optional[str]:
    result = subprocess.run(query, shell=True, capture_output=True, text=True)
    output = (result.stdout or "").strip()
    if not output:
        return None
    return output.split()[0]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="tf new next")
    parser.add_argument("--project", help="Operate on project at <path>")
    args = parser.parse_args(argv)

    if shutil.which("tk") is None:
        print("tk not found in PATH; cannot query tickets.", file=sys.stderr)
        return 1

    project_root = Path(args.project).expanduser() if args.project else find_project_root()
    query = resolve_query(project_root)

    ticket = run_query(query)
    if not ticket:
        print("No ready tickets found.", file=sys.stderr)
        return 1

    print(ticket)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
