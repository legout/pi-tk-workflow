"""Ralph logging helper with levels, timestamps, context, and redaction."""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TextIO


class LogLevel(Enum):
    """Log verbosity levels for Ralph."""

    DEBUG = "debug"  # Most verbose, includes VERBOSE
    INFO = "info"  # Normal operation
    WARN = "warn"  # Warnings only
    ERROR = "error"  # Errors only

    # Legacy aliases for backward compatibility with ralph config
    VERBOSE = "debug"  # Maps to DEBUG for legacy compatibility
    QUIET = "error"  # Maps to ERROR for legacy compatibility
    NORMAL = "info"  # Maps to INFO for legacy compatibility

    @classmethod
    def from_string(cls, value: str) -> LogLevel:
        """Parse log level from string (case-insensitive)."""
        mapping = {
            "debug": cls.DEBUG,
            "verbose": cls.VERBOSE,
            "info": cls.INFO,
            "normal": cls.NORMAL,
            "warn": cls.WARN,
            "warning": cls.WARN,
            "error": cls.ERROR,
            "quiet": cls.QUIET,
        }
        return mapping.get(value.lower().strip(), cls.INFO)


def _utc_now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RedactionHelper:
    """Helper to redact sensitive or overly-large values from log output."""

    # Patterns that likely indicate sensitive data
    SENSITIVE_PATTERNS: List[str] = [
        r"api[_-]?key",
        r"apikey",
        r"token",
        r"secret",
        r"password",
        r"auth",
        r"credential",
        r"private[_-]?key",
        r"access[_-]?token",
        r"bearer",
    ]

    # Default max length for values before truncation
    DEFAULT_MAX_LENGTH: int = 1000

    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        sensitive_patterns: Optional[List[str]] = None,
        redaction_marker: str = "[REDACTED]",
        truncation_marker: str = "...[TRUNCATED]",
    ):
        self.max_length = max_length
        self.sensitive_patterns = sensitive_patterns or self.SENSITIVE_PATTERNS
        self.redaction_marker = redaction_marker
        self.truncation_marker = truncation_marker
        self._sensitive_regex = re.compile(
            "|".join(f"({p})" for p in self.sensitive_patterns),
            re.IGNORECASE,
        )

    def is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data."""
        return bool(self._sensitive_regex.search(key))

    def redact_value(self, value: Any) -> Any:
        """Redact a single value if it's sensitive or too large."""
        if value is None:
            return None

        # Convert to string for checking
        str_value = str(value)

        # Check if value itself looks like a secret (long random strings)
        if self._looks_like_secret(str_value):
            return self.redaction_marker

        # Truncate if too long
        if len(str_value) > self.max_length:
            return str_value[: self.max_length] + self.truncation_marker

        return value

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive keys and large values in a dictionary."""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            if self.is_sensitive_key(key):
                result[key] = self.redaction_marker
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                result[key] = self.redact_list(value)
            else:
                result[key] = self.redact_value(value)
        return result

    def redact_list(self, data: List[Any]) -> List[Any]:
        """Redact large values in a list."""
        result: List[Any] = []
        for item in data:
            if isinstance(item, dict):
                result.append(self.redact_dict(item))
            elif isinstance(item, list):
                result.append(self.redact_list(item))
            else:
                result.append(self.redact_value(item))
        return result

    def _looks_like_secret(self, value: str) -> bool:
        """Heuristic: check if value looks like a secret token."""
        # Skip short values
        if len(value) < 20:
            return False

        # Check for common secret patterns
        secret_indicators = [
            "sk-",  # OpenAI-style secret key
            "eyJ",  # JWT token start (base64 of {" )
            "ghp_",  # GitHub personal access token
            "gho_",
            "ghu_",
            "ghs_",
            "ghr_",
        ]
        lower = value.lower()
        for indicator in secret_indicators:
            if lower.startswith(indicator):
                return True

        # High entropy check: if mostly alphanumeric with few spaces
        # and length > 30, likely a token
        if len(value) > 30 and value.count(" ") < 2:
            alphanumeric = sum(1 for c in value if c.isalnum())
            if alphanumeric / len(value) > 0.85:
                return True

        return False


class RalphLogger:
    """Structured logger for Ralph with levels, timestamps, and context."""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        output: TextIO = sys.stderr,
        context: Optional[Dict[str, Any]] = None,
        redaction: Optional[RedactionHelper] = None,
    ):
        self.level = level
        self.output = output
        self.context = context or {}
        self.redaction = redaction or RedactionHelper()

    def with_context(self, **kwargs: Any) -> RalphLogger:
        """Create a new logger with additional context fields."""
        new_context = dict(self.context)
        new_context.update(kwargs)
        return RalphLogger(
            level=self.level,
            output=self.output,
            context=new_context,
            redaction=self.redaction,
        )

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message at the given level should be logged.

        Level hierarchy (most verbose to least):
        VERBOSE/DEBUG -> INFO/NORMAL -> WARN -> ERROR/QUIET
        """
        # Map aliases to canonical levels for comparison
        canonical_map = {
            LogLevel.VERBOSE: LogLevel.DEBUG,
            LogLevel.NORMAL: LogLevel.INFO,
            LogLevel.QUIET: LogLevel.ERROR,
        }

        level_value = canonical_map.get(level, level)
        current_value = canonical_map.get(self.level, self.level)

        severity = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARN: 30,
            LogLevel.ERROR: 40,
        }
        return severity.get(level_value, 20) >= severity.get(current_value, 20)

    def _format_message(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format a log message with timestamp, level, context, and message."""
        timestamp = _utc_now()
        parts = [timestamp, level.value.upper()]

        # Add context fields if present
        context = dict(self.context)
        if extra:
            context.update(extra)

        # Redact sensitive data
        context = self.redaction.redact_dict(context)

        # Format context as key=value pairs
        for key, value in sorted(context.items()):
            if value is not None:
                # Escape values that contain spaces
                str_value = str(value)
                if " " in str_value:
                    str_value = f'"{str_value}"'
                parts.append(f"{key}={str_value}")

        parts.append(message)
        return " | ".join(parts)

    def _log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal log method."""
        if not self._should_log(level):
            return

        formatted = self._format_message(level, message, extra)
        print(formatted, file=self.output, flush=True)

    def debug(self, message: str, **extra: Any) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, extra or None)

    def info(self, message: str, **extra: Any) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, message, extra or None)

    def warn(self, message: str, **extra: Any) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARN, message, extra or None)

    def error(self, message: str, **extra: Any) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message, extra or None)

    def log_ticket_start(
        self,
        ticket_id: str,
        mode: str = "serial",
        iteration: Optional[int] = None,
        ticket_title: Optional[str] = None,
    ) -> None:
        """Log the start of ticket processing."""
        extra: Dict[str, Any] = {"ticket": ticket_id, "mode": mode}
        if iteration is not None:
            extra["iteration"] = iteration
        if ticket_title:
            extra["ticket_title"] = ticket_title
        self.info(f"Starting ticket processing: {ticket_id}", **extra)

    def log_ticket_complete(
        self,
        ticket_id: str,
        status: str,
        mode: str = "serial",
        iteration: Optional[int] = None,
        ticket_title: Optional[str] = None,
    ) -> None:
        """Log the completion of ticket processing."""
        extra: Dict[str, Any] = {"ticket": ticket_id, "status": status, "mode": mode}
        if iteration is not None:
            extra["iteration"] = iteration
        if ticket_title:
            extra["ticket_title"] = ticket_title
        level = LogLevel.INFO if status == "COMPLETE" else LogLevel.ERROR
        self._log(level, f"Ticket processing {status.lower()}: {ticket_id}", extra)

    def log_phase_transition(
        self,
        ticket_id: str,
        from_phase: str,
        to_phase: str,
        mode: str = "serial",
    ) -> None:
        """Log a workflow phase transition."""
        self.info(
            f"Phase transition: {from_phase} -> {to_phase}",
            ticket=ticket_id,
            phase=to_phase,
            previous_phase=from_phase,
            mode=mode,
        )

    def log_tool_execution(
        self,
        ticket_id: str,
        tool_name: str,
        success: bool = True,
        mode: str = "serial",
    ) -> None:
        """Log a tool/command execution."""
        status = "success" if success else "failure"
        level = LogLevel.INFO if success else LogLevel.ERROR
        self._log(
            level,
            f"Tool execution {status}: {tool_name}",
            {"ticket": ticket_id, "tool": tool_name, "result": status, "mode": mode},
        )

    def log_decision(
        self,
        ticket_id: str,
        decision: str,
        reason: str,
        mode: str = "serial",
    ) -> None:
        """Log a decision with its rationale."""
        self.info(
            f"Decision: {decision}",
            ticket=ticket_id,
            decision=decision,
            reason=reason,
            mode=mode,
        )

    def log_error_summary(
        self,
        ticket_id: str,
        error_msg: str,
        artifact_path: Optional[str] = None,
        mode: str = "serial",
        iteration: Optional[int] = None,
        ticket_title: Optional[str] = None,
    ) -> None:
        """Log an error summary with pointers to more info."""
        extra: Dict[str, Any] = {"ticket": ticket_id, "error": error_msg, "mode": mode}
        if artifact_path:
            extra["artifact_path"] = artifact_path
        if iteration is not None:
            extra["iteration"] = iteration
        if ticket_title:
            extra["ticket_title"] = ticket_title
        self.error("Error summary", **extra)

    def log_loop_start(
        self,
        mode: str = "serial",
        max_iterations: Optional[int] = None,
        parallel_workers: Optional[int] = None,
    ) -> None:
        """Log the start of the Ralph loop."""
        extra: Dict[str, Any] = {"mode": mode, "event": "loop_start"}
        if max_iterations is not None:
            extra["max_iterations"] = max_iterations
        if parallel_workers is not None:
            extra["parallel_workers"] = parallel_workers
        self.info(f"Ralph loop started (mode={mode})", **extra)

    def log_loop_complete(
        self,
        reason: str,
        iterations_completed: int,
        mode: str = "serial",
    ) -> None:
        """Log the completion of the Ralph loop with reason."""
        extra: Dict[str, Any] = {
            "mode": mode,
            "event": "loop_complete",
            "reason": reason,
            "iterations_completed": iterations_completed,
        }
        level = LogLevel.INFO if reason == "backlog_empty" else LogLevel.WARN
        self._log(level, f"Ralph loop complete: {reason}", extra)

    def log_no_ticket_selected(
        self,
        sleep_seconds: float,
        reason: str = "no_ready_tickets",
        mode: str = "serial",
        iteration: Optional[int] = None,
    ) -> None:
        """Log when no ticket is selected and sleep is triggered."""
        extra: Dict[str, Any] = {
            "mode": mode,
            "event": "no_ticket_selected",
            "reason": reason,
            "sleep_seconds": sleep_seconds,
        }
        if iteration is not None:
            extra["iteration"] = iteration
        self.info(f"No ticket selected, sleeping for {sleep_seconds}s", **extra)

    def log_command_executed(
        self,
        ticket_id: str,
        command: str,
        exit_code: int,
        mode: str = "serial",
        iteration: Optional[int] = None,
        ticket_title: Optional[str] = None,
    ) -> None:
        """Log command execution result with sanitized command and exit code."""
        # Sanitize command for logging (remove potential secrets)
        sanitized = self._sanitize_command(command)

        extra: Dict[str, Any] = {
            "ticket": ticket_id,
            "command": sanitized,
            "exit_code": exit_code,
            "mode": mode,
            "event": "command_executed",
        }
        if iteration is not None:
            extra["iteration"] = iteration
        if ticket_title:
            extra["ticket_title"] = ticket_title

        if exit_code == 0:
            self.info(f"Command completed successfully (exit={exit_code}): {sanitized}", **extra)
        else:
            self.error(f"Command failed (exit={exit_code}): {sanitized}", **extra)

    def _sanitize_command(self, command: str) -> str:
        """Sanitize command by redacting potential sensitive values."""
        # Redact common secret patterns in command arguments
        # Handles both space-separated (--api-key value) and equals-separated (--api-key=value) formats
        patterns = [
            (r'(--api-key\s+\S+)', '--api-key [REDACTED]'),
            (r'(--api-key[=:]\S+)', '--api-key=[REDACTED]'),
            (r'(--token\s+\S+)', '--token [REDACTED]'),
            (r'(--token[=:]\S+)', '--token=[REDACTED]'),
            (r'(--secret\s+\S+)', '--secret [REDACTED]'),
            (r'(--secret[=:]\S+)', '--secret=[REDACTED]'),
            (r'(--password\s+\S+)', '--password [REDACTED]'),
            (r'(--password[=:]\S+)', '--password=[REDACTED]'),
            (r'(sk-\w+)', '[REDACTED]'),  # OpenAI-style keys
            (r'(eyJ[\w-]*\.eyJ[\w-]*\.[\w-]*)', '[REDACTED]'),  # JWT tokens (header.payload.signature)
            (r'(ghp_\w+)', '[REDACTED]'),  # GitHub tokens
        ]

        result = command
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def log_batch_selected(
        self,
        tickets: List[str],
        component_tags: Dict[str, List[str]],
        reason: str = "component_diversity",
        mode: str = "parallel",
        iteration: Optional[int] = None,
    ) -> None:
        """Log batch selection with ticket IDs and their component tags.

        Args:
            tickets: List of selected ticket IDs
            component_tags: Dict mapping ticket_id -> list of component tags
            reason: Selection rationale (component_diversity, fallback, etc.)
            mode: Execution mode
            iteration: Optional iteration number
        """
        extra: Dict[str, Any] = {
            "event": "batch_selected",
            "mode": mode,
            "ticket_count": len(tickets),
            "tickets": tickets,
            "reason": reason,
        }
        if iteration is not None:
            extra["iteration"] = iteration

        # Add component tag info for each ticket
        for ticket, tags in component_tags.items():
            if tags:
                extra[f"{ticket}_components"] = tags
            else:
                extra[f"{ticket}_components"] = ["untagged"]

        tag_summary = ", ".join(
            f"{ticket}({','.join(tags) if tags else 'untagged'})"
            for ticket, tags in component_tags.items()
        )
        self.info(f"Selected batch: {tag_summary}", **extra)

    def log_worktree_operation(
        self,
        ticket_id: str,
        operation: str,  # "add" or "remove"
        worktree_path: str,
        success: bool,
        error: Optional[str] = None,
        mode: str = "parallel",
        iteration: Optional[int] = None,
        ticket_title: Optional[str] = None,
    ) -> None:
        """Log worktree add/remove operations with success/failure status.

        Args:
            ticket_id: The ticket being processed
            operation: "add" or "remove"
            worktree_path: Path to the worktree
            success: Whether the operation succeeded
            error: Optional error message on failure
            mode: Execution mode
            iteration: Optional iteration number
            ticket_title: Optional ticket title for verbose logging
        """
        extra: Dict[str, Any] = {
            "event": "worktree_operation",
            "ticket": ticket_id,
            "operation": operation,
            "worktree_path": worktree_path,
            "success": success,
            "mode": mode,
        }
        if iteration is not None:
            extra["iteration"] = iteration
        if error:
            extra["error"] = error
        if ticket_title:
            extra["ticket_title"] = ticket_title

        status = "success" if success else "failed"
        msg = f"Worktree {operation} {status}: {worktree_path}"
        if error:
            msg = f"{msg} - {error}"

        level = LogLevel.INFO if success else LogLevel.ERROR
        self._log(level, msg, extra)


def create_logger(
    level: Optional[LogLevel] = None,
    output: TextIO = sys.stderr,
    ticket_id: Optional[str] = None,
    ticket_title: Optional[str] = None,
    iteration: Optional[int] = None,
    mode: str = "serial",
) -> RalphLogger:
    """Factory function to create a configured RalphLogger.

    Args:
        level: Minimum log level (defaults to INFO)
        output: Output stream (defaults to stderr)
        ticket_id: Optional ticket ID for context
        ticket_title: Optional ticket title for context (shown in verbose logs)
        iteration: Optional iteration number for context
        mode: Execution mode (serial/parallel)

    Returns:
        Configured RalphLogger instance
    """
    context: Dict[str, Any] = {"mode": mode}
    if ticket_id:
        context["ticket"] = ticket_id
    if ticket_title:
        context["ticket_title"] = ticket_title
    if iteration is not None:
        context["iteration"] = iteration

    return RalphLogger(level=level or LogLevel.INFO, output=output, context=context)
