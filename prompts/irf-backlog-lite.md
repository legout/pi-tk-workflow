---
description: Create small, actionable implementation tickets from seed artifacts. Lite version - no subagent, uses model-switch.
---

# IRF Backlog (Lite)

Generate a small, actionable ticket backlog from IRF seed artifacts. Creates self-contained tickets that can be implemented without loading full planning docs.

## Invocation

```
/irf-backlog-lite <optional seed path or topic-id>
```

If `$@` is empty, attempt to locate a single seed automatically.

## Prerequisites

Verify `switch_model` tool is available. If not, suggest using `/irf-backlog` (original) instead.

## Execution

### Step 1: Switch to Planning Model

```
Use switch_model tool with action="switch", search="gpt-5.1-codex-mini" (or config model)
```

### Step 2: Load Config

Read workflow config (project overrides global).

Extract `workflow.knowledgeDir` (default: ".pi/knowledge").

### Step 3: Locate Seed

**If `$@` is provided:**
- If it's a path to a file, use its directory as the topic directory
- If it's a topic-id, use `${knowledgeDir}/topics/${topic-id}/`

**If `$@` is empty:**
```bash
find ${knowledgeDir}/topics -name "seed.md" -type f
```
- If exactly one found: use it
- If multiple found: list them and ask user to specify
- If none found: inform user and stop

### Step 4: Read Seed Artifacts

Read from the topic directory:
- `seed.md` (required)
- `mvp-scope.md` (if exists)
- `success-metrics.md` (if exists)
- `constraints.md` (if exists)

### Step 5: Create Small, Self-Contained Tickets

Based on the seed content, create **5-15 small, implementable tickets**.

**Ticket Size Guidelines:**
- Each ticket should be completable in **1-2 hours maximum**
- **30 lines or less** in the description
- **Single responsibility** - one feature or fix per ticket
- **Self-contained** - includes all context needed to implement

**For each ticket:**

1. Extract a **single, focused task** from the seed/MVP scope
2. **Summarize relevant context** in 2-3 sentences (don't link to full docs)
3. List **3-5 specific acceptance criteria** as checkboxes
4. Include **constraint references** if they affect implementation
5. Create via `tk`:
   ```bash
   tk create "<title>" --description "<description>" --tags irf,backlog --type task --priority 2
   ```

**Ticket Description Template (30-50 lines max):**

```markdown
## Task
<Single-sentence description of what to implement>

## Context
<2-3 sentences summarizing relevant context from seed/MVP scope>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

## Constraints
- <relevant constraint 1 from constraints.md>
- <relevant constraint 2 from constraints.md>

## References
- Seed: <topic-id>
- MVP Scope: <knowledgeDir>/topics/<topic-id>/mvp-scope.md
```

**Example Good Ticket (25 lines):**
```markdown
## Task
Implement database connection pool with max 10 connections

## Context
The auth service needs persistent DB connections for session storage. 
Use the existing postgres client from src/lib/db.ts.

## Acceptance Criteria
- [ ] Connection pool created with max 10 connections
- [ ] Pool recycles connections after 30s idle
- [ ] Graceful shutdown closes all connections
- [ ] Tests verify pool behavior under load

## Constraints
- Must not exceed 10 concurrent DB connections (shared instance)

## References
- Seed: seed-auth-service
```

**Example Bad Ticket (too large):**
```markdown
## Task
Implement entire authentication system

## Context
[... 200 lines of detailed requirements ...]

## Acceptance Criteria
- [ ] Login page
- [ ] Signup flow  
- [ ] Password reset
- [ ] OAuth integration
- [ ] Session management
- [ ] 2FA support
- [ ] Admin dashboard
```

### Step 6: Write Backlog Artifact

Write `backlog.md` to the same topic directory:

```markdown
# Backlog: ${topic-id}

Generated from: seed.md
Date: ${today}

## Tickets

| ID | Title | Est. Hours | Dependencies |
|----|-------|------------|--------------|
| ${id-1} | ${title-1} | 1-2 | - |
| ${id-2} | ${title-2} | 1-2 | ${id-1} |
| ... | ... | ... | ... |

## Summary
- Total tickets: ${count}
- Total estimated hours: ${min}-${max}
- Tags: irf, backlog

## Implementation Order
1. ${id-1}: ${title-1}
2. ${id-2}: ${title-2}
...
```

### Step 7: Report Results

Summarize for the user:
```
Created ${count} small tickets from seed:

${ticket-list with IDs, titles, and estimates}

Total estimated effort: ${min}-${max} hours

Backlog written to: ${knowledgeDir}/topics/${topic-id}/backlog.md

Next steps:
- Review tickets in tk (each is self-contained)
- Adjust priorities if needed
- Start implementation with /irf-lite <ticket-id>
```

## Comparison to /irf-backlog

| Aspect | /irf-backlog | /irf-backlog-lite |
|--------|--------------|-------------------|
| Subagents | 1 (irf-planner) | 0 |
| Ticket size | Variable | Small (1-2 hours, 30 lines) |
| Self-contained | May reference docs | Includes summarized context |
| Model change | Via subagent | Via switch_model |
| Reliability | Lower | Higher |
