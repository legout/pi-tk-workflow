---
description: Convert an IRF seed into small implementation tickets with acceptance criteria.
---

# IRF Backlog

Generate a small, actionable ticket backlog from IRF seed artifacts.

## Invocation

```
/irf-backlog <optional seed path or topic-id>
```

Pi passes args as `$@`.

If `$@` is empty, the planner will attempt to locate a single seed; otherwise it will ask the user to provide a path.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-BACKLOG\nInput: $@",
  "agentScope": "both"
}
```

After completion, summarize created ticket IDs and backlog file location.
