---
description: Implement ticket with deterministic IRF workflow wrapper [tf-workflow]
model: kimi-coding/k2p5
thinking: medium
skill: tf-workflow
---

# /tf

Execute the standard Implement → Review → Fix → Close workflow for a ticket.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Usage

```bash
/tf <ticket-id> [--auto] [--no-clarify] [--no-research] [--with-research]
    [--plan|--dry-run] [--create-followups] [--simplify-tickets]
    [--final-review-loop] [--retry-reset]
```

## Execution (deterministic)

Use the Python wrapper in `tf` tooling so flag parsing and chain construction are deterministic:

```bash
tf irf $@
```

The wrapper handles:
- research entry selection (`tf-research` vs `tf-implement`)
- chain construction (`/chain-prompts ...`)
- `--plan/--dry-run`
- post-chain commands (`tf-followups`, `simplify`, `review-start`)
- strict unknown-flag validation

## Notes

- Phase prompts remain thin wrappers with frontmatter model/thinking/skill.
- Phase procedures live in phase skills.
- Reviewer subagents keep using `skill: tf-review`.
