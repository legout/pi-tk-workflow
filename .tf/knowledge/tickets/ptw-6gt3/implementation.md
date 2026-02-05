# Implementation: ptw-6gt3

## Summary
Update the backlog.md writer in the tf-planning skill to include component tags and linked ticket IDs in the summary table.

## Files Changed
- `skills/tf-planning/SKILL.md` - Updated the "Write backlog.md" section (step 10) to include Components and Links columns

## Key Decisions
- Added "Components" column showing comma-separated tags (e.g., `tf, backlog, plan`)
- Added "Links" column showing comma-separated linked ticket IDs (e.g., `ptw-abc1, ptw-def2`)
- Used dash (`-`) as placeholder when no tags or links exist (consistent with "Depends On" column)
- Columns are positioned as: ID | Title | Est. Hours | Depends On | Components | Links
- This ordering keeps related metadata (deps, tags, links) together at the end

## Changes Made

### skills/tf-planning/SKILL.md

Updated the backlog.md template in step 10 of the Backlog Generation procedure:

**Before:**
```markdown
| ID   | Title   | Est. Hours | Depends On       |
| ---- | ------- | ---------- | ---------------- |
| {id} | {title} | 1-2        | {dep-ids-or-"-"} |
```

**After:**
```markdown
| ID   | Title   | Est. Hours | Depends On | Components | Links |
| ---- | ------- | ---------- | ---------- | ---------- | ----- |
| {id} | {title} | 1-2        | {deps}     | {tags}     | {links} |
```

Also updated the corresponding sample data rows to demonstrate the new format.

## Tests Run
- N/A - Documentation/template update

## Verification
- Reviewed the updated template format for readability
- Verified the format is consistent with existing conventions
- Confirmed new columns are optional/backward-compatible (existing backlog.md files without these columns will still parse correctly)
