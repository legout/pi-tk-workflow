---
description: Create an implementation plan document [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-plan

Create a single plan document for a project, feature, or refactor.

## Usage

```
/irf-plan <request description>
```

## Arguments

- `$@` - The request description for the plan

## Example

```
/irf-plan Refactor auth flow to support OAuth + magic links
```

## Execution

Follow the **IRF Planning Skill** "Plan Interview (Planner)" procedure:

1. Create `plan-*` topic ID
2. Create `.pi/knowledge/topics/{topic-id}/`
3. Write `plan.md` (single source of truth)
4. Update `index.json`

## Output

- `plan.md` in `.pi/knowledge/topics/{topic-id}/`
- Status set to `draft`

## Next Steps

Run consultant and reviewer:
```
/irf-plan-consult {topic-id}
/irf-plan-revise {topic-id}
/irf-plan-review {topic-id} --high-accuracy
```
