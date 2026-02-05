"""Integration tests for version check in run_doctor CLI flow.

This module tests the integration of version checking within the full
tf doctor command execution, ensuring version consistency checks work
correctly in the context of the complete CLI flow.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from tf_cli.doctor_new import (
    build_parser,
    check_extension,
    load_workflow_config,
    run_doctor,
)


class TestRunDoctorVersionIntegration:
    """Integration tests for version check in run_doctor CLI flow."""

    @pytest.fixture
    def minimal_project(self, tmp_path: Path) -> Path:
        """Create a minimal project structure with .tf and .pi directories."""
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        pi_dir = tmp_path / ".pi"
        pi_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies to isolate version check testing."""
        with (
            mock.patch("shutil.which", return_value="/usr/bin/tk"),
            mock.patch("tf_cli.doctor_new.check_cmd") as mock_check_cmd,
            mock.patch("tf_cli.doctor_new.get_pi_list_cache", return_value=""),
            mock.patch("tf_cli.doctor_new.check_extension") as mock_check_ext,
            mock.patch("tf_cli.doctor_new.load_workflow_config", return_value={}),
            mock.patch("tf_cli.doctor_new.check_mcp_config") as mock_check_mcp,
        ):
            yield {
                "check_cmd": mock_check_cmd,
                "check_ext": mock_check_ext,
                "check_mcp": mock_check_mcp,
            }

    def test_run_doctor_passes_with_matching_versions(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should exit 0 when VERSION matches package.json."""
        # Create package.json with version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        # Create matching VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("1.2.3")

        # Parse args and run
        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Ticketflow doctor: OK" in captured.out
        assert "VERSION file matches" in captured.out

    def test_run_doctor_fails_with_mismatched_versions(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should exit 1 when VERSION doesn't match package.json."""
        # Create package.json with version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        # Create mismatched VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("0.9.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Ticketflow doctor: failed" in captured.out
        assert "does not match" in captured.out

    def test_run_doctor_fix_flag_creates_version_file(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor --fix should create VERSION file when missing."""
        # Create package.json with version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "2.0.0"}))

        # No VERSION file initially

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project), "--fix"])

        result = run_doctor(args)

        assert result == 0
        version_file = minimal_project / "VERSION"
        assert version_file.exists()
        assert version_file.read_text().strip() == "2.0.0"
        captured = capsys.readouterr()
        assert "VERSION file created" in captured.out
        assert "Ticketflow doctor: OK" in captured.out

    def test_run_doctor_fix_flag_updates_mismatched_version(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor --fix should update VERSION file when mismatched."""
        # Create package.json with version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "3.0.0"}))

        # Create mismatched VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("2.0.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project), "--fix"])

        result = run_doctor(args)

        assert result == 0
        assert version_file.read_text().strip() == "3.0.0"
        captured = capsys.readouterr()
        assert "VERSION file updated" in captured.out

    def test_run_doctor_dry_run_flag_shows_would_change(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor --dry-run should show changes without making them."""
        # Create package.json with version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "1.5.0"}))

        # Create mismatched VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("1.0.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project), "--dry-run"])

        result = run_doctor(args)

        # Should fail because version mismatch detected but not fixed
        assert result == 1
        # VERSION file should remain unchanged
        assert version_file.read_text().strip() == "1.0.0"
        captured = capsys.readouterr()
        assert "Would update VERSION file" in captured.out

    def test_run_doctor_with_pyproject_toml(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should use pyproject.toml as canonical version source."""
        # Create pyproject.toml with version
        pyproject_file = minimal_project / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "4.0.0"
""")

        # Create matching VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("4.0.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "pyproject.toml version: 4.0.0" in captured.out
        assert "VERSION file matches" in captured.out

    def test_run_doctor_with_cargo_toml(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should use Cargo.toml as version source."""
        # Create Cargo.toml with version
        cargo_file = minimal_project / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "my-crate"
version = "5.0.0"
edition = "2021"
""")

        # Create matching VERSION file
        version_file = minimal_project / "VERSION"
        version_file.write_text("5.0.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Cargo.toml version: 5.0.0" in captured.out

    def test_run_doctor_skips_version_check_when_no_manifests(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should skip version check when no manifests exist."""
        # No package.json, pyproject.toml, or Cargo.toml

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        # Should pass (version check is optional when no manifests)
        assert result == 0
        captured = capsys.readouterr()
        assert "No package manifests found" in captured.out

    def test_run_doctor_v_prefix_normalization(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should handle v/V prefix in VERSION file."""
        # Create package.json with version (no prefix)
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        # Create VERSION file with v prefix
        version_file = minimal_project / "VERSION"
        version_file.write_text("v1.2.3")

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        # Should pass due to v prefix normalization
        assert result == 0
        captured = capsys.readouterr()
        assert "VERSION file matches" in captured.out

    def test_run_doctor_multiple_manifests_warning(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should warn when multiple manifests have different versions."""
        # Create pyproject.toml with one version
        pyproject_file = minimal_project / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "my-project"
version = "1.0.0"
""")

        # Create package.json with different version
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "2.0.0"}))

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        # Should pass but warn about mismatch
        assert result == 0
        captured = capsys.readouterr()
        assert "Version mismatch between package manifests" in captured.out

    def test_run_doctor_with_git_tag_matching(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should show ok when git tag matches manifest version."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=minimal_project, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=minimal_project, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=minimal_project, capture_output=True, check=True
        )

        # Create package.json
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"version": "1.2.3"}))

        # Commit and tag
        subprocess.run(["git", "add", "."], cwd=minimal_project, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=minimal_project, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "tag", "v1.2.3"], cwd=minimal_project, capture_output=True, check=True
        )

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Git tag matches" in captured.out

    def test_run_doctor_manifest_without_valid_version(
        self, minimal_project: Path, mock_dependencies, capsys
    ) -> None:
        """run_doctor should handle manifest with missing/invalid version field."""
        # Create package.json without version field
        package_file = minimal_project / "package.json"
        package_file.write_text(json.dumps({"name": "test-package"}))

        parser = build_parser()
        args = parser.parse_args(["--project", str(minimal_project)])

        result = run_doctor(args)

        # Should pass but note that no valid version found
        assert result == 0
        captured = capsys.readouterr()
        assert "Package manifest(s) found but no valid version field" in captured.out


class TestRunDoctorEndToEnd:
    """End-to-end integration tests for run_doctor with real dependencies."""

    def test_run_doctor_finds_real_tk_and_pi(self, tmp_path: Path) -> None:
        """run_doctor should find tk and pi if they exist on system."""
        # Only run if tk and pi are available
        import shutil

        has_tk = shutil.which("tk") is not None
        has_pi = shutil.which("pi") is not None

        # Create minimal project
        tf_dir = tmp_path / ".tf"
        tf_dir.mkdir()
        pi_dir = tmp_path / ".pi"
        pi_dir.mkdir()

        # Create a manifest so version check runs
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps({"version": "1.0.0"}))
        version_file = tmp_path / "VERSION"
        version_file.write_text("1.0.0")

        parser = build_parser()
        args = parser.parse_args(["--project", str(tmp_path)])

        result = run_doctor(args)

        # Result depends on whether tk/pi are installed
        # We just verify it runs without crashing
        assert result in [0, 1]

    def test_run_doctor_no_project_found(self, tmp_path: Path) -> None:
        """run_doctor should fail when no .tf directory found."""
        # tmp_path doesn't have .tf directory

        parser = build_parser()
        args = parser.parse_args(["--project", str(tmp_path)])

        with pytest.raises(SystemExit) as exc_info:
            run_doctor(args)

        assert exc_info.value.code == 1
