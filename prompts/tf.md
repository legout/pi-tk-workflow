---
description: Implement ticket with IRF workflow using /chain-prompts [tf-workflow]
model: kimi-coding/k2p5
thinking: high
skill: tf-workflow
---

# /tf

Execute the standard Implement → Review → Fix → Close workflow for a ticket using `/chain-prompts`.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Usage

```
/tf <ticket-id> [--no-research] [--with-research] [--create-followups]
                [--simplify-tickets] [--final-review-loop]
```

## Arguments

- `$1` - Ticket ID (e.g., `abc-1234`)
- `$@` - Ticket ID plus optional flags

## Flags

| Flag | Description |
|------|-------------|
| `--no-research` | Skip research phase (start at implement) |
| `--with-research` | Force enable research phase |
| `--create-followups` | Run `/tf-followups` after close |
| `--simplify-tickets` | Run `/simplify` after close |
| `--final-review-loop` | Run `/review-start` after close |

## Execution

### Chain Construction

Build the chain based on research flag:

```bash
# Default or --with-research
/chain-prompts tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close -- $@

# With --no-research
/chain-prompts tf-implement -> tf-review -> tf-fix -> tf-close -- $@
```

### Flag Handling

| Flag | Behavior |
|------|----------|
| `--no-research` | Start chain at `tf-implement` |
| `--with-research` | Start chain at `tf-research` (default) |
| `--create-followups` | Post-chain: run `tf-followups` |
| `--simplify-tickets` | Post-chain: run `simplify` |
| `--final-review-loop` | Post-chain: run `review-start` |

**Flag precedence**: Last flag wins for conflicting flags.

### Post-Chain Commands

After the chain completes (CLOSED status), run post-chain commands in order:
1. `tf-followups` (if `--create-followups`)
2. `simplify` (if `--simplify-tickets`)
3. `review-start` (if `--final-review-loop`)

If chain ends with BLOCKED status, skip all post-chain commands.

## Output Artifacts

Written under `.tf/knowledge/tickets/<ticket-id>/`:
- `research.md` - Ticket research (if research ran)
- `implementation.md` - Implementation summary
- `review.md` - Consolidated review
- `fixes.md` - Fixes applied
- `close-summary.md` - Final summary
- `chain-summary.md` - Artifact index
- `files_changed.txt` - Tracked changed files
- `ticket_id.txt` - Ticket ID

## Notes

- Each phase prompt has its own model/skill/thinking from frontmatter
- Chain restores original model/thinking when complete
- Only the review phase spawns parallel subagents
- The close phase commits only paths from `files_changed.txt` plus artifacts
