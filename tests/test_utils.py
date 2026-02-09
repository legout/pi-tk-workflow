"""Tests for tf.utils module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tf.utils import find_project_root, merge, read_json


class TestReadJson:
    """Tests for read_json function."""

    def test_reads_valid_json(self, tmp_path: Path) -> None:
        """Test reading a valid JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "nested": {"a": 1}}
        test_file.write_text(json.dumps(test_data))

        result = read_json(test_file)
        assert result == test_data

    def test_returns_empty_dict_for_missing_file(self, tmp_path: Path) -> None:
        """Test that missing file returns empty dict."""
        missing_file = tmp_path / "nonexistent.json"

        result = read_json(missing_file)
        assert result == {}

    def test_returns_empty_dict_for_invalid_json(self, tmp_path: Path) -> None:
        """Test that invalid JSON returns empty dict."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json")

        result = read_json(test_file)
        assert result == {}

    def test_handles_unicode_content(self, tmp_path: Path) -> None:
        """Test reading JSON with unicode content."""
        test_file = tmp_path / "unicode.json"
        test_data = {"message": "Hello, 世界! 🌍"}
        test_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")

        result = read_json(test_file)
        assert result == test_data


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_tf_directory(self, tmp_path: Path) -> None:
        """Test finding project root with .tf directory."""
        # Create .tf directory
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = find_project_root(subdir)
        assert result == tmp_path

    def test_finds_pi_directory(self, tmp_path: Path) -> None:
        """Test finding project root with .pi directory."""
        # Create .pi directory
        pi_dir = tmp_path / ".pi"
        pi_dir.mkdir()
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        result = find_project_root(subdir)
        assert result == tmp_path

    def test_prefers_tf_over_parent_search(self, tmp_path: Path) -> None:
        """Test that .tf is found before searching parents."""
        # Create nested structure with .tf at both levels
        outer_tf = tmp_path / ".tf"
        outer_tf.mkdir()
        inner_dir = tmp_path / "inner"
        inner_dir.mkdir()
        inner_tf = inner_dir / ".tf"
        inner_tf.mkdir()

        result = find_project_root(inner_dir)
        # Should find the inner .tf first
        assert result == inner_dir

    def test_returns_none_when_no_marker(self, tmp_path: Path) -> None:
        """Test that None is returned when no marker directory exists."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = find_project_root(subdir)
        assert result is None

    def test_uses_cwd_when_no_start_given(self, tmp_path: Path, monkeypatch) -> None:
        """Test that current working directory is used when no start given."""
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        result = find_project_root()
        assert result == tmp_path

    def test_searches_parents(self, tmp_path: Path) -> None:
        """Test that function searches parent directories."""
        # Create nested structure
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()

        result = find_project_root(level3)
        assert result == tmp_path


class TestMerge:
    """Tests for merge function."""

    def test_simple_merge(self) -> None:
        """Test merging two simple dicts."""
        a = {"x": 1, "y": 2}
        b = {"y": 3, "z": 4}

        result = merge(a, b)

        assert result == {"x": 1, "y": 3, "z": 4}

    def test_nested_merge(self) -> None:
        """Test merging nested dictionaries."""
        a = {"outer": {"inner1": "a", "inner2": "b"}}
        b = {"outer": {"inner2": "c", "inner3": "d"}}

        result = merge(a, b)

        assert result == {"outer": {"inner1": "a", "inner2": "c", "inner3": "d"}}

    def test_does_not_mutate_input(self) -> None:
        """Test that original dicts are not modified."""
        a = {"x": 1, "nested": {"a": 1}}
        b = {"y": 2, "nested": {"b": 2}}
        a_copy = {"x": 1, "nested": {"a": 1}}
        b_copy = {"y": 2, "nested": {"b": 2}}

        merge(a, b)

        assert a == a_copy
        assert b == b_copy

    def test_empty_dict_merge(self) -> None:
        """Test merging with empty dicts."""
        a = {"key": "value"}
        b = {}

        result = merge(a, b)
        assert result == {"key": "value"}

        result = merge(b, a)
        assert result == {"key": "value"}

    def test_deeply_nested_merge(self) -> None:
        """Test merging deeply nested structures."""
        a = {"level1": {"level2": {"level3": {"a": 1, "b": 2}}}}
        b = {"level1": {"level2": {"level3": {"b": 3, "c": 4}}}}

        result = merge(a, b)

        assert result == {"level1": {"level2": {"level3": {"a": 1, "b": 3, "c": 4}}}}

    def test_overwrites_non_dict_values(self) -> None:
        """Test that non-dict values are overwritten."""
        a = {"key": "string"}
        b = {"key": {"nested": "dict"}}

        result = merge(a, b)

        assert result == {"key": {"nested": "dict"}}

    def test_real_world_config_merge(self) -> None:
        """Test merging realistic config structures."""
        global_config = {
            "metaModels": {
                "worker": {"model": "gpt-4", "thinking": "high"}
            },
            "checkers": {
                "python": {"lint": "ruff", "format": "black"}
            }
        }
        project_config = {
            "metaModels": {
                "worker": {"model": "gpt-5"}  # Override model
            },
            "agents": {"reviewer": "worker"}  # New key
        }

        result = merge(global_config, project_config)

        expected = {
            "metaModels": {
                "worker": {"model": "gpt-5", "thinking": "high"}
            },
            "checkers": {
                "python": {"lint": "ruff", "format": "black"}
            },
            "agents": {"reviewer": "worker"}
        }
        assert result == expected
