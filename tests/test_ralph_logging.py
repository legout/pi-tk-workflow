"""Tests for Ralph logging lifecycle events (serial + parallel selection).

These tests validate the new logging helper formatting and key lifecycle logs
without executing real `pi` or modifying `.tickets/`.
"""

from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from tf.logger import LogLevel, RalphLogger, RedactionHelper, create_logger


class TestLoggerFormattingAndFiltering:
    """Test logger formatting and level filtering."""

    def test_timestamp_format_is_iso8601_utc(self):
        """Verify timestamps are in ISO 8601 UTC format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test message")
        content = output.getvalue()
        # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", content)
        assert match is not None, f"Timestamp not found in: {content}"
        timestamp = match.group(1)
        assert len(timestamp) == 20  # YYYY-MM-DDTHH:MM:SSZ

    def test_log_level_filtering_hierarchy(self):
        """Test that log levels filter correctly (DEBUG < INFO < WARN < ERROR)."""
        # DEBUG level shows all
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warn("warn msg")
        logger.error("error msg")
        content = output.getvalue()
        assert "debug msg" in content
        assert "info msg" in content
        assert "warn msg" in content
        assert "error msg" in content

        # INFO level shows INFO and above
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warn("warn msg")
        logger.error("error msg")
        content = output.getvalue()
        assert "debug msg" not in content
        assert "info msg" in content
        assert "warn msg" in content
        assert "error msg" in content

        # WARN level shows WARN and above
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.WARN, output=output)
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warn("warn msg")
        logger.error("error msg")
        content = output.getvalue()
        assert "debug msg" not in content
        assert "info msg" not in content
        assert "warn msg" in content
        assert "error msg" in content

        # ERROR level shows only ERROR
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.ERROR, output=output)
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warn("warn msg")
        logger.error("error msg")
        content = output.getvalue()
        assert "debug msg" not in content
        assert "info msg" not in content
        assert "warn msg" not in content
        assert "error msg" in content

    def test_context_fields_sorted_alphabetically(self):
        """Verify context fields appear in sorted order."""
        output = io.StringIO()
        logger = RalphLogger(
            level=LogLevel.INFO,
            output=output,
            context={"zebra": "z", "alpha": "a", "mike": "m"},
        )
        logger.info("test")
        content = output.getvalue()
        # Fields should appear in alphabetical order: alpha, mike, zebra
        alpha_pos = content.find("alpha=a")
        mike_pos = content.find("mike=m")
        zebra_pos = content.find("zebra=z")
        assert alpha_pos < mike_pos < zebra_pos, f"Fields not sorted: {content}"

    def test_values_with_spaces_are_quoted(self):
        """Verify values containing spaces are wrapped in quotes."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", my_message="hello world")
        content = output.getvalue()
        assert 'my_message="hello world"' in content

    def test_log_format_structure(self):
        """Verify the overall log format: TIMESTAMP | LEVEL | [context] | message"""
        output = io.StringIO()
        logger = RalphLogger(
            level=LogLevel.INFO,
            output=output,
            context={"ticket": "abc-123"},
        )
        logger.info("test message")
        content = output.getvalue().strip()
        # Format: TIMESTAMP | LEVEL | context... | message
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \| INFO \| .*test message$"
        assert re.match(pattern, content), f"Format mismatch: {content}"


class TestRedactionInLogging:
    """Test redaction functionality in logger output."""

    def test_api_key_redacted_in_log_output(self):
        """Verify API keys are redacted in log output."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", api_key="sk-abc123secret")
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "sk-abc123secret" not in content

    def test_token_redacted_in_log_output(self):
        """Verify tokens are redacted in log output."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", access_token="ghp_xxxxxxxxxxxxxxxx")
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "ghp_xxxxxxxxxxxxxxxx" not in content

    def test_nested_dict_redaction(self):
        """Verify nested dictionaries are properly redacted."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", config={"api_key": "secret", "name": "test"})
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "secret" not in content
        # Dict is serialized as a string, so check it's present
        assert "config=" in content
        assert "'name': 'test'" in content or "'name': \"test\"" in content

    def test_jwt_token_redaction(self):
        """Verify JWT tokens are redacted."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        logger.info("test", token=jwt)
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "eyJhbGci" not in content

    def test_long_value_truncation(self):
        """Verify long values are truncated or redacted."""
        output = io.StringIO()
        redaction = RedactionHelper(max_length=50)
        logger = RalphLogger(level=LogLevel.INFO, output=output, redaction=redaction)
        # Use a string with spaces to avoid high-entropy detection
        long_value = "hello world " * 10  # Long but not high entropy
        logger.info("test", data=long_value)
        content = output.getvalue()
        # Either truncated or redacted (high entropy strings get redacted)
        assert "[TRUNCATED]" in content or "[REDACTED]" in content


class TestSerialLoopDecisionLogging:
    """Test serial loop decision logging (no ready tickets / selected ticket)."""

    def test_log_no_ticket_selected_format(self):
        """Verify the format of 'no ticket selected' log entry."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output, context={"mode": "serial"})
        logger.log_no_ticket_selected(
            sleep_seconds=5.0,
            reason="no_ready_tickets",
            mode="serial",
            iteration=3,
        )
        content = output.getvalue()
        assert "No ticket selected, sleeping for 5.0s" in content
        assert "event=no_ticket_selected" in content
        assert "reason=no_ready_tickets" in content
        assert "mode=serial" in content
        assert "iteration=3" in content
        assert "sleep_seconds=5.0" in content

    def test_log_no_ticket_selected_without_iteration(self):
        """Verify 'no ticket selected' works without iteration."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_no_ticket_selected(
            sleep_seconds=10.0,
            reason="backlog_empty",
            mode="serial",
        )
        content = output.getvalue()
        assert "No ticket selected, sleeping for 10.0s" in content
        assert "event=no_ticket_selected" in content
        assert "reason=backlog_empty" in content
        assert "iteration" not in content

    def test_log_ticket_start_format(self):
        """Verify the format of 'ticket start' log entry."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_start("pt-abc123", mode="serial", iteration=5)
        content = output.getvalue()
        assert "Starting ticket processing: pt-abc123" in content
        assert "ticket=pt-abc123" in content
        assert "mode=serial" in content
        assert "iteration=5" in content

    def test_log_ticket_start_without_iteration(self):
        """Verify 'ticket start' works without iteration."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_start("pt-xyz789", mode="serial")
        content = output.getvalue()
        assert "Starting ticket processing: pt-xyz789" in content
        assert "ticket=pt-xyz789" in content
        assert "iteration" not in content

    def test_log_ticket_complete_success(self):
        """Verify successful ticket completion log format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_complete("pt-abc123", "COMPLETE", mode="serial", iteration=5)
        content = output.getvalue()
        assert "Ticket processing complete: pt-abc123" in content
        assert "ticket=pt-abc123" in content
        assert "status=COMPLETE" in content
        assert "mode=serial" in content
        assert "iteration=5" in content
        assert "INFO" in content  # Success is INFO level

    def test_log_ticket_complete_failure(self):
        """Verify failed ticket completion log format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_complete("pt-abc123", "FAILED", mode="serial", iteration=5)
        content = output.getvalue()
        assert "Ticket processing failed: pt-abc123" in content
        assert "ticket=pt-abc123" in content
        assert "status=FAILED" in content
        assert "mode=serial" in content
        assert "iteration=5" in content
        assert "ERROR" in content  # Failure is ERROR level

    def test_log_loop_start_serial(self):
        """Verify loop start log for serial mode."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_loop_start(mode="serial", max_iterations=50)
        content = output.getvalue()
        assert "Ralph loop started (mode=serial)" in content
        assert "mode=serial" in content
        assert "event=loop_start" in content
        assert "max_iterations=50" in content
        assert "parallel_workers" not in content

    def test_log_loop_complete_backlog_empty(self):
        """Verify loop complete log when backlog is empty."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_loop_complete(
            reason="backlog_empty",
            iterations_completed=10,
            mode="serial",
        )
        content = output.getvalue()
        assert "Ralph loop complete: backlog_empty" in content
        assert "reason=backlog_empty" in content
        assert "iterations_completed=10" in content
        assert "mode=serial" in content
        assert "INFO" in content  # Normal completion is INFO

    def test_log_loop_complete_max_iterations(self):
        """Verify loop complete log when max iterations reached."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_loop_complete(
            reason="max_iterations_reached",
            iterations_completed=50,
            mode="serial",
        )
        content = output.getvalue()
        assert "Ralph loop complete: max_iterations_reached" in content
        assert "reason=max_iterations_reached" in content
        assert "WARN" in content  # Max iterations is a warning


class TestParallelLoopDecisionLogging:
    """Test parallel loop decision logging (batch selection)."""

    def test_log_batch_selected_format(self):
        """Verify batch selection log format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        component_tags = {
            "pt-abc123": ["component:api", "component:cli"],
            "pt-def456": ["component:workflow"],
        }
        logger.log_batch_selected(
            tickets=["pt-abc123", "pt-def456"],
            component_tags=component_tags,
            reason="component_diversity",
            mode="parallel",
            iteration=2,
        )
        content = output.getvalue()
        assert "Selected batch:" in content
        assert "pt-abc123" in content
        assert "pt-def456" in content
        assert "event=batch_selected" in content
        assert "mode=parallel" in content
        assert "reason=component_diversity" in content
        assert "ticket_count=2" in content
        assert "iteration=2" in content

    def test_log_batch_selected_fallback(self):
        """Verify batch selection log for fallback case."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        component_tags = {"pt-abc123": []}
        logger.log_batch_selected(
            tickets=["pt-abc123"],
            component_tags=component_tags,
            reason="fallback",
            mode="parallel",
            iteration=0,
        )
        content = output.getvalue()
        assert "reason=fallback" in content
        assert "ticket_count=1" in content

    def test_log_batch_selected_with_untagged(self):
        """Verify batch selection handles untagged tickets."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        component_tags = {
            "pt-abc123": [],  # Empty = untagged
            "pt-def456": ["component:tests"],
        }
        logger.log_batch_selected(
            tickets=["pt-abc123", "pt-def456"],
            component_tags=component_tags,
            reason="component_diversity",
            mode="parallel",
        )
        content = output.getvalue()
        # List values are serialized as Python list representation
        assert "pt-abc123_components=" in content
        assert "untagged" in content
        assert "pt-def456_components=" in content
        assert "component:tests" in content

    def test_log_worktree_operation_add_success(self):
        """Verify worktree add success log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_worktree_operation(
            ticket_id="pt-abc123",
            operation="add",
            worktree_path="/path/to/worktree/pt-abc123",
            success=True,
            mode="parallel",
            iteration=3,
        )
        content = output.getvalue()
        assert "Worktree add success:" in content
        assert "event=worktree_operation" in content
        assert "ticket=pt-abc123" in content
        assert "operation=add" in content
        assert "worktree_path=/path/to/worktree/pt-abc123" in content
        assert "success=True" in content
        assert "INFO" in content

    def test_log_worktree_operation_remove_failure(self):
        """Verify worktree remove failure log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_worktree_operation(
            ticket_id="pt-abc123",
            operation="remove",
            worktree_path="/path/to/worktree/pt-abc123",
            success=False,
            error="worktree is locked",
            mode="parallel",
            iteration=3,
        )
        content = output.getvalue()
        assert "Worktree remove failed:" in content
        assert "worktree is locked" in content
        assert "success=False" in content
        # Error value is quoted because it contains spaces
        assert 'error="worktree is locked"' in content
        assert "ERROR" in content


class TestCommandExecutionLogging:
    """Test command execution logging with sanitization."""

    def test_log_command_executed_success(self):
        """Verify successful command execution log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_command_executed(
            ticket_id="pt-abc123",
            command="pi -p '/tf pt-abc123'",
            exit_code=0,
            mode="serial",
            iteration=2,
        )
        content = output.getvalue()
        assert "Command completed successfully (exit=0)" in content
        assert "ticket=pt-abc123" in content
        assert "exit_code=0" in content
        assert "event=command_executed" in content
        assert "INFO" in content

    def test_log_command_executed_failure(self):
        """Verify failed command execution log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_command_executed(
            ticket_id="pt-abc123",
            command="pi -p '/tf pt-abc123'",
            exit_code=1,
            mode="serial",
            iteration=2,
        )
        content = output.getvalue()
        assert "Command failed (exit=1)" in content
        assert "exit_code=1" in content
        assert "ERROR" in content

    def test_log_command_sanitization_api_key(self):
        """Verify API keys are sanitized in command logs."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_command_executed(
            ticket_id="pt-abc123",
            command="pi --api-key sk-abc123secret '/tf pt-abc123'",
            exit_code=0,
            mode="serial",
        )
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "sk-abc123secret" not in content

    def test_log_command_sanitization_token_equals(self):
        """Verify token= format is sanitized."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_command_executed(
            ticket_id="pt-abc123",
            command="pi --token=ghp_xxxxxxxx '/tf pt-abc123'",
            exit_code=0,
            mode="serial",
        )
        content = output.getvalue()
        assert "--token=[REDACTED]" in content
        assert "ghp_xxxxxxxx" not in content


class TestErrorSummaryLogging:
    """Test error summary logging."""

    def test_log_error_summary_with_artifact_path(self):
        """Verify error summary with artifact path."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_error_summary(
            ticket_id="pt-abc123",
            error_msg="Command failed with exit code 1",
            artifact_path=".tf/knowledge/tickets/pt-abc123",
            mode="serial",
            iteration=5,
        )
        content = output.getvalue()
        assert "Error summary" in content
        assert "ticket=pt-abc123" in content
        # Error value is quoted because it contains spaces
        assert 'error="Command failed with exit code 1"' in content
        assert "artifact_path=.tf/knowledge/tickets/pt-abc123" in content
        assert "mode=serial" in content
        assert "iteration=5" in content
        assert "ERROR" in content

    def test_log_error_summary_without_artifact_path(self):
        """Verify error summary without artifact path."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_error_summary(
            ticket_id="pt-abc123",
            error_msg="Unexpected error",
            mode="serial",
        )
        content = output.getvalue()
        assert "Error summary" in content
        assert "artifact_path" not in content


class TestDecisionLogging:
    """Test decision logging."""

    def test_log_decision_format(self):
        """Verify decision log format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_decision(
            ticket_id="pt-abc123",
            decision="skip ticket",
            reason="dependencies not met - waiting on pt-def456",
            mode="serial",
        )
        content = output.getvalue()
        assert "Decision: skip ticket" in content
        assert "ticket=pt-abc123" in content
        # Values with spaces are quoted
        assert 'decision="skip ticket"' in content
        assert 'reason="dependencies not met - waiting on pt-def456"' in content
        assert "mode=serial" in content


class TestPhaseTransitionLogging:
    """Test phase transition logging."""

    def test_log_phase_transition_format(self):
        """Verify phase transition log format."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_phase_transition(
            ticket_id="pt-abc123",
            from_phase="research",
            to_phase="implement",
            mode="serial",
        )
        content = output.getvalue()
        assert "Phase transition: research -> implement" in content
        assert "ticket=pt-abc123" in content
        assert "phase=implement" in content
        assert "previous_phase=research" in content
        assert "mode=serial" in content


class TestToolExecutionLogging:
    """Test tool execution logging."""

    def test_log_tool_execution_success(self):
        """Verify successful tool execution log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_tool_execution(
            ticket_id="pt-abc123",
            tool_name="git add",
            success=True,
            mode="serial",
        )
        content = output.getvalue()
        assert "Tool execution success: git add" in content
        assert 'tool="git add"' in content
        assert "result=success" in content
        assert "INFO" in content

    def test_log_tool_execution_failure(self):
        """Verify failed tool execution log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_tool_execution(
            ticket_id="pt-abc123",
            tool_name="git push",
            success=False,
            mode="serial",
        )
        content = output.getvalue()
        assert "Tool execution failure: git push" in content
        assert "result=failure" in content
        assert "ERROR" in content


class TestCreateLoggerFactory:
    """Test create_logger factory function."""

    def test_create_logger_with_all_context(self):
        """Verify factory creates logger with full context."""
        logger = create_logger(
            level=LogLevel.DEBUG,
            ticket_id="pt-abc123",
            iteration=5,
            mode="parallel",
        )
        assert logger.level == LogLevel.DEBUG
        assert logger.context["ticket"] == "pt-abc123"
        assert logger.context["iteration"] == 5
        assert logger.context["mode"] == "parallel"

    def test_create_logger_defaults(self):
        """Verify factory creates logger with sensible defaults."""
        logger = create_logger()
        assert logger.level == LogLevel.INFO
        assert logger.context == {"mode": "serial"}


class TestTicketTitleLogging:
    """Test ticket_title field in Ralph logging output."""

    def test_ticket_title_appears_in_log_output(self):
        """Verify ticket_title appears in verbose log output when provided."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_start(
            ticket_id="pt-abc123",
            ticket_title="Fix authentication bug",
            mode="serial",
            iteration=1,
        )
        content = output.getvalue()
        assert 'ticket_title="Fix authentication bug"' in content
        assert "pt-abc123" in content

    def test_ticket_title_appears_in_ticket_complete(self):
        """Verify ticket_title appears in ticket completion log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_complete(
            ticket_id="pt-abc123",
            status="COMPLETE",
            ticket_title="Fix authentication bug",
            mode="serial",
        )
        content = output.getvalue()
        assert 'ticket_title="Fix authentication bug"' in content
        assert "status=COMPLETE" in content

    def test_ticket_title_appears_in_command_executed(self):
        """Verify ticket_title appears in command execution log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_command_executed(
            ticket_id="pt-abc123",
            command="pi -p '/tf pt-abc123'",
            exit_code=0,
            ticket_title="Fix authentication bug",
            mode="serial",
        )
        content = output.getvalue()
        assert 'ticket_title="Fix authentication bug"' in content
        assert "exit_code=0" in content

    def test_ticket_title_appears_in_error_summary(self):
        """Verify ticket_title appears in error summary log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_error_summary(
            ticket_id="pt-abc123",
            error_msg="Command failed",
            ticket_title="Fix authentication bug",
            mode="serial",
        )
        content = output.getvalue()
        assert 'ticket_title="Fix authentication bug"' in content
        assert 'error="Command failed"' in content

    def test_ticket_title_appears_in_worktree_operation(self):
        """Verify ticket_title appears in worktree operation log."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_worktree_operation(
            ticket_id="pt-abc123",
            operation="add",
            worktree_path="/path/to/worktree",
            success=True,
            ticket_title="Fix authentication bug",
            mode="parallel",
        )
        content = output.getvalue()
        assert 'ticket_title="Fix authentication bug"' in content
        assert "operation=add" in content

    def test_graceful_fallback_when_title_unavailable(self):
        """Verify graceful fallback when ticket_title is not provided."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_start(
            ticket_id="pt-abc123",
            mode="serial",
        )
        content = output.getvalue()
        assert "ticket_title" not in content
        assert "pt-abc123" in content
        assert "Starting ticket processing" in content

    def test_ticket_title_not_included_when_none(self):
        """Verify ticket_title field is omitted when explicitly set to None."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_complete(
            ticket_id="pt-abc123",
            status="FAILED",
            ticket_title=None,
            mode="serial",
        )
        content = output.getvalue()
        assert "ticket_title" not in content
        assert "status=FAILED" in content

    def test_ticket_title_with_special_characters(self):
        """Verify ticket_title handles titles with special characters."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_start(
            ticket_id="pt-abc123",
            ticket_title='Fix "broken" authentication (urgent!)',
            mode="serial",
        )
        content = output.getvalue()
        # Values with spaces/quotes should be wrapped in quotes
        assert 'ticket_title=' in content
        assert "Fix" in content
        assert "broken" in content

    def test_sensitive_ticket_title_not_redacted_by_default(self):
        """Verify normal ticket titles are not redacted."""
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.log_ticket_start(
            ticket_id="pt-abc123",
            ticket_title="Implement API key validation",
            mode="serial",
        )
        content = output.getvalue()
        # "API key" in the title should NOT trigger redaction
        # (redaction is based on field name, not value content)
        assert "Implement API key validation" in content
        assert "[REDACTED]" not in content


class TestCapturedStderrOutput:
    """Test that logs go to stderr (captured output)."""

    def test_logger_writes_to_specified_output(self):
        """Verify logger writes to the specified output stream."""
        stderr_capture = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=stderr_capture)
        logger.info("test message")
        assert "test message" in stderr_capture.getvalue()

    def test_logger_default_is_stderr(self):
        """Verify default output is sys.stderr."""
        import sys
        logger = RalphLogger(level=LogLevel.INFO)
        assert logger.output is sys.stderr
