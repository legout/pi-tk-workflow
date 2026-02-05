from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

DEFAULT_MCP_SERVERS = [
    "context7",
    "exa",
    "grep_app",
    "zai-web-search",
    "zai-web-reader",
    "zai-vision",
]


def read_json(path: Path) -> Dict:
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


def resolve_target_base(args: argparse.Namespace) -> tuple[Path, bool]:
    if args.project:
        project_root = Path(args.project).expanduser()
        return project_root / ".pi", False
    if args.global_install:
        return Path.home() / ".pi/agent", True
    if (Path.cwd() / ".pi").is_dir():
        return Path.cwd() / ".pi", False
    return Path.home() / ".pi/agent", True


def get_mcp_servers(config: dict) -> list[str]:
    mcp_servers = config.get("workflow", {}).get("mcpServers")
    if mcp_servers is None:
        return DEFAULT_MCP_SERVERS
    if isinstance(mcp_servers, list):
        return [str(s) for s in mcp_servers]
    return [str(mcp_servers)]


def configure_web_search(target_base: Path, perplexity_key: str) -> None:
    web_search_json = target_base / "web-search.json"
    target_base.mkdir(parents=True, exist_ok=True)
    config = {}
    if web_search_json.exists():
        try:
            config = json.loads(web_search_json.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    config["perplexityApiKey"] = perplexity_key
    web_search_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    web_search_json.chmod(0o600)


def configure_mcp(target_base: Path, config: dict, zai_key: str, ctx7_key: str, exa_key: str) -> None:
    mcp_file = target_base / "mcp.json"
    allowed = set(get_mcp_servers(config))

    mcp_config = {"settings": {"toolPrefix": "short"}, "mcpServers": {}}

    def set_server(name: str, url: str, headers: Optional[dict] = None, auth: Optional[str] = None):
        if name not in allowed:
            return
        srv = {"url": url}
        if auth:
            srv["auth"] = auth
        if headers:
            srv["headers"] = headers
        mcp_config["mcpServers"][name] = srv

    ctx7_key = ctx7_key.strip()
    exa_key = exa_key.strip()
    zai_key = zai_key.strip()

    set_server("context7", "https://mcp.context7.com/mcp", headers={"CONTEXT7_API_KEY": ctx7_key} if ctx7_key else None)
    set_server("exa", "https://mcp.exa.ai/mcp", headers={"EXA_API_KEY": exa_key} if exa_key else None)
    set_server("grep_app", "https://mcp.grep.app")

    if zai_key:
        headers = {"Authorization": f"Bearer {zai_key}"}
        set_server("zai-web-search", "https://api.z.ai/api/mcp/web_search_prime/mcp", headers=headers, auth="bearer")
        set_server("zai-web-reader", "https://api.z.ai/api/mcp/web_reader/mcp", headers=headers, auth="bearer")
        set_server("zai-vision", "https://api.z.ai/api/mcp/vision/mcp", headers=headers, auth="bearer")
    else:
        if allowed.intersection({"zai-web-search", "zai-web-reader", "zai-vision"}):
            print("ZAI_API_KEY not provided; skipping ZAI MCP servers.", file=sys.stderr)

    if not allowed:
        print("workflow.mcpServers is empty; no MCP servers configured.", file=sys.stderr)

    mcp_file.parent.mkdir(parents=True, exist_ok=True)
    mcp_file.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new login")
    parser.add_argument("--project", help="Operate on project at <path>")
    parser.add_argument("--global", dest="global_install", action="store_true", help="Use ~/.pi/agent (default)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_base, ignore_project = resolve_target_base(args)
    config = load_workflow_config(target_base, ignore_project)

    print("Ticketflow Login\n")
    print("Configure API keys for external services.")
    print("Leave blank to skip a service.\n")

    if ignore_project:
        print(f"Using global config: {target_base}")
    else:
        print(f"Using project config: {target_base}")

    print("\n=== Web Search (pi-web-access) ===")
    print("Required for web search functionality.")
    print("Get a key at: https://perplexity.ai/settings/api")
    perplexity_key = input("Perplexity API key: ").strip() or os.environ.get("PERPLEXITY_API_KEY", "")

    print("\n=== MCP Servers ===")
    print("Context7: Works without API key (rate limited)")
    print("Get a key at: https://context7.com/ (optional)")
    ctx7_key = input("Context7 API key (optional): ").strip() or os.environ.get("CONTEXT7_API_KEY", "")

    print("\nExa: Works without API key (rate limited)")
    print("Get a key at: https://exa.ai/ (optional)")
    exa_key = input("Exa API key (optional): ").strip() or os.environ.get("EXA_API_KEY", "")

    print("\nZAI: Required for ZAI MCP servers (web-search, web-reader, vision)")
    zai_key = input("ZAI API key (optional): ").strip() or os.environ.get("ZAI_API_KEY", "")

    if perplexity_key:
        print("\nConfiguring web search...")
        configure_web_search(target_base, perplexity_key)
        print("✓ Configured pi-web-access")
    else:
        print("\nNote: Perplexity API key not provided. To enable web search later:")
        print("  tf new login")

    has_mcp_keys = bool(zai_key or ctx7_key or exa_key)
    if has_mcp_keys:
        print("\nConfiguring MCP servers...")
        configure_mcp(target_base, config, zai_key, ctx7_key, exa_key)
    else:
        print("\nNote: No MCP API keys provided. To configure MCP servers later:")
        print("  tf new login")

    print("\nLogin complete. API keys saved to:")
    if perplexity_key:
        print(f"  - {target_base / 'web-search.json'}")
    if has_mcp_keys:
        print(f"  - {target_base / 'mcp.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
