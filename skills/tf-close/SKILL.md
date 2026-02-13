---
name: tf-close
description: Close phase for TF workflow - verify quality gate, commit, and close ticket. Use after fixes to finalize the workflow.
---

# TF Close Skill

Close phase for the IRF (Implement → Review → Fix → Close) workflow.

## When to Use This Skill

- After fix phase completes
- When finalizing the workflow
- To commit changes and close the ticket

## Prerequisites

- Fix phase completed (or skipped)
- All phase artifacts exist

## Procedure

### Step 1: Load Context

1. **Read all phase artifacts**:
   - `{artifactDir}/implementation.md`
   - `{artifactDir}/review.md`
   - `{artifactDir}/fixes.md` (if exists)
   - `{artifactDir}/files_changed.txt`

2. **Load retry state** (if escalation enabled)

### Step 2: Quality Gate Check

1. **Determine counts source**:
   - If `{artifactDir}/post-fix-verification.md` exists: use post-fix counts
   - Else: parse `{artifactDir}/review.md` for pre-fix counts

2. **Extract severity counts**:
   ```python
   for sev in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
       match = re.search(rf'{sev}\s*:\s*(\d+)', content)
       counts[sev] = int(match.group(1)) if match else 0
   ```

3. **Check quality gate**:
   - If `workflow.enableQualityGate` is true
   - If any severity in `workflow.failOn` has nonzero count
   - Set `closeStatus = BLOCKED`

### Step 3: Handle BLOCKED Status

If `closeStatus == BLOCKED`:
1. Write `{artifactDir}/close-summary.md` with status BLOCKED
2. Update retry state
3. **Do NOT call `tk close`**
4. Return early

### Step 4: Update Retry State (if enabled)

Update `{artifactDir}/retry-state.json`:
```json
{
  "version": 1,
  "ticketId": "{ticket-id}",
  "attempts": [...],
  "lastAttemptAt": "{timestamp}",
  "status": "closed",
  "retryCount": 0
}
```

### Step 5: Commit Changes (required)

```bash
# Stage ticket artifacts
git add -A -- "{artifactDir}"

# Stage changed files
while IFS= read -r path; do
  git add -A -- "$path" 2>/dev/null || true
done < "{artifactDir}/files_changed.txt"

# Commit
git commit -m "{ticket-id}: <short summary>"
```

Capture commit hash for ticket note.

### Step 6: Compose Summary Note

Include:
- Summary of what was done
- Commit hash
- Retry attempt (if > 1)
- Key decisions

### Step 7: Add Note and Close

```bash
tk add-note {ticket} "{summary}"
tk close {ticket}
```

### Step 8: Write close-summary.md

```markdown
# Close Summary: {ticket-id}

## Status
**CLOSED** / **BLOCKED**

## Summary
Brief description of what was accomplished

## Acceptance Criteria
- [x] Criterion 1
- [x] Criterion 2

## Quality Gate
- **Status**: PASSED / FAILED
- **Fail on**: {severities}
- **Counts**: Critical({c}), Major({m}), Minor({n})

## Commit
`{hash}` - {message}

## Artifacts
- `research.md`
- `implementation.md`
- `review.md`
- `fixes.md`
- `close-summary.md`
```

## Output Artifacts

| File | Description |
|------|-------------|
| `{artifactDir}/close-summary.md` | Final summary with status |
| `{artifactDir}/chain-summary.md` | Artifact index |
| `{artifactDir}/retry-state.json` | Retry state (if enabled) |

## Error Handling

- If `git commit` fails, document in close-summary
- If `tk close` fails, document error but don't fail workflow
- Always write close-summary.md regardless of errors
