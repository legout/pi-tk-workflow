"""Module entrypoint for python -m tf.

This module enables running the tf CLI via `python -m tf`.
It imports and calls the main entrypoint from tf.cli.
"""
from __future__ import annotations

import sys

from tf.cli import main

if __name__ == "__main__":
    sys.exit(main())
