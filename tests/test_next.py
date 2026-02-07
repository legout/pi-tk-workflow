"""Tests for tf_cli.next module."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf_cli import next


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_project_root_with_tf_dir(self, tmp_path: Path) -> None:
        """Should find project root when .tf directory exists."""
        (tmp_path / ".tf").mkdir()

        with mock.patch("tf_cli.next.Path.cwd", return_value=tmp_path):
            result = next.find_project_root()
            assert result == tmp_path

    def test_finds_project_root_in_parent(self, tmp_path: Path) -> None:
        """Should find project root in parent directory."""
        (tmp_path / ".tf").mkdir()
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        with mock.patch("tf_cli.next.Path.cwd", return_value=subdir):
            result = next.find_project_root()
            assert result == tmp_path

    def test_returns_none_when_no_tf_dir(self, tmp_path: Path) -> None:
        """Should return None when no .tf directory found."""
        with mock.patch("tf_cli.next.Path.cwd", return_value=tmp_path):
            result = next.find_project_root()
            assert result is None


class TestLoadTicketQuery:
    """Tests for load_ticket_query function."""

    def test_loads_query_from_config(self, tmp_path: Path) -> None:
        """Should load ticketQuery from config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"ticketQuery": "tk list | head -1"}))

        result = next.load_ticket_query(config_file)
        assert result == "tk list | head -1"

    def test_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        """Should return None when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.json"
        result = next.load_ticket_query(config_file)
        assert result is None

    def test_returns_none_on_invalid_json(self, tmp_path: Path) -> None:
        """Should return None when JSON is invalid."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json")

        result = next.load_ticket_query(config_file)
        assert result is None

    def test_returns_none_when_empty_query(self, tmp_path: Path) -> None:
        """Should return None when ticketQuery is empty."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"ticketQuery": "   "}))

        result = next.load_ticket_query(config_file)
        assert result is None

    def test_returns_none_when_no_ticket_query_key(self, tmp_path: Path) -> None:
        """Should return None when ticketQuery key is missing."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"otherKey": "value"}))

        result = next.load_ticket_query(config_file)
        assert result is None


class TestResolveQuery:
    """Tests for resolve_query function."""

    def test_uses_config_query_when_available(self, tmp_path: Path) -> None:
        """Should use query from config when available."""
        (tmp_path / ".tf").mkdir()
        config_file = tmp_path / ".tf/ralph/config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"ticketQuery": "custom query"}))

        result = next.resolve_query(tmp_path)
        assert result == "custom query"

    def test_uses_default_when_no_config(self, tmp_path: Path) -> None:
        """Should use default query when no config."""
        result = next.resolve_query(None)
        assert result == next.DEFAULT_QUERY

    def test_uses_default_when_no_project_root(self) -> None:
        """Should use default query when no project root."""
        result = next.resolve_query(None)
        assert result == next.DEFAULT_QUERY


class TestRunQuery:
    """Tests for run_query function."""

    def test_runs_query_and_returns_first_word(self) -> None:
        """Should run query and return first word of output."""
        mock_result = mock.Mock()
        mock_result.stdout = "abc-123 some other output\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            result = next.run_query("tk ready")
            assert result == "abc-123"

    def test_returns_none_on_empty_output(self) -> None:
        """Should return None when output is empty."""
        mock_result = mock.Mock()
        mock_result.stdout = ""
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            result = next.run_query("tk ready")
            assert result is None

    def test_returns_none_on_whitespace_output(self) -> None:
        """Should return None when output is only whitespace."""
        mock_result = mock.Mock()
        mock_result.stdout = "   \n   "
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            result = next.run_query("tk ready")
            assert result is None


class TestMain:
    """Tests for main function."""

    def test_error_when_tk_not_in_path(self) -> None:
        """Should error when tk is not in PATH."""
        with mock.patch("shutil.which", return_value=None):
            result = next.main([])
            assert result == 1

    def test_error_when_no_tickets_found(self) -> None:
        """Should error when no tickets found."""
        with mock.patch("shutil.which", return_value="/usr/bin/tk"):
            with mock.patch.object(next, "run_query", return_value=None):
                result = next.main([])
                assert result == 1

    def test_success_prints_ticket(self, capsys) -> None:
        """Should print ticket ID on success."""
        with mock.patch("shutil.which", return_value="/usr/bin/tk"):
            with mock.patch.object(next, "run_query", return_value="abc-123"):
                result = next.main([])

        assert result == 0
        captured = capsys.readouterr()
        assert "abc-123" in captured.out

    def test_with_project_arg(self, tmp_path: Path) -> None:
        """Should use project argument when provided."""
        (tmp_path / ".tf").mkdir()
        config_file = tmp_path / ".tf/ralph/config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"ticketQuery": "custom query"}))

        with mock.patch("shutil.which", return_value="/usr/bin/tk"):
            with mock.patch.object(next, "run_query", return_value="xyz-789"):
                result = next.main(["--project", str(tmp_path)])

        assert result == 0
