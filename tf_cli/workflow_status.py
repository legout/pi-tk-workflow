"""Workflow status utility - quick overview of IRF workflow state."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional

# Import from ticket_loader to avoid duplication
from tf_cli.ticket_loader import TicketLoader

logger = logging.getLogger(__name__)


class WorkflowStats(NamedTuple):
    """Statistics about the current workflow state."""
    open_tickets: int
    ready_tickets: int
    in_progress: int
    total_closed: int
    has_ralph: bool
    knowledge_entries: int


@dataclass
class WorkflowStatus:
    """Complete workflow status report."""
    stats: WorkflowStats
    project_root: Path
    config_exists: bool


def count_tickets_by_status(tickets_dir: Path) -> dict[str, int]:
    """Count tickets by their status using TicketLoader."""
    counts = {"open": 0, "ready": 0, "in_progress": 0, "closed": 0}
    
    if not tickets_dir.exists():
        return counts
    
    try:
        loader = TicketLoader(tickets_dir)
        loader.load_all()
        status_counts = loader.count_by_status
        
        # Map loader counts to our expected keys
        for status, count in status_counts.items():
            if status in counts:
                counts[status] = count
        
        # Count ready tickets (open with no deps)
        for ticket in loader._tickets:
            if ticket.status == "open" and len(ticket.deps) == 0:
                counts["ready"] += 1
                
    except Exception as e:
        logger.warning(f"Could not load tickets: {e}")
    
    return counts


def get_knowledge_entries(knowledge_dir: Path) -> int:
    """Count knowledge base entries (actual .md files, not directories)."""
    if not knowledge_dir.exists():
        return 0
    
    entries = 0
    for subdir in ["topics", "spikes", "tickets"]:
        subpath = knowledge_dir / subdir
        if subpath.exists():
            # Count actual markdown files, not directories
            entries += len(list(subpath.rglob("*.md")))
    
    return entries


def _resolve_project_root(cwd: Path | None = None) -> Path:
    """Find project root by looking for .tf directory.
    
    Uses the same pattern as TicketLoader._resolve_tickets_dir().
    """
    cwd = cwd or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return cwd


def get_workflow_status(project_root: Path | str | None = None) -> WorkflowStatus:
    """Get complete workflow status for the project."""
    if project_root is None:
        project_root = _resolve_project_root()
    
    project_root = Path(project_root)
    tf_dir = project_root / ".tf"
    # Tickets are in .tickets/ at project root, not .tf/tickets/
    tickets_dir = project_root / ".tickets"
    knowledge_dir = tf_dir / "knowledge"
    ralph_dir = tf_dir / "ralph"
    
    ticket_counts = count_tickets_by_status(tickets_dir)
    
    stats = WorkflowStats(
        open_tickets=ticket_counts["open"],
        ready_tickets=ticket_counts["ready"],
        in_progress=ticket_counts["in_progress"],
        total_closed=ticket_counts["closed"],
        has_ralph=ralph_dir.exists(),
        knowledge_entries=get_knowledge_entries(knowledge_dir),
    )
    
    return WorkflowStatus(
        stats=stats,
        project_root=project_root,
        config_exists=(tf_dir / "config" / "settings.json").exists(),
    )


def print_status(status: WorkflowStatus | None = None) -> None:
    """Print formatted workflow status to stdout."""
    if status is None:
        status = get_workflow_status()
    
    print("\n🔧 TF Workflow Status")
    print("=" * 40)
    print(f"📁 Project: {status.project_root}")
    print(f"⚙️  Config: {'✅' if status.config_exists else '❌'}")
    print()
    print("📊 Tickets")
    print(f"   Open:       {status.stats.open_tickets}")
    print(f"   Ready:      {status.stats.ready_tickets}")
    print(f"   In Progress:{status.stats.in_progress}")
    print(f"   Closed:     {status.stats.total_closed}")
    print()
    print("📚 Knowledge Base")
    print(f"   Entries:    {status.stats.knowledge_entries}")
    print()
    print("🤖 Ralph Loop")
    print(f"   Status:     {'✅ Active' if status.stats.has_ralph else '❌ Not configured'}")
    print("=" * 40)


if __name__ == "__main__":
    print_status()
