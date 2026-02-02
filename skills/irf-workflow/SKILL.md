---
name: tf-workflow
description: Execute the Implement → Review → Fix → Close workflow for ticket implementation. Use when implementing any ticket, whether standalone or in a Ralph loop.
---

# IRF Workflow Skill

Core expertise for the Implement → Review → Fix → Close cycle.

## When to Use This Skill

- Implementing a ticket from your backlog
- Processing tickets in a Ralph autonomous loop
- Any code change requiring review and quality checks

## Prerequisites

Before executing, verify:
1. `tk` CLI is available: `which tk`
2. `switch_model` tool is available (from `pi-model-switch` extension)
3. `subagent` tool is available (from `pi-subagents` extension)
4. Ticket exists: `tk show <ticket-id>` succeeds

### Extension Requirements

This skill requires three Pi extensions:

| Extension | Purpose |
|-----------|---------|
| `pi-prompt-template-model` | **Entry model switch** - Sets the initial model via frontmatter when the command starts |
| `pi-model-switch` | **Runtime model switches** - Changes models between workflow phases (implement → review → fix) |
| `pi-subagents` | **Parallel reviews** - Spawns reviewer subagents |

Install them:
```bash
pi install npm:pi-prompt-template-model
pi install npm:pi-model-switch
pi install npm:pi-subagents
```

## Configuration

Read workflow config (project overrides global):
- `.pi/workflows/tf/config.json`
- `~/.pi/agent/workflows/tf/config.json`

Key config values:
- `metaModels` - Abstract model definitions (model + thinking)
- `agents` - Maps agent names to meta-model keys
- `workflow.*` - Enable/disable workflow steps

Model resolution order:
1. Look up agent name in `agents` map → get meta-model key
2. Look up meta-model key in `metaModels` → get model ID
3. Use `switch_model` with resolved model ID
- `workflow.enableResearcher` - Whether to run research step
- `workflow.researchParallelAgents` - Parallelism for research fetches
- `workflow.enableReviewers` - Which reviewers to run (empty = skip)
- `workflow.enableFixer` - Whether to run fix step
- `workflow.enableCloser` - Whether to run close step
- `workflow.enableQualityGate` - Whether to enforce fail-on severities
- `workflow.failOn` - List of severities that block closing
- `workflow.knowledgeDir` - Where to store knowledge artifacts

## Flag Handling

Parse flags from the Task input before running any steps:

- `--plan` / `--dry-run`: Print the resolved chain (enabled/disabled steps, models, reviewers) and exit without running agents.
- `--no-research`: Skip research even if enabled in config.
- `--with-research`: Force research even if disabled in config.
- `--create-followups`: After review merge, run `/tf-followups` (or equivalent procedure) on the merged review.
- `--simplify-tickets`: After the chain completes, run `/simplify --create-tickets --last-implementation` if the command exists. If not available, warn and continue.
- `--final-review-loop`: After the chain completes, run `/review-start` if the review-loop extension is installed. If not available, warn and continue.

## Execution Procedures

### Procedure: Re-Anchor Context

Run this at the start of EVERY ticket implementation to prevent context rot.

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.pi/ralph/AGENTS.md`
   - If referenced, read `.pi/ralph/AGENTS.md` for lessons learned

2. **Read knowledge base**
   - Check `{knowledgeDir}/tickets/{ticket}.md` for ticket-specific research
   - Read if exists

3. **Get ticket details**
   - Run `tk show {ticket}` to get full ticket description

4. **Parse planning references** (note, don't load yet):
   - "OpenSpec Change: {id}" → `openspec/changes/{id}/`
   - "IRF Seed: {topic}" → `{knowledgeDir}/topics/{topic}/`
   - "Spike: {topic}" → `{knowledgeDir}/topics/{topic}/`
   - Only load if explicitly needed during implementation

### Procedure: Research (Optional)

Skip if: `--no-research` flag OR (`workflow.enableResearcher` is false AND `--with-research` not set)

**With existing research:**
- If `{knowledgeDir}/tickets/{ticket}.md` exists and is sufficient, use it

**Fresh research:**
1. Check available MCP tools (context7, exa, grep_app, zai-web-search)
2. If `workflow.researchParallelAgents` > 1 and `researcher-fetch` is available, spawn parallel fetches (docs/web/code). Otherwise, query sequentially.
3. Synthesize findings
4. Write to `{knowledgeDir}/tickets/{ticket}.md`

### Procedure: Implement

1. **Switch to implementer model**:
   - Look up `agents.implementer` in config → get meta-model key (e.g., "worker")
   - Look up `metaModels.{key}.model` → get actual model ID
   - ```
     switch_model action="switch" search="{metaModels.worker.model}"
     ```

2. **Review all gathered context** from Re-Anchor procedure

3. **Explore codebase**:
   - Use `find` and `grep` to locate relevant files
   - Follow existing patterns from AGENTS.md

4. **Implement changes**:
   - Make focused, single-responsibility changes
   - Track changed files in memory
   - Follow project patterns exactly

5. **Run quality checks**:
   - Load checkers from config
   - Run lint/format on changed files
   - Run typecheck on project
   - Fix any issues found

6. **Run tests**:
   - Execute relevant tests
   - Verify implementation

7. **Write `implementation.md`**:
   ```markdown
   # Implementation: {ticket-id}

   ## Summary
   Brief description of changes

   ## Files Changed
   - `path/to/file.ts` - what changed

   ## Key Decisions
   - Why approach X was chosen

   ## Tests Run
   - Commands and results

   ## Verification
   - How to verify it works
   ```

### Procedure: Parallel Reviews

This is the ONLY step requiring subagents.

**Determine reviewers**:
- If `workflow.enableReviewers` is set, use that list in order.
- If not set, default to: `reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`.
- If the list is empty, skip reviews and write a stub `review.md` with "No reviews run" in Critical.

Each reviewer uses a different meta-model:
- `reviewer-general` → `metaModels.review-general.model`
- `reviewer-spec-audit` → `metaModels.review-spec.model`  
- `reviewer-second-opinion` → `metaModels.review-secop.model`

**Execute parallel subagents**:
```json
{
  "tasks": [
    {"agent": "reviewer-general", "task": "{ticket}"},
    {"agent": "reviewer-spec-audit", "task": "{ticket}"},
    {"agent": "reviewer-second-opinion", "task": "{ticket}"}
  ]
}
```

Store returned paths for next step.

### Procedure: Merge Reviews

1. **Handle skipped reviews**:
   - If no reviewer outputs exist (reviews disabled), write a stub `review.md` with "No reviews run" in Critical and zero counts, then return.

2. **Switch to review-merge model**:
   - Look up `agents.review-merge` in config → get meta-model key ("fast")
   - Look up `metaModels.fast.model` → get actual model ID
   - ```
     switch_model action="switch" search="{metaModels.fast.model}"
     ```

3. **Read available review outputs**

4. **Deduplicate issues**:
   - Match by file path + line number + description similarity
   - Keep highest severity when duplicates found
   - Note source reviewer(s)

5. **Write consolidated `review.md`**:
   ```markdown
   # Review: {ticket-id}

   ## Critical (must fix)
   - `file.ts:42` - Issue description

   ## Major (should fix)
   - `file.ts:100` - Issue description

   ## Minor (nice to fix)
   - `file.ts:150` - Issue description

   ## Warnings (follow-up ticket)
   - `file.ts:200` - Future work

   ## Suggestions (follow-up ticket)
   - `file.ts:250` - Improvement idea

   ## Summary Statistics
   - Critical: {count}
   - Major: {count}
   - Minor: {count}
   - Warnings: {count}
   - Suggestions: {count}
   ```

### Procedure: Fix Issues

1. **Check if fixer is enabled**:
   - If `workflow.enableFixer` is false, write `fixes.md` noting the fixer is disabled and skip this step.

2. **Switch to fixer model** (if different):
   - Look up `agents.fixer` in config → get meta-model key ("fast")
   - Look up `metaModels.fast.model` → get actual model ID
   - ```
     switch_model action="switch" search="{metaModels.fast.model}"
     ```

3. **Check review issues**:
   - If zero Critical/Major/Minor: write "No fixes needed" to `fixes.md`, skip to Close

4. **Fix issues**:
   - Fix all Critical issues (required)
   - Fix all Major issues (should do)
   - Fix Minor issues if low effort
   - Do NOT fix Warnings/Suggestions (these become follow-up tickets)

5. **Re-run tests** after fixes

6. **Write `fixes.md`** documenting what was fixed

### Procedure: Follow-up Tickets (Optional)

Run only when `--create-followups` is provided.

1. **Use merged review**: Ensure `review.md` exists.
2. **Create follow-ups**: Run `/tf-followups <review.md>` or follow the IRF Planning "Follow-up Creation" procedure.
3. **Write `followups.md`** documenting created tickets or "No follow-ups needed".

### Procedure: Close Ticket

No model switch needed - stay on current model.

1. **Check close gating**:
   - Parse `review.md` counts (Critical/Major/Minor/Warnings/Suggestions).
   - If `workflow.enableCloser` is false, write `close-summary.md` noting closure was skipped and do not call `tk`.
   - If `workflow.enableQualityGate` is true and any severity in `workflow.failOn` has a nonzero count, write `close-summary.md` with status BLOCKED and do not call `tk`.

2. **Read `implementation.md`, `review.md`, `fixes.md`**

3. **Compose summary note** for ticket

4. **Add note via `tk add-note`**

5. **Close ticket via `tk close`**

6. **Write `close-summary.md`**

### Procedure: Final Review Loop (Optional)

Run only when `--final-review-loop` is provided.

1. Check if `/review-start` is available (pi-review-loop extension).
2. If available, run `/review-start`.
3. If not available, warn and continue.

### Procedure: Simplify Tickets (Optional)

Run only when `--simplify-tickets` is provided.

1. Check if `/simplify` is available.
2. If available, run `/simplify --create-tickets --last-implementation`.
3. If not available, warn and continue.

### Procedure: Ralph Integration (Optional)

Only if `.pi/ralph/` directory exists:

**Update Progress**:
- Append to `.pi/ralph/progress.md`:
  ```markdown
  - {ticket-id}: {STATUS} ({timestamp})
    - Summary: {one-line}
    - Issues: Critical({c})/Major({m})/Minor({n})
    - Status: COMPLETE|FAILED
  ```

**Extract Lessons** (conditional):
- Only if a gotcha was discovered or pattern emerged
- Append to `.pi/ralph/AGENTS.md`:
  ```markdown
  ## Lesson from {ticket-id} ({date})

  **Context**: {brief context}
  **Lesson**: {what was learned}
  **Apply when**: {when to use this}
  ```

**Output Promise Sigil**:
```
<promise>TICKET_{ticket-id}_{STATUS}</promise>
```

## Full Workflow Execution

### For /tf (Standard)

```
1. Re-Anchor Context
2. Research (optional)
3. Implement (model-switch)
4. Parallel Reviews (optional)
5. Merge Reviews (optional)
6. Fix Issues (optional)
7. Follow-ups (optional)
8. Close Ticket (optional / gated)
9. Final Review Loop (optional)
10. Simplify Tickets (optional)
11. Ralph Integration (if active)
```

### /tf-lite (Deprecated Alias)

`/tf-lite` runs the same workflow as `/tf` and will be removed in a future release.

## Error Handling

- **switch_model fails**: Report error, continue with current model
- **Parallel reviews fail**: Continue with available reviews
- **tk commands fail**: Document in close-summary.md
- **Quality gate blocks**: Skip closing, mark close-summary.md as BLOCKED
- **Ralph files fail**: Log warning, don't fail ticket

## Output Artifacts

Always written to current working directory:
- `implementation.md` - What was implemented
- `review.md` - Consolidated review
- `fixes.md` - What was fixed
- `followups.md` - Follow-up tickets (if `--create-followups`)
- `close-summary.md` - Final summary
- `chain-summary.md` - Links to artifacts (if closer runs)

Ralph files (if active):
- `.pi/ralph/progress.md` - Updated
- `.pi/ralph/AGENTS.md` - May be updated with lessons

Knowledge base (if research ran):
- `{knowledgeDir}/tickets/{ticket}.md`
