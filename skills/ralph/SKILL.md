---
name: ralph
description: Autonomous ticket processing loop for IRF workflow. Use when processing multiple tickets without manual intervention. Manages re-anchoring, lessons learned, progress tracking, and loop termination.
---

# Ralph Loop Skill

Expertise for autonomous, continuous ticket processing.

## When to Use This Skill

- Processing a backlog of tickets without manual intervention
- Running overnight batch processing
- Maintaining context and learning across multiple tickets
- Tracking progress over long-running sessions

## Core Concepts

### Re-Anchoring

Each iteration starts fresh:
1. Load root `AGENTS.md` (project patterns)
2. Load `.pi/ralph/AGENTS.md` (lessons learned)
3. Load ticket + knowledge base
4. Execute workflow

This prevents "context rot" from accumulated conversation history.

### Lessons Learned

Persistent wisdom across iterations:
- Extracted after each ticket
- Stored in `.pi/ralph/AGENTS.md`
- Read at start of next iteration
- Pruned when too many accumulate

### Progress Tracking

External state in `.pi/ralph/progress.md`:
- Survives context resets
- Tracks completed/failed tickets
- Records statistics
- Enables loop monitoring

### Promise Sigil

Clear termination signal:
```
<promise>COMPLETE</promise>
```

Emitted when:
- Backlog is empty
- Max iterations reached
- Unrecoverable error occurs

Controlled by `promiseOnComplete` (default: true).

## Directory Structure

```
.pi/ralph/
├── AGENTS.md          # Lessons learned
├── progress.md        # Loop state and history
└── config.json        # Loop configuration
```

## Configuration

`.pi/ralph/config.json`:
```json
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
  "completionCheck": "tk ready | grep -q .",
  "workflow": "/tf",
  "workflowFlags": "--auto",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "promiseOnComplete": true,
  "lessonsMaxCount": 50
}
```

## Execution Procedures

### Procedure: Initialize Ralph

Create directory structure:

```bash
mkdir -p .pi/ralph
```

Create `config.json` with defaults.

Create `progress.md`:
```markdown
## Current State
- Status: INITIALIZED
- Current ticket: (none)
- Started: {timestamp}

## Statistics
- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History
```

Create `AGENTS.md`:
```markdown
# Ralph Lessons Learned

## Patterns
## Gotchas
```

---

### Procedure: Start Loop

Main loop execution:

```
FOR iteration = 1 TO maxIterations:

  1. READ STATE
     - Load config.json
     - Load progress.md
     - Load AGENTS.md

  2. GET TICKET
     - Run `ticketQuery` from config (default: `tk ready | head -1 | awk '{print $1}'`).
     - If no ticket and `completionCheck` indicates empty backlog, GOTO COMPLETE.
     - If no ticket but backlog not empty, sleep `sleepBetweenRetries` and retry.

  3. RE-ANCHOR
     - Inject lessons from AGENTS.md
     - Read ticket description
     - Load knowledge base (if configured)

  4. EXECUTE
     - Run workflow: `{workflow} {ticket} {workflowFlags}` from config
     - Wait for completion

  5. PARSE RESULT
     - Check for <promise>TICKET_{id}_COMPLETE</promise>
     - Determine success/failure

  6. UPDATE STATE
     - Append to progress.md history
     - Update statistics
     - (Optional) Synthesize lessons → AGENTS.md

  7. SLEEP
     - Wait sleepBetweenTickets ms

END FOR

COMPLETE:
Output <promise>COMPLETE</promise>
```

---

### Procedure: Extract Lessons

After ticket completion, decide if lesson is worth preserving:

**Criteria** (only extract if):
- A gotcha was discovered
- A successful pattern emerged
- Technical debt was identified
- Tool/environment issues encountered

**Format**:
```markdown
## Lesson from {ticket-id} ({date})

**Context**: {brief context}

**Lesson**: {what was learned}

**Apply when**: {when to use this lesson}
```

**Constraints**:
- Keep concise (3-5 sentences max)
- Be specific about when to apply
- Don't extract obvious things

---

### Procedure: Update Progress

Append to `.pi/ralph/progress.md`:

```markdown
- {ticket-id}: {STATUS} ({timestamp})
  - Summary: {one-line description}
  - Issues: Critical({c})/Major({m})/Minor({n})
  - Status: COMPLETE|FAILED
```

Update statistics section:
- Increment completed or failed count
- Update last updated timestamp

---

### Procedure: Prune Lessons

When lessons exceed `lessonsMaxCount`:

1. Read `AGENTS.md`
2. Count lessons (## Lesson headers)
3. If > maxCount:
   - Keep most recent N lessons
   - Remove oldest lessons
4. Write back

---

### Procedure: Check Status

Read and summarize:
- Current state (RUNNING/IDLE/ERROR)
- Statistics (completed/failed)
- Current ticket (if any)
- Recent history (last 5 tickets)

---

### Procedure: Reset

**Full reset**:
- Clear progress.md (keep structure)
- Optionally clear AGENTS.md

**Reset keeping lessons**:
- Clear progress.md only
- Keep AGENTS.md intact

## Integration with IRF Workflow

Ralph is **additive** - the core `/tf` workflow works identically:

| Aspect | Standalone | With Ralph |
|--------|-----------|------------|
| Context | Fresh | Fresh + lessons |
| Learning | None | Accumulated |
| Progress | Per-ticket | Tracked across tickets |
| Automation | Manual | Fully autonomous |

The workflow skill handles ticket implementation. Ralph skill handles:
- Loop orchestration
- State management
- Lesson synthesis
- Progress tracking

## Error Handling

- **No tickets ready**: Use `completionCheck` to decide complete vs sleep `sleepBetweenRetries`
- **Workflow fails**: Mark failed, continue to next ticket
- **State files corrupt**: Re-initialize from scratch
- **Max iterations reached**: Output promise sigil and stop

## Output

Output promise sigil on completion when `promiseOnComplete` is true:
```
<promise>COMPLETE</promise>
```

## Best Practices

1. **Start small**: Test on 3-5 tickets before large batches
2. **Prime lessons**: Add known patterns to AGENTS.md before starting
3. **Review early**: Check first few tickets manually
4. **Prune regularly**: Remove outdated lessons
5. **Use with planning**: Ralph works best with well-defined tickets
