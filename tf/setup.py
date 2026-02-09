from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from typing import Optional

REQUIRED_EXTENSIONS = [
    "pi-subagents",
    "pi-model-switch",
    "pi-prompt-template-model",
]

OPTIONAL_EXTENSIONS = [
    "pi-review-loop",
    "pi-mcp-adapter",
    "pi-web-access",
]


def prompt_yes_no(message: str, default_yes: bool) -> bool:
    suffix = "(Y/n)" if default_yes else "(y/N)"
    reply = input(f"{message} {suffix} ").strip().lower()
    if not reply:
        return default_yes
    return reply.startswith("y")


def install_extensions(*, install_optional: bool) -> None:
    if shutil.which("pi") is None:
        print("pi not found in PATH; skipping extension installs.", file=sys.stderr)
        return

    for name in REQUIRED_EXTENSIONS:
        subprocess.run(["pi", "install", f"npm:{name}"])

    if install_optional:
        for name in OPTIONAL_EXTENSIONS:
            subprocess.run(["pi", "install", f"npm:{name}"])


def run_setup(_: argparse.Namespace) -> int:
    print("Ticketflow setup (global)\n")
    print("This configures your global Pi environment for TF:")
    print("  - installs required Pi extensions")
    print("  - optionally configures MCP + web-search API keys")
    print("\nTF workflow files (agents/prompts/skills/config) are installed per-project via: tf init / tf sync\n")

    install_required = prompt_yes_no(
        "Install required Pi extensions (subagents, model-switch, prompt-template-model)?",
        True,
    )
    install_optional = prompt_yes_no(
        "Install optional Pi extensions (review-loop, mcp-adapter, web-access)?",
        False,
    )

    if install_required:
        install_extensions(install_optional=install_optional)

    if prompt_yes_no("Configure API keys for MCP servers and web search?", False):
        from tf.login import main as login_main

        login_main([])

    print("\nNext steps:")
    print("  1. In each project, install TF workflow files + config:")
    print("     tf init")
    print("  2. After editing .tf/config/settings.json, sync models:")
    print("     tf sync")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf setup")
    parser.add_argument(
        "--project",
        help="Not supported (setup is global). Present for backward compatibility.",
    )
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Optional (setup is global by default)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_setup(args)


if __name__ == "__main__":
    raise SystemExit(main())
