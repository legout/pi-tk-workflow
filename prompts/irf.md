---
description: Implement ticket with IRF workflow [irf-workflow +Kimi-K2.5]
model: chutes/moonshotai/Kimi-K2.5-TEE
thinking: high
skill: irf-workflow
---

# /irf

Execute the standard Implement → Review → Fix → Close workflow for a ticket.

## Usage

```
/irf <ticket-id> [--auto] [--no-research] [--with-research] [--plan] [--dry-run]
             [--create-followups] [--simplify-tickets] [--final-review-loop]
```

## Arguments

- `$1` - Ticket ID (e.g., `abc-1234`)
- `$@` - Ticket ID plus optional flags

## Flags

| Flag | Description |
|------|-------------|
| `--auto` / `--no-clarify` | Run headless (no confirmation prompts) |
| `--no-research` | Skip research step |
| `--with-research` | Force enable research step |
| `--plan` / `--dry-run` | Print resolved chain and exit without running agents |
| `--create-followups` | Run `/irf-followups` on merged review output |
| `--simplify-tickets` | Run `/simplify --create-tickets --last-implementation` if available |
| `--final-review-loop` | Run `/review-start` after the chain if available |

## Execution

Follow the **IRF Workflow Skill** procedures:

1. **Re-Anchor Context** - Load AGENTS.md, lessons, ticket details
2. **Research** (optional) - MCP tools for knowledge gathering
3. **Implement** (model-switch) - Code changes with quality checks
4. **Parallel Reviews** (optional) - Reviewer subagents when enabled
5. **Merge Reviews** (optional) - Deduplicate and consolidate
6. **Fix Issues** (optional) - Apply fixes when enabled
7. **Follow-ups** (optional) - Create follow-up tickets when requested
8. **Close Ticket** (optional) - Add note and close in `tk` when allowed
9. **Final Review Loop** (optional) - Run `/review-start` when requested
10. **Simplify Tickets** (optional) - Run `/simplify` follow-on if available
11. **Ralph Integration** (if active) - Update progress, extract lessons

## Output Artifacts

- `implementation.md` - Implementation summary
- `review.md` - Consolidated review
- `fixes.md` - Fixes applied
- `close-summary.md` - Final summary

Ralph files (if `.pi/ralph/` exists):
- `.pi/ralph/progress.md` - Updated
- `.pi/ralph/AGENTS.md` - May be updated

## Notes

- This is the standard workflow (model-switch for sequential phases)
- Only the parallel review step spawns subagents
- `/irf-lite` is a deprecated alias that runs the same workflow
