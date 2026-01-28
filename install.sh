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
  Use ./bin/irfc setup for interactive setup (extensions + MCP).
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

cp "$SCRIPT_DIR/prompts/implement-review-fix-close.md" "$TARGET_BASE/prompts/"
cp "$SCRIPT_DIR/prompts/irfc-sync.md" "$TARGET_BASE/prompts/"

cp "$SCRIPT_DIR/workflows/implement-review-fix-close/config.json" \
   "$TARGET_BASE/workflows/implement-review-fix-close/"
cp "$SCRIPT_DIR/workflows/implement-review-fix-close/README.md" \
   "$TARGET_BASE/workflows/implement-review-fix-close/"

echo "Installed IRFC workflow files to: $TARGET_BASE"
