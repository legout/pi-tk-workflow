---
description: Scan ticket artifacts for missing followups.md and create follow-up tickets [tf-planning]
model: openai-codex/gpt-5.2
thinking: medium
skill: tf-planning
---

# /tf-followups-scan

Scan implemented ticket artifact directories and run follow-up creation for those missing `followups.md`.

## Usage

```
/tf-followups-scan [--apply]
```

## Arguments

- `--apply` - Perform actual changes (create tickets, write files). Without this flag, runs in dry-run mode.

## Default Behavior (Dry-Run)

By default, the command **does not**:
- Create any tickets via `tk create`
- Write any `followups.md` files

It only scans and reports what would be done.

## Execution

Execute the following procedure:

### 1. Resolve Knowledge Directory

Read `workflow.knowledgeDir` from `.tf/config/settings.json` (default: `.tf/knowledge`).
Set `ticketsDir = {knowledgeDir}/tickets/`.

### 2. Scan Ticket Directories

Iterate all subdirectories in `{ticketsDir}`:
- For each `{ticket-id}/` directory:
  - Check if `close-summary.md` exists (indicates implemented/closed ticket)
  - Check if `followups.md` does NOT exist
  - If both conditions met: ticket is **eligible**

### 3. Per-Ticket Processing

For each eligible ticket:

1. Read `{ticket-dir}/review.md`
2. Parse for Warnings and Suggestions sections
3. If items found:
   - **Dry-run**: Print `[DRY-RUN] Would create N follow-up tickets for {ticket-id}`
   - **Apply mode**:
     - Create follow-up tickets via `tk create` for each Warning/Suggestion
     - Use tags: `tf,followup`
     - Priority: 3
     - Write `{ticket-dir}/followups.md` documenting created tickets
4. If no items found:
   - **Dry-run**: Print `[DRY-RUN] Would mark {ticket-id} as processed (no follow-ups needed)`
   - **Apply mode**: Write `{ticket-dir}/followups.md` with "No follow-ups needed"

### 4. Skip Rules

Skip directories that already have `followups.md` (idempotent).

### 5. Output Summary

Print final summary:
```
=== Follow-ups Scan Summary ===
Scanned: {N} ticket directories
Eligible: {N} tickets (have close-summary.md, missing followups.md)
Processed: {N} tickets
  - Follow-up tickets created: {N}
  - Marked as "none needed": {N}
Skipped: {N} tickets (already have followups.md)
```

## Ticket Description Template (for created tickets)

```markdown
## Origin
From review of ticket: {original_ticket_id}
File: {file_path}
Line: {line_number}

## Issue
{description from review}

## Severity
{Warning or Suggestion}

## Acceptance Criteria
- [ ] {specific fix}
- [ ] Tests updated if applicable
- [ ] No regressions
```

## Output Artifacts

When `--apply` is used:
- Tickets created in `tk` (tagged: tf, followup)
- `{ticket-dir}/followups.md` written for each processed ticket

## Examples

```bash
# Dry-run: see what would be processed
/tf-followups-scan

# Actually create tickets and write files
/tf-followups-scan --apply
```

## Notes

- Safe/idempotent: re-running won't re-process tickets
- Only processes tickets with `close-summary.md` (indicates implemented/closed ticket)
- Warnings = technical debt (should address)
- Suggestions = improvements (nice to have)
