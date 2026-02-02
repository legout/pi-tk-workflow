# Ralph Loop

Autonomous ticket processing for pi-tk-workflow.

---

## What is Ralph?

Ralph is an orchestration layer that runs the IRF workflow in a loop, processing tickets until your backlog is empty.

**Key Features:**
- **Re-anchoring**: Fresh context for each ticket
- **Lessons Learned**: Persistent wisdom across iterations
- **Progress Tracking**: External state survives resets
- **Promise-based Completion**: Clear termination signal

---

## Quick Start

### 1. Initialize

```bash
./bin/irf ralph init
```

Creates `.pi/ralph/` directory structure.

### 2. Configure Root AGENTS.md (Optional)

Create root `AGENTS.md` for project patterns:

```markdown
# Project Agents

## Patterns
- Use TypeScript strict mode
- All API calls go through `src/lib/api.ts`

## Ralph Loop Integration
If `.pi/ralph/AGENTS.md` exists, read it for lessons learned.
```

### 3. Run IRF (Ralph-Ready by Default)

```
/irf <ticket-id> [--auto]
```

Automatically:
- Reads root `AGENTS.md` (re-anchoring)
- Reads `.pi/ralph/AGENTS.md` if exists (lessons)
- Tracks progress in `.pi/ralph/progress.md`
- Synthesizes lessons after completion

### 4. Run in Loop

```
/ralph-start [--max-iterations 50]
```

Or manually:

```bash
while tk ready | grep -q .; do
  TICKET=$(tk ready | head -1 | awk '{print $1}')
  pi "/irf $TICKET --auto"
done
```

---

## Directory Structure

```
.pi/ralph/
├── AGENTS.md       # Lessons learned (read before each ticket)
├── progress.md     # Loop state and history
└── config.json     # Loop settings
```

---

## Configuration

`.pi/ralph/config.json`:

```json
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
  "completionCheck": "tk ready | grep -q .",
  "workflow": "/irf",
  "workflowFlags": "--auto",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "promiseOnComplete": true,
  "lessonsMaxCount": 50
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `maxIterations` | 50 | Total tickets to process |
| `maxIterationsPerTicket` | 5 | Retries per ticket |
| `ticketQuery` | `tk ready \| head -1` | Command to pick next ticket |
| `completionCheck` | `tk ready \| grep -q .` | Command to detect empty backlog |
| `workflow` | `/irf` | Command to run per ticket |
| `workflowFlags` | `--auto` | Flags for workflow |
| `sleepBetweenTickets` | 5000 | Ms to wait between tickets |
| `promiseOnComplete` | true | Emit `<promise>COMPLETE</promise>` on completion |
| `lessonsMaxCount` | 50 | Max lessons before pruning |

---

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

### Promise Sigil

The loop outputs `<promise>COMPLETE</promise>` when:
- All tickets are processed, OR
- Max iterations reached, OR
- Unrecoverable error occurs

### Progress Tracking

State is stored in `.pi/ralph/progress.md`:

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
```

---

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

---

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
# Review completed tickets in tk
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
/irf-backlog my-feature

# Then run Ralph
/ralph-start
```

---

## Comparison: With vs Without Ralph

| Aspect | Standalone `/irf` | With Ralph Loop |
|--------|-------------------|-----------------|
| Context | Fresh per invocation | Fresh per ticket + lessons |
| Learning | None | Accumulates in AGENTS.md |
| Automation | Manual per ticket | Fully autonomous |
| Monitoring | Per-ticket | Aggregate progress |
| Termination | Manual | Promise sigil |

---

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
