---
name: tf-config
description: Setup, configuration, and maintenance for IRF workflow. Use for installing extensions, syncing models, verifying setup, and managing workflow configuration.
---

# TF Configuration Skill

Expertise for setup, maintenance, and synchronization of the TF workflow.

## When to Use This Skill

- First-time setup of TF workflow
- Updating models in agent files
- Verifying extensions are installed
- Troubleshooting configuration issues
- Syncing after config changes

## Prerequisites Check

Always run first:

```bash
# Required extensions
pi list | grep -q "pi-subagents" && echo "✓ pi-subagents" || echo "✗ pi-subagents"
pi list | grep -q "pi-prompt-template-model" && echo "✓ pi-prompt-template-model" || echo "✗ pi-prompt-template-model"

# Optional extensions
pi list | grep -q "pi-model-switch" && echo "✓ pi-model-switch (optional, legacy)" || echo "○ pi-model-switch (optional, for legacy workflows)"
pi list | grep -q "pi-web-access" && echo "✓ pi-web-access" || echo "○ pi-web-access (preferred for web/docs research)"
pi list | grep -q "pi-mcp-adapter" && echo "✓ pi-mcp-adapter" || echo "○ pi-mcp-adapter (optional)"
pi list | grep -q "pi-review-loop" && echo "✓ pi-review-loop" || echo "○ pi-review-loop (optional)"
```

## Configuration Files

### Workflow Config

Location (project):
- `.tf/config/settings.json`

Structure:
```json
{
  "metaModels": {
    "worker": {
      "model": "kimi-coding/k2p5",
      "thinking": "high"
    },
    "planning": {
      "model": "openai-codex/gpt-5.2",
      "thinking": "medium"
    },
    "research": {
      "model": "minimax/MiniMax-M2.1",
      "thinking": "medium"
    },
    "fast": {
      "model": "zai/glm-4.7-flash",
      "thinking": "medium"
    },
    "general": {
      "model": "zai/glm-4.7",
      "thinking": "medium"
    },
    "review-general": {
      "model": "openai-codex/gpt-5.1-codex-mini",
      "thinking": "high"
    },
    "review-spec": {
      "model": "openai-codex/gpt-5.2-codex",
      "thinking": "high"
    },
    "review-secop": {
      "model": "github-copilot/grok-code-fast-1",
      "thinking": "high"
    }
  },
  "agents": {
    "reviewer-general": "review-general",
    "reviewer-spec-audit": "review-spec",
    "reviewer-second-opinion": "review-secop",
    "review-merge": "general",
    "fixer": "general",
    "closer": "fast",
    "researcher": "research"
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
    "knowledgeDir": ".tf/knowledge",
    "clarifyDefault": true
  }
}
```

### Agent Files

Located at (project-local):
- `.pi/agents/*.md`

Each agent file has frontmatter:
```yaml
---
name: reviewer-general
description: General code review for tickets
model: openai-codex/gpt-5.1-codex-mini:high
tools: read, bash
---
```

## Execution Procedures

### Procedure: Verify Setup

Check complete installation status:

1. **Check extensions** (see Prerequisites Check above)

2. **Check agent files exist** (project-local):
   - `.pi/agents/reviewer-general.md`
   - `.pi/agents/reviewer-spec-audit.md`
   - `.pi/agents/reviewer-second-opinion.md`
   - `.pi/agents/review-merge.md`
   - `.pi/agents/fixer.md`
   - `.pi/agents/closer.md`

3. **Check workflow config exists** (project-local):
   - `.tf/config/settings.json`

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
| `models.reviewer-general` | `.pi/agents/reviewer-general.md` |
| `models.reviewer-spec-audit` | `.pi/agents/reviewer-spec-audit.md` |
| `models.reviewer-second-opinion` | `.pi/agents/reviewer-second-opinion.md` |
| `models.review-merge` | `.pi/agents/review-merge.md` |
| `models.fixer` | `.pi/agents/fixer.md` |
| `models.closer` | `.pi/agents/closer.md` |
| `models.researcher` | `.pi/agents/researcher.md` |
| `models.researcher-fetch` | `.pi/agents/researcher-fetch.md` |

**Prompt mapping (config key → prompt file)**:
| Config Key | Prompt File |
|------------|-------------|
| `models.planning` | `.pi/prompts/tf-plan.md`, `.pi/prompts/tf-plan-chain.md`, `.pi/prompts/tf-plan-consult.md`, `.pi/prompts/tf-plan-revise.md`, `.pi/prompts/tf-plan-review.md`, `.pi/prompts/tf-seed.md`, `.pi/prompts/tf-backlog.md`, `.pi/prompts/tf-backlog-ls.md`, `.pi/prompts/tf-spike.md`, `.pi/prompts/tf-backlog-from-openspec.md`, `.pi/prompts/tf-baseline.md`, `.pi/prompts/tf-followups.md` |
| `models.general` | `.pi/prompts/tf-next.md` |
| `models.config` | `.pi/prompts/tf-sync.md` |

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
model: kimi-coding/k2p5:high
```

---

### Procedure: Generate Model Aliases (Legacy)

**Note:** This is only relevant for legacy workflows not using `/chain-prompts`. With `/chain-prompts`, each phase has its own `model:` frontmatter.

If `pi-model-switch` is installed, suggest useful aliases:

**File**: `~/.pi/agent/extensions/model-switch/aliases.json`

**Suggested content**:
```json
{
  "tf-worker": [
    "kimi-coding/k2p5",
    "anthropic/claude-sonnet-4",
    "openai-codex/gpt-5.2"
  ],
  "tf-reviewer": [
    "openai-codex/gpt-5.1-codex-mini",
    "openai-codex/gpt-5.2-codex",
    "zai/glm-4.7"
  ],
  "tf-fast": [
    "zai/glm-4.7-flash",
    "google/gemini-2.5-flash"
  ],
  "tf-planning": [
    "openai-codex/gpt-5.2",
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
pi install npm:pi-prompt-template-model
pi install npm:pi-subagents

# Optional
pi install npm:pi-mcp-adapter
pi install npm:pi-review-loop
pi install npm:pi-model-switch  # Only for legacy workflows
```

## Output Format

Always provide clear status report:

```
## Extension Status
✓ pi-prompt-template-model (installed)
✓ pi-subagents (installed)
○ pi-model-switch (optional, not installed)
○ pi-mcp-adapter (optional, not installed)

## Agent Models Updated
- fixer: (unchanged) zai/glm-4.7:high

## Agent Models Unchanged
- reviewer-general: review-general (openai-codex/gpt-5.1-codex-mini)
- ...

## Prompt Models Updated
- tf-plan.md: planning (openai-codex/gpt-5.2)

## Prompt Models Unchanged
- tf.md: worker (kimi-coding/k2p5)

## Recommendations
- Consider installing pi-mcp-adapter for research capabilities
```

## Error Handling

- **Config not found**: Create from template
- **Agent file not found**: Skip with warning
- **Prompt file not found**: Skip with warning
- **Model format invalid**: Report and skip
- **Permission denied**: Suggest running with appropriate permissions
