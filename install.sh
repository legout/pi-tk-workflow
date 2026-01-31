#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./install.sh --global
  ./install.sh --project /path/to/project

Options:
  --global              Install into ~/.pi/agent
  --project <path>      Install into <path>/.pi
  --help                Show this help

Notes:
  This script only copies agents, prompts, and workflow config.
  Use ./bin/irf setup for interactive setup (extensions + MCP).
EOF
}

if [ "$#" -eq 0 ]; then
  usage
  exit 1
fi

TARGET_BASE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --global)
      TARGET_BASE="$HOME/.pi/agent"
      shift
      ;;
    --project)
      if [ -z "${2:-}" ]; then
        echo "Missing path after --project" >&2
        exit 1
      fi
      TARGET_BASE="$2/.pi"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
 done

if [ -z "$TARGET_BASE" ]; then
  echo "No target specified." >&2
  usage
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$TARGET_BASE/agents" "$TARGET_BASE/prompts" "$TARGET_BASE/workflows/implement-review-fix-close"

cp "$SCRIPT_DIR/agents/implementer.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/reviewer-general.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/reviewer-spec-audit.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/reviewer-second-opinion.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/review-merge.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/fixer.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/closer.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/researcher.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/researcher-fetch.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/simplifier.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/simplify-ticket.md" "$TARGET_BASE/agents/"
cp "$SCRIPT_DIR/agents/irf-planner.md" "$TARGET_BASE/agents/"

# Original prompts
cp "$SCRIPT_DIR/prompts/irf.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-sync.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-seed.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-backlog.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-spike.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-from-openspec.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-baseline.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-followups.md" "$TARGET_BASE/prompts/"

# Lite prompts (recommended - fewer subagents)
cp "$SCRIPT_DIR/prompts/irf-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-seed-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-backlog-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-spike-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-from-openspec-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-baseline-lite.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irf-followups-lite.md" "$TARGET_BASE/prompts/"

cp "$SCRIPT_DIR/workflows/implement-review-fix-close/config.json" \
   "$TARGET_BASE/workflows/implement-review-fix-close/"
cp "$SCRIPT_DIR/workflows/implement-review-fix-close/README.md" \
   "$TARGET_BASE/workflows/implement-review-fix-close/"

# Create root AGENTS.md if it doesn't exist (for --project installs)
if [ -f "$SCRIPT_DIR/docs/AGENTS.md.template" ] && [ ! -f "AGENTS.md" ]; then
  if [[ "$TARGET_BASE" != "$HOME/.pi/agent" ]]; then
    cp "$SCRIPT_DIR/docs/AGENTS.md.template" "AGENTS.md"
    echo "Created AGENTS.md in project root"
  fi
fi

echo "Installed IRF workflow files to: $TARGET_BASE"
echo ""
echo "Next steps:"
echo "  1. Review AGENTS.md (project patterns)"
echo "  2. Initialize Ralph: ./bin/irf ralph init"
echo "  3. Start working: /irf-lite <ticket>"
