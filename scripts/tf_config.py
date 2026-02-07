#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import sys
from pathlib import Path

# Add parent directory to path for tf_cli imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tf_cli.frontmatter import (
    resolve_meta_model,
    update_agent_frontmatter,
    update_prompt_frontmatter,
    sync_models_to_files,
)
from tf_cli.utils import merge, read_json


def resolve_project_root(base: Path) -> Path:
    # Project installs pass base=<project>/.pi
    if str(base).endswith("/.pi"):
        return base.parent
    # Global installs pass base=~/.pi/agent, but the active project is cwd
    return Path.cwd()


def resolve_project_config(base: Path) -> Path:
    # TF workflow config lives in .tf/config (project-local override)
    return resolve_project_root(base) / ".tf/config/settings.json"


def load_workflow_config(base: Path, ignore_project: bool) -> dict:
    # Optional global TF config (if present)
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


def resolve_knowledge_dir(config: dict, base: Path) -> Path:
    knowledge_dir = config.get("workflow", {}).get("knowledgeDir", ".tf/knowledge")
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


def sync_models(config: dict, base: Path) -> dict:
    """Sync models from config to all agents and prompts."""
    sync_base = resolve_sync_base(base)
    agents_dir = sync_base / "agents"
    prompts_dir = sync_base / "prompts"
    
    return sync_models_to_files(
        config,
        agents_dir if agents_dir.exists() else None,
        prompts_dir if prompts_dir.exists() else None,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="TF config helper")
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
