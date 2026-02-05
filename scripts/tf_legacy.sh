#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_URL="https://raw.githubusercontent.com/legout/pi-ticketflow/main"
CONFIG_HELPER=""
CONFIG_HELPER_SUPPORTS_FLAGS=false

# Fallback for dev mode: use scripts/tf_config.py from the repo
if [ -f "$ROOT_DIR/scripts/tf_config.py" ]; then
  CONFIG_HELPER="$ROOT_DIR/scripts/tf_config.py"
  if grep -q 'add_argument("--base"' "$CONFIG_HELPER"; then
    CONFIG_HELPER_SUPPORTS_FLAGS=true
  fi
fi

usage() {
  cat <<'EOF'
Ticketflow CLI

Usage:
  tf setup [--global|--project <path>]
  tf init [--project <path>]
  tf login [--global|--project <path>]
  tf sync [--project <path>]
  tf update [--global|--project <path>]
  tf doctor [--project <path>]
  tf next [--project <path>]
  tf backlog-ls [topic-id-or-path] [--project <path>]
  tf track <path> [--file <files_changed_path>]
  tf ralph <subcommand> [options]

Commands:
  setup       Install Pi assets + optional dependencies + MCP config
  init        Scaffold .tf/ directories (config, knowledge, ralph)
  login       Configure API keys (Perplexity, Context7, Exa, ZAI)
  sync        Sync agent models from workflow config into agent files
  update      Download latest agents, skills, and prompts
  doctor      Preflight checks for tk/pi/extensions/checkers
  next        Print the next open and ready ticket id
  backlog-ls  List backlog status and tickets for seed/baseline topics
  track       Append file paths to files_changed.txt (deduped)
  ralph       Ralph loop management (see below)
  agentsmd    AGENTS.md management (init, validate, fix, status)

Ralph Subcommands:
  ralph init     Create .tf/ralph/ directory structure
  ralph status   Show current loop state and statistics
  ralph reset    Clear progress (optionally keep lessons)
  ralph lessons  Show or prune lessons learned
  ralph start    Run loop via pi -c (uses /tf)
  ralph run      Run one ticket via pi -c (uses /tf)

Agentsmd Subcommands:
  agentsmd init [path]     Create minimal AGENTS.md (defaults: uv, current dir)
  agentsmd status [path]   Show AGENTS.md overview and recommendations
  agentsmd validate [path] Check for bloat, stale paths, contradictions
  agentsmd fix [path]      Auto-fix common issues (backup created)

Options:
  --global                 Install/sync Pi files in ~/.pi/agent (setup/login only)
  --project <path>         Operate on project at <path> (uses <path>/.pi + <path>/.tf)
  --file <path>            Output files_changed.txt path (track only)
  --keep-lessons           Keep lessons when resetting (ralph reset only)
  --help                   Show this help

Environment (for setup MCP):
  ZAI_API_KEY, CONTEXT7_API_KEY, EXA_API_KEY, PERPLEXITY_API_KEY

Environment (for track):
  TF_FILES_CHANGED, TF_CHAIN_DIR
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

COMMAND="$1"
shift

TARGET_BASE=""   # Pi base (global: ~/.pi/agent, project: <root>/.pi)
TF_BASE=""       # TF base (project: <root>/.tf)
SCOPE_FLAG=""
TRACK_FILE=""
ARGS=()
IS_GLOBAL=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --global)
      TARGET_BASE="$HOME/.pi/agent"
      TF_BASE=""
      SCOPE_FLAG=""
      IS_GLOBAL=true
      shift
      ;;
    --project)
      if [ -z "${2:-}" ]; then
        echo "Missing path after --project" >&2
        exit 1
      fi
      TARGET_BASE="$2/.pi"
      TF_BASE="$2/.tf"
      SCOPE_FLAG="-l"
      IS_GLOBAL=false
      shift 2
      ;;
    --file)
      if [ "$COMMAND" != "track" ]; then
        echo "--file is only valid with 'track'" >&2
        usage
        exit 1
      fi
      if [ -z "${2:-}" ]; then
        echo "Missing path after --file" >&2
        exit 1
      fi
      TRACK_FILE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        ARGS+=("$1")
        shift
      done
      ;;
    -* )
      # For ralph command, pass options through to subcommand
      if [ "$COMMAND" = "ralph" ]; then
        ARGS+=("$1")
        shift
      else
        echo "Unknown option: $1" >&2
        usage
        exit 1
      fi
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
 done

if [ -z "$TARGET_BASE" ] && [ "$COMMAND" != "track" ]; then
  case "$COMMAND" in
    setup)
      # setup defaults to global unless the user selects project during the prompt below
      TARGET_BASE="$HOME/.pi/agent"
      IS_GLOBAL=true
      ;;
    init)
      TARGET_BASE="$(pwd)/.pi"
      TF_BASE="$(pwd)/.tf"
      SCOPE_FLAG="-l"
      IS_GLOBAL=false
      ;;
    login)
      if [ -d ".pi" ]; then
        TARGET_BASE="$(pwd)/.pi"
        SCOPE_FLAG="-l"
        IS_GLOBAL=false
      else
        TARGET_BASE="$HOME/.pi/agent"
        IS_GLOBAL=true
      fi
      ;;
    update)
      if [ -d ".pi" ]; then
        TARGET_BASE="$(pwd)/.pi"
        if [ -d ".tf" ]; then
          TF_BASE="$(pwd)/.tf"
        fi
        SCOPE_FLAG="-l"
        IS_GLOBAL=false
      else
        TARGET_BASE="$HOME/.pi/agent"
        IS_GLOBAL=true
      fi
      ;;
    *)
      if [ -d ".tf" ] && [ -d ".pi" ]; then
        TARGET_BASE="$(pwd)/.pi"
        TF_BASE="$(pwd)/.tf"
        SCOPE_FLAG="-l"
        IS_GLOBAL=false
      elif [ -d ".tf" ]; then
        TARGET_BASE="$(pwd)/.pi"
        TF_BASE="$(pwd)/.tf"
        SCOPE_FLAG="-l"
        IS_GLOBAL=false
      elif [ -d ".pi" ]; then
        TARGET_BASE="$(pwd)/.pi"
        IS_GLOBAL=false
      else
        TARGET_BASE="$HOME/.pi/agent"
        IS_GLOBAL=true
      fi
      ;;
  esac
fi

install_files() {
  if [ ! -f "$ROOT_DIR/config/install-manifest.txt" ] && [ ! -d "$ROOT_DIR/agents" ]; then
    echo "[info] Install sources not found under $ROOT_DIR; skipping file install." >&2
    return 0
  fi

  local manifest="$ROOT_DIR/config/install-manifest.txt"

  # NOTE: When running `tf setup` from an already-installed workflow,
  # older installs may not have shipped the install manifest.
  # In that case, fall back to a baked-in manifest so setup still works.
  local manifest_content=""
  if [ -f "$manifest" ]; then
    manifest_content="$(cat "$manifest")"
  else
    echo "[warn] Install manifest not found: $manifest" >&2
    echo "[warn] Falling back to built-in manifest (please re-install/upgrade for full fidelity)." >&2
    manifest_content="$(cat <<'EOF'
# CLI tool
bin/tf

# Needed so `tf setup` can be run from an already-installed workflow
config/install-manifest.txt

# Helper scripts for CLI
scripts/tf_config.py
scripts/tf_legacy.sh

agents/reviewer-general.md
agents/reviewer-spec-audit.md
agents/reviewer-second-opinion.md
agents/review-merge.md
agents/researcher.md
agents/researcher-fetch.md
agents/fixer.md
agents/closer.md

skills/tf-workflow/SKILL.md
skills/tf-planning/SKILL.md
skills/tf-config/SKILL.md
skills/ralph/SKILL.md

prompts/tf.md
prompts/tf-next.md
prompts/tf-plan.md
prompts/tf-plan-consult.md
prompts/tf-plan-revise.md
prompts/tf-plan-review.md
prompts/tf-seed.md
prompts/tf-backlog.md
prompts/tf-backlog-ls.md
prompts/tf-spike.md
prompts/tf-backlog-from-openspec.md
prompts/tf-baseline.md
prompts/tf-followups.md
prompts/tf-sync.md
prompts/ralph-start.md

config/settings.json
config/workflows/tf/README.md
EOF
)"
  fi

  if [ -z "$TF_BASE" ] && [ "$IS_GLOBAL" = false ]; then
    echo "TF_BASE not set; cannot install." >&2
    exit 1
  fi

  local pi_count=0
  local tf_count=0

  route_dest_base() {
    local rel="$1"
    case "$rel" in
      agents/*|skills/*|prompts/*)
        echo "$TARGET_BASE"
        ;;
      *)
        if [ "$IS_GLOBAL" = true ]; then
          echo ""
        else
          echo "$TF_BASE"
        fi
        ;;
    esac
  }

  while IFS= read -r line || [ -n "$line" ]; do
    line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
      continue
    fi
    if [ ! -f "$ROOT_DIR/$line" ]; then
      echo "Missing install file: $ROOT_DIR/$line" >&2
      exit 1
    fi

    local dest_base
    dest_base="$(route_dest_base "$line")"

    if [ -z "$dest_base" ]; then
      continue
    fi

    mkdir -p "$dest_base/$(dirname "$line")"
    cp "$ROOT_DIR/$line" "$dest_base/$line"

    if [ "$dest_base" = "$TARGET_BASE" ]; then
      pi_count=$((pi_count + 1))
    else
      tf_count=$((tf_count + 1))
    fi
  done <<< "$manifest_content"

  echo "Installed Pi workflow files to: $TARGET_BASE"
  if [ "$IS_GLOBAL" = true ]; then
    echo "Installed files: $pi_count (pi assets)"
  else
    echo "Installed TF runtime/config files to: $TF_BASE"
    echo "Installed files: $((pi_count + tf_count)) (pi: $pi_count, tf: $tf_count)"
  fi
}

download_file() {
  local url="$1"
  local output="$2"
  local dir
  dir="$(dirname "$output")"

  mkdir -p "$dir" 2>/dev/null || {
    echo "ERROR: Cannot create directory $dir" >&2
    return 1
  }

  if command -v curl >/dev/null 2>&1; then
    if ! curl -fsSL "$url" -o "$output"; then
      return 1
    fi
  elif command -v wget >/dev/null 2>&1; then
    if ! wget -q "$url" -O "$output"; then
      return 1
    fi
  else
    echo "ERROR: curl or wget required" >&2
    return 1
  fi
}

update_assets() {
  if [ -z "$TARGET_BASE" ]; then
    echo "Target base not set; use --global or --project <path>." >&2
    exit 1
  fi

  local temp_dir
  temp_dir="$(mktemp -d)"

  local manifest_url="$REPO_URL/config/install-manifest.txt"
  local manifest_file="$temp_dir/install-manifest.txt"

  if ! download_file "$manifest_url" "$manifest_file"; then
    echo "Failed to download manifest from $manifest_url" >&2
    rm -rf "$temp_dir"
    exit 1
  fi

  local new_files=()
  local existing_files=()

  while IFS= read -r line || [ -n "$line" ]; do
    line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
      continue
    fi
    case "$line" in
      agents/*|skills/*|prompts/*) ;;
      *) continue ;;
    esac

    local dest="$TARGET_BASE/$line"
    if [ -f "$dest" ]; then
      existing_files+=("$line")
    else
      new_files+=("$line")
    fi
  done < "$manifest_file"

  if [ "${#new_files[@]}" -eq 0 ] && [ "${#existing_files[@]}" -eq 0 ]; then
    echo "No agent/skill/prompt entries found in manifest."
    rm -rf "$temp_dir"
    return 0
  fi

  local downloaded=0
  local updated=0
  local errors=0

  if [ "${#new_files[@]}" -gt 0 ]; then
    echo "New files available:"
    for file in "${new_files[@]}"; do
      echo "  - $file"
    done
    read -r -p "Download ${#new_files[@]} new files into $TARGET_BASE? (Y/n) " yn
    case "$yn" in
      [Nn]*) ;;
      *)
        for file in "${new_files[@]}"; do
          if download_file "$REPO_URL/$file" "$TARGET_BASE/$file"; then
            downloaded=$((downloaded + 1))
          else
            echo "WARNING: Failed to download $file" >&2
            errors=$((errors + 1))
          fi
        done
        ;;
    esac
  else
    echo "No new files to download."
  fi

  if [ "${#existing_files[@]}" -gt 0 ]; then
    read -r -p "Check for updates to existing files? (y/N) " yn
    case "$yn" in
      [Yy]*)
        local update_files=()
        for file in "${existing_files[@]}"; do
          local temp_file="$temp_dir/$file"
          if download_file "$REPO_URL/$file" "$temp_file"; then
            if ! cmp -s "$temp_file" "$TARGET_BASE/$file"; then
              update_files+=("$file")
            fi
          else
            echo "WARNING: Failed to download $file" >&2
            errors=$((errors + 1))
          fi
        done

        if [ "${#update_files[@]}" -gt 0 ]; then
          echo "Updates available:"
          for file in "${update_files[@]}"; do
            echo "  - $file"
          done
          read -r -p "Overwrite ${#update_files[@]} existing files? (y/N) " yn2
          case "$yn2" in
            [Yy]*)
              for file in "${update_files[@]}"; do
                local temp_file="$temp_dir/$file"
                mkdir -p "$TARGET_BASE/$(dirname "$file")"
                if cp "$temp_file" "$TARGET_BASE/$file"; then
                  updated=$((updated + 1))
                else
                  echo "WARNING: Failed to overwrite $file" >&2
                  errors=$((errors + 1))
                fi
              done
              ;;
          esac
        else
          echo "No updates found for existing files."
        fi
        ;;
    esac
  fi

  rm -rf "$temp_dir"

  echo "Update complete."
  echo "  New files downloaded: $downloaded"
  echo "  Existing files updated: $updated"
  if [ "$errors" -gt 0 ]; then
    echo "  Warnings: $errors"
  fi
}

install_extensions() {
  local install_deps="$1"
  local install_optional="$2"
  if ! command -v pi >/dev/null 2>&1; then
    echo "pi not found in PATH; skipping extension installs." >&2
    return 0
  fi
  if [ "$install_deps" = "true" ]; then
    pi install $SCOPE_FLAG npm:pi-subagents
    pi install $SCOPE_FLAG npm:pi-model-switch
    pi install $SCOPE_FLAG npm:pi-prompt-template-model
  fi
  if [ "$install_optional" = "true" ]; then
    pi install $SCOPE_FLAG npm:pi-review-loop
    pi install $SCOPE_FLAG npm:pi-mcp-adapter
    pi install $SCOPE_FLAG npm:pi-web-access
  fi
}

is_uv_project() {
  if [ -f "uv.lock" ]; then
    return 0
  fi
  if [ -f "pyproject.toml" ] && grep -q "^\[tool\.uv\]" pyproject.toml; then
    return 0
  fi
  return 1
}

resolve_python_cmd() {
  PYTHON_CMD=()
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return 0
  fi
  if command -v uv >/dev/null 2>&1 && is_uv_project; then
    PYTHON_CMD=(uv run python)
    return 0
  fi
  return 1
}

set_config_helper() {
  # Don't overwrite if already set (e.g., from ROOT_DIR for dev mode)
  if [ -n "$CONFIG_HELPER" ] && [ -f "$CONFIG_HELPER" ]; then
    return
  fi

  CONFIG_HELPER="$TF_BASE/scripts/tf_config.py"
  CONFIG_HELPER_SUPPORTS_FLAGS=false
  if [ -f "$CONFIG_HELPER" ] && grep -q 'add_argument("--base"' "$CONFIG_HELPER"; then
    CONFIG_HELPER_SUPPORTS_FLAGS=true
  fi
}

require_project_tf() {
  if [ "$IS_GLOBAL" = true ]; then
    echo "This command requires a project-local .tf directory." >&2
    echo "Run 'tf init' in your project or use --project <path>." >&2
    exit 1
  fi

  if [ -z "$TF_BASE" ]; then
    if [ -d ".tf" ]; then
      TF_BASE="$(pwd)/.tf"
      TARGET_BASE="$(pwd)/.pi"
      SCOPE_FLAG="-l"
      IS_GLOBAL=false
    else
      echo "No .tf directory found in $(pwd)." >&2
      echo "Run 'tf init' to scaffold project files." >&2
      exit 1
    fi
  fi

  if [ ! -d "$TF_BASE" ]; then
    echo "Project .tf directory not found: $TF_BASE" >&2
    echo "Run 'tf init' to scaffold project files." >&2
    exit 1
  fi

  RALPH_DIR="$TF_BASE/ralph"

  set_config_helper

  if [ ! -f "$CONFIG_HELPER" ]; then
    echo "Missing tf_config.py at $CONFIG_HELPER" >&2
    echo "Run 'tf init' to scaffold project files." >&2
    exit 1
  fi

  # Update CONFIG_HELPER_SUPPORTS_FLAGS based on the actual file
  CONFIG_HELPER_SUPPORTS_FLAGS=false
  if grep -q 'add_argument("--base"' "$CONFIG_HELPER"; then
    CONFIG_HELPER_SUPPORTS_FLAGS=true
  fi
}

write_default_settings_json() {
  local dest="$1"
  cat <<'JSON' > "$dest"
{
  "metaModels": {
    "planning": {
      "model": "openai-codex/gpt-5.2",
      "thinking": "medium",
      "description": "Fast, capable model for planning and specification"
    },
    "worker": {
      "model": "kimi-coding/k2p5",
      "thinking": "high",
      "description": "Strong model for implementation and complex reasoning"
    },
    "research": {
      "model": "minimax/MiniMax-M2.1",
      "thinking": "medium",
      "description": "Fast model for research and information gathering"
    },
    "fast": {
      "model": "zai/glm-4.7-flash",
      "thinking": "medium",
      "description": "Cheapest model for quick tasks, fixes, and summaries"
    },
    "general": {
      "model": "zai/glm-4.7",
      "thinking": "medium",
      "description": "General-purpose model for admin tasks"
    },
    "review-general": {
      "model": "openai-codex/gpt-5.1-codex-mini",
      "thinking": "high",
      "description": "Capable model for general code review"
    },
    "review-spec": {
      "model": "openai-codex/gpt-5.2-codex",
      "thinking": "high",
      "description": "Strong model for specification compliance audit"
    },
    "review-secop": {
      "model": "github-copilot/grok-code-fast-1",
      "thinking": "high",
      "description": "Fast model for second-opinion review"
    }
  },
  "agents": {
    "reviewer-general": "review-general",
    "reviewer-spec-audit": "review-spec",
    "reviewer-second-opinion": "review-secop",
    "review-merge": "general",
    "fixer": "general",
    "closer": "fast",
    "researcher": "research",
    "researcher-fetch": "research"
  },
  "prompts": {
    "tf": "worker",
    "tf-next": "general",
    "tf-plan": "planning",
    "tf-plan-consult": "planning",
    "tf-plan-revise": "planning",
    "tf-plan-review": "planning",
    "tf-seed": "planning",
    "tf-backlog": "planning",
    "tf-backlog-ls": "fast",
    "tf-spike": "planning",
    "tf-baseline": "planning",
    "tf-followups": "planning",
    "tf-tags-suggest": "planning",
    "tf-deps-sync": "planning",
    "tf-dedup": "planning",
    "tf-backlog-from-openspec": "planning",
    "tf-sync": "general",
    "ralph-start": "general"
  },
  "checkers": {
    "python": {
      "files": "\\.(py|pyi)$",
      "lint": "ruff check {files} --fix",
      "format": "ruff format {files}",
      "typecheck": "mypy ."
    },
    "typescript": {
      "files": "\\.(js|jsx|ts|tsx)$",
      "lint": "eslint {files} --fix",
      "format": "prettier --write {files}",
      "typecheck": "tsc --noEmit"
    },
    "rust": {
      "files": "\\.rs$",
      "lint": "cargo clippy --fix -- -W clippy::all",
      "format": "cargo fmt",
      "typecheck": "cargo check"
    },
    "go": {
      "files": "\\.go$",
      "format": "gofmt -w {files}",
      "typecheck": "go test ./..."
    },
    "markdown": {
      "files": "\\.(md|mdx)$",
      "format": "prettier --write {files}",
      "lint": "markdownlint {files}"
    },
    "json": {
      "files": "\\.json$",
      "format": "prettier --write {files}"
    },
    "yaml": {
      "files": "\\.(yml|yaml)$",
      "format": "prettier --write {files}"
    },
    "html": {
      "files": "\\.html?$",
      "format": "prettier --write {files}"
    },
    "css": {
      "files": "\\.(css|scss|sass|less)$",
      "format": "prettier --write {files}"
    },
    "shell": {
      "files": "\\.(sh|bash|zsh)$",
      "format": "shfmt -w -s {files}"
    }
  },
  "workflow": {
    "clarifyDefault": true,
    "enableResearcher": true,
    "knowledgeDir": ".tf/knowledge",
    "mcpServers": [
      "context7",
      "exa",
      "grep_app",
      "zai-web-search",
      "zai-web-reader",
      "zai-vision"
    ],
    "researchParallelAgents": 3,
    "enableReviewers": [
      "reviewer-general",
      "reviewer-spec-audit",
      "reviewer-second-opinion"
    ],
    "enableFixer": true,
    "enableCloser": true,
    "enableQualityGate": false,
    "failOn": [],
    "exclude": [
      "node_modules/**",
      "dist/**",
      "build/**",
      "coverage/**",
      ".venv/**",
      "vendor/**"
    ]
  }
}
JSON
}

write_default_tf_config_py() {
  local dest="$1"
  cat <<'PY' > "$dest"
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
    sync_base = resolve_sync_base(base)

    # Sync agents
    agents_dir = sync_base / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            try:
                if update_agent_frontmatter(agent_file, config, agent_name):
                    results["agents"].append(agent_name)
            except Exception as e:
                results["errors"].append(f"agents/{agent_file.name}: {e}")

    # Sync prompts
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
PY
}

write_settings_file() {
  local dest="$1"
  if [ -f "$ROOT_DIR/config/settings.json" ]; then
    cp "$ROOT_DIR/config/settings.json" "$dest"
  else
    write_default_settings_json "$dest"
  fi
}

ensure_global_settings() {
  local dest="$HOME/.tf/config/settings.json"
  if [ -f "$dest" ]; then
    ensure_global_scripts
    return 0
  fi

  mkdir -p "$(dirname "$dest")"
  write_settings_file "$dest"
  echo "Created global TF settings at: $dest"
  ensure_global_scripts
}

ensure_global_scripts() {
  local dest="$HOME/.tf/scripts/tf_config.py"
  if [ -f "$dest" ]; then
    return 0
  fi

  mkdir -p "$(dirname "$dest")"
  write_tf_config_file "$dest"
  echo "Created global tf_config.py at: $dest"
}

write_tf_config_file() {
  local dest="$1"
  if [ -f "$ROOT_DIR/scripts/tf_config.py" ]; then
    cp "$ROOT_DIR/scripts/tf_config.py" "$dest"
  else
    write_default_tf_config_py "$dest"
  fi
  chmod +x "$dest"
}

tf_init() {
  if [ "$IS_GLOBAL" = true ]; then
    echo "tf init is project-local; do not use --global." >&2
    exit 1
  fi

  local project_root=""

  if [ -n "$TF_BASE" ]; then
    project_root="$(cd "$(dirname "$TF_BASE")" && pwd)"
  else
    project_root="$(pwd)"
    TF_BASE="$project_root/.tf"
    TARGET_BASE="$project_root/.pi"
    SCOPE_FLAG="-l"
    IS_GLOBAL=false
  fi

  mkdir -p "$TF_BASE/config" "$TF_BASE/scripts" "$TF_BASE/knowledge" "$TF_BASE/ralph"

  if [ ! -f "$TF_BASE/config/settings.json" ]; then
    write_settings_file "$TF_BASE/config/settings.json"
  fi

  if [ ! -f "$TF_BASE/scripts/tf_config.py" ]; then
    write_tf_config_file "$TF_BASE/scripts/tf_config.py"
  fi

  echo "Initialized .tf directory at: $TF_BASE"
}

configure_mcp() {
  local mcp_file="$TARGET_BASE/mcp.json"
  local zai_key="$1"
  local ctx7_key="$2"
  local exa_key="$3"

  mkdir -p "$(dirname "$mcp_file")"

  local python_cmd=()
  if resolve_python_cmd; then
    python_cmd=("${PYTHON_CMD[@]}")
  else
    echo "Python not found; skipping MCP config." >&2
    return 0
  fi

  if [ "$IS_GLOBAL" = true ] || [ -z "$CONFIG_HELPER" ] || [ ! -f "$CONFIG_HELPER" ]; then
    "${python_cmd[@]}" - "$mcp_file" "$zai_key" "$ctx7_key" "$exa_key" <<'PY'
import json
import sys

mcp_file = sys.argv[1]
zai_key = sys.argv[2].strip()
ctx7_key = sys.argv[3].strip()
exa_key = sys.argv[4].strip()

cfg = {
    "settings": {"toolPrefix": "short"},
    "mcpServers": {}
}

def set_server(name, url, headers=None, auth=None):
    srv = {"url": url}
    if auth:
        srv["auth"] = auth
    if headers:
        srv["headers"] = headers
    cfg["mcpServers"][name] = srv

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

with open(mcp_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print(f"Configured MCP servers in {mcp_file}")
PY
    return 0
  fi

  local ignore_project="false"
  if [ "$IS_GLOBAL" = true ]; then
    ignore_project="true"
  fi

  local args=("$CONFIG_HELPER")
  if [ "$CONFIG_HELPER_SUPPORTS_FLAGS" = true ]; then
    args+=(--base "$TARGET_BASE")
    if [ "$ignore_project" = "true" ]; then
      args+=(--ignore-project)
    fi
  fi
  args+=(
    configure-mcp
    --mcp-file "$mcp_file"
    --zai-key "$zai_key"
    --ctx7-key "$ctx7_key"
    --exa-key "$exa_key"
  )

  TARGET_BASE="$TARGET_BASE" IGNORE_PROJECT_CONFIG="$ignore_project" "${python_cmd[@]}" "${args[@]}"
}

track_file() {
  local tracked_path="${1:-}"
  if [ -z "$tracked_path" ]; then
    echo "Usage: tf track <path> [--file <files_changed_path>]" >&2
    exit 1
  fi

  local files_changed="$TRACK_FILE"
  if [ -z "$files_changed" ]; then
    if [ -n "${TF_FILES_CHANGED:-}" ]; then
      files_changed="$TF_FILES_CHANGED"
    elif [ -n "${TF_CHAIN_DIR:-}" ]; then
      files_changed="$TF_CHAIN_DIR/files_changed.txt"
    else
      files_changed="$(pwd)/files_changed.txt"
    fi
  fi

  if [[ "$files_changed" != /* ]]; then
    files_changed="$(pwd)/$files_changed"
  fi

  if [[ "$tracked_path" != /* ]]; then
    tracked_path="$(pwd)/$tracked_path"
  fi

  mkdir -p "$(dirname "$files_changed")"
  touch "$files_changed"

  if ! grep -Fxq "$tracked_path" "$files_changed"; then
    echo "$tracked_path" >> "$files_changed"
  fi

  echo "Tracked: $tracked_path"
}

doctor() {
  require_project_tf

  local failed=0

  echo "Ticketflow doctor"

  check_cmd() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
      echo "[ok] $name"
    else
      echo "[missing] $name"
      failed=1
    fi
  }

  local PI_LIST_CACHE=""
  get_pi_list() {
    if [ -n "$PI_LIST_CACHE" ]; then
      printf '%s' "$PI_LIST_CACHE"
      return 0
    fi
    if ! command -v pi >/dev/null 2>&1; then
      return 1
    fi
    # `pi list` can be a bit slow; cache the result.
    PI_LIST_CACHE="$(pi list 2>/dev/null || true)"
    printf '%s' "$PI_LIST_CACHE"
  }

  check_extension() {
    local name="$1"

    # Legacy extension install locations (older Pi versions / local installs)
    local global_path="$HOME/.pi/agent/extensions/$name"
    local project_path=""
    if [[ "$TARGET_BASE" == */.pi ]]; then
      project_path="$TARGET_BASE/extensions/$name"
    fi

    if [ -d "$global_path" ] || { [ -n "$project_path" ] && [ -d "$project_path" ]; }; then
      if [ -n "$project_path" ] && [ -d "$project_path" ]; then
        echo "[ok] extension $name (project)"
      else
        echo "[ok] extension $name (global)"
      fi
      return 0
    fi

    # Current preferred install location: Pi user packages (visible via `pi list`)
    local list_out
    list_out="$(get_pi_list || true)"
    if [ -n "$list_out" ] && echo "$list_out" | grep -q "npm:$name"; then
      echo "[ok] extension $name (pi user package)"
      return 0
    fi

    echo "[missing] extension $name"
    failed=1
  }

  check_extension_optional() {
    local name="$1"

    local global_path="$HOME/.pi/agent/extensions/$name"
    local project_path=""
    if [[ "$TARGET_BASE" == */.pi ]]; then
      project_path="$TARGET_BASE/extensions/$name"
    fi

    if [ -d "$global_path" ] || { [ -n "$project_path" ] && [ -d "$project_path" ]; }; then
      if [ -n "$project_path" ] && [ -d "$project_path" ]; then
        echo "[ok] extension $name (project, optional)"
      else
        echo "[ok] extension $name (global, optional)"
      fi
      return 0
    fi

    local list_out
    list_out="$(get_pi_list || true)"
    if [ -n "$list_out" ] && echo "$list_out" | grep -q "npm:$name"; then
      echo "[ok] extension $name (pi user package, optional)"
      return 0
    fi

    echo "[info] extension $name (optional, not installed)"
  }

  check_cmd "tk"
  check_cmd "pi"

  check_extension "pi-subagents"
  check_extension "pi-model-switch"
  check_extension "pi-prompt-template-model"

  # Optional but recommended (research + post-chain review)
  check_extension_optional "pi-mcp-adapter"
  check_extension_optional "pi-review-loop"
  check_extension_optional "pi-web-access"

  local python_cmd=()
  if resolve_python_cmd; then
    python_cmd=("${PYTHON_CMD[@]}")
    local ignore_project="false"
    if [ "$IS_GLOBAL" = true ]; then
      ignore_project="true"
    fi

    local cmds
    local args=("$CONFIG_HELPER")
    if [ "$CONFIG_HELPER_SUPPORTS_FLAGS" = true ]; then
      args+=(--base "$TARGET_BASE")
      if [ "$ignore_project" = "true" ]; then
        args+=(--ignore-project)
      fi
    fi
    args+=(checker-tools)
    cmds=$(TARGET_BASE="$TARGET_BASE" IGNORE_PROJECT_CONFIG="$ignore_project" "${python_cmd[@]}" "${args[@]}")

    if [ -n "$cmds" ]; then
      echo "Checker tools:"
      while IFS= read -r cmd; do
        [ -z "$cmd" ] && continue
        check_cmd "$cmd"
      done <<< "$cmds"
    else
      echo "[info] No checkers configured"
    fi

    # MCP configuration (optional; only required for MCP-backed research)
    local mcp_file="$TARGET_BASE/mcp.json"
    local mcp_servers=""
    local mcp_args=("$CONFIG_HELPER")
    if [ "$CONFIG_HELPER_SUPPORTS_FLAGS" = true ]; then
      mcp_args+=(--base "$TARGET_BASE")
      if [ "$ignore_project" = "true" ]; then
        mcp_args+=(--ignore-project)
      fi
    fi
    mcp_args+=(mcp-servers)
    mcp_servers=$(TARGET_BASE="$TARGET_BASE" IGNORE_PROJECT_CONFIG="$ignore_project" "${python_cmd[@]}" "${mcp_args[@]}" 2>/dev/null || true)

    if [ -n "$mcp_servers" ]; then
      if [ -f "$mcp_file" ]; then
        local expected_csv
        expected_csv="$(echo "$mcp_servers" | tr '\n' ',' | sed 's/,$//')"
        local missing
        missing=$("${python_cmd[@]}" -c 'import json,sys
p=sys.argv[1]
expected=[s for s in sys.argv[2].split(",") if s]
try:
  cfg=json.load(open(p, "r", encoding="utf-8"))
except Exception:
  cfg={}
servers=set((cfg.get("mcpServers") or {}).keys())
missing=[s for s in expected if s not in servers]
print("\n".join(missing))
' "$mcp_file" "$expected_csv" 2>/dev/null || true)

        if [ -z "$missing" ]; then
          echo "[ok] mcp.json ($mcp_file)"
        else
          echo "[warn] mcp.json ($mcp_file) missing servers: $(echo "$missing" | tr '\n' ' ')"
        fi
      else
        echo "[info] mcp.json not found at $mcp_file (MCP research optional; run 'tf setup' to generate)"
      fi
    fi
  else
    echo "[missing] python (required to read checkers config)"
    failed=1
  fi

  if [ "$failed" -ne 0 ]; then
    echo "Ticketflow doctor: failed"
    exit 1
  fi

  echo "Ticketflow doctor: OK"
}

# =============================================================================
# Ralph Loop Management
# =============================================================================

RALPH_DIR=".tf/ralph"

ralph_usage() {
  cat <<'EOF'
Ralph Loop Management

Usage:
  tf ralph init         Create .tf/ralph/ directory structure
  tf ralph status       Show current loop state and statistics
  tf ralph reset        Clear progress (use --keep-lessons to preserve lessons)
  tf ralph lessons      Show lessons learned
  tf ralph lessons prune [N]  Keep only last N lessons (default: 20)
  tf ralph start [--max-iterations N] [--parallel N] [--no-parallel] [--dry-run] [--flags '...']  Run loop via pi -c (uses /tf)
  tf ralph run [ticket-id] [--dry-run] [--flags '...']                               Run a single ticket via pi -c (uses /tf)

The Ralph loop can be started via Pi prompt or CLI:
  /ralph-start [--max-iterations N]
  tf ralph start [--max-iterations N] [--parallel N]
  tf ralph start --max-iterations N --flags "--create-followups --final-review-loop"

Files:
  .tf/ralph/AGENTS.md    Lessons learned (read by main workflow agent)
  .tf/ralph/progress.md  Loop state and ticket history
  .tf/ralph/config.json  Loop configuration
EOF
}

ralph_init() {
  echo "Initializing Ralph loop directory..."
  
  mkdir -p "$RALPH_DIR"
  
  # Create AGENTS.md if not exists
  if [ ! -f "$RALPH_DIR/AGENTS.md" ]; then
    cat > "$RALPH_DIR/AGENTS.md" <<'AGENTS_EOF'
# Ralph Loop: Lessons Learned

This file contains lessons learned during autonomous ticket processing.
It is read by the main workflow agent at the start of each iteration for re-anchoring.

## How This Works

When running in a Ralph loop, the agent reads this file to:
- Apply discovered patterns and conventions
- Avoid known gotchas and pitfalls
- Reuse successful strategies

## Project Patterns

<!-- Discovered patterns and conventions go here -->

## Gotchas

<!-- Things that caused issues and how to avoid them -->

## Successful Strategies

<!-- Approaches that worked well -->

## Technical Debt Notes

<!-- Known issues to address later -->

---

<!-- Lessons are auto-appended below by the closer agent -->
AGENTS_EOF
    echo "Created $RALPH_DIR/AGENTS.md"
  else
    echo "Exists: $RALPH_DIR/AGENTS.md"
  fi
  
  # Create progress.md if not exists
  if [ ! -f "$RALPH_DIR/progress.md" ]; then
    cat > "$RALPH_DIR/progress.md" <<'PROGRESS_EOF'
# Ralph Loop Progress

## Current State

- Status: IDLE
- Current ticket: (none)
- Started: (not started)
- Last updated: (never)

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
PROGRESS_EOF
    echo "Created $RALPH_DIR/progress.md"
  else
    echo "Exists: $RALPH_DIR/progress.md"
  fi
  
  # Create config.json if not exists
  if [ ! -f "$RALPH_DIR/config.json" ]; then
    cat > "$RALPH_DIR/config.json" <<'CONFIG_EOF'
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
  "completionCheck": "tk ready | grep -q .",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "workflow": "/tf",
  "workflowFlags": "--auto",
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "promiseOnComplete": true,
  "lessonsMaxCount": 50,
  "parallelWorkers": 1,
  "parallelWorktreesDir": ".tf/ralph/worktrees",
  "parallelAllowUntagged": false,
  "componentTagPrefix": "component:",
  "parallelKeepWorktrees": false,
  "parallelAutoMerge": true
}
CONFIG_EOF
    echo "Created $RALPH_DIR/config.json"
  else
    echo "Exists: $RALPH_DIR/config.json"
  fi
  
  echo ""
  echo "Ralph loop initialized in $RALPH_DIR/"
  echo ""
  echo "Next steps:"
  echo "  1. Review $RALPH_DIR/config.json"
  echo "  2. Add initial patterns to $RALPH_DIR/AGENTS.md"
  echo "  3. Start the loop with: /ralph-start"
}

ralph_status() {
  if [ ! -d "$RALPH_DIR" ]; then
    echo "Ralph not initialized. Run: tf ralph init"
    exit 1
  fi
  
  echo "=== Ralph Loop Status ==="
  echo ""
  
  # Read progress.md for status
  if [ -f "$RALPH_DIR/progress.md" ]; then
    # Extract current state section
    sed -n '/^## Current State/,/^## /p' "$RALPH_DIR/progress.md" | sed '$d'
    echo ""
    
    # Extract statistics section
    sed -n '/^## Statistics/,/^## /p' "$RALPH_DIR/progress.md" | sed '$d'
  else
    echo "Status: NOT INITIALIZED"
  fi
  
  echo ""
  echo "=== Ticket Queue ==="
  if command -v tk >/dev/null 2>&1; then
    local ready_count
    ready_count=$(tk ready 2>/dev/null | wc -l | tr -d ' ')
    echo "Ready tickets: $ready_count"
    if [ "$ready_count" -gt 0 ]; then
      echo ""
      tk ready 2>/dev/null | head -5 || echo "(unable to list tickets)"
    fi
  else
    echo "(tk not available)"
  fi
  
  echo ""
  echo "=== Lessons Learned ==="
  if [ -f "$RALPH_DIR/AGENTS.md" ]; then
    local lesson_count
    lesson_count=$(grep -c "^## Lesson from" "$RALPH_DIR/AGENTS.md" 2>/dev/null) || lesson_count=0
    echo "Total lessons: $lesson_count"
  else
    echo "No lessons file"
  fi
}

ralph_reset() {
  if [ ! -d "$RALPH_DIR" ]; then
    echo "Ralph not initialized. Run: tf ralph init"
    exit 1
  fi
  
  local keep_lessons=false
  for arg in "$@"; do
    case "$arg" in
      --keep-lessons) keep_lessons=true ;;
    esac
  done
  
  echo "Resetting Ralph loop progress..."
  
  # Reset progress.md
  cat > "$RALPH_DIR/progress.md" <<'PROGRESS_EOF'
# Ralph Loop Progress

## Current State

- Status: IDLE
- Current ticket: (none)
- Started: (not started)
- Last updated: (never)

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
PROGRESS_EOF
  echo "Reset: $RALPH_DIR/progress.md"
  
  if [ "$keep_lessons" = false ]; then
    # Reset AGENTS.md but keep structure
    cat > "$RALPH_DIR/AGENTS.md" <<'AGENTS_EOF'
# Ralph Loop: Lessons Learned

This file contains lessons learned during autonomous ticket processing.
It is read by the main workflow agent at the start of each iteration for re-anchoring.

## How This Works

When running in a Ralph loop, the agent reads this file to:
- Apply discovered patterns and conventions
- Avoid known gotchas and pitfalls
- Reuse successful strategies

## Project Patterns

<!-- Discovered patterns and conventions go here -->

## Gotchas

<!-- Things that caused issues and how to avoid them -->

## Successful Strategies

<!-- Approaches that worked well -->

## Technical Debt Notes

<!-- Known issues to address later -->

---

<!-- Lessons are auto-appended below by the closer agent -->
AGENTS_EOF
    echo "Reset: $RALPH_DIR/AGENTS.md"
  else
    echo "Kept: $RALPH_DIR/AGENTS.md (--keep-lessons)"
  fi
  
  echo ""
  echo "Ralph loop reset complete."
}

ralph_lessons() {
  if [ ! -d "$RALPH_DIR" ]; then
    echo "Ralph not initialized. Run: tf ralph init"
    exit 1
  fi
  
  local subcmd="${1:-show}"
  shift || true
  
  case "$subcmd" in
    show)
      if [ -f "$RALPH_DIR/AGENTS.md" ]; then
        cat "$RALPH_DIR/AGENTS.md"
      else
        echo "No lessons file found."
      fi
      ;;
    prune)
      local keep_count="${1:-20}"
      if [ ! -f "$RALPH_DIR/AGENTS.md" ]; then
        echo "No lessons file found."
        exit 1
      fi
      
      echo "Pruning lessons to keep last $keep_count..."
      
      # Use Python for reliable parsing
      local python_bin=""
      if command -v python3 >/dev/null 2>&1; then
        python_bin="python3"
      elif command -v python >/dev/null 2>&1; then
        python_bin="python"
      else
        echo "Python required for pruning." >&2
        exit 1
      fi
      
      RALPH_DIR="$RALPH_DIR" KEEP_COUNT="$keep_count" "$python_bin" - <<'PY'
import os
import re
from pathlib import Path

ralph_dir = Path(os.environ["RALPH_DIR"])
keep_count = int(os.environ.get("KEEP_COUNT", "20"))
agents_file = ralph_dir / "AGENTS.md"

content = agents_file.read_text(encoding="utf-8")

# Split at the separator line
parts = content.split("\n---\n", 1)
if len(parts) < 2:
    print("No lessons section found (no --- separator)")
    raise SystemExit(0)

header = parts[0]
lessons_section = parts[1]

# Find all lessons (start with "## Lesson from")
lesson_pattern = r"(## Lesson from .+?)(?=## Lesson from |\Z)"
lessons = re.findall(lesson_pattern, lessons_section, re.DOTALL)

total = len(lessons)
if total <= keep_count:
    print(f"Only {total} lessons found, keeping all.")
    raise SystemExit(0)

# Keep last N lessons
kept_lessons = lessons[-keep_count:]
removed = total - keep_count

new_content = header + "\n---\n\n" + "\n".join(kept_lessons)
agents_file.write_text(new_content, encoding="utf-8")

print(f"Pruned {removed} lessons, kept {keep_count}.")
PY
      ;;
    *)
      echo "Unknown lessons subcommand: $subcmd"
      echo "Usage: tf ralph lessons [show|prune [N]]"
      exit 1
      ;;
  esac
}

ralph_sleep_ms() {
  local local_ms="${1:-0}"
  if [ -z "$local_ms" ] || [ "$local_ms" -le 0 ] 2>/dev/null; then
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$local_ms" <<'PY' | xargs sleep
import sys
ms = int(sys.argv[1])
print(ms / 1000)
PY
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    python - "$local_ms" <<'PY' | xargs sleep
import sys
ms = int(sys.argv[1])
print(ms / 1000)
PY
    return 0
  fi
  sleep "$(awk "BEGIN {print $local_ms/1000}")"
}

ralph_config_value() {
  local key="$1"
  local default="$2"
  local config_path="$RALPH_DIR/config.json"

  if [ ! -f "$config_path" ]; then
    echo "$default"
    return 0
  fi

  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi

  if [ -z "$py" ]; then
    echo "$default"
    return 0
  fi

  "$py" - "$config_path" "$key" "$default" <<'PY'
import json
import sys

path = sys.argv[1]
key = sys.argv[2]
default = sys.argv[3]

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    print(default)
    raise SystemExit(0)

val = data.get(key, None)
if val is None:
    print(default)
elif isinstance(val, bool):
    print("true" if val else "false")
elif isinstance(val, (int, float)):
    print(val)
else:
    print(val)
PY
}

ralph_prompt_exists() {
  if [ -f ".pi/prompts/tf.md" ] || [ -f "$HOME/.pi/agent/prompts/tf.md" ]; then
    return 0
  fi
  echo "Missing /tf prompt. Install via: tf setup --project <path> or tf setup --global" >&2
  return 1
}

ralph_sanitize_ticket_query() {
  local query="$1"
  if echo "$query" | grep -Eq '(^|[[:space:]])tf[[:space:]]+next([[:space:]]|$)'; then
    echo "[warn] ticketQuery uses 'tf next' (recursive). Using default tk-ready query." >&2
    echo "tk ready | head -1 | awk '{print \$1}'"
    return 0
  fi
  echo "$query"
}

ralph_ticket_list_query() {
  local query="$1"
  if echo "$query" | grep -q "tk ready"; then
    local simplified
    simplified=$(echo "$query" | sed -E 's/\|[[:space:]]*head -1//g; s/\|[[:space:]]*awk .*$//g')
    echo "$simplified"
    return 0
  fi
  echo "tk ready"
}

ralph_select_parallel_tickets() {
  local max="$1"
  local allow_untagged="$2"
  local tag_prefix="$3"
  local list_query="$4"

  local ready
  ready=$(eval "$list_query" 2>/dev/null | awk '{print $1}')
  if [ -z "$ready" ]; then
    return 0
  fi

  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi

  if [ -z "$py" ]; then
    echo "$ready" | head -1
    return 0
  fi

  RALPH_READY_LIST="$ready" \
  RALPH_MAX_PARALLEL="$max" \
  RALPH_ALLOW_UNTAGGED="$allow_untagged" \
  RALPH_TAG_PREFIX="$tag_prefix" \
  "$py" - <<'PY'
import os
import re
import subprocess

ready = [line.strip() for line in os.environ.get("RALPH_READY_LIST", "").splitlines() if line.strip()]
max_parallel = int(os.environ.get("RALPH_MAX_PARALLEL", "1"))
allow_untagged = os.environ.get("RALPH_ALLOW_UNTAGGED", "false").lower() == "true"
tag_prefix = os.environ.get("RALPH_TAG_PREFIX", "component:")


def extract_components(ticket_id: str):
    try:
        proc = subprocess.run(["tk", "show", ticket_id], capture_output=True, text=True, check=False)
    except Exception:
        return None
    text = proc.stdout
    in_front = False
    tags = []
    for line in text.splitlines():
        if line.strip() == "---":
            in_front = not in_front
            continue
        if in_front and line.startswith("tags:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            tags = [t.strip() for t in value.split(",") if t.strip()]
            break
    components = [t for t in tags if t.startswith(tag_prefix)]
    if not components:
        if not allow_untagged:
            return None
        return {"__untagged__"}
    return set(components)


selected = []
used = set()
for ticket in ready:
    comps = extract_components(ticket)
    if comps is None:
        continue
    if comps & used:
        continue
    selected.append(ticket)
    used.update(comps)
    if len(selected) >= max_parallel:
        break

print("\n".join(selected))
PY
}

ralph_lock_acquire() {
  local lock_path="$RALPH_DIR/lock"
  if [ -f "$lock_path" ]; then
    local pid
    pid=$(head -1 "$lock_path" | awk '{print $1}')
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "Ralph loop already running (pid $pid). Remove $lock_path if stale." >&2
      return 1
    fi
  fi
  echo "$$ $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$lock_path"
  return 0
}

ralph_lock_release() {
  local lock_path="$RALPH_DIR/lock"
  if [ -f "$lock_path" ]; then
    rm -f "$lock_path"
  fi
}

ralph_knowledge_dir() {
  local settings_path="$TF_BASE/config/settings.json"
  if [ ! -f "$settings_path" ]; then
    echo ".tf/knowledge"
    return 0
  fi

  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi

  if [ -z "$py" ]; then
    echo ".tf/knowledge"
    return 0
  fi

  "$py" - "$settings_path" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    print(".tf/knowledge")
    raise SystemExit(0)

workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
print(workflow.get("knowledgeDir", ".tf/knowledge"))
PY
}

ralph_set_state() {
  local state="$1"
  local progress_path="$RALPH_DIR/progress.md"
  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  if [ ! -f "$progress_path" ]; then
    return 0
  fi

  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi

  if [ -z "$py" ]; then
    return 0
  fi

  "$py" - "$progress_path" "$state" "$now" <<'PY'
import re
import sys

path = sys.argv[1]
state = sys.argv[2]
now = sys.argv[3]

text = ""
try:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
except Exception:
    raise SystemExit(0)

if "## Current State" not in text:
    raise SystemExit(0)

lines = text.splitlines()
out = []
for line in lines:
    if line.startswith("- Status:"):
        out.append(f"- Status: {state}")
        continue
    if line.startswith("- Current ticket:"):
        out.append("- Current ticket: (none)")
        continue
    if line.startswith("- Started:"):
        if "(not started)" in line:
            out.append(f"- Started: {now}")
        else:
            out.append(line)
        continue
    if line.startswith("- Last updated:"):
        out.append(f"- Last updated: {now}")
        continue
    out.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
PY
}

ralph_update_state() {
  local ticket="$1"
  local status="$2"
  local error_msg="$3"
  local artifact_root="${4:-}"

  local progress_path="$RALPH_DIR/progress.md"
  local agents_path="$RALPH_DIR/AGENTS.md"
  local knowledge_dir
  if [ -n "$artifact_root" ]; then
    knowledge_dir="$artifact_root"
  else
    knowledge_dir=$(ralph_knowledge_dir)
  fi

  local artifact_dir="$knowledge_dir/tickets/$ticket"
  local close_summary="$artifact_dir/close-summary.md"
  local review_path="$artifact_dir/review.md"

  local fallback_summary="$ticket"
  if command -v tk >/dev/null 2>&1; then
    local title
    title=$(tk show "$ticket" 2>/dev/null | awk 'BEGIN{infront=0} /^---$/{infront=!infront; next} !infront && /^# /{print substr($0,3); exit}')
    if [ -n "$title" ]; then
      fallback_summary="$title"
    fi
  fi

  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py="python3"
  elif command -v python >/dev/null 2>&1; then
    py="python"
  fi

  if [ -z "$py" ]; then
    return 0
  fi

  "$py" - "$progress_path" "$agents_path" "$ticket" "$status" "$now" "$fallback_summary" "$error_msg" "$close_summary" "$review_path" <<'PY'
import re
import sys
from pathlib import Path

progress_path = Path(sys.argv[1])
agents_path = Path(sys.argv[2])
ticket = sys.argv[3]
status = sys.argv[4]
now = sys.argv[5]
fallback_summary = sys.argv[6]
error_msg = sys.argv[7]
close_summary = Path(sys.argv[8])
review_path = Path(sys.argv[9])

summary = fallback_summary
commit = ""

if close_summary.exists():
    text = close_summary.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = re.match(r"\s*[-*]?\s*Summary\s*:\s*(.+)$", line)
        if m:
            summary = m.group(1).strip()
            break
    for line in text.splitlines():
        m = re.match(r"\s*[-*]?\s*Commit\s*:\s*(.+)$", line)
        if m:
            commit = m.group(1).strip()
            break

crit = maj = minor = 0
if review_path.exists():
    for line in review_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*[-*]?\s*Critical\s*:\s*(\d+)", line, re.IGNORECASE)
        if m:
            crit = int(m.group(1))
        m = re.match(r"\s*[-*]?\s*Major\s*:\s*(\d+)", line, re.IGNORECASE)
        if m:
            maj = int(m.group(1))
        m = re.match(r"\s*[-*]?\s*Minor\s*:\s*(\d+)", line, re.IGNORECASE)
        if m:
            minor = int(m.group(1))

# Extract lessons if present
lesson_block = ""
if close_summary.exists():
    lines = close_summary.read_text(encoding="utf-8").splitlines()
    in_lessons = False
    buffer = []
    for line in lines:
        if re.match(r"^#{2,3}\s+Lessons Learned", line):
            in_lessons = True
            continue
        if in_lessons and re.match(r"^#{2,3}\s+", line):
            break
        if in_lessons:
            buffer.append(line)
    lesson_block = "\n".join([l.rstrip() for l in buffer]).strip()

# Update progress
if progress_path.exists():
    text = progress_path.read_text(encoding="utf-8")
else:
    text = "# Ralph Loop Progress\n\n## Current State\n\n- Status: RUNNING\n- Current ticket: (none)\n- Started: {}\n- Last updated: {}\n\n## Statistics\n\n- Tickets completed: 0\n- Tickets failed: 0\n- Total iterations: 0\n\n## History\n\n<!-- Auto-appended entries below -->\n".format(now, now)

lines = text.splitlines()
completed = failed = total = 0
for line in lines:
    m = re.match(r"- Tickets completed: (\d+)", line)
    if m:
        completed = int(m.group(1))
    m = re.match(r"- Tickets failed: (\d+)", line)
    if m:
        failed = int(m.group(1))
    m = re.match(r"- Total iterations: (\d+)", line)
    if m:
        total = int(m.group(1))

if status == "FAILED":
    failed += 1
else:
    completed += 1

total += 1

out = []
for line in lines:
    if line.startswith("- Status:"):
        out.append("- Status: RUNNING")
        continue
    if line.startswith("- Current ticket:"):
        out.append("- Current ticket: (none)")
        continue
    if line.startswith("- Started:"):
        if "(not started)" in line:
            out.append(f"- Started: {now}")
        else:
            out.append(line)
        continue
    if line.startswith("- Last updated:"):
        out.append(f"- Last updated: {now}")
        continue
    if line.startswith("- Tickets completed:"):
        out.append(f"- Tickets completed: {completed}")
        continue
    if line.startswith("- Tickets failed:"):
        out.append(f"- Tickets failed: {failed}")
        continue
    if line.startswith("- Total iterations:"):
        out.append(f"- Total iterations: {total}")
        continue
    out.append(line)

entry_lines = [
    f"- {ticket}: {status} ({now})",
    f"  - Summary: {summary}",
    f"  - Issues: Critical({crit})/Major({maj})/Minor({minor})",
    f"  - Status: {status}",
]
if commit:
    entry_lines.append(f"  - Commit: {commit}")
if error_msg:
    entry_lines.append(f"  - Error: {error_msg}")

entry = "\n".join(entry_lines)
marker = "<!-- Auto-appended entries below -->"
if marker in out:
    idx = out.index(marker)
    out = out[:idx+1] + [entry] + out[idx+1:]
else:
    out.append(entry)

progress_path.write_text("\n".join(out) + "\n", encoding="utf-8")

# Append lessons if present
if lesson_block and agents_path.exists():
    header = f"\n## Lesson from {ticket} ({now})\n\n"
    agents_path.write_text(agents_path.read_text(encoding="utf-8") + header + lesson_block + "\n", encoding="utf-8")
PY
}

ralph_run_ticket() {
  local ticket="$1"
  local workflow="$2"
  local flags="$3"
  local dry_run="$4"

  if [ -z "$ticket" ]; then
    echo "No ticket specified." >&2
    return 1
  fi

  if ! command -v pi >/dev/null 2>&1; then
    echo "pi not found in PATH; cannot run workflow." >&2
    return 1
  fi

  if ! ralph_prompt_exists; then
    return 1
  fi

  local cmd="$workflow $ticket"
  if [ -n "$flags" ]; then
    cmd="$cmd $flags"
  fi

  if [ "$dry_run" = "true" ]; then
    echo "Dry run: pi -c \"$cmd\""
    return 0
  fi

  echo "Running: pi -c \"$cmd\""
  pi -c "$cmd"
}

ralph_run() {
  local ticket_override=""
  local dry_run="false"
  local flags_override=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --dry-run)
        dry_run="true"
        shift
        ;;
      --flags)
        flags_override="$2"
        shift 2
        ;;
      --flags=*)
        flags_override="${1#--flags=}"
        shift
        ;;
      --help|-h)
        echo "Usage: tf ralph run [ticket-id] [--dry-run] [--flags '...']" >&2
        return 1
        ;;
      *)
        if [ -z "$ticket_override" ]; then
          ticket_override="$1"
          shift
        else
          echo "Too many arguments for ralph run" >&2
          return 1
        fi
        ;;
    esac
  done

  local ticket_query
  ticket_query=$(ralph_sanitize_ticket_query "$(ralph_config_value "ticketQuery" "tk ready | head -1 | awk '{print \$1}'")")

  local workflow
  workflow=$(ralph_config_value "workflow" "/tf")

  local workflow_flags
  workflow_flags=$(ralph_config_value "workflowFlags" "--auto")
  if [ -n "$flags_override" ]; then
    workflow_flags="$workflow_flags $flags_override"
  fi

  local ticket="$ticket_override"
  if [ -z "$ticket" ]; then
    ticket=$(eval "$ticket_query" 2>/dev/null | head -1 | awk '{print $1}')
  fi

  if [ -z "$ticket" ]; then
    echo "No ready tickets found." >&2
    return 1
  fi

  ralph_run_ticket "$ticket" "$workflow" "$workflow_flags" "$dry_run"
  local rc=$?
  if [ "$dry_run" = "true" ]; then
    return $rc
  fi
  if [ $rc -ne 0 ]; then
    ralph_update_state "$ticket" "FAILED" "pi -c failed (exit $rc)"
    return $rc
  fi
  ralph_update_state "$ticket" "COMPLETE" ""
}

ralph_start() {
  local max_override=""
  local dry_run="false"
  local parallel_override=""
  local no_parallel="false"
  local flags_override=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --max-iterations)
        max_override="$2"
        shift 2
        ;;
      --max-iterations=*)
        max_override="${1#--max-iterations=}"
        shift
        ;;
      --parallel)
        parallel_override="$2"
        shift 2
        ;;
      --parallel=*)
        parallel_override="${1#--parallel=}"
        shift
        ;;
      --no-parallel)
        no_parallel="true"
        shift
        ;;
      --dry-run)
        dry_run="true"
        shift
        ;;
      --flags)
        flags_override="$2"
        shift 2
        ;;
      --flags=*)
        flags_override="${1#--flags=}"
        shift
        ;;
      --help|-h)
        echo "Usage: tf ralph start [--max-iterations N] [--parallel N] [--no-parallel] [--dry-run] [--flags '...']" >&2
        return 1
        ;;
      *)
        echo "Unknown option for ralph start: $1" >&2
        return 1
        ;;
    esac
  done

  local max_iterations
  max_iterations=$(ralph_config_value "maxIterations" "50")
  if [ -n "$max_override" ]; then
    max_iterations="$max_override"
  fi

  local ticket_query
  ticket_query=$(ralph_sanitize_ticket_query "$(ralph_config_value "ticketQuery" "tk ready | head -1 | awk '{print \$1}'")")

  local completion_check
  completion_check=$(ralph_config_value "completionCheck" "tk ready | grep -q .")

  local sleep_between
  sleep_between=$(ralph_config_value "sleepBetweenTickets" "5000")

  local sleep_retries
  sleep_retries=$(ralph_config_value "sleepBetweenRetries" "10000")

  local workflow
  workflow=$(ralph_config_value "workflow" "/tf")

  local workflow_flags
  workflow_flags=$(ralph_config_value "workflowFlags" "--auto")
  if [ -n "$flags_override" ]; then
    workflow_flags="$workflow_flags $flags_override"
  fi

  local promise_on_complete
  promise_on_complete=$(ralph_config_value "promiseOnComplete" "true")

  local parallel_workers
  parallel_workers=$(ralph_config_value "parallelWorkers" "1")
  if [ -n "$parallel_override" ]; then
    parallel_workers="$parallel_override"
  fi
  if [ "$no_parallel" = "true" ]; then
    parallel_workers="1"
  fi

  local use_parallel="$parallel_workers"
  local repo_root=""
  if [ "$use_parallel" -gt 1 ]; then
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [ -z "$repo_root" ]; then
      echo "[warn] git repo not found; falling back to serial." >&2
      use_parallel="1"
    fi
  fi

  if [ "$dry_run" != "true" ]; then
    if ! ralph_lock_acquire; then
      return 1
    fi
    trap 'ralph_lock_release' EXIT
    ralph_set_state "RUNNING"
  fi

  local iteration=0

  if [ "$use_parallel" -le 1 ]; then
    while [ "$iteration" -lt "$max_iterations" ]; do
      if ! eval "$completion_check" >/dev/null 2>&1; then
        echo "No ready tickets. Ralph loop complete."
        if [ "$dry_run" != "true" ]; then
          ralph_set_state "COMPLETE"
        fi
        if [ "$promise_on_complete" = "true" ]; then
          echo "<promise>COMPLETE</promise>"
        fi
        return 0
      fi

      local ticket
      ticket=$(eval "$ticket_query" 2>/dev/null | head -1 | awk '{print $1}')

      if [ -z "$ticket" ]; then
        ralph_sleep_ms "$sleep_retries"
        continue
      fi

      ralph_run_ticket "$ticket" "$workflow" "$workflow_flags" "$dry_run"
      local rc=$?
      if [ "$dry_run" != "true" ]; then
        if [ $rc -ne 0 ]; then
          ralph_update_state "$ticket" "FAILED" "pi -c failed (exit $rc)"
          return $rc
        fi
        ralph_update_state "$ticket" "COMPLETE" ""
      fi

      iteration=$((iteration + 1))
      ralph_sleep_ms "$sleep_between"
    done

    echo "Max iterations reached ($max_iterations)."
    if [ "$dry_run" != "true" ]; then
      ralph_set_state "COMPLETE"
    fi
    if [ "$promise_on_complete" = "true" ]; then
      echo "<promise>COMPLETE</promise>"
    fi
    return 0
  fi

  local worktrees_dir
  worktrees_dir=$(ralph_config_value "parallelWorktreesDir" ".tf/ralph/worktrees")
  if [[ "$worktrees_dir" != /* ]]; then
    worktrees_dir="$repo_root/$worktrees_dir"
  fi

  local allow_untagged
  allow_untagged=$(ralph_config_value "parallelAllowUntagged" "false")

  local tag_prefix
  tag_prefix=$(ralph_config_value "componentTagPrefix" "component:")

  local keep_worktrees
  keep_worktrees=$(ralph_config_value "parallelKeepWorktrees" "false")

  mkdir -p "$worktrees_dir"

  local list_query
  list_query=$(ralph_ticket_list_query "$ticket_query")

  while [ "$iteration" -lt "$max_iterations" ]; do
    if ! eval "$completion_check" >/dev/null 2>&1; then
      echo "No ready tickets. Ralph loop complete."
      if [ "$dry_run" != "true" ]; then
        ralph_set_state "COMPLETE"
      fi
      if [ "$promise_on_complete" = "true" ]; then
        echo "<promise>COMPLETE</promise>"
      fi
      return 0
    fi

    local remaining
    remaining=$((max_iterations - iteration))

    local batch_size="$use_parallel"
    if [ "$remaining" -lt "$batch_size" ]; then
      batch_size="$remaining"
    fi

    local selected
    selected=$(ralph_select_parallel_tickets "$batch_size" "$allow_untagged" "$tag_prefix" "$list_query")

    if [ -z "$selected" ]; then
      local fallback_ticket
      fallback_ticket=$(eval "$ticket_query" 2>/dev/null | head -1 | awk '{print $1}')
      if [ -z "$fallback_ticket" ]; then
        ralph_sleep_ms "$sleep_retries"
        continue
      fi
      selected="$fallback_ticket"
    fi

    if [ "$dry_run" = "true" ]; then
      for ticket in $selected; do
        echo "Dry run: pi -c \"$workflow $ticket $workflow_flags\" (worktree)"
      done
      iteration=$((iteration + $(echo "$selected" | wc -l | tr -d ' ')))
      ralph_sleep_ms "$sleep_between"
      continue
    fi

    declare -A pid_ticket
    declare -A pid_worktree

    for ticket in $selected; do
      local worktree_path="$worktrees_dir/$ticket"
      git -C "$repo_root" worktree remove -f "$worktree_path" >/dev/null 2>&1 || true
      if ! git -C "$repo_root" worktree add -B "ralph/$ticket" "$worktree_path" HEAD >/dev/null 2>&1; then
        ralph_update_state "$ticket" "FAILED" "worktree add failed" "$repo_root/.tf/knowledge"
        continue
      fi
      (
        cd "$worktree_path" || exit 1
        ralph_run_ticket "$ticket" "$workflow" "$workflow_flags" "false"
      ) &
      local pid=$!
      pid_ticket[$pid]="$ticket"
      pid_worktree[$pid]="$worktree_path"
    done

    for pid in "${!pid_ticket[@]}"; do
      wait "$pid"
      local rc=$?
      local ticket="${pid_ticket[$pid]}"
      local worktree="${pid_worktree[$pid]}"
      if [ $rc -ne 0 ]; then
        ralph_update_state "$ticket" "FAILED" "pi -c failed (exit $rc)" "$worktree/.tf/knowledge"
        return $rc
      fi
      ralph_update_state "$ticket" "COMPLETE" "" "$worktree/.tf/knowledge"

      if [ "$keep_worktrees" != "true" ]; then
        git -C "$repo_root" worktree remove -f "$worktree" >/dev/null 2>&1 || rm -rf "$worktree"
      fi
    done

    iteration=$((iteration + $(echo "$selected" | wc -l | tr -d ' ')))
    ralph_sleep_ms "$sleep_between"
  done

  echo "Max iterations reached ($max_iterations)."
  if [ "$dry_run" != "true" ]; then
    ralph_set_state "COMPLETE"
  fi
  if [ "$promise_on_complete" = "true" ]; then
    echo "<promise>COMPLETE</promise>"
  fi
}

ralph_cmd() {
  require_project_tf

  local subcmd="${1:-}"
  shift || true
  
  case "$subcmd" in
    init)
      ralph_init
      ;;
    status)
      ralph_status
      ;;
    reset)
      ralph_reset "$@"
      ;;
    lessons)
      ralph_lessons "$@"
      ;;
    start)
      ralph_start "$@"
      ;;
    run)
      ralph_run "$@"
      ;;
    ""|help|--help|-h)
      ralph_usage
      ;;
    *)
      echo "Unknown ralph subcommand: $subcmd" >&2
      ralph_usage
      exit 1
      ;;
  esac
}

# =============================================================================
# AGENTS.md Management
# =============================================================================

agentsmd_usage() {
  cat <<'EOF'
AGENTS.md Management

Usage:
  tf agentsmd init [path]          Create minimal AGENTS.md
  tf agentsmd status [path]        Show AGENTS.md overview
  tf agentsmd validate [path]      Check for bloat, stale paths
  tf agentsmd fix [path]           Auto-fix formatting issues
  tf agentsmd update [path]        Update tool preferences

Options:
  [path]      Target directory (default: current directory)
              Creates/updates AGENTS.md at [path]/AGENTS.md
EOF
}

agentsmd_detect_package_manager() {
  local target_dir="$1"
  
  # Check for uv (preferred)
  if [ -f "$target_dir/uv.lock" ] || [ -f "$target_dir/pyproject.toml" ] && grep -q "\[tool.uv\]" "$target_dir/pyproject.toml" 2>/dev/null; then
    echo "uv"
    return 0
  fi
  
  # Check for other Python package managers
  if [ -f "$target_dir/poetry.lock" ]; then
    echo "poetry"
    return 0
  fi
  if [ -f "$target_dir/Pipfile" ]; then
    echo "pipenv"
    return 0
  fi
  if [ -f "$target_dir/requirements.txt" ]; then
    echo "pip"
    return 0
  fi
  if [ -f "$target_dir/setup.py" ] || [ -f "$target_dir/setup.cfg" ]; then
    echo "pip"
    return 0
  fi
  
  # Check for Node package managers
  if [ -f "$target_dir/pnpm-lock.yaml" ]; then
    echo "pnpm"
    return 0
  fi
  if [ -f "$target_dir/yarn.lock" ]; then
    echo "yarn"
    return 0
  fi
  if [ -f "$target_dir/package-lock.json" ]; then
    echo "npm"
    return 0
  fi
  if [ -f "$target_dir/bun.lockb" ]; then
    echo "bun"
    return 0
  fi
  
  # Check for other languages
  if [ -f "$target_dir/Cargo.toml" ]; then
    echo "cargo"
    return 0
  fi
  if [ -f "$target_dir/go.mod" ]; then
    echo "go"
    return 0
  fi
  if [ -f "$target_dir/Gemfile" ]; then
    echo "bundle"
    return 0
  fi
  
  # Default to uv for Python projects (check pyproject.toml without uv marker)
  if [ -f "$target_dir/pyproject.toml" ]; then
    echo "uv"
    return 0
  fi
  
  echo "unknown"
}

agentsmd_get_default_commands() {
  local pm="$1"
  case "$pm" in
    uv)
      echo "run: uv run python"
      echo "test: uv run pytest"
      echo "lint: uv run ruff check ."
      echo "format: uv run ruff format ."
      echo "typecheck: uv run mypy ."
      ;;
    poetry)
      echo "run: poetry run python"
      echo "test: poetry run pytest"
      echo "lint: poetry run ruff check ."
      ;;
    pipenv)
      echo "run: pipenv run python"
      echo "test: pipenv run pytest"
      ;;
    pip)
      echo "run: python"
      echo "test: pytest"
      ;;
    pnpm)
      echo "run: pnpm dev"
      echo "build: pnpm build"
      echo "test: pnpm test"
      echo "lint: pnpm lint"
      ;;
    npm)
      echo "run: npm run dev"
      echo "build: npm run build"
      echo "test: npm test"
      echo "lint: npm run lint"
      ;;
    yarn)
      echo "run: yarn dev"
      echo "build: yarn build"
      echo "test: yarn test"
      ;;
    bun)
      echo "run: bun run dev"
      echo "build: bun run build"
      echo "test: bun test"
      ;;
    cargo)
      echo "build: cargo build"
      echo "test: cargo test"
      echo "run: cargo run"
      ;;
    go)
      echo "build: go build"
      echo "test: go test"
      echo "run: go run ."
      ;;
    bundle)
      echo "run: bundle exec ruby"
      echo "test: bundle exec rspec"
      ;;
    *)
      echo ""
      ;;
  esac
}

agentsmd_init() {
  local target_dir="${1:-$(pwd)}"
  target_dir="$(cd "$target_dir" && pwd)"
  local agents_file="$target_dir/AGENTS.md"
  
  echo "Initializing AGENTS.md..."
  echo "Target directory: $target_dir"
  
  # Check if file already exists
  if [ -f "$agents_file" ]; then
    echo ""
    echo "⚠️  AGENTS.md already exists at:"
    echo "   $agents_file"
    echo ""
    read -r -p "Overwrite? (y/N) " yn
    case "$yn" in
      [Yy]*)
        mv "$agents_file" "$agents_file.backup.$(date +%Y%m%d%H%M%S)"
        echo "Backed up existing file."
        ;;
      *)
        echo "Cancelled."
        exit 0
        ;;
    esac
  fi
  
  # Detect package manager
  local pm
  pm=$(agentsmd_detect_package_manager "$target_dir")
  echo "Detected package manager: $pm"
  
  # Get project name from directory
  local project_name
  project_name=$(basename "$target_dir")
  
  # Interactive prompts
  echo ""
  read -r -p "Project name [$project_name]: " input_name
  project_name="${input_name:-$project_name}"
  
  echo ""
  read -r -p "One-sentence description: " description
  
  if [ -z "$description" ]; then
    description="A $project_name project."
  fi
  
  # Generate AGENTS.md content
  cat > "$agents_file" <<EOF
# $project_name

$description

## Quick Commands
EOF

  # Add commands based on package manager
  local cmds
  cmds=$(agentsmd_get_default_commands "$pm")
  if [ -n "$cmds" ]; then
    while IFS= read -r line; do
      if [ -n "$line" ]; then
        echo "- $line" >> "$agents_file"
      fi
    done <<< "$cmds"
  fi
  
  # Add package manager note
  case "$pm" in
    uv)
      echo "" >> "$agents_file"
      echo "This project uses \`uv\` for Python package management." >> "$agents_file"
      echo "See: https://docs.astral.sh/uv/" >> "$agents_file"
      ;;
    poetry)
      echo "" >> "$agents_file"
      echo "This project uses \`poetry\` for Python package management." >> "$agents_file"
      ;;
    pnpm)
      echo "" >> "$agents_file"
      echo "This project uses \`pnpm\` for Node.js package management." >> "$agents_file"
      ;;
  esac
  
  # Add conventions section
  cat >> "$agents_file" <<'EOF'

## Conventions

<!-- Add links to convention docs as needed: -->
<!-- - TypeScript: See [docs/TYPESCRIPT.md](./docs/TYPESCRIPT.md) -->
<!-- - Testing: See [docs/TESTING.md](./docs/TESTING.md) -->

## Notes

<!-- Project-specific notes for AI agents -->
EOF

  echo ""
  echo "✓ Created AGENTS.md at:"
  echo "  $agents_file"
  echo ""
  echo "File size: $(wc -c < "$agents_file") bytes"
  echo ""
  echo "Next steps:"
  echo "  1. Review and customize the description"
  echo "  2. Add convention docs to docs/ folder if needed"
  echo "  3. Run 'tf agentsmd validate' to check"
  
  # Offer to symlink CLAUDE.md for Claude Code users
  if [ ! -f "$target_dir/CLAUDE.md" ]; then
    echo ""
    read -r -p "Create CLAUDE.md symlink for Claude Code? (y/N) " yn
    case "$yn" in
      [Yy]*)
        ln -s AGENTS.md "$target_dir/CLAUDE.md"
        echo "Created CLAUDE.md → AGENTS.md symlink"
        ;;
    esac
  fi
}

agentsmd_status() {
  local target_dir="${1:-$(pwd)}"
  local agents_file="$target_dir/AGENTS.md"
  
  echo "=== AGENTS.md Status ==="
  echo ""
  
  if [ ! -f "$agents_file" ]; then
    echo "❌ No AGENTS.md found at: $agents_file"
    echo ""
    echo "Create one with:"
    echo "  tf agentsmd init"
    exit 1
  fi
  
  local size
  size=$(wc -c < "$agents_file")
  local lines
  lines=$(wc -l < "$agents_file")
  
  echo "File: $agents_file"
  echo "Size: $size bytes"
  echo "Lines: $lines"
  echo ""
  
  # Size assessment
  if [ "$size" -lt 2048 ]; then
    echo "✓ Size: Good (under 2KB)"
  elif [ "$size" -lt 5120 ]; then
    echo "⚠️  Size: Moderate ($size bytes) - consider using progressive disclosure"
  else
    echo "❌ Size: Large ($size bytes) - recommend refactoring"
  fi
  
  # Check for CLAUDE.md symlink
  echo ""
  if [ -L "$target_dir/CLAUDE.md" ]; then
    echo "✓ CLAUDE.md symlink exists"
  elif [ -f "$target_dir/CLAUDE.md" ]; then
    echo "⚠️  CLAUDE.md exists (separate file, not symlinked)"
  else
    echo "○ CLAUDE.md not found (optional, for Claude Code users)"
  fi
  
  # Check for nested AGENTS.md files
  echo ""
  echo "Nested AGENTS.md files:"
  local found_nested=false
  while IFS= read -r -d '' file; do
    if [ "$file" != "$agents_file" ]; then
      echo "  - ${file#$target_dir/} ($(wc -c < "$file") bytes)"
      found_nested=true
    fi
  done < <(find "$target_dir" -name "AGENTS.md" -type f -print0 2>/dev/null)
  
  if [ "$found_nested" = false ]; then
    echo "  (none found)"
  fi
  
  # Quick content preview
  echo ""
  echo "=== Content Preview ==="
  head -20 "$agents_file"
  if [ "$lines" -gt 20 ]; then
    echo "... ($((lines - 20)) more lines)"
  fi
}

agentsmd_validate() {
  local target_dir="${1:-$(pwd)}"
  local agents_file="$target_dir/AGENTS.md"
  
  echo "=== AGENTS.md Validation ==="
  echo ""
  
  if [ ! -f "$agents_file" ]; then
    echo "❌ AGENTS.md not found at: $agents_file"
    exit 1
  fi
  
  local issues=0
  local warnings=0
  
  # Check file size
  local size
  size=$(wc -c < "$agents_file")
  echo "File size: $size bytes"
  
  if [ "$size" -gt 5120 ]; then
    echo "❌ File is large ($size bytes > 5KB). Consider progressive disclosure."
    ((issues++))
  elif [ "$size" -gt 2048 ]; then
    echo "⚠️  File is moderate size ($size bytes). Monitor for growth."
    ((warnings++))
  else
    echo "✓ File size is good"
  fi
  
  # Extract and check file paths (skip comments)
  echo ""
  echo "Checking referenced paths..."
  local paths
  paths=$(grep -v '^\s*<' "$agents_file" 2>/dev/null | grep -oE '\b(src|lib|docs|test|tests|app|bin|scripts)/[a-zA-Z0-9_./-]+\.[a-z]+' 2>/dev/null || true)
  
  local stale_paths=()
  if [ -n "$paths" ]; then
    while IFS= read -r path; do
      if [ ! -e "$target_dir/$path" ] && [ ! -e "$path" ]; then
        stale_paths+=("$path")
      fi
    done <<< "$paths"
  fi
  
  if [ ${#stale_paths[@]} -gt 0 ]; then
    echo "⚠️  Potentially stale paths found:"
    for path in "${stale_paths[@]}"; do
      echo "   - $path (not found)"
    done
    ((warnings++))
  else
    echo "✓ No obviously stale paths detected"
  fi
  
  # Check for common anti-patterns
  echo ""
  echo "Checking for anti-patterns..."
  
  # Check for vague platitudes
  local platitudes=("write clean code" "follow best practices" "keep it simple" "don't repeat yourself" "write good code")
  local found_platitudes=()
  for phrase in "${platitudes[@]}"; do
    if grep -qi "$phrase" "$agents_file" 2>/dev/null; then
      found_platitudes+=("$phrase")
    fi
  done
  
  if [ ${#found_platitudes[@]} -gt 0 ]; then
    echo "⚠️  Vague platitudes found (not actionable):"
    for phrase in "${found_platitudes[@]}"; do
      echo "   - \"$phrase\""
    done
    ((warnings++))
  else
    echo "✓ No vague platitudes found"
  fi
  
  # Check for "always" / "never" (potential contradictions)
  local absolutes
  absolutes=$(grep -iE "^\s*[-*]?\s*(always|never)\s+" "$agents_file" 2>/dev/null | head -5 || true)
  if [ -n "$absolutes" ]; then
    echo "⚠️  Absolute statements found (may cause contradictions):"
    echo "$absolutes" | head -3 | sed 's/^/   /'
    if [ "$(echo "$absolutes" | wc -l)" -gt 3 ]; then
      echo "   ... ($(echo "$absolutes" | wc -l) more)"
    fi
    ((warnings++))
  fi
  
  # Check for file structure documentation
  if grep -qiE "(directory structure|folder structure|file structure|project structure)" "$agents_file" 2>/dev/null; then
    echo "⚠️  File structure documentation found - this goes stale quickly"
    ((warnings++))
  fi
  
  # Summary
  echo ""
  echo "=== Summary ==="
  if [ $issues -eq 0 ] && [ $warnings -eq 0 ]; then
    echo "✓ All checks passed!"
  else
    echo "Issues: $issues, Warnings: $warnings"
    if [ $issues -gt 0 ]; then
      echo "Run 'tf agentsmd fix' to attempt auto-fixes"
    fi
  fi
}

agentsmd_fix() {
  local target_dir="${1:-$(pwd)}"
  local agents_file="$target_dir/AGENTS.md"
  
  echo "=== AGENTS.md Auto-Fix ==="
  echo ""
  
  if [ ! -f "$agents_file" ]; then
    echo "❌ AGENTS.md not found at: $agents_file"
    exit 1
  fi
  
  # Create backup
  local backup="$agents_file.backup.$(date +%Y%m%d%H%M%S)"
  cp "$agents_file" "$backup"
  echo "✓ Backup created: $backup"
  echo ""
  
  local fixes=0
  
  # Fix 1: Add package manager if missing
  if ! grep -qiE "(package manager|uv|poetry|pip|npm|pnpm|yarn)" "$agents_file"; then
    local pm
    pm=$(agentsmd_detect_package_manager "$target_dir")
    if [ "$pm" != "unknown" ]; then
      echo "Adding package manager ($pm)..."
      # Insert after the first heading
      sed -i.bak "1,/^# /{ /^# /a\\
\\
## Package Manager\\
\\
This project uses \`$pm\`.\\

}" "$agents_file" 2>/dev/null || true
      rm -f "$agents_file.bak"
      ((fixes++))
    fi
  fi
  
  # Fix 2: Remove trailing whitespace
  if sed -i.bak 's/[[:space:]]*$//' "$agents_file" 2>/dev/null; then
    if ! diff -q "$agents_file" "$agents_file.bak" >/dev/null 2>&1; then
      echo "✓ Removed trailing whitespace"
      ((fixes++))
    fi
    rm -f "$agents_file.bak"
  fi
  
  # Fix 3: Ensure single newline at end of file
  if [ -s "$agents_file" ]; then
    if [ "$(tail -c 1 "$agents_file" | wc -l)" -eq 0 ]; then
      echo "" >> "$agents_file"
      echo "✓ Added trailing newline"
      ((fixes++))
    fi
  fi
  
  echo ""
  if [ $fixes -eq 0 ]; then
    echo "No auto-fixes applied."
  else
    echo "Applied $fixes fix(es)."
  fi
  echo ""
  echo "Review changes with: git diff $agents_file"
}

agentsmd_update() {
  local target_dir="${1:-$(pwd)}"
  local agents_file="$target_dir/AGENTS.md"
  
  if [ ! -f "$agents_file" ]; then
    echo "AGENTS.md not found. Run: tf agentsmd init"
    exit 1
  fi
  
  # Backup
  cp "$agents_file" "$agents_file.backup.$(date +%Y%m%d%H%M%S)"
  
  # Update tool preferences section if it exists
  if grep -q "## Tool Preferences" "$agents_file"; then
    echo "Found Tool Preferences section - review manually"
  else
    # Add tool preferences section
    cat >> "$agents_file" <<'EOF'

## Tool Preferences
- Use `rg` instead of `grep` for searching
- Use `ast-grep` for semantic code search when available
EOF
    echo "Added Tool Preferences section"
  fi
  
  echo "Review changes: git diff $agents_file"
}

agentsmd_cmd() {
  local subcmd="${1:-}"
  shift || true
  
  case "$subcmd" in
    init)
      agentsmd_init "$@"
      ;;
    status)
      agentsmd_status "$@"
      ;;
    validate)
      agentsmd_validate "$@"
      ;;
    fix)
      agentsmd_fix "$@"
      ;;
    update)
      agentsmd_update "$@"
      ;;
    ""|help|--help|-h)
      agentsmd_usage
      ;;
    *)
      echo "Unknown agentsmd subcommand: $subcmd" >&2
      agentsmd_usage
      exit 1
      ;;
  esac
}

next_ticket() {
  local query="tk ready | head -1 | awk '{print \$1}'"
  local ralph_config=""

  if [ -n "$TF_BASE" ] && [ -f "$TF_BASE/ralph/config.json" ]; then
    ralph_config="$TF_BASE/ralph/config.json"
  elif [ -f ".tf/ralph/config.json" ]; then
    ralph_config="$(pwd)/.tf/ralph/config.json"
  fi

  if [ -n "$ralph_config" ]; then
    local python_bin=""
    if command -v python3 >/dev/null 2>&1; then
      python_bin="python3"
    elif command -v python >/dev/null 2>&1; then
      python_bin="python"
    fi

    if [ -n "$python_bin" ]; then
      local config_query
      config_query=$(RALPH_CONFIG="$ralph_config" "$python_bin" - <<'PY'
import json
import os
import sys

path = os.environ.get("RALPH_CONFIG", "").strip()
if not path:
    sys.exit(0)

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    sys.exit(0)

query = str(data.get("ticketQuery", "") or "").strip()
if query:
    print(query)
PY
)
      if [ -n "$config_query" ]; then
        query="$config_query"
      fi
    fi
  fi

  if ! command -v tk >/dev/null 2>&1; then
    echo "tk not found in PATH; cannot query tickets." >&2
    exit 1
  fi

  local ticket
  ticket=$(eval "$query" 2>/dev/null | head -1 | awk '{print $1}')
  if [ -z "$ticket" ]; then
    echo "No ready tickets found." >&2
    exit 1
  fi

  echo "$ticket"
}

backlog_ls() {
  require_project_tf

  local topic="${1:-}"
  local python_bin=""
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  else
    echo "Python not found; cannot list backlogs." >&2
    exit 1
  fi

  local ignore_project="false"
  if [ "$IS_GLOBAL" = true ]; then
    ignore_project="true"
  fi

  local args=("$CONFIG_HELPER")
  if [ "$CONFIG_HELPER_SUPPORTS_FLAGS" = true ]; then
    args+=(--base "$TARGET_BASE")
    if [ "$ignore_project" = "true" ]; then
      args+=(--ignore-project)
    fi
  fi
  args+=(knowledge-dir)

  local knowledge_dir
  knowledge_dir=$(TARGET_BASE="$TARGET_BASE" IGNORE_PROJECT_CONFIG="$ignore_project" "$python_bin" "${args[@]}")

  KNOWLEDGE_DIR="$knowledge_dir" TOPIC="$topic" \
    "$python_bin" - <<'PY'
import os
from pathlib import Path

topic_input = os.environ.get("TOPIC", "").strip()
knowledge_dir = os.environ.get("KNOWLEDGE_DIR", "").strip()

if not knowledge_dir:
    print("Knowledge directory not resolved.")
    raise SystemExit(1)

knowledge_path = Path(knowledge_dir).expanduser()
topics_dir = knowledge_path / "topics"

if not topics_dir.exists():
    print(f"No topics directory found: {topics_dir}")
    raise SystemExit(0)


def list_topics():
    topics = []
    for p in sorted(topics_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("seed-") or p.name.startswith("baseline-") or p.name.startswith("plan-"):
            topics.append(p)
    return topics


def parse_backlog(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if cells[0].lower() == "id":
            continue
        if set(cells[0]) == {"-"}:
            continue
        if len(cells) < 2:
            continue
        rows.append(cells)
    return rows


def topic_type(name: str):
    if name.startswith("seed-"):
        return "seed"
    if name.startswith("baseline-"):
        return "baseline"
    if name.startswith("plan-"):
        return "plan"
    return "topic"


def ticket_summary(rows):
    ids = [r[0] for r in rows if r]
    if not ids:
        return "0"
    if len(ids) <= 3:
        return f"{len(ids)} ({', '.join(ids)})"
    return f"{len(ids)} ({', '.join(ids[:3])}, …)"


def resolve_topic(arg: str):
    if not arg:
        return None
    candidate = Path(arg).expanduser()
    if candidate.exists():
        return candidate
    if not candidate.is_absolute():
        rel = Path.cwd() / candidate
        if rel.exists():
            return rel
    return topics_dir / arg


topics = []
if topic_input:
    topic_path = resolve_topic(topic_input)
    if not topic_path.exists():
        available = [p.name for p in list_topics()]
        print(f"Topic not found: {topic_input}")
        if available:
            print("Available topics:")
            for name in available:
                print(f"- {name}")
        raise SystemExit(1)
    topics = [topic_path]
else:
    topics = list_topics()

if not topics:
    print(f"No seed/baseline/plan topics found in {topics_dir}")
    raise SystemExit(0)

if len(topics) == 1:
    topic = topics[0]
    backlog_path = topic / "backlog.md"
    rows = parse_backlog(backlog_path)
    print(f"Topic: {topic.name} ({topic_type(topic.name)})")
    if backlog_path.exists():
        print(f"Backlog: yes ({len(rows)} tickets)")
        print("")
        print(f"# Backlog: {topic.name}")
        print("| ID | Title | Est. Hours |")
        print("|----|-------|------------|")
        for row in rows:
            est = row[2] if len(row) > 2 else ""
            print(f"| {row[0]} | {row[1]} | {est} |")
    else:
        print("Backlog: no (unticketed)")
        print(f"Run: /tf-backlog {topic.name}")
else:
    print("| Topic | Type | Backlog | Tickets |")
    print("|-------|------|---------|---------|")
    for topic in topics:
        backlog_path = topic / "backlog.md"
        rows = parse_backlog(backlog_path)
        backlog_status = "yes" if backlog_path.exists() else "no"
        tickets = ticket_summary(rows) if backlog_path.exists() else "0"
        print(f"| {topic.name} | {topic_type(topic.name)} | {backlog_status} | {tickets} |")
PY
}

sync_models() {
  local python_cmd=()
  if resolve_python_cmd; then
    python_cmd=("${PYTHON_CMD[@]}")
  else
    echo "Python not found; cannot sync models." >&2
    exit 1
  fi

  # In global mode, use ~/.tf/scripts/tf_config.py or fall back to embedded
  if [ "$IS_GLOBAL" = true ]; then
    ensure_global_scripts
    local global_tf_config="$HOME/.tf/scripts/tf_config.py"
    if [ -f "$global_tf_config" ]; then
      CONFIG_HELPER="$global_tf_config"
      CONFIG_HELPER_SUPPORTS_FLAGS=false
      if grep -q 'add_argument("--base"' "$CONFIG_HELPER" 2>/dev/null; then
        CONFIG_HELPER_SUPPORTS_FLAGS=true
      fi
    fi
  else
    require_project_tf
  fi

  if [ -z "$CONFIG_HELPER" ]; then
    echo "Cannot find tf_config.py. Run 'tf init' in a project or 'tf setup --global' first." >&2
    exit 1
  fi

  local ignore_project="false"
  if [ "$IS_GLOBAL" = true ]; then
    ignore_project="true"
  fi

  echo "Syncing models from meta-model configuration..."
  local args=("$CONFIG_HELPER")
  if [ "$CONFIG_HELPER_SUPPORTS_FLAGS" = true ]; then
    args+=(--base "$TARGET_BASE")
    if [ "$ignore_project" = "true" ]; then
      args+=(--ignore-project)
    fi
  fi
  args+=(sync-models)
  TARGET_BASE="$TARGET_BASE" IGNORE_PROJECT_CONFIG="$ignore_project" "${python_cmd[@]}" "${args[@]}"
}

login() {
  echo "Ticketflow Login"
  echo ""
  echo "Configure API keys for external services."
  echo "Leave blank to skip a service."
  echo ""

  # Determine target location
  if [ -z "$TARGET_BASE" ]; then
    if [ -d ".pi" ]; then
      TARGET_BASE="$(pwd)/.pi"
      SCOPE_FLAG="-l"
      IS_GLOBAL=false
      echo "Using project config: $TARGET_BASE"
    else
      TARGET_BASE="$HOME/.pi/agent"
      SCOPE_FLAG=""
      IS_GLOBAL=true
      echo "Using global config: $TARGET_BASE"
    fi
  fi

  if [ -n "$TF_BASE" ] && [ -d "$TF_BASE" ]; then
    set_config_helper
  elif [ -z "$TF_BASE" ] && [ -d ".tf" ]; then
    TF_BASE="$(pwd)/.tf"
    set_config_helper
  fi

  echo ""
  echo "=== Web Search (pi-web-access) ==="
  echo "Required for web search functionality."
  echo "Get a key at: https://perplexity.ai/settings/api"
  read -r -p "Perplexity API key: " perplexity_key
  perplexity_key="${perplexity_key:-${PERPLEXITY_API_KEY:-}}"

  echo ""
  echo "=== MCP Servers ==="
  echo "Context7: Works without API key (rate limited)"
  echo "Get a key at: https://context7.com/ (optional)"
  read -r -p "Context7 API key (optional): " ctx7_key
  ctx7_key="${ctx7_key:-${CONTEXT7_API_KEY:-}}"

  echo ""
  echo "Exa: Works without API key (rate limited)"
  echo "Get a key at: https://exa.ai/ (optional)"
  read -r -p "Exa API key (optional): " exa_key
  exa_key="${exa_key:-${EXA_API_KEY:-}}"

  echo ""
  echo "ZAI: Required for ZAI MCP servers (web-search, web-reader, vision)"
  read -r -p "ZAI API key (optional): " zai_key
  zai_key="${zai_key:-${ZAI_API_KEY:-}}"

  # Configure web-search.json for pi-web-access
  if [ -n "$perplexity_key" ]; then
    local web_search_json="$TARGET_BASE/web-search.json"
    mkdir -p "$TARGET_BASE"
    if [ ! -f "$web_search_json" ]; then
      echo ""
      echo "Creating $web_search_json..."
      echo "{\"perplexityApiKey\": \"$perplexity_key\"}" > "$web_search_json"
      chmod 600 "$web_search_json"
      echo "✓ Configured pi-web-access"
    else
      echo ""
      echo "Updating $web_search_json..."
      if command -v python3 >/dev/null 2>&1; then
        python3 - "$perplexity_key" "$web_search_json" <<'PY'
import json
import sys
import os
key = sys.argv[1]
path = sys.argv[2]
config = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            config = json.load(f)
    except:
        pass
config["perplexityApiKey"] = key
with open(path, "w") as f:
    json.dump(config, f, indent=2)
PY
      else
        # Fallback: just write the key
        echo "{\"perplexityApiKey\": \"$perplexity_key\"}" > "$web_search_json"
      fi
      echo "✓ Updated pi-web-access configuration"
    fi
  else
    echo ""
    echo "Note: Perplexity API key not provided. To enable web search later:"
    echo "  tf login"
  fi

  # Configure mcp.json for MCP servers
  local has_mcp_keys=false
  [ -n "$zai_key" ] || [ -n "$ctx7_key" ] || [ -n "$exa_key" ] && has_mcp_keys=true

  if [ "$has_mcp_keys" = true ]; then
    echo ""
    echo "Configuring MCP servers..."
    configure_mcp "$zai_key" "$ctx7_key" "$exa_key"
  else
    echo ""
    echo "Note: No MCP API keys provided. To configure MCP servers later:"
    echo "  tf login"
  fi

  echo ""
  echo "Login complete. API keys saved to:"
  [ -n "$perplexity_key" ] && echo "  - $TARGET_BASE/web-search.json"
  [ "$has_mcp_keys" = true ] && echo "  - $TARGET_BASE/mcp.json"
}

case "$COMMAND" in
  setup)
    echo "Ticketflow setup"
    if [ -z "$TARGET_BASE" ]; then
      read -r -p "Install Pi assets globally? (Y/n) " yn
      case "$yn" in
        [Nn]*)
          read -r -p "Project path (default: current dir): " project_path
          project_path="${project_path:-$(pwd)}"
          TARGET_BASE="$project_path/.pi"
          TF_BASE="$project_path/.tf"
          SCOPE_FLAG="-l"
          IS_GLOBAL=false
          ;;
        *)
          TARGET_BASE="$HOME/.pi/agent"
          TF_BASE=""
          SCOPE_FLAG=""
          IS_GLOBAL=true
          ;;
      esac
    fi

    read -r -p "Install required Pi extensions (subagents, model-switch, prompt-template-model)? (Y/n) " yn
    install_deps=true
    case "$yn" in [Nn]*) install_deps=false ;; esac

    read -r -p "Install optional Pi extensions (review-loop, mcp-adapter, web-access)? (y/N) " yn
    install_optional=false
    case "$yn" in [Yy]*) install_optional=true ;; esac

    read -r -p "Configure API keys for MCP servers and web search? (y/N) " yn
    case "$yn" in [Yy]*) login ;; esac

    install_files

    if [ "$IS_GLOBAL" = true ]; then
      ensure_global_settings
    fi

    if [ "$IS_GLOBAL" = false ]; then
      tf_init
    else
      echo ""
      echo "Next: run 'tf init' in each project to scaffold .tf/."
    fi

    install_extensions "$install_deps" "$install_optional"
    ;;
  init)
    tf_init
    ;;
  login)
    login
    ;;
  sync)
    sync_models
    ;;
  update)
    update_assets
    ;;
  doctor)
    doctor
    ;;
  next)
    if [ "${#ARGS[@]}" -gt 0 ]; then
      echo "Too many arguments for next" >&2
      exit 1
    fi
    next_ticket
    ;;
  backlog-ls)
    if [ "${#ARGS[@]}" -gt 1 ]; then
      echo "Too many arguments for backlog-ls" >&2
      exit 1
    fi
    backlog_ls "${ARGS[0]:-}"
    ;;
  track)
    if [ "${#ARGS[@]}" -eq 0 ]; then
      track_file ""
    elif [ "${#ARGS[@]}" -eq 1 ]; then
      track_file "${ARGS[0]}"
    else
      echo "Too many arguments for track" >&2
      exit 1
    fi
    ;;
  ralph)
    ralph_cmd "${ARGS[@]}"
    ;;
  agentsmd)
    agentsmd_cmd "${ARGS[@]}"
    ;;
  *)
    usage
    exit 1
    ;;
esac
