---
description: Create tickets from seed, baseline, or plan artifacts [tf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: tf-planning
---

# /tf-backlog

Generate small, actionable implementation tickets from seed (greenfield), baseline (brownfield), or plan artifacts.

## Usage

```
/tf-backlog <seed-baseline-or-plan-path-or-topic-id> [--no-deps]
```

## Arguments

- `$1` - Path to seed/baseline/plan directory or topic ID (`seed-*`, `baseline-*`, or `plan-*`)
- If omitted: auto-locates if exactly one seed, baseline, or plan exists

## Options

- `--no-deps` - Skip automatic dependency inference for seed/baseline backlogs

## Examples

```
/tf-backlog seed-build-a-cli
/tf-backlog baseline-myapp
/tf-backlog plan-auth-rewrite
/tf-backlog .tf/knowledge/topics/baseline-myapp/
```

## Execution

Follow the **TF Planning Skill** "Backlog Generation (Seed, Baseline, or Plan)" procedure:

1. Locate topic directory
2. Detect mode (seed vs baseline vs plan)
3. Read relevant artifacts and plan status (warn if plan not approved)
4. Load existing tickets to avoid duplicates:
   - Read `backlog.md` if it exists
   - Read `existing-tickets.md` if present (from `/tf-baseline`)
   - Run `tk list --help` (or `tk help`) to discover listing/search options
   - If `tk` supports listing/search, pull open tickets with tags like `tf`, `baseline`, or `backlog`
5. Create 5-15 small tickets (1-2 hours each, 30 lines max), skipping duplicates (record skipped items in backlog.md)
6. Create via `tk create`:

   **Seed:**

   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags tf,backlog \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```

   **Baseline:**

   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags tf,backlog,baseline \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```

   **Plan:**

   ```bash
   tk create "<title>" \
     --description "<description>" \
     --tags tf,backlog,plan \
     --type task \
     --priority 2 \
     --external-ref "{topic-id}"
   ```

7. Infer dependencies:

   **Plan mode:**
   - Use Work Plan phases or ordered steps to determine sequencing
   - For phase-based plans: each ticket in phase N depends on all tickets in phase N-1
   - For ordered lists without phases: chain each ticket to the previous one
   - Apply with `tk dep <id> <dep-id>`

   **Seed mode (if `--no-deps` NOT provided):**
   - **Default chain**: Create a simple linear dependency chain in ticket creation order
   - Each ticket N depends on ticket N-1 (the previous one created)
   - Apply with `tk dep <id> <dep-id>`
   - **Hint-based override**: If seed content suggests a different order (e.g., keywords like "define", "implement", "test", "setup", "configure"), adjust the chain to match the logical sequence:
     - "Setup" or "Configure" tasks come first
     - "Define" or "Design" tasks come before "Implement"
     - "Implement" tasks come before "Test"
   - Conservative: prefer the default chain over uncertain deps; skip deps if the order is ambiguous

   **Baseline mode:**
   - Skip dependencies unless explicitly stated in source docs
   - Apply with `tk dep <id> <dep-id>`

8. Write `backlog.md` with ticket summary (include dependencies)

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
- Dependencies applied via `tk dep` when inferred
- `backlog.md` written to topic directory

## Next Steps

Start implementation:

```
/tf <ticket-id>
```
