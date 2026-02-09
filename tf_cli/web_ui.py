"""Sanic + Datastar Web Application for Ticketflow.

Provides a web-native kanban board using Sanic (backend) and Datastar (frontend hypermedia).

Dependencies:
    - datastar-py>=0.7.0,<0.8.0: Python SDK for Datastar SSE responses. Pinned to match the
      Datastar JS bundle version (v1.0.0-RC.7) loaded from CDN in templates/base.html.
      Version 0.7.0 is used because 0.8.0 requires Python >=3.10 while this project
      supports Python >=3.9. Both 0.7.0 and 0.8.0 are compatible with Datastar JS v1.0.0-RC.7.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sanic import Sanic, response
from jinja2 import Environment, FileSystemLoader

from tf_cli.board_classifier import BoardClassifier, BoardColumn
from tf_cli.ticket_loader import TicketLoader
from tf_cli.ui import TopicIndexLoader, TopicIndexLoadError


def _find_repo_root() -> Path | None:
    """Find the repository root by looking for .tf directory."""
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        tf_dir = parent / ".tf"
        if tf_dir.is_dir():
            return parent
    return None


# Get templates directory (relative to this file)
_TEMPLATES_DIR = Path(__file__).parent / "templates"

app = Sanic("TicketflowWeb")

# Jinja2 templates with autoescape enabled for security
env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=True
)


def get_board_data():
    """Load and classify tickets for the kanban board.
    
    Returns:
        BoardView | None: The classified board view, or None if an error occurred.
        Note: An empty BoardView (0 tickets) is valid and truthy.
    """
    try:
        classifier = BoardClassifier()
        board_view = classifier.classify_all()
        return board_view
    except Exception as e:
        print(f"Error loading tickets: {e}", file=sys.stderr)
        return None


def _build_columns_data(board_view):
    """Build columns data dictionary from BoardView.
    
    Args:
        board_view: The BoardView containing classified tickets
        
    Returns:
        dict: Columns data with ready, blocked, in_progress, closed lists
    """
    columns = {
        "ready": [],
        "blocked": [],
        "in_progress": [],
        "closed": []
    }
    
    for column in BoardColumn:
        tickets = board_view.get_by_column(column)
        for ct in tickets:
            columns[column.value].append(_ticket_to_dict(ct))
    
    return columns


def _ticket_to_dict(ct):
    """Convert ClassifiedTicket to dict for templates."""
    return {
        "id": ct.id,
        "title": ct.title,
        "status": ct.ticket.status,
        "priority": ct.ticket.priority,
        "assignee": ct.ticket.assignee,
        "tags": ct.ticket.tags,
        "blocking_deps": ct.blocking_deps,
    }


def _topic_to_dict(topic):
    """Convert Topic to dict for templates."""
    return {
        "id": topic.id,
        "title": topic.title,
        "topic_type": topic.topic_type,
        "keywords": topic.keywords,
        "has_overview": topic.overview is not None and topic.overview.exists,
        "has_sources": topic.sources is not None and topic.sources.exists,
        "has_plan": topic.plan is not None and topic.plan.exists,
        "has_backlog": topic.backlog is not None and topic.backlog.exists,
        "available_docs": list(topic.available_docs.keys()),
    }


def get_topics_data(search_query: str = ""):
    """Load topics for the topic browser.
    
    Args:
        search_query: Optional search query to filter topics
        
    Returns:
        tuple: (topics_by_type dict, total_count) or (None, 0) on error
    """
    # Sanitize search query: trim and limit length
    search_query = search_query.strip()[:100] if search_query else ""
    
    try:
        loader = TopicIndexLoader()
        loader.load()
        
        # Search if query provided
        if search_query:
            topics = loader.search(search_query)
        else:
            topics = loader.get_all()
        
        # Group by type
        topics_by_type = {
            "seed": [],
            "plan": [],
            "spike": [],
            "baseline": [],
            "unknown": [],
        }
        
        for topic in topics:
            topics_by_type[topic.topic_type].append(_topic_to_dict(topic))
        
        # Sort each group by title
        for topic_type in topics_by_type:
            topics_by_type[topic_type].sort(key=lambda t: t["title"].lower())
        
        return topics_by_type, len(topics)
    except TopicIndexLoadError as e:
        print(f"Error loading topics: {e}", file=sys.stderr)
        return None, 0
    except Exception as e:
        print(f"Unexpected error loading topics: {e}", file=sys.stderr)
        return None, 0


@app.get("/")
async def index(request):
    """Main kanban board page."""
    board_view = get_board_data()
    
    # Check for None explicitly - empty BoardView is valid (0 tickets)
    if board_view is None:
        return response.html("<h1>Error loading tickets</h1>", status=500)
    
    columns = _build_columns_data(board_view)
    
    template = env.get_template("index.html")
    rendered = template.render(
        columns=columns,
        counts=board_view.counts,
    )
    return response.html(rendered)


@app.get("/ticket/<ticket_id>")
async def ticket_detail(request, ticket_id: str):
    """Individual ticket detail page."""
    try:
        loader = TicketLoader()
        tickets = loader.load_all()
        
        ticket_map = {t.id: t for t in tickets}
        ticket = ticket_map.get(ticket_id)
        
        if not ticket:
            return response.html(f"<h1>Ticket {ticket_id} not found</h1>", status=404)
        
        template = env.get_template("ticket.html")
        rendered = template.render(
            ticket={
                "id": ticket.id,
                "title": ticket.title,
                "status": ticket.status,
                "priority": ticket.priority,
                "assignee": ticket.assignee,
                "tags": ticket.tags,
                "deps": ticket.deps,
                "links": ticket.links,
                "external_ref": ticket.external_ref,
                "body": ticket.body,
                "created": ticket.created,
            }
        )
        return response.html(rendered)
    except Exception as e:
        return response.html(f"<h1>Error rendering ticket: {e}</h1>", status=500)


@app.get("/api/refresh")
async def refresh_board(request):
    """Datastar endpoint to refresh the kanban board.
    
    Returns HTML fragment that Datastar will morph into the DOM.
    Includes both the board header (with counts) and the board grid
    to keep stats synchronized.
    """
    board_view = get_board_data()
    
    # Check for None explicitly - empty BoardView is valid
    if board_view is None:
        return response.html("<p class='error'>Error loading tickets</p>")
    
    columns = _build_columns_data(board_view)
    
    template = env.get_template("_board.html")
    rendered = template.render(
        columns=columns,
        counts=board_view.counts,
    )
    return response.html(rendered)


@app.get("/topics")
async def topics_browser(request):
    """Topic browser page for navigating knowledge base topics."""
    search_query = request.args.get("search", [""])[0]
    topics_by_type, total_count = get_topics_data(search_query)
    
    if topics_by_type is None:
        return response.html("<h1>Error loading topics</h1>", status=500)
    
    template = env.get_template("topics.html")
    rendered = template.render(
        topics_by_type=topics_by_type,
        total_count=total_count,
        search_query=search_query,
    )
    return response.html(rendered)


@app.get("/api/topics")
async def api_topics(request):
    """Datastar endpoint for topic search/filter.
    
    Returns HTML fragment with filtered topic list.
    """
    search_query = request.args.get("search", [""])[0]
    topics_by_type, total_count = get_topics_data(search_query)
    
    if topics_by_type is None:
        return response.html("<p class='error'>Error loading topics</p>")
    
    template = env.get_template("_topics_list.html")
    rendered = template.render(
        topics_by_type=topics_by_type,
        total_count=total_count,
        search_query=search_query,
    )
    return response.html(rendered)


@app.get("/topic/<topic_id>")
async def topic_detail(request, topic_id: str):
    """Individual topic detail page."""
    try:
        loader = TopicIndexLoader()
        loader.load()
        
        topic = loader.get_by_id(topic_id)
        
        if not topic:
            return response.html(f"<h1>Topic {topic_id} not found</h1>", status=404)
        
        template = env.get_template("topic_detail.html")
        rendered = template.render(
            topic=_topic_to_dict(topic),
            topic_obj=topic,  # Pass original topic object for doc paths
        )
        return response.html(rendered)
    except Exception as e:
        return response.html(f"<h1>Error rendering topic: {e}</h1>", status=500)


def run_web_server(host: str = "127.0.0.1", port: int = 8000) -> int:
    """Run the Sanic web server.
    
    Args:
        host: Host to bind to (default: 127.0.0.1 for security)
        port: Port to listen on (default: 8000)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Sanic handles Ctrl+C gracefully by default
    try:
        print(f"Starting Ticketflow Web UI on http://{host}:{port}", file=sys.stderr)
        print("Press Ctrl+C to stop the server", file=sys.stderr)
        print(f"Datastar version: v1.0.0-RC.7", file=sys.stderr)
        
        app.run(
            host=host,
            port=port,
            access_log=True,  # Enable access logging
            single_process=True,  # Single process to avoid worker issues
        )
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped", file=sys.stderr)
        return 0
    except OSError as e:
        if e.errno == 98 or e.errno == 48:  # Address already in use (Linux/Mac)
            print(f"Error: Port {port} is already in use", file=sys.stderr)
            print(f"Try using a different port with --port", file=sys.stderr)
        else:
            print(f"Error starting server: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
