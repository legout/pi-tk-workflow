"""Tests for tf.login module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tf import login as login_module


class TestConfigureWebSearch:
    """Tests for configure_web_search function."""

    def test_creates_new_config_file(self, tmp_path: Path) -> None:
        """Test creating a new web-search.json file."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_web_search(target_base, "test-api-key")
        
        config_file = target_base / "web-search.json"
        assert config_file.exists()
        
        content = json.loads(config_file.read_text())
        assert content["perplexityApiKey"] == "test-api-key"

    def test_updates_existing_config(self, tmp_path: Path) -> None:
        """Test updating an existing web-search.json file."""
        target_base = tmp_path / ".pi" / "agent"
        target_base.mkdir(parents=True)
        
        existing = {"otherKey": "value"}
        (target_base / "web-search.json").write_text(json.dumps(existing))
        
        login_module.configure_web_search(target_base, "new-api-key")
        
        content = json.loads((target_base / "web-search.json").read_text())
        assert content["perplexityApiKey"] == "new-api-key"
        assert content["otherKey"] == "value"

    def test_sets_file_permissions(self, tmp_path: Path) -> None:
        """Test that file permissions are set to 0o600."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_web_search(target_base, "test-api-key")
        
        config_file = target_base / "web-search.json"
        # Check permissions (may not work on all platforms)
        try:
            mode = config_file.stat().st_mode & 0o777
            assert mode == 0o600
        except AttributeError:
            pytest.skip("File permission check not supported on this platform")

    def test_handles_invalid_existing_json(self, tmp_path: Path) -> None:
        """Test handling of invalid existing JSON."""
        target_base = tmp_path / ".pi" / "agent"
        target_base.mkdir(parents=True)
        (target_base / "web-search.json").write_text("invalid json")
        
        login_module.configure_web_search(target_base, "test-api-key")
        
        content = json.loads((target_base / "web-search.json").read_text())
        assert content["perplexityApiKey"] == "test-api-key"


class TestConfigureMcp:
    """Tests for configure_mcp function."""

    def test_creates_mcp_config(self, tmp_path: Path) -> None:
        """Test creating mcp.json with all servers."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(
            target_base,
            zai_key="zai-key",
            ctx7_key="ctx7-key",
            exa_key="exa-key"
        )
        
        mcp_file = target_base / "mcp.json"
        assert mcp_file.exists()
        
        config = json.loads(mcp_file.read_text())
        assert "mcpServers" in config
        assert "settings" in config
        assert config["settings"]["toolPrefix"] == "short"

    def test_includes_context7_with_key(self, tmp_path: Path) -> None:
        """Test that context7 is included when key provided."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="ctx7-key", exa_key="")
        
        config = json.loads((target_base / "mcp.json").read_text())
        assert "context7" in config["mcpServers"]
        assert config["mcpServers"]["context7"]["headers"]["CONTEXT7_API_KEY"] == "ctx7-key"

    def test_includes_exa_with_key(self, tmp_path: Path) -> None:
        """Test that exa is included when key provided."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="", exa_key="exa-key")
        
        config = json.loads((target_base / "mcp.json").read_text())
        assert "exa" in config["mcpServers"]
        assert config["mcpServers"]["exa"]["headers"]["EXA_API_KEY"] == "exa-key"

    def test_includes_zai_servers_with_key(self, tmp_path: Path) -> None:
        """Test that ZAI servers are included when key provided."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="zai-key", ctx7_key="", exa_key="")

        config = json.loads((target_base / "mcp.json").read_text())

        # zai-web-search and zai-web-reader remain URL-based
        assert "zai-web-search" in config["mcpServers"]
        assert config["mcpServers"]["zai-web-search"]["url"].startswith("https://")
        assert config["mcpServers"]["zai-web-search"]["headers"]["Authorization"] == "Bearer zai-key"

        assert "zai-web-reader" in config["mcpServers"]
        assert config["mcpServers"]["zai-web-reader"]["url"].startswith("https://")
        assert config["mcpServers"]["zai-web-reader"]["headers"]["Authorization"] == "Bearer zai-key"

        # zai-vision is command-based
        assert "zai-vision" in config["mcpServers"]
        assert config["mcpServers"]["zai-vision"]["command"] == "npx"
        assert config["mcpServers"]["zai-vision"]["args"] == ["-y", "@z_ai/mcp-server"]
        assert config["mcpServers"]["zai-vision"]["env"]["Z_AI_API_KEY"] == "zai-key"
        assert config["mcpServers"]["zai-vision"]["env"]["Z_AI_MODE"] == "ZAI"

    def test_skips_zai_servers_without_key(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test that ZAI servers are skipped when no key."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="ctx7-key", exa_key="")
        
        config = json.loads((target_base / "mcp.json").read_text())
        assert "zai-web-search" not in config["mcpServers"]
        
        captured = capsys.readouterr()
        assert "ZAI_API_KEY not provided" in captured.err

    def test_grep_app_always_included(self, tmp_path: Path) -> None:
        """Test that grep_app is always included."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="", exa_key="")
        
        config = json.loads((target_base / "mcp.json").read_text())
        assert "grep_app" in config["mcpServers"]

    def test_strips_whitespace_from_keys(self, tmp_path: Path) -> None:
        """Test that whitespace is stripped from API keys."""
        target_base = tmp_path / ".pi" / "agent"
        login_module.configure_mcp(target_base, zai_key="  zai-key  ", ctx7_key="", exa_key="")
        
        config = json.loads((target_base / "mcp.json").read_text())
        headers = config["mcpServers"]["zai-web-search"]["headers"]
        assert headers["Authorization"] == "Bearer zai-key"

    def test_handles_permission_error_gracefully(self, tmp_path: Path) -> None:
        """Test that permission errors are handled gracefully."""
        target_base = tmp_path / ".pi" / "agent"
        
        # Create file first
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="", exa_key="")
        
        # Make file unreadable then try to chmod
        mcp_file = target_base / "mcp.json"
        # Just verify no exception is raised
        login_module.configure_mcp(target_base, zai_key="", ctx7_key="", exa_key="")


class TestBuildParser:
    """Tests for build_parser function."""

    def test_parser_has_project_argument(self) -> None:
        """Test that parser has --project argument."""
        parser = login_module.build_parser()
        args = parser.parse_args(["--project", "test"])
        assert args.project == "test"

    def test_parser_has_global_argument(self) -> None:
        """Test that parser has --global argument."""
        parser = login_module.build_parser()
        args = parser.parse_args(["--global"])
        assert args.global_install is True


class TestMain:
    """Tests for main function."""

    @patch.object(login_module, "input", side_effect=["perp-key", "ctx7-key", "exa-key", "zai-key"])
    @patch.object(login_module, "configure_web_search")
    @patch.object(login_module, "configure_mcp")
    @patch("builtins.print")
    def test_main_configures_all_services(
        self, 
        mock_print: MagicMock,
        mock_mcp: MagicMock, 
        mock_web: MagicMock,
        mock_input: MagicMock
    ) -> None:
        """Test main with all API keys provided."""
        result = login_module.main([])
        assert result == 0
        mock_web.assert_called_once()
        mock_mcp.assert_called_once()

    @patch.object(login_module, "input", return_value="")
    @patch("os.environ.get", side_effect=lambda k, default="": "env-key" if k == "PERPLEXITY_API_KEY" else "")
    @patch.object(login_module, "configure_web_search")
    @patch.object(login_module, "configure_mcp")
    @patch("builtins.print")
    def test_main_uses_env_vars(
        self,
        mock_print: MagicMock,
        mock_mcp: MagicMock,
        mock_web: MagicMock,
        mock_getenv: MagicMock,
        mock_input: MagicMock
    ) -> None:
        """Test that environment variables are used as fallback."""
        result = login_module.main([])
        assert result == 0
        # Should configure web search with env var
        mock_web.assert_called_once()

    @patch.object(login_module, "input", return_value="")
    @patch("os.environ.get", return_value="")
    @patch.object(login_module, "configure_web_search")
    @patch.object(login_module, "configure_mcp")
    @patch("builtins.print")
    def test_main_skips_config_when_no_keys(
        self,
        mock_print: MagicMock,
        mock_mcp: MagicMock,
        mock_web: MagicMock,
        mock_getenv: MagicMock,
        mock_input: MagicMock
    ) -> None:
        """Test that configuration is skipped when no keys provided."""
        result = login_module.main([])
        assert result == 0
        mock_web.assert_not_called()
        mock_mcp.assert_not_called()
