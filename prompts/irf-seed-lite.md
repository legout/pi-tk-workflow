---
description: Capture a greenfield idea into IRF seed artifacts. Lite version - no subagent, uses model-switch.
---

# IRF Seed (Lite)

Capture an initial idea into structured seed artifacts. This version runs inline with model-switch instead of spawning a subagent.

## Invocation

```
/irf-seed-lite <idea>
```

If `$@` is empty, ask the user for a brief idea description and stop.

## Prerequisites

Verify `switch_model` tool is available. If not, suggest using `/irf-seed` (original) instead.

## Execution

### Step 1: Switch to Planning Model

```
Use switch_model tool with action="switch", search="gpt-5.1-codex-mini" (or config model)
```

### Step 2: Load Config

Read workflow config (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json`
- `~/.pi/agent/workflows/implement-review-fix-close/config.json`

Extract `workflow.knowledgeDir` (default: `.pi/knowledge`).

### Step 3: Create Topic Structure

1. Parse idea from `$@`
2. Create `topic-id` slug:
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `seed-`
   - Example: "Build a CLI for task management" → `seed-build-a-cli-for-task-management`

3. Create topic directory:
   ```bash
   mkdir -p "${knowledgeDir}/topics/${topic-id}"
   ```

### Step 4: Write Seed Artifacts

Write the following files to `${knowledgeDir}/topics/${topic-id}/`:

**overview.md:**
```markdown
# ${topic-id}

Brief 2-3 sentence summary of the idea.

## Keywords
- keyword1
- keyword2
- keyword3
```

**seed.md:**
```markdown
# Seed: ${idea title}

## Vision
What problem does this solve? Who benefits?

## Core Concept
High-level description of the solution.

## Key Features
1. Feature one
2. Feature two
3. Feature three

## Open Questions
- Question 1?
- Question 2?
```

**success-metrics.md:**
```markdown
# Success Metrics

## Primary Metrics
- Metric 1: description and target
- Metric 2: description and target

## Secondary Metrics
- Metric 3: description
```

**assumptions.md:**
```markdown
# Assumptions

## Technical Assumptions
- Assumption 1
- Assumption 2

## User Assumptions
- Assumption 3
- Assumption 4

## Business Assumptions
- Assumption 5
```

**constraints.md:**
```markdown
# Constraints

## Technical Constraints
- Constraint 1
- Constraint 2

## Time/Resource Constraints
- Constraint 3

## Scope Constraints
- Constraint 4
```

**mvp-scope.md:**
```markdown
# MVP Scope

## In Scope (MVP)
- Feature 1
- Feature 2
- Feature 3

## Out of Scope (Post-MVP)
- Feature 4
- Feature 5

## Success Criteria
- Criterion 1
- Criterion 2
```

**sources.md:**
```markdown
# Sources

- Seed input only (user-provided idea)
```

### Step 5: Update Knowledge Index

Read `${knowledgeDir}/index.json`, add new topic entry:

```json
{
  "id": "${topic-id}",
  "title": "${idea title}",
  "keywords": ["keyword1", "keyword2", ...],
  "overview": "topics/${topic-id}/overview.md",
  "sources": "topics/${topic-id}/sources.md"
}
```

Update the `updated` field to today's date. Write back to `index.json`.

### Step 6: Report Results

Summarize for the user:
```
Created seed artifacts in ${knowledgeDir}/topics/${topic-id}/:
- overview.md
- seed.md
- success-metrics.md
- assumptions.md
- constraints.md
- mvp-scope.md
- sources.md

Next steps:
- Review and refine the seed artifacts
- Run /irf-backlog-lite ${topic-id} to create implementation tickets
```

## Comparison to /irf-seed

| Aspect | /irf-seed | /irf-seed-lite |
|--------|-----------|----------------|
| Subagents | 1 (irf-planner) | 0 |
| Model change | Via subagent | Via switch_model |
| Reliability | Lower | Higher |
