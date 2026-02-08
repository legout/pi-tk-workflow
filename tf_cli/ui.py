"""Textual TUI for Ticketflow.

Provides a Kanban-style interface for viewing tickets and browsing knowledge topics.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def resolve_knowledge_dir() -> Path:
    """Resolve the knowledge directory from config or default.
    
    Resolution order:
    1. TF_KNOWLEDGE_DIR environment variable
    2. workflow.knowledgeDir from .tf/config/settings.json
    3. Default: .tf/knowledge (relative to repo root or cwd)
    
    Returns:
        Resolved Path to the knowledge directory
    """
    # 1. Environment variable
    env_dir = os.environ.get("TF_KNOWLEDGE_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    
    # 2. Find repo root and check config
    repo_root = _find_repo_root()
    if repo_root:
        local_config = repo_root / ".tf" / "config" / "settings.json"
        if local_config.is_file():
            try:
                with open(local_config, "r", encoding="utf-8") as f:
                    config = json.load(f)
                knowledge_dir = config.get("workflow", {}).get("knowledgeDir")
                if knowledge_dir:
                    path = Path(knowledge_dir).expanduser()
                    if path.is_absolute():
                        return path.resolve()
                    return (repo_root / path).resolve()
            except (json.JSONDecodeError, IOError):
                pass
        return (repo_root / ".tf" / "knowledge").resolve()
    
    # 3. Fallback to cwd
    return (Path.cwd() / ".tf" / "knowledge").resolve()


def _find_repo_root() -> Optional[Path]:
    """Find the repository root by looking for .tf directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        tf_dir = parent / ".tf"
        if tf_dir.is_dir():
            has_tickets = (tf_dir / "tickets").is_dir()
            has_ralph = (tf_dir / "ralph").is_dir()
            has_agents = (parent / "AGENTS.md").is_file()
            if has_tickets or has_ralph or has_agents:
                return parent
    return None


def get_topic_type(topic_id: str) -> str:
    """Derive topic type from topic ID prefix.
    
    Args:
        topic_id: The topic ID (e.g., "seed-add-versioning")
        
    Returns:
        The topic type: "seed", "plan", "spike", "baseline", or "unknown"
    """
    if topic_id.startswith("seed-"):
        return "seed"
    elif topic_id.startswith("plan-"):
        return "plan"
    elif topic_id.startswith("spike-"):
        return "spike"
    elif topic_id.startswith("baseline-"):
        return "baseline"
    else:
        return "unknown"


@dataclass
class TopicDoc:
    """Represents a topic document with path and existence info."""
    path: str
    exists: bool


@dataclass
class Topic:
    """Represents a knowledge topic with resolved documentation paths."""
    id: str
    title: str
    keywords: list[str] = field(default_factory=list)
    topic_type: str = "unknown"
    overview: Optional[TopicDoc] = None
    sources: Optional[TopicDoc] = None
    plan: Optional[TopicDoc] = None
    backlog: Optional[TopicDoc] = None
    
    @property
    def available_docs(self) -> dict[str, TopicDoc]:
        """Return mapping of doc types to docs that exist."""
        docs = {}
        for doc_type in ["overview", "sources", "plan", "backlog"]:
            doc = getattr(self, doc_type)
            if doc and doc.exists:
                docs[doc_type] = doc
        return docs


class TopicIndexLoadError(Exception):
    """Raised when topic index cannot be loaded."""
    pass


class TopicIndexLoader:
    """Loads and provides access to knowledge topics from index.json.
    
    This class handles:
    - Loading .tf/knowledge/index.json
    - Grouping topics by type (seed/spike/plan/baseline)
    - Resolving documentation paths for each topic
    - Providing filtered access to topics
    
    Example:
        >>> loader = TopicIndexLoader()
        >>> topics = loader.load()
        >>> seed_topics = loader.get_by_type("seed")
        >>> for topic in seed_topics:
        ...     print(f"{topic.id}: {topic.title}")
        ...     print(f"  Available docs: {list(topic.available_docs.keys())}")
    """
    
    def __init__(self, knowledge_dir: Optional[Path] = None):
        """Initialize the loader.
        
        Args:
            knowledge_dir: Optional path to knowledge directory.
                          If not provided, resolves automatically.
        """
        self.knowledge_dir = knowledge_dir or resolve_knowledge_dir()
        self._topics: list[Topic] = []
        self._by_type: dict[str, list[Topic]] = {}
        self._by_id: dict[str, Topic] = {}
        self._loaded = False
    
    def load(self) -> list[Topic]:
        """Load topics from index.json.
        
        Returns:
            List of all topics.
            
        Raises:
            TopicIndexLoadError: If index.json cannot be read or is invalid.
        """
        index_path = self.knowledge_dir / "index.json"
        
        if not index_path.exists():
            raise TopicIndexLoadError(
                f"Knowledge index not found: {index_path}\n"
                "Run 'tf kb rebuild-index' to create it."
            )
        
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TopicIndexLoadError(
                f"Invalid JSON in {index_path}: {e}\n"
                "Run 'tf kb rebuild-index' to fix it."
            )
        except IOError as e:
            raise TopicIndexLoadError(f"Cannot read {index_path}: {e}")
        
        # Handle both dict with 'topics' key and legacy list format
        if isinstance(data, dict):
            topics_data = data.get("topics", [])
        elif isinstance(data, list):
            topics_data = data
        else:
            raise TopicIndexLoadError(
                f"Invalid index format: expected dict or list, got {type(data).__name__}\n"
                "Run 'tf kb rebuild-index' to fix it."
            )
        
        self._topics = []
        self._by_type = {"seed": [], "plan": [], "spike": [], "baseline": [], "unknown": []}
        self._by_id = {}
        
        for topic_data in topics_data:
            topic = self._parse_topic(topic_data)
            self._topics.append(topic)
            self._by_type[topic.topic_type].append(topic)
            self._by_id[topic.id] = topic
        
        self._loaded = True
        return self._topics
    
    def _parse_topic(self, data: dict) -> Topic:
        """Parse a topic from index.json data.
        
        Args:
            data: Raw topic data from index.json
            
        Returns:
            Parsed Topic with resolved doc paths
        """
        topic_id = data.get("id", "")
        topic_type = get_topic_type(topic_id)
        
        # Resolve doc paths
        def resolve_doc(doc_path: Optional[str]) -> Optional[TopicDoc]:
            if not doc_path:
                return None
            full_path = self.knowledge_dir / doc_path
            return TopicDoc(
                path=doc_path,
                exists=full_path.exists()
            )
        
        return Topic(
            id=topic_id,
            title=data.get("title", ""),
            keywords=data.get("keywords", []),
            topic_type=topic_type,
            overview=resolve_doc(data.get("overview")),
            sources=resolve_doc(data.get("sources")),
            plan=resolve_doc(data.get("plan")),
            backlog=resolve_doc(data.get("backlog")),
        )
    
    def get_all(self) -> list[Topic]:
        """Get all topics.
        
        Returns:
            List of all loaded topics.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._topics.copy()
    
    def get_by_type(self, topic_type: str) -> list[Topic]:
        """Get topics filtered by type.
        
        Args:
            topic_type: One of "seed", "plan", "spike", "baseline", "unknown"
            
        Returns:
            List of topics of the specified type.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._by_type.get(topic_type, []).copy()
    
    def get_by_id(self, topic_id: str) -> Optional[Topic]:
        """Get a topic by its ID.
        
        Args:
            topic_id: The topic ID to look up
            
        Returns:
            The topic if found, None otherwise.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        return self._by_id.get(topic_id)
    
    def search(self, query: str) -> list[Topic]:
        """Search topics by keyword in title or keywords.
        
        Args:
            query: Search string (case-insensitive substring match)
            
        Returns:
            List of matching topics.
            
        Raises:
            TopicIndexLoadError: If topics haven't been loaded.
        """
        if not self._loaded:
            raise TopicIndexLoadError("Topics not loaded. Call load() first.")
        
        query_lower = query.lower()
        results = []
        
        for topic in self._topics:
            # Search in title
            if query_lower in topic.title.lower():
                results.append(topic)
                continue
            # Search in keywords
            if any(query_lower in kw.lower() for kw in topic.keywords):
                results.append(topic)
                continue
            # Search in ID
            if query_lower in topic.id.lower():
                results.append(topic)
        
        return results
    
    @property
    def topic_types(self) -> list[str]:
        """Get list of available topic types that have topics."""
        if not self._loaded:
            return []
        return [t for t in ["seed", "plan", "spike", "baseline"] if self._by_type[t]]
    
    @property
    def count_by_type(self) -> dict[str, int]:
        """Get count of topics by type."""
        if not self._loaded:
            return {}
        return {
            "seed": len(self._by_type["seed"]),
            "plan": len(self._by_type["plan"]),
            "spike": len(self._by_type["spike"]),
            "baseline": len(self._by_type["baseline"]),
            "unknown": len(self._by_type["unknown"]),
        }


def format_topic_list(topics: list[Topic], show_docs: bool = False) -> str:
    """Format a list of topics for display.
    
    Args:
        topics: List of topics to format
        show_docs: Whether to show available docs for each topic
        
    Returns:
        Formatted string suitable for display
    """
    if not topics:
        return "No topics found."
    
    lines = []
    for topic in topics:
        doc_indicator = ""
        if show_docs and topic.available_docs:
            doc_indicator = f" [{', '.join(topic.available_docs.keys())}]"
        lines.append(f"  {topic.id}: {topic.title}{doc_indicator}")
    
    return "\n".join(lines)


def open_topic_doc(topic: Topic, doc_type: str) -> bool:
    """Open a topic document in $PAGER or $EDITOR.
    
    Args:
        topic: The topic containing the document
        doc_type: Type of document to open (overview, sources, plan, backlog)
        
    Returns:
        True if document was opened, False otherwise
    """
    doc = getattr(topic, doc_type, None)
    if not doc or not doc.exists:
        return False
    
    doc_path = Path(topic.id).parent / doc.path
    full_path = resolve_knowledge_dir() / doc.path
    
    # Try $PAGER first, then $EDITOR, then fallback
    pager = os.environ.get("PAGER", "")
    editor = os.environ.get("EDITOR", "")
    
    if pager:
        cmd = f'{pager} "{full_path}"'
    elif editor:
        cmd = f'{editor} "{full_path}"'
    else:
        # Fallback to common pagers
        for fallback in ["less", "more", "cat"]:
            if os.system(f"which {fallback} > /dev/null 2>&1") == 0:
                cmd = f'{fallback} "{full_path}"'
                break
        else:
            return False
    
    os.system(cmd)
    return True


def main(argv: Optional[list[str]] = None) -> int:
    """Launch the Ticketflow TUI.
    
    Args:
        argv: Command line arguments (unused, for API compatibility)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Check if we're running in a TTY
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Error: tf ui requires an interactive terminal (TTY)", file=sys.stderr)
        return 1
    
    try:
        from textual.app import App, ComposeResult
        from textual.widgets import (
            Static, Header, Footer, ListView, ListItem, Label,
            TabbedContent, TabPane, Input, Markdown
        )
        from textual.containers import Horizontal, Vertical
        from textual.reactive import reactive
    except ImportError:
        print("Error: Textual is not installed. Run: pip install textual", file=sys.stderr)
        return 1
    
    class TopicBrowser(Static):
        """Widget for browsing knowledge topics."""
        
        topics: reactive[list[Topic]] = reactive([])
        selected_topic: reactive[Optional[Topic]] = reactive(None)
        
        def compose(self) -> ComposeResult:
            """Compose the topic browser layout."""
            with Horizontal():
                # Left sidebar: topic list
                with Vertical(id="topic-sidebar"):
                    yield Input(placeholder="Search topics...", id="topic-search")
                    yield ListView(id="topic-list")
                
                # Right panel: topic details
                with Vertical(id="topic-detail"):
                    yield Static("Select a topic to view details", id="topic-detail-content")
        
        def on_mount(self) -> None:
            """Load topics when mounted."""
            self.load_topics()
        
        def load_topics(self) -> None:
            """Load topics from index."""
            try:
                loader = TopicIndexLoader()
                self.topics = loader.load()
                self.update_topic_list()
            except TopicIndexLoadError as e:
                self.query_one("#topic-list", ListView).clear()
                self.query_one("#topic-detail-content", Static).update(
                    f"[red]Error loading topics:[/red]\n{e}"
                )
        
        def update_topic_list(self) -> None:
            """Update the topic list display."""
            list_view = self.query_one("#topic-list", ListView)
            list_view.clear()
            
            # Group by type
            by_type: dict[str, list[Topic]] = {}
            for topic in self.topics:
                by_type.setdefault(topic.topic_type, []).append(topic)
            
            # Add items grouped by type
            for type_name in ["plan", "spike", "seed", "baseline", "unknown"]:
                if type_name in by_type:
                    # Add type header
                    list_view.append(ListItem(
                        Label(f"[b]{type_name.upper()}[/b]"),
                        disabled=True
                    ))
                    # Add topics
                    for topic in sorted(by_type[type_name], key=lambda t: t.title):
                        list_view.append(ListItem(
                            Label(f"  {topic.title}"),
                            data=topic
                        ))
        
        def on_list_view_selected(self, event: ListView.Selected) -> None:
            """Handle topic selection."""
            item = event.item
            if hasattr(item, "data") and item.data:
                self.selected_topic = item.data
                self.update_detail_view()
        
        def update_detail_view(self) -> None:
            """Update the detail view for selected topic."""
            if not self.selected_topic:
                return
            
            topic = self.selected_topic
            content = self.query_one("#topic-detail-content", Static)
            
            # Build detail text
            lines = [
                f"[b]{topic.title}[/b]",
                f"",
                f"ID: {topic.id}",
                f"Type: {topic.topic_type}",
            ]
            
            if topic.keywords:
                lines.append(f"Keywords: {', '.join(topic.keywords)}")
            
            lines.append("")
            lines.append("[b]Available Documents:[/b]")
            
            for doc_type, doc in topic.available_docs.items():
                lines.append(f"  • {doc_type}: {doc.path}")
            
            if not topic.available_docs:
                lines.append("  (no documents available)")
            
            content.update("\n".join(lines))
        
        def on_input_changed(self, event: Input.Changed) -> None:
            """Handle search input."""
            if not event.value:
                self.update_topic_list()
                return
            
            try:
                loader = TopicIndexLoader()
                loader._topics = self.topics  # Use already loaded topics
                loader._loaded = True
                results = loader.search(event.value)
                
                list_view = self.query_one("#topic-list", ListView)
                list_view.clear()
                
                for topic in sorted(results, key=lambda t: t.title):
                    list_view.append(ListItem(
                        Label(f"[{topic.topic_type}] {topic.title}"),
                        data=topic
                    ))
            except Exception:
                pass  # Ignore search errors
    
    class TicketflowApp(App):
        """Textual app for Ticketflow."""
        
        CSS = """
        Screen {
            align: center middle;
        }
        
        #placeholder {
            width: 60;
            height: auto;
            border: solid green;
            padding: 1 2;
            text-align: center;
        }
        
        #topic-sidebar {
            width: 40%;
            border: solid $primary;
            padding: 1;
        }
        
        #topic-detail {
            width: 60%;
            border: solid $primary;
            padding: 1;
        }
        
        #topic-list {
            height: 1fr;
            border: solid $primary-darken-2;
        }
        
        #topic-search {
            margin-bottom: 1;
        }
        
        #topic-detail-content {
            height: 1fr;
        }
        
        ListView > ListItem.--highlight {
            background: $primary-darken-2;
        }
        """
        
        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh", "Refresh"),
        ]
        
        def compose(self) -> ComposeResult:
            """Compose the app layout."""
            yield Header()
            
            with TabbedContent():
                with TabPane("Topics", id="tab-topics"):
                    yield TopicBrowser()
                
                with TabPane("Tickets", id="tab-tickets"):
                    yield Static(
                        "Ticket board coming soon!\n\n"
                        "Use the Topics tab to browse knowledge base.",
                        id="placeholder"
                    )
            
            yield Footer()
        
        def action_refresh(self) -> None:
            """Refresh the current view."""
            topic_browser = self.query_one(TopicBrowser)
            topic_browser.load_topics()
    
    app = TicketflowApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
