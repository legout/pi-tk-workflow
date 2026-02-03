# Configuration

Setting up pi-ticketflow, models, extensions, and MCP servers.

---

## Installation Methods

### Interactive Setup (Recommended)

```bash
./bin/tf setup
```

Guides you through:
- Global vs project install
- Optional extensions
- MCP server configuration + API keys

### Manual Install

```bash
# Global install
./install.sh --global

# Project install
./install.sh --project /path/to/project
```

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

Models are configured in `workflows/tf/config.json`:

### Default Config

```json
{
  "models": {
    "implementer": "chutes/moonshotai/Kimi-K2.5-TEE:high",
    "reviewer": "openai-codex/gpt-5.1-codex-mini",
    "review-merge": "openai-codex/gpt-5.1-codex-mini",
    "fixer": "zai/glm-4.7",
    "closer": "zai/glm-4.7",
    "planning": "openai-codex/gpt-5.1-codex-mini",
    "config": "zai/glm-4.7"
  }
}
```

### Model Strategy

| Role | Recommended Model Type | Purpose |
|------|------------------------|---------|
| implementer | Strong (Kimi-K2.5, Sonnet) | Deep reasoning for implementation |
| reviewer-* | Fast, capable (GPT-5.1-mini) | Code review |
| review-merge | Cheap (GPT-5.1-mini) | Deduplication |
| fixer | Cheapest (GLM-4.7) | Apply fixes |
| closer | Cheapest (GLM-4.7) | Summarization |
| planning | Cheap, fast (GPT-5.1-mini) | Planning tasks |
| config | Cheapest (GLM-4.7) | Admin tasks |

### Applying Changes

After editing `config.json`:

```bash
./bin/tf sync
# or
/tf-sync
```

This updates `model:` frontmatter in all agent and prompt files.

---

## Workflow Configuration

Additional workflow settings in `config.json`:

```json
{
  "models": { ... },
  "workflow": {
    "enableResearcher": true,
    "researchParallelAgents": 1,
    "enableReviewers": ["reviewer-general", "reviewer-spec-audit", "reviewer-second-opinion"],
    "enableFixer": true,
    "enableCloser": true,
    "enableQualityGate": false,
    "failOn": ["Critical"],
    "knowledgeDir": ".pi/knowledge"
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `enableResearcher` | `true` | Run research step before implementation |
| `researchParallelAgents` | `1` | Number of parallel research fetches (1 = sequential) |
| `enableReviewers` | `["reviewer-general", ...]` | Which reviewers to run (empty = skip) |
| `enableFixer` | `true` | Run fix step after review |
| `enableCloser` | `true` | Close ticket after completion |
| `enableQualityGate` | `false` | Block closing if issues found |
| `failOn` | `["Critical"]` | Severities that block closing |
| `knowledgeDir` | `.pi/knowledge` | Where to store knowledge artifacts |

---

## Knowledge Base

Planning and research artifacts are stored in `knowledgeDir` (default: `.pi/knowledge/`):

```
.pi/knowledge/
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
| zai-vision | Image analysis | Requires API key |

### MCP Config Location

MCP config is written to `<target>/.pi/mcp.json` when you run `./bin/tf setup`.

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

Ralph loop settings in `.pi/ralph/config.json`:

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
  "lessonsMaxCount": 50
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

---

## Optional Extensions

```bash
pi install npm:pi-review-loop    # Post-chain review with /review-start
```

---

## Verification

Check your setup:

```bash
./bin/tf doctor
```

Runs preflight checks for:
- Required extensions installed
- `tk` CLI available
- MCP servers configured (if applicable)

---

## Project Structure

After installation:

```
# Global install
~/.pi/agent/
├── agents/
├── skills/
├── prompts/
└── workflows/
    └── tf/
        └── config.json

# Project install
.pi/
├── agents/
├── skills/
├── prompts/
├── workflows/
│   └── tf/
│       └── config.json
├── mcp.json              # (if configured)
├── ralph/                # (if initialized)
│   ├── AGENTS.md
│   ├── progress.md
│   └── config.json
└── knowledge/            # (auto-created)
    ├── index.json
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
- Check model ID is valid in config.json
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

- Check `workflow.knowledgeDir` in config.json
- Ensure write permissions in project directory
- Knowledge base is auto-created on first use
