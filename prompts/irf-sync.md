---
description: Sync IRF configuration [irf-config +GLM-4.7]
model: zai/glm-4.7
thinking: medium
skill: irf-config
---

# /irf-sync

Apply the workflow configuration and verify required extensions.

## Usage

```
/irf-sync
```

## Execution

Follow the **IRF Config Skill** procedures:

1. **Verify Setup** - Check extensions and agent files
2. **Sync Models** - Update agent and prompt files from config.json
3. **Report Status** - Show what's installed and updated

## What Gets Synced

### Extensions Checked

| Extension | Status | Install Command |
|-----------|--------|-----------------|
| pi-subagents | Required | `pi install npm:pi-subagents` |
| pi-model-switch | Required | `pi install npm:pi-model-switch` |
| pi-mcp-adapter | Optional | `pi install npm:pi-mcp-adapter` |
| pi-review-loop | Optional | `pi install npm:pi-review-loop` |

### Agent Models Updated

Config key → Agent file mapping:
- `models.implementer` → `agents/implementer.md`
- `models.reviewer-general` → `agents/reviewer-general.md`
- `models.reviewer-spec-audit` → `agents/reviewer-spec-audit.md`
- `models.reviewer-second-opinion` → `agents/reviewer-second-opinion.md`
- `models.review-merge` → `agents/review-merge.md`
- `models.fixer` → `agents/fixer.md`
- `models.closer` → `agents/closer.md`
- `models.researcher` → `agents/researcher.md`
- `models.researcher-fetch` → `agents/researcher-fetch.md`

### Prompt Models Updated

Config key → Prompt file mapping:
- `models.implementer` → `prompts/irf.md`, `prompts/irf-lite.md`
- `models.planning` → `prompts/irf-plan.md`, `prompts/irf-plan-consult.md`, `prompts/irf-plan-revise.md`, `prompts/irf-plan-review.md`, `prompts/irf-seed.md`, `prompts/irf-backlog.md`, `prompts/irf-backlog-ls.md`, `prompts/irf-spike.md`, `prompts/irf-from-openspec.md`, `prompts/irf-baseline.md`, `prompts/irf-followups.md`
- `models.config` → `prompts/irf-sync.md`

## Configuration Sources

Read and merge (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json` (project)
- `~/.pi/agent/workflows/implement-review-fix-close/config.json` (global)

## Output Example

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
- irf-plan.md: openai-codex/gpt-5.1-codex-mini → openai-codex/gpt-5.1-codex-mini:medium

## Recommendations
- Consider installing pi-mcp-adapter for research capabilities
```

## When to Run

- After editing `config.json`
- When setting up a new project
- After updating the pi-tk-workflow package
- When troubleshooting model-related issues
