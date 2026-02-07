"""Frontmatter update utilities for agents and prompts.

This module provides a single source of truth for frontmatter manipulation
used by both the sync command and config tooling.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable


def resolve_meta_model(config: dict, name: str) -> dict:
    """Resolve a meta-model reference to actual model + thinking settings.
    
    Resolution order:
    1. Check if name is a direct meta-model key
    2. Check if name is an agent reference (lookup in agents -> meta-models)
    3. Check if name is a prompt reference (lookup in prompts -> meta-models)
    4. Fallback: treat as direct model reference
    
    Args:
        config: The workflow configuration dictionary containing metaModels,
                agents, and prompts mappings.
        name: The name to resolve (agent name, prompt name, or meta-model key).
        
    Returns:
        A dictionary with 'model' and 'thinking' keys.
    """
    meta_models = config.get("metaModels", {}) or {}
    
    # If name is already a meta-model key, return it directly
    if name in meta_models:
        return meta_models[name]
    
    # Check if it's an agent reference
    agents = config.get("agents", {}) or {}
    if name in agents:
        meta_key = agents[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})
    
    # Check if it's a prompt reference
    prompts = config.get("prompts", {}) or {}
    if name in prompts:
        meta_key = prompts[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})
    
    # Fallback: treat as direct model reference
    return {"model": name, "thinking": "medium"}


def _update_frontmatter(
    content: str,
    updates: dict[str, str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Update frontmatter fields in markdown content.
    
    Args:
        content: The markdown file content.
        updates: Dictionary of field names to new values.
        predicate: Optional function to determine if update should apply.
                   Receives the current frontmatter text, returns True to apply.
                   
    Returns:
        Updated content with new frontmatter values.
    """
    frontmatter_pattern = r"^(---\s*\n)(.*?)(\n---\s*\n)"
    
    def replace(match):
        prefix, fm, suffix = match.group(1), match.group(2), match.group(3)
        
        # Check predicate if provided
        if predicate is not None and not predicate(fm):
            return match.group(0)
        
        # Apply each update
        for field, value in updates.items():
            field_pattern = rf"^{field}:\s*"
            new_line = f"{field}: {value}"
            
            if re.search(field_pattern, fm, re.MULTILINE):
                # Update existing field
                fm = re.sub(
                    rf"^{field}:\s*.*$",
                    new_line,
                    fm,
                    flags=re.MULTILINE,
                )
            else:
                # Add new field
                fm += f"\n{new_line}"
        
        return prefix + fm + suffix
    
    return re.sub(frontmatter_pattern, replace, content, flags=re.DOTALL)


def update_frontmatter_fields(
    file_path: Path,
    updates: dict[str, str],
    predicate: Callable[[str], bool] | None = None,
) -> bool:
    """Update frontmatter fields in a markdown file.
    
    Args:
        file_path: Path to the markdown file.
        updates: Dictionary of field names to new values.
        predicate: Optional predicate function for conditional updates.
        
    Returns:
        True if the file was modified, False otherwise.
    """
    content = file_path.read_text(encoding="utf-8")
    new_content = _update_frontmatter(content, updates, predicate)
    
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_agent_frontmatter(
    agent_path: Path,
    config: dict,
    agent_name: str,
    default_model: str = "openai-codex/gpt-5.1-codex-mini",
    default_thinking: str = "medium",
) -> bool:
    """Update agent file with resolved meta-model settings.
    
    Args:
        agent_path: Path to the agent markdown file.
        config: The workflow configuration dictionary.
        agent_name: The name of the agent (used for meta-model lookup).
        default_model: Default model if not resolved from config.
        default_thinking: Default thinking level if not resolved from config.
        
    Returns:
        True if the file was modified, False otherwise.
    """
    resolved = resolve_meta_model(config, agent_name)
    updates = {
        "model": resolved.get("model", default_model),
        "thinking": resolved.get("thinking", default_thinking),
    }
    return update_frontmatter_fields(agent_path, updates)


def update_prompt_frontmatter(
    prompt_path: Path,
    config: dict,
    prompt_name: str,
    default_model: str = "openai-codex/gpt-5.1-codex-mini",
    default_thinking: str = "medium",
) -> bool:
    """Update prompt file with resolved meta-model settings.
    
    Args:
        prompt_path: Path to the prompt markdown file.
        config: The workflow configuration dictionary.
        prompt_name: The name of the prompt (used for meta-model lookup).
        default_model: Default model if not resolved from config.
        default_thinking: Default thinking level if not resolved from config.
        
    Returns:
        True if the file was modified, False otherwise.
    """
    resolved = resolve_meta_model(config, prompt_name)
    updates = {
        "model": resolved.get("model", default_model),
        "thinking": resolved.get("thinking", default_thinking),
    }
    return update_frontmatter_fields(prompt_path, updates)


def sync_models_to_files(
    config: dict,
    agents_dir: Path | None,
    prompts_dir: Path | None,
    default_model: str = "openai-codex/gpt-5.1-codex-mini",
    default_thinking: str = "medium",
) -> dict:
    """Sync meta-model configuration to all agents and prompts.
    
    Args:
        config: The workflow configuration dictionary.
        agents_dir: Directory containing agent markdown files, or None to skip.
        prompts_dir: Directory containing prompt markdown files, or None to skip.
        default_model: Default model for unresolved names.
        default_thinking: Default thinking level for unresolved names.
        
    Returns:
        Dictionary with keys 'agents', 'prompts', and 'errors' containing
        lists of updated items and any errors encountered.
    """
    results = {"agents": [], "prompts": [], "errors": []}
    
    # Sync agents
    if agents_dir is not None and agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            try:
                if update_agent_frontmatter(
                    agent_file, config, agent_name, default_model, default_thinking
                ):
                    results["agents"].append(agent_name)
            except Exception as e:
                results["errors"].append(f"agents/{agent_file.name}: {e}")
    
    # Sync prompts
    if prompts_dir is not None and prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            prompt_name = prompt_file.stem
            try:
                if update_prompt_frontmatter(
                    prompt_file, config, prompt_name, default_model, default_thinking
                ):
                    results["prompts"].append(prompt_name)
            except Exception as e:
                results["errors"].append(f"prompts/{prompt_file.name}: {e}")
    
    return results
