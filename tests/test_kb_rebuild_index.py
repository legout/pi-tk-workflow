"""Tests for kb_cli rebuild-index command.

Tests:
- cmd_rebuild_index dry-run mode
- cmd_rebuild_index actual write
- Title extraction from frontmatter
- Stable ordering by topic ID
- Metadata preservation
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from tf.kb_cli import cmd_rebuild_index, _extract_title_from_frontmatter
from tf.kb_helpers import atomic_read_index, atomic_write_index


@pytest.fixture
def temp_knowledge_dir() -> Generator[Path, None, None]:
    """Create a temporary knowledge directory structure."""
    with tempfile.TemporaryDirectory() as tmp:
        knowledge_dir = Path(tmp) / ".tf" / "knowledge"
        knowledge_dir.mkdir(parents=True)
        yield knowledge_dir


@pytest.fixture
def sample_topics(temp_knowledge_dir: Path) -> Path:
    """Create sample topic directories with content."""
    topics_dir = temp_knowledge_dir / "topics"
    
    # Topic 1: seed topic with overview
    topic1 = topics_dir / "seed-test-topic"
    topic1.mkdir(parents=True)
    (topic1 / "overview.md").write_text("""---
title: Test Seed Topic
---

# Test Seed Topic

Overview content here.
""")
    (topic1 / "sources.md").write_text("# Sources\n\nSome sources.")
    
    # Topic 2: plan topic with plan.md (alphabetically before seed)
    topic2 = topics_dir / "plan-test-plan"
    topic2.mkdir(parents=True)
    (topic2 / "plan.md").write_text("""---
id: plan-test-plan
status: draft
---

# Plan Test Plan

Plan content.
""")
    (topic2 / "backlog.md").write_text("# Backlog\n\nTasks here.")
    
    # Topic 3: topic without frontmatter (just heading)
    topic3 = topics_dir / "baseline-no-frontmatter"
    topic3.mkdir(parents=True)
    (topic3 / "overview.md").write_text("""# Simple Heading Title

Content without frontmatter.
""")
    
    return temp_knowledge_dir


class TestExtractTitleFromFrontmatter:
    """Test title extraction from frontmatter."""
    
    def test_extracts_title_from_frontmatter_field(self, temp_knowledge_dir: Path) -> None:
        """Extract title from frontmatter title field."""
        topic_dir = temp_knowledge_dir / "topics" / "test"
        topic_dir.mkdir(parents=True)
        (topic_dir / "overview.md").write_text("""---
title: My Special Title
---

# Heading Title

Content.
""")
        
        title = _extract_title_from_frontmatter(topic_dir)
        # Should prefer heading over frontmatter title field
        assert title == "Heading Title"
    
    def test_extracts_title_from_heading(self, temp_knowledge_dir: Path) -> None:
        """Extract title from first # heading."""
        topic_dir = temp_knowledge_dir / "topics" / "test"
        topic_dir.mkdir(parents=True)
        (topic_dir / "overview.md").write_text("""# My Heading Title

Content.
""")
        
        title = _extract_title_from_frontmatter(topic_dir)
        assert title == "My Heading Title"
    
    def test_extracts_title_from_plan_md(self, temp_knowledge_dir: Path) -> None:
        """Fall back to plan.md if no overview.md."""
        topic_dir = temp_knowledge_dir / "topics" / "test"
        topic_dir.mkdir(parents=True)
        (topic_dir / "plan.md").write_text("""# Plan Title

Plan content.
""")
        
        title = _extract_title_from_frontmatter(topic_dir)
        assert title == "Plan Title"
    
    def test_returns_none_when_no_docs(self, temp_knowledge_dir: Path) -> None:
        """Return None when no documentation files exist."""
        topic_dir = temp_knowledge_dir / "topics" / "test"
        topic_dir.mkdir(parents=True)
        
        title = _extract_title_from_frontmatter(topic_dir)
        assert title is None


class TestCmdRebuildIndex:
    """Test rebuild-index command."""
    
    def test_dry_run_shows_no_changes_for_empty_index(self, sample_topics: Path, capsys) -> None:
        """Dry run with empty index shows all topics as added."""
        # Ensure no index exists
        index_path = sample_topics / "index.json"
        if index_path.exists():
            index_path.unlink()
        
        result = cmd_rebuild_index(sample_topics, dry_run=True, format_json=False)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Dry-run: Would rebuild index" in captured.out
        assert "Added (3):" in captured.out
        assert "plan-test-plan" in captured.out
        assert "seed-test-topic" in captured.out
        assert "baseline-no-frontmatter" in captured.out
    
    def test_dry_run_json_output(self, sample_topics: Path, capsys) -> None:
        """JSON output in dry run mode."""
        result = cmd_rebuild_index(sample_topics, dry_run=True, format_json=True)
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert data["dry_run"] is True
        assert "proposed_index" in data
        assert "topics" in data["proposed_index"]
    
    def test_rebuild_creates_index(self, sample_topics: Path) -> None:
        """Rebuild creates index.json with correct structure."""
        # Ensure no index exists
        index_path = sample_topics / "index.json"
        if index_path.exists():
            index_path.unlink()
        
        result = cmd_rebuild_index(sample_topics, dry_run=False)
        
        assert result == 0
        assert index_path.exists()
        
        data = atomic_read_index(sample_topics)
        assert data is not None
        assert "topics" in data
        assert len(data["topics"]) == 3
        assert "updated" in data
    
    def test_stable_ordering_by_id(self, sample_topics: Path) -> None:
        """Topics are sorted by ID for stable output."""
        # Ensure no index exists
        index_path = sample_topics / "index.json"
        if index_path.exists():
            index_path.unlink()
        
        cmd_rebuild_index(sample_topics, dry_run=False)
        
        data = atomic_read_index(sample_topics)
        topic_ids = [t["id"] for t in data["topics"]]
        
        # Should be sorted alphabetically
        assert topic_ids == sorted(topic_ids)
    
    def test_preserves_existing_metadata(self, sample_topics: Path) -> None:
        """Existing keywords and metadata are preserved."""
        # Create initial index with custom metadata
        initial_data = {
            "topics": [
                {
                    "id": "seed-test-topic",
                    "title": "Old Title",
                    "keywords": ["custom", "keywords", "here"],
                    "custom_field": "preserved",
                }
            ]
        }
        atomic_write_index(sample_topics, initial_data)
        
        cmd_rebuild_index(sample_topics, dry_run=False)
        
        data = atomic_read_index(sample_topics)
        topic = next(t for t in data["topics"] if t["id"] == "seed-test-topic")
        
        # Keywords should be preserved
        assert "keywords" in topic
        assert topic["keywords"] == ["custom", "keywords", "here"]
        # Custom fields should be preserved
        assert topic.get("custom_field") == "preserved"
    
    def test_extracts_titles_from_content(self, sample_topics: Path) -> None:
        """Titles are extracted from content when not in existing index."""
        # Ensure no index exists
        index_path = sample_topics / "index.json"
        if index_path.exists():
            index_path.unlink()
        
        cmd_rebuild_index(sample_topics, dry_run=False)
        
        data = atomic_read_index(sample_topics)
        
        # Check titles were extracted
        topic1 = next(t for t in data["topics"] if t["id"] == "seed-test-topic")
        assert "Test Seed Topic" in topic1["title"]
        
        topic2 = next(t for t in data["topics"] if t["id"] == "plan-test-plan")
        assert "Plan Test Plan" in topic2["title"]
    
    def test_includes_doc_paths(self, sample_topics: Path) -> None:
        """Doc paths are included for existing files."""
        # Ensure no index exists
        index_path = sample_topics / "index.json"
        if index_path.exists():
            index_path.unlink()
        
        cmd_rebuild_index(sample_topics, dry_run=False)
        
        data = atomic_read_index(sample_topics)
        topic = next(t for t in data["topics"] if t["id"] == "seed-test-topic")
        
        assert "overview" in topic
        assert "sources" in topic
        assert topic["overview"] == "topics/seed-test-topic/overview.md"
    
    def test_removes_stale_paths(self, sample_topics: Path) -> None:
        """Stale doc paths are removed when files don't exist."""
        # Create index with non-existent paths
        initial_data = {
            "topics": [
                {
                    "id": "seed-test-topic",
                    "title": "Test",
                    "backlog": "topics/seed-test-topic/backlog.md",  # Doesn't exist
                }
            ]
        }
        atomic_write_index(sample_topics, initial_data)
        
        cmd_rebuild_index(sample_topics, dry_run=False)
        
        data = atomic_read_index(sample_topics)
        topic = next(t for t in data["topics"] if t["id"] == "seed-test-topic")
        
        # Stale path should be removed
        assert "backlog" not in topic
    
    def test_error_when_topics_dir_missing(self, temp_knowledge_dir: Path, capsys) -> None:
        """Error when topics directory doesn't exist (non-dry-run)."""
        result = cmd_rebuild_index(temp_knowledge_dir, dry_run=False)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Topics directory not found" in captured.err
    
    def test_dry_run_ok_when_topics_dir_missing(self, temp_knowledge_dir: Path) -> None:
        """Dry run succeeds even when topics directory doesn't exist."""
        result = cmd_rebuild_index(temp_knowledge_dir, dry_run=True)
        
        assert result == 0
