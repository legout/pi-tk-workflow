"""Tests for tf.agentsmd module."""

from __future__ import annotations

import shutil
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tf import agentsmd as agentsmd_module


class TestDetectPackageManager:
    """Tests for detect_package_manager function."""

    def test_detects_uv_by_lockfile(self, tmp_path: Path) -> None:
        """Test detecting uv by uv.lock."""
        (tmp_path / "uv.lock").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "uv"

    def test_detects_poetry_by_lockfile(self, tmp_path: Path) -> None:
        """Test detecting poetry by poetry.lock."""
        (tmp_path / "poetry.lock").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "poetry"

    def test_detects_npm_by_lockfile(self, tmp_path: Path) -> None:
        """Test detecting npm by package-lock.json."""
        (tmp_path / "package-lock.json").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "npm"

    def test_detects_pnpm(self, tmp_path: Path) -> None:
        """Test detecting pnpm."""
        (tmp_path / "pnpm-lock.yaml").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "pnpm"

    def test_detects_cargo(self, tmp_path: Path) -> None:
        """Test detecting cargo."""
        (tmp_path / "Cargo.toml").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "cargo"

    def test_detects_go(self, tmp_path: Path) -> None:
        """Test detecting go."""
        (tmp_path / "go.mod").write_text("")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "go"

    def test_detects_uv_by_pyproject_toml(self, tmp_path: Path) -> None:
        """Test detecting uv by pyproject.toml content."""
        (tmp_path / "pyproject.toml").write_text("[tool.uv]")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "uv"

    def test_detects_poetry_by_pyproject_toml(self, tmp_path: Path) -> None:
        """Test detecting poetry by pyproject.toml content."""
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "poetry"

    def test_defaults_to_uv_for_pyproject(self, tmp_path: Path) -> None:
        """Test defaulting to uv for pyproject.toml without markers."""
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "uv"

    def test_returns_unknown_when_no_files(self, tmp_path: Path) -> None:
        """Test returning unknown when no package files found."""
        result = agentsmd_module.detect_package_manager(tmp_path)
        assert result == "unknown"


class TestGetDefaultCommands:
    """Tests for get_default_commands function."""

    def test_uv_commands(self) -> None:
        """Test UV commands."""
        result = agentsmd_module.get_default_commands("uv")
        assert "run: uv run python" in result
        assert "test: uv run pytest" in result

    def test_poetry_commands(self) -> None:
        """Test poetry commands."""
        result = agentsmd_module.get_default_commands("poetry")
        assert "run: poetry run python" in result

    def test_npm_commands(self) -> None:
        """Test npm commands."""
        result = agentsmd_module.get_default_commands("npm")
        assert "run: npm run dev" in result
        assert "build: npm run build" in result

    def test_cargo_commands(self) -> None:
        """Test cargo commands."""
        result = agentsmd_module.get_default_commands("cargo")
        assert "build: cargo build" in result
        assert "test: cargo test" in result

    def test_empty_list_for_unknown(self) -> None:
        """Test empty list for unknown package manager."""
        result = agentsmd_module.get_default_commands("unknown")
        assert result == []


class TestInitAgentsmd:
    """Tests for init_agentsmd function."""

    @patch.object(agentsmd_module, "detect_package_manager", return_value="uv")
    @patch("builtins.input", side_effect=["MyProject", "A test project", "n"])
    @patch("builtins.print")
    def test_creates_agentsmd(self, mock_print: MagicMock, mock_input: MagicMock, mock_detect: MagicMock, tmp_path: Path) -> None:
        """Test creating AGENTS.md file with complete template structure."""
        result = agentsmd_module.init_agentsmd(tmp_path)

        assert result == 0
        agents_file = tmp_path / "AGENTS.md"
        assert agents_file.exists()
        content = agents_file.read_text()
        assert "# MyProject" in content
        assert "A test project" in content
        assert "## Quick Commands" in content
        assert "run: uv run python" in content
        assert "test: uv run pytest" in content
        assert "## Conventions" in content
        assert "## Notes" in content
        assert "This project uses `uv` for Python package management" in content

    @patch.object(agentsmd_module, "detect_package_manager", return_value="uv")
    @patch("builtins.input", side_effect=["n"])
    @patch("builtins.print")
    def test_skips_when_user_declines_overwrite(self, mock_print: MagicMock, mock_input: MagicMock, mock_detect: MagicMock, tmp_path: Path) -> None:
        """Test skipping when user declines overwrite."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("existing content")
        
        result = agentsmd_module.init_agentsmd(tmp_path)
        
        assert result == 0
        assert agents_file.read_text() == "existing content"

    @patch.object(agentsmd_module, "detect_package_manager", return_value="uv")
    @patch("builtins.input", side_effect=["y", "MyProject", "A description", "n"])
    @patch.object(agentsmd_module.shutil, "move")
    @patch("builtins.print")
    def test_creates_backup_on_overwrite(self, mock_print: MagicMock, mock_move: MagicMock, mock_input: MagicMock, mock_detect: MagicMock, tmp_path: Path) -> None:
        """Test creating backup when overwriting."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("existing content")
        
        result = agentsmd_module.init_agentsmd(tmp_path)
        
        assert result == 0
        mock_move.assert_called_once()


class TestStatusAgentsmd:
    """Tests for status_agentsmd function."""

    @patch("builtins.print")
    def test_shows_error_when_no_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test error output when AGENTS.md doesn't exist."""
        result = agentsmd_module.status_agentsmd(tmp_path)
        
        assert result == 1
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "No AGENTS.md found" in output

    @patch("builtins.print")
    def test_shows_status_for_existing_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test status output for existing file."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Project\n\nDescription\n")
        
        result = agentsmd_module.status_agentsmd(tmp_path)
        
        assert result == 0
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Size:" in output
        assert "Lines:" in output

    @patch("builtins.print")
    def test_detects_claude_symlink(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test detecting CLAUDE.md symlink."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("content")
        claude_file = tmp_path / "CLAUDE.md"
        claude_file.symlink_to(agents_file)
        
        result = agentsmd_module.status_agentsmd(tmp_path)
        
        assert result == 0
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "symlink exists" in output


class TestValidateAgentsmd:
    """Tests for validate_agentsmd function."""

    @patch("builtins.print")
    def test_fails_when_no_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test validation fails when file doesn't exist."""
        result = agentsmd_module.validate_agentsmd(tmp_path)
        
        assert result == 1

    @patch("builtins.print")
    def test_passes_for_good_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test passing validation for good file."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Project\n\nGood description.\n")
        
        result = agentsmd_module.validate_agentsmd(tmp_path)
        
        assert result == 0
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "All checks passed" in output

    @patch("builtins.print")
    def test_warns_on_large_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test warning for large files."""
        agents_file = tmp_path / "AGENTS.md"
        # Create a file larger than 5KB
        agents_file.write_text("# Project\n\n" + "x" * 6000)
        
        result = agentsmd_module.validate_agentsmd(tmp_path)
        
        assert result == 1  # Large files are issues, not warnings
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "File is large" in output


class TestFixAgentsmd:
    """Tests for fix_agentsmd function."""

    @patch("builtins.print")
    def test_fails_when_no_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test fix fails when file doesn't exist."""
        result = agentsmd_module.fix_agentsmd(tmp_path)
        
        assert result == 1

    @patch("builtins.print")
    def test_creates_backup(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test creating backup before fix."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("content")
        
        result = agentsmd_module.fix_agentsmd(tmp_path)
        
        assert result == 0
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "Backup created" in output


class TestUpdateAgentsmd:
    """Tests for update_agentsmd function."""

    @patch("builtins.print")
    def test_fails_when_no_file(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test update fails when file doesn't exist."""
        result = agentsmd_module.update_agentsmd(tmp_path)
        
        assert result == 1

    @patch("builtins.print")
    def test_skips_when_tool_prefs_exists(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test skipping when Tool Preferences already exists."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Project\n\n## Tool Preferences\n")
        
        result = agentsmd_module.update_agentsmd(tmp_path)
        
        assert result == 0
        output = " ".join(str(call) for call in mock_print.call_args_list)
        assert "review manually" in output

    @patch("builtins.print")
    def test_adds_tool_preferences(self, mock_print: MagicMock, tmp_path: Path) -> None:
        """Test adding Tool Preferences section."""
        agents_file = tmp_path / "AGENTS.md"
        agents_file.write_text("# Project\n\nDescription\n")
        
        result = agentsmd_module.update_agentsmd(tmp_path)
        
        assert result == 0
        content = agents_file.read_text()
        assert "## Tool Preferences" in content


class TestDatetimeStamp:
    """Tests for datetime_stamp function."""

    def test_returns_14_digit_string(self) -> None:
        """Test that stamp is 14 digits (YYYYMMDDHHMMSS)."""
        stamp = agentsmd_module.datetime_stamp()
        assert len(stamp) == 14
        assert stamp.isdigit()


class TestBuildParser:
    """Tests for build_parser function."""

    def test_parser_has_init_subcommand(self) -> None:
        """Test that parser has init subcommand."""
        parser = agentsmd_module.build_parser()
        with patch.object(parser, "parse_args") as mock_parse:
            mock_parse.return_value = MagicMock(command="init", path=".")
            args = parser.parse_args(["init"])
            assert args.command == "init"

    def test_parser_has_status_subcommand(self) -> None:
        """Test that parser has status subcommand."""
        parser = agentsmd_module.build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parser_has_validate_subcommand(self) -> None:
        """Test that parser has validate subcommand."""
        parser = agentsmd_module.build_parser()
        args = parser.parse_args(["validate"])
        assert args.command == "validate"

    def test_parser_has_fix_subcommand(self) -> None:
        """Test that parser has fix subcommand."""
        parser = agentsmd_module.build_parser()
        args = parser.parse_args(["fix"])
        assert args.command == "fix"

    def test_parser_has_update_subcommand(self) -> None:
        """Test that parser has update subcommand."""
        parser = agentsmd_module.build_parser()
        args = parser.parse_args(["update"])
        assert args.command == "update"


class TestMain:
    """Tests for main function."""

    @patch.object(agentsmd_module, "init_agentsmd", return_value=0)
    def test_main_calls_init(self, mock_init: MagicMock) -> None:
        """Test main with init command."""
        result = agentsmd_module.main(["init"])
        assert result == 0
        mock_init.assert_called_once()

    @patch.object(agentsmd_module, "status_agentsmd", return_value=0)
    def test_main_calls_status(self, mock_status: MagicMock) -> None:
        """Test main with status command."""
        result = agentsmd_module.main(["status"])
        assert result == 0
        mock_status.assert_called_once()

    @patch.object(agentsmd_module, "validate_agentsmd", return_value=0)
    def test_main_calls_validate(self, mock_validate: MagicMock) -> None:
        """Test main with validate command."""
        result = agentsmd_module.main(["validate"])
        assert result == 0
        mock_validate.assert_called_once()

    @patch.object(agentsmd_module, "fix_agentsmd", return_value=0)
    def test_main_calls_fix(self, mock_fix: MagicMock) -> None:
        """Test main with fix command."""
        result = agentsmd_module.main(["fix"])
        assert result == 0
        mock_fix.assert_called_once()

    @patch.object(agentsmd_module, "update_agentsmd", return_value=0)
    def test_main_calls_update(self, mock_update: MagicMock) -> None:
        """Test main with update command."""
        result = agentsmd_module.main(["update"])
        assert result == 0
        mock_update.assert_called_once()

    def test_main_returns_1_on_invalid_command(self) -> None:
        """Test main returns 1 when no command given."""
        # argparse exits with SystemExit when no subcommand
        with pytest.raises(SystemExit):
            agentsmd_module.main([])
