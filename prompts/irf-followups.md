---
description: Create follow-up tickets from review warnings/suggestions.
---

# IRF Followups

Create follow‑up tickets based on Warnings/Suggestions in a review.

## Invocation

```
/irf-followups <review path or ticket-id>
```

Pi passes args as `$@`.

If `$@` is empty and `review.md` exists in the current directory, use it. Otherwise, the planner will try to resolve a review path from a ticket id; if it fails, it will ask for a path and stop.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-FOLLOWUPS\nInput: $@",
  "agentScope": "both"
}
```

After completion, summarize created ticket IDs and the followups artifact path.
