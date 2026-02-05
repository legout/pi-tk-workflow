"""Version information for tf_cli (deprecated, use tf_cli.version instead).

This module is kept for backward compatibility.
Prefer importing from tf_cli.version or tf_cli directly.
"""
from tf_cli.version import get_version, __version__

__all__ = ["__version__", "get_version"]
