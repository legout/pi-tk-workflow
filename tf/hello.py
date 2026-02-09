"""
Hello world demo command for TF workflow testing.

This module implements a simple 'tf hello' CLI command that prints
customizable greeting messages. It demonstrates the standard TF CLI
command structure and serves as a workflow testing example.

Ticket: pt-p37y
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    """Run the hello command."""
    parser = argparse.ArgumentParser(
        prog="tf hello",
        description="Print a hello message (demo command for workflow testing)",
    )
    parser.add_argument(
        "--name",
        "-n",
        default="World",
        help="Name to greet (default: World)",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=1,
        help="Number of times to print the greeting (default: 1)",
    )
    parser.add_argument(
        "--upper",
        "-u",
        action="store_true",
        help="Print greeting in UPPERCASE",
    )

    args: argparse.Namespace = parser.parse_args(argv)

    if args.count < 1:
        print(f"Error: --count must be at least 1 (got {args.count})", file=sys.stderr)
        return 1

    message = f"Hello, {args.name}!"
    if args.upper:
        message = message.upper()

    for _ in range(args.count):
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
