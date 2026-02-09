# pi-ticketflow

> **Migration Notice:** The Python package namespace has changed from `tf_cli` to `tf`. The `tf_cli` package is now a compatibility shim and will be removed in version 0.5.0. See [Migration Guide](#migrating-from-tf_cli-to-tf) below and [docs/deprecation-policy.md](docs/deprecation-policy.md) for details.

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

### Install with uvx (recommended)

```bash
# Global install (installs shim to ~/.local/bin/tf)
uvx --from git+https://github.com/legout/pi-ticketflow tf install --global

# Local clone (development)
uvx --from . tf install

# Install with offline support (uvx + pip install)
uvx --from git+https://github.com/legout/pi-ticketflow tf install --global --force-local
```

> Note: The `git+` prefix is required for GitHub URLs with uvx.
> Use `--force-local` to also install locally via pip for offline/resilient operation.

### Quick Install (via curl, legacy)

```bash
# Global install (installs tf CLI to ~/.local/bin/)
curl -fsSL https://raw.githubusercontent.com/legout/pi-ticketflow/main/install.sh | bash -s -- --global
```

### Interactive Setup (Recommended after install)

After global install, the `tf` CLI is available:

```bash
# Global environment setup (extensions + MCP/web-search config)
tf setup

# In each project, install TF workflow assets + config/state
cd /path/to/project
tf init

# Sync models from project config into project-local agents/prompts
tf sync
```

### Manual Install (from cloned repo, legacy)

```bash
# Clone first
git clone https://github.com/legout/pi-ticketflow.git
cd pi-ticketflow

# Preferred (uvx)
uvx --from . tf install

# Legacy install.sh (curl-style)
./install.sh --global
```

### Installation Locations

| Component | Global Install | Project Install |
|-----------|---------------|-----------------|
| tf CLI shim | `~/.local/bin/tf` | - |
| Pi extensions + MCP/web-search config | `~/.pi/agent/` | - |
| TF agents, prompts, skills | - | `.pi/` |
| TF config + state (knowledge, ralph, etc.) | - | `.tf/` |

---

## Migrating from `tf_cli` to `tf`

The Python package namespace has changed from `tf_cli` to `tf`. The CLI command remains `tf` (unchanged), but Python imports should now use the `tf` package.

### Timeline

| Phase | Version | Behavior |
|-------|---------|----------|
| **Current** | 0.4.x | `tf/` is canonical; `tf_cli/` is a compatibility shim |
| **Deprecation** | 0.4.x | Opt-in warnings via `TF_CLI_DEPRECATION_WARN=1` |
| **Removal** | 0.5.0 | `tf_cli/` shim removed |

### Import Migration

```python
# Before (deprecated, removal in 0.5.0)
from tf_cli.ticket_factory import TicketDef
from tf_cli import get_version
from tf_cli.doctor import run_doctor

# After (preferred)
from tf.ticket_factory import TicketDef
from tf import get_version
from tf.doctor import run_doctor
```

### Enabling Deprecation Warnings

To see warnings when using the old `tf_cli` imports:

```bash
export TF_CLI_DEPRECATION_WARN=1
python -c "from tf_cli import get_version"  # Will emit DeprecationWarning
```

### Module Execution

The `tf` package now supports module execution:

```bash
# New capability
python -m tf --help
python -m tf doctor
```

### Full Details

See [docs/deprecation-policy.md](docs/deprecation-policy.md) for the complete deprecation policy, including:
- Full migration checklist
- Automated migration commands
- Rollback procedures

---

## Quick Start

### 1. Capture an Idea

```bash
/tf-seed "Build a CLI tool for managing database migrations"
```

Creates structured artifacts in `.tf/knowledge/topics/seed-build-a-cli/`.

### 2. Create Tickets

```bash
/tf-backlog seed-build-a-cli
```

Generates appropriately-sized tickets to cover the scope (1-2 hours each), linked to your seed. This could be 1 ticket for a tiny change or many for a large feature.

### 3. Run the TF Workflow

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

### 🧭 Vague Idea (Clarify → Spike → Seed → Plan/Backlog)
**When to use:** Very early ideation with major unknowns

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  /tf-seed  │ → │ /tf-spike  │ → │  /tf-seed  │ → │ /tf-plan?     │ → /tf-backlog
│  "idea+?"   │    │ "unknown"   │    │ "decision"  │    │ "specify"     │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
```

1. Capture the idea plus unknowns:
   ```
   /tf-seed "Build X (unknowns: pricing, auth, hosting)"
   ```
2. Spike the unknowns:
   ```
   /tf-spike "Pricing models for X"
   /tf-spike "Auth strategies for Y" --parallel
   ```
3. Capture the decision in a seed **and reference the spike ID**:
   ```
   /tf-seed "Build X using SSO + magic links based on spike-auth-strategy"
   ```
   Then add the spike docs to `sources.md` (manual):
   ```
   - .tf/knowledge/topics/spike-auth-strategy/spike.md
   ```
4. If the work is complex, create a plan and run the planning loop:
   ```
   /tf-plan "Implement X based on seed-build-x and spike-auth-strategy"
   /tf-plan-consult plan-build-x
   /tf-plan-revise plan-build-x
   /tf-plan-review plan-build-x --high-accuracy
   /tf-backlog plan-build-x
   ```
   If not complex, go straight to:
   ```
   /tf-backlog seed-build-x
   ```

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
┌────────────────────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│/tf-backlog-from-openspec  │ →  │  (review     │ →  │   /tf      │ →  │  /ralph  │
│   <change-id>             │    │  tickets)    │    │   <ticket>  │    │  -start  │
└────────────────────────────┘    └──────────────┘    └─────────────┘    │(optional)│
                                                                        └──────────┘
```

1. Import from OpenSpec with `/tf-backlog-from-openspec`
2. Review generated tickets in `tk`
3. Implement with `/tf <ticket>`
4. (Optional) Run autonomously with `/ralph-start`

Dependencies are inferred from task ordering/headings and applied with `tk dep`.

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
 review.md (from .tf/knowledge/tickets/<ticket>/)
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
| **Vague Idea** | Early ideation with major unknowns | `/tf-seed` → `/tf-spike` → `/tf-seed` → `/tf-plan?` → `/tf-backlog` |
| **Seed + Plan** | Complex new features (explore → specify) | `/tf-seed` → `/tf-plan` → review → `/tf-backlog` |
| **Structured Planning** | Complex features, high-risk (rigorous) | `/tf-plan` → consult → revise → review |
| **Brownfield** | Existing code, refactoring | `/tf-baseline` → `/tf-backlog` |
| **Research First** | Unknown tech, architectural decisions | `/tf-spike` → `/tf-seed` |
| **OpenSpec** | External specifications | `/tf-backlog-from-openspec` |
| **Review-Driven** | Technical debt from reviews | `/tf-followups` |

---

## Commands Overview

### Core Implementation

| Command | Purpose |
|---------|---------|
| `/tf <ticket>` | Execute TF workflow (Implement → Review → Fix → Close) |
| `/tf-next` | Print next open and ready ticket id |
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
| `/tf-backlog <topic>` | Generate tickets from seed/baseline/plan (plan deps inferred) |
| `/tf-backlog-ls [topic]` | List backlog status and ticket counts |
| `/tf-followups <review>` | Create tickets from review Warnings/Suggestions |
| `/tf-backlog-from-openspec <change>` | Import tickets from OpenSpec changes |
| `/tf-priority-reclassify` | Reclassify ticket priorities using P0–P4 rubric |

### Configuration

| Command | Purpose |
|---------|---------|
| `/tf-sync` | Sync models from config/settings.json to all agents |

See [docs/commands.md](docs/commands.md) for complete reference with all flags and options.

---

## Web Mode (Browser UI)

The Ticketflow TUI can be run in a web browser using Textual's `textual serve` command. This is useful for remote access or when you prefer a browser interface over a terminal.

### Prerequisites

The `textual` CLI is provided by the `textual-dev` package. Install it if you haven't already:

```bash
pip install textual-dev
```

### Running in Web Mode

**Installed CLI (recommended):**
```bash
textual serve --command "tf ui"
```

**Development fallback (from repo checkout):**
```bash
textual serve "python -m tf.ui"
```

> **Note:** CLI commands require the `--command` flag, while Python module invocations work directly.

### Accessing the UI

By default, the UI will be available at:
```
http://localhost:8000
```

The terminal will display the exact URL when the server starts.

### Customizing Host and Port

Use the standard `textual serve` flags to customize binding:

```bash
# Custom port
textual serve --command "tf ui" --port 8080

# Custom host (see Security Warning below)
textual serve --command "tf ui" --host 0.0.0.0
```

See `textual serve --help` for the complete list of available options.

### ⚠️ Security Warning: Public Binding

**The default localhost binding is the only officially supported configuration.**

If you bind to a non-localhost address (e.g., `0.0.0.0` or a public IP), be aware that:

- The UI will be accessible to anyone who can reach the network interface
- No authentication is provided by `textual serve`
- **Do not expose the UI publicly without additional security measures**

If you need remote access, consider these mitigations:
- Use an SSH tunnel instead of public binding
- Place a reverse proxy with authentication in front of the service
- Restrict access via firewall rules or VPN
- Only bind to specific, trusted network interfaces

### Session Lifecycle

When running in web mode:

- **The app runs in the terminal** where you started `textual serve`
- **Closing the browser tab does NOT stop the app** — the process continues running
- **Use Ctrl+C** in the terminal to shut down the server
- Each browser tab creates a new session; closing one tab doesn't affect others

This behavior differs from some web applications that terminate when the browser disconnects. The Textual app remains active until you explicitly stop it.

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
  tf.md              # References tf-workflow skill
  tf-seed.md        # References tf-planning skill
  ...

agents/              # Subagent execution units
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

Topics are automatically linked to tickets via `external-ref`.

---

## Priority Rubric (P0–P4)

Ticketflow uses a consistent P0–P4 priority classification system:

| Label | Numeric | Name | Description |
|-------|---------|------|-------------|
| **P0** | 0 | Critical | System down, data loss, security breach, blocking all work |
| **P1** | 1 | High | Major feature, significant bug affecting users, performance degradation |
| **P2** | 2 | Normal | Standard product features, routine enhancements (default) |
| **P3** | 3 | Low | Engineering quality, dev workflow improvements, tech debt |
| **P4** | 4 | Minimal | Code cosmetics, refactors, docs polish, test typing |

### Classification Examples

| Scenario | Priority | Rationale |
|----------|----------|-----------|
| Security vulnerability in auth | P0 | Exploitable risk |
| Database corruption on write | P0 | Irreversible damage |
| User login fails intermittently | P1 | Major user impact |
| Add new export format | P2 | Standard feature work |
| Refactor legacy module | P3 | Engineering quality |
| Fix typo in README | P4 | Documentation polish |

### Priority Reclassification

Automatically classify and re-prioritize tickets using the P0–P4 rubric:

```bash
# Dry-run (default) - see what would change
tf new priority-reclassify --ready
tf new priority-reclassify --ids abc-123,def-456

# Apply changes
tf new priority-reclassify --ready --apply

# With safety caps and confirmation skipping
tf new priority-reclassify --ready --apply --yes --max-changes 10
```

**Options:**
| Flag | Description |
|------|-------------|
| `--apply` | Apply priority changes (default is dry-run) |
| `--yes` | Skip confirmation prompt |
| `--max-changes N` | Limit number of tickets to modify |
| `--ids <id1,id2>` | Process specific ticket IDs |
| `--ready` | Process all ready tickets |
| `--status <status>` | Filter by ticket status |
| `--tag <tag>` | Filter by tag |
| `--json` | Output as JSON for scripting |
| `--report` | Write audit trail to `.tf/knowledge/` |

The rubric matches tickets based on tags, title keywords, and description content. See [docs/commands.md](docs/commands.md) for details on customizing classification rules.

---

## Configuration

Models are configured in `config/settings.json`:

```json
{
  "metaModels": {
    "worker": {
      "model": "kimi-coding/k2p5",
      "thinking": "high",
      "description": "Strong model for implementation"
    },
    "planning": {
      "model": "openai-codex/gpt-5.2",
      "thinking": "medium",
      "description": "Fast model for planning"
    },
    "research": {
      "model": "minimax/MiniMax-M2.1",
      "thinking": "medium",
      "description": "Fast model for research"
    },
    "fast": {
      "model": "zai/glm-4.7-flash",
      "thinking": "medium",
      "description": "Cheapest model for quick tasks"
    },
    "general": {
      "model": "zai/glm-4.7",
      "thinking": "medium",
      "description": "General-purpose model"
    }
  },
  "agents": {
    "reviewer-general": "review-general",
    "fixer": "general",
    "researcher": "research"
  },
  "prompts": {
    "tf": "worker",
    "tf-plan": "planning",
    "tf-backlog": "planning"
  }
}
```

Apply changes with:

```bash
tf sync

# Or via Pi prompt
/tf-sync
```

See [docs/configuration.md](docs/configuration.md) for full setup options.

---

## Ralph Loop (Autonomous Processing)

Ralph enables autonomous ticket processing with:

- **Re-anchoring**: Fresh context per ticket
- **Lessons Learned**: Persistent wisdom in `.tf/ralph/AGENTS.md`
- **Progress Tracking**: External state survives resets

```bash
tf ralph init          # Initialize Ralph
tf ralph status        # Check status
tf ralph lessons       # View lessons

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
├── tf/                     # Python CLI package (canonical)
├── tf_cli/                 # Compatibility shim (deprecated, removal 0.5.0)
├── bin/tf                  # Python shim entrypoint
├── install.sh              # Installation script
└── docs/                   # Documentation
```

---

## Versioning and Releases

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html):

| Bump | When |
|------|------|
| **MAJOR** | Breaking changes (removed commands, config format changes) |
| **MINOR** | New features, backward compatible (new commands, workflows) |
| **PATCH** | Bug fixes, docs improvements |

**Release checklist:**
1. Update `VERSION` file
2. Update `CHANGELOG.md`
3. Sync `package.json` version
4. Run tests (`pytest`)
5. Commit: `git add VERSION package.json CHANGELOG.md`
6. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. Push: `git push origin main && git push origin vX.Y.Z`

See [VERSIONING.md](VERSIONING.md) for the full policy and detailed release process.

---

## Development

### Running Tests

The project includes both unit tests (pytest) and smoke tests (stdlib-only):

```bash
# Run all pytest tests
pytest

# Run smoke test (no pytest required)
python tests/smoke_test_version.py

# Or make it executable first
chmod +x tests/smoke_test_version.py
./tests/smoke_test_version.py
```

The smoke test validates:
- `tf --version` exits with code 0
- Output is non-empty
- Output matches SemVer format (e.g., `0.1.0`, `1.2.3-alpha.1`)

---

## Documentation

- **[docs/commands.md](docs/commands.md)** - Complete command reference
- **[docs/architecture.md](docs/architecture.md)** - How it works
- **[docs/workflows.md](docs/workflows.md)** - Detailed workflow guides
- **[docs/configuration.md](docs/configuration.md)** - Setup and models
- **[docs/ralph.md](docs/ralph.md)** - Autonomous processing
- **[docs/ticket_factory.md](docs/ticket_factory.md)** - Ticket creation API for backlog generation
- **[docs/ticket_factory_refactoring.md](docs/ticket_factory_refactoring.md)** - Migration guide from inline scripts
- **[docs/artifact-policy.md](docs/artifact-policy.md)** - Source-controlled vs runtime artifacts
