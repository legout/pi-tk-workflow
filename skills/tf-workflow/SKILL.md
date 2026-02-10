---
name: tf-workflow
description: Execute the Implement → Review → Fix → Close workflow for ticket implementation. Use when implementing any ticket, whether standalone or in a Ralph loop.
---

# TF Workflow Skill

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

Read workflow config (project):
- `.tf/config/settings.json`

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
- `workflow.knowledgeDir` - Base directory for knowledge/artifacts (artifactDir = `{knowledgeDir}/tickets/{ticket-id}/`)
- `workflow.escalation` - Retry-aware model escalation configuration (see Retry Escalation section)

## Flag Handling

Parse flags from the Task input before running any steps:

- `--plan` / `--dry-run`: Print the resolved chain (enabled/disabled steps, models, reviewers) and exit without running agents.
- `--no-research`: Skip research even if enabled in config.
- `--with-research`: Force research even if disabled in config.
- `--create-followups`: After review merge, run `/tf-followups` (or equivalent procedure) on the merged review.
- `--simplify-tickets`: After the chain completes, run `/simplify --create-tickets --last-implementation` if the command exists. If not available, warn and continue.
- `--final-review-loop`: After the chain completes, run `/review-start` if the review-loop extension is installed. If not available, warn and continue.
- `--retry-reset`: Force a fresh retry attempt (renames existing `retry-state.json` to `.bak.{timestamp}`).

## Execution Procedures

### Procedure: Re-Anchor Context

Run this at the start of EVERY ticket implementation to prevent context rot.

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.tf/ralph/AGENTS.md`
   - If referenced, read `.tf/ralph/AGENTS.md` for lessons learned

2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
   - `mkdir -p {artifactDir}`

3. **Handle retry reset flag** (if `--retry-reset` provided)
   - If `{artifactDir}/retry-state.json` exists, rename to `retry-state.json.bak.{timestamp}`
   - Log: "Retry state reset for {ticket-id}"

4. **Load retry state** (see Load Retry State subsection)
   - Check for `{artifactDir}/retry-state.json`
   - If exists and last attempt was BLOCKED → increment retry count, determine escalation
   - Store `attemptNumber` (1-indexed) and `escalatedModels` for use in subsequent phases

5. **Read knowledge base**
   - Prefer `{artifactDir}/research.md` for ticket-specific research
   - Back-compat: if `{knowledgeDir}/tickets/{ticket}.md` exists, read it and (optionally) migrate to `{artifactDir}/research.md`

6. **Get ticket details**
   - Run `tk show {ticket}` to get full ticket description

7. **Parse planning references** (note, don't load yet):
   - "OpenSpec Change: {id}" → `openspec/changes/{id}/`
   - "IRF Seed: {topic}" → `{knowledgeDir}/topics/{topic}/`
   - "Spike: {topic}" → `{knowledgeDir}/topics/{topic}/`
   - Only load if explicitly needed during implementation

#### Load Retry State (Sub-procedure)

Determines if this is a retry attempt and calculates model escalation.

**Prerequisites**: 
- `workflow.escalation.enabled` must be `true` for escalation to apply
- Escalation config format (inside `workflow` section of `settings.json`):
  ```json
  {
    "workflow": {
      "escalation": {
        "enabled": false,
        "maxRetries": 3,
        "models": {
          "fixer": null,
          "reviewerSecondOpinion": null,
          "worker": null
        }
      }
    }
  }
  ```

**Algorithm**:
1. Check if `{artifactDir}/retry-state.json` exists
2. If not exists: `attemptNumber = 1`, `retryCount = 0`, no escalation
3. If exists:
   - Parse JSON, validate schema version (must be 1), validate required fields (version, ticketId, attempts, lastAttemptAt, status)
   - If corrupted/invalid: Log warning, backup to `retry-state.json.bak.{timestamp}`, treat as no state
   - Else if last attempt was BLOCKED:
     - `attemptNumber = len(attempts) + 1`
     - `retryCount = retryCount + 1`
     - If `retryCount >= maxRetries`: Log warning "Max retries exceeded"
   - Else if last attempt was CLOSED:
     - `attemptNumber = 1`, `retryCount = 0` (reset on success)
   - Else (in_progress): Resume current attempt
4. **Determine escalation models** based on `attemptNumber`:
   
   | Attempt Number | Fixer Model | Reviewer-2nd-Opinion Model | Worker Model |
   |----------------|-------------|---------------------------|--------------|
   | 1 (first attempt) | Base model | Base model | Base model |
   | 2 (first retry) | Escalated fixer or base | Base model | Base model |
   | 3+ (subsequent retries) | Escalated fixer or base | Escalated reviewer-2nd-op or base | Escalated worker or base |

   **Base model resolution**: Look up `agents.{role}` → get meta-model key → look up `metaModels.{key}.model`
   **Escalated model resolution**: If `workflow.escalation.models.{role}` is not null, use it; else use base model

   Base model resolution: `agents.{role}` → `metaModels.{key}.model`

**Detection Algorithm** (for determining BLOCKED status):

Primary detection (close-summary.md):
```python
def detect_blocked_from_close_summary(path):
    if not path.exists(): return None
    content = path.read_text()
    # Match: ## Status followed by BLOCKED (case-insensitive)
    if re.search(r'##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?BLOCKED(?:\*\*)?(?:\s|$)', content, re.IGNORECASE):
        # Extract severity counts from Summary Statistics
        counts = {}
        for sev in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
            match = re.search(rf'(?:^|\s|[-*]\s*)(?:\*\*)?{sev}(?:\*\*)?\s*:\s*(\d+)', content, re.IGNORECASE | re.MULTILINE)
            counts[sev] = int(match.group(1)) if match else 0
        return {"status": "blocked", "counts": counts}
    return None
```

Fallback detection (review.md):
```python
def detect_blocked_from_review(path, fail_on):
    if not path.exists() or not fail_on: return None
    content = path.read_text()
    counts = {}
    blocked = False
    for severity in fail_on:
        # Match section header (e.g., "## Critical (must fix)", "## Major")
        pattern = rf'^##\s*(?:\*\*)?{re.escape(severity)}(?:\*\*)?(?:\s*\([^)]*\))?'
        section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if section_match:
            # Find the section boundaries
            section_start = section_match.end()
            next_header = re.search(r'\n^##\s', content[section_start:], re.MULTILINE)
            section_end = section_start + next_header.start() if next_header else len(content)
            section = content[section_start:section_end]
            
            # Check if section has bullet items
            has_items = bool(re.search(r'\n-\s', section))
            
            # Extract count from summary statistics (fallback to 1 if items exist but no count)
            stat_match = re.search(rf'(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)', content, re.IGNORECASE | re.MULTILINE)
            if stat_match:
                count = int(stat_match.group(1))
            else:
                count = 1 if has_items else 0
            counts[severity] = count
            if count > 0: blocked = True
    return {"status": "blocked", "counts": counts} if blocked else None
```

**Output**: Sets `attemptNumber` (int, 1-indexed) and `escalatedModels` dict for use in Implement, Parallel Reviews, and Fix Issues phases.

### Procedure: Research (Optional)

Skip if: `--no-research` flag OR (`workflow.enableResearcher` is false AND `--with-research` not set)

**Non-negotiable artifact rule (prevents silent skipping):**
If the research step is **active** (i.e. not skipped by `--no-research` and enabled/forced by config/flags), you **MUST ensure** a research artifact exists at:
- `{artifactDir}/research.md`

If you decide that no additional research is required, still write a **minimal stub** that states that research was enabled but nothing was needed.

**With existing research:**
- If `{artifactDir}/research.md` exists and is sufficient, use it
- Back-compat: if `{knowledgeDir}/tickets/{ticket}.md` exists, read it and migrate to `{artifactDir}/research.md`

**Fresh research (best effort):**
1. **Prefer pi-web-access when available** (tools: `web_search`, `fetch_content`, `get_search_content`).
   - If these tools are available, use them as **primary**.
   - Use a **single agent only** (do NOT spawn `researcher-fetch`) because `web_search` can batch queries and `fetch_content` runs concurrent fetches.
   - Suggested flow: `web_search` (optionally with `includeContent: true`) → `fetch_content` for key docs/repos → `get_search_content` as needed.
2. **Fallback to MCP tools** when pi-web-access is unavailable.
   - Check available MCP tools (context7, exa, grep_app, zai-web-search).
   - MCP config may be project-local (`.pi/mcp.json`) or global (`~/.pi/agent/mcp.json`).
   - If `workflow.researchParallelAgents` > 1 and `researcher-fetch` is available, spawn parallel fetches (docs/web/code). Otherwise, query sequentially.
   - If MCP tools are unavailable, fall back to local repo docs.
3. Synthesize findings
4. Write to `{artifactDir}/research.md`

**Minimal stub template (OK when there is nothing to research):**
```markdown
# Research: {ticket-id}

## Status
Research enabled. No additional external research was performed.

## Rationale
- <why research was not needed / ticket is straightforward>

## Context Reviewed
- `tk show {ticket-id}`
- Repo docs / existing topic knowledge

## Sources
- (none)
```

### Procedure: Implement

1. **Switch to worker model**:
   - If `escalatedModels.worker` is set (attempt 3+ with worker escalation): use that model
   - Else: Look up `metaModels.worker.model` → get actual model ID
   - ```
     switch_model action="switch" search="{worker_model_id}"
     ```

2. **Review all gathered context** from Re-Anchor procedure, including `attemptNumber` and `escalatedModels`

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

7. **Write `{artifactDir}/implementation.md`**:
   ```markdown
   # Implementation: {ticket-id}

   ## Summary
   Brief description of changes

   ## Retry Context
   - Attempt: {attemptNumber}
   - Escalated Models: fixer={escalatedModels.fixer or 'base'}, reviewer-second={escalatedModels.reviewerSecondOpinion or 'base'}, worker={escalatedModels.worker or 'base'}

   ## Files Changed
   - `path/to/file.ts` - what changed

   ## Key Decisions
   - Why approach X was chosen

   ## Tests Run
   - Commands and results

   ## Verification
   - How to verify it works
   ```
   Also write `{artifactDir}/ticket_id.txt` containing only the ticket ID.
   Ensure `{artifactDir}/files_changed.txt` is updated via `tf track ... --file {artifactDir}/files_changed.txt`.

### Procedure: Parallel Reviews

This is the ONLY step requiring subagents.

**Determine reviewers**:
- If `workflow.enableReviewers` is set, use that list in order.
- If not set, default to: `reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`.
- If the list is empty, skip reviews and write a stub `{artifactDir}/review.md` with "No reviews run" in Critical.

Each reviewer uses a different meta-model:
- `reviewer-general` → `metaModels.review-general.model`
- `reviewer-spec-audit` → `metaModels.review-spec.model`
- `reviewer-second-opinion` → `escalatedModels.reviewerSecondOpinion` (if set for attempt 3+) or `metaModels.review-secop.model`

Reviewer implementation note:
- The three reviewer agents are thin wrappers over the shared `tf-review` skill.
- Keep wrappers separate to preserve model diversity in parallel review runs.

**Resolve repo root for reviewer cwd**:
- Run `git rev-parse --show-toplevel` to get `{repoRoot}`
- If it fails (non-git), use the current working directory

**Execute parallel subagents** (run from repo root so `src/...` and `tk show` work):
```json
{
  "agentScope": "project",
  "tasks": [
    {"agent": "reviewer-general", "task": "{ticket}", "cwd": "{repoRoot}"},
    {"agent": "reviewer-spec-audit", "task": "{ticket}", "cwd": "{repoRoot}"},
    {"agent": "reviewer-second-opinion", "task": "{ticket}", "cwd": "{repoRoot}"}
  ]
}
```

**Model escalation for reviewer-second-opinion**:
- If `escalatedModels.reviewerSecondOpinion` is set (attempt 3+ with escalation): Pass it to the subagent via model parameter or ensure the agent reads it from context
- The reviewer-second-opinion agent should use the escalated model if provided

`agentScope: "project"` is required so reviewer agents are discovered from `.pi/agents/` in this repository.

Ensure reviewers read `{artifactDir}/implementation.md` (derive `artifactDir` from config or default `.tf/knowledge`).
Store returned paths for next step.

### Procedure: Merge Reviews

1. **Handle skipped reviews**:
   - If no reviewer outputs exist (reviews disabled), write a stub `{artifactDir}/review.md` with "No reviews run" in Critical and zero counts, then return.

2. **Switch to review-merge model**:
   - Look up `agents.review-merge` in config → get meta-model key ("general")
   - Look up `metaModels.general.model` → get actual model ID
   - ```
     switch_model action="switch" search="{metaModels.general.model}"
     ```

3. **Read available review outputs** from `{artifactDir}/review-general.md`, `{artifactDir}/review-spec.md`, `{artifactDir}/review-second.md` when present

4. **Deduplicate issues**:
   - Match by file path + line number + description similarity
   - Keep highest severity when duplicates found
   - Note source reviewer(s)

5. **Write consolidated `{artifactDir}/review.md`**:
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
   - If `workflow.enableFixer` is false, write `{artifactDir}/fixes.md` noting the fixer is disabled and skip this step.

2. **Switch to fixer model** (with escalation support):
   - If `escalatedModels.fixer` is set (attempt 2+ with fixer escalation): use that model
   - Else: Look up `agents.fixer` → `metaModels.general.model` → get actual model ID
   - ```
     switch_model action="switch" search="{fixer_model_id}"
     ```

3. **Check review issues**:
   - If zero Critical/Major/Minor: write "No fixes needed" to `{artifactDir}/fixes.md`, skip to Close

4. **Fix issues**:
   - Fix all Critical issues (required)
   - Fix all Major issues (should do)
   - Fix Minor issues if low effort
   - Do NOT fix Warnings/Suggestions (these become follow-up tickets)
   - Track edits via `tf track ... --file {artifactDir}/files_changed.txt`

5. **Re-run tests** after fixes

6. **Write `{artifactDir}/fixes.md`** documenting what was fixed

### Procedure: Follow-up Tickets (Optional)

Run only when `--create-followups` is provided.

1. **Use merged review**: Ensure `{artifactDir}/review.md` exists.
2. **Create follow-ups**: Run `/tf-followups {artifactDir}/review.md` or follow the IRF Planning "Follow-up Creation" procedure.
3. **Write `{artifactDir}/followups.md`** documenting created tickets or "No follow-ups needed".

### Procedure: Close Ticket

No model switch needed - stay on current model.

1. **Check close gating**:
   - Parse `{artifactDir}/review.md` counts (Critical/Major/Minor/Warnings/Suggestions) using the detection algorithm:
     ```python
     severity_counts = {}
     for sev in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
         match = re.search(rf'(?:^|\s|[-*]\s*)(?:\*\*)?{sev}(?:\*\*)?\s*:\s*(\d+)', review_content, re.IGNORECASE | re.MULTILINE)
         severity_counts[sev] = int(match.group(1)) if match else 0
     ```
   - If `workflow.enableCloser` is false, write `{artifactDir}/close-summary.md` noting closure was skipped and do not call `tk`.
   - If `workflow.enableQualityGate` is true and any severity in `workflow.failOn` has nonzero count:
     - Set `closeStatus = BLOCKED`
     - `blocked_counts = {sev: severity_counts[sev] for sev in workflow.failOn if severity_counts.get(sev, 0) > 0}`
   - Else: `closeStatus = CLOSED`, `blocked_counts = {}`

2. **Update retry state** (if escalation enabled):
   - Read or initialize `{artifactDir}/retry-state.json`:
     ```json
     {
       "version": 1,
       "ticketId": "{ticket-id}",
       "attempts": [],
       "lastAttemptAt": "",
       "status": "active",
       "retryCount": 0
     }
     ```
   - Create new attempt entry:
     ```json
     {
       "attemptNumber": {attemptNumber},
       "startedAt": "{start_timestamp}",
       "completedAt": "{now_timestamp}",
       "status": "{closeStatus.lower()}",
       "trigger": "{trigger_type}",
       "qualityGate": {
         "failOn": {workflow.failOn},
         "counts": {blocked_counts if closeStatus == BLOCKED else severity_counts}
       },
       "escalation": {
         "fixer": {escalatedModels.fixer or null},
         "reviewerSecondOpinion": {escalatedModels.reviewerSecondOpinion or null},
         "worker": {escalatedModels.worker or null}
       },
       "closeSummaryRef": "close-summary.md"
     }
     ```
   - Append to `attempts` array
   - Update aggregate fields:
     - `lastAttemptAt = now_timestamp`
     - `status = "closed"` if `closeStatus == CLOSED`, else `"blocked"`
     - `retryCount = retryCount + 1` if `closeStatus == BLOCKED`, else `0` (reset on success)
   - Write updated `retry-state.json` atomically:
     ```python
     import json
     import os
     temp_path = f"{retry_state_path}.tmp"
     with open(temp_path, 'w') as f:
         json.dump(state, f, indent=2)
     os.replace(temp_path, retry_state_path)  # Atomic rename
     ```

3. **Handle BLOCKED status**:
   - If `closeStatus == BLOCKED`: Write `{artifactDir}/close-summary.md` with status BLOCKED, skip calling `tk close`
   - If `closeStatus == CLOSED`: Continue with close workflow

4. **Read artifacts**: `{artifactDir}/implementation.md`, `{artifactDir}/review.md`, `{artifactDir}/fixes.md` (if exists), and `{artifactDir}/files_changed.txt`.

5. **Commit changes (required)**:
   - If inside a git repo, stage the ticket artifacts plus any paths from `{artifactDir}/files_changed.txt`:
     ```bash
     git add -A -- "{artifactDir}"
     if [ -f "{artifactDir}/files_changed.txt" ]; then
       while IFS= read -r path; do
         git add -A -- "$path" 2>/dev/null || true
       done < "{artifactDir}/files_changed.txt"
     fi
     ```
   - If staging produced changes, commit with message `"{ticket-id}: <short summary>"`.
   - Capture the commit hash for the ticket note and close-summary.
   - If no repo or no changes, note it in close-summary.

6. **Compose summary note** for ticket (include commit hash if available, retry attempt if > 1)

7. **Add note via `tk add-note`**

8. **Close ticket via `tk close`** (only if `closeStatus == CLOSED`)

9. **Write `{artifactDir}/close-summary.md`** with `## Status\n**{CLOSED|BLOCKED}**`

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

Only if `.tf/ralph/` directory exists:

**Check Skip Conditions** (before ticket selection):
- If `workflow.escalation.enabled` is true:
  - Check `{artifactDir}/retry-state.json` for `status: blocked` and `retryCount >= maxRetries`
  - If exceeded: Skip ticket, log "Skipping {ticket-id}: max retries ({maxRetries}) exceeded"
  - Also skip if `parallelWorkers > 1` and no locking mechanism is implemented (log warning)

**Update Progress**:
- Append to `.tf/ralph/progress.md`:
  ```markdown
  - {ticket-id}: {STATUS} ({timestamp})
    - Summary: {one-line}
    - Issues: Critical({c})/Major({m})/Minor({n})
    - Retry: Attempt {attemptNumber}, Count {retryCount}
    - Status: COMPLETE|FAILED|BLOCKED
  ```

**Extract Lessons** (conditional):
- Only if a gotcha was discovered or pattern emerged
- Append to `.tf/ralph/AGENTS.md`:
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
1. Re-Anchor Context (includes Load Retry State)
2. Research (optional)
3. Implement (model-switch, with escalation)
4. Parallel Reviews (optional, with escalation)
5. Merge Reviews (optional)
6. Fix Issues (optional, with escalation)
7. Follow-ups (optional)
8. Close Ticket (optional / gated, updates retry state)
9. Final Review Loop (optional)
10. Simplify Tickets (optional)
11. Ralph Integration (if active)
```

## Retry Escalation

When `workflow.escalation.enabled: true`, the workflow detects retry attempts (previous BLOCKED closes) and escalates to stronger models.

### Configuration

```json
{
  "workflow": {
    "escalation": {
      "enabled": false,
      "maxRetries": 3,
      "models": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      }
    }
  }
}
```

- `enabled`: Whether retry escalation is active (default: false)
- `maxRetries`: Maximum BLOCKED attempts before giving up (default: 3)
- `models`: Escalation model overrides (null = use base model)

### Escalation Curve

| Attempt | Fixer | Reviewer-2nd-Opinion | Worker |
|---------|-------|---------------------|--------|
| 1 (fresh) | Base | Base | Base |
| 2 | Escalated | Base | Base |
| 3+ | Escalated | Escalated | Escalated (if configured) |

### Retry State Schema

Location: `{artifactDir}/retry-state.json`

```json
{
  "version": 1,
  "ticketId": "pt-example",
  "attempts": [
    {
      "attemptNumber": 1,
      "startedAt": "2026-02-10T12:00:00Z",
      "completedAt": "2026-02-10T12:30:00Z",
      "status": "blocked",
      "trigger": "initial",
      "qualityGate": {
        "failOn": ["Critical", "Major"],
        "counts": {"Critical": 0, "Major": 2, "Minor": 1}
      },
      "escalation": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      },
      "closeSummaryRef": "close-summary.md"
    }
  ],
  "lastAttemptAt": "2026-02-10T12:00:00Z",
  "status": "blocked",
  "retryCount": 1
}
```

### Reset Policy

- Counter resets **only** on successful close (CLOSED status)
- Use `--retry-reset` flag to force fresh attempt

### Parallel Worker Safety

**Assumption**: Retry logic assumes `ralph.parallelWorkers: 1` (default).

When `ralph.parallelWorkers > 1`:
- **Option A** (recommended): Implement file-based locking on `retry-state.json` using `filelock` library:
  ```python
  from filelock import FileLock
  lock = FileLock(f"{retry_state_path}.lock")
  with lock:
      # read/write retry state
  ```
- **Option B**: Disable retry logic and log warning: "Retry escalation disabled: parallelWorkers > 1 without locking"

**Default behavior** without locking: Disable retry logic to prevent race conditions (lost updates, duplicate attempts, inconsistent escalation).
- State persists across Ralph restarts

### Parallel Worker Safety

Retry logic assumes `ralph.parallelWorkers: 1`. When parallel workers > 1:
- **Option A**: Implement file-based locking on `retry-state.json`
- **Option B**: Disable retry logic and warn about race conditions

## Error Handling

- **switch_model fails**: Report error, continue with current model
- **Parallel reviews fail**: Continue with available reviews
- **tk commands fail**: Document in close-summary.md
- **Quality gate blocks**: Skip closing, mark close-summary.md as BLOCKED
- **Ralph files fail**: Log warning, don't fail ticket

## Output Artifacts

Written under `{artifactDir}` (default `{knowledgeDir}/tickets/{ticket-id}/`):
- `research.md` - Ticket research (if research ran or migrated)
- `implementation.md` - What was implemented (includes retry attempt and escalated models)
- `review.md` - Consolidated review
- `fixes.md` - What was fixed
- `followups.md` - Follow-up tickets (if `--create-followups`)
- `close-summary.md` - Final summary (status: CLOSED or BLOCKED)
- `chain-summary.md` - Links to artifacts (if closer runs)
- `files_changed.txt` - Tracked changed files for this ticket
- `ticket_id.txt` - Ticket ID (single line)
- `retry-state.json` - Retry tracking state (if escalation enabled, see Retry State Schema)

Ralph files (if active):
- `.tf/ralph/progress.md` - Updated
- `.tf/ralph/AGENTS.md` - May be updated with lessons
