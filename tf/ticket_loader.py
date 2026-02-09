"""Ticket loader for UI with frontmatter parsing and lazy body loading.

This module provides efficient loading of ticket metadata from `.tickets/*.md` files,
with support for lazy loading of full ticket body content.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Optional YAML import - fall back to basic parsing if not available
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

logger = logging.getLogger(__name__)

# Regex pattern for YAML frontmatter (supports both Unix \n and Windows \r\n line endings)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.DOTALL)

# Regex pattern for markdown title (first # heading)
TITLE_PATTERN = re.compile(r"^#\s*(.+)$", re.MULTILINE)


@dataclass
class Ticket:
    """Represents a ticket with metadata and lazy body loading.

    Attributes:
        id: Ticket ID (e.g., "pt-yeny")
        status: Ticket status (e.g., "open", "closed", "in-progress")
        title: Ticket title from markdown heading
        file_path: Path to the ticket markdown file
        deps: List of ticket dependencies
        tags: List of tags
        assignee: Optional assignee username
        external_ref: Optional external reference
        priority: Optional priority level
        ticket_type: Optional ticket type
        created: Optional creation timestamp
        links: List of linked tickets
        _body: Cached body content (None until loaded)
        _body_loaded: Whether body has been loaded
    """

    id: str
    status: str
    title: str
    file_path: Path
    deps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    external_ref: Optional[str] = None
    priority: Optional[int] = None
    ticket_type: Optional[str] = None
    created: Optional[str] = None
    links: list[str] = field(default_factory=list)
    _body: Optional[str] = field(default=None, repr=False)
    _body_loaded: bool = field(default=False, repr=False)

    @property
    def body(self) -> str:
        """Get the full ticket body, loading lazily if needed.

        Returns:
            The markdown body content (excluding frontmatter and title).
        """
        if not self._body_loaded:
            self._load_body()
        return self._body or ""

    def _load_body(self) -> None:
        """Load the body content from disk."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
            # Extract body after frontmatter
            match = FRONTMATTER_PATTERN.match(content)
            if match:
                body_content = match.group(2)
            else:
                body_content = content

            # Remove title line if present
            lines = body_content.split("\n")
            if lines and lines[0].startswith("# "):
                body_content = "\n".join(lines[1:]).lstrip("\n")

            self._body = body_content
        except (IOError, OSError) as e:
            logger.warning(f"Failed to load body for ticket {self.id}: {e}")
            self._body = ""
        self._body_loaded = True

    def get_summary(self) -> str:
        """Get a summary of the ticket for display.

        Returns:
            A formatted summary string.
        """
        parts = [f"[{self.status}] {self.id}: {self.title}"]
        if self.assignee:
            parts.append(f"  Assignee: {self.assignee}")
        if self.tags:
            parts.append(f"  Tags: {', '.join(self.tags)}")
        if self.deps:
            parts.append(f"  Dependencies: {', '.join(self.deps)}")
        return "\n".join(parts)


class TicketLoadError(Exception):
    """Raised when a ticket cannot be loaded."""
    pass


class TicketLoader:
    """Loads tickets from `.tickets/*.md` files.

    This loader provides:
    - Efficient loading of frontmatter + title only (fast for many tickets)
    - Lazy loading of full body content (on demand)
    - Graceful handling of malformed tickets (warnings, no crashes)

    Example:
        >>> loader = TicketLoader()
        >>> tickets = loader.load_all()
        >>> for ticket in tickets:
        ...     print(f"{ticket.id}: {ticket.title}")
        ...     # Body is only loaded when accessed:
        ...     print(ticket.body[:100])
    """

    def __init__(self, tickets_dir: Optional[Path] = None):
        """Initialize the loader.

        Args:
            tickets_dir: Optional path to tickets directory.
                        If not provided, resolves to `.tickets` in repo root or cwd.
        """
        self.tickets_dir = tickets_dir or self._resolve_tickets_dir()
        self._tickets: list[Ticket] = []
        self._by_id: dict[str, Ticket] = {}
        self._loaded = False

    def _resolve_tickets_dir(self) -> Path:
        """Resolve the tickets directory from repo root or cwd.

        Returns:
            Resolved Path to the tickets directory
        """
        # Find repo root by looking for .tf directory
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            tf_dir = parent / ".tf"
            if tf_dir.is_dir():
                return parent / ".tickets"

        # Fallback to cwd
        return cwd / ".tickets"

    def load_all(self) -> list[Ticket]:
        """Load all tickets from the tickets directory.

        Returns:
            List of all loaded tickets (metadata only, bodies are lazy-loaded).

        Raises:
            TicketLoadError: If tickets directory cannot be found.
        """
        if not self.tickets_dir.exists():
            raise TicketLoadError(
                f"Tickets directory not found: {self.tickets_dir}\n"
                "Run 'tk init' to create it."
            )

        self._tickets = []
        self._by_id = {}

        # Find all .md files in tickets directory
        ticket_files = sorted(self.tickets_dir.glob("*.md"))

        for file_path in ticket_files:
            try:
                ticket = self._parse_ticket(file_path)
                if ticket:
                    self._tickets.append(ticket)
                    self._by_id[ticket.id] = ticket
            except Exception as e:
                logger.warning(f"Skipping malformed ticket {file_path.name}: {e}")
                continue

        self._loaded = True
        return self._tickets.copy()

    def _parse_ticket(self, file_path: Path) -> Optional[Ticket]:
        """Parse a single ticket file.

        Args:
            file_path: Path to the ticket markdown file

        Returns:
            Parsed Ticket or None if parsing fails
        """
        content = file_path.read_text(encoding="utf-8")

        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)
        if frontmatter is None:
            logger.warning(f"No frontmatter found in {file_path.name}")
            return None

        # Extract title from markdown body
        title = self._extract_title(content)

        # Build ticket object
        return Ticket(
            id=frontmatter.get("id", file_path.stem),
            status=frontmatter.get("status", "unknown"),
            title=title,
            file_path=file_path,
            deps=frontmatter.get("deps", []),
            tags=frontmatter.get("tags", []),
            assignee=frontmatter.get("assignee"),
            external_ref=frontmatter.get("external-ref"),
            priority=frontmatter.get("priority"),
            ticket_type=frontmatter.get("type"),
            created=frontmatter.get("created"),
            links=frontmatter.get("links", []),
        )

    def _parse_frontmatter(self, content: str) -> Optional[dict]:
        """Parse YAML frontmatter from content.

        Args:
            content: The markdown file content

        Returns:
            Dictionary of frontmatter fields or None if no frontmatter
        """
        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            return None

        frontmatter_text = match.group(1)

        if HAS_YAML:
            try:
                return yaml.safe_load(frontmatter_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"YAML parsing failed, trying basic parser: {e}")
                # Fallback to basic parser on YAML failure
                return self._basic_parse_frontmatter(frontmatter_text)
        else:
            # Basic fallback parsing for simple key: value pairs
            return self._basic_parse_frontmatter(frontmatter_text)

    def _basic_parse_frontmatter(self, text: str) -> dict:
        """Basic frontmatter parser as fallback when YAML is not available.

        Handles simple key: value and key: [list] formats.

        Args:
            text: The frontmatter text (without delimiters)

        Returns:
            Dictionary of parsed fields
        """
        result = {}
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Try to parse as list
                if value.startswith("[") and value.endswith("]"):
                    # Parse [item1, item2, item3]
                    list_content = value[1:-1]
                    result[key] = [
                        item.strip().strip('"\'') for item in list_content.split(",") if item.strip()
                    ]
                elif value.lower() == "true":
                    result[key] = True
                elif value.lower() == "false":
                    result[key] = False
                elif value == "":
                    result[key] = None
                else:
                    # Try to parse as number (int or float)
                    try:
                        if "." in value:
                            result[key] = float(value)
                        else:
                            result[key] = int(value)
                    except ValueError:
                        # Not a number, store as string
                        result[key] = value

        return result

    def _extract_title(self, content: str) -> str:
        """Extract the title from markdown content.

        Args:
            content: The markdown file content

        Returns:
            The title (first # heading) or empty string if not found
        """
        # Remove frontmatter first
        match = FRONTMATTER_PATTERN.match(content)
        if match:
            body = match.group(2)
        else:
            body = content

        # Find first # heading
        title_match = TITLE_PATTERN.search(body)
        if title_match:
            return title_match.group(1).strip()

        return ""

    def get_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by its ID.

        Args:
            ticket_id: The ticket ID to look up

        Returns:
            The ticket if found, None otherwise

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return self._by_id.get(ticket_id)

    def get_by_status(self, status: str) -> list[Ticket]:
        """Get tickets filtered by status.

        Args:
            status: Status to filter by (e.g., "open", "closed")

        Returns:
            List of tickets with matching status

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return [t for t in self._tickets if t.status == status]

    def get_by_tag(self, tag: str) -> list[Ticket]:
        """Get tickets filtered by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tickets with the specified tag

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return [t for t in self._tickets if tag in t.tags]

    def get_by_assignee(self, assignee: str) -> list[Ticket]:
        """Get tickets filtered by assignee.

        Args:
            assignee: Assignee username to filter by

        Returns:
            List of tickets assigned to the user

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return [t for t in self._tickets if t.assignee == assignee]

    def search(self, query: str) -> list[Ticket]:
        """Search tickets by query string in title, id, or tags.

        Args:
            query: Search string (case-insensitive substring match)

        Returns:
            List of matching tickets

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")

        query_lower = query.lower()
        results = []

        for ticket in self._tickets:
            # Search in ID
            if query_lower in ticket.id.lower():
                results.append(ticket)
                continue
            # Search in title
            if query_lower in ticket.title.lower():
                results.append(ticket)
                continue
            # Search in tags
            if any(query_lower in tag.lower() for tag in ticket.tags):
                results.append(ticket)
                continue

        return results

    @property
    def all_tickets(self) -> list[Ticket]:
        """Get all loaded tickets.

        Returns:
            List of all tickets

        Raises:
            TicketLoadError: If tickets haven't been loaded
        """
        if not self._loaded:
            raise TicketLoadError("Tickets not loaded. Call load_all() first.")
        return self._tickets.copy()

    @property
    def count_by_status(self) -> dict[str, int]:
        """Get count of tickets by status.

        Returns:
            Dictionary mapping status to count
        """
        if not self._loaded:
            return {}

        counts: dict[str, int] = {}
        for ticket in self._tickets:
            counts[ticket.status] = counts.get(ticket.status, 0) + 1
        return counts


def format_ticket_list(tickets: list[Ticket], show_tags: bool = False) -> str:
    """Format a list of tickets for display.

    Args:
        tickets: List of tickets to format
        show_tags: Whether to show tags for each ticket

    Returns:
        Formatted string suitable for display
    """
    if not tickets:
        return "No tickets found."

    lines = []
    for ticket in tickets:
        tag_str = ""
        if show_tags and ticket.tags:
            tag_str = f" [{', '.join(ticket.tags)}]"
        lines.append(f"  [{ticket.status}] {ticket.id}: {ticket.title}{tag_str}")

    return "\n".join(lines)
