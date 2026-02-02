# Command Reference

Complete reference for all pi-ticketflow commands.

---

## Implementation Commands

### `/tf`

Execute the Implement → Review → Fix → Close workflow on a ticket.

```
/tf <ticket-id> [--auto] [--no-research] [--with-research] [--plan]
                 [--create-followups] [--simplify-tickets] [--final-review-loop]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `ticket-id` | Ticket identifier (e.g., `abc-123`) |
| `--auto` / `--no-clarify` | Run headless (no confirmation prompts) |
| `--no-research` | Skip research step |
| `--with-research` | Force enable research step |
| `--plan` / `--dry-run` | Show resolved chain and exit |
| `--create-followups` | Create follow-up tickets after review |
| `--simplify-tickets` | Run simplify on created tickets |
| `--final-review-loop` | Run `/review-start` after chain |

**Workflow:**
1. Re-anchor context (load AGENTS.md, lessons, ticket)
2. Research (optional, MCP tools)
3. Implement (model-switch to implementer model)
4. Parallel reviews (3 subagents)
5. Merge reviews (deduplication)
6. Fix issues
7. Follow-ups (optional)
8. Close ticket
9. Ralph integration (if active)

**Output Artifacts:**
- `implementation.md` - Implementation summary
- `review.md` - Consolidated review
- `fixes.md` - Fixes applied
- `close-summary.md` - Final summary
- `.pi/ralph/progress.md` - Updated (if Ralph active)

---

### `/ralph-start`

Start autonomous ticket processing loop.

```
/ralph-start [--max-iterations N]
```

Processes tickets until backlog is empty, max iterations reached, or error occurs.

**Features:**
- Re-anchors context per ticket
- Reads lessons from `.pi/ralph/AGENTS.md`
- Updates progress in `.pi/ralph/progress.md`
- Outputs `<promise>COMPLETE</promise>` on finish

---

## Planning Commands

### `/tf-plan`

Create a plan document from a request.

```
/tf-plan <request description>
```

Creates a structured plan in `.pi/knowledge/topics/plan-*/`:
- `plan.md` - Single source of truth
- Status starts as `draft`

**Example:**
```
/tf-plan Refactor auth flow to support OAuth + magic links
```

**Next Steps:**
```
/tf-plan-consult plan-auth-refactor
/tf-plan-revise plan-auth-refactor
/tf-plan-review plan-auth-refactor --high-accuracy
```

---

### `/tf-plan-consult`

Review a plan for gaps, ambiguities, and over-engineering.

```
/tf-plan-consult <plan-id-or-path>
```

Updates the same `plan.md` with Consultant Notes and sets status to `consulted`.

---

### `/tf-plan-revise`

Revise a plan based on consultant/reviewer feedback.

```
/tf-plan-revise <plan-id-or-path>
```

Updates the same `plan.md` with revisions and sets status to `revised`.

---

### `/tf-plan-review`

Validate a plan with high-accuracy checks.

```
/tf-plan-review <plan-id-or-path> [--high-accuracy]
```

Updates `plan.md` with PASS/FAIL status:
- `status: approved` if passes
- `status: blocked` if fails

---

## Research Commands

### `/tf-seed`

Capture an idea into structured seed artifacts.

```
/tf-seed <idea description>
```

**Creates artifacts in `.pi/knowledge/topics/seed-*/`:**
- `overview.md` - Summary + keywords
- `seed.md` - Vision, concept, features, questions
- `success-metrics.md` - How to measure success
- `assumptions.md` - Technical/user/business assumptions
- `constraints.md` - Limitations and boundaries
- `mvp-scope.md` - What's in/out of MVP
- `sources.md` - Source tracking

**Example:**
```
/tf-seed Build a CLI tool for managing database migrations
```

**Next Steps:**
```
/tf-backlog seed-build-a-cli
```

---

### `/tf-spike`

Research spike on a topic.

```
/tf-spike <topic> [--parallel]
```

**Modes:**
| Mode | Description |
|------|-------------|
| Sequential (default) | Query tools one by one |
| Parallel (`--parallel`) | Spawn 3 subagents simultaneously |

**Creates artifacts in `.pi/knowledge/topics/spike-*/`:**
- `overview.md` - Summary + quick answer
- `spike.md` - Full analysis with findings, options, recommendation
- `sources.md` - All URLs and tools used

**Example:**
```
/tf-spike "React Server Components vs Next.js App Router"
/tf-spike "PostgreSQL partitioning strategies" --parallel
```

---

### `/tf-baseline`

Capture status-quo of an existing project.

```
/tf-baseline [focus-area]
```

**Creates artifacts in `.pi/knowledge/topics/baseline-*/`:**
- `overview.md` - Project summary
- `baseline.md` - Architecture, components, entry points
- `risk-map.md` - Technical, dependency, knowledge risks
- `test-inventory.md` - Test structure and gaps
- `dependency-map.md` - Dependencies and external services
- `sources.md` - Files scanned

**Examples:**
```
/tf-baseline
/tf-baseline "authentication system"
```

**Next Steps:**
```
/tf-backlog baseline-myapp
```

---

## Ticket Creation Commands

### `/tf-backlog`

Create tickets from seeds, baselines, or plans.

```
/tf-backlog <seed|baseline|plan>
```

Generates 5-15 small tickets:
- **30 lines or less** in description
- **1-2 hours** estimated work
- **Self-contained** - no need to load full planning docs
- **Linked** via `external-ref` to source topic

**Ticket templates vary by source:**
- **Seed**: Includes context, acceptance criteria, constraints, seed reference
- **Baseline**: Includes risk/test context, baseline reference
- **Plan**: Includes plan context, work plan reference

**Examples:**
```
/tf-backlog seed-build-a-cli
/tf-backlog baseline-myapp
/tf-backlog plan-auth-rewrite
```

**Output:**
- Tickets created in `tk`
- `backlog.md` written to topic directory

---

### `/tf-backlog-ls`

List backlog status and tickets.

```
/tf-backlog-ls [topic-id-or-path]
```

**Without topic:** Lists all seed/baseline/plan topics with backlog status
**With topic:** Shows full backlog table + summary

**Example:**
```
/tf-backlog-ls
/tf-backlog-ls seed-build-a-cli
```

---

### `/tf-followups`

Create follow-up tickets from review warnings/suggestions.

```
/tf-followups <review-path-or-ticket-id>
```

Creates tickets from:
- **Warnings** - Technical debt (should address)
- **Suggestions** - Improvements (nice to have)

Both are out of scope for the original ticket.

**Example:**
```
/tf-followups ./review.md
/tf-followups abc-1234
```

---

### `/tf-from-openspec`

Create tickets from an OpenSpec change.

```
/tf-from-openspec <change-id-or-path>
```

Reads OpenSpec artifacts:
- `tasks.md` (required)
- `proposal.md`, `design.md` (for context)

Creates tickets tagged with `openspec` and linked via `external-ref`.

**Example:**
```
/tf-from-openspec auth-pkce-support
/tf-from-openspec openspec/changes/auth-pkce-support/
```

---

## Configuration Commands

### `/tf-sync`

Sync configuration from `config.json` to agent and prompt files.

```
/tf-sync
```

Updates `model:` frontmatter in all agent and prompt files based on `workflows/tf/config.json`.

---

## CLI Reference

The `tf` CLI is installed during setup and provides utilities for workflow management.

### Global Install (CLI at `~/.local/bin/tf`)

```bash
# Setup
tf setup                          # Interactive install + extensions + MCP

# Sync
tf sync                           # Sync models from config

# Diagnostics
tf doctor                         # Preflight checks

# Backlog
irf backlog-ls [topic]             # List backlog status

# Track changes
tf track <path>                   # Append to files_changed.txt

# Ralph Loop
tf ralph init                     # Create .pi/ralph/ directory
tf ralph status                   # Show current loop state
tf ralph reset                    # Clear progress
tf ralph reset --keep-lessons     # Clear progress, keep lessons
tf ralph lessons                  # Show lessons learned
tf ralph lessons prune 20         # Keep only last 20 lessons

# AGENTS.md Management
tf agentsmd init                  # Create minimal AGENTS.md
tf agentsmd status                # Show AGENTS.md overview
tf agentsmd validate              # Check for bloat, stale paths
tf agentsmd fix                   # Auto-fix common issues
```

### Project Install (CLI at `.pi/bin/tf`)

Use `./.pi/bin/tf` instead of `irf` for project installs.

```bash
./.pi/bin/tf setup
./.pi/bin/tf sync
./.pi/bin/tf ralph init
```
