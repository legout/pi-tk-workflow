# Getting Started

## Prerequisites

- [`pi`](https://github.com/mariozechner/pi)
- `tk` ticket CLI in `PATH`
- Python 3.9+
- `uvx` (recommended installer/runtime)

## Install

```bash
uvx --from git+https://github.com/legout/pi-ticketflow tf install --global
```

Alternative (legacy installer script):

```bash
curl -fsSL https://raw.githubusercontent.com/legout/pi-ticketflow/main/install.sh | bash -s -- --global
```

## Global Setup

Configure Pi extensions and optional MCP/web search integration:

```bash
tf setup
```

Typical required extensions:

```bash
pi install npm:pi-prompt-template-model
pi install npm:pi-model-switch
pi install npm:pi-subagents
```

## Project Setup

In each project where you want TF workflow assets:

```bash
cd /path/to/project
tf init
tf sync
```

This creates/updates:

- `.pi/agents`, `.pi/prompts`, `.pi/skills`
- `.tf/config`, `.tf/knowledge`, `.tf/ralph`

## First End-to-End Run

1. Capture idea/context:

```bash
/tf-seed "Build a CLI tool for managing database migrations"
```

2. Generate backlog from the seed:

```bash
/tf-backlog <seed-topic-id>
```

Use the topic id returned by `/tf-seed` (for example, `seed-build-a-cli-tool`).

3. Execute one ticket:

```bash
/tf <ticket-id>
```

4. Optional autonomous execution:

```bash
/ralph-start --max-iterations 10
```

## Common Next Commands

- `/tf-next` - get next ready ticket
- `/tf-plan-chain "<request>"` - run full plan consult/revise/review loop
- `/tf-tags-suggest --apply` - fill missing `component:*` tags
- `/tf-deps-sync --apply` - align dependency edges
- `tf doctor` - diagnose environment/config issues

## Where to Go Next

- Command details: [`commands.md`](commands.md)
- Workflow selection: [`workflows.md`](workflows.md)
- Configuration tuning: [`configuration.md`](configuration.md)
- Architecture: [`architecture.md`](architecture.md)
