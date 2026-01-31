---
description: Capture a greenfield idea into IRF seed artifacts (vision, metrics, assumptions, scope).
---

# IRF Seed

This command captures an initial idea into structured seed artifacts.

## Invocation

```
/irf-seed <idea>
```

Pi passes args as `$@`.

If `$@` is empty, ask the user for a brief idea description and stop.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-SEED\nIdea: $@",
  "agentScope": "both"
}
```

After completion, summarize the created artifact paths for the user.
