---
description: Sync IRF workflow config into agent files (models, defaults) and verify extensions.
---

# IRF Sync

Apply the workflow configuration and verify required extensions are installed.

## Configuration Sources

Read and merge configs (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json` (project)
- `~/.pi/agent/workflows/implement-review-fix-close/config.json` (global)

## What to sync

### 1) Verify Required Extensions

Check that required extensions are installed:

**For lite workflows (recommended):**
```bash
# Check pi-subagents
pi list | grep -q "pi-subagents" && echo "✓ pi-subagents" || echo "✗ pi-subagents (run: pi install npm:pi-subagents)"

# Check pi-model-switch
pi list | grep -q "pi-model-switch" && echo "✓ pi-model-switch" || echo "✗ pi-model-switch (run: pi install npm:pi-model-switch)"
```

**Optional extensions:**
```bash
# Check pi-mcp-adapter (for research)
pi list | grep -q "pi-mcp-adapter" && echo "✓ pi-mcp-adapter" || echo "○ pi-mcp-adapter (optional, for MCP research tools)"

# Check pi-review-loop (for post-chain review)
pi list | grep -q "pi-review-loop" && echo "✓ pi-review-loop" || echo "○ pi-review-loop (optional, for /review-start)"
```

Report status for each extension.

### 2) Sync Agent Models

Update the `model:` field in these agent files when a model is provided in `models`:

| Config Key | Agent File |
|------------|------------|
| `implementer` | `agents/implementer.md` |
| `reviewer-general` | `agents/reviewer-general.md` |
| `reviewer-spec-audit` | `agents/reviewer-spec-audit.md` |
| `reviewer-second-opinion` | `agents/reviewer-second-opinion.md` |
| `review-merge` | `agents/review-merge.md` |
| `fixer` | `agents/fixer.md` |
| `closer` | `agents/closer.md` |
| `researcher` | `agents/researcher.md` |
| `researcher-fetch` | `agents/researcher-fetch.md` |

**Process:**
1. For each agent in the config `models` section:
2. Read the agent file
3. Find the `model:` line in the frontmatter
4. If different from config, update it
5. Write the file back

If a model is missing for an agent, leave its `model:` unchanged.

### 3) Verify Model Aliases (Optional)

If using `pi-model-switch`, check for model aliases config:
- `~/.pi/agent/extensions/model-switch/aliases.json`

If not present, suggest creating one with IRF-specific aliases:
```json
{
  "implementer": ["chutes/moonshotai/Kimi-K2.5-TEE", "anthropic/claude-sonnet-4"],
  "reviewer": ["openai-codex/gpt-5.1-codex-mini", "anthropic/claude-sonnet-4"],
  "cheap": ["zai/glm-4.7", "google/gemini-2.5-flash"],
  "planning": ["openai-codex/gpt-5.1-codex-mini", "zai/glm-4.7"]
}
```

## Output

After syncing, report:

```
## Extension Status
✓ pi-subagents (installed)
✓ pi-model-switch (installed)
○ pi-mcp-adapter (optional, not installed)
○ pi-review-loop (optional, not installed)

## Agent Models Updated
- implementer: anthropic/claude-sonnet-4 → chutes/moonshotai/Kimi-K2.5-TEE:high
- fixer: (unchanged) zai/glm-4.7:high

## Agent Models Unchanged
- reviewer-general: openai-codex/gpt-5.1-codex-mini:high
- reviewer-spec-audit: openai-codex/gpt-5.1-codex-mini:high
- ...

## Recommendations
- Consider installing pi-mcp-adapter for research capabilities
- Model aliases not configured - see ~/.pi/agent/extensions/model-switch/aliases.json
```

## Installation Commands

If extensions are missing, provide installation commands:

```bash
# Required for lite workflows
pi install npm:pi-subagents
pi install npm:pi-model-switch

# Optional
pi install npm:pi-mcp-adapter
pi install npm:pi-review-loop
```
