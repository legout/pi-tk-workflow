---
description: Consult an implementation plan for gaps and ambiguities [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-plan-consult

Review a plan for gaps, ambiguities, and over-engineering. Updates the same `plan.md`.

## Usage

```
/irf-plan-consult <plan-id-or-path>
```

## Arguments

- `$1` - Plan topic ID (`plan-*`) or path to plan directory
- If omitted: auto-locates if exactly one plan exists

## Example

```
/irf-plan-consult plan-auth-rewrite
```

## Execution

Follow the **IRF Planning Skill** "Plan Consultant (Gap Detection)" procedure:

1. Locate plan directory
2. Read `plan.md`
3. Update plan sections and Consultant Notes
4. Set status to `consulted`

## Output

- Updated `plan.md` with Consultant Notes
