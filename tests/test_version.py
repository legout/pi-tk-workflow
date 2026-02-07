"""Tests for tf_cli.version and tf_cli._version modules."""
from __future__ import annotations

import json
import subprocess
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


class TestGetGitTagVersion:
    """Tests for _get_git_tag_version function."""

    def test_returns_exact_tag_without_v_prefix(self, tmp_path: Path) -> None:
        """Should return exact tag with 'v' prefix stripped."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                returncode=0, stdout="v1.2.3\n", stderr=""
            )
            result = version._get_git_tag_version(tmp_path)
            assert result == "1.2.3"
            mock_run.assert_called_once_with(
                ["git", "describe", "--tags", "--exact-match"],
                capture_output=True,
                text=True,
                cwd=str(tmp_path),
                check=False,
            )

    def test_returns_exact_tag_without_prefix(self, tmp_path: Path) -> None:
        """Should return exact tag without 'v' prefix as-is."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                returncode=0, stdout="1.2.3\n", stderr=""
            )
            result = version._get_git_tag_version(tmp_path)
            assert result == "1.2.3"

    def test_falls_back_to_latest_tag(self, tmp_path: Path) -> None:
        """Should fall back to latest tag if no exact match."""
        def side_effect(cmd, **kwargs):
            if "--exact-match" in cmd:
                return mock.Mock(returncode=128, stdout="", stderr="fatal: no tag exactly matches")
            return mock.Mock(returncode=0, stdout="v2.0.0\n", stderr="")

        with mock.patch("subprocess.run", side_effect=side_effect):
            result = version._get_git_tag_version(tmp_path)
            assert result == "2.0.0"

    def test_returns_none_when_no_git(self, tmp_path: Path) -> None:
        """Should return None when git is not available."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = version._get_git_tag_version(tmp_path)
            assert result is None

    def test_returns_none_when_no_tags(self, tmp_path: Path) -> None:
        """Should return None when no git tags exist."""
        def side_effect(cmd, **kwargs):
            return mock.Mock(returncode=128, stdout="", stderr="fatal: No names found")

        with mock.patch("subprocess.run", side_effect=side_effect):
            result = version._get_git_tag_version(tmp_path)
            assert result is None

    def test_strips_v_prefix_from_latest_tag(self, tmp_path: Path) -> None:
        """Should strip 'v' prefix from latest tag."""
        def side_effect(cmd, **kwargs):
            if "--exact-match" in cmd:
                return mock.Mock(returncode=128, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="v0.5.0-rc1\n", stderr="")

        with mock.patch("subprocess.run", side_effect=side_effect):
            result = version._get_git_tag_version(tmp_path)
            assert result == "0.5.0-rc1"


class TestVerifyPackageJsonVersion:
    """Tests for verify_package_json_version function."""

    def test_returns_ok_when_versions_match(self, tmp_path: Path) -> None:
        """Should return ok=True when package.json matches git tag."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"version": "1.0.0"}))

        with mock.patch("tf_cli.version._get_git_tag_version", return_value="1.0.0"):
            result = version.verify_package_json_version(tmp_path)
            assert result["ok"] is True
            assert result["package_version"] == "1.0.0"
            assert result["git_version"] == "1.0.0"
            assert result["error"] is None

    def test_returns_error_when_versions_mismatch(self, tmp_path: Path) -> None:
        """Should return error when versions don't match."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"version": "1.0.0"}))

        with mock.patch("tf_cli.version._get_git_tag_version", return_value="1.1.0"):
            result = version.verify_package_json_version(tmp_path)
            assert result["ok"] is False
            assert result["package_version"] == "1.0.0"
            assert result["git_version"] == "1.1.0"
            assert "Version mismatch" in result["error"]

    def test_returns_error_when_no_package_json(self, tmp_path: Path) -> None:
        """Should return error when package.json doesn't exist."""
        result = version.verify_package_json_version(tmp_path)
        assert result["ok"] is False
        assert "package.json not found" in result["error"]

    def test_returns_error_when_no_version_in_package_json(self, tmp_path: Path) -> None:
        """Should return error when package.json has no version field."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"name": "test"}))

        result = version.verify_package_json_version(tmp_path)
        assert result["ok"] is False
        assert "No version field" in result["error"]

    def test_returns_error_when_no_git_tag(self, tmp_path: Path) -> None:
        """Should return error when no git tag exists."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"version": "1.0.0"}))

        with mock.patch("tf_cli.version._get_git_tag_version", return_value=None):
            result = version.verify_package_json_version(tmp_path)
            assert result["ok"] is False
            assert "No git tag found" in result["error"]

    def test_returns_error_when_not_in_git_repo(self) -> None:
        """Should return error when not in a git repository."""
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=None):
            result = version.verify_package_json_version()
            assert result["ok"] is False
            assert "Not in a git repository" in result["error"]

    def test_handles_invalid_json(self, tmp_path: Path) -> None:
        """Should handle invalid JSON in package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text("not valid json")

        result = version.verify_package_json_version(tmp_path)
        assert result["ok"] is False
        assert "Error reading package.json" in result["error"]


class TestGetVersionWithGitTagFallback:
    """Tests for get_version git tag fallback."""

    def test_falls_back_to_git_tag_when_no_version_file(self, tmp_path: Path) -> None:
        """Should fall back to git tag when VERSION file not found."""
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            with mock.patch("tf_cli.version._read_version_file", return_value=None):
                with mock.patch("tf_cli.version._get_git_tag_version", return_value="1.5.0"):
                    result = version.get_version()
                    assert result == "1.5.0"

    def test_returns_unknown_when_all_sources_fail(self, tmp_path: Path) -> None:
        """Should return 'unknown' when all version sources fail."""
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            with mock.patch("tf_cli.version._read_version_file", return_value=None):
                with mock.patch("tf_cli.version._get_git_tag_version", return_value=None):
                    result = version.get_version()
                    assert result == "unknown"

    def test_prefers_version_file_over_git_tag(self, tmp_path: Path) -> None:
        """Should prefer VERSION file over git tag."""
        with mock.patch("tf_cli.version._resolve_repo_root", return_value=tmp_path):
            with mock.patch("tf_cli.version._read_version_file", return_value="2.0.0"):
                with mock.patch("tf_cli.version._get_git_tag_version", return_value="1.0.0"):
                    result = version.get_version()
                    assert result == "2.0.0"


class TestPublicAPI:
    """Tests for public API exports."""

    def test_verify_package_json_version_exported(self) -> None:
        """Should have verify_package_json_version exported."""
        assert hasattr(version, "verify_package_json_version")
        assert callable(version.verify_package_json_version)

    def test_all_exports_present(self) -> None:
        """Should have all expected exports in __all__."""
        expected = ["get_version", "verify_package_json_version", "__version__"]
        assert version.__all__ == expected
