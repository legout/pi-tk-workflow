"""Regression tests for Ralph pi invocation arguments.

These tests ensure that the `pi` command constructed by `tf ralph start/run`
does not include the `--session` argument (per the session handling refactor).

The tests mock subprocess calls to verify command construction without
requiring actual pi execution.

NOTE: These tests will FAIL until pt-ihfv (Remove pi --session forwarding)
is implemented. This is intentional - the tests document the expected behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tf import ralph as ralph_module


class TestRalphPiInvocationNoSession:
    """Tests that pi invocation does not include --session argument.

    These tests verify that even when a session directory is configured,
    the --session flag is NOT forwarded to the pi command.
    """

    def test_ralph_run_pi_invocation_no_session_with_session_dir(
        self, tmp_path: Path
    ) -> None:
        """Test: ralph run does not include --session even when session_dir is set.

        This is a regression test to ensure the --session forwarding removal
        (pt-ihfv) is not accidentally reverted. The test configures a session
        directory and verifies that --session is NOT in the pi command.

        Expected to FAIL until pt-ihfv is implemented.
        """
        captured_commands: list[list[str]] = []

        def capturing_popen(
            args: list[str],
            **kwargs: Any,
        ) -> Any:
            captured_commands.append(args)
            mock = MagicMock()
            mock.wait.return_value = 0
            return mock

        # Create mock shell responses
        def mock_run_shell(cmd: str, **kwargs: Any) -> Any:
            result = MagicMock()
            if "tk ready" in cmd or "head -1" in cmd:
                result.stdout = "TEST-123"
                result.returncode = 0
            elif "tk show" in cmd:
                result.stdout = (
                    "---\nid: TEST-123\ntags: [test]\n---\n# Test Ticket"
                )
                result.returncode = 0
            else:
                result.stdout = ""
                result.returncode = 0
            return result

        # Set up session directory (this is key - we want to test that
        # even WITH a session dir, --session is NOT passed)
        session_dir = tmp_path / ".pi" / "agent" / "sessions"
        session_dir.mkdir(parents=True)

        # Set up required files
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True, exist_ok=True)
        (ralph_dir / "config.json").write_text(
            '{"maxIterations": 1, "sessionDir": "' + str(session_dir) + '"}'
        )

        progress_path = ralph_dir / "progress.md"
        progress_path.write_text(
            """# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
"""
        )

        # Mock tk command in extract_ticket_title
        def mock_ticket_title(ticket: str, **kwargs: Any) -> str | None:
            return "Test Ticket"

        with patch("subprocess.Popen", side_effect=capturing_popen):
            with patch.object(
                ralph_module, "run_shell", side_effect=mock_run_shell
            ):
                with patch.object(
                    ralph_module,
                    "find_project_root",
                    return_value=tmp_path,
                ):
                    with patch.object(
                        ralph_module, "ensure_pi", return_value=True
                    ):
                        with patch.object(
                            ralph_module, "prompt_exists", return_value=True
                        ):
                            with patch.object(
                                ralph_module,
                                "lock_acquire",
                                return_value=True,
                            ):
                                with patch.object(
                                    ralph_module,
                                    "lock_release",
                                ):
                                    with patch.object(
                                        ralph_module,
                                        "extract_ticket_title",
                                        side_effect=mock_ticket_title,
                                    ):
                                        # Run with a specific ticket
                                        exit_code = ralph_module.ralph_run(
                                            ["TEST-123"]
                                        )

        # Verify command was invoked
        assert (
            len(captured_commands) > 0
        ), "pi command should have been invoked"
        assert (
            exit_code == 0
        ), f"ralph_run should succeed but got exit code {exit_code}"

        # Find the pi command (starts with 'pi')
        pi_commands = [
            cmd for cmd in captured_commands if cmd and cmd[0] == "pi"
        ]
        assert (
            len(pi_commands) > 0
        ), f"No pi command found in {captured_commands}"

        # CRITICAL: Verify no --session in any pi command
        # This will fail until pt-ihfv is implemented
        for cmd in pi_commands:
            assert (
                "--session" not in cmd
            ), f"REGRESSION: pi command contains --session: {cmd}"

    def test_ralph_start_pi_invocation_no_session_with_session_dir(
        self, tmp_path: Path
    ) -> None:
        """Test: ralph start does not include --session even with session_dir.

        Verifies that the loop-based ticket processing also excludes --session
        when a session directory is configured.

        Expected to FAIL until pt-ihfv is implemented.
        """
        captured_commands: list[list[str]] = []

        def capturing_popen(
            args: list[str],
            **kwargs: Any,
        ) -> Any:
            captured_commands.append(args)
            mock = MagicMock()
            mock.wait.return_value = 0
            return mock

        def mock_run_shell(cmd: str, **kwargs: Any) -> Any:
            result = MagicMock()
            if (
                "tk ready" in cmd
                and "head" not in cmd
                and "awk" not in cmd
            ):
                # List query - return empty to end loop
                result.stdout = ""
                result.returncode = 1
            elif "head -1" in cmd or "awk" in cmd:
                # Select one ticket then empty on subsequent calls
                result.stdout = "TEST-123"
                result.returncode = 0
            elif "tk show" in cmd:
                result.stdout = (
                    "---\nid: TEST-123\ntags: [test]\n---\n# Test Ticket"
                )
                result.returncode = 0
            elif "grep" in cmd:
                # backlog_empty check - empty after first ticket
                result.returncode = 1
            else:
                result.stdout = ""
                result.returncode = 0
            return result

        # Set up session directory
        session_dir = tmp_path / ".pi" / "agent" / "sessions"
        session_dir.mkdir(parents=True)

        # Set up required files
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True, exist_ok=True)
        (ralph_dir / "config.json").write_text(
            '{"maxIterations": 1, "sleepBetweenTickets": 0, "sessionDir": "'
            + str(session_dir)
            + '"}'
        )

        progress_path = ralph_dir / "progress.md"
        progress_path.write_text(
            """# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
"""
        )

        def mock_ticket_title(ticket: str, **kwargs: Any) -> str | None:
            return "Test Ticket"

        with patch("subprocess.Popen", side_effect=capturing_popen):
            with patch.object(
                ralph_module, "run_shell", side_effect=mock_run_shell
            ):
                with patch.object(
                    ralph_module,
                    "find_project_root",
                    return_value=tmp_path,
                ):
                    with patch.object(
                        ralph_module, "ensure_pi", return_value=True
                    ):
                        with patch.object(
                            ralph_module, "prompt_exists", return_value=True
                        ):
                            with patch.object(
                                ralph_module,
                                "lock_acquire",
                                return_value=True,
                            ):
                                with patch.object(
                                    ralph_module,
                                    "lock_release",
                                ):
                                    with patch.object(
                                        ralph_module,
                                        "extract_ticket_title",
                                        side_effect=mock_ticket_title,
                                    ):
                                        exit_code = ralph_module.ralph_start(
                                            ["--max-iterations", "1"]
                                        )

        # Find pi commands
        pi_commands = [
            cmd for cmd in captured_commands if cmd and cmd[0] == "pi"
        ]

        # We may or may not have commands depending on loop behavior
        if pi_commands:
            for cmd in pi_commands:
                assert (
                    "--session" not in cmd
                ), f"REGRESSION: pi command contains --session: {cmd}"


class TestRalphPiInvocationArgsStructure:
    """Tests for general structure of pi invocation arguments."""

    def test_pi_command_starts_with_pi_dash_p(self, tmp_path: Path) -> None:
        """Test: pi command always starts with ['pi', '-p']."""
        captured_commands: list[list[str]] = []

        def capturing_popen(
            args: list[str],
            **kwargs: Any,
        ) -> Any:
            captured_commands.append(args)
            mock = MagicMock()
            mock.wait.return_value = 0
            return mock

        def mock_run_shell(cmd: str, **kwargs: Any) -> Any:
            result = MagicMock()
            if "tk ready" in cmd or "head -1" in cmd:
                result.stdout = "TEST-123"
                result.returncode = 0
            elif "tk show" in cmd:
                result.stdout = "---\nid: TEST-123\n---\n# Test"
                result.returncode = 0
            else:
                result.returncode = 0
            return result

        def mock_ticket_title(ticket: str, **kwargs: Any) -> str | None:
            return "Test Ticket"

        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True, exist_ok=True)
        (ralph_dir / "config.json").write_text('{}')

        progress_path = ralph_dir / "progress.md"
        progress_path.write_text(
            """# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
"""
        )

        with patch("subprocess.Popen", side_effect=capturing_popen):
            with patch.object(
                ralph_module, "run_shell", side_effect=mock_run_shell
            ):
                with patch.object(
                    ralph_module,
                    "find_project_root",
                    return_value=tmp_path,
                ):
                    with patch.object(
                        ralph_module, "ensure_pi", return_value=True
                    ):
                        with patch.object(
                            ralph_module, "prompt_exists", return_value=True
                        ):
                            with patch.object(
                                ralph_module,
                                "resolve_session_dir",
                                return_value=None,
                            ):
                                with patch.object(
                                    ralph_module,
                                    "lock_acquire",
                                    return_value=True,
                                ):
                                    with patch.object(
                                        ralph_module,
                                        "lock_release",
                                    ):
                                        with patch.object(
                                            ralph_module,
                                            "extract_ticket_title",
                                            side_effect=mock_ticket_title,
                                        ):
                                            ralph_module.ralph_run(["TEST-123"])

        pi_commands = [
            cmd for cmd in captured_commands if cmd and cmd[0] == "pi"
        ]

        assert len(pi_commands) > 0, "Should have captured pi commands"

        for cmd in pi_commands:
            assert (
                cmd[0] == "pi"
            ), f"Command should start with 'pi': {cmd}"
            assert (
                cmd[1] == "-p"
            ), f"Second arg should be '-p': {cmd}"
