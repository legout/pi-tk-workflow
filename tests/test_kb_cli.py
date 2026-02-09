"""Unit tests for kb_cli module.

Tests:
- cmd_ls: List topics with filtering and output formats
- cmd_show: Show topic details
- cmd_archive: Archive topics (idempotent)
- cmd_restore: Restore archived topics (idempotent)
- cmd_delete: Delete topics permanently
- cmd_validate: Validate KB integrity
- cmd_index_status: Show index statistics
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from tf.kb_cli import (
    cmd_ls,
    cmd_show,
    cmd_archive,
    cmd_restore,
    cmd_delete,
    cmd_validate,
    cmd_index_status,
)
from tf.kb_helpers import atomic_write_index, atomic_read_index


@pytest.fixture
def temp_kb_dir() -> Generator[Path, None, None]:
    """Create a temporary knowledge directory."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_kb(temp_kb_dir: Path) -> Path:
    """Create a sample knowledge base with topics."""
    # Create index.json
    index_data = {
        "topics": [
            {
                "id": "seed-test-topic",
                "title": "Test Seed Topic",
                "overview": "topics/seed-test-topic/overview.md",
                "sources": "topics/seed-test-topic/sources.md",
            },
            {
                "id": "plan-test-plan",
                "title": "Test Plan",
                "plan": "topics/plan-test-plan/plan.md",
            },
            {
                "id": "spike-test-spike",
                "title": "Test Spike",
            },
        ]
    }
    atomic_write_index(temp_kb_dir, index_data)
    
    # Create topic directories and files
    seed_dir = temp_kb_dir / "topics" / "seed-test-topic"
    seed_dir.mkdir(parents=True)
    (seed_dir / "overview.md").write_text("# Test Seed Topic\n\nOverview content.")
    (seed_dir / "sources.md").write_text("# Sources\n\nSome sources.")
    
    plan_dir = temp_kb_dir / "topics" / "plan-test-plan"
    plan_dir.mkdir(parents=True)
    (plan_dir / "plan.md").write_text("# Test Plan\n\nPlan content.")
    
    spike_dir = temp_kb_dir / "topics" / "spike-test-spike"
    spike_dir.mkdir(parents=True)
    (spike_dir / "overview.md").write_text("# Test Spike")
    
    return temp_kb_dir


class TestCmdLs:
    """Tests for cmd_ls function."""
    
    def test_list_all_topics(self, sample_kb: Path, capsys) -> None:
        """List all topics in human-readable format."""
        result = cmd_ls(sample_kb, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "seed-test-topic" in captured.out
        assert "plan-test-plan" in captured.out
        assert "spike-test-spike" in captured.out
        assert "Test Seed Topic" in captured.out
    
    def test_list_json_format(self, sample_kb: Path, capsys) -> None:
        """List topics in JSON format."""
        result = cmd_ls(sample_kb, format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert "topics" in data
        assert len(data["topics"]) == 3
        
        topic_ids = [t["id"] for t in data["topics"]]
        assert "seed-test-topic" in topic_ids
        assert "plan-test-plan" in topic_ids
    
    def test_filter_by_type(self, sample_kb: Path, capsys) -> None:
        """Filter topics by type."""
        result = cmd_ls(sample_kb, format_json=False, topic_type="seed")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "seed-test-topic" in captured.out
        assert "plan-test-plan" not in captured.out
        assert "spike-test-spike" not in captured.out
    
    def test_include_archived(self, sample_kb: Path, capsys) -> None:
        """Include archived topics in listing."""
        # Create an archived topic
        archive_dir = sample_kb / "archive" / "topics" / "archived-topic"
        archive_dir.mkdir(parents=True)
        (archive_dir / "overview.md").write_text("# Archived")
        
        result = cmd_ls(sample_kb, format_json=False, include_archived=True)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "archived-topic" in captured.out
        assert "ARCHIVED" in captured.out
    
    def test_empty_kb(self, temp_kb_dir: Path, capsys) -> None:
        """Handle empty knowledge base."""
        result = cmd_ls(temp_kb_dir, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "No knowledge base index found" in captured.out
    
    def test_empty_kb_json(self, temp_kb_dir: Path, capsys) -> None:
        """Handle empty KB in JSON format."""
        result = cmd_ls(temp_kb_dir, format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["topics"] == []


class TestCmdShow:
    """Tests for cmd_show function."""
    
    def test_show_active_topic(self, sample_kb: Path, capsys) -> None:
        """Show details for an active topic."""
        result = cmd_show(sample_kb, "seed-test-topic", format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "ID: seed-test-topic" in captured.out
        assert "Type: seed" in captured.out
        assert "Test Seed Topic" in captured.out
        assert "Status: active" in captured.out
    
    def test_show_topic_json(self, sample_kb: Path, capsys) -> None:
        """Show topic in JSON format."""
        result = cmd_show(sample_kb, "plan-test-plan", format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert data["id"] == "plan-test-plan"
        assert data["type"] == "plan"
        assert "docs" in data
    
    def test_show_archived_topic(self, sample_kb: Path, capsys) -> None:
        """Show archived topic details."""
        # Archive a topic first
        cmd_archive(sample_kb, "seed-test-topic")
        
        result = cmd_show(sample_kb, "seed-test-topic", format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Status: ARCHIVED" in captured.out
    
    def test_show_nonexistent_topic(self, sample_kb: Path, capsys) -> None:
        """Handle non-existent topic."""
        result = cmd_show(sample_kb, "nonexistent-topic", format_json=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCmdArchive:
    """Tests for cmd_archive function."""
    
    def test_archive_active_topic(self, sample_kb: Path, capsys) -> None:
        """Archive an active topic."""
        result = cmd_archive(sample_kb, "spike-test-spike", reason="No longer needed")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Archived" in captured.out
        
        # Verify topic moved to archive
        archive_dir = sample_kb / "archive" / "topics" / "spike-test-spike"
        assert archive_dir.exists()
        
        # Verify removed from active
        active_dir = sample_kb / "topics" / "spike-test-spike"
        assert not active_dir.exists()
        
        # Verify archive.md created
        assert (archive_dir / "archive.md").exists()
    
    def test_archive_idempotent(self, sample_kb: Path, capsys) -> None:
        """Archiving already archived topic is idempotent."""
        # Archive first time
        cmd_archive(sample_kb, "spike-test-spike")
        
        # Archive second time
        result = cmd_archive(sample_kb, "spike-test-spike")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "already archived" in captured.out
    
    def test_archive_removes_from_index(self, sample_kb: Path) -> None:
        """Archived topic is removed from index.json."""
        cmd_archive(sample_kb, "spike-test-spike")
        
        data = atomic_read_index(sample_kb)
        topic_ids = [t["id"] for t in data.get("topics", [])]
        
        assert "spike-test-spike" not in topic_ids
        assert "seed-test-topic" in topic_ids  # Others remain
    
    def test_archive_nonexistent_topic(self, sample_kb: Path, capsys) -> None:
        """Handle archiving non-existent topic."""
        result = cmd_archive(sample_kb, "nonexistent-topic")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCmdRestore:
    """Tests for cmd_restore function."""
    
    def test_restore_archived_topic(self, sample_kb: Path, capsys) -> None:
        """Restore an archived topic."""
        # Archive first
        cmd_archive(sample_kb, "spike-test-spike")
        
        # Restore
        result = cmd_restore(sample_kb, "spike-test-spike")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Restored" in captured.out
        
        # Verify topic moved back to active
        active_dir = sample_kb / "topics" / "spike-test-spike"
        assert active_dir.exists()
        
        # Verify removed from archive
        archive_dir = sample_kb / "archive" / "topics" / "spike-test-spike"
        assert not archive_dir.exists()
    
    def test_restore_idempotent(self, sample_kb: Path, capsys) -> None:
        """Restoring active topic is idempotent."""
        result = cmd_restore(sample_kb, "seed-test-topic")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "already active" in captured.out
    
    def test_restore_adds_to_index(self, sample_kb: Path) -> None:
        """Restored topic is added back to index.json."""
        # Archive first
        cmd_archive(sample_kb, "spike-test-spike")
        
        # Verify not in index
        data = atomic_read_index(sample_kb)
        topic_ids = [t["id"] for t in data.get("topics", [])]
        assert "spike-test-spike" not in topic_ids
        
        # Restore
        cmd_restore(sample_kb, "spike-test-spike")
        
        # Verify back in index
        data = atomic_read_index(sample_kb)
        topic_ids = [t["id"] for t in data.get("topics", [])]
        assert "spike-test-spike" in topic_ids
    
    def test_restore_nonexistent_topic(self, sample_kb: Path, capsys) -> None:
        """Handle restoring non-existent topic."""
        result = cmd_restore(sample_kb, "nonexistent-topic")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found in archive" in captured.err


class TestCmdDelete:
    """Tests for cmd_delete function."""
    
    def test_delete_active_topic(self, sample_kb: Path, capsys) -> None:
        """Delete an active topic."""
        result = cmd_delete(sample_kb, "spike-test-spike")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Deleted" in captured.out
        
        # Verify directory removed
        topic_dir = sample_kb / "topics" / "spike-test-spike"
        assert not topic_dir.exists()
    
    def test_delete_archived_topic(self, sample_kb: Path, capsys) -> None:
        """Delete an archived topic."""
        # Archive first
        cmd_archive(sample_kb, "spike-test-spike")
        
        # Delete
        result = cmd_delete(sample_kb, "spike-test-spike")
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Deleted" in captured.out
        
        # Verify removed from archive
        archive_dir = sample_kb / "archive" / "topics" / "spike-test-spike"
        assert not archive_dir.exists()
    
    def test_delete_removes_from_index(self, sample_kb: Path) -> None:
        """Deleted topic is removed from index.json."""
        cmd_delete(sample_kb, "spike-test-spike")
        
        data = atomic_read_index(sample_kb)
        topic_ids = [t["id"] for t in data.get("topics", [])]
        
        assert "spike-test-spike" not in topic_ids
    
    def test_delete_nonexistent_topic(self, sample_kb: Path, capsys) -> None:
        """Handle deleting non-existent topic."""
        result = cmd_delete(sample_kb, "nonexistent-topic")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCmdValidate:
    """Tests for cmd_validate function."""
    
    def test_valid_kb(self, sample_kb: Path, capsys) -> None:
        """Validate a valid knowledge base."""
        result = cmd_validate(sample_kb, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "PASSED" in captured.out
        assert "No issues found" in captured.out
    
    def test_missing_files(self, sample_kb: Path, capsys) -> None:
        """Detect missing files referenced in index."""
        # Create a topic with non-existent file reference
        data = atomic_read_index(sample_kb)
        data["topics"].append({
            "id": "broken-topic",
            "title": "Broken Topic",
            "overview": "topics/broken-topic/overview.md",  # File doesn't exist
        })
        atomic_write_index(sample_kb, data)
        
        result = cmd_validate(sample_kb, format_json=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "FAILED" in captured.out
        assert "Missing file" in captured.out
    
    def test_orphan_directories(self, sample_kb: Path, capsys) -> None:
        """Detect orphan directories not in index."""
        # Create directory not in index
        orphan_dir = sample_kb / "topics" / "orphan-topic"
        orphan_dir.mkdir(parents=True)
        (orphan_dir / "overview.md").write_text("# Orphan")
        
        result = cmd_validate(sample_kb, format_json=False)
        
        assert result == 0  # Warnings don't fail
        captured = capsys.readouterr()
        assert "Orphan directory" in captured.out
    
    def test_duplicate_ids(self, sample_kb: Path, capsys) -> None:
        """Detect duplicate topic IDs."""
        data = atomic_read_index(sample_kb)
        # Add duplicate
        data["topics"].append({
            "id": "seed-test-topic",  # Duplicate
            "title": "Duplicate",
        })
        atomic_write_index(sample_kb, data)
        
        result = cmd_validate(sample_kb, format_json=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Duplicate topic ID" in captured.out
    
    def test_validate_json_output(self, sample_kb: Path, capsys) -> None:
        """Validate with JSON output."""
        result = cmd_validate(sample_kb, format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert "valid" in data
        assert data["valid"] is True
        assert "errors" in data
        assert "warnings" in data
    
    def test_validate_no_index(self, temp_kb_dir: Path, capsys) -> None:
        """Validate when no index exists."""
        result = cmd_validate(temp_kb_dir, format_json=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCmdIndexStatus:
    """Tests for cmd_index_status function."""
    
    def test_index_status_ok(self, sample_kb: Path, capsys) -> None:
        """Show index status for valid KB."""
        result = cmd_index_status(sample_kb, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "OK" in captured.out
        assert "Active topics: 3" in captured.out
    
    def test_index_status_with_archived(self, sample_kb: Path, capsys) -> None:
        """Show index status with archived topics."""
        # Archive a topic
        cmd_archive(sample_kb, "spike-test-spike")
        
        result = cmd_index_status(sample_kb, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Active topics: 2" in captured.out
        assert "Archived topics: 1" in captured.out
    
    def test_index_status_json(self, sample_kb: Path, capsys) -> None:
        """Show index status in JSON format."""
        result = cmd_index_status(sample_kb, format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert data["status"] == "ok"
        assert data["topics"] == 3
    
    def test_index_status_not_found(self, temp_kb_dir: Path, capsys) -> None:
        """Show status when index not found."""
        result = cmd_index_status(temp_kb_dir, format_json=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "NOT FOUND" in captured.out
