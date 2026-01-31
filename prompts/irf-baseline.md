---
description: Capture brownfield status quo into baseline artifacts.
---

# IRF Baseline

Capture a status‑quo baseline for an existing project.

## Invocation

```
/irf-baseline <optional focus>
```

Pi passes args as `$@`.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-BASELINE\nFocus: $@",
  "agentScope": "both"
}
```

After completion, summarize the created artifact paths for the user.
