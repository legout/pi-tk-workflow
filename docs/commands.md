# Command Reference

Complete reference for all pi-tk-workflow commands.

---

## Implementation Commands

### `/irf`

Execute the Implement → Review → Fix → Close workflow on a ticket.

```
/irf <ticket-id> [--auto] [--no-research] [--with-research] [--plan]
                 [--create-followups] [--simplify-tickets] [--final-review-loop]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `ticket-id` | Ticket identifier (e.g., `ABC-123`) |
| `--auto` / `--no-clarify` | Run headless (no confirmation prompts) |
| `--no-research` | Skip research step |
| `--with-research` | Force enable research step |
| `--plan` / `--dry-run` | Show resolved chain and exit |
| `--create-followups` | Create follow-up tickets after review |
| `--simplify-tickets` | Run simplify on created tickets |
| `--final-review-loop` | Run `/review-start` after chain |

**Workflow:**
1. Research (optional, MCP tools)
2. Implement (model-switch to implementer model)
3. Parallel reviews (3 subagents)
4. Merge reviews (deduplication)
5. Fix issues
6. Follow-ups (optional)
7. Close ticket

---

## Planning Commands

### `/irf-plan`

Create a plan document from a request.

```
/irf-plan <request>
```

Creates a structured plan in `.pi/knowledge/plans/`.

---

### `/irf-plan-consult`

Gap detection and edits in an existing plan.

```
/irf-plan-consult <plan-id>
```

---

### `/irf-plan-revise`

Apply feedback to a plan.

```
/irf-plan-revise <plan-id>
```

---

### `/irf-plan-review`

Validate a plan with high accuracy.

```
/irf-plan-review <plan-id> [--high-accuracy]
```

---

### `/irf-seed`

Capture an idea into seed artifacts.

```
/irf-seed <idea>
```

Creates structured artifacts in `.pi/knowledge/topics/<topic>/`:
- `seed.md` - Core idea
- `mvp-scope.md` - Minimum viable scope
- `success-metrics.md` - How to measure success

---

### `/irf-backlog`

Create tickets from seeds, baselines, or plans.

```
/irf-backlog <seed|baseline|plan>
```

Generates small, self-contained tickets (30 lines or less, 1-2 hours work).

---

### `/irf-backlog-ls`

List backlog status and tickets.

```
/irf-backlog-ls [topic]
```

---

### `/irf-spike`

Research spike on a topic.

```
/irf-spike <topic> [--parallel]
```

| Flag | Description |
|------|-------------|
| `--parallel` | Use parallel subagents for research |

---

### `/irf-baseline`

Capture project baseline (brownfield analysis).

```
/irf-baseline [focus-area]
```

Documents current state for future reference.

---

### `/irf-followups`

Create follow-up tickets from review warnings.

```
/irf-followups <review-path>
```

---

### `/irf-from-openspec`

Bridge from OpenSpec to tickets.

```
/irf-from-openspec <change-id>
```

Converts OpenSpec changes into implementation tickets.

---

## Configuration Commands

### `/irf-sync`

Sync configuration from `config.json` to agent and prompt files.

```
/irf-sync
```

Updates `model:` frontmatter in all agent and prompt files based on `workflows/implement-review-fix-close/config.json`.

**CLI equivalent:** `./bin/irf sync`

---

## Ralph Loop Commands

### `/ralph-start`

Start autonomous ticket processing loop.

```
/ralph-start [--max-iterations N]
```

Processes tickets until:
- Backlog is empty
- Max iterations reached
- Unrecoverable error occurs

**Features:**
- Re-anchors context per ticket
- Reads lessons from `.pi/ralph/AGENTS.md`
- Updates progress in `.pi/ralph/progress.md`
- Outputs `<promise>COMPLETE</promise>` on finish

---

## CLI Reference

The `./bin/irf` script provides additional utilities:

```bash
# Setup
./bin/irf setup                    # Interactive install + extensions + MCP

# Sync
./bin/irf sync                     # Sync models from config

# Diagnostics
./bin/irf doctor                   # Preflight checks

# Backlog
./bin/irf backlog-ls               # List backlog status

# Ralph Loop
./bin/irf ralph init               # Create .pi/ralph/ directory
./bin/irf ralph status             # Show current loop state
./bin/irf ralph reset              # Clear progress
./bin/irf ralph reset --keep-lessons  # Clear progress, keep lessons
./bin/irf ralph lessons            # Show lessons learned
./bin/irf ralph lessons prune 20   # Keep only last 20 lessons
```

---

## Flag Reference

| Flag | Applies To | Description |
|------|------------|-------------|
| `--auto` / `--no-clarify` | `/irf` | Run without confirmation prompts |
| `--no-research` | `/irf` | Skip research step |
| `--with-research` | `/irf` | Force research step |
| `--plan` / `--dry-run` | `/irf` | Show chain and exit |
| `--create-followups` | `/irf` | Create tickets from review warnings |
| `--simplify-tickets` | `/irf` | Run simplify on tickets |
| `--final-review-loop` | `/irf` | Run review loop after chain |
| `--parallel` | `/irf-spike` | Parallel research subagents |
| `--high-accuracy` | `/irf-plan-review` | Use stronger model |
| `--max-iterations N` | `/ralph-start` | Limit loop iterations |
