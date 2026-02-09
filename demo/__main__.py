"""CLI entry point for demo package."""

from __future__ import annotations

import sys

from demo.hello import hello


def main() -> None:
    """Run the hello CLI."""
    name = " ".join(sys.argv[1:]).strip() or "World"
    print(hello(name))


if __name__ == "__main__":
    main()
