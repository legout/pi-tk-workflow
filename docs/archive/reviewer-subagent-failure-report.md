# Reviewer Subagent Failure Analysis (mme-359d)

## Executive Summary
Reviewer subagents exited with **code 1** because their **working directory (cwd)** was set to the **ticket artifact directory** (`.tf/knowledge/tickets/<ticket-id>`), while reviewer prompts assume **repo-root relative paths** (e.g., `src/...`) and `tk show <ticket-id>` expects repo root to locate `.tickets/`. This mismatch caused read errors (`ENOENT`) and `tk` failures despite the reviewers producing valid output text.

**Root cause:** Configuration mismatch between **tf-workflow skill** (reviewer cwd = artifactDir) and **reviewer agent prompts** (assume repo-root paths).

**Not a model/skill issue:** The reviewers executed normally and produced review text; the runs were marked failed due to tool errors.

---

## Symptoms Observed (from subagent artifacts)

### reviewer-general
- **Error:**
  - `read failed (exit 1): ENOENT .../.tf/knowledge/src/mms2_mdb_exporter/cli.py`
- **Implication:** `read src/...` resolved under `.tf/knowledge/tickets/<ticket>` instead of repo root.

### reviewer-second-opinion
- **Error:**
  - `read failed (exit 1): ENOENT .../.tf/knowledge/src/mms2_mdb_exporter/cli.py`
- **Implication:** same as above.

### reviewer-spec-audit
- **Error:**
  - `bash failed (exit 1): Error: ticket 'mme-359d' not found`
- **Implication:** `tk show` executed outside repo root (cannot resolve `.tickets`).

---

## Root Cause Analysis

### 1) tf-workflow skill sets reviewer cwd to artifactDir
**File:** `~/.pi/agent/skills/tf-workflow/SKILL.md`
```json
{
  "tasks": [
    {"agent": "reviewer-general", "task": "{ticket}", "cwd": "{artifactDir}"},
    {"agent": "reviewer-spec-audit", "task": "{ticket}", "cwd": "{artifactDir}"},
    {"agent": "reviewer-second-opinion", "task": "{ticket}", "cwd": "{artifactDir}"}
  ]
}
```

### 2) Reviewer agents assume repo-root paths
**Files:**
- `<project>/.pi/agents/reviewer-general.md`
- `<project>/.pi/agents/reviewer-second-opinion.md`

These agents instruct the model to “read actual files mentioned in implementation” (e.g., `src/...`), which only works if cwd is the repo root.

### 3) Spec auditor assumes `tk show` works from cwd
**File:** `<project>/.pi/agents/reviewer-spec-audit.md`

It explicitly runs `tk show <ticket-id>`, which requires repo root so `.tickets/` can be located.

---

## Fixing Guidance (Recommended Approach)

### ✅ Preferred Fix: Run reviewers from repo root
This keeps all reviewer prompts intact and avoids path confusion.

**Change:** update tf-workflow review step to use repo root as `cwd`.

#### Implementation Steps
1. **Resolve repo root** at runtime (in tf-workflow implementation):
   - `git rev-parse --show-toplevel` (fallback to current cwd if not a git repo)

2. **Launch subagents with cwd=repo root**, but still **read/write** artifacts in `{artifactDir}`.

3. **Ensure reviewers can find implementation.md** by passing it explicitly (absolute path) or by using `reads` with full path.

#### Example Patch (conceptual)
```json
{
  "tasks": [
    {
      "agent": "reviewer-general",
      "task": "{ticket}",
      "cwd": "{repoRoot}",
      "reads": ["{artifactDir}/implementation.md"]
    },
    {
      "agent": "reviewer-spec-audit",
      "task": "{ticket}",
      "cwd": "{repoRoot}",
      "reads": ["{artifactDir}/implementation.md"]
    },
    {
      "agent": "reviewer-second-opinion",
      "task": "{ticket}",
      "cwd": "{repoRoot}",
      "reads": ["{artifactDir}/implementation.md"]
    }
  ]
}
```

---

## Alternative Fixes (if you cannot change reviewer cwd)

### Option B: Modify reviewer agents to resolve repo root internally
Add a standard pre-step in reviewer prompts:

1. Run `git rev-parse --show-toplevel` to get repo root
2. When reading `src/...` paths, prefix with repo root
3. When invoking `tk show`, run it from repo root (via `bash -c "cd <root> && tk show <ticket>"`)

**Downside:** More complex prompt logic; reviewers must handle path rewriting.

### Option C: Change implementation.md to include absolute paths
Have the main workflow agent write absolute file paths in `implementation.md`. This is intrusive and inconsistent with existing conventions.

---

## Validation Steps
After applying the preferred fix:

1. Run `/tf <ticket>`
2. Confirm reviewers succeed (exitCode 0) in `~/.pi/agent/sessions/.../subagent-artifacts/` meta files
3. Verify:
   - `reviewer-general` can read `src/...` with no ENOENT
   - `reviewer-spec-audit` can `tk show` successfully
4. Ensure review outputs are written to `{artifactDir}`

---

## Recommendation to pi-ticketflow

**Implement fix in ticketflow’s review orchestration layer**:
- Compute repo root once
- Run reviewer subagents from repo root
- Pass `{artifactDir}/implementation.md` as a read
- Keep review outputs stored in `{artifactDir}`

This resolves the path mismatch without changing reviewer prompts or skills and preserves existing review output formats.

---

## Appendix: Evidence Links
- Subagent artifacts:
  - `ed451d2a_reviewer-general_0_meta.json`
  - `ed451d2a_reviewer-second-opinion_2_meta.json`
  - `ed451d2a_reviewer-spec-audit_1_meta.json`

These show failures caused by `read` and `tk show` executed from the artifact directory.
