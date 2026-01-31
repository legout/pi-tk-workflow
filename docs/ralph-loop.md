# Ralph Loop

Autonomous ticket processing for pi-tk-workflow.

## What is Ralph?

Ralph is an external orchestration layer that runs the IRF workflow in a loop, processing tickets until your backlog is empty. It provides:

- **Re-anchoring**: Fresh context for each ticket
- **Lessons learned**: Persistent wisdom across iterations  
- **Progress tracking**: External state survives resets
- **Promise-based completion**: Clear termination signal

## Core Concepts

### Re-anchoring

Each iteration starts fresh. The agent reads:
1. Root `AGENTS.md` (project patterns)
2. `.pi/ralph/AGENTS.md` (lessons from previous tickets)
3. Ticket description and knowledge base

This prevents "context rot" where accumulated conversation history degrades performance.

### Lessons Learned

After each ticket, insights are captured:

```markdown
## Lesson from abc-1234 (2026-01-30)

**Context**: Implementing OAuth login

**Lesson**: The `auth` module uses legacy callback patterns. New code should use the `auth2` wrapper.

**Recommendation**: Always check for `auth2` utilities before adding new auth logic.
```

Future iterations read these lessons to avoid repeating mistakes.

### Promise Sigil

The loop outputs `<promise>COMPLETE</promise>` when:
- All tickets are processed, OR
- Max iterations reached, OR
- Unrecoverable error occurs

This gives external tools a clear termination signal.

### Progress Tracking

State is stored externally in `.pi/ralph/progress.md`:

```markdown
## Current State
- Status: RUNNING
- Current ticket: abc-5678
- Started: 2026-01-30T10:00:00

## Statistics
- Tickets completed: 12
- Tickets failed: 1
- Total iterations: 13

## History
- abc-1234: COMPLETE (OAuth login)
- abc-1235: COMPLETE (User profile)
...
```

## Directory Structure

```
.pi/ralph/
├── AGENTS.md       # Lessons learned (read before each ticket)
├── progress.md     # Loop state and history
└── config.json     # Loop settings
```

## Quick Start

### 1. Initialize

```bash
# Create .pi/ralph/ directory structure
./bin/irf ralph init

# Or create root AGENTS.md (for project patterns)
cp docs/AGENTS.md.template AGENTS.md
```

### 2. Configure Root AGENTS.md

Edit root `AGENTS.md` (or use the template):

```markdown
# Project Agents

## Patterns
- Use TypeScript strict mode
- All API calls go through `src/lib/api.ts`

## Ralph Loop Integration
If `.pi/ralph/AGENTS.md` exists, read it for lessons learned from 
autonomous ticket processing.
```

### 3. Run /irf-lite (Ralph-Ready by Default)

```
/irf-lite <ticket-id> [--auto]
```

**Automatically:**
- Reads root `AGENTS.md` (re-anchoring)
- Reads `.pi/ralph/AGENTS.md` if exists (lessons)
- Tracks progress in `.pi/ralph/progress.md`
- Synthesizes lessons after completion
- Outputs promise sigil

### 4. Run in Loop (Optional)

```
/ralph-start [--max-iterations 50]
```

Or manually:

```bash
while tk ready | grep -q .; do
  TICKET=$(tk ready | head -1 | awk '{print $1}')
  pi "/irf-lite $TICKET --auto"
done
```

### 5. Monitor

```bash
./bin/irf ralph status      # Show current state
./bin/irf ralph lessons     # View lessons learned
./bin/irf ralph reset --keep-lessons  # Clear progress
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  RALPH LOOP (external orchestrator)                     │
├─────────────────────────────────────────────────────────┤
│  while tickets remain AND iterations < max:             │
│                                                         │
│    1. READ STATE                                        │
│       - .pi/ralph/config.json                           │
│       - .pi/ralph/progress.md                           │
│       - .pi/ralph/AGENTS.md (lessons)                   │
│                                                         │
│    2. GET TICKET                                        │
│       - tk ready | head -1                              │
│                                                         │
│    3. RE-ANCHOR                                         │
│       - Inject lessons into context                     │
│       - Read ticket description                         │
│       - Load knowledge base                             │
│                                                         │
│    4. EXECUTE                                           │
│       - /irf-lite <ticket> --auto                       │
│       - Agents work unchanged                           │
│                                                         │
│    5. PARSE RESULT                                      │
│       - Read close-summary.md                           │
│       - Determine success/failure                       │
│                                                         │
│    6. UPDATE STATE                                      │
│       - Append to progress.md                           │
│       - (Optional) Synthesize lessons                   │
│       - Update statistics                               │
│                                                         │
│  7. OUTPUT <promise>COMPLETE</promise>                  │
└─────────────────────────────────────────────────────────┘
```

## Configuration

`.pi/ralph/config.json`:

```json
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "workflow": "/irf-lite",
  "workflowFlags": "--auto",
  "sleepBetweenTickets": 5000,
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "lessonsMaxCount": 50
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `maxIterations` | 50 | Total tickets to process |
| `workflow` | `/irf-lite` | Command to run per ticket |
| `workflowFlags` | `--auto` | Flags for workflow |
| `sleepBetweenTickets` | 5000 | Ms to wait between tickets |
| `lessonsMaxCount` | 50 | Max lessons before pruning |

## CLI Reference

```bash
# Initialize
./bin/irf ralph init

# Check status
./bin/irf ralph status

# View lessons
./bin/irf ralph lessons

# Prune old lessons (keep last N)
./bin/irf ralph lessons prune 20

# Reset progress
./bin/irf ralph reset --keep-lessons  # Keep lessons
./bin/irf ralph reset                 # Clear everything
```

## Best Practices

### 1. Start Small

Test on 3-5 tickets before running large batches:

```
/ralph-start --max-iterations 3
```

### 2. Prime Lessons

Before starting, add known patterns to `.pi/ralph/AGENTS.md`:

```markdown
## Gotchas
- Always use `safeParse()` for user input
- The `cache` module needs explicit TTL
```

### 3. Review Early

Check first few tickets manually:

```bash
./bin/irf ralph status
# Review the completed tickets in tk
```

### 4. Prune Lessons

Keep lessons file manageable:

```bash
./bin/irf ralph lessons prune 30
```

Old lessons may become outdated as the codebase evolves.

### 5. Use With Planning

Ralph works best with well-defined tickets:

```bash
# Create detailed backlog first
/irf-backlog-lite my-feature

# Then run Ralph
/ralph-start
```

## Comparison: With vs Without Ralph

| Aspect | Standalone `/irf-lite` | With Ralph Loop |
|--------|------------------------|-----------------|
| Context | Fresh per invocation | Fresh per ticket + lessons |
| Learning | None | Accumulates in AGENTS.md |
| Automation | Manual per ticket | Fully autonomous |
| Monitoring | Per-ticket | Aggregate progress |
| Termination | Manual | Promise sigil |

## Troubleshooting

**Loop stops early?**
- Check `tk ready` - are there tickets with unmet dependencies?
- Check `.pi/ralph/progress.md` for failures

**Lessons not helping?**
- Review `.pi/ralph/AGENTS.md` for stale info
- Prune outdated lessons
- Add more specific patterns

**Too many iterations on one ticket?**
- The ticket may be too large - split it in `tk`
- Check `maxIterationsPerTicket` in config

## Integration with Planning

Ralph can process tickets from any planning source:

| Source | Tickets Created By | Ralph Reads |
|--------|-------------------|-------------|
| IRF Seed | `/irf-backlog-lite` | Seed reference in ticket |
| OpenSpec | `/irf-from-openspec-lite` | Change ID in ticket |
| Manual | `tk create` | Direct description |

The planning docs (seed.md, proposal.md, design.md) are referenced in ticket descriptions and loaded during re-anchoring.

---

**Key Principle**: Ralph is **additive orchestration**. Your core workflow (`/irf-lite`) works identically with or without Ralph. The loop is just a smart wrapper that manages context and tracks progress.
