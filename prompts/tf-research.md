---
description: Research phase for TF workflow [tf-research]
model: kimi-coding/k2p5
thinking: medium
skill: tf-research
---

# /tf-research

Execute the Research phase for TF workflow ticket implementation.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Execution

Follow the **tf-research** skill procedure to:

1. Re-anchor context (AGENTS.md, lessons, ticket details)
2. Check research prerequisites (flags, config)
3. Conduct research (pi-web-access or MCP tools)
4. Write `{artifactDir}/research.md`

## Usage

```
/tf-research <ticket-id> [--no-research] [--with-research]
```

## Output

- `{artifactDir}/research.md` - Research findings
- `{artifactDir}/ticket_id.txt` - Ticket ID
