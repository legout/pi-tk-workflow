"""Tests for tf_cli.version and tf_cli._version modules."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf_cli import version, _version


class TestResolveRepoRoot:
    """Tests for _resolve_repo_root function."""

    def test_finds_repo_with_tf_and_version(self, tmp_path: Path) -> None:
        """Should find repo root with .tf dir and VERSION file."""
        (tmp_path / ".tf").mkdir()
        (tmp_path / "VERSION").write_text("1.0.0")
        (tmp_path / "tf_cli").mkdir()

        with mock.patch.object(Path, "resolve", return_value=tmp_path / "tf_cli" / "version.py"):
            with mock.patch("tf_cli.version.Path.parents", property(lambda self: [tmp_path])):
                result = version._resolve_repo_root()
                assert result == tmp_path


class TestReadVersionFile:
    """Tests for _read_version_file function."""

    def test_reads_version_file(self, tmp_path: Path) -> None:
        """Should read version from file."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("  1.2.3  \n")

        result = version._read_version_file(version_file)
        assert result == "1.2.3"

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        """Should return None for missing file."""
        result = version._read_version_file(tmp_path / "nonexistent")
        assert result is None

    def test_returns_none_on_os_error(self, tmp_path: Path) -> None:
        """Should return None on OS error."""
        with mock.patch("pathlib.Path.is_file", return_value=True):
            with mock.patch("pathlib.Path.read_text", side_effect=PermissionError()):
                result = version._read_version_file(tmp_path / "VERSION")
                assert result is None


class TestGetVersion:
    """Tests for get_version function."""

    def test_returns_version_from_repo_root(self, tmp_path: Path) -> None:
        """Should return version from repo root."""
        (tmp_path / "VERSION").write_text("1.2.3")

        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            result = version.get_version()
            assert result == "1.2.3"

    def test_falls_back_to_module_parent(self, tmp_path: Path) -> None:
        """Should fall back to module parent directory."""
        parent = tmp_path / "package"
        parent.mkdir()
        (parent / "VERSION").write_text("2.0.0")

        with mock.patch("tf_cli.version._resolve_repo_root", return_value=None):
            with mock.patch("pathlib.Path.parent", property(lambda self: parent)):
                result = version.get_version()
                assert result == "2.0.0"

    def test_returns_unknown_when_no_version_found(self) -> None:
        """Should return 'unknown' when no version found."""
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=None):
            with mock.patch("pathlib.Path.is_file", return_value=False):
                result = version.get_version()
                assert result == "unknown"


class TestVersionModule:
    """Tests for version module exports."""

    def test_version_exported(self) -> None:
        """Should have __version__ exported."""
        assert hasattr(version, "__version__")
        assert version.__version__ is not None

    def test_get_version_exported(self) -> None:
        """Should have get_version exported."""
        assert hasattr(version, "get_version")
        assert callable(version.get_version)


class TestVersionCompatibility:
    """Tests for backward compatibility module."""

    def test_version_import_from_compat(self) -> None:
        """Should be able to import from _version module."""
        assert hasattr(_version, "get_version")
        assert hasattr(_version, "__version__")
        assert callable(_version.get_version)

    def test_version_same_as_main_module(self) -> None:
        """_version exports should match version module."""
        assert _version.get_version is version.get_version
