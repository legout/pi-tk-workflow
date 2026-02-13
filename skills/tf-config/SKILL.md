---
name: tf-config
description: Setup, configuration, and maintenance for IRF workflow. Use for installing extensions, syncing models, and verifying project assets.
---

# TF Configuration Skill

Configuration and maintenance guide for project-local TF assets.

## Prerequisites Check

```bash
# Required extensions
pi list | grep -q "pi-subagents" && echo "✓ pi-subagents" || echo "✗ pi-subagents"
pi list | grep -q "pi-prompt-template-model" && echo "✓ pi-prompt-template-model" || echo "✗ pi-prompt-template-model"

# Optional extensions
pi list | grep -q "pi-review-loop" && echo "✓ pi-review-loop" || echo "○ pi-review-loop (optional)"
pi list | grep -q "pi-mcp-adapter" && echo "✓ pi-mcp-adapter" || echo "○ pi-mcp-adapter (optional)"
pi list | grep -q "pi-web-access" && echo "✓ pi-web-access" || echo "○ pi-web-access (optional)"
```

## Canonical Project Paths

- `agents/*.md`
- `prompts/*.md`
- `skills/*/SKILL.md`
- `.tf/config/settings.json`

Legacy `.pi/{agents,prompts,skills}` may still exist in older projects but is no longer canonical.

## Verify Setup

1. Check required extensions are installed.
2. Verify project files exist:
   - `agents/reviewer-general.md`
   - `prompts/tf.md`
   - `skills/tf-workflow/SKILL.md`
   - `.tf/config/settings.json`
3. Verify `tk` CLI availability: `which tk && tk --version`

## Model Sync

Run:

```bash
tf sync
```

`tf sync` updates frontmatter model/thinking in:
- `agents/*.md`
- `prompts/*.md`

using `.tf/config/settings.json` (`metaModels`, `agents`, `prompts`).

## MCP Configuration

Check MCP config locations:
- Project: `.pi/mcp.json` (optional)
- Global: `~/.pi/agent/mcp.json`

Expected servers from workflow config: `context7`, `exa`, `grep_app`, `zai-web-search`, `zai-web-reader`, `zai-vision`.

## Installation Commands

```bash
# Required
pi install npm:pi-prompt-template-model
pi install npm:pi-subagents

# Optional
pi install npm:pi-review-loop
pi install npm:pi-mcp-adapter
pi install npm:pi-web-access
```

## Error Handling

- Missing config: run `tf init`
- Missing assets: run `tf sync`
- Invalid model config: fix `.tf/config/settings.json`, then re-run `tf sync`
