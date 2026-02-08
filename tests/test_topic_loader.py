"""Tests for the topic index loader in tf_cli/ui.py."""

import json
import os
from pathlib import Path

import pytest

from tf_cli.ui import (
    Topic,
    TopicDoc,
    TopicIndexLoader,
    TopicIndexLoadError,
    get_topic_type,
    format_topic_list,
    resolve_knowledge_dir,
)


class TestGetTopicType:
    """Tests for get_topic_type function."""
    
    def test_seed_prefix(self):
        assert get_topic_type("seed-add-versioning") == "seed"
        assert get_topic_type("seed-foo-bar") == "seed"
    
    def test_plan_prefix(self):
        assert get_topic_type("plan-kb-management-cli") == "plan"
        assert get_topic_type("plan-ticketflow-kanban-tui") == "plan"
    
    def test_spike_prefix(self):
        assert get_topic_type("spike-kanban-style-tui-in-python") == "spike"
    
    def test_baseline_prefix(self):
        assert get_topic_type("baseline-some-topic") == "baseline"
    
    def test_unknown_prefix(self):
        assert get_topic_type("random-topic") == "unknown"
        assert get_topic_type("feature-something") == "unknown"
        assert get_topic_type("") == "unknown"


class TestTopicDoc:
    """Tests for TopicDoc dataclass."""
    
    def test_creation(self):
        doc = TopicDoc(path="topics/test/overview.md", exists=True)
        assert doc.path == "topics/test/overview.md"
        assert doc.exists is True


class TestTopic:
    """Tests for Topic dataclass."""
    
    def test_basic_creation(self):
        topic = Topic(id="seed-test", title="Test Topic")
        assert topic.id == "seed-test"
        assert topic.title == "Test Topic"
        assert topic.topic_type == "unknown"
        assert topic.keywords == []
    
    def test_with_type(self):
        topic = Topic(id="seed-test", title="Test", topic_type="seed")
        assert topic.topic_type == "seed"
    
    def test_available_docs_empty(self):
        topic = Topic(id="seed-test", title="Test")
        assert topic.available_docs == {}
    
    def test_available_docs_with_existing(self):
        topic = Topic(
            id="seed-test",
            title="Test",
            overview=TopicDoc(path="topics/test/overview.md", exists=True),
            plan=TopicDoc(path="topics/test/plan.md", exists=False),
        )
        assert "overview" in topic.available_docs
        assert "plan" not in topic.available_docs
        assert topic.available_docs["overview"].path == "topics/test/overview.md"
    
    def test_available_docs_multiple(self):
        topic = Topic(
            id="plan-test",
            title="Test",
            overview=TopicDoc(path="o.md", exists=True),
            sources=TopicDoc(path="s.md", exists=True),
            plan=TopicDoc(path="p.md", exists=True),
            backlog=TopicDoc(path="b.md", exists=False),
        )
        docs = topic.available_docs
        assert set(docs.keys()) == {"overview", "sources", "plan"}


class TestTopicIndexLoader:
    """Tests for TopicIndexLoader class."""
    
    @pytest.fixture
    def tmp_knowledge_dir(self, tmp_path):
        """Create a temporary knowledge directory structure."""
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        knowledge_dir.mkdir(parents=True)
        
        # Create topic directories with files
        topics_dir = knowledge_dir / "topics"
        
        # Seed topic
        seed_dir = topics_dir / "seed-add-versioning"
        seed_dir.mkdir(parents=True)
        (seed_dir / "overview.md").write_text("# Overview")
        (seed_dir / "sources.md").write_text("# Sources")
        
        # Plan topic
        plan_dir = topics_dir / "plan-kb-management-cli"
        plan_dir.mkdir(parents=True)
        (plan_dir / "plan.md").write_text("# Plan")
        (plan_dir / "backlog.md").write_text("# Backlog")
        
        # Spike topic
        spike_dir = topics_dir / "spike-kanban-style-tui-in-python"
        spike_dir.mkdir(parents=True)
        (spike_dir / "overview.md").write_text("# Spike Overview")
        
        return knowledge_dir
    
    @pytest.fixture
    def populated_index(self, tmp_knowledge_dir):
        """Create a populated index.json."""
        index_data = {
            "topics": [
                {
                    "id": "seed-add-versioning",
                    "title": "Add versioning",
                    "keywords": ["versioning", "semantic-versioning"],
                    "overview": "topics/seed-add-versioning/overview.md",
                    "sources": "topics/seed-add-versioning/sources.md",
                },
                {
                    "id": "plan-kb-management-cli",
                    "title": "Knowledge base management commands",
                    "keywords": ["knowledge-base", "cli"],
                    "plan": "topics/plan-kb-management-cli/plan.md",
                    "backlog": "topics/plan-kb-management-cli/backlog.md",
                },
                {
                    "id": "spike-kanban-style-tui-in-python",
                    "title": "Kanban-style TUI in Python",
                    "keywords": ["kanban", "tui", "python"],
                    "overview": "topics/spike-kanban-style-tui-in-python/overview.md",
                },
            ]
        }
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text(json.dumps(index_data))
        return tmp_knowledge_dir
    
    def test_load_populated_index(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        topics = loader.load()
        
        assert len(topics) == 3
        assert loader._loaded is True
    
    def test_get_all(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        topics = loader.get_all()
        assert len(topics) == 3
        # Should return a copy
        topics.pop()
        assert len(loader.get_all()) == 3
    
    def test_get_by_type(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        seeds = loader.get_by_type("seed")
        plans = loader.get_by_type("plan")
        spikes = loader.get_by_type("spike")
        
        assert len(seeds) == 1
        assert seeds[0].id == "seed-add-versioning"
        assert len(plans) == 1
        assert plans[0].id == "plan-kb-management-cli"
        assert len(spikes) == 1
        assert spikes[0].id == "spike-kanban-style-tui-in-python"
    
    def test_get_by_id(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        topic = loader.get_by_id("seed-add-versioning")
        assert topic is not None
        assert topic.title == "Add versioning"
        
        missing = loader.get_by_id("nonexistent")
        assert missing is None
    
    def test_get_by_type_not_loaded(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        with pytest.raises(TopicIndexLoadError, match="not loaded"):
            loader.get_by_type("seed")
    
    def test_search_by_title(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        results = loader.search("versioning")
        assert len(results) == 1
        assert results[0].id == "seed-add-versioning"
    
    def test_search_by_keyword(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        results = loader.search("kanban")
        assert len(results) == 1
        assert results[0].id == "spike-kanban-style-tui-in-python"
    
    def test_search_by_id(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        results = loader.search("kb-management")
        assert len(results) == 1
        assert results[0].id == "plan-kb-management-cli"
    
    def test_search_case_insensitive(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        results_lower = loader.search("python")
        results_upper = loader.search("PYTHON")
        results_mixed = loader.search("Python")
        
        assert len(results_lower) == len(results_upper) == len(results_mixed)
    
    def test_search_no_results(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        results = loader.search("nonexistent")
        assert results == []
    
    def test_topic_types(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        types = loader.topic_types
        assert set(types) == {"seed", "plan", "spike"}
        assert "unknown" not in types
    
    def test_count_by_type(self, populated_index):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        counts = loader.count_by_type
        assert counts["seed"] == 1
        assert counts["plan"] == 1
        assert counts["spike"] == 1
        assert counts["baseline"] == 0
        assert counts["unknown"] == 0
    
    def test_missing_index_file(self, tmp_knowledge_dir):
        loader = TopicIndexLoader(tmp_knowledge_dir)
        
        with pytest.raises(TopicIndexLoadError) as exc_info:
            loader.load()
        
        assert "not found" in str(exc_info.value)
        assert "rebuild-index" in str(exc_info.value)
    
    def test_invalid_json(self, tmp_knowledge_dir):
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text("not valid json")
        
        loader = TopicIndexLoader(tmp_knowledge_dir)
        
        with pytest.raises(TopicIndexLoadError) as exc_info:
            loader.load()
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_invalid_format_number(self, tmp_knowledge_dir):
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text("42")
        
        loader = TopicIndexLoader(tmp_knowledge_dir)
        
        with pytest.raises(TopicIndexLoadError) as exc_info:
            loader.load()
        
        assert "Invalid index format" in str(exc_info.value)
    
    def test_legacy_list_format(self, tmp_knowledge_dir):
        """Test loading legacy format where index.json is a list."""
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text(json.dumps([
            {"id": "seed-test", "title": "Test"},
        ]))
        
        loader = TopicIndexLoader(tmp_knowledge_dir)
        topics = loader.load()
        
        assert len(topics) == 1
        assert topics[0].id == "seed-test"
    
    def test_empty_topics_list(self, tmp_knowledge_dir):
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text(json.dumps({"topics": []}))
        
        loader = TopicIndexLoader(tmp_knowledge_dir)
        topics = loader.load()
        
        assert topics == []
        assert loader.count_by_type == {
            "seed": 0, "plan": 0, "spike": 0, "baseline": 0, "unknown": 0
        }
    
    def test_doc_existence_check(self, populated_index, tmp_knowledge_dir):
        loader = TopicIndexLoader(populated_index)
        loader.load()
        
        seed = loader.get_by_id("seed-add-versioning")
        assert seed.overview.exists is True
        assert seed.sources.exists is True
        # plan not defined
        assert seed.plan is None
        
        plan = loader.get_by_id("plan-kb-management-cli")
        assert plan.plan.exists is True
        assert plan.backlog.exists is True
        assert plan.overview is None
    
    def test_doc_missing_file(self, populated_index, tmp_knowledge_dir):
        """Test that doc.exists is False when file doesn't exist."""
        index_path = tmp_knowledge_dir / "index.json"
        index_path.write_text(json.dumps({
            "topics": [{
                "id": "seed-test",
                "title": "Test",
                "overview": "topics/seed-test/nonexistent.md",
            }]
        }))
        
        loader = TopicIndexLoader(tmp_knowledge_dir)
        loader.load()
        
        topic = loader.get_by_id("seed-test")
        assert topic.overview.exists is False


class TestFormatTopicList:
    """Tests for format_topic_list function."""
    
    def test_empty_list(self):
        result = format_topic_list([])
        assert result == "No topics found."
    
    def test_single_topic(self):
        topic = Topic(id="seed-test", title="Test Topic")
        result = format_topic_list([topic])
        assert "seed-test" in result
        assert "Test Topic" in result
    
    def test_multiple_topics(self):
        topics = [
            Topic(id="seed-a", title="First"),
            Topic(id="plan-b", title="Second"),
        ]
        result = format_topic_list(topics)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert "First" in lines[0]
        assert "Second" in lines[1]
    
    def test_with_docs(self):
        topic = Topic(
            id="seed-test",
            title="Test",
            overview=TopicDoc(path="o.md", exists=True),
            plan=TopicDoc(path="p.md", exists=True),
        )
        result = format_topic_list([topic], show_docs=True)
        assert "overview" in result
        assert "plan" in result


class TestResolveKnowledgeDir:
    """Tests for resolve_knowledge_dir function."""
    
    def test_env_variable(self, monkeypatch, tmp_path):
        env_dir = tmp_path / "custom" / "knowledge"
        env_dir.mkdir(parents=True)
        monkeypatch.setenv("TF_KNOWLEDGE_DIR", str(env_dir))
        
        result = resolve_knowledge_dir()
        assert result == env_dir
    
    def test_cwd_fallback(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TF_KNOWLEDGE_DIR", raising=False)
        
        result = resolve_knowledge_dir()
        assert result == tmp_path / ".tf" / "knowledge"


class TestTopicIndexError:
    """Tests for TopicIndexLoadError."""
    
    def test_is_exception(self):
        with pytest.raises(TopicIndexLoadError):
            raise TopicIndexLoadError("test error")
    
    def test_message(self):
        err = TopicIndexLoadError("custom message")
        assert "custom message" in str(err)
