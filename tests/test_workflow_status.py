"""Tests for workflow_status module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tf_cli.workflow_status import (
    WorkflowStats,
    WorkflowStatus,
    count_tickets_by_status,
    get_knowledge_entries,
    get_workflow_status,
    _resolve_project_root,
)


class TestResolveProjectRoot:
    """Tests for _resolve_project_root function."""

    def test_finds_tf_directory(self, tmp_path: Path):
        """Should find project root when .tf directory exists."""
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        
        result = _resolve_project_root(tmp_path)
        
        assert result == tmp_path

    def test_falls_back_to_cwd(self, tmp_path: Path):
        """Should fall back to cwd when no .tf directory found."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        result = _resolve_project_root(subdir)
        
        assert result == subdir

    def test_searches_parents(self, tmp_path: Path):
        """Should search parent directories for .tf."""
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        
        result = _resolve_project_root(subdir)
        
        assert result == tmp_path


class TestCountTicketsByStatus:
    """Tests for count_tickets_by_status function."""

    def test_empty_directory(self, tmp_path: Path):
        """Should return zero counts for empty directory."""
        result = count_tickets_by_status(tmp_path)
        
        assert result == {"open": 0, "ready": 0, "in_progress": 0, "closed": 0}

    def test_nonexistent_directory(self, tmp_path: Path):
        """Should return zero counts for nonexistent directory."""
        result = count_tickets_by_status(tmp_path / "nonexistent")
        
        assert result == {"open": 0, "ready": 0, "in_progress": 0, "closed": 0}

    def test_counts_open_ticket(self, tmp_path: Path):
        """Should count an open ticket."""
        ticket_file = tmp_path / "test-123.md"
        ticket_file.write_text("""---
id: test-123
status: open
deps: []
---
# Test Ticket
""")
        
        result = count_tickets_by_status(tmp_path)
        
        assert result["open"] == 1
        assert result["ready"] == 1  # open with no deps = ready

    def test_counts_closed_ticket(self, tmp_path: Path):
        """Should count a closed ticket."""
        ticket_file = tmp_path / "test-456.md"
        ticket_file.write_text("""---
id: test-456
status: closed
deps: []
---
# Closed Ticket
""")
        
        result = count_tickets_by_status(tmp_path)
        
        assert result["closed"] == 1

    def test_not_ready_with_deps(self, tmp_path: Path):
        """Should not count ticket as ready if it has deps."""
        ticket_file = tmp_path / "test-789.md"
        ticket_file.write_text("""---
id: test-789
status: open
deps: [test-123]
---
# Ticket With Deps
""")
        
        result = count_tickets_by_status(tmp_path)
        
        assert result["open"] == 1
        assert result["ready"] == 0  # has deps, not ready


class TestGetKnowledgeEntries:
    """Tests for get_knowledge_entries function."""

    def test_empty_directory(self, tmp_path: Path):
        """Should return 0 for empty directory."""
        result = get_knowledge_entries(tmp_path)
        
        assert result == 0

    def test_counts_markdown_files(self, tmp_path: Path):
        """Should count markdown files in subdirectories."""
        topics_dir = tmp_path / "topics"
        topics_dir.mkdir()
        (topics_dir / "test.md").write_text("# Test")
        (topics_dir / "test2.md").write_text("# Test 2")
        
        result = get_knowledge_entries(tmp_path)
        
        assert result == 2

    def test_ignores_directories(self, tmp_path: Path):
        """Should not count directories, only .md files."""
        topics_dir = tmp_path / "topics"
        topics_dir.mkdir()
        (topics_dir / "test.md").write_text("# Test")
        (topics_dir / "subdir").mkdir()  # Directory, not a file
        
        result = get_knowledge_entries(tmp_path)
        
        assert result == 1

    def test_searches_all_subdirs(self, tmp_path: Path):
        """Should search topics, spikes, and tickets subdirectories."""
        for subdir in ["topics", "spikes", "tickets"]:
            d = tmp_path / subdir
            d.mkdir()
            (d / "file.md").write_text("# Test")
        
        result = get_knowledge_entries(tmp_path)
        
        assert result == 3


class TestWorkflowStats:
    """Tests for WorkflowStats NamedTuple."""

    def test_creation(self):
        """Should create WorkflowStats with correct fields."""
        stats = WorkflowStats(
            open_tickets=5,
            ready_tickets=2,
            in_progress=1,
            total_closed=10,
            has_ralph=True,
            knowledge_entries=100,
        )
        
        assert stats.open_tickets == 5
        assert stats.ready_tickets == 2
        assert stats.in_progress == 1
        assert stats.total_closed == 10
        assert stats.has_ralph is True
        assert stats.knowledge_entries == 100


class TestWorkflowStatus:
    """Tests for WorkflowStatus dataclass."""

    def test_creation(self, tmp_path: Path):
        """Should create WorkflowStatus with correct fields."""
        stats = WorkflowStats(
            open_tickets=1,
            ready_tickets=0,
            in_progress=0,
            total_closed=5,
            has_ralph=False,
            knowledge_entries=10,
        )
        status = WorkflowStatus(
            stats=stats,
            project_root=tmp_path,
            config_exists=True,
        )
        
        assert status.stats == stats
        assert status.project_root == tmp_path
        assert status.config_exists is True
