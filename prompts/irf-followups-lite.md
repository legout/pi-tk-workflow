---
description: Create follow-up tickets from review warnings/suggestions. Lite version - no subagent, uses model-switch.
---

# IRF Followups (Lite)

Create follow-up tickets from Warnings and Suggestions in a review. This version runs inline with model-switch instead of spawning a subagent.

## Invocation

```
/irf-followups-lite <review path or ticket-id>
```

If `$@` is empty and `review.md` exists in current directory, use it.

## Prerequisites

Verify `switch_model` tool is available. If not, suggest using `/irf-followups` (original) instead.

## Execution

### Step 1: Switch to Planning Model

```
Use switch_model tool with action="switch", search="gpt-5.1-codex-mini" (or config model)
```

### Step 2: Resolve Review Path

**If `$@` is empty:**
- Check if `review.md` exists in current directory
- If yes, use it
- If no, ask user for path and stop

**If `$@` is a path:**
- Verify file exists
- Use it directly

**If `$@` looks like a ticket ID (e.g., `mme-a1b2`):**
- Search for matching review:
  ```bash
  find /tmp/pi-chain-runs -name "review.md" -exec grep -l "# Review: $ticket_id" {} \; 2>/dev/null | head -1
  ```
- If found, use the newest match
- If not found, ask user for explicit path

### Step 3: Parse Review

Read the review file and extract:

**Warnings section:**
```
## Warnings (follow-up ticket)
- `file.ts:200` - Issue description
- `file.ts:210` - Another issue
```

**Suggestions section:**
```
## Suggestions (follow-up ticket)
- `file.ts:300` - Improvement idea
- `file.ts:310` - Another suggestion
```

If neither section exists or both are empty:
- Write `followups.md` stating "No follow-ups needed"
- Report to user and stop

### Step 4: Create Tickets

For each warning and suggestion, create a ticket:

```bash
tk create "<title derived from issue>" \
  --description "<full description with file:line reference>" \
  --tags irf,followup \
  --type task \
  --priority 3
```

**Title guidelines:**
- Keep concise but descriptive
- Include component/file name if relevant
- Example: "Add error handling to UserService.validate"

**Description template:**
```
## Origin
From review of ticket: ${original_ticket_id}
File: ${file_path}
Line: ${line_number}

## Issue
${description from review}

## Severity
${Warning or Suggestion}

## Acceptance Criteria
- [ ] ${specific fix or improvement}
- [ ] Tests updated if applicable
- [ ] No regressions introduced
```

### Step 5: Write Followups Artifact

Write `followups.md` to the same directory as the review:

```markdown
# Follow-up Tickets: ${original_ticket_id}

Generated from: ${review_path}
Date: ${today}

## Summary
- Warnings: ${warning_count}
- Suggestions: ${suggestion_count}
- Total tickets created: ${total_count}

## Tickets Created

### From Warnings

| ID | Title | File:Line |
|----|-------|-----------|
| ${id-1} | ${title-1} | ${file:line} |
| ${id-2} | ${title-2} | ${file:line} |

### From Suggestions

| ID | Title | File:Line |
|----|-------|-----------|
| ${id-3} | ${title-3} | ${file:line} |
| ${id-4} | ${title-4} | ${file:line} |

## Notes
- All tickets tagged with: irf, followup
- Priority: 3 (normal)
```

If no items found:
```markdown
# Follow-up Tickets: ${original_ticket_id}

Generated from: ${review_path}
Date: ${today}

No follow-ups needed. Review contained no Warnings or Suggestions.
```

### Step 6: Report Results

```
Created ${count} follow-up tickets from review:

Warnings (${warning_count}):
${list of warning ticket IDs and titles}

Suggestions (${suggestion_count}):
${list of suggestion ticket IDs and titles}

Written to: ${followups_path}
```

## Comparison to /irf-followups

| Aspect | /irf-followups | /irf-followups-lite |
|--------|----------------|---------------------|
| Subagents | 1 (irf-planner) | 0 |
| Model change | Via subagent | Via switch_model |
| Reliability | Lower | Higher |
