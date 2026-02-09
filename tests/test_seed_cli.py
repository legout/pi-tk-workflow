"""Tests for tf.seed_cli module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tf import seed_cli as seed_module


class TestCmdActive:
    """Tests for cmd_active function."""

    @patch.object(seed_module, "get_active_session_info")
    def test_active_shows_none_when_no_session(self, mock_get_info: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test output when no active session."""
        mock_get_info.return_value = None
        
        result = seed_module.cmd_active()
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "none"

    @patch.object(seed_module, "get_active_session_info")
    def test_active_shows_session_info(self, mock_get_info: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test output with active session."""
        mock_get_info.return_value = {
            "session_id": "sess-123",
            "root_seed": "my-seed",
            "state": "active",
            "spike_count": 3,
            "has_plan": True,
            "has_backlog": True,
            "ticket_count": 5
        }
        
        result = seed_module.cmd_active()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "sess-123" in captured.out
        assert "my-seed" in captured.out
        assert "active" in captured.out
        assert "spikes: 3" in captured.out
        assert "plan: yes" in captured.out
        assert "backlog: yes" in captured.out
        assert "tickets: 5" in captured.out

    @patch.object(seed_module, "get_active_session_info")
    def test_active_with_no_backlog_tickets(self, mock_get_info: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test output when backlog has no tickets."""
        mock_get_info.return_value = {
            "session_id": "sess-456",
            "root_seed": "other-seed",
            "state": "planning",
            "spike_count": 0,
            "has_plan": False,
            "has_backlog": False,
            "ticket_count": 0
        }
        
        result = seed_module.cmd_active()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "sess-456" in captured.out
        assert "plan: no" in captured.out
        assert "backlog: no" in captured.out


class TestCmdSessions:
    """Tests for cmd_sessions function."""

    @patch.object(seed_module, "list_archived_sessions")
    def test_sessions_shows_empty_message(self, mock_list: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test message when no sessions exist."""
        mock_list.return_value = []
        
        result = seed_module.cmd_sessions()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "No archived sessions found" in captured.out

    @patch.object(seed_module, "list_archived_sessions")
    def test_sessions_lists_sessions(self, mock_list: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test listing multiple sessions."""
        mock_list.return_value = [
            {
                "session_id": "sess-1",
                "root_seed": "seed-a",
                "state": "archived",
                "created": "2024-01-01",
                "updated": "2024-01-02",
                "spikes": ["spike1"],
                "plan": {"name": "plan"},
                "backlog": {"tickets": [{"id": "t1"}]}
            },
            {
                "session_id": "sess-2",
                "root_seed": "seed-b",
                "state": "archived",
                "created": "2024-02-01",
                "updated": "2024-02-02",
                "spikes": [],
                "plan": None,
                "backlog": None
            }
        ]
        
        result = seed_module.cmd_sessions()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "sess-1" in captured.out
        assert "sess-2" in captured.out
        assert "seed-a" in captured.out
        assert "seed-b" in captured.out
        assert "Total: 2 session(s)" in captured.out

    @patch.object(seed_module, "list_archived_sessions")
    def test_sessions_filtered_by_seed(self, mock_list: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test filtering sessions by seed ID."""
        mock_list.return_value = []
        
        result = seed_module.cmd_sessions(seed_id="my-seed")
        
        assert result == 0
        mock_list.assert_called_once_with("my-seed", None)
        captured = capsys.readouterr()
        assert "my-seed" in captured.out


class TestCmdResume:
    """Tests for cmd_resume function."""

    @patch.object(seed_module, "load_archived_session")
    @patch.object(seed_module, "resume_session")
    def test_resume_by_session_id(self, mock_resume: MagicMock, mock_load: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test resuming by direct session ID."""
        mock_load.return_value = {"session_id": "sess-123"}
        mock_resume.return_value = {"session_id": "sess-123", "root_seed": "my-seed"}
        
        result = seed_module.cmd_resume("sess-123")
        
        assert result == 0
        mock_load.assert_called_once_with("sess-123", None)
        mock_resume.assert_called_once_with("sess-123", None)
        captured = capsys.readouterr()
        assert "Resumed planning session: sess-123" in captured.out

    @patch.object(seed_module, "load_archived_session")
    @patch.object(seed_module, "find_latest_session_for_seed")
    @patch.object(seed_module, "resume_session")
    def test_resume_by_seed_id(self, mock_resume: MagicMock, mock_find: MagicMock, mock_load: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test resuming by seed ID (finds latest session)."""
        mock_load.return_value = None
        mock_find.return_value = {"session_id": "sess-latest"}
        mock_resume.return_value = {"session_id": "sess-latest", "root_seed": "my-seed"}
        
        result = seed_module.cmd_resume("my-seed")
        
        assert result == 0
        mock_load.assert_called_once_with("my-seed", None)
        mock_find.assert_called_once_with("my-seed", None)
        captured = capsys.readouterr()
        assert "Found latest session for my-seed: sess-latest" in captured.out

    @patch.object(seed_module, "load_archived_session")
    @patch.object(seed_module, "find_latest_session_for_seed")
    def test_resume_fails_when_no_session_found(self, mock_find: MagicMock, mock_load: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test error when no session found."""
        mock_load.return_value = None
        mock_find.return_value = None
        
        result = seed_module.cmd_resume("nonexistent")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "nonexistent" in captured.err

    @patch.object(seed_module, "load_archived_session")
    @patch.object(seed_module, "resume_session")
    def test_resume_fails_when_resume_fails(self, mock_resume: MagicMock, mock_load: MagicMock, capsys: pytest.CaptureFixture) -> None:
        """Test error when resume_session returns None."""
        mock_load.return_value = {"session_id": "sess-123"}
        mock_resume.return_value = None
        
        result = seed_module.cmd_resume("sess-123")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestMain:
    """Tests for main function."""

    @patch.object(seed_module, "cmd_active")
    def test_main_defaults_to_active(self, mock_active: MagicMock) -> None:
        """Test that main defaults to --active behavior."""
        mock_active.return_value = 0
        result = seed_module.main([])
        assert result == 0
        mock_active.assert_called_once()

    @patch.object(seed_module, "cmd_active")
    def test_main_explicit_active(self, mock_active: MagicMock) -> None:
        """Test explicit --active flag."""
        mock_active.return_value = 0
        result = seed_module.main(["--active"])
        assert result == 0
        mock_active.assert_called_once()

    @patch.object(seed_module, "cmd_sessions")
    def test_main_sessions_flag(self, mock_sessions: MagicMock) -> None:
        """Test --sessions flag."""
        mock_sessions.return_value = 0
        result = seed_module.main(["--sessions"])
        assert result == 0
        mock_sessions.assert_called_once()

    @patch.object(seed_module, "cmd_sessions")
    def test_main_sessions_with_seed(self, mock_sessions: MagicMock) -> None:
        """Test --sessions with seed ID."""
        from unittest.mock import ANY
        mock_sessions.return_value = 0
        result = seed_module.main(["--sessions", "my-seed"])
        assert result == 0
        mock_sessions.assert_called_once_with("my-seed", ANY)

    @patch.object(seed_module, "cmd_resume")
    def test_main_resume_flag(self, mock_resume: MagicMock) -> None:
        """Test --resume flag."""
        mock_resume.return_value = 0
        result = seed_module.main(["--resume", "sess-123"])
        assert result == 0
        mock_resume.assert_called_once_with("sess-123", None)

    @patch.object(seed_module, "cmd_active")
    def test_main_knowledge_dir_option(self, mock_active: MagicMock) -> None:
        """Test --knowledge-dir option."""
        from pathlib import Path
        mock_active.return_value = 0
        result = seed_module.main(["--knowledge-dir", "/path/to/kb"])
        assert result == 0
        args = mock_active.call_args
        assert isinstance(args[0][0], Path)
        assert str(args[0][0]) == "/path/to/kb"

    def test_main_mutually_exclusive(self) -> None:
        """Test that --active and --resume are mutually exclusive."""
        # argparse exits with SystemExit for mutually exclusive argument errors
        with pytest.raises(SystemExit) as exc_info:
            seed_module.main(["--active", "--resume", "sess-123"])
        assert exc_info.value.code == 2  # argparse error exit code
