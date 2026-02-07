from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


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


def configure_mcp(target_base: Path, *, zai_key: str, ctx7_key: str, exa_key: str) -> None:
    """Write ~/.pi/agent/mcp.json.

    This is global Pi configuration (not project configuration).
    """

    mcp_file = target_base / "mcp.json"

    mcp_config = {"settings": {"toolPrefix": "short"}, "mcpServers": {}}

    def set_server(name: str, url: str, headers: Optional[dict] = None, auth: Optional[str] = None):
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
        print("ZAI_API_KEY not provided; skipping ZAI MCP servers.", file=sys.stderr)

    target_base.mkdir(parents=True, exist_ok=True)
    mcp_file.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")
    try:
        mcp_file.chmod(0o600)
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf login")
    parser.add_argument(
        "--project",
        help="Ignored (login is global). Present for backward compatibility.",
    )
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Optional (login is global by default)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    _ = build_parser().parse_args(argv)

    target_base = Path.home() / ".pi" / "agent"

    print("Ticketflow Login (global)\n")
    print("Configures API keys for Pi web search + MCP servers.")
    print(f"Writes to: {target_base}\n")

    print("=== Web Search (pi-web-access) ===")
    print("Get a key at: https://perplexity.ai/settings/api")
    perplexity_key = input("Perplexity API key (optional): ").strip() or os.environ.get("PERPLEXITY_API_KEY", "")

    print("\n=== MCP Servers ===")
    ctx7_key = input("Context7 API key (optional): ").strip() or os.environ.get("CONTEXT7_API_KEY", "")
    exa_key = input("Exa API key (optional): ").strip() or os.environ.get("EXA_API_KEY", "")
    zai_key = input("ZAI API key (optional): ").strip() or os.environ.get("ZAI_API_KEY", "")

    if perplexity_key:
        configure_web_search(target_base, perplexity_key)
        print("\n✓ Configured web search")
    else:
        print("\nNote: Perplexity API key not provided. Web search remains disabled.")

    has_mcp_keys = bool(zai_key or ctx7_key or exa_key)
    if has_mcp_keys:
        configure_mcp(target_base, zai_key=zai_key, ctx7_key=ctx7_key, exa_key=exa_key)
        print("✓ Configured MCP servers")
    else:
        print("Note: No MCP API keys provided. MCP remains unconfigured.")

    print("\nLogin complete. Files:")
    if perplexity_key:
        print(f"  - {target_base / 'web-search.json'}")
    if has_mcp_keys:
        print(f"  - {target_base / 'mcp.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
