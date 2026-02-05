from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional


def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def merge(a, b):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def resolve_project_root(base: Path) -> Path:
    if str(base).endswith("/.pi"):
        return base.parent
    return Path.cwd()


def resolve_project_config(base: Path) -> Path:
    return resolve_project_root(base) / ".tf/config/settings.json"


def load_workflow_config(base: Path, ignore_project: bool) -> dict:
    global_config = Path.home() / ".tf/config/settings.json"
    project_config = resolve_project_config(base)
    if ignore_project:
        return read_json(global_config)
    return merge(read_json(global_config), read_json(project_config))


def resolve_sync_base(base: Path) -> Path:
    agents_dir = base / "agents"
    prompts_dir = base / "prompts"
    if agents_dir.exists() or prompts_dir.exists():
        return base

    global_base = Path.home() / ".pi/agent"
    if (global_base / "agents").exists() or (global_base / "prompts").exists():
        return global_base

    return base


def resolve_meta_model(config: dict, name: str) -> dict:
    meta_models = config.get("metaModels", {})
    if name in meta_models:
        return meta_models[name]

    agents = config.get("agents", {})
    if name in agents:
        meta_key = agents[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})

    prompts = config.get("prompts", {})
    if name in prompts:
        meta_key = prompts[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})

    return {"model": name, "thinking": "medium"}


def update_agent_frontmatter(agent_path: Path, config: dict, agent_name: str) -> bool:
    content = agent_path.read_text(encoding="utf-8")
    resolved = resolve_meta_model(config, agent_name)
    model = resolved.get("model", "openai-codex/gpt-5.1-codex-mini")
    thinking = resolved.get("thinking", "medium")

    frontmatter_pattern = r"^(---\s*\n)(.*?)(\n---\s*\n)"

    def replace_frontmatter(match):
        prefix = match.group(1)
        frontmatter = match.group(2)
        suffix = match.group(3)

        if re.search(r"^model:\s*", frontmatter, re.MULTILINE):
            frontmatter = re.sub(r"^model:\s*.*$", f"model: {model}", frontmatter, flags=re.MULTILINE)
        else:
            frontmatter += f"\nmodel: {model}"

        if re.search(r"^thinking:\s*", frontmatter, re.MULTILINE):
            frontmatter = re.sub(r"^thinking:\s*.*$", f"thinking: {thinking}", frontmatter, flags=re.MULTILINE)
        else:
            frontmatter += f"\nthinking: {thinking}"

        return prefix + frontmatter + suffix

    new_content = re.sub(frontmatter_pattern, replace_frontmatter, content, flags=re.DOTALL)

    if new_content != content:
        agent_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_prompt_frontmatter(prompt_path: Path, config: dict, prompt_name: str) -> bool:
    content = prompt_path.read_text(encoding="utf-8")
    resolved = resolve_meta_model(config, prompt_name)
    model = resolved.get("model", "openai-codex/gpt-5.1-codex-mini")
    thinking = resolved.get("thinking", "medium")

    frontmatter_pattern = r"^(---\s*\n)(.*?)(\n---\s*\n)"

    def replace_frontmatter(match):
        prefix = match.group(1)
        frontmatter = match.group(2)
        suffix = match.group(3)

        if re.search(r"^model:\s*", frontmatter, re.MULTILINE):
            frontmatter = re.sub(r"^model:\s*.*$", f"model: {model}", frontmatter, flags=re.MULTILINE)
        else:
            frontmatter += f"\nmodel: {model}"

        if re.search(r"^thinking:\s*", frontmatter, re.MULTILINE):
            frontmatter = re.sub(r"^thinking:\s*.*$", f"thinking: {thinking}", frontmatter, flags=re.MULTILINE)
        else:
            frontmatter += f"\nthinking: {thinking}"

        return prefix + frontmatter + suffix

    new_content = re.sub(frontmatter_pattern, replace_frontmatter, content, flags=re.DOTALL)

    if new_content != content:
        prompt_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def sync_models(config: dict, base: Path) -> dict:
    results = {"agents": [], "prompts": [], "errors": []}
    sync_base = resolve_sync_base(base)

    agents_dir = sync_base / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            try:
                if update_agent_frontmatter(agent_file, config, agent_name):
                    results["agents"].append(agent_name)
            except Exception as e:
                results["errors"].append(f"agents/{agent_file.name}: {e}")

    prompts_dir = sync_base / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            prompt_name = prompt_file.stem
            try:
                if update_prompt_frontmatter(prompt_file, config, prompt_name):
                    results["prompts"].append(prompt_name)
            except Exception as e:
                results["errors"].append(f"prompts/{prompt_file.name}: {e}")

    return results


def resolve_target_base(args) -> tuple[Path, bool]:
    if args.project:
        project_root = Path(args.project).expanduser()
        return project_root / ".pi", False
    if args.global_install:
        return Path.home() / ".pi/agent", True

    if (Path.cwd() / ".pi").is_dir():
        return Path.cwd() / ".pi", False

    return Path.home() / ".pi/agent", True


def run_sync(args: argparse.Namespace) -> int:
    base, ignore_project = resolve_target_base(args)
    config = load_workflow_config(base, ignore_project)

    print("Syncing models from meta-model configuration...")
    results = sync_models(config, base)
    if results["agents"]:
        print(f"Updated agents: {', '.join(results['agents'])}")
    if results["prompts"]:
        print(f"Updated prompts: {', '.join(results['prompts'])}")
    if results["errors"]:
        print("Errors:", file=sys.stderr)
        for err in results["errors"]:
            print(f"  {err}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new sync")
    parser.add_argument("--project", help="Operate on project at <path>")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Use ~/.pi/agent (default)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_sync(args)


if __name__ == "__main__":
    raise SystemExit(main())
