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

**Purpose**: Create a single plan document from a project/feature/refactor request, with optional session awareness.

**Input**: Request description (from user)

**Steps**:

1. **Check for active planning session**:
   - Load `{knowledgeDir}/.active-planning.json` if it exists
   - If `state` is `"active"`, capture `session_id`, `root_seed`, and `spikes` array
   - If no active session, proceed with normal flow (no session linking)

2. **Create topic ID**:
   - If input already starts with `plan-`, use it as topic-id
   - Otherwise slugify request (lowercase, spaces → dashes, max 40 chars)
   - Prefix with `plan-`
   - Example: "Refactor auth flow" → `plan-refactor-auth-flow`

3. **Create directory**:

   ```bash
   mkdir -p "{knowledgeDir}/topics/{topic-id}"
   ```

4. **Write `plan.md`** (single source of truth):

   ```markdown
   ---
   id: { topic-id }
   status: draft
   last_updated: YYYY-MM-DD
   ---

   # Plan: <title>

   ## Summary

   <1–2 paragraphs>

   ## Inputs / Related Topics

   <!-- Include this section if created during an active planning session -->
   - Root Seed: [{root_seed}](topics/{root_seed}/seed.md)
   - Session: {session_id}
   - Related Spikes:
     - [{spike-id}](topics/{spike-id}/spike.md)
     - ... (list all spikes from session)

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

   **Note on "Inputs / Related Topics" section**:
   - Only include if an active session was detected in step 1
   - List the root seed with a relative link
   - List all spikes from the session's `spikes[]` array with relative links
   - If no spikes exist yet, show "- (none yet)" or omit the spikes list

5. **Update index.json**:
   ```json
   {
     "id": "{topic-id}",
     "title": "{plan title}",
     "keywords": ["keyword1"],
     "overview": "topics/{topic-id}/plan.md",
     "sources": "topics/{topic-id}/plan.md"
   }
   ```

6. **Update active session (if applicable)**:
   - If an active session was detected in step 1:
     - Set `plan` field in `.active-planning.json` to the new `{topic-id}` (overwrites any prior plan)
     - Update `updated` timestamp in session file
     - Emit notice: `[tf] Auto-attached plan to session: {session_id} (root: {root_seed})`

7. **Cross-link with root seed (if applicable)**:
   - If an active session was detected:
     - **Root seed `sources.md`**: Add or append to "Session Links" section:
       ```markdown
       ## Session Links

       - Plan: [{topic-id}](topics/{topic-id}/plan.md)
       ```
       (dedup: skip if link already exists)
     - **Plan `sources.md`**: Add link back to root seed:
       ```markdown
       ## Parent Session

       - Root Seed: [{root_seed}](topics/{root_seed}/seed.md)
       - Session: {session_id}
       ```
       (dedup: skip if already present)

**Output**:
- `plan.md` stored in topic directory, status = `draft`
- Session updated with `plan: {topic-id}` (if active session exists)
- Cross-links in `sources.md` files (if active session exists)

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

**Purpose**: Capture a greenfield idea into structured artifacts and optionally activate a planning session.

**Input**: Idea description (from user), optional flags

**Flags**:
- `--no-session` - Create seed without activating a planning session (legacy behavior)
- `--active` - Print current active session and exit
- `--sessions [seed-id]` - List archived sessions, optionally filtered by seed
- `--resume <id>` - Resume an archived session by seed-id or session-id

**Steps**:

1. **Parse flags** from input:
   - Check for `--active`, `--sessions`, `--resume`, `--no-session`
   - Handle query flags first (return early for `--active`, `--sessions`, `--resume`)

2. **Handle `--active` query**:
   - Load `.active-planning.json` from knowledge directory
   - If exists: print session details (session_id, root_seed, state, spike_count, has_plan)
   - If not exists: print "No active planning session"
   - Return (no seed created)

3. **Handle `--sessions [seed-id]` query**:
   - List files in `sessions/` directory
   - Filter by seed_id if provided
   - Sort by created timestamp (newest first)
   - Print table: Session ID | Root Seed | State | Created
   - Return (no seed created)

4. **Handle `--resume <id>` query**:
   - If id contains `@`: treat as session_id, load directly
   - Else: treat as seed_id, find latest session for that seed
   - Archive any currently active session
   - Activate the resumed session (write to `.active-planning.json`)
   - Print: "Resumed session: {session_id}"
   - Return (no new seed created)

5. **Create topic ID** (for new seed):
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `seed-`
   - Example: "Build a CLI" → `seed-build-a-cli`

6. **Create directory**:

   ```bash
   mkdir -p "{knowledgeDir}/topics/{topic-id}"
   ```

7. **Write artifacts**:

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

8. **Update index.json**:
   ```json
   {
     "id": "{topic-id}",
     "title": "{idea title}",
     "keywords": ["keyword1"],
     "overview": "topics/{topic-id}/overview.md",
     "sources": "topics/{topic-id}/sources.md"
   }
   ```

9. **Activate planning session** (unless `--no-session`):

   **Check for existing active session**:
   - Load `.active-planning.json`
   - If exists: archive it to `sessions/{session_id}.json`

   **Create and activate new session**:
   - Generate session_id: `{topic-id}@{YYYY-MM-DDTHH-MM-SSZ}` (hyphens in timestamp for filename safety)
   - Create session JSON:
     ```json
     {
       "schema_version": 1,
       "session_id": "{session-id}",
       "state": "active",
       "root_seed": "{topic-id}",
       "spikes": [],
       "plan": null,
       "backlog": null,
       "created": "ISO-8601-timestamp",
       "updated": "ISO-8601-timestamp",
       "completed_at": null
     }
     ```
   - Atomic write to `.active-planning.json` (temp file + rename)

   **Emit notice**:
   ```
   [tf] Activated planning session: {session_id} (root: {topic-id})
   ```

   If a session was archived:
   ```
   [tf] Archived previous session: {previous_session_id}
   [tf] Activated planning session: {new_session_id} (root: {topic-id})
   ```

**Output**: 
- Topic directory with seed artifacts
- `.active-planning.json` (unless `--no-session`)
- Archived session in `sessions/` (if switching from previous active session)

**Session Store API** (for implementation):
```python
from tf_cli.session_store import (
    load_active_session,
    archive_and_create_session,
    list_archived_sessions,
    find_latest_session_for_seed,
    resume_session,
    get_active_session_info
)
```

---

### Procedure: Backlog Generation (Seed, Baseline, or Plan)

**Purpose**: Create small, actionable tickets from a seed (greenfield), baseline (brownfield), or plan.

**Input**: Seed, baseline, or plan topic-id or path

**Flags**:
- `--no-deps` - Skip automatic dependency inference (default: dependencies are inferred)

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
   - Note: Use `--no-deps` flag to skip automatic dependency inference (see step 9)

3. **Load existing tickets to avoid duplicates**:
   - Read `backlog.md` if it exists (capture existing IDs + titles)
   - Read `existing-tickets.md` if present (from `/tf-baseline`)
   - Run `tk list --help` (or `tk help`) to discover listing/search options
   - If `tk` supports listing/search, pull open tickets with tags like `tf`, `baseline`, or `backlog`
   - Build a de-dupe set by normalized title + ID

4. **Seed mode**:
   - Read `seed.md` (required)
   - Read `mvp-scope.md`, `success-metrics.md`, `constraints.md` (if exist)
   - Derive small tickets from the seed (as many as needed to cover the scope—could be 1 for a small change, or many for a large feature)

5. **Baseline mode**:
   - Read `baseline.md` (required)
   - Read `risk-map.md`, `test-inventory.md`, `dependency-map.md`, `overview.md` (if exist)
   - Derive small tickets from risks, test gaps, dependency issues, and architectural hotspots (number varies based on scope—could be 1 quick fix or more for extensive refactor)
   - Split large refactors into 1-2 hour chunks

6. **Plan mode**:
   - Read `plan.md` (required)
   - Extract Summary, Requirements, Constraints, Acceptance Criteria, and Work Plan items
   - Derive small tickets from Work Plan entries (create as many as needed—could be 1 for a simple change, or split large phases into multiple 1-2 hour chunks)
   - Split large phases into 1-2 hour chunks

7. **Create tickets** (1-2 hours each, 30 lines max):
   - **PREFERRED**: Use `tf_cli.ticket_factory` module (see "Ticket Creation with ticket_factory Module" in Common Tool Usage) instead of writing inline scripts
   - If using the module:
     ```python
     from tf_cli.ticket_factory import TicketDef, create_tickets, score_tickets
     tickets = [TicketDef(title="...", description="..."), ...]
     scored = score_tickets(tickets)
     created = create_tickets(scored, topic_id=TOPIC_ID, mode="seed")
     ```
   - If writing inline script, follow these steps:
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
   - **If using ticket_factory**: Already handled by `create_tickets()` function
   - If using inline script:

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
   - **If using ticket_factory**: Already handled by `apply_dependencies(created, mode='chain' or mode='phases')`
   - If using inline script, follow these steps:

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
   - **Out-of-order creation**: The chain is based on creation sequence, not ticket IDs. If ticket 5 is created before ticket 3, ticket 5 will have no dependency (first created) and ticket 3 will depend on ticket 5 (if created second). To correct this, manually adjust with `tk dep <ticket-3> <ticket-5>` and `tk dep <ticket-5> --remove`.
   - **Hint-based override**: If seed content suggests a different order, adjust the chain:
     - Look for keywords in titles/descriptions: "setup", "configure", "define", "design", "implement", "test"
     - "Setup"/"Configure" → comes first
     - "Define"/"Design" → comes before "Implement"
     - "Implement" → comes before "Test"
   - Conservative: prefer the default chain over uncertain deps; skip if ambiguous

   **Baseline mode:**
   - Skip dependencies unless explicitly stated in source docs
   - Apply with `tk dep <id> <dep-id>` (one command per dependency)

10. **Suggest component tags** (unless `--no-component-tags` flag provided):
    - **If using ticket_factory**: Already handled by `create_tickets(..., component_tags=True)`
    - If using inline script:
    - Analyze each ticket's title and description for component indicators
    - Suggest `component:*` tags (e.g., `component:ui`, `component:api`, `component:db`)
    - Apply tags to ticket frontmatter during creation
    - Purpose: Enable safe parallel scheduling in Ralph
    - If skipped, users can run `/tf-tags-suggest --apply` later to add component tags

11. **Link related tickets** (unless `--no-links` flag provided):
    - **If using ticket_factory**: Already handled by `apply_links(created)`
    - If using inline script:

    Link tickets that are tightly related for discoverability/grouping. Links are symmetric and advisory (not blocking like dependencies).

    **Linking criteria** (conservative - prefer under-linking):
    - **Same component + adjacent**: Tickets with identical component tags created consecutively
    - **Title similarity**: Tickets sharing significant words (e.g., "component classifier" and "component tags" share "component")
    - **Max 2-3 links per ticket** to avoid noise

    **Apply links**:
    ```bash
    tk link <id1> <id2>
    ```
    Links are symmetric, so `tk link A B` links both directions.

    **Record links**: Track which tickets are linked for the backlog.md table.

12. **Write backlog.md**:
    - **If using ticket_factory**: Already handled by `write_backlog_md(created, topic_id=TOPIC_ID)`
    - If using inline script, write the markdown table directly:

```markdown
# Backlog: {topic-id}

| ID   | Title   | Est. Hours | Depends On | Components | Links |
| ---- | ------- | ---------- | ---------- | ---------- | ----- |
| {id} | {title} | 1-2        | {deps}     | {tags}     | {links} |
```

Where:
- `{deps}`: Comma-separated dependency IDs, or `-` if none
- `{tags}`: Comma-separated component tags (e.g., `component:ui, component:api`), or `-` if none (populated unless `--no-component-tags` used)
- `{links}`: Comma-separated linked ticket IDs (symmetric relationships for discoverability), or `-` if none

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

**Purpose**: Research a topic and store findings, optionally auto-attaching to an active planning session.

**Input**: Topic to research, optional `--parallel` flag

**Steps**:

1. **Create topic ID**:
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `spike-`

2. **Check for active planning session**:
   - Load `{knowledgeDir}/.active-planning.json` if it exists
   - If `state` is `"active"`, capture `session_id` and `root_seed`
   - If no active session, proceed with normal flow (no session linking)

3. **Check MCP tools**:
   - context7 (documentation)
   - exa (web search)
   - grep_app (code search)
   - zai-web-search (alternative search)

4. **Research**:

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

5. **Write artifacts**:

   **overview.md**: Summary + keywords
   **sources.md**: All URLs and tools used
   **spike.md**: Full analysis with findings, options, recommendation

6. **Update active session (if applicable)**:
   - If an active session was detected in step 2:
     - Append `topic-id` to `spikes[]` array in `.active-planning.json` (dedup: skip if already present)
     - Update `updated` timestamp in session file
     - Emit notice: `[tf] Auto-attached spike to session: {session_id}`

7. **Cross-link with root seed (if applicable)**:
   - If an active session was detected:
     - **Root seed `sources.md`**: Add or append to "Session Links" section:
       ```markdown
       ## Session Links

       - Spike: [{topic-id}](topics/{topic-id}/spike.md)
       ```
       (dedup: skip if link already exists)
     - **Spike `sources.md`**: Add link back to root seed:
       ```markdown
       ## Parent Session

       - Root Seed: [{root_seed}](topics/{root_seed}/seed.md)
       - Session: {session_id}
       ```
       (dedup: skip if already present)

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

### Ticket Creation with ticket_factory Module

**Instead of writing inline Python scripts for ticket creation, use the `tf_cli.ticket_factory` module.** This module provides reusable functions for scoring, creating, and managing tickets during backlog generation.

**Usage Pattern:**

```python
from __future__ import annotations

from tf_cli.ticket_factory import (
    TicketDef,
    create_tickets,
    write_backlog_md,
    score_tickets,
    apply_dependencies,
    apply_links,
    print_created_summary,
)

# Define tickets
tickets = [
    TicketDef(
        title='Define Ralph logging spec',
        description=md([
            '## Task',
            'Define what Ralph should log...',
            '',
            '## Acceptance Criteria',
            '- [ ] Log format is defined',
            '- [ ] Redaction rules defined',
        ]),
    ),
    TicketDef(
        title='Implement Ralph logger helper',
        description=md([
            '## Task',
            'Implement logging helper with level filtering...',
            '',
            '## Acceptance Criteria',
            '- [ ] Helper supports levels (info/warn/error/debug)',
            '- [ ] Output goes to stderr',
        ]),
    ),
]

# Score tickets (higher score = higher priority)
scored = score_tickets(tickets)

# Create tickets
TOPIC_ID = 'seed-add-more-logging'
created = create_tickets(
    scored,
    topic_id=TOPIC_ID,
    mode='seed',
    component_tags=True,  # Auto-assign component:cli, etc.
    existing_titles=existing_titles_set,  # For de-duplication
    priority=2,
)

# Apply dependencies (chain mode by default)
created = apply_dependencies(created, mode='chain')

# Apply links between related tickets
created = apply_links(created)

# Write backlog.md
write_backlog_md(created, topic_id=TOPIC_ID)

# Print summary
print_created_summary(created)
```

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `TicketDef(title, description, optional_tags)` | Define a ticket to create |
| `score_tickets(tickets, weights)` | Score tickets by keyword (setup→10, implement→3, test→1) |
| `create_tickets(scored_tickets, topic_id, mode, ...)` | Create tickets via `tk create` with auto-component-tags |
| `apply_dependencies(tickets, mode)` | Apply `tk dep` for ticket dependencies |
| `apply_links(tickets)` | Link related tickets via `tk link` |
| `write_backlog_md(tickets, topic_id)` | Write `backlog.md` file |
| `print_created_summary(tickets)` | Print creation summary to stdout |

**Benefits:**

- **No inline scripts**: Import and call functions instead of writing bash/inline Python
- **Consistent scoring**: Uses the same keyword weights across all backlogs
- **Auto component tags**: Integrates with `component_classifier` automatically
- **De-duplication**: Built-in duplicate detection by normalized title
- **Testable**: Functions can be unit tested independently
- **Reduced prompt size**: No need to repeat the scoring/creation logic in prompts

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
