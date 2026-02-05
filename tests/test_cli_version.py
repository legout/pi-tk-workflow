"""Tests for tf CLI --version flag.

This module contains tests for the --version and -v CLI flags
in tf_cli/cli.py, ensuring correct version display and exit behavior.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from tf_cli.cli import main
from tf_cli.version import get_version


class TestGetVersion:
    """Tests for get_version function."""

    def test_returns_version_from_repo_root(self, tmp_path: Path) -> None:
        """Should return version from VERSION file in repo root."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3\n")
        
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            result = get_version()
        
        assert result == "1.2.3"

    def test_returns_unknown_when_no_version_file(self, tmp_path: Path) -> None:
        """Should return 'unknown' when VERSION file doesn't exist."""
        # Mock both repo_root and the fallback path to not exist
        with (
            mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path),
            mock.patch.object(Path, "is_file", return_value=False),
        ):
            result = get_version()
        
        assert result == "unknown"

    def test_returns_unknown_when_repo_root_none(self) -> None:
        """Should return 'unknown' when repo root cannot be resolved."""
        # Mock both repo_root as None and the fallback path to not exist
        with (
            mock.patch("tf_cli.version._resolve_repo_root", return_value=None),
            mock.patch.object(Path, "is_file", return_value=False),
        ):
            result = get_version()
        
        assert result == "unknown"

    def test_strips_whitespace_from_version(self, tmp_path: Path) -> None:
        """Should strip whitespace from version string."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("  1.2.3  \n")
        
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            result = get_version()
        
        assert result == "1.2.3"



class TestMainVersionFlag:
    """Tests for --version and -v flags in main function."""

    def test_version_flag_prints_version(self, capsys) -> None:
        """Should print version and exit 0 with --version flag."""
        with mock.patch("tf_cli.cli.get_version", return_value="1.2.3"):
            result = main(["--version"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "1.2.3"

    def test_v_flag_prints_version(self, capsys) -> None:
        """Should print version and exit 0 with -v flag."""
        with mock.patch("tf_cli.cli.get_version", return_value="1.2.3"):
            result = main(["-v"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "1.2.3"

    def test_version_flag_with_actual_version_file(self, tmp_path: Path, capsys) -> None:
        """Integration test: should read and print actual VERSION file."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("0.1.0\n")
        
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            result = main(["--version"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "0.1.0"

    def test_version_flag_takes_precedence_over_commands(self, capsys) -> None:
        """--version should be handled before any command routing."""
        with mock.patch("tf_cli.cli.get_version", return_value="1.0.0"):
            # Even with "install" as second arg, --version should win
            result = main(["--version", "install"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "1.0.0"
