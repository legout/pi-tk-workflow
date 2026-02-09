"""Tests for the Ralph logger module."""

from __future__ import annotations

import io
import re
from unittest.mock import patch

import pytest

from tf.logger import (
    LogLevel,
    RalphLogger,
    RedactionHelper,
    _utc_now,
    create_logger,
)


class TestLogLevel:
    """Test LogLevel enum."""

    def test_from_string_debug(self):
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG

    def test_from_string_info(self):
        assert LogLevel.from_string("info") == LogLevel.INFO
        assert LogLevel.from_string("INFO") == LogLevel.INFO

    def test_from_string_warn(self):
        assert LogLevel.from_string("warn") == LogLevel.WARN
        assert LogLevel.from_string("warning") == LogLevel.WARN
        assert LogLevel.from_string("WARN") == LogLevel.WARN

    def test_from_string_error(self):
        assert LogLevel.from_string("error") == LogLevel.ERROR
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR

    def test_from_string_defaults_to_info(self):
        assert LogLevel.from_string("unknown") == LogLevel.INFO
        assert LogLevel.from_string("") == LogLevel.INFO


class TestRedactionHelper:
    """Test RedactionHelper class."""

    def test_is_sensitive_key_detects_api_key(self):
        helper = RedactionHelper()
        assert helper.is_sensitive_key("api_key")
        assert helper.is_sensitive_key("API_KEY")
        assert helper.is_sensitive_key("my_api_key")

    def test_is_sensitive_key_detects_token(self):
        helper = RedactionHelper()
        assert helper.is_sensitive_key("token")
        assert helper.is_sensitive_key("access_token")
        assert helper.is_sensitive_key("TOKEN")

    def test_is_sensitive_key_detects_secret(self):
        helper = RedactionHelper()
        assert helper.is_sensitive_key("secret")
        assert helper.is_sensitive_key("client_secret")

    def test_is_sensitive_key_allows_safe_keys(self):
        helper = RedactionHelper()
        assert not helper.is_sensitive_key("name")
        assert not helper.is_sensitive_key("id")
        assert not helper.is_sensitive_key("count")

    def test_redact_value_truncates_long_strings(self):
        helper = RedactionHelper(max_length=10)
        # Use a string that won't be detected as a secret (includes spaces)
        result = helper.redact_value("hello world this is a long text with spaces")
        assert "[TRUNCATED]" in result
        assert len(result) < 60

    def test_redact_value_redacts_secrets(self):
        helper = RedactionHelper()
        # OpenAI-style key (must be long enough for high entropy check or match pattern)
        assert helper.redact_value("sk-abc123xyzabcdefghijklmnopqrstuvwxyz") == "[REDACTED]"
        # JWT token (base64 encoded JSON)
        assert helper.redact_value("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature") == "[REDACTED]"
        # GitHub token
        assert helper.redact_value("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx") == "[REDACTED]"

    def test_redact_value_preserves_short_strings(self):
        helper = RedactionHelper()
        assert helper.redact_value("hello") == "hello"
        assert helper.redact_value("test value") == "test value"

    def test_redact_dict_redacts_sensitive_keys(self):
        helper = RedactionHelper()
        data = {"name": "test", "api_key": "secret123", "count": 42}
        result = helper.redact_dict(data)
        assert result["name"] == "test"
        assert result["api_key"] == "[REDACTED]"
        assert result["count"] == 42

    def test_redact_dict_handles_nested_dicts(self):
        helper = RedactionHelper()
        data = {"outer": {"api_key": "secret", "value": "ok"}}
        result = helper.redact_dict(data)
        assert result["outer"]["api_key"] == "[REDACTED]"
        assert result["outer"]["value"] == "ok"

    def test_redact_list_handles_nested_structures(self):
        helper = RedactionHelper()
        data = [{"api_key": "secret"}, "normal", ["nested"]]
        result = helper.redact_list(data)
        assert result[0]["api_key"] == "[REDACTED]"
        assert result[1] == "normal"
        assert result[2] == ["nested"]

    def test_looks_like_secret_detects_high_entropy(self):
        helper = RedactionHelper()
        # Long alphanumeric string with few spaces
        assert helper._looks_like_secret("a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0")
        # Normal text
        assert not helper._looks_like_secret("This is a normal sentence with spaces")


class TestRalphLogger:
    """Test RalphLogger class."""

    def test_debug_logs_when_level_is_debug(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.DEBUG, output=output)
        logger.debug("test message")
        assert "DEBUG" in output.getvalue()
        assert "test message" in output.getvalue()

    def test_debug_does_not_log_when_level_is_info(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.debug("test message")
        assert output.getvalue() == ""

    def test_info_logs_when_level_is_info(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test message")
        assert "INFO" in output.getvalue()
        assert "test message" in output.getvalue()

    def test_warn_logs_to_stderr(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.warn("warning message")
        content = output.getvalue()
        assert "WARN" in content
        assert "warning message" in content

    def test_error_logs_to_stderr(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.error("error message")
        content = output.getvalue()
        assert "ERROR" in content
        assert "error message" in content

    def test_includes_timestamp(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test")
        content = output.getvalue()
        # Check for ISO timestamp format
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", content)

    def test_includes_context_fields(self):
        output = io.StringIO()
        logger = RalphLogger(
            level=LogLevel.INFO,
            output=output,
            context={"ticket": "abc-123", "mode": "serial"},
        )
        logger.info("test message")
        content = output.getvalue()
        assert "ticket=abc-123" in content
        assert "mode=serial" in content

    def test_with_context_creates_new_logger(self):
        output = io.StringIO()
        logger = RalphLogger(
            level=LogLevel.INFO,
            output=output,
            context={"ticket": "abc-123"},
        )
        new_logger = logger.with_context(iteration=5)
        new_logger.info("test")
        content = output.getvalue()
        assert "ticket=abc-123" in content
        assert "iteration=5" in content

    def test_extra_fields_in_log_call(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", custom_field="value")
        content = output.getvalue()
        assert "custom_field=value" in content

    def test_log_ticket_start(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_start("abc-123", mode="serial", iteration=1)
        content = output.getvalue()
        assert "Starting ticket" in content
        assert "ticket=abc-123" in content
        assert "mode=serial" in content
        assert "iteration=1" in content

    def test_log_ticket_complete_success(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_complete("abc-123", "COMPLETE", mode="serial")
        content = output.getvalue()
        assert "COMPLETE" in content
        assert "ticket=abc-123" in content
        assert "status=COMPLETE" in content

    def test_log_ticket_complete_failure(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_ticket_complete("abc-123", "FAILED", mode="serial")
        content = output.getvalue()
        assert "ERROR" in content
        assert "status=FAILED" in content

    def test_log_phase_transition(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_phase_transition("abc-123", "research", "implement", mode="serial")
        content = output.getvalue()
        assert "Phase transition" in content
        assert "research -> implement" in content

    def test_log_tool_execution_success(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_tool_execution("abc-123", "git add", success=True)
        content = output.getvalue()
        assert "Tool execution success" in content
        # Values with spaces are quoted
        assert 'tool="git add"' in content

    def test_log_tool_execution_failure(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_tool_execution("abc-123", "git add", success=False)
        content = output.getvalue()
        assert "ERROR" in content
        assert "result=failure" in content

    def test_log_decision(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_decision("abc-123", "skip ticket", "dependencies not met")
        content = output.getvalue()
        assert "Decision: skip ticket" in content
        # Values with spaces are quoted
        assert 'reason="dependencies not met"' in content

    def test_log_error_summary(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.log_error_summary("abc-123", "Command failed", "/path/to/artifact")
        content = output.getvalue()
        assert "ERROR" in content
        assert "Error summary" in content
        # Values with spaces are quoted
        assert 'error="Command failed"' in content
        assert "artifact_path=/path/to/artifact" in content

    def test_redaction_in_log_output(self):
        output = io.StringIO()
        logger = RalphLogger(level=LogLevel.INFO, output=output)
        logger.info("test", api_key="secret123")
        content = output.getvalue()
        assert "[REDACTED]" in content
        assert "secret123" not in content


class TestCreateLogger:
    """Test create_logger factory function."""

    def test_creates_logger_with_defaults(self):
        logger = create_logger()
        assert logger.level == LogLevel.INFO
        assert logger.context == {"mode": "serial"}

    def test_creates_logger_with_ticket(self):
        logger = create_logger(ticket_id="abc-123")
        assert logger.context["ticket"] == "abc-123"

    def test_creates_logger_with_iteration(self):
        logger = create_logger(iteration=5)
        assert logger.context["iteration"] == 5

    def test_creates_logger_with_mode(self):
        logger = create_logger(mode="parallel")
        assert logger.context["mode"] == "parallel"

    def test_creates_logger_with_custom_level(self):
        logger = create_logger(level=LogLevel.DEBUG)
        assert logger.level == LogLevel.DEBUG


class TestUtcNow:
    """Test _utc_now helper."""

    def test_returns_iso_format(self):
        result = _utc_now()
        # Check format: YYYY-MM-DDTHH:MM:SSZ
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result)

    def test_returns_utc_time(self):
        with patch("tf.logger.datetime") as mock_datetime:
            mock_now = mock_datetime.now
            mock_now.return_value.strftime.return_value = "2024-01-15T10:30:00Z"
            result = _utc_now()
            mock_datetime.now.assert_called_once()
            assert result == "2024-01-15T10:30:00Z"
