---
name: tf-planning
description: Research and planning activities for IRF workflow. Use for capturing ideas, creating tickets, research spikes, and bridging from external specs. Includes seed capture, backlog generation, baseline analysis, and OpenSpec integration.
---

# TF Planning Skill

Expertise for upstream planning activities - everything that happens BEFORE implementation.

## When to Use This Skill

- Capturing a new feature idea
- Researching a technical topic
- Creating and validating implementation plans
- Creating implementation tickets from seeds/specs
- Analyzing an existing codebase (baseline)
- Creating follow-up tickets from reviews

## Key Principle: Small, Self-Contained Tickets

All ticket creation in this skill follows these rules:

- **30 lines or less** in description
- **1-2 hours** estimated work
- **Self-contained** - includes all needed context
- **Single responsibility** - one feature per ticket

## Configuration

Read workflow config (project):

- `.tf/config/settings.json`

Extract `workflow.knowledgeDir` (default: `.tf/knowledge`).

## Execution Procedures

### Procedure: Plan Interview (Planner)

**Purpose**: Create a single plan document from a project/feature/refactor request.

**Input**: Request description (from user)

**Steps**:

1. **Create topic ID**:
   - If input already starts with `plan-`, use it as topic-id
   - Otherwise slugify request (lowercase, spaces → dashes, max 40 chars)
   - Prefix with `plan-`
   - Example: "Refactor auth flow" → `plan-refactor-auth-flow`

2. **Create directory**:

   ```bash
   mkdir -p "{knowledgeDir}/topics/{topic-id}"
   ```

3. **Write `plan.md`** (single source of truth):

   ```markdown
   ---
   id: { topic-id }
   status: draft
   last_updated: YYYY-MM-DD
   ---

   # Plan: <title>

   ## Summary

   <1–2 paragraphs>

   ## Requirements

   - ...

   ## Constraints

   - ...

   ## Assumptions

   - ...

   ## Risks & Gaps

   - ...

   ## Work Plan (phases / tickets)

   1. ...

   ## Acceptance Criteria

   - [ ] ...

   ## Open Questions

   - ...

   ---

   ## Consultant Notes (Metis)

   - YYYY-MM-DD: <gap detection / ambiguity flags>

   ## Reviewer Notes (Momus)

   - YYYY-MM-DD: PASS|FAIL
     - Blockers:
       - ...
     - Required changes:
       - ...
   ```

4. **Update index.json**:
   ```json
   {
     "id": "{topic-id}",
     "title": "{plan title}",
     "keywords": ["keyword1"],
     "overview": "topics/{topic-id}/plan.md",
     "sources": "topics/{topic-id}/plan.md"
   }
   ```

**Output**: `plan.md` stored in topic directory, status = `draft`

---

### Procedure: Plan Consultant (Gap Detection)

**Purpose**: Identify missing requirements, ambiguities, risks, or over-engineering.

**Input**: Plan topic-id or path

**Steps**:

1. **Locate plan directory**:
   - If path provided: use directly
   - If topic-id: `{knowledgeDir}/topics/{topic-id}/`
   - If no input: auto-locate if exactly one `plan-*` exists; otherwise ask

2. **Read `plan.md`**.

3. **Update the plan directly**:
   - Add missing requirements, constraints, risks, or acceptance criteria
   - Clarify ambiguous items
   - Keep structure intact

4. **Append Consultant Notes** with findings and changes.

5. **Update frontmatter**: set `status: consulted`, update `last_updated`.

**Output**: Updated `plan.md`

---

### Procedure: Plan Revision

**Purpose**: Apply consultant/reviewer feedback to the plan.

**Input**: Plan topic-id or path

**Steps**:

1. Locate plan directory (same as consultant)
2. Read `plan.md` plus Consultant/Reviewer notes
3. Update plan sections to resolve gaps and blockers
4. Append a revision note under Consultant Notes or Reviewer Notes (as appropriate)
5. Update frontmatter: set `status: revised`, update `last_updated`

**Output**: Updated `plan.md` ready for re-review

---

### Procedure: Plan Review (High-Accuracy)

**Purpose**: Validate the plan with high-precision checks.

**Input**: Plan topic-id or path (supports `--high-accuracy` flag from prompt)

**Steps**:

1. Locate plan directory (same as consultant)
2. Read `plan.md`
3. Validate:
   - Requirements completeness
   - Clear scope boundaries
   - Constraints covered
   - Risks identified with mitigations
   - Work plan sequenced and feasible
   - Acceptance criteria testable
   - Open questions minimized
4. Update plan sections if needed for clarity/precision
5. Append **Reviewer Notes** with PASS/FAIL and blockers
6. Update frontmatter:
   - `status: approved` if PASS
   - `status: blocked` if FAIL
   - Update `last_updated`

**Output**: Updated `plan.md` with approval status

---

### Procedure: Seed Capture

**Purpose**: Capture a greenfield idea into structured artifacts.

**Input**: Idea description (from user)

**Steps**:

1. **Create topic ID**:
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `seed-`
   - Example: "Build a CLI" → `seed-build-a-cli`

2. **Create directory**:

   ```bash
   mkdir -p "{knowledgeDir}/topics/{topic-id}"
   ```

3. **Write artifacts**:

   **overview.md**:

   ```markdown
   # {topic-id}

   Brief 2-3 sentence summary.

   ## Keywords

   - keyword1
   - keyword2
   ```

   **seed.md**:

   ```markdown
   # Seed: {idea}

   ## Vision

   What problem does this solve?

   ## Core Concept

   High-level solution description

   ## Key Features

   1. Feature one
   2. Feature two

   ## Open Questions

   - Question 1?
   ```

   **success-metrics.md**, **assumptions.md**, **constraints.md**, **mvp-scope.md**, **sources.md**

4. **Update index.json**:
   ```json
   {
     "id": "{topic-id}",
     "title": "{idea title}",
     "keywords": ["keyword1"],
     "overview": "topics/{topic-id}/overview.md",
     "sources": "topics/{topic-id}/sources.md"
   }
   ```

**Output**: Topic directory with seed artifacts

---

### Procedure: Backlog Generation (Seed, Baseline, or Plan)

**Purpose**: Create small, actionable tickets from a seed (greenfield), baseline (brownfield), or plan.

**Input**: Seed, baseline, or plan topic-id or path

**Steps**:

1. **Locate topic directory**:
   - If path provided: use directly
   - If topic-id: `{knowledgeDir}/topics/{topic-id}/`
   - If no input: auto-locate if exactly one seed, baseline, or plan exists; otherwise ask for a topic

2. **Detect mode**:
   - If `plan.md` exists or topic-id starts with `plan-` → **plan mode**
   - If `baseline.md` exists or topic-id starts with `baseline-` → **baseline mode**
   - If `seed.md` exists or topic-id starts with `seed-` → **seed mode**
   - If both/neither, ask user to clarify
   - If plan mode: read frontmatter `status`; if not `approved`, **warn** but continue

3. **Load existing tickets to avoid duplicates**:
   - Read `backlog.md` if it exists (capture existing IDs + titles)
   - Read `existing-tickets.md` if present (from `/tf-baseline`)
   - Run `tk list --help` (or `tk help`) to discover listing/search options
   - If `tk` supports listing/search, pull open tickets with tags like `tf`, `baseline`, or `backlog`
   - Build a de-dupe set by normalized title + ID

4. **Seed mode**:
   - Read `seed.md` (required)
   - Read `mvp-scope.md`, `success-metrics.md`, `constraints.md` (if exist)
   - Derive 5-15 small tickets from the seed

5. **Baseline mode**:
   - Read `baseline.md` (required)
   - Read `risk-map.md`, `test-inventory.md`, `dependency-map.md`, `overview.md` (if exist)
   - Derive 5-15 small tickets from risks, test gaps, dependency issues, and architectural hotspots
   - Split large refactors into 1-2 hour chunks

6. **Plan mode**:
   - Read `plan.md` (required)
   - Extract Summary, Requirements, Constraints, Acceptance Criteria, and Work Plan items
   - Derive 5-15 small tickets from Work Plan entries
   - Split large phases into 1-2 hour chunks

7. **Create tickets** (1-2 hours each, 30 lines max):
   - Skip any ticket whose normalized title matches an existing ticket from backlog/existing list
   - If a ticket overlaps an existing one, note it in backlog.md as skipped (do not create)

   **Seed ticket template:**

   ```markdown
   ## Task

   <Single-sentence description>

   ## Context

   <2-3 sentences summarizing relevant context>

   ## Acceptance Criteria

   - [ ] <criterion 1>
   - [ ] <criterion 2>
   - [ ] <criterion 3>

   ## Constraints

   - <relevant constraint>

   ## References

   - Seed: <topic-id>
   ```

   **Baseline ticket template:**

   ```markdown
   ## Task

   <Single-sentence description>

   ## Context

   <2-3 sentences summarizing relevant context>

   ## Acceptance Criteria

   - [ ] <criterion 1>
   - [ ] <criterion 2>
   - [ ] <criterion 3>

   ## Constraints

   - <relevant constraint>

   ## References

   - Baseline: <topic-id>
   - Source: risk-map.md|test-inventory.md|dependency-map.md
   ```

   **Plan ticket template:**

   ```markdown
   ## Task

   <Single-sentence description>

   ## Context

   <2-3 sentences from the plan summary/requirements>

   ## Acceptance Criteria

   - [ ] <criterion 1>
   - [ ] <criterion 2>
   - [ ] <criterion 3>

   ## Constraints

   - <relevant constraint>

   ## References

   - Plan: <topic-id>
   ```

8. **Create via `tk`**:

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

9. **Infer dependencies**:

   **Plan mode:**
   - Track created ticket IDs with their phase/order
   - Use Work Plan phases/headings to group tickets into phases
   - For phase-based plans: each ticket in phase N depends on **all** tickets in phase N-1
   - For ordered lists without phases: chain each ticket to the previous one
   - Apply with `tk dep <id> <dep-id>` (one command per dependency)

   **Seed mode (unless `--no-deps` flag provided):**
   - **Default chain**: Create a simple linear dependency chain in ticket creation order
   - Each ticket N depends on ticket N-1 (the previous ticket created)
   - Apply with `tk dep <id> <dep-id>` (one command per dependency)
   - **Hint-based override**: If seed content suggests a different order, adjust the chain:
     - Look for keywords in titles/descriptions: "setup", "configure", "define", "design", "implement", "test"
     - "Setup"/"Configure" → comes first
     - "Define"/"Design" → comes before "Implement"
     - "Implement" → comes before "Test"
   - Conservative: prefer the default chain over uncertain deps; skip if ambiguous

   **Baseline mode:**
   - Skip dependencies unless explicitly stated in source docs
   - Apply with `tk dep <id> <dep-id>` (one command per dependency)

10. **Write backlog.md**:

```markdown
# Backlog: {topic-id}

| ID   | Title   | Est. Hours | Depends On       |
| ---- | ------- | ---------- | ---------------- |
| {id} | {title} | 1-2        | {dep-ids-or-"-"} |
```

---

### Procedure: Backlog Listing

**Purpose**: Show backlog status and corresponding tickets for seed/baseline/plan topics.

**Input**: Optional topic-id or path

**Steps**:

1. **Resolve knowledgeDir** from config (default: `.tf/knowledge`).

2. **If input provided**:
   - If path provided: use directly
   - If topic-id: `{knowledgeDir}/topics/{topic-id}/`
   - If not found: list available `seed-*`, `baseline-*`, and `plan-*` topics, ask user to choose, then stop

3. **If no input**:
   - Scan `{knowledgeDir}/topics/` for `seed-*`, `baseline-*`, and `plan-*`
   - For each topic, check for `backlog.md`

4. **If `backlog.md` exists**:
   - Read and parse the backlog table
   - Extract ticket IDs and titles
   - Count tickets and show a summary

5. **If `backlog.md` missing**:
   - Mark as **unticketed**
   - Suggest running `/tf-backlog <topic>`

6. **Output format**:
   - If a single topic is requested: print full backlog table + summary
   - If multiple topics: print summary table:
     ```markdown
     | Topic             | Type     | Backlog | Tickets                  |
     | ----------------- | -------- | ------- | ------------------------ |
     | seed-foo          | seed     | yes     | 8 (TKT-1, TKT-2, TKT-3…) |
     | plan-auth-rewrite | plan     | yes     | 5 (TKT-4, TKT-5…)        |
     | baseline-bar      | baseline | no      | 0                        |
     ```

---

### Procedure: Research Spike

**Purpose**: Research a topic and store findings.

**Input**: Topic to research, optional `--parallel` flag

**Steps**:

1. **Create topic ID**:
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `spike-`

2. **Check MCP tools**:
   - context7 (documentation)
   - exa (web search)
   - grep_app (code search)
   - zai-web-search (alternative search)

3. **Research**:

   **Sequential mode** (default):
   - Query each available tool one by one
   - Synthesize in main agent

   **Parallel mode** (`--parallel` flag):

   ```json
   {
     "tasks": [
       { "agent": "researcher-fetch", "task": "Docs: {topic}" },
       { "agent": "researcher-fetch", "task": "Web: {topic}" },
       { "agent": "researcher-fetch", "task": "Code: {topic}" }
     ]
   }
   ```

4. **Write artifacts**:

   **overview.md**: Summary + keywords
   **sources.md**: All URLs and tools used
   **spike.md**: Full analysis with findings, options, recommendation

---

### Procedure: Baseline Capture

**Purpose**: Document status-quo of existing project.

**Input**: Optional focus area

**Steps**:

1. **Determine topic ID**:

   ```bash
   repo_name=$(basename $(pwd))
   topic_id="baseline-${repo_name}"
   ```

2. **Scan project**:
   - Read: README.md, package.json, etc.
   - Find entry points: `find . -name "main.*" -o -name "app.*"`
   - Find tests: `find . -type d -name "test*"`

3. **Capture existing tickets (if `tk` available)**:
   - Run `tk list --help` to discover supported filters
   - Prefer listing open tickets with tags like `tf`, `baseline`, or `backlog` (if supported)
   - If listing is unavailable, capture `tk ready` output
   - Write `existing-tickets.md` with a table: ID | Title | Status | Tags | Notes

4. **Write artifacts**:
   - **overview.md**: Summary
   - **baseline.md**: Architecture, components, entry points
   - **risk-map.md**: Technical, dependency, knowledge risks
   - **test-inventory.md**: Test directories, commands, coverage gaps
   - **dependency-map.md**: Runtime/dev dependencies, external services
   - **existing-tickets.md**: Current tickets (from `tk`)
   - **sources.md**: Files scanned

---

### Procedure: Follow-up Creation

**Purpose**: Create tickets from review Warnings/Suggestions.

**Input**: Path to review.md or ticket ID

**Steps**:

1. **Resolve review path**:
   - If path: use directly
   - If ticket ID: prefer `{knowledgeDir}/tickets/{ticket-id}/review.md` when it exists; otherwise search `/tmp/pi-chain-runs`
   - If empty: use `./review.md` if exists (or the current ticket artifact directory)

2. **Parse review**:
   - Extract Warnings section
   - Extract Suggestions section

3. **Create ticket per item**:

   ```bash
   tk create "<title>" \
     --description "## Origin\nFrom review of: {ticket}\nFile: {file}\nLine: {line}\n\n## Issue\n{description}" \
      --tags tf,followup \
     --priority 3
   ```

4. **Write followups.md** documenting created tickets (prefer the same directory as the review file or the ticket artifact directory)

---

### Procedure: OpenSpec Backlog

**Purpose**: Convert an OpenSpec change into TF backlog tickets and infer dependencies.

**Input**: Change ID or path

**Steps**:

1. **Locate change**:
   - Look for `openspec/changes/{id}/`
   - Fallback: `changes/{id}/`

2. **Read artifacts**:
   - `tasks.md` (required)
   - `proposal.md`, `design.md` (for context extraction)

3. **Parse tasks**:
   - For each task in tasks.md
   - Extract relevant sections from proposal/design
   - Split large tasks into 1-2 hour chunks

4. **Create tickets** with template:

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

5. **Create via `tk`**:

   ```bash
   tk create "<title>" \
     --description "<description>" \
      --tags tf,openspec \
     --type task \
     --priority 2 \
     --external-ref "openspec-{change_id}"
   ```

6. **Infer dependencies from tasks.md**:
   - Track created ticket IDs in task order
   - If tasks are in a numbered/ordered list: chain each ticket to the previous one
   - If tasks are grouped by headings: treat each heading as a phase; tasks in phase N depend on all tasks in phase N-1
   - If tasks explicitly note dependencies (e.g., "Depends on:"): honor those first
   - Apply with `tk dep <id> <dep-id>`

7. **Write backlog.md** in change directory (include dependencies)

---

## Common Tool Usage

### Model Switching

All procedures use model-switch pattern with meta-model resolution:

1. Look up `prompts.{command}` in config → get meta-model key (e.g., "planning")
2. Look up `metaModels.{key}.model` → get actual model ID
3. ```
   switch_model action="switch" search="{metaModels.planning.model}"
   ```

For example, for `/tf-plan`:

- `prompts.tf-plan` → "planning"
- `metaModels.planning.model` → "openai-codex/gpt-5.1-codex-mini"

### Ticket Creation Pattern

```bash
tk create "<title>" \
  --description "<markdown description>" \
   --tags tf,<tag> \
  --type task \
  --priority <1-5> \
  --external-ref "<source-id>"   # e.g., plan-foo, seed-bar, openspec-baz
```

### Knowledge Base Structure

```
.tf/knowledge/
├── index.json              # Registry of all topics
├── tickets/
│   └── {ticket-id}/
│       ├── research.md     # Per-ticket research
│       ├── implementation.md
│       ├── review.md
│       ├── fixes.md
│       ├── followups.md
│       ├── close-summary.md
│       ├── chain-summary.md
│       ├── files_changed.txt
│       └── ticket_id.txt
└── topics/
    └── {topic-id}/
        ├── plan.md
        ├── overview.md
        ├── seed.md|spike.md|baseline.md
        ├── sources.md
        └── backlog.md
```

## Error Handling

- **Seed not found**: List available seeds and ask user
- **Plan not found**: List available plans and ask user
- **No warnings/suggestions**: Write "No follow-ups needed" and exit
- **OpenSpec not found**: Ask for explicit path
- **tk create fails**: Log error, continue with remaining tickets

## Output Summary

| Procedure        | Primary Output           | Secondary Output                    |
| ---------------- | ------------------------ | ----------------------------------- |
| Plan Interview   | `plan.md`                | index.json updated                  |
| Plan Consultant  | `plan.md`                | status = consulted                  |
| Plan Revision    | `plan.md`                | status = revised                    |
| Plan Review      | `plan.md`                | status = approved/blocked           |
| Seed Capture     | `topics/{id}/` directory | index.json updated                  |
| Backlog          | `backlog.md`             | Tickets in `tk` (with external-ref) |
| Spike            | `topics/{id}/` directory | index.json updated                  |
| Baseline         | `topics/{id}/` directory | index.json updated                  |
| Follow-ups       | `followups.md`           | Tickets in `tk`                     |
| OpenSpec Backlog | `backlog.md`             | Tickets in `tk` (with external-ref) |
