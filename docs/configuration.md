# Configuration

Setting up pi-ticketflow, models, extensions, and MCP servers.

---

## Installation Methods

### Install with uvx (Recommended)

```bash
# Global install (installs shim to ~/.local/bin/tf)
uvx --from git+https://github.com/legout/pi-ticketflow tf install --global

# Local clone (development)
uvx --from . tf install
```

> Note: Some uvx versions require `git+https://...` instead of a plain URL.
> Once published to PyPI, this becomes: `uvx tf install`.

### Interactive Setup (Recommended)

```bash
# Global install
tf setup

# In each project
tf init
tf sync
```

(Project installs are deprecated; use the global `tf` CLI.)

Guides you through:
- Installing required/optional Pi extensions
- MCP server configuration + API keys
- Project scaffolding via `tf init`

### Manual Install (Legacy)

```bash
# Global install
./install.sh --global

# Project install
./install.sh --project /path/to/project
```

After a global install, run `tf init` in each project to scaffold `.tf/`.

---

## Required Extensions

Install these Pi extensions:

```bash
pi install npm:pi-prompt-template-model  # Entry model switch via frontmatter
pi install npm:pi-model-switch           # Runtime model switching
pi install npm:pi-subagents              # Parallel reviewer subagents
```

**Extension Roles:**

| Extension | When | Purpose |
|-----------|------|---------|
| `pi-prompt-template-model` | Command entry | Reads `model:` and `skill:` frontmatter, handles initial model switch |
| `pi-model-switch` | During workflow | Runtime switches between phases (implement → review → fix) |
| `pi-subagents` | During workflow | Spawns parallel reviewer subagents |

---

## Model Configuration

Models are configured in `config/settings.json`:

### Default Config

```json
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
      "model": "zai-org/GLM-4.7-Flash",
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
      "model": "openai-codex/gpt-5.3-codex",
      "thinking": "high",
      "description": "Strong model for specification compliance audit"
    },
    "review-secop": {
      "model": "google-antigravity/gemini-3-flash",
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
    "tf-plan-chain": "planning",
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
  }
}
```

### Model Strategy

| Role | Default Model | Purpose |
|------|---------------|---------|
| worker | kimi-coding/k2p5 | Deep reasoning for implementation |
| researcher | minimax/MiniMax-M2.1 | Fast research and information gathering |
| fast | zai-org/GLM-4.7-Flash | Cheapest model for quick tasks |
| general | zai/glm-4.7 | General-purpose admin tasks |
| review-general | openai-codex/gpt-5.1-codex-mini | General code review |
| review-spec | openai-codex/gpt-5.3-codex | Specification compliance audit |
| review-secop | google-antigravity/gemini-3-flash | Second-opinion review |
| planning | openai-codex/gpt-5.2 | Planning and specification |

### Applying Changes

After editing `.tf/config/settings.json`:

```bash
tf sync
# or (Pi prompt)
/tf-sync
```

This updates `model:` frontmatter in all agent and prompt files.

---

## Workflow Configuration

Additional workflow settings in `config/settings.json`:

```json
{
  "metaModels": { ... },
  "agents": { ... },
  "prompts": { ... },
  "workflow": {
    "enableResearcher": true,
    "researchParallelAgents": 3,
    "enableReviewers": ["reviewer-general", "reviewer-spec-audit", "reviewer-second-opinion"],
    "enableFixer": true,
    "enableCloser": true,
    "enableQualityGate": false,
    "failOn": [],
    "knowledgeDir": ".tf/knowledge",
    "escalation": {
      "enabled": false,
      "maxRetries": 3,
      "models": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      }
    }
  }
}
```

> Because `config/settings.json` is version-controlled, keep the `workflow.escalation` block there so the elevated defaults are tracked in the repo. Run `/tf-sync` (or `tf sync`) after editing `.tf/config/settings.json` to sync any overrides from the repository config.

| Setting | Default | Description |
|---------|---------|-------------|
| `enableResearcher` | `true` | Run research step before implementation |
| `researchParallelAgents` | `3` | Number of parallel research fetches (1 = sequential) |
| `enableReviewers` | `["reviewer-general", ...]` | Which reviewers to run (empty = skip) |
| `enableFixer` | `true` | Run fix step after review |
| `enableCloser` | `true` | Close ticket after completion |
| `enableQualityGate` | `false` | Block closing if issues found |
| `failOn` | `[]` | Severities that block closing |
| `knowledgeDir` | `.tf/knowledge` | Where to store knowledge artifacts |
| `escalation.enabled` | `false` | Enable retry escalation on quality gate blocks |
| `escalation.maxRetries` | `3` | Maximum blocked attempts before skipping ticket |
| `escalation.models.fixer` | `null` | Escalation model for fixer (null = use base) |
| `escalation.models.reviewerSecondOpinion` | `null` | Escalation model for 2nd opinion reviewer |
| `escalation.models.worker` | `null` | Escalation model for implementation worker |

### Escalation Configuration

When `escalation.enabled` is `true`, blocked tickets are retried with escalated models:

| Attempt | Fixer | Reviewer-2nd-Opinion | Worker |
|---------|-------|---------------------|--------|
| 1 | Base model | Base model | Base model |
| 2 | Escalation model | Base model | Base model |
| 3+ | Escalation model | Escalation model | Escalation model (if configured) |

Each override targets a specific workflow role: `models.fixer` feeds the fixer agent (`agents.fixer`), `models.reviewerSecondOpinion` feeds the second-opinion reviewer (`reviewer-second-opinion`), and `models.worker` feeds the implementation worker (`agents.worker`). Set any override to `null` to fall back to the base model, and keep `escalation.enabled` false when you need the previous, non-escalated behavior.

**Example escalation config**:

```json
{
  "workflow": {
    "escalation": {
      "enabled": true,
      "maxRetries": 3,
      "models": {
        "fixer": "openai-codex/gpt-5.3-codex",
        "reviewerSecondOpinion": "openai-codex/gpt-5.2-codex",
        "worker": null
      }
    }
  }
}
```

See [Retries and Escalation](./retries-and-escalation.md) for full details.

---

## Knowledge Base

Planning and research artifacts are stored in `knowledgeDir` (default: `.tf/knowledge/`):

```
.tf/knowledge/
├── index.json                    # Registry of all topics
├── tickets/
│   └── {ticket-id}.md           # Per-ticket research
└── topics/
    └── {topic-id}/
        ├── overview.md
        ├── seed.md|baseline.md|plan.md|spike.md
        ├── backlog.md
        └── ...
```

The knowledge base is automatically managed. You rarely need to edit it manually.

---

## MCP Configuration (Optional)

For research steps, install the MCP adapter:

```bash
pi install npm:pi-mcp-adapter
```

### Available MCP Servers

| Server | Purpose | Setup |
|--------|---------|-------|
| context7 | Documentation search | Built-in |
| exa | Web search | Requires API key |
| grep_app | Code search | Requires API key |
| zai-web-search | Web search | Requires API key |
| zai-web-reader | Page reading | Requires API key |
| zai-vision | Image analysis | Requires API key + Node.js |

> **Note:** `zai-vision` runs locally via `npx -y @z_ai/mcp-server` and requires Node.js with npx available. The `zai-web-search` and `zai-web-reader` servers remain remote URL-based services.

### MCP Config Location

MCP config is written globally to `~/.pi/agent/mcp.json` when you run `tf setup` (or `tf login`).

Example structure:

```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "@mcp/exa"],
      "env": {
        "EXA_API_KEY": "your-key-here"
      }
    }
  }
}
```

---

## Ralph Configuration

Ralph loop settings in `.tf/ralph/config.json`:

```json
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
  "completionCheck": "tk ready | grep -q .",
  "workflow": "/tf",
  "workflowFlags": "--auto",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "promiseOnComplete": true,
  "lessonsMaxCount": 50,
  "logLevel": "normal",
  "captureJson": false
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `maxIterations` | 50 | Total tickets to process |
| `maxIterationsPerTicket` | 5 | Retries per ticket before moving on |
| `ticketQuery` | `tk ready \| head -1` | Command to pick next ticket |
| `completionCheck` | `tk ready \| grep -q .` | Command to detect empty backlog |
| `workflow` | `/tf` | Command to run per ticket |
| `workflowFlags` | `--auto` | Flags for workflow |
| `sleepBetweenTickets` | 5000 | Ms to wait between tickets |
| `sleepBetweenRetries` | 10000 | Ms to wait before retrying when no ticket found |
| `promiseOnComplete` | true | Emit `<promise>COMPLETE</promise>` on completion |
| `lessonsMaxCount` | 50 | Max lessons before pruning |
| `sessionDir` | `~/.pi/agent/sessions` | Directory for Ralph session artifacts (Pi conversation logs) |
| `logLevel` | `normal` | Logging verbosity: `quiet`, `normal`, `verbose`, `debug` |
| `captureJson` | false | Capture Pi JSON mode output to `.tf/ralph/logs/{ticket}.jsonl` |

**Session Storage Notes:**

- **Default location**: `~/.pi/agent/sessions/` (Pi's standard session directory)
- **Legacy location**: `.tf/ralph/sessions/` (backward compatibility detected with warning)
- **Override env var**: `RALPH_FORCE_LEGACY_SESSIONS=1` forces use of legacy location
- If legacy directory exists and you haven't explicitly configured `sessionDir`, Ralph warns but uses the new default

---

## Optional Extensions

```bash
pi install npm:pi-review-loop    # Post-chain review with /review-start
```

---

## Verification

Check your setup:

```bash
tf doctor
```

Runs preflight checks for:
- Required extensions installed
- `tk` CLI available
- MCP servers configured (if applicable)

---

## Project Structure

After installation:

```
# Global install (Pi assets + CLI)
~/.pi/agent/
├── agents/
├── skills/
└── prompts/

~/.local/bin/tf

# Project (after `tf init` or project install)
.pi/
├── agents/
├── skills/
└── prompts/

# Pi extension config (optional)
.pi/mcp.json

.tf/
├── bin/
│   └── tf                # (if installed locally)
├── config/
│   └── settings.json
├── scripts/
│   └── tf_config.py
├── ralph/
│   ├── AGENTS.md
│   ├── progress.md
│   └── config.json
└── knowledge/
    ├── tickets/
    └── topics/
```

---

## Troubleshooting

### Extension not found

```bash
pi install npm:pi-prompt-template-model
# Restart pi
```

### Model not switching

- Verify `pi-prompt-template-model` installed (for entry switch)
- Verify `pi-model-switch` installed (for runtime switches)
- Check model ID is valid in config/settings.json
- Run `/tf-sync` after config changes

### Skill not loading

- Check skill is in `skills/{name}/SKILL.md`
- Verify frontmatter has `name:` and `description:`
- Run `pi` and check for skill loading errors

### MCP tools not available

- Verify `pi-mcp-adapter` installed
- Check `.pi/mcp.json` exists and is valid
- Verify API keys are set for external services

### Knowledge base not created

- Check `workflow.knowledgeDir` in config/settings.json
- Ensure write permissions in project directory
- Knowledge base is auto-created on first use
