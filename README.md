# pi-tk-workflow

A reusable Pi workflow package for ticket-based development using the **Implement → Review → Fix → Close** cycle.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Implement│ → │  Review  │ → │   Fix    │ → │  Close   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Installation

### Prerequisites

- [Pi](https://github.com/mariozechner/pi) installed and configured
- `tk` CLI in your PATH (ticket management)
- Language tools for your project (see workflow-specific docs)

### Required Pi Extensions

```bash
pi install npm:pi-prompt-template-model  # Entry model switch via frontmatter
pi install npm:pi-model-switch           # Runtime model switching
pi install npm:pi-subagents              # Parallel reviewer subagents
```

### Interactive Setup (Recommended)

```bash
./bin/irf setup
```

This guides you through global vs project install, optional extensions, and MCP configuration.

### Manual Install

```bash
# Global install (recommended)
./install.sh --global

# Project install
./install.sh --project /path/to/project
```

Files are installed to:
- **Global**: `~/.pi/agent/{agents,skills,prompts,workflows}/`
- **Project**: `.pi/{agents,skills,prompts,workflows}/`

---

## Quick Start

### 1. Create a Ticket

```bash
# Create a ticket using your ticket CLI
tk create "Add user authentication endpoint"
```

### 2. Run the IRF Workflow

```
/irf TICKET-123
```

This executes the full cycle:
1. **Research** (optional) - Gather context via MCP tools
2. **Implement** - Write code with model-switch to strong model
3. **Review** - Parallel subagents review the changes
4. **Fix** - Address issues with cheap model
5. **Close** - Mark ticket complete

### 3. Run Autonomously (Optional)

```
/ralph-start --max-iterations 10
```

Processes tickets in a loop until backlog is empty.

---

## Commands Overview

| Command | Purpose |
|---------|---------|
| `/irf <ticket>` | Execute IRF workflow on a ticket |
| `/irf-plan <request>` | Create a plan document |
| `/irf-seed <idea>` | Capture idea into seed artifacts |
| `/irf-backlog <seed>` | Create tickets from seed/baseline |
| `/irf-spike <topic>` | Research spike on a topic |
| `/irf-baseline [focus]` | Capture project baseline |
| `/irf-sync` | Sync models from config |
| `/ralph-start` | Start autonomous loop |

See [docs/commands.md](docs/commands.md) for complete reference.

---

## Architecture

This package uses a **skill-centric** architecture:

```
skills/              # Domain expertise (reusable)
  irf-workflow/      # Core implementation workflow
  irf-planning/      # Research & planning activities
  irf-config/        # Setup & configuration
  ralph/             # Autonomous loop orchestration

prompts/             # Command entry points (thin wrappers)
  irf.md             # References irf-workflow skill
  irf-plan.md        # References irf-planning skill
  ...

agents/              # Subagent execution units
  implementer.md
  reviewer-*.md
  fixer.md
  closer.md
```

When you type `/irf`:
1. Extension reads `model:` and `skill:` frontmatter
2. Switches to specified model
3. Injects skill content into context
4. Executes command

See [docs/architecture.md](docs/architecture.md) for details.

---

## Configuration

Models are configured in `workflows/implement-review-fix-close/config.json`:

```json
{
  "models": {
    "implementer": "chutes/moonshotai/Kimi-K2.5-TEE:high",
    "reviewer": "openai-codex/gpt-5.1-codex-mini",
    "fixer": "zai/glm-4.7"
  }
}
```

Apply changes with:

```bash
./bin/irf sync
# or
/irf-sync
```

See [docs/configuration.md](docs/configuration.md) for full setup options including MCP servers.

---

## Ralph Loop (Autonomous Processing)

Ralph enables autonomous ticket processing with:

- **Re-anchoring**: Fresh context per ticket
- **Lessons Learned**: Persistent wisdom in `.pi/ralph/AGENTS.md`
- **Progress Tracking**: External state survives resets

```bash
# Initialize Ralph directory
./bin/irf ralph init

# Start loop
/ralph-start --max-iterations 50

# Check status
./bin/irf ralph status
```

See [docs/ralph.md](docs/ralph.md) for the complete guide.

---

## Project Structure

```
pi-tk-workflow/
├── agents/                 # Subagent definitions
├── skills/                 # Domain expertise
├── prompts/                # Command entry points
├── workflows/              # Workflow configurations
├── bin/irf                 # CLI tool
├── install.sh              # Installation script
└── docs/                   # Documentation
```

---

## Next Steps

- **Commands**: See [docs/commands.md](docs/commands.md) for detailed command reference
- **Architecture**: See [docs/architecture.md](docs/architecture.md) to understand how it works
- **Ralph Loop**: See [docs/ralph.md](docs/ralph.md) for autonomous processing
- **Configuration**: See [docs/configuration.md](docs/configuration.md) for model setup
