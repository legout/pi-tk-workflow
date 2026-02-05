import sys
from typing import Optional, List

from . import ralph_new


def usage() -> None:
    print(
        """Ticketflow (new Python CLI)

Usage:
  tf new ralph <subcommand> [options]

Commands:
  ralph   Python implementation of Ralph loop (start/run)
"""
    )


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"-h", "--help", "help"}:
        usage()
        return 0

    command = argv[0]
    rest = argv[1:]

    if command == "ralph":
        return ralph_new.main(rest)

    print(f"Unknown 'new' subcommand: {command}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
