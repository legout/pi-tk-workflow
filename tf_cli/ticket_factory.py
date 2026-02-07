"""Ticket creation and backlog generation helpers.

Provides reusable functions for creating tickets from seed/baseline/plan artifacts.
This module is used by tf-backlog and other planning commands to avoid repetitive
inline scripts.

Example:
    >>> from tf_cli.ticket_factory import (
    ...     create_tickets,
    ...     write_backlog_md,
    ...     score_tickets,
    ... )
    >>> tickets = [
    ...     TicketDef(title="Setup project", description="..."),
    ...     TicketDef(title="Implement feature", description="..."),
    ... ]
    >>> scored = score_tickets(tickets)
    >>> created = create_tickets(scored, topic_id="seed-foo", mode="seed")
    >>> write_backlog_md(created, topic_id="seed-foo")
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tf_cli.component_classifier import classify_components, format_tags_for_tk
from tf_cli.utils import find_project_root


#: Default keyword weights for ticket scoring.
#: Higher scores indicate higher priority (foundational tasks first).
DEFAULT_WEIGHTS: Dict[str, int] = {
    "setup": 10,
    "configure": 8,
    "define": 6,
    "design": 5,
    "implement": 3,
    "test": 1,
}


@dataclass
class TicketDef:
    """Definition of a ticket to create.

    Attributes:
        title: Ticket title
        description: Ticket description (markdown)
        optional_tags: Additional tags beyond the standard mode tags
    """

    title: str
    description: str
    optional_tags: List[str] = None

    def __post_init__(self):
        if self.optional_tags is None:
            self.optional_tags = []


@dataclass
class CreatedTicket:
    """Result of ticket creation.

    Attributes:
        id: The ticket ID returned by tk create
        title: Ticket title
        score: Calculated priority score
        tags: Tags assigned to the ticket
        depends_on: List of ticket IDs this ticket depends on
        links: List of ticket IDs linked to this ticket
        skipped: True if ticket was skipped (duplicate, etc.)
        skip_reason: Reason for skipping (if skipped)
    """

    id: str
    title: str
    score: int
    tags: List[str]
    depends_on: List[str] = None
    links: List[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.links is None:
            self.links = []


def score_tickets(
    tickets: List[TicketDef],
    weights: Optional[Dict[str, int]] = None,
) -> List[Tuple[int, TicketDef]]:
    """Score tickets based on keyword weights.

    Args:
        tickets: List of ticket definitions to score
        weights: Custom keyword weights (uses DEFAULT_WEIGHTS if not provided)

    Returns:
        List of (score, ticket) tuples sorted by score descending

    Example:
        >>> tickets = [
        ...     TicketDef("Setup project", "..."),
        ...     TicketDef("Write tests", "..."),
        ... ]
        >>> scored = score_tickets(tickets)
        >>> scored[0][0]  # First ticket (highest score)
        10
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    scored = []
    for ticket in tickets:
        text = f"{ticket.title}\n{ticket.description}"
        ticket_score = _calculate_score(text, weights)
        scored.append((ticket_score, ticket))

    # Sort by score descending, then by original order
    scored.sort(key=lambda x: (-x[0], tickets.index(x[1])))
    return scored


def _calculate_score(text: str, weights: Dict[str, int]) -> int:
    """Calculate score for text based on keyword weights.

    Args:
        text: Text to score (title + description)
        weights: Keyword weights dict

    Returns:
        Cumulative score for all matched keywords
    """
    text_lower = text.lower()
    score = 0
    for keyword, weight in weights.items():
        # Match as word boundary, but also match common variations (plural, -ing, -ed)
        # e.g., "test" matches "test", "tests", "testing", "tested"
        pattern = rf"\b{re.escape(keyword)}(?:s|ing|ed)?\b"
        if re.search(pattern, text_lower):
            score += weight
    return score


def create_tickets(
    scored_tickets: List[Tuple[int, TicketDef]],
    topic_id: str,
    mode: str = "seed",
    base_tags: Optional[List[str]] = None,
    component_tags: bool = True,
    existing_tickets: Optional[set] = None,
    skip_duplicates: bool = True,
    priority: int = 2,
    dry_run: bool = False,
) -> List[CreatedTicket]:
    """Create tickets via tk create command.

    Args:
        scored_tickets: List of (score, ticket) tuples from score_tickets()
        topic_id: Topic ID (e.g., "seed-foo", "plan-bar")
        mode: One of "seed", "baseline", "plan", "openspec"
        base_tags: Base tags to apply (default: ["tf", "backlog"] + mode-specific)
        component_tags: Whether to auto-assign component tags
        existing_tickets: Set of normalized titles to skip as duplicates
        skip_duplicates: If True, skip tickets matching existing_titles
        priority: Ticket priority (default: 2)
        dry_run: If True, print what would be done without creating

    Returns:
        List of CreatedTicket objects (including skipped tickets)

    Example:
        >>> scored = score_tickets(tickets)
        >>> created = create_tickets(
        ...     scored,
        ...     topic_id="seed-foo",
        ...     mode="seed",
        ...     dry_run=True,
        ... )
    """
    if existing_tickets is None:
        existing_tickets = set()

    if base_tags is None:
        base_tags = ["tf", "backlog"]
        if mode in ("baseline", "plan", "openspec"):
            base_tags.append(mode)

    created = []
    for score, ticket in scored_tickets:
        # Check for duplicate
        normalized_title = _normalize_title(ticket.title)
        if skip_duplicates and normalized_title in existing_tickets:
            created.append(
                CreatedTicket(
                    id="",
                    title=ticket.title,
                    score=score,
                    tags=[],
                    skipped=True,
                    skip_reason="Duplicate title",
                )
            )
            continue

        # Build tags
        tags = base_tags.copy()
        if ticket.optional_tags:
            tags.extend(ticket.optional_tags)

        # Add component tags if requested
        if component_tags:
            comp_result = classify_components(ticket.title, ticket.description)
            if comp_result.tags:
                tags.extend(comp_result.tags)

        # De-duplicate tags
        tags = _deduplicate_tags(tags)

        # Build command
        cmd = _build_create_command(
            ticket.title,
            ticket.description,
            tags,
            topic_id,
            priority,
        )

        if dry_run:
            # Print what would be done
            print(f"Would create: {ticket.title}")
            print(f"  Tags: {','.join(tags)}")
            print(f"  Score: {score}")
            continue

        # Execute command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            ticket_id = result.stdout.strip()
            if not ticket_id:
                raise RuntimeError("tk create returned empty id")

            created.append(
                CreatedTicket(
                    id=ticket_id,
                    title=ticket.title,
                    score=score,
                    tags=tags,
                )
            )
        except subprocess.CalledProcessError as e:
            print(f"Error creating ticket '{ticket.title}': {e.stderr}", file=__import__("sys").stderr)
            created.append(
                CreatedTicket(
                    id="",
                    title=ticket.title,
                    score=score,
                    tags=tags,
                    skipped=True,
                    skip_reason=f"Error: {e.stderr}",
                )
            )

    return created


def _normalize_title(title: str) -> str:
    """Normalize title for duplicate detection."""
    return re.sub(r"\s+", " ", title.lower().strip())


def _deduplicate_tags(tags: List[str]) -> List[str]:
    """Remove duplicate tags while preserving order."""
    seen = set()
    deduped = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)
    return deduped


def _build_create_command(
    title: str,
    description: str,
    tags: List[str],
    external_ref: str,
    priority: int,
) -> List[str]:
    """Build tk create command arguments."""
    return [
        "tk",
        "create",
        title,
        "--description",
        description,
        "--tags",
        ",".join(tags),
        "--type",
        "task",
        "--priority",
        str(priority),
        "--external-ref",
        external_ref,
    ]


def write_backlog_md(
    created_tickets: List[CreatedTicket],
    topic_id: str,
    output_path: Optional[Path] = None,
    knowledge_dir: Optional[Path] = None,
) -> Path:
    """Write backlog.md file for a topic.

    Args:
        created_tickets: List of CreatedTicket objects
        topic_id: Topic ID (used for file path and header)
        output_path: Explicit path for backlog.md (overrides knowledge_dir/topic_id)
        knowledge_dir: Path to knowledge directory (default: .tf/knowledge)

    Returns:
        Path to the written backlog.md file

    Example:
        >>> write_backlog_md(created, topic_id="seed-foo")
        PosixPath('.tf/knowledge/topics/seed-foo/backlog.md')
    """
    if knowledge_dir is None:
        project_root = find_project_root()
        if project_root:
            knowledge_dir = project_root / ".tf" / "knowledge"
        else:
            knowledge_dir = Path(".tf/knowledge")

    if output_path is None:
        output_path = knowledge_dir / "topics" / topic_id / "backlog.md"

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build content
    lines = [
        f"# Backlog: {topic_id}",
        "",
        "| ID | Title | Score | Est. Hours | Depends On | Links |",
        "|----|-------|-------|------------|------------|-------|",
    ]

    for ticket in created_tickets:
        if ticket.skipped:
            # Mark skipped tickets
            depends = ticket.skip_reason or "skipped"
            links = "skipped"
        else:
            depends = ",".join(ticket.depends_on) if ticket.depends_on else "-"
            links = ",".join(ticket.links) if ticket.links else "-"

        lines.append(
            f"| {ticket.id or '-'} | {ticket.title} | {ticket.score} | 1-2 | {depends} | {links} |"
        )

    content = "\n".join(lines)

    # Write file
    output_path.write_text(content, encoding="utf-8")

    return output_path


def apply_dependencies(
    created_tickets: List[CreatedTicket],
    dependency_groups: Optional[List[List[str]]] = None,
    mode: str = "chain",
    dry_run: bool = False,
) -> List[CreatedTicket]:
    """Apply dependencies between tickets using tk dep command.

    Args:
        created_tickets: List of CreatedTicket objects (unskipped only)
        dependency_groups: Optional explicit dependency groups.
            Each group is a list of ticket IDs that depend on the previous group.
            If not provided, dependencies are inferred from mode.
        mode: Dependency mode:
            - "chain": Each ticket depends on the previous one (default)
            - "phases": Tickets in group N depend on all tickets in group N-1
            - "none": No dependencies applied
        dry_run: If True, print what would be done without applying

    Returns:
        Updated list of CreatedTicket objects with depends_on populated

    Example:
        >>> # Chain mode (default)
        >>> created = apply_dependencies(created, mode="chain")
        >>> # created[1].depends_on will contain created[0].id
        >>> # created[2].depends_on will contain created[1].id

        >>> # Phases mode
        >>> groups = [[created[0].id], [created[1].id, created[2].id]]
        >>> created = apply_dependencies(created, dependency_groups=groups, mode="phases")
    """
    # Filter to non-skipped tickets with IDs
    valid_tickets = [t for t in created_tickets if not t.skipped and t.id]

    if mode == "none" or not valid_tickets:
        return created_tickets

    if dependency_groups:
        # Apply explicit dependency groups (phases mode)
        for i in range(1, len(dependency_groups)):
            current_group = dependency_groups[i]
            prev_group = dependency_groups[i - 1]

            for ticket in created_tickets:
                if ticket.id in current_group:
                    ticket.depends_on = prev_group.copy()

                    if dry_run:
                        print(f"Would add dependencies: {ticket.id} -> {prev_group}")
                    else:
                        for dep_id in prev_group:
                            subprocess.run(
                                ["tk", "dep", ticket.id, dep_id],
                                capture_output=True,
                            )

    else:
        # Chain mode: each ticket depends on previous one
        for i in range(1, len(valid_tickets)):
            current = valid_tickets[i]
            prev = valid_tickets[i - 1]

            # Find ticket in created_tickets and update
            for ticket in created_tickets:
                if ticket.id == current.id:
                    ticket.depends_on = [prev.id]

                    if dry_run:
                        print(f"Would add dependency: {ticket.id} -> {prev.id}")
                    else:
                        subprocess.run(
                            ["tk", "dep", ticket.id, prev.id],
                            capture_output=True,
                        )

    return created_tickets


def apply_links(
    created_tickets: List[CreatedTicket],
    dry_run: bool = False,
) -> List[CreatedTicket]:
    """Apply links between related tickets using tk link command.

    Links are conservative (under-linking preferred):
    - Same component tags + adjacent in creation order
    - Title similarity (shared words)

    Args:
        created_tickets: List of CreatedTicket objects (unskipped only)
        dry_run: If True, print what would be done without applying

    Returns:
        Updated list of CreatedTicket objects with links populated

    Example:
        >>> created = apply_links(created)
        >>> # Tickets with same component tags will be linked
    """
    # Filter to non-skipped tickets with IDs
    valid_tickets = [t for t in created_tickets if not t.skipped and t.id]

    for i, ticket in enumerate(valid_tickets):
        # Check next ticket for linkage
        if i + 1 >= len(valid_tickets):
            continue

        next_ticket = valid_tickets[i + 1]

        # Check if tickets should be linked
        should_link = _should_link_tickets(ticket, next_ticket)

        if should_link:
            # Add links to both tickets
            for t in created_tickets:
                if t.id == ticket.id:
                    if next_ticket.id not in t.links:
                        t.links.append(next_ticket.id)
                elif t.id == next_ticket.id:
                    if ticket.id not in t.links:
                        t.links.append(ticket.id)

            if dry_run:
                print(f"Would link: {ticket.id} <-> {next_ticket.id}")
            else:
                subprocess.run(
                    ["tk", "link", ticket.id, next_ticket.id],
                    capture_output=True,
                )

    return created_tickets


def _should_link_tickets(t1: CreatedTicket, t2: CreatedTicket) -> bool:
    """Determine if two tickets should be linked."""
    # Check for shared component tags
    comp_tags_1 = [t for t in t1.tags if t.startswith("component:")]
    comp_tags_2 = [t for t in t2.tags if t.startswith("component:")]

    if comp_tags_1 and comp_tags_2:
        # Have component tags - check for overlap
        if set(comp_tags_1) & set(comp_tags_2):
            return True

    # Check for title similarity (shared significant words)
    words_1 = set(_extract_significant_words(t1.title))
    words_2 = set(_extract_significant_words(t2.title))

    if words_1 & words_2:
        # At least one shared significant word
        return True

    return False


def _extract_significant_words(title: str) -> List[str]:
    """Extract significant words from title for similarity matching."""
    # Lowercase and extract alphanumeric words
    words = re.findall(r"\b[a-z]{3,}\b", title.lower())

    # Filter out common words
    stop_words = {
        "and", "the", "for", "add", "set", "use", "new", "old", "fix",
        "make", "get", "put", "see", "did", "not", "but", "can", "all",
    }

    return [w for w in words if w not in stop_words]


def print_created_summary(created_tickets: List[CreatedTicket]) -> None:
    """Print a summary of created tickets.

    Args:
        created_tickets: List of CreatedTicket objects
    """
    created = [t for t in created_tickets if not t.skipped]
    skipped = [t for t in created_tickets if t.skipped]

    if created:
        print("\nCREATED")
        for ticket in created:
            tags_str = ",".join(ticket.tags) if ticket.tags else "-"
            print(f"{ticket.id}\t{ticket.title}\t(score: {ticket.score}, tags: {tags_str})")

    if skipped:
        print("\nSKIPPED")
        for ticket in skipped:
            reason = ticket.skip_reason or "unknown"
            print(f"{ticket.title}\t({reason})")

    print(f"\nSummary: {len(created)} created, {len(skipped)} skipped")
