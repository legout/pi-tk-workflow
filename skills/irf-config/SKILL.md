---
name: tf-config
description: Setup, configuration, and maintenance for IRF workflow. Use for installing extensions, syncing models, verifying setup, and managing workflow configuration.
---

# IRF Configuration Skill

Expertise for setup, maintenance, and synchronization of the IRF workflow.

## When to Use This Skill

- First-time setup of IRF workflow
- Updating models in agent files
- Verifying extensions are installed
- Troubleshooting configuration issues
- Syncing after config changes

## Prerequisites Check

Always run first:

```bash
# Required extensions
pi list | grep -q "pi-subagents" && echo "✓ pi-subagents" || echo "✗ pi-subagents"
pi list | grep -q "pi-model-switch" && echo "✓ pi-model-switch" || echo "✗ pi-model-switch"

# Optional extensions
pi list | grep -q "pi-mcp-adapter" && echo "✓ pi-mcp-adapter" || echo "○ pi-mcp-adapter (optional)"
pi list | grep -q "pi-review-loop" && echo "✓ pi-review-loop" || echo "○ pi-review-loop (optional)"
```

## Configuration Files

### Workflow Config

Location (project overrides global):
- `.pi/workflows/tf/config.json` (project)
- `~/.pi/agent/workflows/tf/config.json` (global)

Structure:
```json
{
  "models": {
    "implementer": "chutes/moonshotai/Kimi-K2.5-TEE:high",
    "reviewer-general": "openai-codex/gpt-5.1-codex-mini:high",
    "review-merge": "zai/glm-4.7:medium",
    "fixer": "zai/glm-4.7:high",
    "closer": "zai/glm-4.7:medium",
    "planning": "openai-codex/gpt-5.1-codex-mini:medium",
    "config": "zai/glm-4.7:medium"
  },
  "checkers": {
    "typescript": {
      "files": "\\.(ts|tsx)$",
      "lint": "eslint {files} --fix",
      "format": "prettier --write {files}",
      "typecheck": "tsc --noEmit"
    }
  },
  "workflow": {
    "enableResearcher": true,
    "knowledgeDir": ".pi/knowledge",
    "clarifyDefault": true
  }
}
```

### Agent Files

Located at (project overrides global):
- `.pi/agents/*.md` (project)
- `~/.pi/agent/agents/*.md` (global)

Each agent file has frontmatter:
```yaml
---
name: implementer
description: Implements tickets
model: chutes/moonshotai/Kimi-K2.5-TEE:high
tools: read, edit, write, bash
---
```

## Execution Procedures

### Procedure: Verify Setup

Check complete installation status:

1. **Check extensions** (see Prerequisites Check above)

2. **Check agent files exist**:
   - `agents/implementer.md`
   - `agents/reviewer-general.md`
   - `agents/reviewer-spec-audit.md`
   - `agents/reviewer-second-opinion.md`
   - `agents/review-merge.md`
   - `agents/fixer.md`
   - `agents/closer.md`

3. **Check workflow config exists**:
   - Look for `workflows/tf/config.json`

4. **Check `tk` CLI**:
   ```bash
   which tk && tk --version
   ```

5. **Report status** with installation commands for missing items.

---

### Procedure: Sync Models

Update agent **and prompt** files from config:

**Agent mapping (config key → agent file)**:
| Config Key | Agent File |
|------------|------------|
| `models.implementer` | `agents/implementer.md` |
| `models.reviewer-general` | `agents/reviewer-general.md` |
| `models.reviewer-spec-audit` | `agents/reviewer-spec-audit.md` |
| `models.reviewer-second-opinion` | `agents/reviewer-second-opinion.md` |
| `models.review-merge` | `agents/review-merge.md` |
| `models.fixer` | `agents/fixer.md` |
| `models.closer` | `agents/closer.md` |
| `models.researcher` | `agents/researcher.md` |
| `models.researcher-fetch` | `agents/researcher-fetch.md` |

**Prompt mapping (config key → prompt file)**:
| Config Key | Prompt File |
|------------|-------------|
| `models.implementer` | `prompts/tf.md`, `prompts/tf-lite.md` |
| `models.planning` | `prompts/tf-plan.md`, `prompts/tf-plan-consult.md`, `prompts/tf-plan-revise.md`, `prompts/tf-plan-review.md`, `prompts/tf-seed.md`, `prompts/tf-backlog.md`, `prompts/tf-backlog-ls.md`, `prompts/tf-spike.md`, `prompts/tf-from-openspec.md`, `prompts/tf-baseline.md`, `prompts/tf-followups.md` |
| `models.config` | `prompts/tf-sync.md` |

**Steps**:

1. Read workflow config
2. For each mapping:
   - Read file
   - Find `model:` line in frontmatter
   - If different from config, update it
   - Write file back
3. Report changes made

**Example update**:
```yaml
# Before
model: anthropic/claude-sonnet-4

# After  
model: chutes/moonshotai/Kimi-K2.5-TEE:high
```

---

### Procedure: Generate Model Aliases

If `pi-model-switch` is installed, suggest useful aliases:

**File**: `~/.pi/agent/extensions/model-switch/aliases.json`

**Suggested content**:
```json
{
  "tf-implementer": [
    "chutes/moonshotai/Kimi-K2.5-TEE",
    "anthropic/claude-sonnet-4",
    "openai-codex/gpt-5.2"
  ],
  "tf-reviewer": [
    "openai-codex/gpt-5.1-codex-mini",
    "anthropic/claude-sonnet-4",
    "zai/glm-4.7"
  ],
  "tf-cheap": [
    "zai/glm-4.7",
    "google/gemini-2.5-flash"
  ],
  "tf-planning": [
    "openai-codex/gpt-5.1-codex-mini",
    "zai/glm-4.7"
  ],
  "tf-config": [
    "zai/glm-4.7",
    "openai-codex/gpt-5.1-codex-mini"
  ]
}
```

---

### Procedure: Verify MCP Configuration

Check if MCP tools are configured:

1. **Check for config file**:
   - `.pi/mcp.json` (project)
   - `~/.pi/agent/mcp.json` (global)

2. **Expected servers** (from config `workflow.mcpServers`):
   - context7
   - exa
   - grep_app
   - zai-web-search
   - zai-web-reader
   - zai-vision

3. **Report status**:
   - Which servers are configured
   - Which are missing
   - API key requirements

---

## Installation Commands

If extensions missing, provide:

```bash
# Required
pi install npm:pi-subagents
pi install npm:pi-model-switch

# Optional
pi install npm:pi-mcp-adapter
pi install npm:pi-review-loop
```

## Output Format

Always provide clear status report:

```
## Extension Status
✓ pi-subagents (installed)
✓ pi-model-switch (installed)
○ pi-mcp-adapter (optional, not installed)

## Agent Models Updated
- implementer: anthropic/claude-sonnet-4 → chutes/moonshotai/Kimi-K2.5-TEE:high
- fixer: (unchanged) zai/glm-4.7:high

## Agent Models Unchanged
- reviewer-general: openai-codex/gpt-5.1-codex-mini:high
- ...

## Prompt Models Updated
- tf-plan.md: openai-codex/gpt-5.1-codex-mini → openai-codex/gpt-5.1-codex-mini:medium

## Prompt Models Unchanged
- irf.md: chutes/moonshotai/Kimi-K2.5-TEE:high

## Recommendations
- Consider installing pi-mcp-adapter for research capabilities
```

## Error Handling

- **Config not found**: Create from template
- **Agent file not found**: Skip with warning
- **Prompt file not found**: Skip with warning
- **Model format invalid**: Report and skip
- **Permission denied**: Suggest running with appropriate permissions
