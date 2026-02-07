"""Tests for tf_cli.sync module (project-local sync after refactor)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from tf_cli import sync

pytestmark = pytest.mark.unit


class TestReadJson:
    def test_reads_valid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "config.json"
        p.write_text(json.dumps({"a": 1}))
        assert sync.read_json(p) == {"a": 1}

    def test_returns_empty_on_missing(self, tmp_path: Path) -> None:
        assert sync.read_json(tmp_path / "missing.json") == {}

    def test_returns_empty_on_invalid(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("not-json")
        assert sync.read_json(p) == {}


class TestFindProjectRoot:
    def test_finds_parent_with_tf_dir(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        (project / ".tf").mkdir(parents=True)
        nested = project / "a" / "b"
        nested.mkdir(parents=True)
        assert sync.find_project_root(nested) == project

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        assert sync.find_project_root(nested) is None


class TestResolveProjectRoot:
    def test_uses_project_arg(self, tmp_path: Path) -> None:
        args = mock.Mock(project=str(tmp_path / "p"), global_install=False)
        assert sync.resolve_project_root(args) == tmp_path / "p"

    def test_errors_on_global_flag(self) -> None:
        args = mock.Mock(project=None, global_install=True)
        with pytest.raises(SystemExit):
            sync.resolve_project_root(args)


class TestLoadProjectConfig:
    def test_loads_project_config(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        cfg = project / ".tf" / "config" / "settings.json"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({"metaModels": {"x": {"model": "m", "thinking": "low"}}}))
        assert sync.load_project_config(project)["metaModels"]["x"]["model"] == "m"


class TestResolveMetaModel:
    def test_resolves_from_meta_models(self) -> None:
        config = {"metaModels": {"fast": {"model": "gpt-4", "thinking": "low"}}}
        assert sync.resolve_meta_model(config, "fast") == {"model": "gpt-4", "thinking": "low"}

    def test_resolves_via_agents_map(self) -> None:
        config = {
            "metaModels": {"worker": {"model": "gpt-4", "thinking": "medium"}},
            "agents": {"my_agent": "worker"},
        }
        assert sync.resolve_meta_model(config, "my_agent") == {"model": "gpt-4", "thinking": "medium"}


class TestUpdateFrontmatter:
    def test_updates_agent_frontmatter(self, tmp_path: Path) -> None:
        p = tmp_path / "a.md"
        p.write_text("""---\nmodel: old\nthinking: low\n---\n# x\n""")
        config = {"metaModels": {"a": {"model": "new", "thinking": "high"}}, "agents": {"a": "a"}}
        assert sync.update_agent_frontmatter(p, config, "a") is True
        text = p.read_text()
        assert "model: new" in text
        assert "thinking: high" in text

    def test_updates_prompt_frontmatter(self, tmp_path: Path) -> None:
        p = tmp_path / "p.md"
        p.write_text("""---\nmodel: old\n---\n# x\n""")
        config = {"metaModels": {"p": {"model": "new", "thinking": "medium"}}, "prompts": {"p": "p"}}
        assert sync.update_prompt_frontmatter(p, config, "p") is True
        text = p.read_text()
        assert "model: new" in text
        assert "thinking: medium" in text


class TestSyncModels:
    def test_syncs_project_local_agents_and_prompts(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        agents_dir = project / ".pi" / "agents"
        prompts_dir = project / ".pi" / "prompts"
        agents_dir.mkdir(parents=True)
        prompts_dir.mkdir(parents=True)

        (agents_dir / "reviewer-general.md").write_text("""---\nmodel: old\n---\n# Agent\n""")
        (prompts_dir / "tf.md").write_text("""---\nmodel: old\n---\n# Prompt\n""")

        config = {
            "metaModels": {
                "review": {"model": "m1", "thinking": "high"},
                "worker": {"model": "m2", "thinking": "medium"},
            },
            "agents": {"reviewer-general": "review"},
            "prompts": {"tf": "worker"},
        }

        results = sync.sync_models(project, config)
        assert "reviewer-general" in results["agents"]
        assert "tf" in results["prompts"]
        assert results["errors"] == []


class TestRunSync:
    def test_runs_sync_and_installs_bundle(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        (project / ".tf" / "config").mkdir(parents=True)
        (project / ".tf" / "config" / "settings.json").write_text(
            json.dumps({"metaModels": {}, "agents": {}, "prompts": {}})
        )
        (project / ".pi" / "agents").mkdir(parents=True)
        (project / ".pi" / "prompts").mkdir(parents=True)

        args = mock.Mock(project=str(project), global_install=False)

        with mock.patch("tf_cli.project_bundle.install_bundle") as mock_install:
            result = sync.run_sync(args)
            assert result == 0
            mock_install.assert_called_once()

    def test_errors_when_config_missing_and_bundle_does_not_install(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        args = mock.Mock(project=str(project), global_install=False)

        with mock.patch("tf_cli.project_bundle.install_bundle"):
            # No config file
            result = sync.run_sync(args)
            assert result == 1
