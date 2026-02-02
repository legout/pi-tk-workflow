# Architecture

How pi-tk-workflow is structured and how it works.

---

## Overview

pi-tk-workflow uses a **skill-centric** architecture where:

- **Skills** contain domain expertise and procedures
- **Commands** are thin wrappers with `model:` and `skill:` frontmatter
- **Agents** are execution units spawned by skills for parallel work

---

## Component Hierarchy

```
User types: /irf ABC-123
         │
         ▼
┌─────────────────┐
│  Extension      │  Reads frontmatter:
│  (pi-prompt-    │    model: chutes/moonshotai/Kimi-K2.5-TEE:high
│   template-     │    skill: irf-workflow
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
│  Skill Injection│  Injects skills/irf-workflow/SKILL.md
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
│  Skill Procedures│ Follow IRF workflow:
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
| `irf-workflow` | Core implementation | Re-anchor, Research, Implement, Review, Fix, Close |
| `irf-planning` | Research & planning | Seed capture, Backlog generation, Research spike |
| `irf-config` | Setup & maintenance | Verify setup, Sync models, Check MCP |
| `ralph` | Autonomous loop | Initialize, Start loop, Extract lessons |

### Skill Structure

```markdown
---
name: irf-workflow
description: Core IRF implementation workflow
---

# IRF Workflow Skill

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
description: Implement ticket [irf-workflow +Kimi-K2.5]
model: chutes/moonshotai/Kimi-K2.5-TEE:high
skill: irf-workflow
---

# /irf

Execute the IRF workflow for ticket: $@

Follow the **IRF Workflow Skill** procedures.
```

### Autocomplete Display

With the `pi-prompt-template-model` extension, commands show skill and model:

```
/irf              Implement ticket [irf-workflow +Kimi-K2.5]
/irf-plan         Create plan [irf-planning +codex-mini]
/irf-sync         Sync config [irf-config +GLM-4.7]
/ralph-start      Autonomous loop [ralph]
```

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

## Workflow Flow

### `/irf` Flow (Standard)

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN AGENT                                                 │
├─────────────────────────────────────────────────────────────┤
│  0. Research (optional, sequential or parallel)             │
│  1. Implement (model-switch to implementer model)           │
├─────────────────────────────────────────────────────────────┤
│  2. SUBAGENT: Parallel Reviews                              │
│     ├─ reviewer-general                                     │
│     ├─ reviewer-spec-audit                                  │
│     └─ reviewer-second-opinion                              │
├─────────────────────────────────────────────────────────────┤
│  3. Merge reviews (model-switch to cheap model)             │
│  4. Fix issues (same cheap model)                           │
│  5. Follow-ups (optional, --create-followups)               │
│  6. Close ticket                                            │
│  7. Final review loop (optional, --final-review-loop)       │
│  8. Simplify tickets (optional, --simplify-tickets)         │
│  9. Learn & Track (updates .pi/ralph/ if active)            │
└─────────────────────────────────────────────────────────────┘
```

### Planning Flow

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

---

## Model Strategy

Models are configured in `workflows/implement-review-fix-close/config.json`:

| Role | Default Model | Purpose |
|------|---------------|---------|
| implementer | Kimi-K2.5 / Sonnet | Deep reasoning for implementation |
| reviewer-* | GPT-5.1-mini | Fast, capable review |
| review-merge | GPT-5.1-mini | Deduplication and consolidation |
| fixer | GLM-4.7 | Cheap fixes |
| closer | GLM-4.7 | Cheap summarization |
| planning | GPT-5.1-mini | Planning workflows |
| config | GLM-4.7 | Setup and sync |

Run `/irf-sync` after editing config to apply changes.

---

## Knowledge Base

Workflows write artifacts to a knowledge base:

```
.pi/knowledge/
├── topics/
│   └── <topic>/
│       ├── seed.md
│       ├── mvp-scope.md
│       └── success-metrics.md
├── plans/
│   └── <plan>.md
├── tickets/
│   └── <ticket>.md
└── index.json
```

Tickets can reference planning docs in their descriptions for traceability.

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
