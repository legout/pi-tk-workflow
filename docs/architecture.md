# Architecture

How pi-ticketflow is structured and how it works.

---

## Overview

pi-ticketflow uses a **skill-centric** architecture where:

- **Skills** contain domain expertise and procedures
- **Commands** are thin wrappers with `model:` and `skill:` frontmatter
- **Agents** are execution units spawned by skills for parallel work
- **Knowledge Base** stores planning and research artifacts

---

## Component Hierarchy

```
User types: /tf ABC-123
         │
         ▼
┌─────────────────┐
│  Extension      │  Reads frontmatter:
│  (pi-prompt-    │    model: kimi-coding/k2p5
│   template-     │    skill: tf-workflow
│   model)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Switch   │  Switches to kimi-coding/k2p5
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Skill Injection│  Injects skills/tf-workflow/SKILL.md
│                 │  into system prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Command Body   │  Executes: parse args, delegate to skill
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Skill Procedures│ Follow TF workflow:
│                 │   1. Re-anchor context
│                 │   2. Research (optional)
│                 │   3. Implement (model-switch)
│                 │   4. Review (subagents)
│                 │   5. Fix (model-switch)
│                 │   6. Close
└─────────────────┘
```

---

## Skills

Skills are the core expertise containers. They live in `skills/*/SKILL.md`.

### Available Skills

| Skill | Purpose | Key Procedures |
|-------|---------|----------------|
| `tf-workflow` | Core implementation | Re-anchor, Research, Implement, Review, Fix, Close |
| `tf-review` | Shared reviewer contract | Artifact resolution, findings format, severity accounting |
| `tf-planning` | Research & planning | Seed capture, Backlog generation, Plan lifecycle, Research spike, Baseline, Follow-ups, OpenSpec bridge |
| `tf-config` | Setup & maintenance | Verify setup, Sync models, Check MCP |
| `ralph` | Autonomous loop | Initialize, Start loop, Extract lessons, Progress tracking |

### Skill Structure

```markdown
---
name: tf-workflow
description: Core TF implementation workflow
---

# TF Workflow Skill

## Overview
Brief description of what this skill does.

## Procedures

### Procedure Name

**When to use**: Description

**Steps**:
1. Step one
2. Step two
   - Sub-step

**Tools**: List of tools used

**Outputs**: What gets produced
```

---

## Commands

Commands are thin wrappers in `prompts/*.md`. They specify:

1. **Model** - Which model to use via `model:` frontmatter
2. **Skill** - Which skill to inject via `skill:` frontmatter
3. **Invocation** - How to parse and delegate

### Example Command

```markdown
---
description: Implement ticket [tf-workflow]
model: kimi-coding/k2p5
skill: tf-workflow
---

# /tf

Execute the TF workflow for ticket: $@

Follow the **TF Workflow Skill** procedures.
```

### Command Categories

| Category | Commands | Skill |
|----------|----------|-------|
| Implementation | `/tf`, `/ralph-start` | tf-workflow, ralph |
| Planning | `/tf-plan`, `/tf-plan-chain`, `/tf-plan-consult`, `/tf-plan-revise`, `/tf-plan-review` | tf-planning |
| Research | `/tf-seed`, `/tf-spike`, `/tf-baseline` | tf-planning |
| Ticket Creation | `/tf-backlog`, `/tf-backlog-ls`, `/tf-followups`, `/tf-backlog-from-openspec` | tf-planning |
| Config | `/tf-sync` | tf-config |

---

## Agents

Agents are subagent definitions in `agents/*.md`. They are:

- **Execution units** spawned by skills for parallel work
- **Not skills** - they don't contain reusable expertise
- **Spawned with subagent tool** for isolation

### Agent Types

| Agent | Purpose | When Spawned |
|-------|---------|--------------|
| `reviewer-general` | General code review wrapper (shared `tf-review` skill) | Parallel with others |
| `reviewer-spec-audit` | Spec compliance wrapper (shared `tf-review` skill) | Parallel with others |
| `reviewer-second-opinion` | Alternate-perspective wrapper (shared `tf-review` skill) | Parallel with others |
| `review-merge` | Consolidate reviews | After parallel reviews |
| `fixer` | Fix identified issues | After review merge |
| `closer` | Close ticket, summarize | After fixes complete |
| `researcher` | Research coordination | Research phase (optional) |
| `researcher-fetch` | Fetch specific sources | Research phase (parallel) |

---

## Knowledge Base

All planning and research artifacts are stored in `.tf/knowledge/`:

```
.tf/knowledge/
├── index.json                    # Registry of all topics
├── tickets/
│   └── {ticket-id}/
│       ├── research.md           # Per-ticket research
│       ├── implementation.md
│       ├── review.md
│       ├── fixes.md
│       ├── followups.md
│       ├── close-summary.md
│       ├── chain-summary.md
│       ├── files_changed.txt
│       └── ticket_id.txt
└── topics/
    └── {topic-id}/
        ├── overview.md           # Summary + keywords
        ├── sources.md            # References and URLs
        ├── seed.md               # Greenfield ideas
        ├── baseline.md           # Brownfield analysis
        ├── plan.md               # Implementation plans
        ├── spike.md              # Research findings
        ├── backlog.md            # Generated tickets
        ├── mvp-scope.md          # What's in/out
        ├── risk-map.md           # Technical risks
        ├── test-inventory.md     # Test coverage
        └── dependency-map.md     # External dependencies
```

### Topic Types

| Prefix | Type | Created By | Purpose |
|--------|------|------------|---------|
| `seed-*` | Greenfield | `/tf-seed` | New ideas and features |
| `baseline-*` | Brownfield | `/tf-baseline` | Existing project analysis |
| `plan-*` | Plan | `/tf-plan` | Structured implementation plans |
| `spike-*` | Research | `/tf-spike` | Technology research |

### Linking Tickets to Topics

Tickets are linked to topics via `external-ref`:

```bash
tk create "Title" \
  --description "..." \
  --external-ref "seed-my-feature"
```

During implementation, the workflow reads the linked topic for context.

---

## Model Switching

Two extensions handle model switching:

### 1. pi-prompt-template-model (Entry)

Handles the **initial** model switch when you type a command.

- Reads `model:` frontmatter
- Switches to specified model
- Injects `skill:` content

### 2. pi-model-switch (Runtime)

Handles **runtime** model switches during workflow execution.

Used by skills to switch between phases:
- Implement (strong model) → Review merge (cheap model)
- Review merge → Fix (cheap model)
- Fix → Close (cheap model)

---

## Workflow Flows

### `/tf` Flow (Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN AGENT                                                 │
├─────────────────────────────────────────────────────────────┤
│  0. Re-anchor Context                                       │
│     - Read root AGENTS.md                                   │
│     - Read .tf/ralph/AGENTS.md (lessons)                    │
│     - Read ticket + knowledge base                          │
├─────────────────────────────────────────────────────────────┤
│  1. Research (optional)                                     │
│     - MCP tools (context7, exa, grep_app)                   │
│     - Write to .tf/knowledge/tickets/{id}/research.md       │
├─────────────────────────────────────────────────────────────┤
│  2. Implement (model-switch)                                │
│     - Switch to worker model                                │
│     - Write implementation.md (ticket artifact dir)         │
├─────────────────────────────────────────────────────────────┤
│  3. Parallel Reviews (subagents)                            │
│     - reviewer-general                                      │
│     - reviewer-spec-audit                                   │
│     - reviewer-second-opinion                               │
├─────────────────────────────────────────────────────────────┤
│  4. Merge Reviews (model-switch)                            │
│     - Switch to cheap model                                 │
│     - Deduplicate issues                                    │
│     - Write review.md (ticket artifact dir)                 │
├─────────────────────────────────────────────────────────────┤
│  5. Fix Issues                                              │
│     - Fix Critical/Major/Minor                              │
│     - Write fixes.md (ticket artifact dir)                  │
├─────────────────────────────────────────────────────────────┤
│  6. Follow-ups (optional, --create-followups)               │
│     - Create tickets from Warnings/Suggestions              │
├─────────────────────────────────────────────────────────────┤
│  7. Close Ticket                                            │
│     - Add note to tk                                        │
│     - Close ticket                                          │
│     - Write close-summary.md (ticket artifact dir)          │
├─────────────────────────────────────────────────────────────┤
│  8. Ralph Integration (if .tf/ralph/ exists)                │
│     - Update progress.md                                    │
│     - Extract lessons → AGENTS.md                           │
│     - Output <promise>TICKET_COMPLETE</promise>             │
└─────────────────────────────────────────────────────────────┘
```

### Planning Flows

#### Seed → Tickets

```
/tf-seed "Idea"
  ↓
Create .tf/knowledge/topics/seed-*/
  - seed.md, mvp-scope.md, success-metrics.md, etc.
  ↓
/tf-backlog seed-*
  ↓
Create tickets in tk (with external-ref: seed-*)
  ↓
/tf <ticket>
```

#### Baseline → Tickets

```
/tf-baseline [focus]
  ↓
Create .tf/knowledge/topics/baseline-*/
  - baseline.md, risk-map.md, test-inventory.md, etc.
  ↓
/tf-backlog baseline-*
  ↓
Create tickets from risks, test gaps, dependencies
  ↓
/tf <ticket>
```

#### Plan Lifecycle

```
/tf-plan "Feature"
  ↓
plan.md (status: draft)
  ↓
/tf-plan-consult → plan.md (status: consulted)
  ↓
/tf-plan-revise → plan.md (status: revised)
  ↓
/tf-plan-review → plan.md (status: approved/blocked)
  ↓
(if approved)
  ↓
/tf-backlog plan-*
  ↓
/tf <ticket>
```

---

## Model Strategy

Models are configured in `config/settings.json`:

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

Run `/tf-sync` after editing config to apply changes.

---

## Extension Requirements

### Required

```bash
pi install npm:pi-prompt-template-model  # Entry model switch
pi install npm:pi-model-switch           # Runtime model switch
pi install npm:pi-subagents              # Parallel reviews
```

### Optional

```bash
pi install npm:pi-review-loop    # Post-chain review
pi install npm:pi-mcp-adapter    # MCP tools for research
```

---

## Shared Modules (`tf`)

The canonical `tf` Python package provides reusable modules that skills can import to avoid repetitive inline scripts:

### component_classifier

Maps keywords in ticket titles/descriptions to component tags (`component:cli`, `component:api`, etc.).

**Used by:**
- `/tf-backlog` - Auto-assign component tags during ticket creation
- `/tf-tags-suggest` - Suggest missing component tags

**Example:**
```python
from tf.component_classifier import classify_components

result = classify_components("Add --version flag to CLI")
print(result.tags)  # ['component:cli']
```

### ticket_factory

Reusable functions for creating tickets during backlog generation. Eliminates repetitive inline Python scripts.

**Key Functions:**
- `TicketDef` - Define tickets with title, description, optional tags
- `score_tickets()` - Score by keyword (setup=10, implement=3, test=1)
- `create_tickets()` - Create via `tk create` with auto-component-tags
- `apply_dependencies()` - Apply `tk dep` (chain/phases modes)
- `apply_links()` - Link related tickets via `tk link`
- `write_backlog_md()` - Write `backlog.md` file

**Used by:**
- `/tf-backlog` - Create tickets from seed/baseline/plan
- `/tf-backlog-from-openspec` - Create tickets from OpenSpec changes

**Example:**
```python
from tf.ticket_factory import (
    TicketDef, create_tickets, score_tickets,
    apply_dependencies, write_backlog_md
)

tickets = [TicketDef(title="...", description="..."), ...]
scored = score_tickets(tickets)
created = create_tickets(scored, topic_id="seed-foo", mode="seed")
created = apply_dependencies(created, mode="chain")
write_backlog_md(created, topic_id="seed-foo")
```

See `docs/ticket_factory.md` for complete API documentation.

---

## Benefits of This Architecture

1. **DRY**: Workflow knowledge lives in one place per domain
2. **Auto Model Management**: Extension switches models via frontmatter
3. **Skill Injection**: `skill:` frontmatter forces skill loading
4. **Composability**: Skills can be combined and reused
5. **Maintainability**: Change logic in one place, all commands benefit
6. **Clarity**: Commands show their dependencies in autocomplete
7. **Shared Modules**: Common functionality in `tf` avoids repetitive inline scripts

---

## Web UI Namespace

- Canonical web app module: `tf/web/app.py`
- Compatibility shim: `tf_cli/web_ui.py`
- Canonical web assets: `tf/web/templates/`, `tf/web/static/`
- Legacy asset paths remain present for compatibility: `tf_cli/templates/`, `tf_cli/static/`
