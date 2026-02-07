"""Tests for tf doctor version check functionality.

This module contains comprehensive tests for the version check functionality
in tf_cli/doctor.py, covering all version-related functions with
normal paths, edge cases, and error conditions.

Uses pytest fixtures (tmp_path, capsys) for isolated test environments
and unittest.mock for testing error conditions.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf_cli.doctor import (
    check_version_consistency,
    detect_manifest_versions,
    get_cargo_version,
    get_git_tag_version,
    get_package_version,
    get_pyproject_version,
    get_version_file_version,
    normalize_version,
    read_toml,
    sync_version_file,
)


class TestGetPackageVersion:
    """Tests for get_package_version function."""

    def test_returns_version_from_package_json(self, tmp_path: Path) -> None:
        """Should return version string from valid package.json."""

        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        result = get_package_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_when_package_json_missing(self, tmp_path: Path) -> None:
        """Should return None when package.json doesn't exist."""
        result = get_package_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_missing(self, tmp_path: Path) -> None:
        """Should return None when version field is missing."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"name": "test-package"}))
        
        result = get_package_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_is_empty_string(self, tmp_path: Path) -> None:
        """Should return None when version is empty string."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": ""}))
        
        result = get_package_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_is_whitespace(self, tmp_path: Path) -> None:
        """Should return None when version is whitespace only."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "   "}))
        
        result = get_package_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_is_not_string(self, tmp_path: Path) -> None:
        """Should return None when version is not a string (e.g., number)."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": 123}))
        
        result = get_package_version(tmp_path)
        
        assert result is None

    def test_strips_whitespace_from_version(self, tmp_path: Path) -> None:
        """Should strip whitespace from version string."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "  1.2.3  "}))
        
        result = get_package_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_on_invalid_json(self, tmp_path: Path) -> None:
        """Should return None when package.json contains invalid JSON."""
        package_file = tmp_path / "package.json"
        package_file.write_text("not valid json")
        
        result = get_package_version(tmp_path)
        
        assert result is None


class TestGetPyprojectVersion:
    """Tests for get_pyproject_version function."""

    def test_returns_version_from_pyproject_toml(self, tmp_path: Path) -> None:
        """Should return version string from valid pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "1.2.3"
description = "A test project"
""")
        
        result = get_pyproject_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_when_pyproject_toml_missing(self, tmp_path: Path) -> None:
        """Should return None when pyproject.toml doesn't exist."""
        result = get_pyproject_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_missing(self, tmp_path: Path) -> None:
        """Should return None when version field is missing from [project]."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
description = "A test project"
""")
        
        result = get_pyproject_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_project_section_missing(self, tmp_path: Path) -> None:
        """Should return None when [project] section is missing."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[build-system]
requires = ["setuptools"]
""")
        
        result = get_pyproject_version(tmp_path)
        
        assert result is None

    def test_strips_whitespace_from_version(self, tmp_path: Path) -> None:
        """Should strip whitespace from version string."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "  1.2.3  "
""")
        
        result = get_pyproject_version(tmp_path)
        
        assert result == "1.2.3"


class TestGetCargoVersion:
    """Tests for get_cargo_version function."""

    def test_returns_version_from_cargo_toml(self, tmp_path: Path) -> None:
        """Should return version string from valid Cargo.toml."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
version = "1.2.3"
edition = "2021"
""")
        
        result = get_cargo_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_when_cargo_toml_missing(self, tmp_path: Path) -> None:
        """Should return None when Cargo.toml doesn't exist."""
        result = get_cargo_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_missing(self, tmp_path: Path) -> None:
        """Should return None when version field is missing from [package]."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
edition = "2021"
""")
        
        result = get_cargo_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_package_section_missing(self, tmp_path: Path) -> None:
        """Should return None when [package] section is missing."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[dependencies]
serde = "1.0"
""")
        
        result = get_cargo_version(tmp_path)
        
        assert result is None

    def test_strips_whitespace_from_version(self, tmp_path: Path) -> None:
        """Should strip whitespace from version string."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
version = "  1.2.3  "
""")
        
        result = get_cargo_version(tmp_path)
        
        assert result == "1.2.3"


class TestReadToml:
    """Tests for read_toml function."""

    def test_parses_simple_toml(self, tmp_path: Path) -> None:
        """Should parse a simple TOML file."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[project]
name = "test"
version = "1.0.0"

[build-system]
requires = ["setuptools"]
""")
        
        result = read_toml(toml_file)
        
        assert result["project"]["name"] == "test"
        assert result["project"]["version"] == "1.0.0"

    def test_parses_nested_sections(self, tmp_path: Path) -> None:
        """Should parse TOML with nested sections."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[package]
name = "my-package"
version = "2.0.0"

[dependencies.serde]
version = "1.0"
""")
        
        result = read_toml(toml_file)
        
        assert result["package"]["name"] == "my-package"
        assert result["dependencies"]["serde"]["version"] == "1.0"

    def test_skips_comments(self, tmp_path: Path) -> None:
        """Should skip full-line comment lines."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
# This is a comment
[project]
name = "test"
version = "1.0.0"
# Another comment
""")
        
        result = read_toml(toml_file)
        
        assert result["project"]["name"] == "test"
        assert result["project"]["version"] == "1.0.0"

    def test_returns_empty_dict_for_missing_file(self, tmp_path: Path) -> None:
        """Should return empty dict when file doesn't exist."""
        result = read_toml(tmp_path / "nonexistent.toml")
        
        assert result == {}

    def test_parses_boolean_values(self, tmp_path: Path) -> None:
        """Should parse boolean values."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[tool]
enabled = true
disabled = false
""")

        result = read_toml(toml_file)

        assert result["tool"]["enabled"] is True
        assert result["tool"]["disabled"] is False

    def test_parses_inline_comments(self, tmp_path: Path) -> None:
        """Should strip inline comments from values."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[project]
name = "test"  # project name
version = "1.2.3"  # release version

[tool]
# This is a full-line comment
value = "data"  # inline comment
""")

        result = read_toml(toml_file)

        assert result["project"]["name"] == "test"
        assert result["project"]["version"] == "1.2.3"
        assert result["tool"]["value"] == "data"

    def test_parses_inline_comments_with_hash_in_quotes(self, tmp_path: Path) -> None:
        """Should not strip # inside quoted strings."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text('''
[project]
name = "test # not a comment"
version = "1.0.0"  # real comment
''')

        result = read_toml(toml_file)

        assert result["project"]["name"] == "test # not a comment"
        assert result["project"]["version"] == "1.0.0"


class TestDetectManifestVersions:
    """Tests for detect_manifest_versions function."""

    def test_detects_single_manifest(self, tmp_path: Path) -> None:
        """Should detect a single manifest file."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        canonical, canonical_manifest, found, versions = detect_manifest_versions(tmp_path)

        assert canonical == "1.2.3"
        assert canonical_manifest == "package.json"
        assert found == ["package.json"]
        assert versions == {"package.json": "1.2.3"}

    def test_detects_multiple_manifests(self, tmp_path: Path) -> None:
        """Should detect multiple manifest files."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "1.0.0"
""")
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "2.0.0"}))

        canonical, canonical_manifest, found, versions = detect_manifest_versions(tmp_path)

        # pyproject.toml has priority
        assert canonical == "1.0.0"
        assert canonical_manifest == "pyproject.toml"
        assert found == ["pyproject.toml", "package.json"]
        assert versions == {"pyproject.toml": "1.0.0", "package.json": "2.0.0"}

    def test_handles_invalid_version_in_manifest(self, tmp_path: Path) -> None:
        """Should handle manifests with invalid/missing versions."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
""")
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        canonical, canonical_manifest, found, versions = detect_manifest_versions(tmp_path)

        # pyproject.toml exists but has no version, so package.json becomes canonical
        assert canonical == "1.2.3"
        assert canonical_manifest == "package.json"
        assert found == ["pyproject.toml", "package.json"]
        assert versions == {"pyproject.toml": "invalid", "package.json": "1.2.3"}

    def test_returns_none_when_no_manifests(self, tmp_path: Path) -> None:
        """Should return None when no manifests exist."""
        canonical, canonical_manifest, found, versions = detect_manifest_versions(tmp_path)

        assert canonical is None
        assert canonical_manifest is None
        assert found == []
        assert versions == {}


class TestGetVersionFileVersion:
    """Tests for get_version_file_version function."""

    def test_returns_version_from_version_file(self, tmp_path: Path) -> None:
        """Should return version string from VERSION file."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")
        
        result = get_version_file_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_when_version_file_missing(self, tmp_path: Path) -> None:
        """Should return None when VERSION file doesn't exist."""
        result = get_version_file_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_version_file_empty(self, tmp_path: Path) -> None:
        """Should return None when VERSION file is empty."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("")
        
        result = get_version_file_version(tmp_path)
        
        assert result is None

    def test_strips_whitespace_and_newlines(self, tmp_path: Path) -> None:
        """Should strip whitespace and newlines from version."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("  1.2.3\n\n  ")
        
        result = get_version_file_version(tmp_path)
        
        assert result == "1.2.3"

    def test_returns_none_on_read_error(self, tmp_path: Path) -> None:
        """Should return None when VERSION file cannot be read."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")
        
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("Permission denied")):
            result = get_version_file_version(tmp_path)
        
        assert result is None

    def test_prints_warning_on_permission_error(self, tmp_path: Path, capsys) -> None:
        """Should print warning when VERSION file cannot be read due to permissions."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")
        
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("Permission denied")):
            get_version_file_version(tmp_path)
        
        captured = capsys.readouterr()
        assert "[warn] VERSION file exists but cannot be read" in captured.out
        assert "Permission denied" in captured.out

    def test_prints_warning_on_encoding_error(self, tmp_path: Path, capsys) -> None:
        """Should print warning when VERSION file has encoding issues."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")
        
        with mock.patch.object(Path, "read_text", side_effect=UnicodeDecodeError(
            'utf-8', b'invalid', 0, 1, 'invalid start byte'
        )):
            get_version_file_version(tmp_path)
        
        captured = capsys.readouterr()
        assert "[warn] VERSION file has encoding issues" in captured.out


class TestNormalizeVersion:
    """Tests for normalize_version function."""

    @pytest.mark.parametrize(
        "input_version,expected",
        [
            ("1.2.3", "1.2.3"),
            ("2.0.0-beta", "2.0.0-beta"),
            ("v1.2.3", "1.2.3"),
            ("v2.0.0", "2.0.0"),
            ("V1.2.3", "1.2.3"),
            ("V2.0.0", "2.0.0"),
            ("", ""),
            ("v1.0.0-alpha", "1.0.0-alpha"),
            ("v1.0.0v2", "1.0.0v2"),
        ],
    )
    def test_normalize_version(self, input_version: str, expected: str) -> None:
        """Should correctly normalize version strings."""

        result = normalize_version(input_version)
        assert result == expected


class TestSyncVersionFile:
    """Tests for sync_version_file function."""

    def test_creates_version_file_when_missing(self, tmp_path: Path) -> None:
        """Should create VERSION file when it doesn't exist."""
        version_file = tmp_path / "VERSION"
        
        result = sync_version_file(tmp_path, "1.2.3")
        
        assert result is True
        assert version_file.exists()
        assert version_file.read_text().strip() == "1.2.3"

    def test_updates_existing_version_file(self, tmp_path: Path) -> None:
        """Should update VERSION file when it exists with different version."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("0.9.0")
        
        result = sync_version_file(tmp_path, "1.2.3")
        
        assert result is True
        assert version_file.read_text().strip() == "1.2.3"

    def test_avoids_unnecessary_write_when_content_unchanged(self, tmp_path: Path) -> None:
        """Should skip write when file already has correct content with newline."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3\n")
        original_stat = version_file.stat()
        
        result = sync_version_file(tmp_path, "1.2.3")
        
        assert result is True
        new_stat = version_file.stat()
        # Verify file was not rewritten (mtime unchanged)
        assert new_stat.st_mtime == original_stat.st_mtime

    def test_writes_when_content_differs(self, tmp_path: Path) -> None:
        """Should update file when version differs (no trailing newline case)."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")  # No newline
        
        result = sync_version_file(tmp_path, "1.2.3")
        
        assert result is True
        assert version_file.read_text() == "1.2.3\n"

    def test_adds_newline_to_version(self, tmp_path: Path) -> None:
        """Should add trailing newline to version in file."""
        version_file = tmp_path / "VERSION"
        
        sync_version_file(tmp_path, "1.2.3")
        
        assert version_file.read_text() == "1.2.3\n"

    def test_returns_false_on_write_error(self, tmp_path: Path) -> None:
        """Should return False when VERSION file cannot be written."""
        with mock.patch.object(Path, "write_text", side_effect=PermissionError("Permission denied")):
            result = sync_version_file(tmp_path, "1.2.3")
        
        assert result is False


class TestCheckVersionConsistency:
    """Tests for check_version_consistency function."""

    def test_returns_true_when_no_package_json(self, tmp_path: Path, capsys) -> None:
        """Should return True when no package manifests exist."""
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "No package manifests found" in captured.out

    def test_returns_true_when_package_json_has_no_version(self, tmp_path: Path, capsys) -> None:
        """Should return True when package.json has no version field."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"name": "test"}))
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "Package manifest(s) found but no valid version field" in captured.out

    def test_returns_true_when_only_package_json_exists(self, tmp_path: Path, capsys) -> None:
        """Should return True when only package.json exists with valid version."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "[ok] package.json version: 1.2.3" in captured.out
        assert "No VERSION file found" in captured.out

    def test_returns_true_when_versions_match(self, tmp_path: Path, capsys) -> None:
        """Should return True when VERSION file matches package.json."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.2.3")
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "VERSION file matches" in captured.out

    def test_returns_true_with_v_prefix_normalization(self, tmp_path: Path, capsys) -> None:
        """Should return True when versions match after v prefix normalization."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("v1.2.3")
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "VERSION file matches" in captured.out

    def test_returns_false_when_versions_mismatch(self, tmp_path: Path, capsys) -> None:
        """Should return False when VERSION file doesn't match package.json."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("0.9.0")
        
        result = check_version_consistency(tmp_path)
        
        assert result is False
        captured = capsys.readouterr()
        assert "does not match" in captured.out

    def test_fix_creates_version_file_when_missing(self, tmp_path: Path, capsys) -> None:
        """Should create VERSION file when fix=True and file is missing."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        result = check_version_consistency(tmp_path, fix=True)
        
        assert result is True
        version_file = tmp_path / "VERSION"
        assert version_file.exists()
        assert version_file.read_text().strip() == "1.2.3"
        captured = capsys.readouterr()
        assert "VERSION file created" in captured.out

    def test_fix_updates_mismatched_version(self, tmp_path: Path, capsys) -> None:
        """Should update VERSION file when fix=True and versions mismatch."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("0.9.0")
        
        result = check_version_consistency(tmp_path, fix=True)
        
        assert result is True
        assert version_file.read_text().strip() == "1.2.3"
        captured = capsys.readouterr()
        assert "VERSION file updated" in captured.out

    def test_dry_run_shows_would_create(self, tmp_path: Path, capsys) -> None:
        """Should show what would be created without creating in dry-run mode."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        result = check_version_consistency(tmp_path, dry_run=True)
        
        assert result is False
        version_file = tmp_path / "VERSION"
        assert not version_file.exists()
        captured = capsys.readouterr()
        assert "Would create VERSION file" in captured.out

    def test_dry_run_shows_would_update(self, tmp_path: Path, capsys) -> None:
        """Should show what would be updated without updating in dry-run mode."""
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("0.9.0")
        
        result = check_version_consistency(tmp_path, dry_run=True)
        
        assert result is False
        assert version_file.read_text().strip() == "0.9.0"  # Unchanged
        captured = capsys.readouterr()
        assert "Would update VERSION file" in captured.out


class TestMultiLanguageVersionCheck:
    """Tests for multi-language version checking with pyproject.toml and Cargo.toml."""

    def test_pyproject_toml_priority_over_package_json(self, tmp_path: Path, capsys) -> None:
        """Should use pyproject.toml as canonical source when both exist."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "2.0.0"
""")
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.0.0"}))
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "[ok] pyproject.toml version: 2.0.0" in captured.out
        assert "[ok] package.json version: 1.0.0" in captured.out
        assert "Would create VERSION file" in captured.out or "No VERSION file found" in captured.out

    def test_warns_on_manifest_version_mismatch(self, tmp_path: Path, capsys) -> None:
        """Should warn when multiple manifests have different versions."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "1.0.0"
""")
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
version = "2.0.0"
""")
        
        result = check_version_consistency(tmp_path)
        
        assert result is True  # Warning, not failure
        captured = capsys.readouterr()
        assert "Version mismatch between package manifests" in captured.out
        assert "pyproject.toml = 1.0.0" in captured.out
        assert "Cargo.toml = 2.0.0" in captured.out

    def test_cargo_toml_alone(self, tmp_path: Path, capsys) -> None:
        """Should work with only Cargo.toml present."""
        cargo_file = tmp_path / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
version = "3.0.0"
""")
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "[ok] Cargo.toml version: 3.0.0" in captured.out

    def test_pyproject_toml_alone(self, tmp_path: Path, capsys) -> None:
        """Should work with only pyproject.toml present."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "4.0.0"
""")
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "[ok] pyproject.toml version: 4.0.0" in captured.out

    def test_version_file_syncs_with_pyproject(self, tmp_path: Path, capsys) -> None:
        """Should sync VERSION file with pyproject.toml when using --fix."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "5.0.0"
""")
        
        result = check_version_consistency(tmp_path, fix=True)
        
        assert result is True
        version_file = tmp_path / "VERSION"
        assert version_file.exists()
        assert version_file.read_text().strip() == "5.0.0"
        captured = capsys.readouterr()
        assert "VERSION file created" in captured.out


class TestGetGitTagVersion:
    """Tests for get_git_tag_version function."""

    def test_returns_tag_when_on_tagged_commit(self, tmp_path: Path) -> None:
        """Should return tag name when on a tagged commit."""
        import subprocess

        # Initialize git repo and create a tag
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        # Create a file and commit
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        
        # Create tag
        subprocess.run(["git", "tag", "v1.2.3"], cwd=tmp_path, capture_output=True, check=True)
        
        result = get_git_tag_version(tmp_path)
        
        # Tag should be normalized (v prefix stripped)
        assert result == "1.2.3"

    def test_returns_none_when_not_on_tagged_commit(self, tmp_path: Path) -> None:
        """Should return None when not on a tagged commit."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        # Create a file and commit
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        
        result = get_git_tag_version(tmp_path)
        
        assert result is None

    def test_returns_none_when_not_git_repo(self, tmp_path: Path) -> None:
        """Should return None when not in a git repo."""
        result = get_git_tag_version(tmp_path)
        
        assert result is None

    def test_normalizes_v_prefix(self, tmp_path: Path) -> None:
        """Should normalize tags with v/V prefix."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        
        # Test uppercase V prefix
        subprocess.run(["git", "tag", "V2.0.0"], cwd=tmp_path, capture_output=True, check=True)
        
        result = get_git_tag_version(tmp_path)
        
        assert result == "2.0.0"


class TestGitTagVersionCheck:
    """Tests for git tag version checking in check_version_consistency."""

    def test_shows_ok_when_git_tag_matches(self, tmp_path: Path, capsys) -> None:
        """Should show [ok] when git tag matches manifest version."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        # Create package.json
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        # Commit and tag
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v1.2.3"], cwd=tmp_path, capture_output=True, check=True)
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        assert "[ok] Git tag matches: 1.2.3" in captured.out

    def test_shows_warning_when_git_tag_mismatches(self, tmp_path: Path, capsys) -> None:
        """Should show [warn] when git tag doesn't match manifest version."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        # Create package.json with version 1.2.3
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        # Commit and tag with different version
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v2.0.0"], cwd=tmp_path, capture_output=True, check=True)
        
        result = check_version_consistency(tmp_path)
        
        # Should not fail, just warn
        assert result is True
        captured = capsys.readouterr()
        assert "[warn] Git tag (2.0.0) does not match package.json (1.2.3)" in captured.out

    def test_no_git_tag_check_when_not_tagged(self, tmp_path: Path, capsys) -> None:
        """Should skip git tag check when not on a tagged commit."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True, check=True)
        
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))
        
        # Commit but don't tag
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True)
        
        result = check_version_consistency(tmp_path)
        
        assert result is True
        captured = capsys.readouterr()
        # Should not mention git tag at all
        assert "Git tag" not in captured.out
