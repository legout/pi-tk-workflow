"""Unit tests for board classification logic.

Tests the Ready/Blocked/In Progress/Closed classification rules
with various ticket dependency graphs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tf.board_classifier import (
    BoardClassifier,
    BoardColumn,
    BoardView,
    ClassifiedTicket,
    classify_tickets,
)
from tf.ticket_loader import Ticket


def create_ticket(
    ticket_id: str,
    status: str,
    title: str = "",
    deps: list[str] | None = None,
    tags: list[str] | None = None,
    assignee: str | None = None,
    priority: int | None = None,
) -> Ticket:
    """Helper to create a Ticket for testing."""
    return Ticket(
        id=ticket_id,
        status=status,
        title=title or f"Test ticket {ticket_id}",
        file_path=Path(f"{ticket_id}.md"),
        deps=deps or [],
        tags=tags or [],
        assignee=assignee,
        priority=priority,
    )


class TestColumnClassificationRules:
    """Test the core classification rules."""

    def test_closed_status_goes_to_closed_column(self):
        """Closed tickets go to Closed column regardless of deps."""
        tickets = [
            create_ticket("t-1", "closed", deps=["t-2", "t-3"]),
            create_ticket("t-2", "closed"),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.CLOSED
        assert board.get_by_id("t-1").is_closed()

    def test_in_progress_status_goes_to_in_progress_column(self):
        """In Progress tickets with no blocking deps go to In Progress column."""
        tickets = [
            create_ticket("t-1", "in_progress"),
            create_ticket("t-2", "in_progress"),  # No deps - not blocked
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.IN_PROGRESS
        assert board.get_by_id("t-1").is_in_progress()
        assert board.get_by_id("t-2").column == BoardColumn.IN_PROGRESS

    def test_open_with_no_deps_is_ready(self):
        """Open ticket with no dependencies is Ready."""
        tickets = [
            create_ticket("t-1", "open"),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.READY
        assert board.get_by_id("t-1").is_ready()

    def test_open_with_all_closed_deps_is_ready(self):
        """Open ticket with all closed dependencies is Ready."""
        tickets = [
            create_ticket("t-1", "closed"),
            create_ticket("t-2", "closed"),
            create_ticket("t-3", "open", deps=["t-1", "t-2"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-3").column == BoardColumn.READY
        assert board.get_by_id("t-3").blocking_deps == []

    def test_open_with_open_dep_is_blocked(self):
        """Open ticket with open dependency is Blocked."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "open", deps=["t-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-2").column == BoardColumn.BLOCKED
        assert board.get_by_id("t-2").is_blocked()
        assert "t-1" in board.get_by_id("t-2").blocking_deps

    def test_open_with_in_progress_dep_is_blocked(self):
        """Open ticket with in_progress dependency is Blocked."""
        tickets = [
            create_ticket("t-1", "in_progress"),
            create_ticket("t-2", "open", deps=["t-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-2").column == BoardColumn.BLOCKED
        assert "t-1" in board.get_by_id("t-2").blocking_deps

    def test_in_progress_with_open_dep_is_blocked(self):
        """In Progress ticket with open dependency is Blocked."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "in_progress", deps=["t-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-2").column == BoardColumn.BLOCKED

    def test_blocked_ticket_with_multiple_blocking_deps(self):
        """Blocked ticket shows all blocking dependencies."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "in_progress"),
            create_ticket("t-3", "closed"),
            create_ticket("t-4", "open", deps=["t-1", "t-2", "t-3"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-4").column == BoardColumn.BLOCKED
        assert "t-1" in board.get_by_id("t-4").blocking_deps
        assert "t-2" in board.get_by_id("t-4").blocking_deps
        assert "t-3" not in board.get_by_id("t-4").blocking_deps

    def test_missing_dependency_treated_as_blocking(self):
        """Dependency not in ticket list is treated as non-closed (blocking)."""
        tickets = [
            create_ticket("t-1", "open", deps=["missing-ticket"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.BLOCKED
        assert "missing-ticket" in board.get_by_id("t-1").blocking_deps


class TestDependencyGraphScenarios:
    """Test realistic dependency graph scenarios."""

    def test_linear_chain_blocked_to_ready(self):
        """Linear chain: t1 -> t2 -> t3, closing t1 unblocks t2."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "open", deps=["t-1"]),
            create_ticket("t-3", "open", deps=["t-2"]),
        ]
        
        board = classify_tickets(tickets)
        
        # t-1 is READY (no deps, open status), t-2 and t-3 are BLOCKED by upstream deps
        assert board.get_by_id("t-1").column == BoardColumn.READY
        assert board.get_by_id("t-2").column == BoardColumn.BLOCKED
        assert board.get_by_id("t-3").column == BoardColumn.BLOCKED
        
        # Now simulate closing t-1
        tickets[0] = create_ticket("t-1", "closed")
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.CLOSED
        assert board.get_by_id("t-2").column == BoardColumn.READY
        assert board.get_by_id("t-3").column == BoardColumn.BLOCKED

    def test_diamond_dependency_pattern(self):
        """Diamond pattern: root -> left/right -> leaf."""
        tickets = [
            create_ticket("root", "closed"),
            create_ticket("left", "open", deps=["root"]),
            create_ticket("right", "open", deps=["root"]),
            create_ticket("leaf", "open", deps=["left", "right"]),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("root").column == BoardColumn.CLOSED
        assert board.get_by_id("left").column == BoardColumn.READY
        assert board.get_by_id("right").column == BoardColumn.READY
        assert board.get_by_id("leaf").column == BoardColumn.BLOCKED
        assert "left" in board.get_by_id("leaf").blocking_deps
        assert "right" in board.get_by_id("leaf").blocking_deps

    def test_parallel_independent_tasks(self):
        """Multiple independent ready tasks."""
        tickets = [
            create_ticket("task-a", "open"),
            create_ticket("task-b", "open"),
            create_ticket("task-c", "open"),
        ]
        
        board = classify_tickets(tickets)
        
        ready = board.get_ready()
        assert len(ready) == 3

    def test_complex_graph_with_mixed_status(self):
        """Complex graph with tickets in all columns."""
        tickets = [
            # Done
            create_ticket("done-1", "closed"),
            create_ticket("done-2", "closed"),
            # In Progress
            create_ticket("wip-1", "in_progress"),
            create_ticket("wip-2", "in_progress", deps=["done-1"]),
            # Ready (all deps closed)
            create_ticket("ready-1", "open"),
            create_ticket("ready-2", "open", deps=["done-1"]),
            create_ticket("ready-3", "open", deps=["done-1", "done-2"]),
            # Blocked (has open/in_progress deps)
            create_ticket("blocked-1", "open", deps=["wip-1"]),
            create_ticket("blocked-2", "open", deps=["ready-1"]),
            create_ticket("blocked-3", "in_progress", deps=["wip-1", "done-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        # Verify closed
        for tid in ["done-1", "done-2"]:
            assert board.get_by_id(tid).column == BoardColumn.CLOSED
        
        # Verify in progress
        for tid in ["wip-1", "wip-2"]:
            assert board.get_by_id(tid).column == BoardColumn.IN_PROGRESS
        
        # Verify ready
        for tid in ["ready-1", "ready-2", "ready-3"]:
            assert board.get_by_id(tid).column == BoardColumn.READY
        
        # Verify blocked
        for tid in ["blocked-1", "blocked-2", "blocked-3"]:
            assert board.get_by_id(tid).column == BoardColumn.BLOCKED


class TestBoardViewOperations:
    """Test BoardView query and filter operations."""

    def test_get_by_column(self):
        """BoardView.get_by_column returns tickets in that column."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "closed"),
            create_ticket("t-3", "open"),
        ]
        
        board = classify_tickets(tickets)
        
        ready = board.get_by_column(BoardColumn.READY)
        assert len(ready) == 2
        assert {t.id for t in ready} == {"t-1", "t-3"}
        
        closed = board.get_by_column(BoardColumn.CLOSED)
        assert len(closed) == 1
        assert closed[0].id == "t-2"

    def test_get_by_id(self):
        """BoardView.get_by_id returns specific ticket."""
        tickets = [
            create_ticket("t-1", "open"),
            create_ticket("t-2", "closed"),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.READY
        assert board.get_by_id("t-2").column == BoardColumn.CLOSED
        assert board.get_by_id("t-missing") is None

    def test_counts_property(self):
        """BoardView.counts returns correct ticket counts."""
        tickets = [
            create_ticket("t-1", "open"),           # ready
            create_ticket("t-2", "open"),           # ready
            create_ticket("t-3", "closed"),         # closed
            create_ticket("t-4", "in_progress"),    # in_progress
            create_ticket("t-5", "open", deps=["t-1"]),  # blocked
        ]
        
        board = classify_tickets(tickets)
        
        assert board.counts == {
            "ready": 2,
            "blocked": 1,
            "in_progress": 1,
            "closed": 1,
        }
        assert board.total == 5

    def test_filter_by_tag(self):
        """BoardView.filter_by_tag returns filtered view."""
        tickets = [
            create_ticket("t-1", "open", tags=["backend", "urgent"]),
            create_ticket("t-2", "open", tags=["frontend"]),
            create_ticket("t-3", "closed", tags=["backend"]),
        ]
        
        board = classify_tickets(tickets)
        backend_board = board.filter_by_tag("backend")
        
        assert backend_board.total == 2
        assert {t.id for t in backend_board.all_tickets} == {"t-1", "t-3"}
        assert backend_board.counts["ready"] == 1
        assert backend_board.counts["closed"] == 1

    def test_filter_by_assignee(self):
        """BoardView.filter_by_assignee returns filtered view."""
        tickets = [
            create_ticket("t-1", "open", assignee="alice"),
            create_ticket("t-2", "open", assignee="bob"),
            create_ticket("t-3", "closed", assignee="alice"),
        ]
        
        board = classify_tickets(tickets)
        alice_board = board.filter_by_assignee("alice")
        
        assert alice_board.total == 2
        assert {t.id for t in alice_board.all_tickets} == {"t-1", "t-3"}

    def test_search_by_title(self):
        """BoardView.search finds tickets by title."""
        tickets = [
            create_ticket("t-1", "open", title="Implement authentication"),
            create_ticket("t-2", "open", title="Add login page"),
            create_ticket("t-3", "closed", title="Fix auth bug"),
        ]
        
        board = classify_tickets(tickets)
        auth_board = board.search("auth")
        
        assert auth_board.total == 2
        assert {t.id for t in auth_board.all_tickets} == {"t-1", "t-3"}

    def test_search_by_id(self):
        """BoardView.search finds tickets by ID."""
        tickets = [
            create_ticket("abc-123", "open"),
            create_ticket("abc-456", "open"),
            create_ticket("xyz-789", "closed"),
        ]
        
        board = classify_tickets(tickets)
        abc_board = board.search("abc")
        
        assert abc_board.total == 2
        assert {t.id for t in abc_board.all_tickets} == {"abc-123", "abc-456"}

    def test_search_by_tag(self):
        """BoardView.search finds tickets by tag."""
        tickets = [
            create_ticket("t-1", "open", tags=["backend"]),
            create_ticket("t-2", "open", tags=["backend-api"]),
            create_ticket("t-3", "closed", tags=["frontend"]),
        ]
        
        board = classify_tickets(tickets)
        backend_board = board.search("backend")
        
        assert backend_board.total == 2


class TestSorting:
    """Test ticket sorting within columns."""

    def test_sorting_by_priority_then_id(self):
        """Tickets sorted by priority (desc) then ID (asc)."""
        tickets = [
            create_ticket("c-low", "open", priority=1),
            create_ticket("a-high", "open", priority=3),
            create_ticket("b-med", "open", priority=2),
            create_ticket("d-none", "open", priority=None),
            create_ticket("e-none", "open", priority=None),
        ]
        
        board = classify_tickets(tickets)
        ready = board.get_ready()
        ids = [t.id for t in ready]
        
        # Should be sorted: high (3), med (2), low (1), none (0), none (0)
        # Within same priority, sorted by ID
        assert ids == ["a-high", "b-med", "c-low", "d-none", "e-none"]


class TestClassifiedTicketProperties:
    """Test ClassifiedTicket convenience properties."""

    def test_property_delegation(self):
        """ClassifiedTicket properties delegate to underlying ticket."""
        ticket = create_ticket(
            "t-1",
            "open",
            title="Test Title",
            tags=["tag1", "tag2"],
        )
        
        ct = ClassifiedTicket(ticket, BoardColumn.READY)
        
        assert ct.id == "t-1"
        assert ct.status == "open"
        assert ct.title == "Test Title"
        assert ct.ticket.tags == ["tag1", "tag2"]

    def test_is_column_helpers(self):
        """is_ready(), is_blocked(), etc. work correctly."""
        ticket = create_ticket("t-1", "open")
        
        ready = ClassifiedTicket(ticket, BoardColumn.READY)
        assert ready.is_ready()
        assert not ready.is_blocked()
        assert not ready.is_in_progress()
        assert not ready.is_closed()


class TestBoardClassifier:
    """Test BoardClassifier initialization and loading."""

    def test_classifier_with_custom_loader(self):
        """BoardClassifier works with custom TicketLoader."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tickets_dir = Path(tmpdir)
            
            # Create a test ticket file
            ticket_file = tickets_dir / "test-ticket.md"
            ticket_file.write_text("""---
id: test-ticket
status: open
---
# Test Ticket

Description here.
""")
            
            from tf.ticket_loader import TicketLoader
            loader = TicketLoader(tickets_dir)
            classifier = BoardClassifier(loader=loader)
            board = classifier.classify_all()
            
            assert board.total == 1
            assert board.get_by_id("test-ticket").column == BoardColumn.READY

    def test_classifier_with_tickets_dir(self):
        """BoardClassifier works with explicit tickets_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tickets_dir = Path(tmpdir)
            
            ticket_file = tickets_dir / "abc-123.md"
            ticket_file.write_text("""---
id: abc-123
status: closed
---
# Done Ticket
""")
            
            classifier = BoardClassifier(tickets_dir=tickets_dir)
            board = classifier.classify_all()
            
            assert board.total == 1
            assert board.get_by_id("abc-123").column == BoardColumn.CLOSED


class TestCaseInsensitiveStatus:
    """Test case-insensitive status handling."""

    def test_status_case_insensitivity(self):
        """Status comparison is case-insensitive."""
        tickets = [
            create_ticket("t-1", "CLOSED"),
            create_ticket("t-2", "Closed"),
            create_ticket("t-3", "In_Progress"),
            create_ticket("t-4", "IN_PROGRESS"),
            create_ticket("t-5", "Open"),
            create_ticket("t-6", "OPEN"),
        ]
        
        board = classify_tickets(tickets)
        
        assert board.get_by_id("t-1").column == BoardColumn.CLOSED
        assert board.get_by_id("t-2").column == BoardColumn.CLOSED
        assert board.get_by_id("t-3").column == BoardColumn.IN_PROGRESS
        assert board.get_by_id("t-4").column == BoardColumn.IN_PROGRESS
        assert board.get_by_id("t-5").column == BoardColumn.READY
        assert board.get_by_id("t-6").column == BoardColumn.READY


class TestEmptyAndEdgeCases:
    """Test edge cases and empty inputs."""

    def test_empty_ticket_list(self):
        """Empty ticket list returns empty board."""
        board = classify_tickets([])
        
        assert board.total == 0
        assert board.counts == {
            "ready": 0,
            "blocked": 0,
            "in_progress": 0,
            "closed": 0,
        }

    def test_unknown_status_treated_as_ready(self):
        """Unknown status defaults to Ready (no deps assumed)."""
        tickets = [
            create_ticket("t-1", "unknown_status"),
        ]
        
        board = classify_tickets(tickets)
        
        # Unknown status falls through to default case -> READY
        assert board.get_by_id("t-1").column == BoardColumn.READY

    def test_self_referential_dependency(self):
        """Ticket depending on itself is blocked."""
        tickets = [
            create_ticket("t-1", "open", deps=["t-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        # t-1 is not closed, so it blocks itself
        assert board.get_by_id("t-1").column == BoardColumn.BLOCKED
        assert "t-1" in board.get_by_id("t-1").blocking_deps

    def test_circular_dependencies(self):
        """Circular dependencies are handled."""
        tickets = [
            create_ticket("t-1", "open", deps=["t-2"]),
            create_ticket("t-2", "open", deps=["t-1"]),
        ]
        
        board = classify_tickets(tickets)
        
        # Both block each other
        assert board.get_by_id("t-1").column == BoardColumn.BLOCKED
        assert board.get_by_id("t-2").column == BoardColumn.BLOCKED
        assert "t-2" in board.get_by_id("t-1").blocking_deps
        assert "t-1" in board.get_by_id("t-2").blocking_deps