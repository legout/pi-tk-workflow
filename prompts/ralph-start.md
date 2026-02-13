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

- Global environment setup done (extensions + MCP/web-search config): `tf setup`
- Project initialized (installs TF prompts/agents/skills into project root): `tf init`
- Ralph initialized (creates `.tf/ralph/` state): `tf ralph init`
- Tickets ready in backlog: `tk ready`

## Preflight: Ensure `/tf` Prompt Exists

Before starting, confirm the prompt is available **as a Pi prompt** (not a shell command):

```bash
ls prompts/tf.md 2>/dev/null
```

If it does not exist, run:

```bash
tf init
# or (to re-ensure workflow files)
tf sync
```

## Execution

For robustness, **delegate to the CLI loop runner** instead of re-implementing the loop in this prompt:

```bash
# Basic run
tf ralph start --max-iterations N

# With workflow flags
tf ralph start --max-iterations N --flags "--create-followups --final-review-loop"

# Parallel (worktrees + component tags)
tf ralph start --max-iterations N --parallel 2
```

The CLI runner handles:
- `/tf` invocation via `pi -p` (fresh process per ticket)
- Progress updates in `.tf/ralph/progress.md`
- Optional lessons extraction into `.tf/ralph/AGENTS.md`
- Locking to prevent concurrent loops
- Completion handling (`<promise>COMPLETE</promise>`)

Parallel runs use **component tags** in ticket frontmatter:
```
tags: [component:delta, component:checkpoint]
```
Tickets only run concurrently when their component tags do not overlap.

This avoids prompt/subagent confusion and guarantees fresh context per ticket.

## How It Works

1. **Re-Anchoring**: Each ticket starts fresh with accumulated lessons
2. **Lessons Learned**: Extracted after each ticket, stored in `.tf/ralph/AGENTS.md`
3. **Progress Tracking**: State in `.tf/ralph/progress.md` survives context resets
4. **Promise Sigil**: Clear termination signal when done

## Configuration

`.tf/ralph/config.json`:
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
tf ralph status     # Current state
tf ralph lessons    # View lessons learned
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
