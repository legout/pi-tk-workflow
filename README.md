# pi-ticketflow

A comprehensive Pi workflow package for ticket-based development using the **Implement → Review → Fix → Close** cycle.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Implement│ → │  Review  │ → │   Fix    │ → │  Close   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

**Features:** Planning → Research → Ticket Creation → Implementation → Review → Autonomous Processing

---

## Installation

### Prerequisites

- [Pi](https://github.com/mariozechner/pi) installed and configured
- `tk` CLI in your PATH (ticket management)
- Language tools for your project

### Required Pi Extensions

```bash
pi install npm:pi-prompt-template-model  # Entry model switch via frontmatter
pi install npm:pi-model-switch           # Runtime model switching
pi install npm:pi-subagents              # Parallel reviewer subagents
```

### Quick Install (via curl)

```bash
# Global install (installs tf CLI to ~/.local/bin/)
curl -fsSL https://raw.githubusercontent.com/legout/pi-ticketflow/main/install.sh | bash -s -- --global

# Project install (current directory)
curl -fsSL https://raw.githubusercontent.com/legout/pi-ticketflow/main/install.sh | bash

# Project install (specific path)
curl -fsSL https://raw.githubusercontent.com/legout/pi-ticketflow/main/install.sh | bash -s -- --project /path/to/project
```

### Interactive Setup (Recommended after install)

After global install, the `tf` CLI is available:

```bash
# Interactive setup (installs extensions, configures MCP)
tf setup

# Sync models from config
tf sync
```

For project installs, use `./.pi/bin/tf` instead.

### Manual Install (from cloned repo)

```bash
# Clone first
git clone https://github.com/legout/pi-ticketflow.git
cd pi-ticketflow

# Global install (adds tf to ~/.local/bin/)
./install.sh --global

# Project install
./install.sh --project /path/to/project
```

### Installation Locations

| Component | Global Install | Project Install |
|-----------|---------------|-----------------|
| Agents, Skills, Prompts | `~/.pi/agent/` | `.pi/` |
| tf CLI | `~/.local/bin/tf` | `.pi/bin/tf` |
| Config | `~/.pi/agent/workflows/` | `.pi/workflows/` |

---

## Quick Start

### 1. Capture an Idea

```bash
/tf-seed "Build a CLI tool for managing database migrations"
```

Creates structured artifacts in `.pi/knowledge/topics/seed-build-a-cli/`.

### 2. Create Tickets

```bash
/tf-backlog seed-build-a-cli
```

Generates 5-15 small, actionable tickets (1-2 hours each) linked to your seed.

### 3. Run the IRF Workflow

```
/tf TICKET-123
```

Executes the full cycle: Research → Implement → Review → Fix → Close.

### 4. Run Autonomously (Optional)

```
/ralph-start --max-iterations 10
```

Processes tickets in a loop until backlog is empty.

---

## Workflows

Choose the workflow that matches your situation:

### 🌱 Greenfield Development (Seed → Backlog)
**When to use:** Starting a new project or feature from scratch

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│  /tf-seed  │ →  │ /tf-backlog │ →  │  /tf       │ →  │  /ralph  │
│  "Your idea"│    │   seed-*     │    │  <ticket>   │    │  -start  │
└─────────────┘    └──────────────┘    └─────────────┘    │(optional)│
                                                          └──────────┘
```

**Best for:** Exploring new ideas, prototyping, when requirements are fuzzy

1. Capture your idea with `/tf-seed`
2. Generate tickets with `/tf-backlog`
3. Implement with `/tf <ticket>`
4. (Optional) Run autonomously with `/ralph-start`

---

### 📋 Structured Planning (Plan → Consult → Revise → Review → Backlog)
**When to use:** Complex features requiring careful design, multiple stakeholders, or high-risk changes

```
┌────────────┐   ┌──────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────┐
│ /tf-plan  │ → │/tf-plan-    │ → │/tf-plan-   │ → │/tf-plan-   │ → │ /tf-backlog │ → │  /tf    │
│  "Feature" │   │   consult    │   │   revise    │   │   review    │   │    plan-*    │   │ <ticket> │
└────────────┘   └──────────────┘   └─────────────┘   └─────────────┘   └──────────────┘   └──────────┘
      ↓                                                                                           ↓
   draft                                                                                      approved
```

**Best for:** Production features, architecture changes, when you need rigor

1. Create plan with `/tf-plan`
2. Detect gaps with `/tf-plan-consult`
3. Apply feedback with `/tf-plan-revise`
4. Validate with `/tf-plan-review` (must be approved)
5. Create tickets with `/tf-backlog`
6. Implement with `/tf <ticket>`

---

### 🌱📋 Seed + Plan Combo (Exploration → Specification)
**When to use:** Complex new features where you want to explore first, then specify rigorously

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│  /tf-seed  │ →  │  /tf-plan  │ →  │   /tf-plan- │ →  │  /tf-backlog│ →  │   /tf   │
│  "Big idea" │    │ "Refined    │    │   review     │    │   plan-*     │    │ <ticket> │
│             │    │  from seed" │    │              │    │              │    │          │
└─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
   explore            specify              validate            tickets         implement
```

**Best for:** Major features, architectural changes, when you need both exploration AND rigor

1. **Explore** with `/tf-seed` - capture the vision, constraints, MVP scope
2. **Read** the seed artifacts (especially `seed.md`, `mvp-scope.md`, `constraints.md`)
3. **Specify** with `/tf-plan` - use the seed content as input for a rigorous plan
4. **Iterate** the plan through consult/revise/review if needed
5. Create tickets and implement

**Why combine them?**
- Seed captures the "why" and "what" (vision, scope, constraints)
- Plan captures the "how" (detailed work plan, acceptance criteria)
- Seed is quick and exploratory; Plan is rigorous and approval-gated

---

### 🏗️ Brownfield Development
**When to use:** Working with an existing codebase, refactoring, or improvements

```
┌──────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│/tf-baseline │ →  │ /tf-backlog │ →  │  /tf       │ →  │  /ralph  │
│  [focus]     │    │  baseline-*  │    │  <ticket>   │    │  -start  │
└──────────────┘    └──────────────┘    └─────────────┘    │(optional)│
                                                           └──────────┘
```

**Best for:** Refactoring, adding features to existing code, modernizing

1. Capture current state with `/tf-baseline` (analyzes risks, tests, dependencies)
2. Create improvement tickets with `/tf-backlog`
3. Implement with `/tf <ticket>`
4. (Optional) Run autonomously with `/ralph-start`

---

### 🔬 Research First
**When to use:** Evaluating technical approaches, unfamiliar technology, or making architectural decisions

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│ /tf-spike  │ →  │  /tf-seed  │ →  │ /tf-backlog │ →  │   /tf      │ →  │  /ralph  │
│  "Topic"    │    │  "Decision" │    │    seed-*    │    │   <ticket>  │    │  -start  │
│ [--parallel]│    │             │    │              │    │             │    │(optional)│
└─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘    └──────────┘
```

1. Research with `/tf-spike` (use `--parallel` for faster research)
2. Capture decision as `/tf-seed`
3. Create tickets with `/tf-backlog`
4. Implement with `/tf <ticket>`
5. (Optional) Run autonomously with `/ralph-start`

---

### 📄 OpenSpec Integration
**When to use:** Working from external specifications or product requirements documents

```
┌──────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│/tf-from-openspec│ →  │  (review     │ →  │   /tf      │ →  │  /ralph  │
│   <change-id>    │    │  tickets)    │    │   <ticket>  │    │  -start  │
└──────────────────┘    └──────────────┘    └─────────────┘    │(optional)│
                                                               └──────────┘
```

1. Import from OpenSpec with `/tf-from-openspec`
2. Review generated tickets in `tk`
3. Implement with `/tf <ticket>`
4. (Optional) Run autonomously with `/ralph-start`

**Setup:** Ensure OpenSpec change artifacts exist at `openspec/changes/{id}/tasks.md`

---

### 🔄 Review-Driven Improvements
**When to use:** Addressing technical debt or improvements found during code review

```
┌────────────┐    ┌─────────────┐    ┌────────────────┐    ┌──────────┐
│   /tf     │ →  │/tf-followups│ →  │     /tf       │ →  │  /ralph  │
│  <ticket>  │    │  review.md   │    │   <followup>   │    │  -start  │
└────────────┘    └─────────────┘    └────────────────┘    │(optional)│
     ↓                                                      └──────────┘
 review.md
 (Warnings +
Suggestions)
```

1. Run normal implementation with `/tf <ticket>`
2. Create follow-up tickets from review warnings with `/tf-followups`
3. Process follow-ups with `/tf <followup-ticket>`
4. (Optional) Run autonomously with `/ralph-start`

---

### Quick Reference

| Workflow | Use When | Key Commands |
|----------|----------|--------------|
| **Greenfield** | New projects/features (exploratory) | `/tf-seed` → `/tf-backlog` |
| **Seed + Plan** | Complex new features (explore → specify) | `/tf-seed` → `/tf-plan` → review → `/tf-backlog` |
| **Structured Planning** | Complex features, high-risk (rigorous) | `/tf-plan` → consult → revise → review |
| **Brownfield** | Existing code, refactoring | `/tf-baseline` → `/tf-backlog` |
| **Research First** | Unknown tech, architectural decisions | `/tf-spike` → `/tf-seed` |
| **OpenSpec** | External specifications | `/tf-from-openspec` |
| **Review-Driven** | Technical debt from reviews | `/tf-followups` |

---

## Commands Overview

### Core Implementation

| Command | Purpose |
|---------|---------|
| `/tf <ticket>` | Execute IRF workflow (Implement → Review → Fix → Close) |
| `/ralph-start` | Start autonomous ticket processing loop |

### Planning & Design

| Command | Purpose |
|---------|---------|
| `/tf-plan <request>` | Create structured implementation plan |
| `/tf-plan-consult <plan>` | Review plan for gaps and ambiguities |
| `/tf-plan-revise <plan>` | Apply consultant/reviewer feedback |
| `/tf-plan-review <plan>` | High-accuracy validation (PASS/FAIL) |

### Research & Discovery

| Command | Purpose |
|---------|---------|
| `/tf-seed <idea>` | Capture greenfield idea with MVP scope, constraints, metrics |
| `/tf-spike <topic>` | Research technical topic (sequential or `--parallel`) |
| `/tf-baseline [focus]` | Document brownfield codebase (risks, tests, dependencies) |

### Ticket Creation

| Command | Purpose |
|---------|---------|
| `/tf-backlog <topic>` | Generate tickets from seed/baseline/plan |
| `/tf-backlog-ls [topic]` | List backlog status and ticket counts |
| `/tf-followups <review>` | Create tickets from review Warnings/Suggestions |
| `/tf-from-openspec <change>` | Import tickets from OpenSpec changes |

### Configuration

| Command | Purpose |
|---------|---------|
| `/tf-sync` | Sync models from config.json to all agents |

See [docs/commands.md](docs/commands.md) for complete reference with all flags and options.

---

## Architecture

This package uses a **skill-centric** architecture:

```
skills/              # Domain expertise (reusable)
  tf-workflow/      # Core implementation workflow
  tf-planning/      # Research & planning activities
  tf-config/        # Setup & configuration
  ralph/             # Autonomous loop orchestration

prompts/             # Command entry points (thin wrappers)
  irf.md             # References tf-workflow skill
  tf-seed.md        # References tf-planning skill
  ...

agents/              # Subagent execution units
  implementer.md
  reviewer-*.md
  fixer.md
  closer.md
```

When you type a command:
1. Extension reads `model:` and `skill:` frontmatter
2. Switches to specified model
3. Injects skill content into context
4. Executes command

See [docs/architecture.md](docs/architecture.md) for details.

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

Topics are automatically linked to tickets via `external-ref`.

---

## Configuration

Models are configured in `workflows/tf/config.json`:

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
# Global install
tf sync

# Project install
./.pi/bin/tf sync

# Or via Pi prompt
/tf-sync
```

See [docs/configuration.md](docs/configuration.md) for full setup options.

---

## Ralph Loop (Autonomous Processing)

Ralph enables autonomous ticket processing with:

- **Re-anchoring**: Fresh context per ticket
- **Lessons Learned**: Persistent wisdom in `.pi/ralph/AGENTS.md`
- **Progress Tracking**: External state survives resets

```bash
# After global install:
tf ralph init          # Initialize Ralph
tf ralph status        # Check status
tf ralph lessons       # View lessons

# After project install:
./.pi/bin/tf ralph init
./.pi/bin/tf ralph status

# Start loop (in Pi)
/ralph-start --max-iterations 50
```

See [docs/ralph.md](docs/ralph.md) for the complete guide.

---

## Project Structure

```
pi-ticketflow/
├── agents/                 # Subagent definitions
├── skills/                 # Domain expertise
├── prompts/                # Command entry points
├── workflows/              # Workflow configurations
├── bin/tf                 # CLI tool
├── install.sh              # Installation script
└── docs/                   # Documentation
```

---

## Documentation

- **[docs/commands.md](docs/commands.md)** - Complete command reference
- **[docs/architecture.md](docs/architecture.md)** - How it works
- **[docs/ralph.md](docs/ralph.md)** - Autonomous processing
- **[docs/configuration.md](docs/configuration.md)** - Setup and models
- **[docs/workflows.md](docs/workflows.md)** - Detailed workflow guides
