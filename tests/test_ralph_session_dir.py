"""Tests for Ralph sessionDir resolution and legacy warning behavior.

These tests validate the resolve_session_dir() function covering:
- Default path selection (Pi standard session directory)
- Config override semantics (relative vs absolute paths)
- Legacy .tf/ralph/sessions detection and warn-once behavior
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from tf import ralph as ralph_module


class TestDefaultSessionDir:
    """Tests for default session directory selection."""

    def test_default_session_dir_is_pi_standard(self, tmp_path: Path) -> None:
        """Test: Default sessionDir is Pi's standard session directory."""
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_default_path_expands_tilde(self, tmp_path: Path) -> None:
        """Test: Tilde in default path is expanded to home directory."""
        config = {"sessionDir": "~/custom/sessions"}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = Path.home() / "custom/sessions"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_default_path_creates_directory(self, tmp_path: Path) -> None:
        """Test: Session directory is created if it doesn't exist."""
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        custom_dir = tmp_path / "new_sessions"
        config["sessionDir"] = str(custom_dir)
        
        assert not custom_dir.exists(), "Directory should not exist before call"
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result == custom_dir, f"Expected {custom_dir}, got {result}"
        assert custom_dir.exists(), "Directory should be created"
        assert custom_dir.is_dir(), "Path should be a directory"


class TestConfigOverrideSemantics:
    """Tests for config override semantics (relative vs absolute paths)."""

    def test_config_override_absolute_path(self, tmp_path: Path) -> None:
        """Test: Absolute path in config is used as-is."""
        absolute_path = tmp_path / "absolute" / "sessions"
        config = {"sessionDir": str(absolute_path)}
        raw_config = {"sessionDir": str(absolute_path)}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result == absolute_path, f"Expected {absolute_path}, got {result}"

    def test_config_override_relative_path(self, tmp_path: Path) -> None:
        """Test: Relative path in config is resolved relative to project root."""
        config = {"sessionDir": ".tf/custom/sessions"}
        raw_config = {"sessionDir": ".tf/custom/sessions"}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = tmp_path / ".tf/custom/sessions"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_config_override_with_tilde(self, tmp_path: Path) -> None:
        """Test: Config path with tilde is expanded to home directory."""
        config = {"sessionDir": "~/my/sessions"}
        raw_config = {"sessionDir": "~/my/sessions"}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = Path.home() / "my/sessions"
        assert result == expected, f"Expected {expected}, got {result}"

    def test_config_disabled_with_empty_string(self, tmp_path: Path) -> None:
        """Test: Empty string in config disables sessions."""
        config = {"sessionDir": ""}
        raw_config = {"sessionDir": ""}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result is None, "Expected None for empty string sessionDir"

    def test_config_disabled_with_false(self, tmp_path: Path) -> None:
        """Test: Boolean False in config disables sessions."""
        config = {"sessionDir": False}
        raw_config = {"sessionDir": False}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result is None, "Expected None for False sessionDir"

    def test_config_disabled_with_none(self, tmp_path: Path) -> None:
        """Test: None value in config disables sessions."""
        config = {"sessionDir": None}
        raw_config = {"sessionDir": None}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result is None, "Expected None for None sessionDir"


class TestLegacyWarningBehavior:
    """Tests for legacy .tf/ralph/sessions detection and warn-once behavior."""

    def setup_method(self) -> None:
        """Reset the legacy warning flag before each test."""
        # Reset the module-level warning flag
        ralph_module._legacy_warning_emitted = False

    def test_legacy_warning_emitted_when_legacy_exists(self, tmp_path: Path) -> None:
        """Test: Warning is emitted when legacy directory exists and has content."""
        # Create legacy directory with a file
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "some_session.json").write_text("{}")
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        mock_logger = MagicMock()
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        # Verify default path is still used (not legacy)
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Verify warning was logged
        mock_logger.warn.assert_called_once()
        warning_call = mock_logger.warn.call_args[0][0]
        assert "Legacy session directory detected" in warning_call
        assert ".tf/ralph/sessions" in warning_call

    def test_legacy_warning_not_emitted_when_user_explicitly_sets_sessiondir(
        self, tmp_path: Path
    ) -> None:
        """Test: No warning when user explicitly configures sessionDir."""
        # Create legacy directory with a file
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "some_session.json").write_text("{}")
        
        config = {"sessionDir": "~/custom/sessions"}
        raw_config = {"sessionDir": "~/custom/sessions"}
        mock_logger = MagicMock()
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        # Verify custom path is used
        expected = Path.home() / "custom/sessions"
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Verify warning was NOT logged
        mock_logger.warn.assert_not_called()

    def test_legacy_warning_emitted_only_once(self, tmp_path: Path) -> None:
        """Test: Legacy warning is emitted only once per run (warn-once behavior)."""
        # Create legacy directory with a file
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "some_session.json").write_text("{}")
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        mock_logger = MagicMock()
        
        # First call - warning should be emitted
        ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        assert mock_logger.warn.call_count == 1, "Warning should be emitted once"
        
        # Reset mock but NOT the module flag
        mock_logger.reset_mock()
        
        # Second call - warning should NOT be emitted again
        ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        mock_logger.warn.assert_not_called()

    def test_legacy_warning_not_emitted_when_legacy_empty(self, tmp_path: Path) -> None:
        """Test: No warning when legacy directory exists but is empty."""
        # Create empty legacy directory
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        mock_logger = MagicMock()
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        # Verify default path is used
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Verify warning was NOT logged (directory is empty)
        mock_logger.warn.assert_not_called()

    def test_legacy_warning_not_emitted_when_no_legacy(self, tmp_path: Path) -> None:
        """Test: No warning when legacy directory doesn't exist."""
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        mock_logger = MagicMock()
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
            logger=mock_logger,
        )
        
        # Verify default path is used
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Verify warning was NOT logged
        mock_logger.warn.assert_not_called()


class TestForceLegacyEnvironmentVariable:
    """Tests for RALPH_FORCE_LEGACY_SESSIONS environment variable."""

    def setup_method(self) -> None:
        """Reset the legacy warning flag before each test."""
        ralph_module._legacy_warning_emitted = False

    @patch.dict(os.environ, {"RALPH_FORCE_LEGACY_SESSIONS": "1"})
    def test_force_legacy_env_var_uses_legacy_path(self, tmp_path: Path) -> None:
        """Test: RALPH_FORCE_LEGACY_SESSIONS=1 forces use of legacy path."""
        # Create legacy directory
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        # Verify legacy path is used
        assert result == legacy_dir, f"Expected {legacy_dir}, got {result}"

    @patch.dict(os.environ, {"RALPH_FORCE_LEGACY_SESSIONS": "true"})
    def test_force_legacy_env_var_accepts_true(self, tmp_path: Path) -> None:
        """Test: RALPH_FORCE_LEGACY_SESSIONS=true forces use of legacy path."""
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result == legacy_dir, f"Expected {legacy_dir}, got {result}"

    @patch.dict(os.environ, {"RALPH_FORCE_LEGACY_SESSIONS": "yes"})
    def test_force_legacy_env_var_accepts_yes(self, tmp_path: Path) -> None:
        """Test: RALPH_FORCE_LEGACY_SESSIONS=yes forces use of legacy path."""
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result == legacy_dir, f"Expected {legacy_dir}, got {result}"

    @patch.dict(os.environ, {"RALPH_FORCE_LEGACY_SESSIONS": "0"})
    def test_force_legacy_env_var_zero_uses_default(self, tmp_path: Path) -> None:
        """Test: RALPH_FORCE_LEGACY_SESSIONS=0 uses default path."""
        # Create legacy directory with content
        legacy_dir = tmp_path / ".tf/ralph/sessions"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "session.json").write_text("{}")
        
        config: Dict[str, Any] = {}
        raw_config: Dict[str, Any] = {}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        # Verify default path is used (not legacy)
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"


class TestSessionDirEdgeCases:
    """Tests for edge cases in sessionDir resolution."""

    def setup_method(self) -> None:
        """Reset the legacy warning flag before each test."""
        ralph_module._legacy_warning_emitted = False

    def test_session_dir_with_nested_path_creation(self, tmp_path: Path) -> None:
        """Test: Nested session directory path is created correctly."""
        nested_path = "very/deep/nested/sessions/path"
        config = {"sessionDir": nested_path}
        raw_config = {"sessionDir": nested_path}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = tmp_path / nested_path
        assert result == expected, f"Expected {expected}, got {result}"
        assert expected.exists(), "Nested directory should be created"
        assert expected.is_dir(), "Path should be a directory"

    def test_session_dir_preserves_existing_directory(self, tmp_path: Path) -> None:
        """Test: Existing session directory is preserved (not recreated)."""
        existing_dir = tmp_path / "existing_sessions"
        existing_dir.mkdir()
        (existing_dir / "existing_file.txt").write_text("content")
        
        config = {"sessionDir": str(existing_dir)}
        raw_config = {"sessionDir": str(existing_dir)}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        assert result == existing_dir, f"Expected {existing_dir}, got {result}"
        assert (existing_dir / "existing_file.txt").exists(), "Existing content should be preserved"

    def test_default_used_when_config_has_no_sessiondir_key(self, tmp_path: Path) -> None:
        """Test: Default is used when config doesn't have sessionDir key."""
        config: Dict[str, Any] = {"otherKey": "value"}
        raw_config: Dict[str, Any] = {"otherKey": "value"}
        
        result = ralph_module.resolve_session_dir(
            project_root=tmp_path,
            config=config,
            raw_config=raw_config,
        )
        
        expected = Path.home() / ".pi/agent/sessions"
        assert result == expected, f"Expected {expected}, got {result}"
