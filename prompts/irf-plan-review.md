---
description: Review an implementation plan with high-accuracy validation [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-plan-review

Validate a plan with high-precision checks. Updates the same `plan.md`.

## Usage

```
/irf-plan-review <plan-id-or-path> [--high-accuracy]
```

## Arguments

- `$1` - Plan topic ID (`plan-*`) or path to plan directory
- `--high-accuracy` - Trigger stricter validation and rejection on gaps
- If omitted: auto-locates if exactly one plan exists

## Example

```
/irf-plan-review plan-auth-rewrite --high-accuracy
```

## Execution

Follow the **IRF Planning Skill** "Plan Review (High-Accuracy)" procedure:

1. Locate plan directory
2. Read `plan.md`
3. Validate requirements, constraints, risks, sequencing, acceptance criteria
4. Append Reviewer Notes with PASS/FAIL
5. Set status to `approved` or `blocked`

## Output

- Updated `plan.md` with review status
