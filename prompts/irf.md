---
description: Full workflow - implement ticket, review with fresh eyes, fix issues, and close. Use --auto/--no-clarify for non-interactive mode.
---

# Implement → Review → Fix → Close Workflow

Execute the complete ticket implementation workflow using the `subagent` tool.

## Invocation arguments (IMPORTANT)

This prompt template is invoked as:

```
/irf <ticket-id> [flags...]
```

Pi passes the arguments to this template as:

- First arg: `$1`
- All args (space-joined): `$@`

Use **`$@` as the raw task input** for parsing ticket + flags.

If `$1` is empty (no args provided), ask the user for the ticket ID (and optional flags) and stop.

## Workflow Config (optional)

Look for workflow config files (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json` (project)
- `~/.pi/agent/workflows/implement-review-fix-close/config.json` (global)

If present, merge them with project settings taking precedence.

Use config values if provided:
- `workflow.clarifyDefault`: default clarify value when no flags are passed (fallback: true)
- `workflow.enableResearcher`: enable/disable research step (default true)
- `workflow.knowledgeDir`: knowledge directory for research (default `.pi/knowledge`)
- `workflow.enableReviewers`: list of reviewer agent names for parallel review step (fallback: reviewer-general, reviewer-spec-audit, reviewer-second-opinion)
- `workflow.enableFixer`: include/exclude fixer step (default true)
- `workflow.enableCloser`: include/exclude closer step (default true)
- `workflow.enableQualityGate`: run quality checks after fix/merge (default false)
- `workflow.failOn`: list of severities that block closing (e.g., ["Critical","Major"])
- `workflow.researchParallelAgents`: minimum parallel research agents when fetching (default 3)

If you update model settings in the config, run `/irf-sync` to apply models to agent files.

## Parse Task Flags

From `$@` determine flags:

- `--auto` or `--no-clarify` → set `clarify: false` (headless mode)
- `--plan` or `--dry-run` → show resolved plan, do not run any agents
- `--create-followups` → after review merge, run `/irf-followups` on the merged review
- `--simplify-tickets` → after closing the ticket, run: `/simplify --create-tickets --last-implementation`
- `--final-review-loop` → after the chain completes, start review loop: `/review-start`
- `--with-research` → force enable research step
- `--no-research` → force disable research step
- No flags → set `clarify` to `workflow.clarifyDefault` if configured, otherwise `true`

Determine `{ticket}`:

- Prefer `$1` as the ticket ID.
- If `$1` does not look like a ticket ID, scan `$@` for the first token matching `mme-...`.
- Strip/remove flags from the ticket string.

## Reviewer Output Derivation (dynamic)

Build reviewer steps from `workflow.enableReviewers` if provided, otherwise use:

- `reviewer-general`
- `reviewer-spec-audit`
- `reviewer-second-opinion`

For each reviewer agent name:

- **Short name**: strip the `reviewer-` prefix if present; otherwise use the full name.
- **Output filename**: `review-{short}.md`
- **Task text**:
  - `reviewer-general` → `Review implementation for {ticket} with fresh eyes`
  - `reviewer-spec-audit` → `Spec audit for {ticket}`
  - `reviewer-second-opinion` → `Second-opinion review for {ticket}`
  - Default → `Review implementation for {ticket}`

The merge step must read the reviewer outputs from the parallel step directory. After you build the chain array, determine the **parallel step index** (0-based) and use:

```
parallel-{parallelIndex}/{i}-{agentName}/{outputFile}
```

## Execution Plan (two-phase)

### Phase A: Base chain (research → implement → parallel reviews → merge)

Build the base chain array:

1. **Research** (optional)
2. **Implement** (task includes chain dir in text)
3. **Parallel reviews** (dynamic list)
4. **Review merge** (reads dynamic outputs)

If `--plan/--dry-run` is set:
- Print the resolved chain as JSON (including reviewer outputs and merge reads).
- Print `clarify` value and the computed reviewer list.
- Exit without running any agents.

Otherwise, execute **Phase A** with `subagent` (chain mode) using `clarify: {determine_from_flags}`.

### Phase B: Conditional steps (fixer/closer)

After Phase A finishes:

1. **Get chain dir** from the subagent result (line like `Artifacts: /tmp/pi-chain-runs/...`).
2. **Read** `${chainDir}/review.md` and **count issues** per severity:
   - Parse sections `## Critical`, `## Major`, `## Minor`, `## Warnings`, `## Suggestions`
   - Count bullet lines beginning with `- ` under each section.

3. **Follow-ups (optional)**:
   - If `--create-followups` is set, run `/irf-followups` using the merged review:
     ```json
     {
       "agent": "irf-planner",
       "task": "IRF-FOLLOWUPS\nInput: {chainDir}/review.md",
       "output": "{chainDir}/followups.md",
       "clarify": false
     }
     ```

4. **Fixer (conditional)**:
   - If `workflow.enableFixer` is false → skip.
   - If Critical/Major/Minor counts are all zero → write `${chainDir}/fixes.md` stub: "No fixes needed" (do **not** invoke fixer).
   - Else invoke fixer as a **single subagent call**:
     ```json
     {
       "agent": "fixer",
       "task": "Fix Critical/Major/Minor issues for {ticket} from review (chain dir: {chainDir})",
       "reads": ["{chainDir}/review.md"],
       "output": "{chainDir}/fixes.md",
       "clarify": "{determine_from_flags}"
     }
     ```

5. **Quality Gate (optional)**:
   - If `workflow.enableQualityGate` is true, run checkers against `${chainDir}/files_changed.txt`.
   - Use the same checker config rules as `implementer` (lint/format per file list, typecheck once).
   - Write results to `${chainDir}/quality.md` (commands + exit codes + notes).
   - If no `files_changed.txt` exists, note that and skip checks.

6. **Fail-on gate**:
   - If `workflow.failOn` contains any severity whose count > 0, stop **before closer**.
   - Print a clear blocking message and exit non‑zero (after fixer/quality gate if they ran).

7. **Closer (conditional)**:
   - If `workflow.enableCloser` is false → skip.
   - Otherwise invoke closer as a **single subagent call**:
     ```json
     {
       "agent": "closer",
       "task": "Add summary comment and close ticket {ticket} (chain dir: {chainDir})",
       "reads": [
         "{chainDir}/implementation.md",
         "{chainDir}/review.md",
         "{chainDir}/ticket_id.txt",
         "{chainDir}/fixes.md"
       ],
       "output": "{chainDir}/close-summary.md",
       "clarify": "{determine_from_flags}"
     }
     ```

8. **Summary JSON (always)**:
   - Write `${chainDir}/summary.json` with:
     - `ticketId`
     - `flags`
     - `reviewCounts` (Critical/Major/Minor/Warnings/Suggestions)
     - `filesChanged` (from `${chainDir}/files_changed.txt` if present)
     - `testsRun` (parse from `implementation.md` and `fixes.md` sections)
     - `timestamps` (start/end ISO)

## Optional Post-Chain Steps

After the chain completes:

- If `--simplify-tickets` was set: run `/simplify --create-tickets --last-implementation`
- If `--final-review-loop` was set: run `/review-start`
