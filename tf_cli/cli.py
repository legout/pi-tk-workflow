"""CLI entrypoint - DEPRECATED shim.

DEPRECATED: This module is maintained for backward compatibility through version 0.4.x.
Use 'tf.cli' instead. This shim will be removed in version 0.5.0.

To see deprecation warnings, set TF_CLI_DEPRECATION_WARN=1
"""
from __future__ import annotations

import os
import warnings

# Emit deprecation warning if opted in (default off to avoid CI noise)
if os.environ.get("TF_CLI_DEPRECATION_WARN"):
    warnings.warn(
        "tf_cli.cli is deprecated. Use 'tf.cli' instead. "
        "This shim will be removed in version 0.5.0. "
        "See https://github.com/legout/pi-ticketflow/blob/main/docs/deprecation-policy.md",
        DeprecationWarning,
        stacklevel=2,
    )

# Re-export only public API from canonical tf package
# Internal functions (install_main, read_root_file, etc.) are not exported
from tf.cli import main, can_import_tf
from tf import get_version

# Keep backward compatibility for any code importing can_import_tf_cli
# (renamed to can_import_tf in the new package)
can_import_tf_cli = can_import_tf

__all__ = [
    "main",
    "can_import_tf",
    "can_import_tf_cli",  # backward compat alias
    "get_version",
]

# For module execution: python -m tf_cli.cli
if __name__ == "__main__":
    import sys
    raise SystemExit(main())
