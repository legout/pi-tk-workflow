"""CLI entry point for demo package."""

from __future__ import annotations

import sys

from demo.hello import hello


def main() -> int:
    """Run the hello CLI.

    Returns:
        int: Exit code (0 for success).
    """
    name = " ".join(sys.argv[1:]).strip() or "World"
    print(hello(name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
