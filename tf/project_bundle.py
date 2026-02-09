"""Project bundle installation using the canonical asset planner.

This module is now a thin wrapper around asset_planner for backward compatibility.
New code should use asset_planner directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

# Re-export from asset_planner for backward compatibility
from .asset_planner import (
    DEFAULT_RAW_REPO_URL,
    DEFAULT_UVX_SOURCE,
    ExecutionResult,
    PlanResult,
    find_repo_root,
    install_bundle,
    load_manifest,
    plan_installation,
    raw_base_from_source,
    resolve_raw_base,
)

# Re-export common types
__all__ = [
    "DEFAULT_RAW_REPO_URL",
    "DEFAULT_UVX_SOURCE",
    "ExecutionResult",
    "PlanResult",
    "find_repo_root",
    "install_bundle",
    "load_manifest",
    "plan_installation",
    "raw_base_from_source",
    "resolve_raw_base",
]


def compute_bundle_plan(project_root: Path, manifest: List[str]) -> List:
    """Legacy compatibility: compute bundle plan (now uses asset_planner).

    This function is kept for backward compatibility. New code should use
    asset_planner.plan_installation() directly.
    """
    from .asset_planner import AssetEntry, AssetPlan, AssetAction, classify_asset

    plan: List[AssetPlan] = []
    for rel in manifest:
        classified = classify_asset(rel, project_root)
        if classified is not None:
            dest_path, executable = classified
            # Create a minimal AssetPlan for compatibility
            plan.append(
                AssetPlan(
                    entry=AssetEntry(rel_path=rel),
                    dest_path=dest_path,
                    action=AssetAction.INSTALL,
                    executable=executable,
                )
            )
    return plan
