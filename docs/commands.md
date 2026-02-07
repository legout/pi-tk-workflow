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
3. Implement (model-switch to worker model)
4. Parallel reviews (3 subagents)
5. Merge reviews (deduplication)
6. Fix issues
7. Follow-ups (optional)
8. Close ticket
9. Ralph integration (if active)

**Output Artifacts (written under `.tf/knowledge/tickets/<ticket-id>/`):**
- `research.md` - Ticket research (if any)
- `implementation.md` - Implementation summary
- `review.md` - Consolidated review
- `fixes.md` - Fixes applied
- `followups.md` - Follow-up tickets (if created)
- `close-summary.md` - Final summary
- `chain-summary.md` - Artifact index
- `files_changed.txt` - Tracked changed files
- `ticket_id.txt` - Ticket ID
- `.tf/ralph/progress.md` - Updated (if Ralph active)

**Close step behavior:**
- Stages and commits only files listed in `files_changed.txt` before closing the ticket.

---

### `/tf-next`

Print the next open and ready ticket id.

```
/tf-next
```

**Behavior:**
- If `.tf/ralph/config.json` exists and defines `ticketQuery`, that command is used.
- Otherwise falls back to: `tk ready | head -1 | awk '{print $1}'`.

Outputs a single ticket id or "No ready tickets found.".

---

### `/ralph-start`

Start autonomous ticket processing loop.

```
/ralph-start [--max-iterations N]
```

Processes tickets until backlog is empty, max iterations reached, or error occurs.

**Features:**
- Re-anchors context per ticket
- Reads lessons from `.tf/ralph/AGENTS.md`
- Updates progress in `.tf/ralph/progress.md`
- Outputs `<promise>COMPLETE</promise>` on finish

---

## Planning Commands

### `/tf-plan`

Create a plan document from a request.

```
/tf-plan <request description>
```

Creates a structured plan in `.tf/knowledge/topics/plan-*/`:
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

**Creates artifacts in `.tf/knowledge/topics/seed-*/`:**
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

**Creates artifacts in `.tf/knowledge/topics/spike-*/`:**
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

**Creates artifacts in `.tf/knowledge/topics/baseline-*/`:**
- `overview.md` - Project summary
- `baseline.md` - Architecture, components, entry points
- `risk-map.md` - Technical, dependency, knowledge risks
- `test-inventory.md` - Test structure and gaps
- `dependency-map.md` - Dependencies and external services
- `existing-tickets.md` - Current tickets (from `tk` when available)
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
/tf-backlog <seed|baseline|plan> [--no-deps] [--no-component-tags] [--no-links]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--no-deps` | Skip automatic dependency inference |
| `--no-component-tags` | Skip automatic component tag suggestion |
| `--no-links` | Skip automatic linking of related tickets |

Generates appropriately-sized tickets to cover the scope (could be 1 ticket for a small change, or many for a large refactor). Skips duplicates already listed in `backlog.md` or `existing-tickets.md`:
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
/tf-backlog seed-build-a-cli --no-component-tags
/tf-backlog baseline-myapp --no-deps --no-component-tags --no-links
```

**Output:**
- Tickets created in `tk`
- Dependencies inferred for plan work plans (applied via `tk dep`)
- `backlog.md` written to topic directory

**Component Tag Assignment:**
`/tf-backlog` uses the shared `tf_cli.component_classifier` module to automatically
assign `component:*` tags based on keyword matching in ticket titles and descriptions.
This ensures consistency with `/tf-tags-suggest`, which uses the same classifier.

**Fallback Workflow:**
When inference is incomplete or you used opt-out flags, correct with:
```
/tf-tags-suggest --apply    # Add missing component tags (if --no-component-tags used)
/tf-deps-sync --apply       # Sync parent/child dependencies (if --no-deps used)
tk link CHILD PARENT        # Manual linking if needed (if --no-links used)
```

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

### `/tf-tags-suggest`

Suggest missing `component:*` tags for open tickets.

```
/tf-tags-suggest [--apply] [--status open|in_progress|all] [--limit N]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--apply` | Apply suggested tags to ticket files |
| `--status` | Filter tickets (default: open,in_progress) |
| `--limit` | Limit number of tickets processed |

**Purpose:**
Component tags enable safe parallel scheduling in Ralph. Run this after `/tf-backlog` if tickets lack component tags.

**Shared Classifier:**
This command uses the same `tf_cli.component_classifier` module as `/tf-backlog`,
ensuring consistent `component:*` suggestions whether tags are assigned during
backlog creation or via explicit suggestion.

**Example:**
```
/tf-tags-suggest
/tf-tags-suggest --apply
/tf-tags-suggest --apply --status open
```

---

### `/tf-deps-sync`

Sync parent-child relationships into ticket `deps`.

```
/tf-deps-sync [--apply] [--status open|in_progress|all]
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--apply` | Apply missing parent deps using `tk dep` |
| `--status` | Filter tickets (default: open,in_progress) |

**Purpose:**
Ensures parent tickets are reflected in `deps` for proper sequencing. Run this after `/tf-backlog` if dependencies look incomplete.

**Example:**
```
/tf-deps-sync
/tf-deps-sync --apply
/tf-deps-sync --apply --status all
```

**Manual fallback:**
If automatic sync misses a dependency, link manually:
```
tk link CHILD-123 PARENT-456
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

### `/tf-backlog-from-openspec`

Create backlog tickets from an OpenSpec change and infer dependencies.

```
/tf-backlog-from-openspec <change-id-or-path>
```

Reads OpenSpec artifacts:
- `tasks.md` (required)
- `proposal.md`, `design.md` (for context)

Creates tickets tagged with `openspec`, linked via `external-ref`, and applies dependencies from task ordering/headings.

**Example:**
```
/tf-backlog-from-openspec auth-pkce-support
/tf-backlog-from-openspec openspec/changes/auth-pkce-support/
```

---

## Knowledge Base Commands

### `tf kb`

Manage the knowledge base (topics, seeds, plans, spikes) via the CLI.

```
tf kb ls [--json] [--type <type>] [--archived] [--knowledge-dir <path>]
tf kb show <topic-id> [--json] [--knowledge-dir <path>]
tf kb index [--json] [--knowledge-dir <path>]
tf kb validate [--json] [--knowledge-dir <path>]
tf kb rebuild-index [--dry-run] [--json] [--knowledge-dir <path>]
tf kb archive <topic-id> [--reason TEXT] [--knowledge-dir <path>]
tf kb restore <topic-id> [--knowledge-dir <path>]
tf kb delete <topic-id> [--knowledge-dir <path>]
```

**Commands:**

| Command | Description |
|---------|-------------|
| `ls` | List all knowledge base topics from index.json |
| `show` | Show details for a specific topic |
| `index` | Show index status and statistics |
| `validate` | Validate KB integrity (missing files, orphans, duplicates) |
| `rebuild-index` | Regenerate index.json from filesystem |
| `archive` | Move a topic to archive (removes from index) |
| `restore` | Restore an archived topic back to active |
| `delete` | Permanently delete a topic (active or archived) |

**Global Options:**

| Option | Description |
|--------|-------------|
| `--json` | Output in JSON format |
| `--knowledge-dir <path>` | Use specific knowledge directory |

**Examples:**

```bash
# List all topics
tf kb ls

# List only seed topics
tf kb ls --type seed

# Include archived topics in listing
tf kb ls --archived

# Show topic details
tf kb show seed-build-a-cli

# Validate knowledge base integrity
tf kb validate

# Preview index rebuild without writing
tf kb rebuild-index --dry-run

# Archive a topic with reason
tf kb archive old-topic --reason "Superseded by new design"

# Restore archived topic
tf kb restore old-topic

# Permanently delete a topic
tf kb delete old-topic
```

**Validation Checks:**

The `validate` command detects:
- **Missing files** - Index entries referencing non-existent files
- **Orphan directories** - Topic directories not in index
- **Duplicate IDs** - Multiple index entries with same topic ID

---

## Priority Reclassification Commands

### `/tf-priority-reclassify` (Prompt) / `tf new priority-reclassify` (CLI)

Review and reclassify ticket priorities according to the P0–P4 rubric.

**CLI Usage:**
```
tf new priority-reclassify [--apply] [--ids <id1,id2,...>] [--ready] [--status <status>] [--tag <tag>]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `--apply` | Apply priority changes (default is dry-run) |
| `--yes` | Skip confirmation prompt (required with `--apply` in non-interactive mode) |
| `--max-changes N` | Maximum number of tickets to modify (safety cap) |
| `--force` | Apply changes even for ambiguous/unknown classifications |
| `--ids <id1,id2,...>` | Comma-separated list of ticket IDs to process |
| `--ready` | Process all ready tickets |
| `--status <status>` | Filter by ticket status |
| `--tag <tag>` | Filter by tag |
| `--include-closed` | Include closed tickets in processing (default: excluded) |
| `--include-unknown` | Include tickets with unknown/ambiguous priority in output |
| `--json` | Output results as JSON for scripting |
| `--report` | Write audit report to `.tf/knowledge/priority-reclassify-{timestamp}.md` |

**P0–P4 Priority Rubric:**

| Label | Numeric | Name | Description |
|-------|---------|------|-------------|
| **P0** | 0 | Critical | System down, data loss, security breach, blocking all work |
| **P1** | 1 | High | Major feature, significant bug affecting users, performance degradation |
| **P2** | 2 | Normal | Standard product features, routine enhancements (default) |
| **P3** | 3 | Low | Engineering quality, dev workflow improvements, tech debt |
| **P4** | 4 | Minimal | Code cosmetics, refactors, docs polish, test typing |

**Classification Keywords:**

The rubric uses keyword matching on ticket titles, descriptions, and tags:

| Priority | Indicators |
|----------|------------|
| P0 | `security`, `vulnerability`, `CVE`, `exploit`, `breach`, `XSS`, `injection`, `data loss`, `corruption`, `outage`, `crash`, `OOM`, `deadlock`, `GDPR`, `legal`, `compliance violation` |
| P1 | `user-facing`, `customer reported`, `regression`, `broken`, `release blocker`, `milestone`, `launch`, `slow`, `timeout`, `memory leak`, `wrong results`, `calculation error` |
| P2 | `feature`, `implement`, `add support`, `enhancement`, `API`, `webhook`, `export`, `import`, `integration` |
| P3 | `refactor`, `cleanup`, `tech debt`, `architecture`, `DX`, `dev workflow`, `build time`, `CI/CD`, `metrics`, `logging`, `tracing`, `monitoring`, `test coverage` |
| P4 | `typo`, `formatting`, `lint`, `style`, `naming`, `cosmetic`, `docs`, `README`, `comments`, `docstrings`, `type hints`, `mypy`, `typing` |

**Examples:**

```bash
# Dry-run on ready tickets (shows what would change)
/tf-priority-reclassify --ready

# Apply changes to ready tickets with confirmation
tf new priority-reclassify --ready --apply

# Process specific tickets
tf new priority-reclassify --ids abc-123,def-456 --apply --yes

# Filter by tag
tf new priority-reclassify --tag bug --apply

# Output as JSON for scripting
tf new priority-reclassify --ready --json

# Generate audit report
tf new priority-reclassify --ready --apply --report
```

**Customizing Classification Rules:**

The rubric is defined in `tf_cli/priority_reclassify_new.py`:
- `RUBRIC` dict - keyword definitions for each priority level
- `TAG_MAP` - tag-to-priority mappings (tags take precedence)
- `TYPE_DEFAULTS` - fallback priorities by ticket type

To extend the rubric, edit these dictionaries in the source file.

---

## Configuration Commands

### `/tf-sync`

Sync configuration from `config/settings.json` to agent and prompt files.

```
/tf-sync
```

Updates `model:` frontmatter in all agent and prompt files based on `config/settings.json`.

---

## CLI Reference

The `tf` CLI is a small Python shim that provides utilities for workflow management.
Install it with uvx (recommended) or via the legacy `install.sh`.

```bash
uvx --from https://github.com/legout/pi-ticketflow tf install --global
```

### Global Install (CLI at `~/.local/bin/tf`)

```bash
# Install/refresh CLI shim
tf install --global               # Explicit global install (default)

# Setup
tf setup                          # Interactive install + extensions + MCP

# Project scaffolding
tf init                           # Create .tf/ directories in the project

# Sync
tf sync                           # Sync models from config

# Update
tf update                         # Download latest agents/skills/prompts

# Diagnostics
tf doctor                         # Preflight checks

# Queue
tf next                           # Print next open and ready ticket id

# Backlog
tf backlog-ls [topic]             # List backlog status

# Track changes
tf track <path>                   # Append to files_changed.txt

# Knowledge Base Management
tf kb ls [--json] [--type <type>] [--archived]  # List topics
tf kb show <topic-id> [--json]                  # Show topic details
tf kb index [--json]                            # Show index status
tf kb validate [--json]                         # Validate KB integrity
tf kb rebuild-index [--dry-run] [--json]        # Rebuild index from filesystem
tf kb archive <topic-id> [--reason TEXT]        # Archive a topic
tf kb restore <topic-id>                        # Restore archived topic
tf kb delete <topic-id>                         # Permanently delete topic

# Ralph Loop
tf ralph init                     # Create .tf/ralph/ directory
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

### Project Initialization (Workflow Files)

The `tf` CLI is installed globally. To install TF workflow files (agents/prompts/skills) into a project:

```bash
cd /path/to/project
tf init

# After editing .tf/config/settings.json
tf sync
```
