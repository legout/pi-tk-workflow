---
description: Create tickets from OpenSpec change [tf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: tf-planning
---

# /tf-from-openspec

Create small, self-contained IRF tickets from an OpenSpec change.

## Usage

```
/tf-from-openspec <change-id-or-path>
```

## Arguments

- `$1` - OpenSpec change ID or path to change directory

## Examples

```
/tf-from-openspec auth-pkce-support
/tf-from-openspec openspec/changes/auth-pkce-support/
```

## Execution

Follow the **IRF Planning Skill** "OpenSpec Bridge" procedure:

1. Locate change:
   - Try `openspec/changes/{id}/`
   - Fallback: `changes/{id}/`
2. Read artifacts:
   - `tasks.md` (required)
   - `proposal.md`, `design.md` (for context)
3. Parse tasks:
   - Extract each task from tasks.md
   - Pull relevant context from proposal/design
   - Split large tasks into 1-2 hour chunks
4. Create tickets with template:
   ```markdown
   ## Task
   <Specific task>

   ## Context
   <2-3 sentences from OpenSpec>

   ## Technical Details
   <Key decisions affecting this task>

   ## Acceptance Criteria
   - [ ] <criterion 1>
   - [ ] Tests added

   ## Constraints
   <Relevant constraints>

   ## References
   - OpenSpec Change: {change_id}
   ```
5. Create via `tk`:
   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags tf,openspec \
     --type task \
     --priority 2 \
     --external-ref "openspec-{change_id}"
   ```
6. Write `backlog.md` in change directory

## Ticket Guidelines

- **30 lines or less** in description
- **1-2 hours** estimated work
- **Self-contained** - implementable without reading full OpenSpec
- Summarize design decisions (don't paste full docs)

## Output

- Tickets created in `tk` (tagged: tf, openspec, external-ref: openspec-{change_id})
- `backlog.md` in change directory

## Next Steps

Start implementation:
```
/tf <ticket-id>
```
