"""Tests for Ralph progress total computation (pt-u3vz).

These tests verify that the progress display shows the actual ready ticket count
instead of defaulting to maxIterations (50).

Tests cover:
- Progress total equals actual ready ticket count
- '?' placeholder shown when ticket listing fails
- No regression to default 50 when ready count differs
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tf import ralph as ralph_module


class TestRalphProgressTotalComputation:
    """Test that progress total is computed from ready tickets, not maxIterations."""

    def test_progress_total_matches_ready_ticket_count(self, tmp_path: Path) -> None:
        """Progress total should equal len(list_ready_tickets()), not default 50.
        
        This test ensures the fix from pt-qu8a doesn't regress - the progress
        display should show the actual ready ticket count, not maxIterations.
        """
        # Mock project structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{
            "maxIterations": 50,
            "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
            "completionCheck": "tk ready | grep -q .",
            "sleepBetweenTickets": 100,
            "workflow": "/tf",
            "workflowFlags": "--auto"
        }"""
        (ralph_dir / "config.json").write_text(config_content)
        
        # Create a mock StringIO to capture progress output
        progress_output = StringIO()
        
        # Patch dependencies
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
                    "completionCheck": "tk ready | grep -q .",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "--auto",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    with patch.object(ralph_module, "list_ready_tickets", return_value=["TICKET-1", "TICKET-2", "TICKET-3"]):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):  # One iteration then empty
                            with patch.object(ralph_module, "select_ticket", return_value="TICKET-1"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    # Mock ProgressDisplay to capture what total was passed
                                                    mock_display = MagicMock()
                                                    mock_display.start_ticket = MagicMock()
                                                    mock_display.complete_ticket = MagicMock()
                                                    
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            # Run ralph_start with --progress
                                                            with patch.object(sys, "stderr", progress_output):
                                                                with patch("sys.stderr.isatty", return_value=False):
                                                                    result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                    
                                                                    # Verify the loop completed successfully
                                                                    assert result == 0
                                                                    
                                                                    # Verify ProgressDisplay was created
                                                                    ralph_module.ProgressDisplay.assert_called_once()
                                                                    
                                                                    # Verify start_ticket was called with correct total (3 tickets, not 50)
                                                                    mock_display.start_ticket.assert_called_once()
                                                                    call_args = mock_display.start_ticket.call_args
                                                                    # call_args[0] = positional args, call_args[1] = kwargs
                                                                    if call_args[1]:
                                                                        # Called with kwargs
                                                                        total_arg = call_args[1].get('total_tickets') or call_args[0][2]
                                                                    else:
                                                                        # Called with positional args: (ticket_id, iteration, total_tickets)
                                                                        total_arg = call_args[0][2]
                                                                    
                                                                    # The key assertion: total should be "3" (actual ticket count), NOT "50"
                                                                    assert total_arg == "3", f"Expected progress total to be '3' (actual ticket count), but got '{total_arg}'"
                                                                    assert total_arg != "50", "Progress total should not be default maxIterations (50)"

    def test_progress_total_with_five_tickets(self, tmp_path: Path) -> None:
        """Test that progress shows [1/5] when there are 5 ready tickets."""
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        # Five ready tickets
        ready_tickets = ["T-1", "T-2", "T-3", "T-4", "T-5"]
        
        mock_display = MagicMock()
        mock_display.start_ticket = MagicMock()
        mock_display.complete_ticket = MagicMock()
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    with patch.object(ralph_module, "list_ready_tickets", return_value=ready_tickets):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                            with patch.object(ralph_module, "select_ticket", return_value="T-1"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            with patch("sys.stderr.isatty", return_value=False):
                                                                result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                
                                                                assert result == 0
                                                                mock_display.start_ticket.assert_called_once()
                                                                call_args = mock_display.start_ticket.call_args
                                                                if call_args[1]:
                                                                    total_arg = call_args[1].get('total_tickets') or call_args[0][2]
                                                                else:
                                                                    total_arg = call_args[0][2]
                                                                
                                                                # Progress should show 5 tickets, not 50
                                                                assert total_arg == "5", f"Expected '5', got '{total_arg}'"

    def test_progress_shows_placeholder_when_listing_fails(self, tmp_path: Path) -> None:
        """When list_ready_tickets fails, progress should show '?' not '50'."""
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        mock_display = MagicMock()
        mock_display.start_ticket = MagicMock()
        mock_display.complete_ticket = MagicMock()
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    # Simulate listing failure - returns empty list or raises exception
                    with patch.object(ralph_module, "list_ready_tickets", side_effect=Exception("tk failed")):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                            with patch.object(ralph_module, "select_ticket", return_value="T-1"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            with patch("sys.stderr.isatty", return_value=False):
                                                                result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                
                                                                assert result == 0
                                                                mock_display.start_ticket.assert_called_once()
                                                                call_args = mock_display.start_ticket.call_args
                                                                if call_args[1]:
                                                                    total_arg = call_args[1].get('total_tickets') or call_args[0][2]
                                                                else:
                                                                    total_arg = call_args[0][2]
                                                                
                                                                # When listing fails, should show '?' not '50'
                                                                assert total_arg == "?", f"Expected '?' when listing fails, got '{total_arg}'"

    def test_progress_shows_question_when_empty_list(self, tmp_path: Path) -> None:
        """When list_ready_tickets returns empty, progress should show '?' not '50'."""
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        mock_display = MagicMock()
        mock_display.start_ticket = MagicMock()
        mock_display.complete_ticket = MagicMock()
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    # Empty list returned (edge case - shouldn't happen with active tickets)
                    with patch.object(ralph_module, "list_ready_tickets", return_value=[]):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                            with patch.object(ralph_module, "select_ticket", return_value="T-1"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            with patch("sys.stderr.isatty", return_value=False):
                                                                result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                
                                                                assert result == 0
                                                                mock_display.start_ticket.assert_called_once()
                                                                call_args = mock_display.start_ticket.call_args
                                                                if call_args[1]:
                                                                    total_arg = call_args[1].get('total_tickets') or call_args[0][2]
                                                                else:
                                                                    total_arg = call_args[0][2]
                                                                
                                                                # Empty list means ready_tickets_count is 0, which is falsy → '?'
                                                                assert total_arg == "?", f"Expected '?' for empty list, got '{total_arg}'"

    def test_no_progress_without_flag(self, tmp_path: Path) -> None:
        """ProgressDisplay should not be created when --progress flag is not used."""
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                        with patch.object(ralph_module, "select_ticket", return_value="T-1"):
                            with patch.object(ralph_module, "lock_acquire", return_value=True):
                                with patch.object(ralph_module, "lock_release"):
                                    with patch.object(ralph_module, "set_state"):
                                        with patch.object(ralph_module, "clear_ticket_title_cache"):
                                            with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                with patch.object(ralph_module, "ProgressDisplay") as mock_progress_class:
                                                    with patch.object(ralph_module, "run_ticket", return_value=0):
                                                        with patch("sys.stderr.isatty", return_value=False):
                                                            # Run WITHOUT --progress flag
                                                            result = ralph_module.ralph_start(["--max-iterations", "1", "--quiet"])
                                                            
                                                            assert result == 0
                                                            # ProgressDisplay should NOT be instantiated
                                                            mock_progress_class.assert_not_called()


class TestProgressTotalRegression:
    """Regression tests to ensure progress total bug doesn't reoccur."""

    def test_progress_not_shows_fifty_for_small_backlog(self, tmp_path: Path) -> None:
        """Critical regression test: [1/50] should NOT appear when only 3 tickets ready.
        
        This test would fail if the code reverts to using maxIterations (50) as total.
        """
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        mock_display = MagicMock()
        mock_display.start_ticket = MagicMock()
        mock_display.complete_ticket = MagicMock()
        
        # Capture what would be output
        captured_total = None
        
        def capture_start(ticket_id: str, iteration: int, total_tickets: Any) -> None:
            nonlocal captured_total
            captured_total = str(total_tickets)
        
        mock_display.start_ticket.side_effect = capture_start
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    # Only 3 tickets ready (small backlog)
                    with patch.object(ralph_module, "list_ready_tickets", return_value=["A", "B", "C"]):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                            with patch.object(ralph_module, "select_ticket", return_value="A"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            with patch("sys.stderr.isatty", return_value=False):
                                                                result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                
                                                                assert result == 0
                                                                assert captured_total is not None, "start_ticket was not called"
                                                                
                                                                # THE KEY REGRESSION TEST:
                                                                # If this fails, the bug is back - showing [*/50] for small backlogs
                                                                assert captured_total != "50", (
                                                                    f"REGRESSION: Progress shows '[*/50]' but only 3 tickets ready. "
                                                                    f"The code has reverted to using maxIterations instead of actual count."
                                                                )
                                                                assert captured_total == "3", f"Expected '3', got '{captured_total}'"

    def test_progress_single_ticket_not_shows_fifty(self, tmp_path: Path) -> None:
        """Single ticket ready should show [1/1], NOT [1/50]."""
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        
        config_content = """{"maxIterations": 50, "ticketQuery": "tk ready", "completionCheck": "test", "sleepBetweenTickets": 100, "workflow": "/tf"}"""
        (ralph_dir / "config.json").write_text(config_content)
        
        mock_display = MagicMock()
        mock_display.start_ticket = MagicMock()
        mock_display.complete_ticket = MagicMock()
        
        captured_total = None
        
        def capture_start(ticket_id: str, iteration: int, total_tickets: Any) -> None:
            nonlocal captured_total
            captured_total = str(total_tickets)
        
        mock_display.start_ticket.side_effect = capture_start
        
        with patch.object(ralph_module, "find_project_root", return_value=tmp_path):
            with patch.object(ralph_module, "ensure_ralph_dir", return_value=ralph_dir):
                with patch.object(ralph_module, "load_config", return_value={
                    "maxIterations": 50,
                    "ticketQuery": "tk ready",
                    "completionCheck": "test",
                    "sleepBetweenTickets": 100,
                    "workflow": "/tf",
                    "workflowFlags": "",
                    "parallelWorkers": 1,
                    "logLevel": "quiet",
                }):
                    # Single ticket ready
                    with patch.object(ralph_module, "list_ready_tickets", return_value=["ONLY-TICKET"]):
                        with patch.object(ralph_module, "backlog_empty", side_effect=[False, True]):
                            with patch.object(ralph_module, "select_ticket", return_value="ONLY-TICKET"):
                                with patch.object(ralph_module, "lock_acquire", return_value=True):
                                    with patch.object(ralph_module, "lock_release"):
                                        with patch.object(ralph_module, "set_state"):
                                            with patch.object(ralph_module, "clear_ticket_title_cache"):
                                                with patch.object(ralph_module, "resolve_knowledge_dir", return_value=tmp_path / ".tf" / "knowledge"):
                                                    with patch.object(ralph_module, "ProgressDisplay", return_value=mock_display):
                                                        with patch.object(ralph_module, "run_ticket", return_value=0):
                                                            with patch("sys.stderr.isatty", return_value=False):
                                                                result = ralph_module.ralph_start(["--progress", "--max-iterations", "1", "--quiet"])
                                                                
                                                                assert result == 0
                                                                assert captured_total is not None
                                                                assert captured_total == "1", f"Single ticket should show '1', got '{captured_total}'"
                                                                assert captured_total != "50", "REGRESSION: Showing [1/50] for single ticket!"
