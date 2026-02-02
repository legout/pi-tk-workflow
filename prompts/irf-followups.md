---
description: Create tickets from review warnings/suggestions [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-followups

Create follow-up tickets from Warnings and Suggestions in a review.

## Usage

```
/irf-followups <review-path-or-ticket-id>
```

## Arguments

- `$1` - Path to review.md or original ticket ID
- If omitted: uses `./review.md` if it exists

## Examples

```
/irf-followups ./review.md
/irf-followups abc-1234
```

## Execution

Follow the **IRF Planning Skill** "Follow-up Creation" procedure:

1. Resolve review path:
   - If path: use directly
   - If ticket ID: search `/tmp/pi-chain-runs` for matching review
   - If empty: check `./review.md`
2. Parse review:
   - Extract Warnings section
   - Extract Suggestions section
3. For each item, create ticket:
   ```bash
   tk create "<title>" \
     --description "## Origin\nFrom review of: {ticket}\nFile: {file}\nLine: {line}\n\n## Issue\n{description}" \
     --tags irf,followup \
     --priority 3
   ```
4. Write `followups.md` documenting created tickets

## Ticket Description Template

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

## Output

- Tickets created in `tk` (tagged: irf, followup)
- `followups.md` with summary

## Notes

- Warnings = technical debt, should address
- Suggestions = improvements, nice to have
- Both are out of scope for the original ticket
- Priority is lower (3) than implementation tickets
