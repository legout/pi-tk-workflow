---
description: Convert OpenSpec change into small, self-contained IRF tickets. Lite version - no subagent, uses model-switch.
---

# IRF from OpenSpec (Lite)

Create small, self-contained IRF tickets from an OpenSpec change. Each ticket includes summarized context so it can be implemented without loading full planning docs.

## Invocation

```
/irf-from-openspec-lite <change-id or path>
```

If `$@` is empty, ask user for a change id or path and stop.

## Prerequisites

Verify `switch_model` tool is available. If not, suggest using `/irf-from-openspec` (original) instead.

## Execution

### Step 1: Switch to Planning Model

```
Use switch_model tool with action="switch", search="gpt-5.1-codex-mini" (or config model)
```

### Step 2: Locate Change Directory

**If `$@` is a path:**
- Verify directory exists
- Use it directly

**If `$@` is a change ID:**
- Look for `openspec/changes/${change_id}/`
- If not found, try `changes/${change_id}/`
- If still not found, ask user for explicit path

### Step 3: Read OpenSpec Artifacts

Read from the change directory:

**Required:**
- `tasks.md` - list of implementation tasks

**Optional (for context extraction):**
- `proposal.md` - change proposal
- `design.md` - technical design
- `scope.md` - scope definition

If `tasks.md` doesn't exist:
- Inform user this is required
- Stop

### Step 4: Parse Tasks and Extract Context

Extract tasks from `tasks.md`. For each task:

1. **Identify the specific task** from tasks.md
2. **Find related context** in proposal.md and design.md
3. **Extract only relevant sections** - not full documents
4. **Note technical constraints** that affect implementation

### Step 5: Create Small, Self-Contained Tickets

For each task, create a ticket with **summarized context** (not full doc references).

**Ticket Size Guidelines:**
- **30 lines or less** in description
- **1-2 hours** estimated work
- **Self-contained** - implementable without reading full proposal/design

**Description Template:**

```markdown
## Task
<Specific, single-responsibility task description>

## Context
<2-3 sentences summarizing relevant context from OpenSpec>

## Technical Details
<Key technical decisions from design.md that affect this task>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>
- [ ] Tests added/updated

## Constraints
- <relevant constraint from proposal/scope>

## References
- OpenSpec Change: ${change_id}
- Proposal: openspec/changes/${change_id}/proposal.md
- Design: openspec/changes/${change_id}/design.md
```

**Example Good Ticket (20 lines):**
```markdown
## Task
Add OAuth2 PKCE flow to authentication endpoint

## Context
The auth system needs to support mobile clients that cannot keep secrets.
PKCE extends the authorization code flow for public clients.

## Technical Details
- Use S256 code challenge method
- Store code_verifier in short-lived cache (5 min)
- Extend existing /auth endpoint

## Acceptance Criteria
- [ ] PKCE parameters (code_challenge, code_challenge_method) accepted
- [ ] Token exchange validates code_verifier
- [ ] Backward compatible with non-PKCE clients
- [ ] Unit tests for PKCE flow

## Constraints
- Must maintain backward compatibility with existing auth flow

## References
- OpenSpec Change: auth-pkce-support
- Design: openspec/changes/auth-pkce-support/design.md
```

**Example Bad Ticket (too large/vague):**
```markdown
## Task
Implement authentication improvements

## Context
See full proposal at openspec/changes/auth/proposal.md

## Acceptance Criteria
- [ ] Improve auth system
- [ ] Add security features
- [ ] Update documentation
```

**Split large tasks:**
- If a task in tasks.md describes multiple days of work, split it
- Create multiple tickets with dependencies
- Example: "Implement user management" → "Create user model", "Add user API", "Build user UI"

### Step 6: Create Tickets

```bash
tk create "<task title>" \
  --description "<description from template above>" \
  --tags irf,openspec \
  --type task \
  --priority 2
```

**Guidelines:**
- Each ticket maps to **one task** from tasks.md (or a split of one task)
- **Summarize** design decisions in 2-3 sentences, don't paste full design.md
- **Include constraints** that directly affect implementation
- **Keep acceptance criteria specific and testable**
- **Link** to full docs for reference, don't include them

### Step 7: Write Backlog Artifact

Write `backlog.md` to the change directory:

```markdown
# Backlog: ${change_id}

Generated from: ${change_dir}/
Date: ${today}

## OpenSpec References
- Change ID: ${change_id}
- Proposal: ${proposal.md path or "N/A"}
- Design: ${design.md path or "N/A"}
- Tasks: ${tasks.md path}

## Tickets Created

| ID | Title | Est. Hours | OpenSpec Task |
|----|-------|------------|---------------|
| ${id-1} | ${title-1} | 1-2 | Task 1 from tasks.md |
| ${id-2} | ${title-2} | 1-2 | Task 2 from tasks.md |
| ... | ... | ... | ... |

## Summary
- Total tickets: ${count}
- Total estimated hours: ${min}-${max}
- Tags: irf, openspec
```

### Step 8: Report Results

```
Created ${count} small tickets from OpenSpec change ${change_id}:

${ticket list with IDs, titles, and estimates}

Total estimated effort: ${min}-${max} hours

Each ticket includes summarized context and links to full OpenSpec docs.

Backlog written to: ${change_dir}/backlog.md

Next steps:
- Review tickets in tk
- Adjust priorities/dependencies if needed
- Start implementation with /irf-lite <ticket-id>
```

## Comparison to /irf-from-openspec

| Aspect | /irf-from-openspec | /irf-from-openspec-lite |
|--------|--------------------|-----------------------|
| Subagents | 1 (irf-planner) | 0 |
| Ticket size | Variable | Small (1-2 hours, 30 lines) |
| Self-contained | May paste full docs | Summarized context |
| Model change | Via subagent | Via switch_model |
| Reliability | Lower | Higher |
