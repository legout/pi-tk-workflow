"""Tests for tf.asset_planner module."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

pytestmark = pytest.mark.unit

from tf import asset_planner
from tf.asset_planner import AssetAction, AssetEntry, AssetPlan, PlanResult


class TestParseManifest:
    """Tests for manifest parsing."""

    def test_parses_valid_entries(self) -> None:
        """Should parse valid manifest entries."""
        text = """
agents/test.md
skills/test/
prompts/test.md
# This is a comment
   agents/spaces.md

other/file.txt
"""
        result = asset_planner._parse_manifest(text)
        assert "agents/test.md" in result
        assert "skills/test/" in result
        assert "prompts/test.md" in result
        assert "agents/spaces.md" in result
        assert "other/file.txt" in result  # All non-comment lines included
        assert "# This is a comment" not in result

    def test_returns_empty_on_empty_string(self) -> None:
        """Should return empty list for empty string."""
        result = asset_planner._parse_manifest("")
        assert result == []

    def test_skips_comments_and_empty_lines(self) -> None:
        """Should skip comments and empty lines."""
        text = """
# Comment 1
agents/test.md

# Comment 2
   
prompts/test.md
"""
        result = asset_planner._parse_manifest(text)
        assert result == ["agents/test.md", "prompts/test.md"]


class TestClassifyAsset:
    """Tests for asset classification."""

    def test_classifies_agents(self, tmp_path: Path) -> None:
        """Should classify agent files."""
        result = asset_planner.classify_asset("agents/test.md", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".pi" / "agents" / "test.md"
        assert result[1] is False

    def test_classifies_prompts(self, tmp_path: Path) -> None:
        """Should classify prompt files."""
        result = asset_planner.classify_asset("prompts/tf.md", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".pi" / "prompts" / "tf.md"

    def test_classifies_skills(self, tmp_path: Path) -> None:
        """Should classify skill directories."""
        result = asset_planner.classify_asset("skills/workflow/SKILL.md", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".pi" / "skills" / "workflow" / "SKILL.md"

    def test_classifies_config_settings(self, tmp_path: Path) -> None:
        """Should classify config settings."""
        result = asset_planner.classify_asset("config/settings.json", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".tf" / "config" / "settings.json"

    def test_classifies_workflows(self, tmp_path: Path) -> None:
        """Should classify workflow files."""
        result = asset_planner.classify_asset("config/workflows/default.yaml", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".tf" / "config" / "workflows" / "default.yaml"

    def test_classifies_scripts(self, tmp_path: Path) -> None:
        """Should classify script files."""
        result = asset_planner.classify_asset("scripts/test.py", tmp_path)
        assert result is not None
        assert result[0] == tmp_path / ".tf" / "scripts" / "test.py"
        assert result[1] is True  # Executable

    def test_skips_bin_tf(self, tmp_path: Path) -> None:
        """Should skip bin/tf."""
        result = asset_planner.classify_asset("bin/tf", tmp_path)
        assert result is None

    def test_skips_legacy_script(self, tmp_path: Path) -> None:
        """Should skip legacy shell script."""
        result = asset_planner.classify_asset("scripts/tf_legacy.sh", tmp_path)
        assert result is None

    def test_skips_manifest(self, tmp_path: Path) -> None:
        """Should skip install manifest."""
        result = asset_planner.classify_asset("config/install-manifest.txt", tmp_path)
        assert result is None


class TestRawBaseFromSource:
    """Tests for raw URL resolution."""

    def test_converts_github_url(self) -> None:
        """Should convert GitHub URL to raw URL."""
        result = asset_planner.raw_base_from_source(
            "https://github.com/owner/repo"
        )
        assert result == "https://raw.githubusercontent.com/owner/repo/main"

    def test_converts_git_plus_url(self) -> None:
        """Should handle git+ prefix."""
        result = asset_planner.raw_base_from_source(
            "git+https://github.com/owner/repo"
        )
        assert result == "https://raw.githubusercontent.com/owner/repo/main"

    def test_handles_branch_ref(self) -> None:
        """Should handle branch reference."""
        result = asset_planner.raw_base_from_source(
            "https://github.com/owner/repo@develop"
        )
        assert result == "https://raw.githubusercontent.com/owner/repo/develop"

    def test_handles_dot_git_suffix(self) -> None:
        """Should handle .git suffix."""
        result = asset_planner.raw_base_from_source(
            "https://github.com/owner/repo.git"
        )
        assert result == "https://raw.githubusercontent.com/owner/repo/main"

    def test_returns_none_for_non_github(self) -> None:
        """Should return None for non-GitHub URLs."""
        result = asset_planner.raw_base_from_source(
            "https://gitlab.com/owner/repo"
        )
        assert result is None


class TestPlanInstallation:
    """Tests for installation planning."""

    def test_plans_new_installations(self, tmp_path: Path) -> None:
        """Should plan new file installations."""
        manifest = ["agents/test.md", "prompts/main.md"]

        result = asset_planner.plan_installation(
            tmp_path,
            manifest,
            repo_root=None,
            raw_base="https://example.com",
        )

        assert len(result.to_install) == 2
        assert len(result.skipped) == 0
        assert result.to_install[0].action == AssetAction.INSTALL

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        """Should skip existing files by default."""
        # Create existing file
        agents_dir = tmp_path / ".pi" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "test.md").write_text("exists")

        manifest = ["agents/test.md"]

        result = asset_planner.plan_installation(
            tmp_path,
            manifest,
            repo_root=None,
            raw_base="https://example.com",
        )

        assert len(result.to_install) == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].action == AssetAction.SKIP

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """Should plan updates when force=True."""
        # Create existing file
        agents_dir = tmp_path / ".pi" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "test.md").write_text("exists")

        manifest = ["agents/test.md"]

        result = asset_planner.plan_installation(
            tmp_path,
            manifest,
            repo_root=None,
            raw_base="https://example.com",
            force=True,
        )

        assert len(result.to_update) == 1
        assert result.to_update[0].action == AssetAction.UPDATE


class TestExecutePlan:
    """Tests for plan execution."""

    def test_installs_new_files(self, tmp_path: Path) -> None:
        """Should install new files from local source."""
        # Create source file
        source_file = tmp_path / "source.md"
        source_file.write_text("content")

        plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md", local_path=source_file),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.INSTALL,
        )

        plan_result = PlanResult(to_install=[plan])
        result = asset_planner.execute_plan(plan_result)

        assert result.installed == 1
        assert (tmp_path / ".pi" / "agents" / "test.md").exists()
        assert (tmp_path / ".pi" / "agents" / "test.md").read_text() == "content"

    def test_skips_when_dry_run(self, tmp_path: Path) -> None:
        """Should not write files when dry_run=True."""
        source_file = tmp_path / "source.md"
        source_file.write_text("content")

        plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md", local_path=source_file),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.INSTALL,
        )

        plan_result = PlanResult(to_install=[plan])
        result = asset_planner.execute_plan(plan_result, dry_run=True)

        assert result.installed == 1  # Counted but not written
        assert not (tmp_path / ".pi" / "agents" / "test.md").exists()

    def test_updates_existing_files(self, tmp_path: Path) -> None:
        """Should update existing files with new content."""
        # Create existing file
        dest_file = tmp_path / ".pi" / "agents" / "test.md"
        dest_file.parent.mkdir(parents=True)
        dest_file.write_text("old content")

        plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md"),
            dest_path=dest_file,
            action=AssetAction.UPDATE,
            new_content=b"new content",
        )

        plan_result = PlanResult(to_update=[plan])
        result = asset_planner.execute_plan(plan_result)

        assert result.updated == 1
        assert dest_file.read_text() == "new content"

    def test_handles_execution_errors(self, tmp_path: Path) -> None:
        """Should track errors during execution."""
        plan = AssetPlan(
            entry=AssetEntry(rel_path="agents/test.md", local_path=Path("/nonexistent")),
            dest_path=tmp_path / ".pi" / "agents" / "test.md",
            action=AssetAction.INSTALL,
        )

        plan_result = PlanResult(to_install=[plan])
        result = asset_planner.execute_plan(plan_result)

        assert result.errors == 1
        assert len(result.error_details) == 1


class TestInstallBundle:
    """Tests for install_bundle function."""

    def test_installs_bundle_successfully(self, tmp_path: Path) -> None:
        """Should install bundle and return counts."""
        # Create source repo with manifest
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("agent content")

        project_root = tmp_path / "project"

        installed, skipped = asset_planner.install_bundle(
            project_root,
            repo_root=repo_root,
        )

        assert installed == 1
        assert skipped == 0
        assert (project_root / ".pi" / "agents" / "test.md").exists()

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        """Should skip files that already exist."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("agent content")

        # Create project with existing file
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("existing")

        installed, skipped = asset_planner.install_bundle(
            project_root,
            repo_root=repo_root,
        )

        assert installed == 0
        assert skipped == 1

    def test_overwrites_when_requested(self, tmp_path: Path) -> None:
        """Should overwrite existing files when overwrite=True."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("new content")

        # Create project with existing file
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("old content")

        installed, skipped = asset_planner.install_bundle(
            project_root,
            repo_root=repo_root,
            overwrite=True,
        )

        # With overwrite=True, files are updated
        # install_bundle returns (total_changed, skipped) where total_changed = installed + updated
        assert installed == 1  # 1 file was updated
        assert skipped == 0    # No files skipped
        # The file should have been updated
        assert (project_root / ".pi" / "agents" / "test.md").read_text() == "new content"

    def test_raises_on_empty_manifest(self, tmp_path: Path) -> None:
        """Should raise error when manifest is empty."""
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("")

        project_root = tmp_path / "project"

        with pytest.raises(RuntimeError):
            asset_planner.install_bundle(project_root, repo_root=repo_root)


class TestCheckForUpdates:
    """Tests for check_for_updates function."""

    def test_finds_updates_when_content_differs(self, tmp_path: Path) -> None:
        """Should find files with different content."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("new content")

        # Create project with different content
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("old content")

        updates, errors = asset_planner.check_for_updates(
            project_root,
            repo_root=repo_root,
        )

        assert len(updates) == 1
        assert len(errors) == 0
        assert updates[0].entry.rel_path == "agents/test.md"

    def test_no_updates_when_content_matches(self, tmp_path: Path) -> None:
        """Should not report updates when content matches."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("same content")

        # Create project with same content
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("same content")

        updates, errors = asset_planner.check_for_updates(
            project_root,
            repo_root=repo_root,
        )

        assert len(updates) == 0
        assert len(errors) == 0


class TestUpdateAssets:
    """Tests for update_assets function."""

    def test_updates_files_with_changes(self, tmp_path: Path) -> None:
        """Should update files that have changes."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text("agents/test.md")
        (repo_root / "agents" / "test.md").write_text("new content")

        # Create project with old content
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("old content")

        result = asset_planner.update_assets(
            project_root,
            repo_root=repo_root,
        )

        assert result.updated == 1
        assert (project_root / ".pi" / "agents" / "test.md").read_text() == "new content"

    def test_respects_select_filter(self, tmp_path: Path) -> None:
        """Should only update selected files when select is provided."""
        # Create source repo
        repo_root = tmp_path / "repo"
        (repo_root / "config").mkdir(parents=True)
        (repo_root / "agents").mkdir(parents=True)
        (repo_root / "prompts").mkdir(parents=True)
        (repo_root / "config" / "install-manifest.txt").write_text(
            "agents/test.md\nprompts/other.md"
        )
        (repo_root / "agents" / "test.md").write_text("new agent")
        (repo_root / "prompts" / "other.md").write_text("new prompt")

        # Create project with old content
        project_root = tmp_path / "project"
        (project_root / ".pi" / "agents").mkdir(parents=True)
        (project_root / ".pi" / "prompts").mkdir(parents=True)
        (project_root / ".pi" / "agents" / "test.md").write_text("old agent")
        (project_root / ".pi" / "prompts" / "other.md").write_text("old prompt")

        # Only update agents
        result = asset_planner.update_assets(
            project_root,
            repo_root=repo_root,
            select=["agents/test.md"],
        )

        assert result.updated == 1
        assert (project_root / ".pi" / "agents" / "test.md").read_text() == "new agent"
        assert (project_root / ".pi" / "prompts" / "other.md").read_text() == "old prompt"
