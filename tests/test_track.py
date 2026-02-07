"""Tests for tf_cli.track module."""
from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf_cli import track


class TestResolveFilesChanged:
    """Tests for resolve_files_changed function."""

    def test_with_path_arg(self, tmp_path: Path) -> None:
        """Should use path argument when provided."""
        result = track.resolve_files_changed(str(tmp_path / "custom.txt"))
        assert result == tmp_path / "custom.txt"

    def test_with_env_tf_files_changed(self, tmp_path: Path) -> None:
        """Should use TF_FILES_CHANGED environment variable."""
        env_path = str(tmp_path / "env_file.txt")
        with mock.patch.dict(os.environ, {"TF_FILES_CHANGED": env_path}):
            result = track.resolve_files_changed(None)
            assert result == Path(env_path)

    def test_with_env_tf_chain_dir(self, tmp_path: Path) -> None:
        """Should use TF_CHAIN_DIR environment variable."""
        with mock.patch.dict(os.environ, {"TF_CHAIN_DIR": str(tmp_path)}):
            result = track.resolve_files_changed(None)
            assert result == tmp_path / "files_changed.txt"

    def test_default_path(self, tmp_path: Path) -> None:
        """Should default to cwd/files_changed.txt."""
        with mock.patch("tf_cli.track.Path.cwd", return_value=tmp_path):
            result = track.resolve_files_changed(None)
            assert result == tmp_path / "files_changed.txt"

    def test_relative_path_becomes_absolute(self, tmp_path: Path) -> None:
        """Should convert relative path to absolute."""
        with mock.patch("tf_cli.track.Path.cwd", return_value=tmp_path):
            result = track.resolve_files_changed("relative/path.txt")
            assert result == tmp_path / "relative" / "path.txt"


class TestMain:
    """Tests for main function."""

    def test_track_file(self, tmp_path: Path) -> None:
        """Should track a new file path."""
        files_changed = tmp_path / "files_changed.txt"
        file_to_track = tmp_path / "src" / "test.py"

        with mock.patch("tf_cli.track.resolve_files_changed", return_value=files_changed):
            result = track.main([str(file_to_track)])

        assert result == 0
        assert files_changed.exists()
        content = files_changed.read_text()
        assert str(file_to_track) in content

    def test_track_duplicate_file(self, tmp_path: Path) -> None:
        """Should not duplicate entries for same file."""
        files_changed = tmp_path / "files_changed.txt"
        file_to_track = tmp_path / "test.py"
        files_changed.write_text(f"{file_to_track}\n")

        with mock.patch("tf_cli.track.resolve_files_changed", return_value=files_changed):
            result = track.main([str(file_to_track)])

        assert result == 0
        content = files_changed.read_text()
        assert content.count(str(file_to_track)) == 1

    def test_track_multiple_files(self, tmp_path: Path) -> None:
        """Should track multiple different files."""
        files_changed = tmp_path / "files_changed.txt"
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"

        with mock.patch("tf_cli.track.resolve_files_changed", return_value=files_changed):
            track.main([str(file1)])
            track.main([str(file2)])

        content = files_changed.read_text()
        assert str(file1) in content
        assert str(file2) in content

    def test_track_relative_path(self, tmp_path: Path) -> None:
        """Should convert relative path to absolute."""
        files_changed = tmp_path / "files_changed.txt"

        with mock.patch("tf_cli.track.Path.cwd", return_value=tmp_path):
            with mock.patch("tf_cli.track.resolve_files_changed", return_value=files_changed):
                result = track.main(["src/test.py"])

        assert result == 0
        content = files_changed.read_text()
        assert str(tmp_path / "src" / "test.py") in content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Should create parent directories for files_changed.txt."""
        files_changed = tmp_path / "nested" / "deep" / "files_changed.txt"
        file_to_track = tmp_path / "test.py"

        with mock.patch("tf_cli.track.resolve_files_changed", return_value=files_changed):
            result = track.main([str(file_to_track)])

        assert result == 0
        assert files_changed.exists()


@pytest.mark.integration
class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Test complete tracking workflow."""
        files_changed = tmp_path / "artifacts" / "files_changed.txt"
        file1 = tmp_path / "module.py"
        file2 = tmp_path / "tests" / "test_module.py"

        # Track first file
        with mock.patch.dict(os.environ, {"TF_FILES_CHANGED": str(files_changed)}):
            result1 = track.main([str(file1)])
        assert result1 == 0

        # Track second file
        with mock.patch.dict(os.environ, {"TF_FILES_CHANGED": str(files_changed)}):
            result2 = track.main([str(file2)])
        assert result2 == 0

        content = files_changed.read_text()
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        assert len(lines) == 2
        assert str(file1) in lines
        assert str(file2) in lines
