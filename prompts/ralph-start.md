---
description: Start autonomous ticket processing loop [ralph]
skill: ralph
restore: false
---

# /ralph-start

Start the Ralph autonomous loop for continuous ticket processing.

## Usage

```
/ralph-start [--max-iterations 50]
```

## Flags

| Flag | Description |
|------|-------------|
| `--max-iterations N` | Process at most N tickets (default: 50) |

## Prerequisites

- Ralph initialized: `./bin/tf ralph init`
- Tickets ready in backlog: `tk ready`
- `/tf` working standalone

## Execution

Follow the **Ralph Skill** "Start Loop" procedure:

```
FOR iteration = 1 TO maxIterations:
  1. READ STATE - Load config, progress, lessons
  2. GET TICKET - `tk ready | head -1`
  3. RE-ANCHOR - Load lessons, ticket, knowledge
  4. EXECUTE - Run `/tf {ticket} --auto`
  5. PARSE RESULT - Check promise sigil
  6. UPDATE STATE - Progress, statistics, lessons
  7. SLEEP - Wait between tickets
END FOR

Output: <promise>COMPLETE</promise> (if promiseOnComplete)
```

## How It Works

1. **Re-Anchoring**: Each ticket starts fresh with accumulated lessons
2. **Lessons Learned**: Extracted after each ticket, stored in `.pi/ralph/AGENTS.md`
3. **Progress Tracking**: State in `.pi/ralph/progress.md` survives context resets
4. **Promise Sigil**: Clear termination signal when done

## Configuration

`.pi/ralph/config.json`:
```json
{
  "maxIterations": 50,
  "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
  "completionCheck": "tk ready | grep -q .",
  "workflow": "/tf",
  "workflowFlags": "--auto",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "promiseOnComplete": true,
  "lessonsMaxCount": 50
}
```

## Monitoring

In another terminal:
```bash
./bin/tf ralph status     # Current state
./bin/tf ralph lessons    # View lessons learned
```

## Stopping

The loop stops when:
- `completionCheck` reports the backlog is empty
- Max iterations reached
- Unrecoverable error occurs

## Notes

- Uses `restore: false` - stays on loop model after completion
- Works best with well-defined tickets (use `/tf-backlog` first)
- First run: start with `--max-iterations 3` to verify
- Check first few tickets manually before long runs
