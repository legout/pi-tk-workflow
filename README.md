# pi-tk-workflow

A reusable Pi workflow package for ticket implementation:

**Implement → Review → Fix → Close**

This package bundles the agents, prompts, and workflow config used by the `/irf` and `/irf-lite` commands.

---

## What's included

```
agents/
  implementer.md
  reviewer-general.md
  reviewer-spec-audit.md
  reviewer-second-opinion.md
  review-merge.md
  fixer.md
  closer.md
  researcher.md
  researcher-fetch.md
  simplifier.md
  simplify-ticket.md
  irf-planner.md

prompts/
  # Implementation workflows
  irf.md                    # Original (6-8 subagents)
  irf-lite.md               # Simplified (3 subagents) ← Recommended

  # Planning workflows - Original
  irf-seed.md
  irf-backlog.md
  irf-spike.md
  irf-baseline.md
  irf-followups.md
  irf-from-openspec.md

  # Planning workflows - Lite (no subagents) ← Recommended
  irf-seed-lite.md
  irf-backlog-lite.md
  irf-spike-lite.md
  irf-baseline-lite.md
  irf-followups-lite.md
  irf-from-openspec-lite.md

  # Utilities
  irf-sync.md

workflows/implement-review-fix-close/
  config.json
  README.md

docs/
  subagent-simplification.md  # Analysis of subagent reduction
```

---

## Workflow Variants

This package provides two variants for each workflow: **original** (more subagents) and **lite** (fewer subagents, more reliable).

### Implementation Workflows

| Command | Subagents | Description |
|---------|-----------|-------------|
| `/irf <ticket>` | 6-8 | Original full chain |
| `/irf-lite <ticket>` | 3 | **Recommended** - Uses model-switch |

### Planning Workflows

| Command | Subagents | Lite Equivalent |
|---------|-----------|-----------------|
| `/irf-seed <idea>` | 1 | `/irf-seed-lite` (0) |
| `/irf-backlog <seed>` | 1 | `/irf-backlog-lite` (0) |
| `/irf-spike <topic>` | 4 | `/irf-spike-lite` (0-3) |
| `/irf-baseline [focus]` | 1 | `/irf-baseline-lite` (0) |
| `/irf-followups <review>` | 1 | `/irf-followups-lite` (0) |
| `/irf-from-openspec <id>` | 1 | `/irf-from-openspec-lite` (0) |

**Recommendation:** Use `-lite` variants for better reliability. See `docs/subagent-simplification.md` for the full analysis.

---

## Prerequisites

- Pi installed and configured
- Ticket CLI: `tk` in PATH
- Language tools you intend to use (see workflow README)

### Required Pi extensions

For `-lite` workflows (recommended):
```bash
pi install npm:pi-subagents      # For parallel reviews
pi install npm:pi-model-switch   # For on-the-fly model switching
```

For original workflows:
```bash
pi install npm:pi-subagents
```

### Optional extensions

```bash
pi install npm:pi-review-loop    # Post-chain review with /review-start
pi install npm:pi-mcp-adapter    # MCP tools for research step
```

### Optional MCP servers

For research steps, install the MCP adapter and configure servers:

```bash
pi install npm:pi-mcp-adapter
```

Available MCP servers:
- context7 - documentation search
- exa - web search
- grep_app - code search
- zai web search / zai web reader / zai vision (requires API key)

> Tip: Run `./bin/irf setup` to install extensions and configure MCP interactively.

---

## Installation

### Interactive setup (recommended)

```bash
./bin/irf setup
```

This guides you through:
- global vs project install
- optional extensions
- MCP server configuration + API keys

### Global install (files only)

```bash
./install.sh --global
```

Installs into:
- `~/.pi/agent/agents`
- `~/.pi/agent/prompts`
- `~/.pi/agent/workflows/implement-review-fix-close`

### Project install (files only)

```bash
./install.sh --project /path/to/project
```

Installs into:
- `/path/to/project/.pi/agents`
- `/path/to/project/.pi/prompts`
- `/path/to/project/.pi/workflows/implement-review-fix-close`

---

## Usage

### Implementation Workflows

```bash
# Recommended - fewer subagents, more reliable
/irf-lite <ticket-id> [--auto] [--no-research] [--with-research]

# Original - full subagent chain
/irf <ticket-id> [flags]
```

### Planning Workflows (Lite - Recommended)

```bash
/irf-seed-lite <idea>                  # Capture idea into seed artifacts
/irf-backlog-lite <seed-path>          # Create tickets from seed
/irf-spike-lite <topic> [--parallel]   # Research spike
/irf-baseline-lite [focus]             # Capture brownfield status quo
/irf-followups-lite <review-path>      # Create follow-up tickets
/irf-from-openspec-lite <change-id>    # Bridge from OpenSpec
```

### Planning Workflows (Original)

```bash
/irf-seed <idea>
/irf-backlog <seed-path>
/irf-spike <topic>
/irf-baseline [focus]
/irf-followups <review-path>
/irf-from-openspec <change-id>
```

### Flags

| Flag | Description |
|------|-------------|
| `--auto` / `--no-clarify` | Run headless (no confirmation prompts) |
| `--no-research` | Skip research step |
| `--with-research` | Force enable research step |
| `--parallel` | Use parallel subagents for research (/irf-spike-lite only) |

---

## CLI

### Commands

```bash
./bin/irf setup   # Interactive install + extensions + MCP
./bin/irf sync    # Sync models from config into agent files
./bin/irf doctor  # Preflight checks for tools and extensions
```

### Ralph Loop Commands

```bash
./bin/irf ralph init           # Create .pi/ralph/ directory structure
./bin/irf ralph status         # Show current loop state and statistics
./bin/irf ralph reset          # Clear progress and lessons
./bin/irf ralph reset --keep-lessons  # Clear progress, keep lessons
./bin/irf ralph lessons        # Show lessons learned
./bin/irf ralph lessons prune 20      # Keep only last 20 lessons
```

### Starting a Ralph Loop

After initializing with `./bin/irf ralph init`, start the loop in Pi:

```
/ralph-start [--max-iterations 50]
```

Or use the built-in `ralph_loop` tool for custom orchestration.

### Updating models

Edit `workflows/implement-review-fix-close/config.json` and run:

```bash
/irf-sync
# or
./bin/irf sync
```

---

## Architecture

### `/irf-lite` flow (recommended)

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN AGENT                                                 │
├─────────────────────────────────────────────────────────────┤
│  0. Research (optional, sequential, no subagent)            │
│  1. Implement (model-switch to implementer model)           │
├─────────────────────────────────────────────────────────────┤
│  2. SUBAGENT: Parallel Reviews ← Only subagent step         │
│     ├─ reviewer-general                                     │
│     ├─ reviewer-spec-audit                                  │
│     └─ reviewer-second-opinion                              │
├─────────────────────────────────────────────────────────────┤
│  3. Merge reviews (model-switch to cheap model)             │
│  4. Fix issues (same cheap model)                           │
│  5. Close ticket                                            │
│  6. Learn & Track (updates .pi/ralph/ if active)            │
└─────────────────────────────────────────────────────────────┘
```

**Ralph-Ready**: Automatically loads lessons from `.pi/ralph/AGENTS.md` and tracks progress.

### Planning workflows (lite)

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN AGENT                                                 │
├─────────────────────────────────────────────────────────────┤
│  1. model-switch to planning model (cheap)                  │
│  2. Execute planning task inline                            │
│  3. Write artifacts to knowledge base                       │
│  4. [spike only, --parallel] Optional parallel research     │
└─────────────────────────────────────────────────────────────┘
```

### `/irf` flow (original)

```
researcher (subagent)
    └─ 3× researcher-fetch (parallel sub-subagents)
         ↓
implementer (subagent)
         ↓
┌─ reviewer-general ──────┐
├─ reviewer-spec-audit ───┼─ (parallel subagents)
└─ reviewer-second-opinion┘
         ↓
review-merge (subagent)
         ↓
fixer (subagent)
         ↓
closer (subagent)
```

---

## Key Features

### Ralph-Ready by Default

`/irf-lite` is designed for autonomous operation:

- **Re-anchoring**: Reads `AGENTS.md` and `.pi/ralph/AGENTS.md` at start
- **Lessons Learned**: Synthesizes and appends lessons after each ticket
- **Progress Tracking**: Updates `.pi/ralph/progress.md` automatically
- **Promise Sigil**: Outputs `<promise>TICKET_XXX_COMPLETE</promise>` for loop detection

Works standalone or in a Ralph loop—no configuration needed.

### Small, Self-Contained Tickets

Planning workflows (`/irf-backlog-lite`, `/irf-from-openspec-lite`) create:

- **30 lines or less** per ticket description
- **1-2 hours** estimated work
- **Self-contained context** - no need to load full planning docs
- **Summarized constraints** from original specs

---

## Subagent Comparison

| Workflow | Original | Lite | Reduction |
|----------|----------|------|-----------|
| `/irf` | 6-8 | 3 | ~60% |
| `/irf-seed` | 1 | 0 | 100% |
| `/irf-backlog` | 1 | 0 | 100% |
| `/irf-spike` | 4 | 0-3 | 25-100% |
| `/irf-baseline` | 1 | 0 | 100% |
| `/irf-followups` | 1 | 0 | 100% |
| `/irf-from-openspec` | 1 | 0 | 100% |
| **Total (worst case)** | 14-17 | 3-6 | **~70%** |

---

## Ralph Loop (Autonomous Processing)

The Ralph Loop enables autonomous ticket processing with re-anchoring and lessons learned.

### Concept

```
┌──────────────────────────────────────────────────────────────┐
│  RALPH LOOP                                                  │
├──────────────────────────────────────────────────────────────┤
│  while tickets remain:                                       │
│    1. RE-ANCHOR: Read .pi/ralph/AGENTS.md (lessons learned)  │
│    2. PICK: Get next ready ticket from backlog               │
│    3. EXECUTE: Run /irf-lite <ticket> --auto                 │
│    4. LEARN: Append lessons to .pi/ralph/AGENTS.md           │
│    5. TRACK: Update .pi/ralph/progress.md                    │
│    6. PROMISE: Output <promise>COMPLETE</promise> when done  │
└──────────────────────────────────────────────────────────────┘
```

### Files

```
.pi/ralph/
├── AGENTS.md      # Lessons learned (read by implementer for re-anchoring)
├── progress.md    # Loop state and ticket history
└── config.json    # Loop configuration (max iterations, queries, etc.)
```

### Setup

```bash
# Initialize Ralph directory
./bin/irf ralph init

# Check status
./bin/irf ralph status

# Start loop in Pi
/ralph-start --max-iterations 50
```

### Key Principles

1. **Re-anchoring**: Each iteration starts fresh, reading lessons from `.pi/ralph/AGENTS.md`
2. **Lessons Learned**: The closer synthesizes discoveries and appends them for future iterations
3. **Progress Tracking**: External state in `.pi/ralph/progress.md` survives context resets
4. **Promise Sigil**: Loop terminates when `<promise>COMPLETE</promise>` is output

See `docs/ralph-loop.md` for usage guide and `docs/ralph-integration-plan.md` for implementation details.

---

## Notes

- Config is read at runtime by the prompt and agents
- Models are applied via `/irf-sync` (updates agent frontmatter)
- MCP config is written to `<target>/.pi/mcp.json` when you run `./bin/irf setup`
- `-lite` workflows write artifacts to cwd; original workflows use chain_dir
- Original agents (`irf-planner`, `researcher`, etc.) are kept as fallback

