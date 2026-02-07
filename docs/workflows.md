# Workflow Guides

Step-by-step guides for common development scenarios.

---

## Choosing Between Seed and Plan

| | Seed (`/tf-seed`) | Plan (`/tf-plan`) |
|---|---|---|
| **Purpose** | Explore and capture ideas | Specify implementation details |
| **When to use** | New ideas, fuzzy requirements | Complex features, need rigor |
| **Process** | One-shot capture | Multi-phase (consult → revise → review) |
| **Artifacts** | `seed.md`, `mvp-scope.md`, `constraints.md` | `plan.md` with requirements, work plan |
| **Approval** | None | Formal review (PASS/FAIL) |
| **Speed** | Fast | Slower but thorough |

**Can I use both?** Yes! For complex new features, use seed first to explore, then plan to specify rigorously. See [Seed + Plan Combo](#seed--plan-combo) below.

---

## Vague Idea → Decision Guide

Use this when you have a fuzzy idea and want guidance to converge on scope and approach.

### 1. Start with a clarifying seed
Capture the idea plus unknowns so you have something concrete to refine.

```
/tf-seed "Build X for Y (unknowns: pricing model, auth strategy, hosting)"
```

### 2. Spike the unknowns
Run a spike for each major uncertainty (use `--parallel` if you want speed).

```
/tf-spike "Pricing models for X"
/tf-spike "Auth strategy for Y" --parallel
```

### 3. Capture decisions with spike references
Create a new seed (or update your existing one) and **reference the spike IDs** in the prompt. Then add the spike docs to `sources.md` (there is no automatic linking).

```
/tf-seed "Build X using SSO + magic links based on spike-auth-strategy"
```

Add to `.tf/knowledge/topics/seed-build-x/sources.md`:

```
- .tf/knowledge/topics/spike-auth-strategy/spike.md
```

### 4. Plan if the work is complex
Use the seed + spike context in your plan prompt.

```
/tf-plan "Implement X based on seed-build-x and spike-auth-strategy"
```

### 5. Planning loop (if plan used)

```
/tf-plan-consult plan-build-x
/tf-plan-revise plan-build-x
/tf-plan-review plan-build-x --high-accuracy
/tf-backlog plan-build-x
```

If the plan is not needed, go straight to:

```
/tf-backlog seed-build-x
```

---

## Greenfield Development (Seed Only)

Starting a new project or feature from scratch when you want to move fast.

### 1. Capture Your Idea

```
/tf-seed "Build a CLI tool for managing database migrations"
```

This creates structured artifacts in `.tf/knowledge/topics/seed-build-a-cli/`:
- `seed.md` - Your vision and core concept
- `mvp-scope.md` - What's in/out of the first version
- `success-metrics.md` - How you'll measure success
- `assumptions.md` - What you're assuming
- `constraints.md` - Limitations to work within

### 2. (Optional) Research First

If you need to research technical approaches:

```
/tf-spike "Database migration tools in Python"
```

Creates `.tf/knowledge/topics/spike-database-migration-tools/` with:
- `spike.md` - Analysis of options with recommendations
- `sources.md` - URLs and references

### 3. Create Tickets

```
/tf-backlog seed-build-a-cli
```

Generates appropriately-sized tickets in `tk`—this could be 1 ticket for a tiny fix or many for a large feature. Each ticket is:
- 30 lines or less
- 1-2 hours of work
- Self-contained with context from seed
- Linked via `external-ref`

### 4. Implement

```
/tf TICKET-123
```

Runs the full TF cycle on each ticket.

### 5. Autonomous Processing (Optional)

```
/ralph-start --max-iterations 20
```

Processes remaining tickets automatically.

### 6. Refine Backlog (Optional)

When `/tf-backlog` inference is incomplete, use these manual correction tools:

**Typical sequence:**
```
/tf-backlog seed-build-a-cli      # Generate initial tickets
/tf-tags-suggest --apply          # Add missing component tags
/tf-deps-sync --apply             # Sync parent/child dependencies
```

**What each tool does:**
- `/tf-tags-suggest` - Suggests `component:*` tags for parallel scheduling safety
- `/tf-deps-sync` - Ensures parent tickets are reflected in `deps` field

**Manual linking:**
If automatic inference misses a dependency, link manually:
```
tk link CHILD-123 PARENT-456
```

**When to run:**
- After `/tf-backlog` if tags or dependencies look incomplete
- Before `/ralph-start` to ensure safe parallel scheduling
- Any time you modify ticket relationships manually

---

## Seed + Plan Combo

For complex new features where you want to explore first, then specify rigorously.

**When to use:**
- Major new features with lots of unknowns
- Architectural changes that need both exploration AND rigor
- When stakeholders need approval gates but you need to explore first

**The flow:**

```
/tf-seed "Big idea" → /tf-plan "Refined from seed" → review → /tf-backlog → /tf
   explore              specify rigorously              tickets        implement
```

### Step 1: Explore with Seed

```
/tf-seed "Build a distributed task queue system"
```

This captures:
- **Vision** - What problem we're solving
- **Core concept** - High-level approach
- **MVP scope** - What's in/out for first version
- **Constraints** - Performance, scalability, tech limits
- **Assumptions** - What we're assuming about users/tech

**Review the artifacts:**
```bash
cat .tf/knowledge/topics/seed-distributed-task-queue/seed.md
cat .tf/knowledge/topics/seed-distributed-task-queue/mvp-scope.md
cat .tf/knowledge/topics/seed-distributed-task-queue/constraints.md
```

### Step 2: Specify with Plan

Now create a rigorous plan using the seed content as input:

```
/tf-plan "Distributed task queue: implement core message broker with Redis streams, 
           supporting at-least-once delivery, 10K msgs/sec throughput, 
           based on seed-distributed-task-queue"
```

The plan will include:
- **Requirements** - Specific, testable requirements
- **Work plan** - Phased implementation with sequencing
- **Acceptance criteria** - How we know it's done
- **Risks** - What could go wrong

### Step 3: Iterate the Plan (Optional)

For complex features, run the plan through review:

```
/tf-plan-consult plan-distributed-task-queue   # Detect gaps
/tf-plan-revise plan-distributed-task-queue    # Apply feedback
/tf-plan-review plan-distributed-task-queue    # Get approval
```

### Step 4: Create Tickets and Implement

```
/tf-backlog plan-distributed-task-queue
/tf TICKET-123
```

### Why Combine Them?

| Phase | Seed Provides | Plan Provides |
|-------|---------------|---------------|
| **Explore** | Vision, scope, constraints | — |
| **Specify** | Context for decisions | Detailed requirements, work plan |
| **Review** | — | Formal approval gate |
| **Implement** | Background context | Specific acceptance criteria |

**Seed alone** = Fast but might miss edge cases  
**Plan alone** = Rigid, might over-specify  
**Seed + Plan** = Exploratory then rigorous

---

## Brownfield Development

Working with an existing codebase.

### 1. Capture Baseline

Document the current state before making changes:

```
/tf-baseline
```

Or focus on a specific area:

```
/tf-baseline "authentication system"
```

Creates `.tf/knowledge/topics/baseline-myapp/` with:
- `baseline.md` - Architecture and components
- `risk-map.md` - Technical risks and fragile areas
- `test-inventory.md` - Test coverage gaps
- `dependency-map.md` - External dependencies
- `existing-tickets.md` - Current open tickets (from `tk` if available)

### 2. Create Improvement Tickets

```
/tf-backlog baseline-myapp
```

Generates tickets from:
- Risk map items (high priority)
- Test coverage gaps
- Dependency issues
- Architectural hotspots
- Skips duplicates already present in `backlog.md` or `existing-tickets.md`

### 3. Implement

```
/tf TICKET-123
```

Each ticket includes baseline context so you understand the existing code.

---

## Structured Planning (Plan Only)

For complex features requiring careful design. Use this when you already understand the problem well and want to go straight to rigorous specification.

**When to use plan directly (without seed first):**
- You have clear requirements already
- Refactoring existing features
- Adding capabilities to established systems
- Team already aligned on approach

**When to use seed + plan combo instead:**
- New territory, lots of unknowns
- Need to explore options before specifying
- Stakeholders need to see vision before details

### 1. Create Initial Plan

```
/tf-plan "Refactor auth flow to support OAuth + magic links"
```

Creates `.tf/knowledge/topics/plan-auth-refactor/plan.md` with:
- Summary and requirements
- Constraints and assumptions
- Risks and gaps
- Work plan with phases
- Acceptance criteria

Status: `draft`

### 2. Consult for Gaps

```
/tf-plan-consult plan-auth-refactor
```

Identifies:
- Missing requirements
- Ambiguous specifications
- Over-engineering
- Hidden risks

Updates plan.md with Consultant Notes. Status: `consulted`

### 3. Revise Based on Feedback

```
/tf-plan-revise plan-auth-refactor
```

Applies changes to address consultant findings.

Status: `revised`

### 4. High-Accuracy Review

```
/tf-plan-review plan-auth-refactor --high-accuracy
```

Validates:
- Completeness of requirements
- Clear scope boundaries
- Feasible work plan
- Testable acceptance criteria

Status: `approved` or `blocked`

### 5. Create Tickets

Only proceed if plan is approved:

```
/tf-backlog plan-auth-refactor
```

Generates tickets from the work plan, each referencing the approved plan.

### 6. Implement

```
/tf TICKET-123
```

---

## Research-Driven Development

When you need to evaluate options before deciding.

### 1. Research Spike

```
/tf-spike "React Server Components vs Next.js App Router" --parallel
```

Uses parallel subagents for faster research. Creates:
- `overview.md` - Quick summary
- `spike.md` - Detailed analysis with pros/cons/recommendations

### 2. Capture Decision as Seed

```
/tf-seed "Migrate to Next.js App Router based on spike findings"
```

References the spike in your seed.

### 3. Create and Implement Tickets

```
/tf-backlog seed-migrate-nextjs
/tf TICKET-123
```

---

## Review-Driven Improvements

Addressing issues found during code review.

### 1. Normal Implementation

```
/tf TICKET-123
```

Produces `review.md` with findings.

### 2. Create Follow-up Tickets

For warnings and suggestions that are out of scope:

```
/tf-followups ./review.md
```

Creates tickets tagged with `followup` and priority 3 (lower than implementation).

### 3. Process Follow-ups

```
/tf FOLLOWUP-456
```

---

## OpenSpec Integration

Working with external specifications.

### 1. Create Tickets from OpenSpec

```
/tf-backlog-from-openspec auth-pkce-support
```

Reads from `openspec/changes/auth-pkce-support/`:
- `tasks.md` for task list
- `proposal.md` and `design.md` for context

Creates tickets tagged with `openspec`, linked to the change, and applies dependencies from task ordering/headings.

### 2. Implement

```
/tf TICKET-123
```

Each ticket includes relevant technical details from the OpenSpec.

---

## Autonomous Processing with Ralph

Running batches of tickets without manual intervention.

### 1. Initialize Ralph

```bash
tf ralph init
```

Creates `.tf/ralph/` directory with:
- `AGENTS.md` - Lessons learned
- `progress.md` - Loop state
- `config.json` - Configuration

### 2. (Optional) Prime with Known Patterns

Edit `.tf/ralph/AGENTS.md`:

```markdown
## Gotchas
- Always use safeParse() for user input
- The cache module needs explicit TTL

## Patterns
- Use the Result type for error handling
```

### 3. Start the Loop

```
/ralph-start --max-iterations 20
```

Or with CLI:

```bash
tf ralph init
# Then in pi:
/ralph-start
```

### 4. Monitor Progress

```bash
tf ralph status
tf ralph lessons
```

### 5. Review and Prune

```bash
# Remove outdated lessons
tf ralph lessons prune 30
```

---

## Ticket Guidelines

All ticket creation follows these principles:

| Attribute | Target |
|-----------|--------|
| Description | 30 lines or less |
| Work time | 1-2 hours |
| Context | Self-contained (no need to load planning docs) |
| Scope | Single responsibility |
| Linking | Via `external-ref` to source topic |

---

## Planning Sessions

Planning sessions connect `/tf-seed`, `/tf-spike`, `/tf-plan`, and `/tf-backlog` into a single workflow with automatic linking.

### How Sessions Work

1. **Start a session**: `/tf-seed "My idea"` creates seed artifacts **and** activates a session
2. **Add research**: `/tf-spike "Technology options"` auto-links to the session
3. **Create plan**: `/tf-plan "Implementation plan"` attaches to the session, references seed and spikes
4. **Generate tickets**: `/tf-backlog plan-my-idea` creates tickets and archives the session

### Session Commands

| Command | Purpose |
|---------|---------|
| `/tf-seed --active` | Show current active session (or "none") |
| `/tf-seed --sessions [seed-id]` | List archived sessions, optionally filtered by seed |
| `/tf-seed --resume <id>` | Resume an archived session |

### Session State

- **Active**: Only one session can be active at a time
- **Auto-link**: Spike, plan, and backlog auto-link to active session
- **Completion**: Backlog creation archives the session (removes `.active-planning.json`)

### Bypassing Sessions

For standalone work without session tracking:

```
/tf-seed --no-session "Standalone idea"  # No session created
/tf-spike "Quick research"               # No linking when no session active
/tf-plan "Direct plan"                   # Standalone plan
/tf-backlog plan-direct                  # No session finalization
```

## Knowledge Base Organization

```
.tf/knowledge/
├── index.json                    # Registry
├── .active-planning.json         # Current session (if active)
├── sessions/                     # Archived session snapshots
│   └── seed-idea@2026-02-06T12-30-00Z.json
├── tickets/
│   └── TICKET-123/
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
    ├── seed-my-feature/         # Greenfield ideas
    ├── baseline-myapp/          # Brownfield analysis
    ├── plan-auth-refactor/      # Structured plans
    └── spike-technology/        # Research findings
```

Topics are automatically created and linked. You rarely need to manage them manually.
