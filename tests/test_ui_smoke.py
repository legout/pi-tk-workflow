"""Smoke tests for the `tf ui` CLI command.

Tests the CLI wiring and basic error handling without requiring
a full Textual TUI environment.
"""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from tf import ui as ui_module
from tf.cli import main as cli_main


class TestUiHelp:
    """Test that tf --help includes ui command documentation."""

    def test_help_includes_ui_command(self, capsys):
        """Main help text should document the ui command."""
        cli_main(["--help"])
        captured = capsys.readouterr()
        
        assert "ui" in captured.out
        assert "Kanban TUI" in captured.out or "interactive" in captured.out.lower()

    def test_help_shows_ui_in_command_list(self, capsys):
        """Help should list ui in the Commands section."""
        cli_main(["--help"])
        captured = capsys.readouterr()
        
        assert "ui" in captured.out


class TestUiCliWiring:
    """Test that tf ui command is properly wired in CLI."""

    def test_ui_command_imports_module(self):
        """The ui command should import and call ui.main."""
        # This test verifies the import path works
        from tf_cli import ui
        assert hasattr(ui, "main")
        assert callable(ui.main)

    def test_ui_module_has_main_function(self):
        """ui.py should expose a main function with standard signature."""
        import inspect
        sig = inspect.signature(ui_module.main)
        params = list(sig.parameters.keys())
        
        assert "argv" in params
        # argv should have default None
        assert sig.parameters["argv"].default is None


class TestUiErrorHandling:
    """Test UI error handling for non-interactive environments."""

    def test_ui_requires_tty(self, monkeypatch):
        """tf ui should error when not running in a TTY."""
        # Mock stdin/stdout to not be ttys
        mock_stdin = mock.MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdout = mock.MagicMock()
        mock_stdout.isatty.return_value = False
        
        monkeypatch.setattr(sys, "stdin", mock_stdin)
        monkeypatch.setattr(sys, "stdout", mock_stdout)
        
        result = ui_module.main([])
        
        assert result == 1

    def test_ui_shows_error_without_tty(self, monkeypatch, capsys):
        """tf ui should show helpful error when TTY is not available."""
        mock_stdin = mock.MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdout = mock.MagicMock()
        mock_stdout.isatty.return_value = False
        
        monkeypatch.setattr(sys, "stdin", mock_stdin)
        monkeypatch.setattr(sys, "stdout", mock_stdout)
        
        # Also capture the actual stderr
        with mock.patch.object(sys, "stderr", sys.stderr):
            result = ui_module.main([])
        
        captured = capsys.readouterr()
        assert result == 1
        # Error message should mention TTY requirement
        assert "TTY" in captured.err or "interactive" in captured.err.lower()


class TestUiHeadlessImport:
    """Test that tf.ui can be imported in CI/headless contexts.

    These tests verify the module doesn't crash on import when running
    in non-TTY environments (e.g., CI, web-served contexts).
    """

    def test_ui_module_imports_without_error(self):
        """Importing tf.ui should not raise in headless contexts."""
        # This test verifies the basic import works - critical for CI
        import tf.ui as ui

        assert ui is not None

    def test_ui_module_imports_in_non_tty_context(self, monkeypatch):
        """Import should succeed even when stdin/stdout are not TTYs."""
        # Simulate headless/CI environment
        mock_stdin = mock.MagicMock()
        mock_stdin.isatty.return_value = False
        mock_stdout = mock.MagicMock()
        mock_stdout.isatty.return_value = False

        monkeypatch.setattr(sys, "stdin", mock_stdin)
        monkeypatch.setattr(sys, "stdout", mock_stdout)

        # Force re-import by clearing cache
        if "tf.ui" in sys.modules:
            del sys.modules["tf.ui"]

        # Import should not raise
        import tf.ui as ui

        assert ui is not None


class TestUiModuleImports:
    """Test that ui module can import its dependencies."""

    def test_ui_imports_ticket_loader(self):
        """ui module should import ticket_loader components."""
        from tf.ui import TicketLoader, Ticket
        assert TicketLoader is not None
        assert Ticket is not None

    def test_ui_imports_board_classifier(self):
        """ui module should import board_classifier components."""
        from tf.ui import BoardClassifier, BoardColumn, ClassifiedTicket
        assert BoardClassifier is not None
        assert BoardColumn is not None
        assert ClassifiedTicket is not None

    def test_ui_imports_topic_index_loader(self):
        """ui module should import TopicIndexLoader."""
        from tf.ui import TopicIndexLoader, Topic, TopicIndexLoadError
        assert TopicIndexLoader is not None
        assert Topic is not None
        assert TopicIndexLoadError is not None


class TestUiTopicFunctions:
    """Test UI topic-related utility functions."""

    def test_get_topic_type_recognizes_prefixes(self):
        """get_topic_type should recognize all topic type prefixes."""
        from tf.ui import get_topic_type
        
        assert get_topic_type("seed-add-versioning") == "seed"
        assert get_topic_type("plan-kb-management") == "plan"
        assert get_topic_type("spike-kanban-tui") == "spike"
        assert get_topic_type("baseline-something") == "baseline"
        assert get_topic_type("unknown-topic") == "unknown"

    def test_resolve_knowledge_dir_returns_path(self):
        """resolve_knowledge_dir should return a Path."""
        from tf.ui import resolve_knowledge_dir
        from pathlib import Path
        
        result = resolve_knowledge_dir()
        assert isinstance(result, Path)

    def test_resolve_knowledge_dir_cwd_fallback(self, monkeypatch, tmp_path):
        """resolve_knowledge_dir should fallback to cwd/.tf/knowledge."""
        from tf.ui import resolve_knowledge_dir
        
        monkeypatch.chdir(tmp_path)
        # Clear any env variable
        monkeypatch.delenv("TF_KNOWLEDGE_DIR", raising=False)
        
        result = resolve_knowledge_dir()
        assert result == tmp_path / ".tf" / "knowledge"


class TestUiSmokeIntegration:
    """Integration smoke tests for UI components."""

    def test_topic_index_loader_can_be_instantiated(self):
        """TopicIndexLoader should be instantiable."""
        from tf.ui import TopicIndexLoader
        
        loader = TopicIndexLoader()
        assert loader is not None
        assert not loader._loaded

    def test_board_classifier_can_be_instantiated(self):
        """BoardClassifier should be instantiable."""
        from tf.ui import BoardClassifier
        
        classifier = BoardClassifier()
        assert classifier is not None
