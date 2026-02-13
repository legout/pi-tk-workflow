---
name: tf-fix
description: Fix phase for TF workflow - apply fixes based on review feedback. Use after review to address identified issues.
---

# TF Fix Skill

Fix phase for the IRF (Implement → Review → Fix → Close) workflow.

## When to Use This Skill

- After review phase completes
- When addressing review feedback
- Before close phase

## Prerequisites

- Review phase completed
- `{artifactDir}/review.md` exists

## Procedure

### Step 1: Load Context

1. **Read previous phase artifacts**:
   - `{artifactDir}/review.md` - Issues to fix
   - `{artifactDir}/implementation.md` - Original implementation

2. **Load retry state** (if escalation enabled):
   - Get `escalatedModels.fixer` for escalation support

### Step 2: Check if Fixer Enabled

From config:
- If `workflow.enableFixer` is false, write `{artifactDir}/fixes.md` noting fixer disabled and skip

### Step 3: Analyze Issues

Extract severity counts from `{artifactDir}/review.md`:

| Severity | Action |
|----------|--------|
| Critical | **Must fix** - required |
| Major | **Should fix** - strongly recommended |
| Minor | Fix if low effort |
| Warnings | **Do NOT fix** - defer to follow-up |
| Suggestions | **Do NOT fix** - defer to follow-up |

If zero Critical/Major/Minor: write "No fixes needed" to `{artifactDir}/fixes.md`, skip to return

### Step 4: Apply Fixes

1. **Fix all Critical issues** (required)
2. **Fix all Major issues** (should do)
3. **Fix Minor issues** if low effort
4. **Do NOT fix Warnings/Suggestions** (these become follow-up tickets)

Track edits via:
```bash
tf track {file1} {file2} --file {artifactDir}/files_changed.txt
```

### Step 5: Re-run Tests

```bash
# Run relevant tests after fixes
pytest tests/ -v
```

### Step 6: Write fixes.md

Write to `{artifactDir}/fixes.md`:

```markdown
# Fixes: {ticket-id}

## Summary
Brief description of fixes applied

## Fixes by Severity

### Critical (must fix)
- [x] `file.ts:42` - Issue description and fix applied

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

**Important**: Count an issue as fixed ONLY if it has `[x]` checkbox.

## Output Artifacts

| File | Description |
|------|-------------|
| `{artifactDir}/fixes.md` | Fixes applied with statistics |

## Error Handling

- If fix introduces new issues, document in fixes.md
- Continue even if some fixes cannot be applied
- Document unresolved issues clearly
