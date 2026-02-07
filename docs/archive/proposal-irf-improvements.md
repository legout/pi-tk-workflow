# Proposal: TF Workflow Improvements

## Background
The current TF workflow provides a strong end‑to‑end chain (Research → Implement → Parallel Review → Merge → Fix → Close). The improvements below focus on reliability, configurability, and better automation—while keeping the workflow safe for parallel ticket work.

## Goals
- Improve robustness and operator confidence (preflight checks, plan mode).
- Reduce manual bookkeeping (change tracking, structured outputs).
- Add optional automation (follow‑ups, quality gate) behind flags or config.
- Support project‑specific configurations cleanly (MCP server selection, reviewer list).

## Non‑Goals
- Changing the core chain order (unless explicitly gated/conditional).
- Forcing new behavior by default (most features are opt‑in via flags/config).
- Requiring git‑diff‑based tracking (problematic with parallel ticket sessions).

---

## Proposed Improvements

### 1) `tf doctor` (preflight checks)
**What:** Add `./.tf/bin/tf doctor` to validate prerequisites: `tk`, Pi binary, required extensions, MCP availability (if enabled), and language tools configured in `checkers`.

### 2) Session‑scoped change tracking (no git diff)
**What:** Maintain a per‑run change ledger in the subagent **chain artifacts directory** (`{chain_dir}`; fixed by pi‑subagents). Use **absolute paths** when writing (e.g., `${chain_dir}/files_changed.txt`). Provide a helper (`./.tf/bin/tf track <path>`) and update agents to call it after each edit/write. This keeps `files_changed.txt` **session‑accurate** and isolated from other tickets.

### 3) Follow‑up tickets behind a flag
**What:** Add `--create-followups` to run a dedicated **`/tf-followups`** command after review merge. The command parses `review.md`, creates follow‑up tickets via `tk create` (tagged, e.g. `followup`), and writes `followups.md` as a run artifact. Default behavior remains unchanged (no follow‑ups).

### 4) Quality Gate step + `quality.md`
**What:** Add an optional step that runs checkers/tests (using workflow config) and writes `quality.md` to an **absolute path** (e.g., `${chain_dir}/quality.md`). This can run after fixer (if any), or after review merge when fixer is skipped.

### 5) Skip fixer when no actionable issues
**What:** If review merge yields zero Critical/Major/Minor issues, omit the fixer step entirely and generate a `fixes.md` stub (“No fixes needed”).

### 6) `summary.json` structured output
**What:** Emit a machine‑readable summary to an **absolute path** (e.g., `${chain_dir}/summary.json`) with counts, flags, files changed, tests run, and durations.

### 7) Severity gates (fail‑on)
**What:** Add `workflow.failOn` in config (e.g., `["Critical", "Major"]`). If triggered, the chain stops before closing and reports a clear block.

### 8) Config‑driven MCP server selection
**What:** Add `workflow.mcpServers` list in config to explicitly enable/disable MCP servers. `bin/tf setup` respects this list when writing `mcp.json`.

### 9) `--plan` / `--dry-run` flag
**What:** Resolve config + flags and print the computed chain (including reviewers and steps) without running any agents.

### 10) Dynamic reviewer outputs
**What:** When `workflow.enableReviewers` changes, the prompt derives review outputs + `review-merge.reads` automatically (no manual edits).

---

## Acceptance Criteria

### 1) `tf doctor`
- Running `./.tf/bin/tf doctor` prints a checklist with pass/fail for `tk`, `pi`, required extensions, and checker tools.
- Exit code is **non‑zero** when required tools are missing.
- No files are modified.

### 2) Session‑scoped change tracking
- `files_changed.txt` is created per chain run at an **absolute path** (`${chain_dir}/files_changed.txt`) and only includes files edited/written in that run.
- No git‑diff is used to populate `files_changed.txt`.
- The helper (`./.tf/bin/tf track <path>`) appends paths in a de‑duplicated way.
- Parallel ticket runs do **not** contaminate each other’s `files_changed.txt`.

### 3) Follow‑up tickets behind a flag
- With `--create-followups`, `/tf-followups` runs after review merge and creates tickets for Warnings/Suggestions via `tk create` **with a follow‑up tag** (default: `followup`).
- The created ticket IDs and summaries are recorded in `followups.md` at an absolute path (e.g., `${chain_dir}/followups.md`).
- Without the flag, **no** follow‑up tickets are created and `/tf-followups` is not invoked.

### 4) Quality Gate step
- When enabled, the workflow writes `quality.md` with lint/format/typecheck/test commands and results to an **absolute path** (e.g., `${chain_dir}/quality.md`).
- The step runs after fixer (if invoked), otherwise after review merge.
- If disabled, no `quality.md` is generated and no quality commands are run.

### 5) Skip fixer when no actionable issues
- If review merge has zero Critical/Major/Minor issues, the fixer step is **not** invoked.
- A `fixes.md` stub is still created stating “No fixes needed.”

### 6) `summary.json`
- Each chain run produces `summary.json` at an **absolute path** (e.g., `${chain_dir}/summary.json`).
- The JSON includes: ticket ID, flags, review counts, files changed, tests run, and timestamps.

### 7) Severity gates
- Config supports `workflow.failOn` with a list of severities.
- If any matching issues exist, the chain stops before `closer`, prints a clear reason, and exits non‑zero.

### 8) Config‑driven MCP server selection
- `workflow.mcpServers` controls which MCP servers are written to `mcp.json`.
- If the list is empty, no MCP servers are configured.
- `bin/tf setup` respects this list without additional prompts.

### 9) `--plan` / `--dry-run`
- Running `/tf <ticket> --plan` prints the resolved chain and exits without invoking agents.
- Output includes resolved reviewers, steps, and config overrides.

### 10) Dynamic reviewer outputs
- `workflow.enableReviewers` can be changed without manual edits to prompt templates.
- Review output filenames and `review-merge.reads` are derived automatically and stay consistent with the reviewer list.

---

## Suggested Files to Update
- `prompts/tf.md`
- `prompts/tf-followups.md` (new command)
- `config/settings.json`
- `bin/tf`
- Agent files (`review-merge.md`, `fixer.md`, `closer.md`) where needed for new artifacts

---

## Open Questions
- Confirm follow‑up ticket tag name (default: `followup`)?
- Should Quality Gate be on by default or opt‑in (`workflow.enableQualityGate`)?
- Should `summary.json` also include review excerpts/links to artifacts?
