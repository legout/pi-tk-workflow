---
description: Create tickets from seed, baseline, or plan artifacts [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-backlog

Generate small, actionable implementation tickets from seed (greenfield), baseline (brownfield), or plan artifacts.

## Usage

```
/irf-backlog <seed-baseline-or-plan-path-or-topic-id>
```

## Arguments

- `$1` - Path to seed/baseline/plan directory or topic ID (`seed-*`, `baseline-*`, or `plan-*`)
- If omitted: auto-locates if exactly one seed, baseline, or plan exists

## Examples

```
/irf-backlog seed-build-a-cli
/irf-backlog baseline-myapp
/irf-backlog plan-auth-rewrite
/irf-backlog .pi/knowledge/topics/baseline-myapp/
```

## Execution

Follow the **IRF Planning Skill** "Backlog Generation (Seed, Baseline, or Plan)" procedure:

1. Locate topic directory
2. Detect mode (seed vs baseline vs plan)
3. Read relevant artifacts and plan status (warn if plan not approved)
4. Create 5-15 small tickets (1-2 hours each, 30 lines max)
5. Create via `tk create`:

   **Seed:**
   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags irf,backlog \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```

   **Baseline:**
   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags irf,backlog,baseline \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```

   **Plan:**
   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags irf,backlog,plan \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```
6. Write `backlog.md` with ticket summary

## Ticket Templates

**Seed**
```markdown
## Task
<Single-sentence description>

## Context
<2-3 sentences from seed>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

## Constraints
<Relevant constraints>

## References
- Seed: <topic-id>
```

**Baseline**
```markdown
## Task
<Single-sentence description>

## Context
<2-3 sentences from baseline/risk/test inventory>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

## Constraints
<Relevant constraints>

## References
- Baseline: <topic-id>
- Source: risk-map.md|test-inventory.md|dependency-map.md
```

**Plan**
```markdown
## Task
<Single-sentence description>

## Context
<2-3 sentences from plan summary/requirements>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

## Constraints
<Relevant constraints>

## References
- Plan: <topic-id>
```

## Output

- Tickets created in `tk` (with external-ref linking to source)
- `backlog.md` written to topic directory

## Next Steps

Start implementation:
```
/irf <ticket-id>
```
