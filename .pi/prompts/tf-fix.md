---
description: Fix phase for TF workflow - apply fixes based on review feedback [tf-fix]
model: zai/glm-5
thinking: high
skill: tf-fix
---

# /tf-fix

Execute the Fix phase for TF workflow ticket implementation.

## Usage

```
/tf-fix <ticket-id>
```

## Arguments

- `<ticket-id>` - The ticket to fix (e.g., `pt-1234`)

## Execution

Follow the **Fix Issues** procedure from tf-workflow skill:

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
3. **Load retry state** to get `escalatedModels` for fixer
4. **Get ticket details**: `tk show {ticket}`

### Step 2: Check if Fixer is Enabled

From config (`.tf/config/settings.json`):
- If `workflow.enableFixer` is false, write `{artifactDir}/fixes.md` noting the fixer is disabled and skip this step.

### Step 3: Check Review Issues

- Read `{artifactDir}/review.md`
- If zero Critical/Major/Minor: write "No fixes needed" to `{artifactDir}/fixes.md`, skip to end

### Step 4: Fix Issues

Fix in priority order:
- **Critical** - Required to fix
- **Major** - Should fix
- **Minor** - Fix if low effort
- **Warnings** - Do NOT fix (become follow-up tickets)
- **Suggestions** - Do NOT fix (become follow-up tickets)

**Regression handling**: After applying fixes, re-run tests. If tests fail or new issues are introduced:
1. Revert the changes that caused the regression
2. Document the regression in `fixes.md`
3. Do NOT proceed to close - the quality gate will catch this

Track edits via updating `{artifactDir}/files_changed.txt` (use atomic write: write to temp file then rename).

### Step 5: Re-run Tests

After fixes, run relevant tests to verify.

### Step 6: Write fixes.md

Write to `{artifactDir}/fixes.md`:

```markdown
# Fixes: {ticket-id}

## Summary
Brief description of fixes applied

## Fixes by Severity

### Critical (must fix)
- [x] `file.ts:42` - Issue description and fix applied
- [x] `file.ts:45` - Another critical fix

### Major (should fix)
- [x] `file.ts:100` - Issue description and fix applied

### Minor (nice to fix)
- [x] `file.ts:150` - Issue description and fix applied

### Warnings (follow-up)
- [ ] `file.ts:200` - Not fixed (deferred to follow-up)

### Suggestions (follow-up)
- [ ] `file.ts:250` - Not fixed (deferred to follow-up)

## Summary Statistics
- **Critical**: {count_fixed}
- **Major**: {count_fixed}
- **Minor**: {count_fixed}
- **Warnings**: 0
- **Suggestions**: 0

## Verification
- Commands run to verify fixes
- Test results
```

**Important**: The Summary Statistics section is required for Post-Fix Verification.

## Output

**Always written:**
- `{artifactDir}/fixes.md` - Fixes applied

**Preserve from previous phases:**
- `{artifactDir}/research.md`
- `{artifactDir}/implementation.md`
- `{artifactDir}/review.md`
- `{artifactDir}/ticket_id.txt`
- `{artifactDir}/files_changed.txt`
