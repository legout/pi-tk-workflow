---
description: Revise an implementation plan based on feedback [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-plan-revise

Revise a plan based on consultant/reviewer feedback. Updates the same `plan.md`.

## Usage

```
/irf-plan-revise <plan-id-or-path>
```

## Arguments

- `$1` - Plan topic ID (`plan-*`) or path to plan directory
- If omitted: auto-locates if exactly one plan exists

## Example

```
/irf-plan-revise plan-auth-rewrite
```

## Execution

Follow the **IRF Planning Skill** "Plan Revision" procedure:

1. Locate plan directory
2. Read `plan.md` + notes
3. Apply revisions and append a revision note
4. Set status to `revised`

## Output

- Updated `plan.md` ready for re-review
