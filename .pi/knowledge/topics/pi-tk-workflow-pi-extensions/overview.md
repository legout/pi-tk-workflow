# Pi usage and extensions in pi-tk-workflow

## Pi workflow context
- **pi-tk-workflow** packages a Pi workflow for `/implement-review-fix-close`, bundling agent markdown files and prompt templates to install under `~/.pi/agent` or `<project>/.pi` (README.md, workflows/implement-review-fix-close/README.md).
- The prompt template (`prompts/irf.md` and `prompts/irf-lite.md`) drives the chain using the **`subagent`** tool and reads config from `.pi/workflows/implement-review-fix-close/config.json` and/or `~/.pi/agent/workflows/implement-review-fix-close/config.json` to decide research, reviewer, fixer, and closer steps. It uses `workflow.knowledgeDir` (default `.pi/knowledge`) for research storage.

## Extensions referenced by the repo
- **Required extensions** (README.md, bin/irf):
  - `pi-subagents` — provides the `subagent` tool used to run parallel reviews.
  - `pi-model-switch` — provides the `switch_model` tool for on-the-fly model changes in lite workflows.
- **Optional extensions** (README.md, bin/irf):
  - `pi-review-loop` — referenced by the `--final-review-loop` flag in the prompt (runs `/review-start`).
  - `pi-mcp-adapter` — enables MCP tool access for research steps.
- `bin/irf setup` installs these extensions via `pi install` and uses `-l` for project-local installs.

## Workflow variants
- **Original workflows** (`/irf`, `/irf-seed`, etc.) use subagents for most steps.
- **Lite workflows** (`/irf-lite`, `/irf-seed-lite`, etc.) use `pi-model-switch` to reduce subagent usage by ~70%.

## MCP integration
- `bin/irf setup` can write MCP configuration to `<target>/.pi/mcp.json` or `~/.pi/agent/mcp.json` with servers for **context7**, **exa**, **grep_app**, and optionally **ZAI web search/reader/vision** (requires `ZAI_API_KEY`).
- MCP config sets `settings.toolPrefix` to `short` and uses per-server headers when keys are supplied.

## Extension background (from prior repo research)
- **pi-subagents**: Based on the pi-mono Subagent Example extension that runs parallel or chained Pi sub-processes with isolated context.
- **pi-model-switch**: Adds a `switch_model` tool to list, search, and switch models at runtime. Supports aliases for common model choices.
- **pi-mcp-adapter**: Adds an `mcp` proxy tool and expects servers in `~/.pi/agent/mcp.json`.
- **pi-review-loop**: Provides a review loop for iterative code review after the main chain completes.
