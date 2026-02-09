"""Tests for tf.setup module."""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tf import setup as tf_setup_module


class TestPromptYesNo:
    """Tests for prompt_yes_no function."""

    @patch("builtins.input", return_value="")
    def test_default_yes_returns_true_on_empty(self, mock_input: MagicMock) -> None:
        """Test that default_yes=True returns True on empty input."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=True)
        assert result is True

    @patch("builtins.input", return_value="")
    def test_default_no_returns_false_on_empty(self, mock_input: MagicMock) -> None:
        """Test that default_yes=False returns False on empty input."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=False)
        assert result is False

    @patch("builtins.input", return_value="y")
    def test_y_returns_true(self, mock_input: MagicMock) -> None:
        """Test that 'y' returns True."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=False)
        assert result is True

    @patch("builtins.input", return_value="Y")
    def test_uppercase_y_returns_true(self, mock_input: MagicMock) -> None:
        """Test that 'Y' returns True."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=False)
        assert result is True

    @patch("builtins.input", return_value="n")
    def test_n_returns_false(self, mock_input: MagicMock) -> None:
        """Test that 'n' returns False."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=True)
        assert result is False

    @patch("builtins.input", return_value="yes")
    def test_yes_returns_true(self, mock_input: MagicMock) -> None:
        """Test that 'yes' returns True (startswith check)."""
        result = tf_setup_module.prompt_yes_no("Test message", default_yes=False)
        assert result is True


class TestInstallExtensions:
    """Tests for install_extensions function."""

    @patch.object(tf_setup_module.shutil, "which", return_value=None)
    def test_skips_when_pi_not_found(self, mock_which: MagicMock) -> None:
        """Test that install skips when pi is not in PATH."""
        with patch.object(sys.stderr, "write") as mock_stderr:
            tf_setup_module.install_extensions(install_optional=False)
        mock_which.assert_called_once_with("pi")

    @patch.object(tf_setup_module.shutil, "which", return_value="/usr/bin/pi")
    @patch.object(tf_setup_module.subprocess, "run")
    def test_installs_required_extensions(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Test that required extensions are installed."""
        tf_setup_module.install_extensions(install_optional=False)
        
        assert mock_run.call_count == len(tf_setup_module.REQUIRED_EXTENSIONS)
        for name in tf_setup_module.REQUIRED_EXTENSIONS:
            mock_run.assert_any_call(["pi", "install", f"npm:{name}"])

    @patch.object(tf_setup_module.shutil, "which", return_value="/usr/bin/pi")
    @patch.object(tf_setup_module.subprocess, "run")
    def test_installs_optional_when_requested(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Test that optional extensions are installed when requested."""
        tf_setup_module.install_extensions(install_optional=True)
        
        total_calls = len(tf_setup_module.REQUIRED_EXTENSIONS) + len(tf_setup_module.OPTIONAL_EXTENSIONS)
        assert mock_run.call_count == total_calls
        for name in tf_setup_module.OPTIONAL_EXTENSIONS:
            mock_run.assert_any_call(["pi", "install", f"npm:{name}"])


class TestRunSetup:
    """Tests for run_setup function."""

    @patch.object(tf_setup_module, "prompt_yes_no", side_effect=[True, False, False])
    @patch.object(tf_setup_module, "install_extensions")
    @patch("builtins.print")
    def test_installs_required_only(self, mock_print: MagicMock, mock_install: MagicMock, mock_prompt: MagicMock) -> None:
        """Test setup with required extensions only."""
        args = MagicMock()
        result = tf_setup_module.run_setup(args)
        
        assert result == 0
        mock_install.assert_called_once_with(install_optional=False)

    @patch.object(tf_setup_module, "prompt_yes_no", side_effect=[True, True, False])
    @patch.object(tf_setup_module, "install_extensions")
    @patch("builtins.print")
    def test_installs_optional_when_requested(self, mock_print: MagicMock, mock_install: MagicMock, mock_prompt: MagicMock) -> None:
        """Test setup with optional extensions."""
        args = MagicMock()
        result = tf_setup_module.run_setup(args)
        
        assert result == 0
        mock_install.assert_called_once_with(install_optional=True)

    @patch.object(tf_setup_module, "prompt_yes_no", side_effect=[False, False, True])
    @patch.object(tf_setup_module, "install_extensions")
    @patch("builtins.print")
    @patch("builtins.input", return_value="")
    def test_skips_install_but_configures_login(self, mock_input: MagicMock, mock_print: MagicMock, mock_install: MagicMock, mock_prompt: MagicMock) -> None:
        """Test that install is skipped when user opts for API key config only."""
        args = MagicMock()
        result = tf_setup_module.run_setup(args)
        
        assert result == 0
        mock_install.assert_not_called()

    @patch.object(tf_setup_module, "prompt_yes_no", return_value=False)
    @patch.object(tf_setup_module, "install_extensions")
    @patch("builtins.print")
    def test_skips_all_when_no_prompts_accepted(self, mock_print: MagicMock, mock_install: MagicMock, mock_prompt: MagicMock) -> None:
        """Test that nothing is installed when user declines all."""
        args = MagicMock()
        result = tf_setup_module.run_setup(args)
        
        assert result == 0
        mock_install.assert_not_called()


class TestBuildParser:
    """Tests for build_parser function."""

    def test_parser_has_project_argument(self) -> None:
        """Test that parser has --project argument."""
        parser = tf_setup_module.build_parser()
        args = parser.parse_args(["--project", "test"])
        assert args.project == "test"

    def test_parser_has_global_argument(self) -> None:
        """Test that parser has --global argument."""
        parser = tf_setup_module.build_parser()
        args = parser.parse_args(["--global"])
        assert args.global_install is True

    def test_parser_defaults(self) -> None:
        """Test parser default values."""
        parser = tf_setup_module.build_parser()
        args = parser.parse_args([])
        assert args.project is None
        assert args.global_install is False


class TestMain:
    """Tests for main function."""

    @patch.object(tf_setup_module, "run_setup", return_value=0)
    def test_main_calls_run_setup(self, mock_run_setup: MagicMock) -> None:
        """Test that main calls run_setup."""
        result = tf_setup_module.main([])
        assert result == 0
        mock_run_setup.assert_called_once()

    @patch.object(tf_setup_module, "run_setup", return_value=1)
    def test_main_returns_exit_code(self, mock_run_setup: MagicMock) -> None:
        """Test that main returns the exit code from run_setup."""
        result = tf_setup_module.main([])
        assert result == 1

    def test_main_accepts_argv(self) -> None:
        """Test that main accepts command line arguments."""
        with patch.object(tf_setup_module, "run_setup") as mock_run_setup:
            tf_setup_module.main(["--global"])
            args = mock_run_setup.call_args[0][0]
            assert args.global_install is True
