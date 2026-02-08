"""Tests for ProgressDisplay class and non-TTY progress behavior.

Tests cover:
- Non-TTY progress behavior (no control characters)
- TTY mode control character handling
- Ticket start/complete/fail state updates
"""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from tf_cli.ralph import ProgressDisplay


class TestProgressDisplayInit:
    """Test ProgressDisplay initialization."""

    def test_default_tty_detection(self):
        """Default is_tty should be detected from output stream."""
        output = StringIO()
        display = ProgressDisplay(output=output)
        # StringIO is not a TTY
        assert display.is_tty is False
        assert display.output is output

    def test_explicit_tty_true(self):
        """Can explicitly set is_tty=True."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=True)
        assert display.is_tty is True

    def test_explicit_tty_false(self):
        """Can explicitly set is_tty=False."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        assert display.is_tty is False

    def test_initial_state(self):
        """Initial state should be zeroed."""
        output = StringIO()
        display = ProgressDisplay(output=output)
        assert display.current_ticket is None
        assert display.completed == 0
        assert display.failed == 0
        assert display.total == 0
        assert display._last_line_len == 0


class TestProgressDisplayNonTTY:
    """Test ProgressDisplay in non-TTY mode (no control characters)."""

    def test_start_ticket_no_output(self):
        """Non-TTY: start_ticket should not produce output."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 5)
        
        # In non-TTY mode, intermediate progress is suppressed
        assert output.getvalue() == ""
        assert display.current_ticket == "abc-123"
        assert display.total == 5

    def test_complete_ticket_success_newline(self):
        """Non-TTY: complete_ticket should produce plain text with newline."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 5)
        display.complete_ticket("abc-123", "COMPLETE", 0)
        
        result = output.getvalue()
        # Should have exactly one newline at the end
        assert result.endswith("\n")
        # Should NOT have carriage return or escape sequences
        assert "\r" not in result
        assert "\x1b" not in result  # ESC character
        # Should contain the completion message
        assert "✓ abc-123 complete" in result
        assert "[1/5]" in result

    def test_complete_ticket_failure_newline(self):
        """Non-TTY: failed ticket should produce plain text with newline."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 2, 5)
        display.complete_ticket("abc-123", "FAILED", 2)
        
        result = output.getvalue()
        assert result.endswith("\n")
        assert "\r" not in result
        assert "\x1b" not in result
        assert "✗ abc-123 failed" in result
        assert "[3/5]" in result

    def test_complete_unknown_status(self):
        """Non-TTY: unknown status should still produce output."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 5)
        display.complete_ticket("abc-123", "UNKNOWN", 0)
        
        result = output.getvalue()
        assert result.endswith("\n")
        assert "? abc-123 unknown" in result.lower()

    def test_no_control_characters_in_non_tty(self):
        """Non-TTY mode should never produce control characters."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        # Run through a complete sequence
        for i in range(3):
            display.start_ticket(f"ticket-{i}", i, 3)
            display.complete_ticket(f"ticket-{i}", "COMPLETE", i)
        
        result = output.getvalue()
        # No escape sequences
        assert "\x1b" not in result
        # No carriage returns
        assert "\r" not in result
        # No bell characters
        assert "\x07" not in result
        # Should have newlines at end of each final line
        lines = result.strip().split("\n")
        assert len(lines) == 3

    def test_completed_counter_increments(self):
        """Non-TTY: completed counter should increment on COMPLETE."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.complete_ticket("abc-123", "COMPLETE", 0)
        assert display.completed == 1
        
        display.complete_ticket("def-456", "COMPLETE", 1)
        assert display.completed == 2

    def test_failed_counter_increments(self):
        """Non-TTY: failed counter should increment on FAILED."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.complete_ticket("abc-123", "FAILED", 0)
        assert display.failed == 1
        
        display.complete_ticket("def-456", "FAILED", 1)
        assert display.failed == 2


class TestProgressDisplayTTY:
    """Test ProgressDisplay in TTY mode (uses control characters)."""

    def test_start_ticket_clears_line(self):
        """TTY: start_ticket should use carriage return and clear."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=True)
        
        display.start_ticket("abc-123", 0, 5)
        
        result = output.getvalue()
        # Should use escape sequence to clear line
        assert "\x1b[2K" in result  # Clear line
        assert "\r" in result  # Carriage return
        assert "Processing abc-123" in result

    def test_complete_ticket_adds_newline(self):
        """TTY: complete_ticket should add newline for final output."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=True)
        
        display.start_ticket("abc-123", 0, 5)
        display.complete_ticket("abc-123", "COMPLETE", 0)
        
        result = output.getvalue()
        # Should end with newline for final output
        lines = result.split("\n")
        assert len(lines) >= 2  # At least start + complete lines

    def test_tty_intermediate_no_newline(self):
        """TTY: intermediate updates should not have newlines."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=True)
        
        display.start_ticket("abc-123", 0, 5)
        
        # Get just the start output (before complete)
        result = output.getvalue()
        # The start output itself should not end with newline
        # (only complete_ticket adds newlines in TTY mode)
        assert not result.endswith("\n") or result.count("\n") <= 1


class TestProgressDisplayCounters:
    """Test ProgressDisplay counter behavior."""

    def test_counters_accumulate(self):
        """Counters should accumulate across multiple tickets."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.complete_ticket("t1", "COMPLETE", 0)
        display.complete_ticket("t2", "FAILED", 1)
        display.complete_ticket("t3", "COMPLETE", 2)
        display.complete_ticket("t4", "FAILED", 3)
        
        assert display.completed == 2
        assert display.failed == 2
        assert display.total == 0  # total is set by start_ticket

    def test_current_ticket_cleared_on_complete(self):
        """current_ticket should be cleared when ticket completes."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 5)
        assert display.current_ticket == "abc-123"
        
        display.complete_ticket("abc-123", "COMPLETE", 0)
        assert display.current_ticket is None

    def test_iteration_number_in_output(self):
        """Output should include correct iteration number (1-indexed)."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 5)
        display.complete_ticket("abc-123", "COMPLETE", 0)
        
        result = output.getvalue()
        # iteration 0 should display as [1/5] (1-indexed)
        assert "[1/5]" in result

    def test_iteration_number_mid_sequence(self):
        """Output should include correct iteration number mid-sequence."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 2, 5)
        display.complete_ticket("abc-123", "COMPLETE", 2)
        
        result = output.getvalue()
        # iteration 2 should display as [3/5] (1-indexed)
        assert "[3/5]" in result


class TestProgressDisplayIntegration:
    """Integration tests for ProgressDisplay behavior."""

    def test_full_ticket_sequence(self):
        """Test a full sequence of ticket processing."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        tickets = [
            ("ticket-1", "COMPLETE"),
            ("ticket-2", "FAILED"),
            ("ticket-3", "COMPLETE"),
        ]
        
        for i, (ticket_id, status) in enumerate(tickets):
            display.start_ticket(ticket_id, i, len(tickets))
            display.complete_ticket(ticket_id, status, i)
        
        result = output.getvalue()
        lines = result.strip().split("\n")
        
        assert len(lines) == 3
        assert "✓ ticket-1 complete" in lines[0]
        assert "✗ ticket-2 failed" in lines[1]
        assert "✓ ticket-3 complete" in lines[2]
        assert display.completed == 2
        assert display.failed == 1

    def test_multiple_starts_no_output(self):
        """Multiple start_ticket calls without complete should not produce output."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("t1", 0, 3)
        display.start_ticket("t2", 1, 3)
        display.start_ticket("t3", 2, 3)
        
        # No output in non-TTY mode for intermediate progress
        assert output.getvalue() == ""


class TestProgressDisplayWithRealStream:
    """Test ProgressDisplay with different stream types."""

    def test_with_stderr_mock(self):
        """Test with mocked stderr-like stream."""
        output = StringIO()
        display = ProgressDisplay(output=output, is_tty=False)
        
        display.start_ticket("abc-123", 0, 1)
        display.complete_ticket("abc-123", "COMPLETE", 0)
        
        result = output.getvalue()
        assert "complete" in result  # lowercase in output
        assert "\n" in result

    def test_flush_is_called(self):
        """Display should flush output after writes."""
        output = MagicMock()
        output.isatty.return_value = False
        
        display = ProgressDisplay(output=output)
        
        display.complete_ticket("abc-123", "COMPLETE", 0)
        
        # flush should be called
        output.flush.assert_called()
