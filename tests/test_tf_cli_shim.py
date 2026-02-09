"""Regression tests for tf_cli shim compatibility.

Ensures the tf_cli package continues to function as a shim during
the deprecation period (through version 0.4.x).

These tests validate that:
1. tf_cli can still be imported
2. tf_cli re-exports work correctly
3. The shim doesn't break existing code

See: https://github.com/legout/pi-ticketflow/blob/main/docs/deprecation-policy.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


class TestTfCliShimImports:
    """Test that tf_cli package can be imported and used."""

    def test_tf_cli_package_imports(self):
        """tf_cli package should import without errors."""
        import tf_cli

        assert tf_cli is not None
        assert hasattr(tf_cli, "__version__")

    def test_tf_cli_has_version(self):
        """tf_cli should expose __version__."""
        import tf_cli

        assert isinstance(tf_cli.__version__, str)
        assert len(tf_cli.__version__) > 0

    def test_tf_cli_get_version_function(self):
        """tf_cli should expose get_version function."""
        import tf_cli

        assert callable(tf_cli.get_version)
        version = tf_cli.get_version()
        assert isinstance(version, str)
        assert version == tf_cli.__version__


class TestTfCliShimReexports:
    """Test that tf_cli re-exports from tf package work."""

    def test_tf_cli_cli_reexports_main(self):
        """tf_cli.cli should re-export main from tf.cli."""
        from tf_cli.cli import main
        from tf.cli import main as tf_main

        assert main is tf_main

    def test_tf_cli_cli_has_can_import_tf(self):
        """tf_cli.cli should expose can_import_tf."""
        from tf_cli.cli import can_import_tf
        import shutil

        assert callable(can_import_tf)
        # Should return True since tf is importable
        python = shutil.which("python3") or shutil.which("python")
        assert can_import_tf(python) is True

    def test_tf_cli_cli_has_backward_compat_alias(self):
        """tf_cli.cli should have can_import_tf_cli alias."""
        from tf_cli.cli import can_import_tf_cli
        from tf_cli.cli import can_import_tf

        assert can_import_tf_cli is can_import_tf


class TestTfCliModuleImports:
    """Test that individual tf_cli modules can be imported."""

    def test_tf_cli_next_imports(self):
        """tf_cli.next should be importable."""
        from tf_cli import next

        assert next is not None
        assert hasattr(next, "main")

    def test_tf_cli_init_imports(self):
        """tf_cli.init should be importable."""
        from tf_cli import init

        assert init is not None
        assert hasattr(init, "main")

    def test_tf_cli_ticket_factory_imports(self):
        """tf_cli.ticket_factory should be importable."""
        from tf_cli.ticket_factory import TicketDef

        assert TicketDef is not None

    def test_tf_cli_component_classifier_imports(self):
        """tf_cli.component_classifier should be importable."""
        from tf_cli.component_classifier import classify_components

        assert callable(classify_components)


class TestTfCliShimBehavior:
    """Test that tf_cli shim behavior is consistent."""

    def test_tf_cli_and_tf_versions_match(self):
        """tf_cli and tf should report the same version."""
        import tf_cli
        import tf

        assert tf_cli.__version__ == tf.__version__

    def test_tf_cli_module_execution(self):
        """python -m tf_cli should work."""
        # We can't actually run python -m tf_cli in this test,
        # but we can verify the __main__ module exists
        import tf_cli.__main__

        assert hasattr(tf_cli.__main__, "main")


class TestTfCliTicketFactoryExports:
    """Test tf_cli exports for ticket_factory (shim compatibility)."""

    def test_tf_cli_has_ticket_def(self):
        """tf_cli should expose TicketDef."""
        from tf_cli import TicketDef
        from tf.ticket_factory import TicketDef as TfTicketDef

        # Both packages should have the class, but they may be different objects
        # during the transition period - verify they work identically
        assert TicketDef is not None
        assert TfTicketDef is not None

    def test_tf_cli_has_created_ticket(self):
        """tf_cli should expose CreatedTicket."""
        from tf_cli import CreatedTicket
        from tf.ticket_factory import CreatedTicket as TfCreatedTicket

        assert CreatedTicket is not None
        assert TfCreatedTicket is not None

    def test_tf_cli_has_create_tickets(self):
        """tf_cli should expose create_tickets function."""
        from tf_cli import create_tickets
        from tf.ticket_factory import create_tickets as tf_create_tickets

        assert callable(create_tickets)
        assert callable(tf_create_tickets)


class TestTfCliDeprecationWarnings:
    """Test deprecation warning behavior."""

    def test_tf_cli_no_warnings_by_default(self):
        """tf_cli should NOT emit warnings by default (to avoid CI noise)."""
        import warnings

        # Clear any cached modules to force re-import
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith("tf_cli")]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import tf_cli

            # Should have no deprecation warnings by default
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0, (
                f"Unexpected deprecation warnings: {[str(x.message) for x in deprecation_warnings]}"
            )

    def test_tf_cli_warnings_with_env_var(self, monkeypatch):
        """tf_cli should emit warnings when TF_CLI_DEPRECATION_WARN=1."""
        import warnings

        monkeypatch.setenv("TF_CLI_DEPRECATION_WARN", "1")

        # Clear cached modules
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith("tf_cli")]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import tf_cli

            # Should have at least one deprecation warning
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) > 0, (
                "Expected deprecation warnings when TF_CLI_DEPRECATION_WARN=1"
            )
