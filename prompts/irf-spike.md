---
description: Run a focused research spike and write results into the knowledge base.
---

# IRF Spike

Run a focused research spike on a topic and store results in the knowledge base.

## Invocation

```
/irf-spike <topic>
```

Pi passes args as `$@`.

If `$@` is empty, ask the user for a spike topic and stop.

## Execution

Use the **subagent** tool with the `irf-planner` agent:

```json
{
  "agent": "irf-planner",
  "task": "IRF-SPIKE\nTopic: $@",
  "agentScope": "both"
}
```

After completion, summarize the spike output paths for the user.
