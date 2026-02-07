"""Suggest component tags for tickets using the conservative keyword classifier.

This module provides CLI commands for component tag suggestion. It uses the
shared `tf_cli.component_classifier` module as the single source of truth for
classification logic, ensuring consistency with `/tf-backlog` automatic tagging.

Commands:
    tf new tags-suggest - Suggest tags for a ticket or text
    tf new tags-classify - Classify arbitrary text
    tf new tags-keywords - Show the keyword mapping documentation

The shared classifier ensures that both `/tf-backlog` (during ticket creation)
and `/tf-tags-suggest` (as a fallback/explicit tool) produce consistent
component:* tag suggestions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .component_classifier import (
    ClassificationResult,
    classify_components,
    format_tags_for_tk,
    get_keyword_map_documentation,
    suggest_tags_for_ticket,
)


def run_suggest(
    title: Optional[str],
    description: Optional[str],
    ticket_id: Optional[str],
    json_output: bool = False,
    show_rationale: bool = False,
) -> int:
    """Run the tag suggestion logic.

    Args:
        title: Ticket title (if not using ticket_id)
        description: Ticket description (if not using ticket_id)
        ticket_id: Ticket ID to fetch and classify
        json_output: Whether to output as JSON
        show_rationale: Whether to show rationale for each tag

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if ticket_id:
        try:
            result = suggest_tags_for_ticket(ticket_id)
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif title:
        result = classify_components(title, description or "")
    else:
        print("Error: Either --ticket or title must be provided", file=sys.stderr)
        return 1

    if json_output:
        output = {
            "tags": result.tags,
            "rationale": result.rationale,
            "matched_keywords": result.matched_keywords,
        }
        print(json.dumps(output, indent=2))
    else:
        if result.tags:
            print(format_tags_for_tk(result.tags))
            if show_rationale:
                print("\nRationale:")
                for tag in result.tags:
                    print(f"  {tag}: {result.rationale[tag]}")
        else:
            print("(no component tags suggested)")

    return 0


def run_classify_text(
    text: str,
    json_output: bool = False,
    show_rationale: bool = False,
) -> int:
    """Classify arbitrary text and show results.

    Args:
        text: Text to classify
        json_output: Whether to output as JSON
        show_rationale: Whether to show rationale

    Returns:
        Exit code
    """
    result = classify_components(text)

    if json_output:
        output = {
            "tags": result.tags,
            "rationale": result.rationale,
            "matched_keywords": result.matched_keywords,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Text: {text}")
        if result.tags:
            print(f"\nSuggested tags: {format_tags_for_tk(result.tags)}")
            if show_rationale:
                print("\nRationale:")
                for tag in result.tags:
                    print(f"  {tag}: {result.rationale[tag]}")
        else:
            print("\nNo component tags suggested.")

    return 0


def run_show_keywords() -> int:
    """Show the keyword mapping documentation.

    Returns:
        Exit code (always 0)
    """
    print(get_keyword_map_documentation())
    return 0


def build_suggest_parser() -> argparse.ArgumentParser:
    """Build the argument parser for tags-suggest."""
    parser = argparse.ArgumentParser(
        prog="tf new tags-suggest",
        description="Suggest component tags for tickets using keyword classification.",
    )
    parser.add_argument(
        "title",
        nargs="?",
        help="Ticket title to classify (if not using --ticket)",
    )
    parser.add_argument(
        "--ticket",
        "-t",
        metavar="ID",
        help="Ticket ID to fetch and classify",
    )
    parser.add_argument(
        "--description",
        "-d",
        help="Ticket description (when using title)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--rationale",
        "-r",
        action="store_true",
        help="Show rationale for each suggested tag",
    )
    return parser


def build_classify_parser() -> argparse.ArgumentParser:
    """Build the argument parser for tags-classify."""
    parser = argparse.ArgumentParser(
        prog="tf new tags-classify",
        description="Classify arbitrary text and suggest component tags.",
    )
    parser.add_argument(
        "text",
        help="Text to classify",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--rationale",
        "-r",
        action="store_true",
        help="Show rationale for each suggested tag",
    )
    return parser


def build_keywords_parser() -> argparse.ArgumentParser:
    """Build the argument parser for tags-keywords."""
    return argparse.ArgumentParser(
        prog="tf new tags-keywords",
        description="Show the keyword mapping used for component classification.",
    )


def suggest_main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for tags-suggest command."""
    parser = build_suggest_parser()
    args = parser.parse_args(argv)
    return run_suggest(
        title=args.title,
        description=args.description,
        ticket_id=args.ticket,
        json_output=args.json,
        show_rationale=args.rationale,
    )


def classify_main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for tags-classify command."""
    parser = build_classify_parser()
    args = parser.parse_args(argv)
    return run_classify_text(
        text=args.text,
        json_output=args.json,
        show_rationale=args.rationale,
    )


def keywords_main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for tags-keywords command."""
    parser = build_keywords_parser()
    parser.parse_args(argv)
    return run_show_keywords()


if __name__ == "__main__":
    raise SystemExit(suggest_main())
