"""Unit tests for kb_helpers module.

Tests:
- resolve_knowledge_dir with various resolution paths
- atomic_read_index for reading index.json
- atomic_write_index for atomic writes using tmp+rename
- get_topic_type for deriving topic type from ID
- is_topic_archived for checking archive status
- get_topic_docs for getting documentation paths
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from tf_cli.kb_helpers import (
    atomic_read_index,
    atomic_write_index,
    ensure_index_exists,
    resolve_knowledge_dir,
    get_topic_type,
    is_topic_archived,
    get_topic_docs,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_repo(temp_dir: Path) -> Path:
    """Create a mock ticketflow repo structure."""
    tf_dir = temp_dir / ".tf"
    tf_dir.mkdir()
    (tf_dir / "tickets").mkdir()
    (tf_dir / "ralph").mkdir()
    (temp_dir / "AGENTS.md").write_text("# Test")
    (temp_dir / "pyproject.toml").write_text("[project]")
    return temp_dir


class TestResolveKnowledgeDir:
    """Tests for resolve_knowledge_dir function."""

    def test_cli_override_priority(self, mock_repo: Path) -> None:
        """CLI --knowledge-dir override has highest priority."""
        override = Path("/custom/kb")
        result = resolve_knowledge_dir(
            project_path=mock_repo,
            knowledge_dir_override=override
        )
        assert result == Path("/custom/kb").resolve()

    def test_env_var_priority(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """TF_KNOWLEDGE_DIR env var has second priority."""
        monkeypatch.setenv("TF_KNOWLEDGE_DIR", "/env/kb")
        result = resolve_knowledge_dir(project_path=mock_repo)
        assert result == Path("/env/kb").resolve()

    def test_cli_override_beats_env_var(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI override beats environment variable."""
        monkeypatch.setenv("TF_KNOWLEDGE_DIR", "/env/kb")
        override = Path("/cli/kb")
        result = resolve_knowledge_dir(
            project_path=mock_repo,
            knowledge_dir_override=override
        )
        assert result == Path("/cli/kb").resolve()

    def test_config_file_priority(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """workflow.knowledgeDir from config has third priority."""
        monkeypatch.chdir(mock_repo)
        config_dir = mock_repo / ".tf" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text(json.dumps({
            "workflow": {"knowledgeDir": "/config/kb"}
        }))

        result = resolve_knowledge_dir()
        assert result == Path("/config/kb").resolve()

    def test_config_relative_path(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Relative knowledgeDir in config is resolved relative to repo root."""
        monkeypatch.chdir(mock_repo)
        config_dir = mock_repo / ".tf" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text(json.dumps({
            "workflow": {"knowledgeDir": "custom/kb"}
        }))

        result = resolve_knowledge_dir()
        assert result == (mock_repo / "custom" / "kb").resolve()

    def test_config_with_tilde(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """knowledgeDir with ~ is expanded to home directory."""
        monkeypatch.chdir(mock_repo)
        monkeypatch.setenv("HOME", str(mock_repo))
        config_dir = mock_repo / ".tf" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text(json.dumps({
            "workflow": {"knowledgeDir": "~/kb"}
        }))

        result = resolve_knowledge_dir()
        assert result == (mock_repo / "kb").resolve()

    def test_default_in_repo(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default is .tf/knowledge in repo root when no config."""
        monkeypatch.chdir(mock_repo)
        result = resolve_knowledge_dir()
        assert result == (mock_repo / ".tf" / "knowledge").resolve()

    def test_env_var_beats_config(self, mock_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variable beats config file."""
        monkeypatch.setenv("TF_KNOWLEDGE_DIR", "/env/kb")
        config_dir = mock_repo / ".tf" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "settings.json"
        config_file.write_text(json.dumps({
            "workflow": {"knowledgeDir": "/config/kb"}
        }))

        result = resolve_knowledge_dir()
        assert result == Path("/env/kb").resolve()

    def test_explicit_project_path(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit project_path parameter works."""
        monkeypatch.chdir(temp_dir)
        result = resolve_knowledge_dir(project_path=temp_dir)
        assert result == (temp_dir / ".tf" / "knowledge").resolve()

    def test_cwd_fallback(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Fallback to cwd/.tf/knowledge when not in a repo."""
        monkeypatch.chdir(temp_dir)
        result = resolve_knowledge_dir()
        assert result == (temp_dir / ".tf" / "knowledge").resolve()


class TestAtomicReadIndex:
    """Tests for atomic_read_index function."""

    def test_returns_none_when_not_exists(self, temp_dir: Path) -> None:
        """Returns None when index.json doesn't exist."""
        result = atomic_read_index(temp_dir)
        assert result is None

    def test_reads_valid_index(self, temp_dir: Path) -> None:
        """Successfully reads a valid index.json file."""
        index_file = temp_dir / "index.json"
        data = {"topics": [{"id": "test", "title": "Test Topic"}]}
        index_file.write_text(json.dumps(data))

        result = atomic_read_index(temp_dir)
        assert result is not None
        assert result["topics"][0]["id"] == "test"

    def test_reads_array_format(self, temp_dir: Path) -> None:
        """Handles array format (list instead of dict with topics)."""
        index_file = temp_dir / "index.json"
        data = [{"id": "test", "title": "Test Topic"}]
        index_file.write_text(json.dumps(data))

        result = atomic_read_index(temp_dir)
        assert result is not None
        assert result["topics"][0]["id"] == "test"

    def test_handles_corrupted_json(self, temp_dir: Path) -> None:
        """Returns empty topics list for corrupted JSON."""
        index_file = temp_dir / "index.json"
        index_file.write_text("{invalid json")

        result = atomic_read_index(temp_dir)
        assert result is not None
        assert result["topics"] == []

    def test_handles_missing_topics_key(self, temp_dir: Path) -> None:
        """Adds empty topics key if missing."""
        index_file = temp_dir / "index.json"
        index_file.write_text(json.dumps({"version": "1.0"}))

        result = atomic_read_index(temp_dir)
        assert result is not None
        assert "topics" in result
        assert result["topics"] == []

    def test_raises_permission_error_on_unreadable(self, temp_dir: Path) -> None:
        """Raises PermissionError when file exists but cannot be read."""
        index_file = temp_dir / "index.json"
        index_file.write_text(json.dumps({"topics": []}))
        # Make file unreadable
        os.chmod(index_file, 0o000)

        try:
            with pytest.raises(PermissionError):
                atomic_read_index(temp_dir)
        finally:
            os.chmod(index_file, 0o644)


class TestAtomicWriteIndex:
    """Tests for atomic_write_index function."""

    def test_creates_directory_if_needed(self, temp_dir: Path) -> None:
        """Creates knowledge directory if it doesn't exist."""
        kb_dir = temp_dir / "new" / "kb"
        data = {"topics": []}

        result = atomic_write_index(kb_dir, data)

        assert kb_dir.exists()
        assert result == (kb_dir / "index.json")

    def test_writes_valid_json(self, temp_dir: Path) -> None:
        """Writes valid JSON that can be read back."""
        data = {"topics": [{"id": "test", "title": "Test"}]}

        atomic_write_index(temp_dir, data)

        content = (temp_dir / "index.json").read_text()
        parsed = json.loads(content)
        assert parsed["topics"][0]["id"] == "test"

    def test_atomic_write_no_partial_files(self, temp_dir: Path) -> None:
        """Atomic write leaves no temp files behind."""
        data = {"topics": [{"id": "test"}]}

        atomic_write_index(temp_dir, data)

        # Should only have index.json, no .tmp files
        files = list(temp_dir.iterdir())
        assert len(files) == 1
        assert files[0].name == "index.json"

    def test_overwrites_existing(self, temp_dir: Path) -> None:
        """Can overwrite existing index.json."""
        index_file = temp_dir / "index.json"
        index_file.write_text(json.dumps({"topics": [{"id": "old"}]}))

        new_data = {"topics": [{"id": "new"}]}
        atomic_write_index(temp_dir, new_data)

        content = json.loads(index_file.read_text())
        assert content["topics"][0]["id"] == "new"

    def test_pretty_printed_json(self, temp_dir: Path) -> None:
        """Output is pretty-printed with indentation."""
        data = {"topics": [{"id": "test", "title": "Test Topic"}]}

        atomic_write_index(temp_dir, data)

        content = (temp_dir / "index.json").read_text()
        assert "  \"topics\"" in content or '"topics"' in content
        assert "\n" in content  # Has newlines for pretty printing


class TestEnsureIndexExists:
    """Tests for ensure_index_exists function."""

    def test_creates_new_index_when_missing(self, temp_dir: Path) -> None:
        """Creates new index.json with empty topics when missing."""
        result = ensure_index_exists(temp_dir)

        assert (temp_dir / "index.json").exists()
        assert result["topics"] == []

    def test_returns_existing_data(self, temp_dir: Path) -> None:
        """Returns existing data when index.json exists."""
        existing = {"topics": [{"id": "existing"}]}
        (temp_dir / "index.json").write_text(json.dumps(existing))

        result = ensure_index_exists(temp_dir)

        assert result["topics"][0]["id"] == "existing"


class TestGetTopicType:
    """Tests for get_topic_type function."""

    def test_seed_prefix(self) -> None:
        """Returns 'seed' for seed- prefixed IDs."""
        assert get_topic_type("seed-add-versioning") == "seed"
        assert get_topic_type("seed-kb-management") == "seed"

    def test_plan_prefix(self) -> None:
        """Returns 'plan' for plan- prefixed IDs."""
        assert get_topic_type("plan-kb-management-cli") == "plan"
        assert get_topic_type("plan-auto-linking") == "plan"

    def test_spike_prefix(self) -> None:
        """Returns 'spike' for spike- prefixed IDs."""
        assert get_topic_type("spike-web-search") == "spike"

    def test_baseline_prefix(self) -> None:
        """Returns 'baseline' for baseline- prefixed IDs."""
        assert get_topic_type("baseline-codebase") == "baseline"

    def test_unknown_prefix(self) -> None:
        """Returns 'unknown' for unrecognized prefixes."""
        assert get_topic_type("custom-topic") == "unknown"
        assert get_topic_type("") == "unknown"


class TestIsTopicArchived:
    """Tests for is_topic_archived function."""

    def test_not_archived_when_directory_missing(self, temp_dir: Path) -> None:
        """Returns False when archive directory doesn't exist."""
        assert is_topic_archived(temp_dir, "seed-test") is False

    def test_not_archived_when_topic_not_in_archive(self, temp_dir: Path) -> None:
        """Returns False when topic is not in archive."""
        archive_dir = temp_dir / "archive" / "topics"
        archive_dir.mkdir(parents=True)
        (archive_dir / "other-topic").mkdir()
        assert is_topic_archived(temp_dir, "seed-test") is False

    def test_archived_when_topic_in_archive(self, temp_dir: Path) -> None:
        """Returns True when topic exists in archive."""
        topic_dir = temp_dir / "archive" / "topics" / "seed-test"
        topic_dir.mkdir(parents=True)
        assert is_topic_archived(temp_dir, "seed-test") is True


class TestGetTopicDocs:
    """Tests for get_topic_docs function."""

    def test_returns_doc_paths_for_active_topic(self, temp_dir: Path) -> None:
        """Returns doc paths for an active topic."""
        topic_dir = temp_dir / "topics" / "seed-test"
        topic_dir.mkdir(parents=True)
        (topic_dir / "overview.md").write_text("# Overview")
        (topic_dir / "plan.md").write_text("# Plan")

        docs = get_topic_docs(temp_dir, "seed-test", archived=False)

        assert docs["overview"]["exists"] is True
        assert docs["sources"]["exists"] is False
        assert docs["plan"]["exists"] is True
        assert docs["backlog"]["exists"] is False

    def test_returns_doc_paths_for_archived_topic(self, temp_dir: Path) -> None:
        """Returns doc paths for an archived topic."""
        topic_dir = temp_dir / "archive" / "topics" / "seed-test"
        topic_dir.mkdir(parents=True)
        (topic_dir / "sources.md").write_text("# Sources")

        docs = get_topic_docs(temp_dir, "seed-test", archived=True)

        assert docs["overview"]["exists"] is False
        assert docs["sources"]["exists"] is True
        assert docs["plan"]["exists"] is False
        assert docs["backlog"]["exists"] is False
