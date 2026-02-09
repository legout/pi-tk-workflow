"""Sanic + Datastar Web Application POC for Ticketflow.

This is a proof-of-concept showing a web-native kanban board
using Sanic (backend) and Datastar (frontend hypermedia).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


def _find_repo_root() -> Optional[Path]:
    """Find the repository root by looking for .tf directory."""
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        tf_dir = parent / ".tf"
        if tf_dir.is_dir():
            return parent
    return None


# Add repo root to path for imports
REPO_ROOT = _find_repo_root()
if REPO_ROOT:
    sys.path.insert(0, str(REPO_ROOT))
else:
    REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent

from sanic import Sanic
from sanic.response import html
from jinja2 import Environment, FileSystemLoader
import markdown

from datastar_py.sanic import DatastarResponse
from datastar_py import ServerSentEventGenerator

from tf_cli.board_classifier import BoardClassifier, BoardColumn
from tf_cli.ticket_loader import TicketLoader

app = Sanic("TicketflowWebDatastar")

# Jinja2 templates
env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

# Markdown extensions configuration
MD_EXTENSIONS = ["fenced_code", "tables", "toc"]


def get_board_data():
    """Load and classify tickets for the kanban board."""
    try:
        classifier = BoardClassifier()
        board_view = classifier.classify_all()
        return board_view
    except Exception as e:
        print(f"Error loading tickets: {e}")
        return None


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


@app.get("/")
async def index(request):
    """Main kanban board page."""
    board_view = get_board_data()
    
    if not board_view:
        return html("<h1>Error loading tickets</h1>", status=500)
    
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
    
    template = env.get_template("index.html")
    rendered = template.render(
        columns=columns,
        counts=board_view.counts,
    )
    return html(rendered)


@app.get("/board")
async def board(request):
    """Board page - same as index for Datastar navigation."""
    return await index(request)


@app.get("/ticket/<ticket_id>")
async def ticket_detail(request, ticket_id: str):
    """Individual ticket detail page."""
    try:
        loader = TicketLoader()
        tickets = loader.load_all()

        ticket_map = {t.id: t for t in tickets}
        ticket = ticket_map.get(ticket_id)

        if not ticket:
            return html(f"<h1>Ticket {ticket_id} not found</h1>", status=404)

        # Render markdown body to HTML (new instance per request for thread safety)
        md = markdown.Markdown(extensions=MD_EXTENSIONS)
        body_html = md.convert(ticket.body) if ticket.body else ""

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
                "body_html": body_html,
                "created": ticket.created,
            }
        )
        return html(rendered)
    except Exception as e:
        return html(f"<h1>Error: {e}</h1>", status=500)


@app.get("/api/refresh")
async def refresh_board(request):
    """Datastar endpoint to refresh the kanban board.

    Returns a DatastarResponse with SSE events that patch both the board
    and the stats counters, enabling multi-target updates from one action.
    """
    board_view = get_board_data()

    if not board_view:
        # Return error as SSE event for consistent Datastar handling
        error_event = ServerSentEventGenerator.patch_elements(
            elements="<p class='error'>Error loading tickets</p>",
            selector="#board"
        )
        return DatastarResponse([error_event], status=500)

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

    # Render board fragment
    board_template = env.get_template("_board.html")
    board_html = board_template.render(columns=columns)

    # Render stats fragment
    stats_template = env.get_template("_board_stats.html")
    stats_html = stats_template.render(counts=board_view.counts)

    # Create SSE events for multi-target patching
    board_event = ServerSentEventGenerator.patch_elements(
        elements=board_html,
        selector="#board"
    )
    stats_event = ServerSentEventGenerator.patch_elements(
        elements=stats_html,
        selector="#board-stats"
    )

    return DatastarResponse([board_event, stats_event])


if __name__ == "__main__":
    print("Starting Ticketflow Web POC (Sanic+Datastar) on http://127.0.0.1:8080")
    print("Datastar version: v1.0.0-RC.7")
    app.run(host="127.0.0.1", port=8080, debug=True)
