"""Tests for tf.sync module (project-local sync after refactor)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from tf import sync

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

    def test_fallback_when_meta_model_missing(self) -> None:
        """When agents.fixer points to missing meta-model, fallback to meta-key as literal model ID."""
        config = {
            "metaModels": {"general": {"model": "gpt-4", "thinking": "medium"}},
            "agents": {"fixer": "fixer"},  # metaModels.fixer is missing
        }
        # Fallback treats the meta-model key ("fixer") as literal model ID
        assert sync.resolve_meta_model(config, "fixer") == {"model": "fixer", "thinking": "medium"}

    def test_fallback_uses_meta_key_not_agent_name(self) -> None:
        """Fallback should use meta-model key, not agent name, when meta-model is missing."""
        config = {
            "metaModels": {},
            "agents": {"fixer": "custom-fixer"},  # Different agent name vs meta-key
        }
        # Should use "custom-fixer" (the meta-key), not "fixer" (the agent name)
        assert sync.resolve_meta_model(config, "fixer") == {"model": "custom-fixer", "thinking": "medium"}

    def test_resolves_via_prompts_map(self) -> None:
        config = {
            "metaModels": {"planning": {"model": "gpt-4", "thinking": "medium"}},
            "prompts": {"tf-plan": "planning"},
        }
        assert sync.resolve_meta_model(config, "tf-plan") == {"model": "gpt-4", "thinking": "medium"}

    def test_prompt_fallback_when_meta_model_missing(self) -> None:
        """When prompt points to missing meta-model, fallback to meta-key as literal model ID."""
        config = {
            "metaModels": {},
            "prompts": {"tf-custom": "custom-model"},
        }
        # Fallback treats the meta-model key as literal model ID
        assert sync.resolve_meta_model(config, "tf-custom") == {"model": "custom-model", "thinking": "medium"}


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


class TestFixerMetaModelSelection:
    """Tests for fixer meta-model selection and backward compatibility.

    Covers acceptance criteria from ticket pt-6zp2:
    - With metaModels.fixer present, fixer resolves to that model
    - With metaModels.fixer absent, fixer follows documented fallback
    - Escalation overrides work correctly when configured
    """

    def test_fixer_resolves_to_meta_model_when_present(self) -> None:
        """AC1: With metaModels.fixer present, fixer resolves to that model."""
        config = {
            "metaModels": {
                "fixer": {
                    "model": "chutes/zai-org/GLM-4.7-Flash",
                    "thinking": "medium",
                },
                "general": {"model": "kimi-coding/k2p5", "thinking": "medium"},
            },
            "agents": {"fixer": "fixer"},
        }
        result = sync.resolve_meta_model(config, "fixer")
        assert result["model"] == "chutes/zai-org/GLM-4.7-Flash"
        assert result["thinking"] == "medium"

    def test_fixer_resolves_to_general_when_configured(self) -> None:
        """Backward compat: agents.fixer='general' uses metaModels.general.

        Note: This test uses 'my_fixer' as agent name to avoid conflict with
        metaModels.fixer key - the resolution order checks metaModels first.
        """
        config = {
            "metaModels": {
                "fixer": {"model": "chutes/zai-org/GLM-4.7-Flash", "thinking": "medium"},
                "general": {"model": "kimi-coding/k2p5", "thinking": "medium"},
            },
            "agents": {"my_fixer": "general"},  # Map to general instead of fixer
        }
        result = sync.resolve_meta_model(config, "my_fixer")
        assert result["model"] == "kimi-coding/k2p5"
        assert result["thinking"] == "medium"

    def test_fixer_uses_general_when_meta_model_missing(self) -> None:
        """Backward compat: agents.fixer='general' with missing metaModels.fixer uses metaModels.general.

        This tests the exact fallback scenario: the fixer agent is mapped to 'general',
        and there is no metaModels.fixer defined, so resolution should use metaModels.general.
        """
        config = {
            "metaModels": {
                "general": {"model": "kimi-coding/k2p5", "thinking": "medium"},
                # metaModels.fixer is intentionally missing
            },
            "agents": {"fixer": "general"},
        }
        result = sync.resolve_meta_model(config, "fixer")
        assert result["model"] == "kimi-coding/k2p5"
        assert result["thinking"] == "medium"

    def test_fixer_fallback_when_meta_model_missing(self) -> None:
        """AC2: With metaModels.fixer absent, fixer follows documented fallback.

        The fallback treats the meta-model key ("fixer") as a literal model ID.
        This is documented behavior - users should define metaModels.fixer or
        use agents.fixer="general" for backward compatibility.
        """
        config = {
            "metaModels": {
                "general": {"model": "kimi-coding/k2p5", "thinking": "medium"}
                # metaModels.fixer is intentionally missing
            },
            "agents": {"fixer": "fixer"},
        }
        result = sync.resolve_meta_model(config, "fixer")
        # Fallback uses meta-model key as literal model ID
        assert result["model"] == "fixer"
        assert result["thinking"] == "medium"

    def test_escalation_overrides_fixer_model(self) -> None:
        """AC3: Escalation model takes precedence over base fixer model on retry.

        This test verifies end-to-end integration: base model is resolved via
        sync.resolve_meta_model, then escalation overrides it on attempt 2.
        """
        from tf.retry_state import RetryState

        # Full config with metaModels and agents
        config = {
            "metaModels": {
                "fixer": {
                    "model": "chutes/zai-org/GLM-4.7-Flash",
                    "thinking": "medium",
                },
            },
            "agents": {"fixer": "fixer"},
            "workflow": {
                "escalation": {
                    "enabled": True,
                    "models": {"fixer": "openai-codex/gpt-5.3-codex"},
                }
            },
        }
        # Resolve base model for fixer via the actual resolver
        base_model = sync.resolve_meta_model(config, "fixer")["model"]
        base_models = {"fixer": base_model}
        escalation_config = config["workflow"]["escalation"]

        # Simulate a ticket that completed attempt 1 as blocked
        state = RetryState("/tmp/test", ticket_id="pt-test")
        state.start_attempt()
        state.complete_attempt(status="blocked")

        # Determine escalation for the next attempt (attempt 2)
        result = state.resolve_escalation(escalation_config, base_models, next_attempt_number=2)
        assert result.fixer == "openai-codex/gpt-5.3-codex"

    def test_escalation_fallback_to_base_when_no_override(self) -> None:
        """When no escalation override is provided, base model is used on retry."""
        from tf.retry_state import RetryState

        config = {
            "metaModels": {
                "fixer": {"model": "chutes/zai-org/GLM-4.7-Flash", "thinking": "medium"},
            },
            "agents": {"fixer": "fixer"},
            "workflow": {
                "escalation": {
                    "enabled": True,
                    "models": {"fixer": None},  # No override
                }
            },
        }
        base_model = sync.resolve_meta_model(config, "fixer")["model"]
        base_models = {"fixer": base_model}
        escalation_config = config["workflow"]["escalation"]

        state = RetryState("/tmp/test", ticket_id="pt-test")
        state.start_attempt()
        state.complete_attempt(status="blocked")

        result = state.resolve_escalation(escalation_config, base_models, next_attempt_number=2)
        assert result.fixer == base_model

    def test_escalation_disabled_uses_base_model(self) -> None:
        """When escalation is disabled, always use base model."""
        from tf.retry_state import RetryState

        state = RetryState("/tmp/test", ticket_id="pt-test")
        # No attempts yet - first run

        config = {"enabled": False, "models": {"fixer": "strong-model"}}
        base_models = {"fixer": "base-model"}

        result = state.resolve_escalation(config, base_models)
        # No escalation when disabled
        assert result.fixer is None  # No escalation, use base


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

        with mock.patch("tf.project_bundle.install_bundle") as mock_install:
            result = sync.run_sync(args)
            assert result == 0
            mock_install.assert_called_once()

    def test_errors_when_config_missing_and_bundle_does_not_install(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        args = mock.Mock(project=str(project), global_install=False)

        with mock.patch("tf.project_bundle.install_bundle"):
            # No config file
            result = sync.run_sync(args)
            assert result == 1
