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
│  (pi-prompt-    │    model: chutes/moonshotai/Kimi-K2.5-TEE:high
│   template-     │    skill: tf-workflow
│   model)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Switch   │  Switches to Kimi-K2.5
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
description: Implement ticket [tf-workflow +Kimi-K2.5]
model: chutes/moonshotai/Kimi-K2.5-TEE:high
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
| Planning | `/tf-plan`, `/tf-plan-consult`, `/tf-plan-revise`, `/tf-plan-review` | tf-planning |
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
| `implementer` | Write implementation | After research |
| `reviewer-general` | General code review | Parallel with others |
| `reviewer-spec-audit` | Spec compliance check | Parallel with others |
| `reviewer-second-opinion` | Alternative perspective | Parallel with others |
| `review-merge` | Consolidate reviews | After parallel reviews |
| `fixer` | Fix identified issues | After review merge |
| `closer` | Close ticket, summarize | After fixes complete |
| `researcher` | Research coordination | Research phase (optional) |
| `researcher-fetch` | Fetch specific sources | Research phase (parallel) |

---

## Knowledge Base

All planning and research artifacts are stored in `.pi/knowledge/`:

```
.pi/knowledge/
├── index.json                    # Registry of all topics
├── tickets/
│   └── {ticket-id}.md           # Per-ticket research
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
│     - Read .pi/ralph/AGENTS.md (lessons)                    │
│     - Read ticket + knowledge base                          │
├─────────────────────────────────────────────────────────────┤
│  1. Research (optional)                                     │
│     - MCP tools (context7, exa, grep_app)                   │
│     - Write to .pi/knowledge/tickets/{id}.md                │
├─────────────────────────────────────────────────────────────┤
│  2. Implement (model-switch)                                │
│     - Switch to implementer model                           │
│     - Write implementation.md                               │
├─────────────────────────────────────────────────────────────┤
│  3. Parallel Reviews (subagents)                            │
│     - reviewer-general                                      │
│     - reviewer-spec-audit                                   │
│     - reviewer-second-opinion                               │
├─────────────────────────────────────────────────────────────┤
│  4. Merge Reviews (model-switch)                            │
│     - Switch to cheap model                                 │
│     - Deduplicate issues                                    │
│     - Write review.md                                       │
├─────────────────────────────────────────────────────────────┤
│  5. Fix Issues                                              │
│     - Fix Critical/Major/Minor                              │
│     - Write fixes.md                                        │
├─────────────────────────────────────────────────────────────┤
│  6. Follow-ups (optional, --create-followups)               │
│     - Create tickets from Warnings/Suggestions              │
├─────────────────────────────────────────────────────────────┤
│  7. Close Ticket                                            │
│     - Add note to tk                                        │
│     - Close ticket                                          │
│     - Write close-summary.md                                │
├─────────────────────────────────────────────────────────────┤
│  8. Ralph Integration (if .pi/ralph/ exists)                │
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
Create .pi/knowledge/topics/seed-*/
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
Create .pi/knowledge/topics/baseline-*/
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

Models are configured in `workflows/tf/config.json`:

| Role | Default Model | Purpose |
|------|---------------|---------|
| implementer | Kimi-K2.5 / Sonnet | Deep reasoning for implementation |
| reviewer-* | GPT-5.1-mini | Fast, capable review |
| review-merge | GPT-5.1-mini | Deduplication and consolidation |
| fixer | GLM-4.7 | Cheap fixes |
| closer | GLM-4.7 | Cheap summarization |
| planning | GPT-5.1-mini | Planning workflows |
| config | GLM-4.7 | Setup and sync |

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

## Benefits of This Architecture

1. **DRY**: Workflow knowledge lives in one place per domain
2. **Auto Model Management**: Extension switches models via frontmatter
3. **Skill Injection**: `skill:` frontmatter forces skill loading
4. **Composability**: Skills can be combined and reused
5. **Maintainability**: Change logic in one place, all commands benefit
6. **Clarity**: Commands show their dependencies in autocomplete
