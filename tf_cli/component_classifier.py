"""Conservative component classifier for ticket tagging.

Maps keywords in ticket titles/descriptions to component tags.
Designed to be simple, explainable, and easy to extend.

Example:
    >>> from tf_cli.component_classifier import classify_components
    >>> result = classify_components("Add --version flag to CLI")
    >>> result.tags
    ['component:cli']
    >>> result.rationale
    {"component:cli": "Matched keywords: CLI, flag"}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union


#: Default keyword-to-component mapping.
#: Extend this by passing custom_keywords to classify_components().
DEFAULT_KEYWORD_MAP: Dict[str, List[str]] = {
    "component:cli": [
        "cli",
        "command",
        "command-line",
        "argument",
        "flag",
        "option",
        "subcommand",
        "argparse",
        "terminal",
        "shell",
        "script",
        "shim",
        "uvx",
        "pip",
        "install",
    ],
    "component:api": [
        "api",
        "endpoint",
        "rest",
        "graphql",
        "http",
        "request",
        "response",
        "json",
        "webhook",
        "sdk",
        "interface",
        "protocol",
    ],
    "component:docs": [
        "doc",
        "documentation",
        "readme",
        "guide",
        "tutorial",
        "example",
        "reference",
        "manual",
        "markdown",
        "md",
        "help text",
        "comment",
    ],
    "component:tests": [
        "test",
        "testing",
        "pytest",
        "unittest",
        "coverage",
        "mock",
        "fixture",
        "assert",
        "e2e",
        "integration test",
        "unit test",
        "regression",
        "qa",
        "quality",
    ],
    "component:config": [
        "config",
        "configuration",
        "settings",
        "setting",
        "json",
        "yaml",
        "yml",
        "toml",
        "env",
        "environment",
        "variable",
        "dotfile",
        ".tf",
        "setup",
        "init",
    ],
    "component:workflow": [
        "workflow",
        "ralph",
        "loop",
        "irf",
        "implement",
        "review",
        "fix",
        "close",
        "ticket",
        "backlog",
        "seed",
        "baseline",
        "plan",
    ],
    "component:agents": [
        "agent",
        "subagent",
        "reviewer",
        "fixer",
        "implementer",
        "worker",
        "prompt",
        "skill",
        "mcp",
    ],
}


@dataclass(frozen=True)
class ClassificationResult:
    """Result of component classification.

    Attributes:
        tags: List of component tags (e.g., ['component:cli', 'component:tests'])
        rationale: Dict mapping each tag to its rationale string
        matched_keywords: Dict mapping each tag to the keywords that matched
    """

    tags: List[str] = field(default_factory=list)
    rationale: Dict[str, str] = field(default_factory=dict)
    matched_keywords: Dict[str, List[str]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Return True if any tags were classified."""
        return bool(self.tags)


def _normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, preserve structure."""
    return text.lower()


def _find_matches(text: str, keywords: List[str]) -> List[str]:
    """Find all keywords that appear in the text.

    Args:
        text: Normalized text to search in
        keywords: List of keywords to look for

    Returns:
        List of keywords that were found in the text
    """
    matches = []
    for kw in keywords:
        # Match whole words or substrings for compound terms
        if " " in kw:
            # Multi-word keyword: match as substring
            if kw in text:
                matches.append(kw)
        else:
            # Single word: match as word boundary or substring for short terms
            if len(kw) <= 4:
                # Short terms: substring match (e.g., "cli" matches "cli-root")
                if kw in text:
                    matches.append(kw)
            else:
                # Longer terms: word boundary match
                # Simple word boundary check: preceded/followed by non-word char
                import re

                pattern = r"(?:^|[^a-z0-9])" + re.escape(kw) + r"(?:[^a-z0-9]|$)"
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(kw)
    return matches


def classify_components(
    title: str,
    description: str = "",
    keyword_map: Optional[Dict[str, List[str]]] = None,
    custom_keywords: Optional[Dict[str, List[str]]] = None,
    min_confidence: float = 0.0,
) -> ClassificationResult:
    """Classify a ticket into component tags based on keyword matching.

    This is a conservative classifier: it only assigns tags when keywords
    explicitly match, avoiding false positives. It's designed to be:
    - Simple and explainable
    - Deterministic (same input always gives same output)
    - Easy to extend without modifying core logic

    Args:
        title: Ticket title (required)
        description: Ticket description (optional)
        keyword_map: Complete mapping to use instead of DEFAULT_KEYWORD_MAP
        custom_keywords: Additional keywords to merge with DEFAULT_KEYWORD_MAP
        min_confidence: Minimum confidence threshold (0.0-1.0, currently unused)

    Returns:
        ClassificationResult with tags, rationale, and matched keywords

    Example:
        >>> result = classify_components(
        ...     "Add --version flag to CLI",
        ...     "Implement a --version flag that prints the version"
        ... )
        >>> result.tags
        ['component:cli']
        >>> result.rationale['component:cli']
        'Matched keywords: CLI, flag'

        >>> # With custom keywords
        >>> result = classify_components(
        ...     "Update ML model training",
        ...     custom_keywords={"component:ml": ["model", "training", "ml"]}
        ... )
    """
    # Build the effective keyword map
    if keyword_map is not None:
        effective_map = keyword_map
    else:
        effective_map = dict(DEFAULT_KEYWORD_MAP)
        if custom_keywords:
            for tag, keywords in custom_keywords.items():
                if tag in effective_map:
                    effective_map[tag] = list(set(effective_map[tag] + keywords))
                else:
                    effective_map[tag] = list(keywords)

    # Normalize text
    text = _normalize_text(f"{title} {description}")

    # Find matches for each component
    tags = []
    rationale = {}
    matched_keywords = {}

    for tag, keywords in effective_map.items():
        matches = _find_matches(text, keywords)
        if matches:
            tags.append(tag)
            matched_keywords[tag] = matches
            # Build rationale
            match_str = ", ".join(sorted(set(matches)))
            rationale[tag] = f"Matched keywords: {match_str}"

    # Sort tags for deterministic output
    tags.sort()

    return ClassificationResult(
        tags=tags,
        rationale=rationale,
        matched_keywords=matched_keywords,
    )


def get_keyword_map_documentation() -> str:
    """Return markdown documentation of the default keyword mapping.

    This can be used to generate documentation or help text.
    """
    lines = ["# Component Keyword Mapping\n"]
    lines.append("The following keywords map to each component tag:\n")

    for tag, keywords in sorted(DEFAULT_KEYWORD_MAP.items()):
        lines.append(f"## {tag}\n")
        for kw in sorted(keywords):
            lines.append(f"- `{kw}`")
        lines.append("")

    return "\n".join(lines)


def suggest_tags_for_ticket(
    ticket_id: str,
    keyword_map: Optional[Dict[str, List[str]]] = None,
    custom_keywords: Optional[Dict[str, List[str]]] = None,
) -> ClassificationResult:
    """Suggest component tags for an existing ticket.

    Fetches the ticket via `tk show` and classifies it.

    Args:
        ticket_id: The ticket ID (e.g., "abc-1234")
        keyword_map: Optional custom keyword mapping
        custom_keywords: Optional additional keywords

    Returns:
        ClassificationResult with suggested tags

    Raises:
        RuntimeError: If tk command fails or ticket not found
    """
    import subprocess

    try:
        result = subprocess.run(
            ["tk", "show", ticket_id],
            capture_output=True,
            text=True,
            check=True,
        )
        content = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch ticket {ticket_id}: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError("tk command not found. Is ticketflow installed?")

    # Parse title and description from ticket content
    # Ticket format: frontmatter + markdown body
    lines = content.splitlines()
    title = ""
    description = ""
    in_frontmatter = False
    body_lines = []

    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        body_lines.append(line)

    # First line of body is usually the title (H1)
    if body_lines:
        first_line = body_lines[0].strip()
        if first_line.startswith("# "):
            title = first_line[2:].strip()
        else:
            title = first_line
        description = "\n".join(body_lines[1:]).strip()

    return classify_components(
        title=title,
        description=description,
        keyword_map=keyword_map,
        custom_keywords=custom_keywords,
    )


def format_tags_for_tk(tags: List[str]) -> str:
    """Format tags for use with tk commands.

    Args:
        tags: List of component tags

    Returns:
        Comma-separated string suitable for tk tag commands
    """
    return ",".join(tags)


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python component_classifier.py '<title>' [description]")
        print("\nDefault keyword mapping:")
        print(get_keyword_map_documentation())
        sys.exit(0)

    test_title = sys.argv[1]
    test_desc = sys.argv[2] if len(sys.argv) > 2 else ""

    result = classify_components(test_title, test_desc)

    print(f"Title: {test_title}")
    if test_desc:
        print(f"Description: {test_desc}")
    print(f"\nSuggested tags: {result.tags if result.tags else '(none)'}")
    if result.rationale:
        print("\nRationale:")
        for tag in result.tags:
            print(f"  {tag}: {result.rationale[tag]}")
