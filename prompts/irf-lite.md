---
description: Simplified IRF workflow with Ralph-ready re-anchoring, lessons learned, and progress tracking. Fewer subagents, uses model-switch for sequential steps.
---

# Implement → Review → Fix → Close (Lite)

A streamlined workflow that minimizes subagent usage. Uses `pi-model-switch` for sequential steps, keeping subagents **only** for the parallel review step.

**Ralph-Ready**: Automatically loads lessons from `.pi/ralph/AGENTS.md` and tracks progress when Ralph loop is active.

## Invocation

```
/irf-lite <ticket-id> [--auto] [--no-research] [--with-research]
```

Parse `$@` for ticket ID and flags. If no ticket ID provided, ask and stop.

## Prerequisites Check

Before starting, verify:
1. `tk` CLI is available: `which tk`
2. `switch_model` tool is available (from pi-model-switch extension)
3. `subagent` tool is available (from pi-subagents extension)

If any missing, inform the user and stop.

---

## Execution Flow

### Load Config

Read and merge configs (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json`
- `~/.pi/agent/workflows/implement-review-fix-close/config.json`

Extract:
- `models.implementer` (default: "anthropic/claude-sonnet-4")
- `models.reviewer-general`, `models.reviewer-spec-audit`, `models.reviewer-second-opinion`
- `models.review-merge` (default: "zai/glm-4.7")
- `models.fixer` (default: "zai/glm-4.7")
- `workflow.enableResearcher` (default: true)
- `workflow.knowledgeDir` (default: ".pi/knowledge")

---

### Step 0: Re-Anchor Context

Before any work, load all available context to prevent "context rot" and apply lessons from previous work.

**Execute**:

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.pi/ralph/AGENTS.md`
   - If referenced, also read `.pi/ralph/AGENTS.md` for lessons learned

2. **Read Ralph lessons** (if `.pi/ralph/AGENTS.md` exists)
   - This file contains accumulated wisdom from previous ticket implementations
   - Apply any relevant patterns or avoid noted gotchas

3. **Read knowledge base**
   - Check `.pi/knowledge/tickets/{ticket}.md` (ticket-specific research)
   - Read if exists

4. **Get ticket details**
   - Run `tk show {ticket}` to get full ticket description

5. **Parse planning doc references** (from ticket description)
   - Look for "OpenSpec Change: {id}" → note `openspec/changes/{id}/` path
   - Look for "IRF Seed: {topic}" → note `.pi/knowledge/topics/{topic}/` path
   - Look for "Spike: {topic}" → note `.pi/knowledge/topics/{topic}/` path
   - Look for "From Review: {ticket}" → note relationship
   - **Only load these docs if explicitly needed during implementation**
   - Prefer summarized context in ticket over loading full docs

---

### Step 1: Research (Optional, In Main Agent)

**Skip if**: `--no-research` flag OR `workflow.enableResearcher` is false

**Execute**:
1. Check if research already exists from Step 0 (`.pi/knowledge/tickets/{ticket}.md`)
   - If yes and sufficient: use existing, continue to Step 2
   - If no or outdated: proceed with fresh research

2. Fresh research (sequential, no subagents):
   - If MCP tools available (context7, exa, grep_app), use them one by one
   - Synthesize findings
   - Write to `.pi/knowledge/tickets/{ticket}.md`

No model switch needed - use current model.

---

### Step 2: Implement (Main Agent + Model Switch)

**Model switch**:
```
Use switch_model tool with action="switch", search="{models.implementer}"
```

**Execute**:
1. Review all context gathered in Step 0
2. Explore codebase with find/grep to locate relevant files
3. Implement changes following:
   - Project patterns from AGENTS.md
   - Lessons from `.pi/ralph/AGENTS.md` (if available)
   - Ticket acceptance criteria
4. Track changed files (keep list in memory)
5. Run quality checks per config `checkers`:
   - Lint changed files
   - Format changed files  
   - Typecheck project
6. Run relevant tests
7. Write `implementation.md` with:
   - Summary of changes
   - Files changed list
   - Key decisions
   - Test results

**Note on planning docs**: Only read referenced proposal/design docs if:
- Ticket description says "see X for details"
- Implementation requires deeper context than ticket provides
- Stuck on how to interpret a requirement

---

### Step 3: Parallel Reviews (SUBAGENT - Required)

This is the **only step requiring subagents** - true parallelism cannot be achieved otherwise.

**Execute** using the `subagent` tool:

```json
{
  "tasks": [
    {
      "agent": "reviewer-general",
      "task": "{ticket}"
    },
    {
      "agent": "reviewer-spec-audit", 
      "task": "{ticket}"
    },
    {
      "agent": "reviewer-second-opinion",
      "task": "{ticket}"
    }
  ]
}
```

**After completion**: The subagent tool returns paths to the three review outputs. Store these paths for the next step.

---

### Step 4: Merge Reviews (Main Agent + Model Switch)

**Model switch**:
```
Use switch_model tool with action="switch", search="{models.review-merge}"
```

**Execute**:
1. Read all three review files from the paths returned in Step 3
2. Parse each review's Critical/Major/Minor/Warnings/Suggestions sections
3. Deduplicate issues:
   - Match by file path + line number + similar description
   - Keep highest severity when duplicates found
   - Note source reviewer(s) for each issue
4. Write consolidated `review.md`

---

### Step 5: Fix Issues (Main Agent + Model Switch)

**Model switch** (if different from merge model):
```
Use switch_model tool with action="switch", search="{models.fixer}"
```

**Execute**:
1. Read `review.md`, count Critical/Major/Minor issues
2. **If zero Critical/Major/Minor**:
   - Write `fixes.md`: "# Fixes: {ticket}\n\nNo fixes needed. Review contained no Critical/Major/Minor issues."
   - Skip to Step 6

3. **Otherwise**:
   - Fix all Critical issues (required)
   - Fix all Major issues (should do)
   - Fix Minor issues if low effort
   - Do NOT fix Warnings/Suggestions (these become follow-up tickets)
   - Run tests after fixes
   - Write `fixes.md`

---

### Step 6: Close Ticket (Main Agent, Same Model)

No model switch needed - stay on current cheap model.

**Execute**:
1. Read `implementation.md`, `review.md`, `fixes.md`
2. Compose summary note
3. Add note to ticket via `tk add-note`
4. Close ticket via `tk close`
5. Write `close-summary.md`

---

### Step 7: Learn & Track (Ralph Integration)

**This step runs automatically if `.pi/ralph/` directory exists.**

If Ralph loop is active (`.pi/ralph/` exists):

**7a. Update Progress**

Append to `.pi/ralph/progress.md`:
```markdown
- {ticket-id}: {STATUS} ({timestamp})
  - Summary: {one-line description}
  - Issues: Critical({c})/Major({m})/Minor({n})
  - Status: COMPLETE|FAILED
```

Update statistics section in `.pi/ralph/progress.md`:
- Increment "Tickets completed" or "Tickets failed"
- Update "Last updated" timestamp

**7b. Extract Lessons (Conditional)**

Review the implementation journey and identify lessons worth preserving:

Only extract a lesson if:
- A gotcha was discovered that could trip up future work
- A successful pattern emerged that should be reused
- Technical debt was identified that needs tracking
- Tool/environment issues were encountered

If lessons found, append to `.pi/ralph/AGENTS.md`:
```markdown
## Lesson from {ticket-id} ({date})

**Context**: {brief context - what were you working on}

**Lesson**: {what was learned}

**Apply when**: {when to use this lesson in future}
```

Keep lessons concise (3-5 sentences max).

**7c. Output Promise Sigil**

Print to output:
```
<promise>TICKET_{ticket-id}_{STATUS}</promise>
```

Where STATUS is:
- `COMPLETE` - ticket successfully implemented and closed
- `FAILED` - unrecoverable error or max retries reached

---

## Output Artifacts

Written to current working directory:
- `implementation.md`
- `review.md` 
- `fixes.md`
- `close-summary.md`

Ralph loop files (if `.pi/ralph/` exists):
- `.pi/ralph/progress.md` - Updated with this ticket
- `.pi/ralph/AGENTS.md` - May be updated with new lessons

Plus knowledge base (if research ran):
- `.pi/knowledge/tickets/{ticket}.md`

---

## Error Handling

- If `switch_model` fails, report the error and continue with current model
- If parallel reviews fail, report which reviewer(s) failed and continue with available reviews
- If `tk` commands fail, document the failure in close-summary.md and progress.md (if Ralph active)
- If `.pi/ralph/` files cannot be written, log warning but don't fail the ticket

---

## Comparison: /irf vs /irf-lite

| Aspect | /irf | /irf-lite |
|--------|------|-----------|
| Subagent spawns | 6-8 | 3 |
| Points of failure | 6-8 | 3 |
| Re-anchoring | No | Yes (Step 0) |
| Lessons learned | No | Yes (if Ralph active) |
| Progress tracking | No | Yes (if Ralph active) |
| Promise sigil | No | Yes (if Ralph active) |
| Research | Parallel subagents | Sequential (main agent) |
| Wall-clock (research) | ~5s | ~15s |
| Reliability | Lower | Higher |

---

## Ralph Loop Integration

When running in a Ralph loop:
1. Each ticket starts with fresh context + accumulated lessons
2. Progress is automatically tracked
3. Lessons are synthesized after each ticket
4. Promise sigil enables loop termination detection

When running standalone (no `.pi/ralph/`):
1. Works identically minus progress/lessons tracking
2. Root `AGENTS.md` still read for project patterns
3. No promise sigil output

---

## Using with Ralph

Initialize once:
```bash
./bin/irf ralph init
```

Run manually with tracking:
```
/irf-lite <ticket-id>
# Progress and lessons automatically captured
```

Or run in loop:
```
/ralph-start --max-iterations 50
# Calls /irf-lite repeatedly until backlog empty
```
