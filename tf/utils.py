"""Shared CLI utility module for root resolution and JSON helpers.

This module provides common utility functions used across multiple CLI modules
to avoid code duplication.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def read_json(path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        The parsed JSON content as a dictionary. Returns an empty dict
        if the file doesn't exist or cannot be parsed.
    """
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Find the project root by looking for .tf or .pi directory.
    
    Searches upward from the starting directory (or current working directory)
    for a directory containing either a .tf or .pi subdirectory.
    
    Args:
        start: The directory to start searching from. Defaults to current working directory.
        
    Returns:
        The Path to the project root, or None if not found.
    """
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir() or (parent / ".pi").is_dir():
            return parent
    return None


def merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Recursively merges dictionary b into dictionary a. For nested dictionaries,
    values from b are merged into a. For non-dict values, b's values overwrite a's.
    
    Args:
        a: The base dictionary.
        b: The dictionary to merge into a.
        
    Returns:
        A new dictionary containing the merged result.
    """
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out
