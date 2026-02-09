"""Tests for tf.update module using asset_planner."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf import update
from tf.asset_planner import AssetAction, AssetEntry, AssetPlan


class TestResolveTargetBase:
    """Tests for resolve_target_base function."""

    def test_uses_project_arg(self, tmp_path: Path) -> None:
        """Should use project argument."""
        args = mock.Mock(project=str(tmp_path / "project"), global_install=False)
        result = update.resolve_target_base(args)
        assert result == tmp_path / "project" / ".pi"

    def test_uses_global_when_flag_set(self, tmp_path: Path) -> None:
        """Should use global path when --global flag set."""
        with mock.patch("tf.update.Path.home", return_value=tmp_path / "home"):
            args = mock.Mock(project=None, global_install=True)
            result = update.resolve_target_base(args)
            assert result == tmp_path / "home" / ".pi" / "agent"

    def test_uses_cwd_pi_when_exists(self, tmp_path: Path) -> None:
        """Should use cwd/.pi when it exists."""
        (tmp_path / ".pi").mkdir()
        with mock.patch("tf.update.Path.cwd", return_value=tmp_path):
            args = mock.Mock(project=None, global_install=False)
            result = update.resolve_target_base(args)
            assert result == tmp_path / ".pi"

    def test_falls_back_to_global(self, tmp_path: Path) -> None:
        """Should fall back to global when no .pi in cwd."""
        with mock.patch("tf.update.Path.cwd", return_value=tmp_path):
            with mock.patch("tf.update.Path.home", return_value=tmp_path / "home"):
                args = mock.Mock(project=None, global_install=False)
                result = update.resolve_target_base(args)
                assert result == tmp_path / "home" / ".pi" / "agent"


class TestPromptYesNo:
    """Tests for prompt_yes_no function."""

    def test_yes_input_with_default_yes(self) -> None:
        """Should return True for 'y' input with default_yes=True."""
        with mock.patch("builtins.input", return_value="y"):
            result = update.prompt_yes_no("Continue?", default_yes=True)
            assert result is True

    def test_yes_input_with_default_no(self) -> None:
        """Should return True for 'y' input with default_yes=False."""
        with mock.patch("builtins.input", return_value="y"):
            result = update.prompt_yes_no("Continue?", default_yes=False)
            assert result is True

    def test_no_input_with_default_yes(self) -> None:
        """Should return False for 'n' input with default_yes=True."""
        with mock.patch("builtins.input", return_value="n"):
            result = update.prompt_yes_no("Continue?", default_yes=True)
            assert result is False

    def test_no_input_with_default_no(self) -> None:
        """Should return False for 'n' input with default_yes=False."""
        with mock.patch("builtins.input", return_value="n"):
            result = update.prompt_yes_no("Continue?", default_yes=False)
            assert result is False

    def test_empty_input_uses_default_yes(self) -> None:
        """Should return True for empty input with default_yes=True."""
        with mock.patch("builtins.input", return_value=""):
            result = update.prompt_yes_no("Continue?", default_yes=True)
            assert result is True

    def test_empty_input_uses_default_no(self) -> None:
        """Should return False for empty input with default_yes=False."""
        with mock.patch("builtins.input", return_value=""):
            result = update.prompt_yes_no("Continue?", default_yes=False)
            assert result is False

    def test_case_insensitive_yes(self) -> None:
        """Should handle 'Y' input case-insensitively."""
        with mock.patch("builtins.input", return_value="Y"):
            result = update.prompt_yes_no("Continue?", default_yes=False)
            assert result is True

    def test_yes_with_extra_whitespace(self) -> None:
        """Should handle 'yes' with extra whitespace."""
        with mock.patch("builtins.input", return_value="  yes  "):
            result = update.prompt_yes_no("Continue?", default_yes=False)
            assert result is True


class TestRunUpdate:
    """Tests for run_update function using asset_planner."""

    def test_no_updates_available(self, tmp_path: Path) -> None:
        """Should report when no updates are available."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        args = mock.Mock(project=str(tmp_path), global_install=False)

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([], []),
        ):
            result = update.run_update(args)

        assert result == 0

    def test_updates_available_and_confirmed(self, tmp_path: Path) -> None:
        """Should update files when updates available and user confirms."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        args = mock.Mock(project=str(tmp_path), global_install=False)

        # Create a mock update plan
        mock_plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md"),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.UPDATE,
        )

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([mock_plan], []),
        ):
            with mock.patch("tf.update.prompt_yes_no", return_value=True):
                with mock.patch(
                    "tf.asset_planner.update_assets",
                    return_value=mock.Mock(updated=1, skipped=0, errors=0, error_details=[]),
                ) as mock_update:
                    result = update.run_update(args)

        assert result == 0
        mock_update.assert_called_once()

    def test_updates_cancelled_by_user(self, tmp_path: Path) -> None:
        """Should cancel when user declines update."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        args = mock.Mock(project=str(tmp_path), global_install=False)

        mock_plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md"),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.UPDATE,
        )

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([mock_plan], []),
        ):
            with mock.patch("tf.update.prompt_yes_no", return_value=False):
                result = update.run_update(args)

        assert result == 0

    def test_errors_during_check(self, tmp_path: Path) -> None:
        """Should report errors during update check."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        args = mock.Mock(project=str(tmp_path), global_install=False)

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([],["Failed to load manifest"]),
        ):
            result = update.run_update(args)

        assert result == 1

    def test_errors_during_update(self, tmp_path: Path) -> None:
        """Should report errors during update execution."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        args = mock.Mock(project=str(tmp_path), global_install=False)

        mock_plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md"),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.UPDATE,
        )

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([mock_plan], []),
        ):
            with mock.patch("tf.update.prompt_yes_no", return_value=True):
                with mock.patch(
                    "tf.asset_planner.update_assets",
                    return_value=mock.Mock(updated=0, skipped=0, errors=1, error_details=["agents/test.md: failed"]),
                ):
                    result = update.run_update(args)

        assert result == 1


class TestBuildParser:
    """Tests for build_parser function."""

    def test_parser_has_project_option(self) -> None:
        """Parser should have --project option."""
        parser = update.build_parser()
        args = parser.parse_args(["--project", "/some/path"])
        assert args.project == "/some/path"

    def test_parser_has_global_flag(self) -> None:
        """Parser should have --global flag."""
        parser = update.build_parser()
        args = parser.parse_args(["--global"])
        assert args.global_install is True


class TestMain:
    """Tests for main function."""

    def test_runs_update_successfully(self, tmp_path: Path) -> None:
        """Should run update and return result."""
        (tmp_path / ".pi").mkdir(parents=True)
        (tmp_path / ".tf").mkdir(parents=True)

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([], []),
        ):
            result = update.main(["--project", str(tmp_path)])
            assert result == 0

    def test_creates_target_base_if_missing(self, tmp_path: Path) -> None:
        """Should create target base directory if it doesn't exist."""
        project_path = tmp_path / "new" / "project"
        project_path.mkdir(parents=True)

        with mock.patch(
            "tf.asset_planner.check_for_updates",
            return_value=([], []),
        ):
            result = update.main(["--project", str(project_path)])

        assert result == 0

    def test_parses_args(self, tmp_path: Path) -> None:
        """Should parse command line arguments."""
        project_path = tmp_path / "project"
        project_path.mkdir(parents=True)

        with mock.patch("tf.update.run_update") as mock_update:
            update.main(["--project", str(project_path)])
            mock_update.assert_called_once()
