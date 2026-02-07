"""Tests for tf_cli.init module."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf_cli import init


class TestInitProject:
    """Tests for init_project function."""

    def test_creates_tf_state_dirs_and_calls_bundle_install(self, tmp_path: Path) -> None:
        """Should create state dirs and install the workflow bundle into the project."""
        with mock.patch("tf_cli.asset_planner.install_bundle", return_value=(0, 0)) as mock_install:
            result = init.init_project(tmp_path)

        assert result == 0
        assert (tmp_path / ".tf").exists()
        assert (tmp_path / ".tf/knowledge").exists()
        assert (tmp_path / ".tf/ralph").exists()
        mock_install.assert_called_once_with(tmp_path)

    def test_handles_install_bundle_failure(self, tmp_path: Path) -> None:
        """Should return error when bundle install fails."""
        with mock.patch(
            "tf_cli.asset_planner.install_bundle",
            side_effect=RuntimeError("Install failed"),
        ):
            result = init.init_project(tmp_path)

        assert result == 1


class TestMain:
    """Tests for main function."""

    def test_rejects_global_flag(self, capsys) -> None:
        """Should reject --global flag."""
        result = init.main(["--global"])
        assert result == 1
        captured = capsys.readouterr()
        assert "project-local" in captured.err

    def test_uses_project_arg(self, tmp_path: Path) -> None:
        """Should use --project argument."""
        project_path = tmp_path / "myproject"

        with mock.patch.object(init, "init_project", return_value=0) as mock_init:
            result = init.main(["--project", str(project_path)])

        assert result == 0
        mock_init.assert_called_once_with(project_path)

    def test_uses_cwd_when_no_project_arg(self, tmp_path: Path) -> None:
        """Should use current directory when no --project."""
        with mock.patch("tf_cli.init.Path.cwd", return_value=tmp_path):
            with mock.patch.object(init, "init_project", return_value=0) as mock_init:
                result = init.main([])

        assert result == 0
        mock_init.assert_called_once_with(tmp_path)

    def test_expands_user_in_project_path(self, tmp_path: Path) -> None:
        """Should expand ~ in project path."""
        with mock.patch("pathlib.Path.expanduser", return_value=tmp_path) as mock_expand:
            with mock.patch.object(init, "init_project", return_value=0):
                init.main(["--project", "~/project"])

        mock_expand.assert_called()
