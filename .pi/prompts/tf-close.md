---
description: Close phase for TF workflow - verify quality gate, commit, and close ticket [tf-close]
model: chutes/zai-org/GLM-4.7-Flash
thinking: medium
skill: tf-close
---

# /tf-close

Execute the Close phase for TF workflow ticket implementation.

## Usage

```
/tf-close <ticket-id>
```

## Arguments

- `<ticket-id>` - The ticket to close (e.g., `pt-1234`)

## Execution

Follow the **Post-Fix Verification** and **Close Ticket** procedures from tf-workflow skill:

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
3. **Load retry state** to get attempt info
4. **Get ticket details**: `tk show {ticket}`

### Step 2: Post-Fix Verification

**When quality gate is enabled** (`workflow.enableQualityGate: true`):

1. **Try CLI first**:
   ```bash
   tf post-fix-verify {ticket-id} --write
   ```
   This writes `{artifactDir}/post-fix-verification.md`

2. **Manual fallback** (if CLI not available):
   - Read `{artifactDir}/review.md` for pre-fix severity counts
   - Read `{artifactDir}/fixes.md` for what was fixed
   - Calculate: `post_fix = max(0, pre_fix - fixed)` (note: assumes 1:1 fix-to-issue mapping)
   - If a single fix addresses multiple issues or multiple fixes address one issue, manually adjust the counts
   
   Write `{artifactDir}/post-fix-verification.md`:
   ```markdown
   # Post-Fix Verification: {ticket-id}

   ## Summary
   - **Status**: PASS|FAIL
   - **Quality Gate**: blocks on {failOn_severities}

   ## Pre-Fix Counts (from review.md)
   - **Critical**: {pre_fix[Critical]}
   - **Major**: {pre_fix[Major]}
   - **Minor**: {pre_fix[Minor]}
   - **Warnings**: {pre_fix[Warnings]}
   - **Suggestions**: {pre_fix[Suggestions]}

   ## Fixes Applied (from fixes.md)
   - **Critical**: {fixed[Critical]}
   - **Major**: {fixed[Major]}
   - **Minor**: {fixed[Minor]}
   - **Warnings**: {fixed[Warnings]}
   - **Suggestions**: {fixed[Suggestions]}

   ## Post-Fix Counts (calculated)
   - **Critical**: {post_fix[Critical]}
   - **Major**: {post_fix[Major]}
   - **Minor**: {post_fix[Minor]}
   - **Warnings**: {post_fix[Warnings]}
   - **Suggestions**: {post_fix[Suggestions]}

   ## Quality Gate Decision
   - **Based on**: Post-fix counts
   - **Result**: {PASS|BLOCKED}
   - **Reason**: {explanation}
   ```

### Step 3: Check Close Gating

1. If `workflow.enableCloser` is false, write `{artifactDir}/close-summary.md` noting closure was skipped and do not call `tk`.
2. Determine which counts to use:
   - If `post-fix-verification.md` exists → use post-fix counts
   - Else → use pre-fix counts from `review.md`
3. If `workflow.failOn` has any non-zero severity → `closeStatus = BLOCKED`
4. Else → `closeStatus = CLOSED`

### Step 4: Update Retry State

If escalation is enabled (`workflow.escalation.enabled: true`):

1. Read or initialize `{artifactDir}/retry-state.json`
2. Create new attempt entry with:
   - attemptNumber
   - startedAt, completedAt timestamps
   - status (closed/blocked)
   - qualityGate counts
   - escalation models used
3. Write updated retry-state.json

**Retry State Schema**:
```json
{
  "version": 1,
  "ticketId": "pt-1234",
  "attempts": [
    {
      "attemptNumber": 1,
      "startedAt": "2026-02-13T12:00:00Z",
      "completedAt": "2026-02-13T12:30:00Z",
      "status": "closed|blocked",
      "trigger": "initial|retry",
      "qualityGate": {
        "failOn": ["Critical", "Major"],
        "counts": {"Critical": 0, "Major": 0, "Minor": 1}
      },
      "escalation": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      },
      "closeSummaryRef": "close-summary.md"
    }
  ],
  "lastAttemptAt": "2026-02-13T12:00:00Z",
  "status": "closed|blocked",
  "retryCount": 0
}
```

### Step 5: Handle BLOCKED Status

- If `closeStatus == BLOCKED`: Write `{artifactDir}/close-summary.md` with status BLOCKED, skip calling `tk close`
- If `closeStatus == CLOSED`: Continue with close workflow

### Step 6: Read Artifacts

Read:
- `{artifactDir}/implementation.md`
- `{artifactDir}/review.md`
- `{artifactDir}/fixes.md` (if exists)
- `{artifactDir}/files_changed.txt`

### Step 7: Commit Changes

1. Stage ticket artifacts:
   ```bash
   git add -A -- "{artifactDir}"
   ```
2. Stage changed files from `files_changed.txt`:
   ```bash
   while IFS= read -r path; do
     git add -A -- "$path" 2>/dev/null || true
   done < "{artifactDir}/files_changed.txt"
   ```
3. Commit if changes exist:
   ```bash
   if git diff --cached --quiet; then
     echo "No changes to commit"
     commit_hash="none"
   else
     # Verify git config is set
     if ! git config user.email >/dev/null 2>&1; then
       echo "Warning: git user.email not configured, skipping commit"
       commit_hash="none"
     else
       if git commit -m "{ticket-id}: <short summary>"; then
         commit_hash=$(git rev-parse HEAD)
       else
         echo "Warning: git commit failed (check hooks, GPG signing, etc.)"
         commit_hash="failed"
       fi
     fi
   fi
   ```

### Step 8: Add Note and Close Ticket

1. Compose summary note (include commit hash if available, retry attempt if > 1)
2. Add note via `tk add-note`
3. Close ticket via `tk close` (only if `closeStatus == CLOSED`)

### Step 9: Write close-summary.md

```markdown
# Close Summary: {ticket-id}

## Status
**{CLOSED|BLOCKED}**

## Summary
- Attempt: {attemptNumber}
- Quality Gate: {PASS|FAIL}
- Commit: {commit-hash or 'none'}

## Review Summary
- Critical: {count}
- Major: {count}
- Minor: {count}

## Fixes Applied
- Critical: {fixed}
- Major: {fixed}
- Minor: {fixed}
```

## Output

**Always written:**
- `{artifactDir}/close-summary.md` - Final summary
- `{artifactDir}/post-fix-verification.md` - Post-fix verification (when quality gate enabled)
- `{artifactDir}/chain-summary.md` - Links to all artifacts

**Preserve from previous phases:**
- `{artifactDir}/research.md`
- `{artifactDir}/implementation.md`
- `{artifactDir}/review.md`
- `{artifactDir}/fixes.md`
- `{artifactDir}/ticket_id.txt`
- `{artifactDir}/files_changed.txt`
- `{artifactDir}/retry-state.json` (if escalation enabled)
