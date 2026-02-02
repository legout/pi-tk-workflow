#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path

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


def resolve_project_config(base: Path) -> Path:
    project_config = Path(".pi/workflows/irf/config.json")
    if str(base).endswith("/.pi"):
        project_config = base / "workflows/irf/config.json"
    return project_config


def load_workflow_config(base: Path, ignore_project: bool) -> dict:
    global_config = Path.home() / ".pi/agent/workflows/irf/config.json"
    project_config = resolve_project_config(base)

    if ignore_project:
        return read_json(global_config)

    return merge(read_json(global_config), read_json(project_config))


def resolve_project_root(base: Path) -> Path:
    if str(base).endswith("/.pi"):
        return base.parent
    return Path.cwd()


def resolve_knowledge_dir(config: dict, base: Path) -> Path:
    knowledge_dir = config.get("workflow", {}).get("knowledgeDir", ".pi/knowledge")
    knowledge_path = Path(str(knowledge_dir)).expanduser()
    if not knowledge_path.is_absolute():
        knowledge_path = resolve_project_root(base) / knowledge_dir
    return knowledge_path


def get_checker_tools(config: dict):
    checkers = config.get("checkers", {}) or {}
    cmds = set()
    for spec in checkers.values():
        for key in ("lint", "format", "typecheck"):
            cmd = spec.get(key)
            if not cmd:
                continue
            try:
                parts = shlex.split(cmd)
            except ValueError:
                parts = cmd.split()
            if parts:
                cmds.add(parts[0])
    return sorted(cmds)


def get_mcp_servers(config: dict):
    mcp_servers = config.get("workflow", {}).get("mcpServers")
    if mcp_servers is None:
        return [
            "context7",
            "exa",
            "grep_app",
            "zai-web-search",
            "zai-web-reader",
            "zai-vision",
        ]
    if isinstance(mcp_servers, list):
        return [str(s) for s in mcp_servers]
    return [str(mcp_servers)]


def configure_mcp(config: dict, mcp_file: Path, zai_key: str, ctx7_key: str, exa_key: str):
    allowed = set(get_mcp_servers(config))

    if mcp_file.exists():
        try:
            mcp_config = json.loads(mcp_file.read_text(encoding="utf-8"))
        except Exception:
            mcp_config = {}
    else:
        mcp_config = {}

    if not isinstance(mcp_config, dict):
        mcp_config = {}

    mcp_config.setdefault("settings", {})
    mcp_config["settings"].setdefault("toolPrefix", "short")
    mcp_config["mcpServers"] = {}

    servers = mcp_config["mcpServers"]

    def set_server(name, url, headers=None, auth=None):
        if name not in allowed:
            return
        srv = {"url": url}
        if auth:
            srv["auth"] = auth
        if headers:
            srv["headers"] = headers
        servers[name] = srv

    ctx7_key = ctx7_key.strip()
    exa_key = exa_key.strip()
    zai_key = zai_key.strip()

    set_server(
        "context7",
        "https://mcp.context7.com/mcp",
        headers={"CONTEXT7_API_KEY": ctx7_key} if ctx7_key else None,
    )
    set_server(
        "exa",
        "https://mcp.exa.ai/mcp",
        headers={"EXA_API_KEY": exa_key} if exa_key else None,
    )
    set_server("grep_app", "https://mcp.grep.app")

    if zai_key:
        headers = {"Authorization": f"Bearer {zai_key}"}
        set_server(
            "zai-web-search",
            "https://api.z.ai/api/mcp/web_search_prime/mcp",
            headers=headers,
            auth="bearer",
        )
        set_server(
            "zai-web-reader",
            "https://api.z.ai/api/mcp/web_reader/mcp",
            headers=headers,
            auth="bearer",
        )
        set_server(
            "zai-vision",
            "https://api.z.ai/api/mcp/vision/mcp",
            headers=headers,
            auth="bearer",
        )
    else:
        if allowed.intersection({"zai-web-search", "zai-web-reader", "zai-vision"}):
            print("ZAI_API_KEY not provided; skipping ZAI MCP servers.", file=sys.stderr)

    if not allowed:
        print("workflow.mcpServers is empty; no MCP servers configured.", file=sys.stderr)

    mcp_file.parent.mkdir(parents=True, exist_ok=True)
    mcp_file.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")
    print(f"Configured MCP servers in {mcp_file}")


def resolve_meta_model(config: dict, name: str) -> dict:
    """Resolve a meta-model reference to actual model + thinking."""
    meta_models = config.get("metaModels", {})
    
    # If name is already a meta-model key, resolve it
    if name in meta_models:
        return meta_models[name]
    
    # Check if it's an agent reference
    agents = config.get("agents", {})
    if name in agents:
        meta_key = agents[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})
    
    # Check if it's a prompt reference
    prompts = config.get("prompts", {})
    if name in prompts:
        meta_key = prompts[name]
        return meta_models.get(meta_key, {"model": name, "thinking": "medium"})
    
    # Fallback: treat as direct model reference
    return {"model": name, "thinking": "medium"}


def update_agent_frontmatter(agent_path: Path, config: dict, agent_name: str) -> bool:
    """Update agent file with resolved meta-model."""
    content = agent_path.read_text(encoding="utf-8")
    
    # Resolve the meta-model for this agent
    resolved = resolve_meta_model(config, agent_name)
    model = resolved.get("model", "openai-codex/gpt-5.1-codex-mini")
    thinking = resolved.get("thinking", "medium")
    
    # Pattern to match frontmatter
    frontmatter_pattern = r'^(---\s*\n)(.*?)(\n---\s*\n)'
    
    def replace_frontmatter(match):
        prefix = match.group(1)
        frontmatter = match.group(2)
        suffix = match.group(3)
        
        # Update or add model
        if re.search(r'^model:\s*', frontmatter, re.MULTILINE):
            frontmatter = re.sub(
                r'^model:\s*.*$', 
                f'model: {model}', 
                frontmatter, 
                flags=re.MULTILINE
            )
        else:
            frontmatter += f'\nmodel: {model}'
        
        # Update or add thinking
        if re.search(r'^thinking:\s*', frontmatter, re.MULTILINE):
            frontmatter = re.sub(
                r'^thinking:\s*.*$', 
                f'thinking: {thinking}', 
                frontmatter, 
                flags=re.MULTILINE
            )
        else:
            frontmatter += f'\nthinking: {thinking}'
        
        return prefix + frontmatter + suffix
    
    new_content = re.sub(frontmatter_pattern, replace_frontmatter, content, flags=re.DOTALL)
    
    if new_content != content:
        agent_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_prompt_frontmatter(prompt_path: Path, config: dict, prompt_name: str) -> bool:
    """Update prompt file with resolved meta-model."""
    content = prompt_path.read_text(encoding="utf-8")
    
    # Resolve the meta-model for this prompt
    resolved = resolve_meta_model(config, prompt_name)
    model = resolved.get("model", "openai-codex/gpt-5.1-codex-mini")
    thinking = resolved.get("thinking", "medium")
    
    # Pattern to match frontmatter
    frontmatter_pattern = r'^(---\s*\n)(.*?)(\n---\s*\n)'
    
    def replace_frontmatter(match):
        prefix = match.group(1)
        frontmatter = match.group(2)
        suffix = match.group(3)
        
        # Update or add model
        if re.search(r'^model:\s*', frontmatter, re.MULTILINE):
            frontmatter = re.sub(
                r'^model:\s*.*$', 
                f'model: {model}', 
                frontmatter, 
                flags=re.MULTILINE
            )
        else:
            frontmatter += f'\nmodel: {model}'
        
        # Update or add thinking
        if re.search(r'^thinking:\s*', frontmatter, re.MULTILINE):
            frontmatter = re.sub(
                r'^thinking:\s*.*$', 
                f'thinking: {thinking}', 
                frontmatter, 
                flags=re.MULTILINE
            )
        else:
            frontmatter += f'\nthinking: {thinking}'
        
        return prefix + frontmatter + suffix
    
    new_content = re.sub(frontmatter_pattern, replace_frontmatter, content, flags=re.DOTALL)
    
    if new_content != content:
        prompt_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def sync_models(config: dict, base: Path) -> dict:
    """Sync models from config to all agents and prompts."""
    results = {"agents": [], "prompts": [], "errors": []}
    
    # Sync agents
    agents_dir = base / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            try:
                if update_agent_frontmatter(agent_file, config, agent_name):
                    results["agents"].append(agent_name)
            except Exception as e:
                results["errors"].append(f"agents/{agent_file.name}: {e}")
    
    # Sync prompts
    prompts_dir = base / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            prompt_name = prompt_file.stem
            try:
                if update_prompt_frontmatter(prompt_file, config, prompt_name):
                    results["prompts"].append(prompt_name)
            except Exception as e:
                results["errors"].append(f"prompts/{prompt_file.name}: {e}")
    
    return results


def parse_args():
    parser = argparse.ArgumentParser(description="IRF config helper")
    parser.add_argument("--base", default=os.environ.get("TARGET_BASE", ""))
    parser.add_argument(
        "--ignore-project",
        action="store_true",
        default=os.environ.get("IGNORE_PROJECT_CONFIG", "").lower() == "true",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("print-config")
    subparsers.add_parser("checker-tools")
    subparsers.add_parser("knowledge-dir")
    subparsers.add_parser("mcp-servers")
    subparsers.add_parser("sync-models", help="Sync meta-models to agents and prompts")

    mcp_parser = subparsers.add_parser("configure-mcp")
    mcp_parser.add_argument("--mcp-file", required=True)
    mcp_parser.add_argument("--zai-key", default=os.environ.get("ZAI_API_KEY", ""))
    mcp_parser.add_argument("--ctx7-key", default=os.environ.get("CONTEXT7_API_KEY", ""))
    mcp_parser.add_argument("--exa-key", default=os.environ.get("EXA_API_KEY", ""))

    return parser.parse_args()


def main():
    args = parse_args()
    base = Path(args.base).expanduser() if args.base else Path.cwd()

    config = load_workflow_config(base, args.ignore_project)

    if args.command == "print-config":
        print(json.dumps(config))
        return
    if args.command == "checker-tools":
        print("\n".join(get_checker_tools(config)))
        return
    if args.command == "knowledge-dir":
        print(resolve_knowledge_dir(config, base))
        return
    if args.command == "mcp-servers":
        print("\n".join(get_mcp_servers(config)))
        return
    if args.command == "sync-models":
        results = sync_models(config, base)
        if results["agents"]:
            print(f"Updated agents: {', '.join(results['agents'])}")
        if results["prompts"]:
            print(f"Updated prompts: {', '.join(results['prompts'])}")
        if results["errors"]:
            print("Errors:", file=sys.stderr)
            for err in results["errors"]:
                print(f"  {err}", file=sys.stderr)
        return
    if args.command == "configure-mcp":
        configure_mcp(
            config,
            Path(args.mcp_file).expanduser(),
            args.zai_key or "",
            args.ctx7_key or "",
            args.exa_key or "",
        )
        return

    raise SystemExit(1)


if __name__ == "__main__":
    main()
