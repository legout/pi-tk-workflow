---
description: Convert an OpenSpec change into IRF tickets using tasks.md and specs.
---

# IRF from OpenSpec

Create IRF tickets from an OpenSpec change folder.

## Invocation

```
/irf-from-openspec <change-id or path>
```

Pi passes args as `$@`.

If `$@` is empty, ask the user for a change id or path and stop.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-FROM-OPENSPEC\nChange: $@",
  "agentScope": "both"
}
```

After completion, summarize created ticket IDs and backlog file location.
