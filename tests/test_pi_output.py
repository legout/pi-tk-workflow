"""Tests for --pi-output flag handling in Ralph.

Tests the --pi-output flag (inherit/file/discard) and --pi-output-file custom path.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch, mock_open

import pytest

from tf_cli.logger import LogLevel
from tf_cli.ralph import (
    DEFAULTS,
    parse_run_args,
    parse_start_args,
    run_ticket,
    _validate_pi_output,
)


class TestValidatePiOutput:
    """Test pi_output value validation."""

    def test_valid_inherit(self):
        """'inherit' should be valid."""
        assert _validate_pi_output("inherit") is True

    def test_valid_file(self):
        """'file' should be valid."""
        assert _validate_pi_output("file") is True

    def test_valid_discard(self):
        """'discard' should be valid."""
        assert _validate_pi_output("discard") is True

    def test_invalid_value(self):
        """Invalid values should return False."""
        assert _validate_pi_output("invalid") is False
        assert _validate_pi_output("stdout") is False
        assert _validate_pi_output("") is False


class TestParseRunArgsPiOutput:
    """Test --pi-output flag parsing in ralph run."""

    def test_pi_output_defaults_inherit(self):
        """--pi-output should default to 'inherit'."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["abc-123"]
        )
        assert pi_output == "inherit"
        assert pi_output_file is None

    def test_pi_output_file_parsed(self):
        """--pi-output=file should be parsed correctly."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output", "file", "abc-123"]
        )
        assert pi_output == "file"

    def test_pi_output_discard_parsed(self):
        """--pi-output=discard should be parsed correctly."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output=discard", "abc-123"]
        )
        assert pi_output == "discard"

    def test_pi_output_inherit_parsed(self):
        """--pi-output=inherit should be parsed correctly."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output=inherit", "abc-123"]
        )
        assert pi_output == "inherit"

    def test_pi_output_file_path_parsed(self):
        """--pi-output-file should parse custom path."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output-file", "/custom/path.log", "abc-123"]
        )
        assert pi_output_file == "/custom/path.log"

    def test_pi_output_file_path_equals_syntax(self):
        """--pi-output-file=path should work."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output-file=/custom/path.log", "abc-123"]
        )
        assert pi_output_file == "/custom/path.log"

    def test_combined_flags(self):
        """All pi-output flags should work together."""
        ticket, dry_run, flags, log_level, capture_json, progress, pi_output, pi_output_file = parse_run_args(
            ["--pi-output", "file", "--pi-output-file", "/tmp/out.log", "abc-123"]
        )
        assert pi_output == "file"
        assert pi_output_file == "/tmp/out.log"


class TestParseStartArgsPiOutput:
    """Test --pi-output flag parsing in ralph start."""

    def test_pi_output_defaults_inherit(self):
        """--pi-output should default to 'inherit'."""
        options = parse_start_args(["--max-iterations", "10"])
        assert options["pi_output"] == "inherit"
        assert options["pi_output_file"] is None

    def test_pi_output_file_parsed(self):
        """--pi-output=file should be parsed correctly."""
        options = parse_start_args(["--pi-output", "file", "--progress"])
        assert options["pi_output"] == "file"
        assert options["progress"] is True

    def test_pi_output_discard_parsed(self):
        """--pi-output=discard should be parsed correctly."""
        options = parse_start_args(["--pi-output=discard", "--max-iterations", "5"])
        assert options["pi_output"] == "discard"

    def test_pi_output_file_path_parsed(self):
        """--pi-output-file should parse custom path."""
        options = parse_start_args(["--pi-output-file", "/var/log/pi.log"])
        assert options["pi_output_file"] == "/var/log/pi.log"

    def test_combined_flags(self):
        """All pi-output flags should work together."""
        options = parse_start_args(
            ["--progress", "--pi-output", "discard", "--pi-output-file", "/tmp/out.log"]
        )
        assert options["progress"] is True
        assert options["pi_output"] == "discard"
        assert options["pi_output_file"] == "/tmp/out.log"


class TestRunTicketPiOutput:
    """Test run_ticket function with pi_output modes."""

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_dry_run_shows_file_output(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Dry run should indicate file output mode."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()

        rc = run_ticket(
            "abc-123",
            "/tf",
            "--auto",
            dry_run=True,
            logger=mock_logger,
            pi_output="file",
            pi_output_file="/tmp/test.log",
        )

        assert rc == 0
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "output to" in str(call_args)
        assert "/tmp/test.log" in str(call_args)

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_dry_run_shows_discard_output(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Dry run should indicate discard output mode."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()

        rc = run_ticket(
            "abc-123",
            "/tf",
            "--auto",
            dry_run=True,
            logger=mock_logger,
            pi_output="discard",
        )

        assert rc == 0
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "output discarded" in str(call_args)

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_dry_run_inherit_no_note(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Dry run with inherit should not have output note."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()

        rc = run_ticket(
            "abc-123",
            "/tf",
            "--auto",
            dry_run=True,
            logger=mock_logger,
            pi_output="inherit",
        )

        assert rc == 0
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "output" not in str(call_args).lower() or "discarded" not in str(call_args).lower()


class TestPiOutputFileMode:
    """Test file output mode functionality."""

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_file_mode_creates_log(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """File mode should write pi output to log file."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)

        mock_logger = MagicMock()

        with patch("pathlib.Path.open", mock_open()):
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                logs_dir=logs_dir,
                pi_output="file",
            )

        assert rc == 0
        mock_logger.info.assert_any_call(
            f"Pi output written to: {logs_dir / 'abc-123.log'}",
            ticket="abc-123",
            pi_log_path=str(logs_dir / "abc-123.log"),
        )

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_file_mode_with_custom_path(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """File mode with custom path should use specified path."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        # Use a path under tmp_path to ensure parent exists
        custom_path = str(tmp_path / "custom" / "output.log")

        mock_logger = MagicMock()

        with patch("builtins.open", mock_open()):
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                pi_output="file",
                pi_output_file=custom_path,
            )

        assert rc == 0
        mock_logger.info.assert_any_call(
            f"Pi output written to: {custom_path}",
            ticket="abc-123",
            pi_log_path=custom_path,
        )

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_file_mode_failure_shows_log_path(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """On failure with file mode, should print exit code and log path."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=1)

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)

        mock_logger = MagicMock()

        with patch("pathlib.Path.open", mock_open()):
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                logs_dir=logs_dir,
                pi_output="file",
            )

        assert rc == 1
        # Should log error with exit code and log path
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "exit code 1" in str(call_args)
        assert str(logs_dir / "abc-123.log") in str(call_args)


class TestPiOutputDiscardMode:
    """Test discard output mode functionality."""

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_discard_mode_runs_without_capture(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Discard mode should run pi without capturing output."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        mock_logger = MagicMock()

        with patch("builtins.open", mock_open()):
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                pi_output="discard",
            )

        assert rc == 0
        # Should call subprocess.run with stdout/stderr redirected to devnull
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        # In discard mode, stdout is set to the devnull file handle
        assert call_kwargs.get("stdout") is not None
        assert call_kwargs.get("stderr") == subprocess.STDOUT


class TestPiOutputInheritMode:
    """Test inherit output mode (default) functionality."""

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_inherit_mode_passes_through(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Inherit mode should pass output through to terminal (current behavior)."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        mock_logger = MagicMock()

        rc = run_ticket(
            "abc-123",
            "/tf",
            "--auto",
            dry_run=False,
            logger=mock_logger,
            pi_output="inherit",
        )

        assert rc == 0
        # Should call subprocess.run without stdout/stderr capture
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        # When inherit mode, we don't pass stdout/stderr so it goes to terminal
        assert "stdout" not in call_kwargs or call_kwargs.get("stdout") is None


class TestPiOutputWithJsonCapture:
    """Test pi_output combined with capture_json."""

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    @patch("subprocess.run")
    def test_both_json_and_file_mode(
        self, mock_run, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Both capture_json and file mode should write to separate files."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)

        mock_logger = MagicMock()

        with patch("pathlib.Path.open", mock_open()):
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                logs_dir=logs_dir,
                capture_json=True,
                pi_output="file",
            )

        assert rc == 0
        # Should log both JSONL and pi output paths
        mock_logger.info.assert_any_call(
            f"JSONL trace written to: {logs_dir / 'abc-123.jsonl'}",
            ticket="abc-123",
            jsonl_path=str(logs_dir / "abc-123.jsonl"),
        )


class TestPiOutputDefaults:
    """Test default values and integration with config."""

    def test_pi_output_not_in_defaults(self):
        """pi_output is not a default config value (it's CLI-only)."""
        assert "pi_output" not in DEFAULTS

    def test_run_ticket_default_inherit(self):
        """run_ticket should default to inherit mode."""
        # This is tested implicitly through the function signature
        import inspect
        sig = inspect.signature(run_ticket)
        params = sig.parameters
        assert params["pi_output"].default == "inherit"
        assert params["pi_output_file"].default is None


class TestOutputRoutingWithoutSubprocess:
    """Test output routing decisions without invoking subprocess.run.
    
    These tests verify that the correct output routing mode is determined
    based on the pi_output parameter and configuration, without actually
    running pi subprocess.
    """

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    def test_inherit_mode_routing_decision(
        self, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Inherit mode should decide to pass through stdout/stderr."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()

        # Mock subprocess.run to capture what would be called
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            rc = run_ticket(
                "abc-123",
                "/tf",
                "--auto",
                dry_run=False,
                logger=mock_logger,
                pi_output="inherit",
            )

            assert rc == 0
            # Verify subprocess.run was called with no stdout/stderr capture
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args.kwargs
            # Inherit mode means no stdout/stderr redirection
            assert call_kwargs.get("stdout") is None
            assert call_kwargs.get("stderr") is None

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    def test_file_mode_routing_decision(
        self, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """File mode should decide to redirect to file."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)

        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.open", mock_open()):
                mock_run.return_value = MagicMock(returncode=0)
                
                rc = run_ticket(
                    "abc-123",
                    "/tf",
                    "--auto",
                    dry_run=False,
                    logger=mock_logger,
                    logs_dir=logs_dir,
                    pi_output="file",
                )

                assert rc == 0
                # File mode should redirect stdout to file
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args.kwargs
                # stdout should be a file handle, not None
                assert call_kwargs.get("stdout") is not None
                assert call_kwargs.get("stderr") == subprocess.STDOUT

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    def test_discard_mode_routing_decision(
        self, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """Discard mode should decide to redirect to devnull."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()

        with patch("subprocess.run") as mock_run:
            with patch("builtins.open", mock_open()):
                mock_run.return_value = MagicMock(returncode=0)
                
                rc = run_ticket(
                    "abc-123",
                    "/tf",
                    "--auto",
                    dry_run=False,
                    logger=mock_logger,
                    pi_output="discard",
                )

                assert rc == 0
                # Discard mode should redirect to devnull
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args.kwargs
                # stdout should be set (to devnull handle)
                assert call_kwargs.get("stdout") is not None
                assert call_kwargs.get("stderr") == subprocess.STDOUT

    @patch("tf_cli.ralph.ensure_pi")
    @patch("tf_cli.ralph.find_project_root")
    @patch("tf_cli.ralph.prompt_exists")
    def test_file_mode_with_custom_path_decision(
        self, mock_prompt, mock_root, mock_ensure_pi, tmp_path: Path
    ):
        """File mode with custom path should use specified path."""
        mock_ensure_pi.return_value = True
        mock_root.return_value = tmp_path
        mock_prompt.return_value = True

        mock_logger = MagicMock()
        custom_path = str(tmp_path / "custom" / "output.log")

        with patch("subprocess.run") as mock_run:
            with patch("builtins.open", mock_open()) as mock_file:
                mock_run.return_value = MagicMock(returncode=0)
                
                rc = run_ticket(
                    "abc-123",
                    "/tf",
                    "--auto",
                    dry_run=False,
                    logger=mock_logger,
                    pi_output="file",
                    pi_output_file=custom_path,
                )

                assert rc == 0
                # Should have logged the custom path
                mock_logger.info.assert_any_call(
                    f"Pi output written to: {custom_path}",
                    ticket="abc-123",
                    pi_log_path=custom_path,
                )

    def test_dry_run_shows_routing_decision_inherit(self):
        """Dry run should show inherit routing decision."""
        with patch("tf_cli.ralph.ensure_pi") as mock_ensure:
            with patch("tf_cli.ralph.find_project_root") as mock_root:
                with patch("tf_cli.ralph.prompt_exists") as mock_prompt:
                    mock_ensure.return_value = True
                    mock_root.return_value = Path("/tmp")
                    mock_prompt.return_value = True

                    mock_logger = MagicMock()
                    
                    rc = run_ticket(
                        "abc-123",
                        "/tf",
                        "--auto",
                        dry_run=True,
                        logger=mock_logger,
                        pi_output="inherit",
                    )

                    assert rc == 0
                    # Inherit mode should not mention output in dry run
                    call_args = str(mock_logger.info.call_args)
                    assert "output to" not in call_args.lower() and "discarded" not in call_args.lower()

    def test_dry_run_shows_routing_decision_file(self):
        """Dry run should show file routing decision."""
        with patch("tf_cli.ralph.ensure_pi") as mock_ensure:
            with patch("tf_cli.ralph.find_project_root") as mock_root:
                with patch("tf_cli.ralph.prompt_exists") as mock_prompt:
                    mock_ensure.return_value = True
                    mock_root.return_value = Path("/tmp")
                    mock_prompt.return_value = True

                    mock_logger = MagicMock()
                    
                    rc = run_ticket(
                        "abc-123",
                        "/tf",
                        "--auto",
                        dry_run=True,
                        logger=mock_logger,
                        pi_output="file",
                        pi_output_file="/tmp/test.log",
                    )

                    assert rc == 0
                    # File mode should show output path in dry run
                    call_args = str(mock_logger.info.call_args)
                    assert "output to" in call_args
                    assert "/tmp/test.log" in call_args

    def test_dry_run_shows_routing_decision_discard(self):
        """Dry run should show discard routing decision."""
        with patch("tf_cli.ralph.ensure_pi") as mock_ensure:
            with patch("tf_cli.ralph.find_project_root") as mock_root:
                with patch("tf_cli.ralph.prompt_exists") as mock_prompt:
                    mock_ensure.return_value = True
                    mock_root.return_value = Path("/tmp")
                    mock_prompt.return_value = True

                    mock_logger = MagicMock()
                    
                    rc = run_ticket(
                        "abc-123",
                        "/tf",
                        "--auto",
                        dry_run=True,
                        logger=mock_logger,
                        pi_output="discard",
                    )

                    assert rc == 0
                    # Discard mode should show "discarded" in dry run
                    call_args = str(mock_logger.info.call_args)
                    assert "output discarded" in call_args
