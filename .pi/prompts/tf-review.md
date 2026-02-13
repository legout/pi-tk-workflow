---
description: Review phase for TF workflow - run parallel reviewers and merge results [tf-review]
model: openai-codex/gpt-5.3-codex
thinking: high
skill: tf-review
---

# /tf-review

Execute the Review phase for TF workflow ticket implementation. Uses pi-subagents for parallel reviewer fan-out and merge.

## Usage

```
/tf-review <ticket-id>
```

## Arguments

- `<ticket-id>` - The ticket to review (e.g., `pt-1234`)

## Execution

Follow the **Parallel Reviews** and **Merge Reviews** procedures from tf-workflow skill:

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
3. **Load retry state** to get `escalatedModels` for reviewer-second-opinion
4. **Get ticket details**: `tk show {ticket}`

### Step 2: Determine Reviewers

From config (`.tf/config/settings.json`):
- If `workflow.enableReviewers` is set, use that list
- Default: `reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`

### Step 3: Resolve Repo Root

```bash
git rev-parse --show-toplevel
```

### Step 4: Execute Parallel Subagents

Run from repo root so `src/...` and `tk show` work:

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

**Timeout and failure handling:**
- Set a reasonable timeout for each reviewer (e.g., 5 minutes)
- If a reviewer times out or fails, continue with available results
- Write a partial review stub for failed reviewers with "Review failed" in Critical
- Merge will handle missing reviews gracefully

Each reviewer uses a different meta-model from config:
- `reviewer-general` → `metaModels.review-general.model`
- `reviewer-spec-audit` → `metaModels.review-spec.model`
- `reviewer-second-opinion` → `metaModels.review-secop.model` (or escalated model if set)

Ensure reviewers read `{artifactDir}/implementation.md`.

### Step 5: Handle Skipped Reviews

If no reviewer outputs exist (reviews disabled), write a stub `{artifactDir}/review.md` with "No reviews run" in Critical and zero counts.

### Step 6: Merge Reviews

1. **Read available review outputs** from:
   - `{artifactDir}/review-general.md`
   - `{artifactDir}/review-spec.md`
   - `{artifactDir}/review-second.md`

2. **Deduplicate issues**:
   - Match by file path + line number + description similarity
   - Use fuzzy matching: if descriptions are >70% similar, consider them duplicates
   - Keep highest severity when duplicates found
   - Note source reviewer(s) in the merged output

3. **Write consolidated `{artifactDir}/review.md`**:

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

## Output

**Always written:**
- `{artifactDir}/review.md` - Consolidated review

**Preserve from previous phases:**
- `{artifactDir}/research.md`
- `{artifactDir}/implementation.md`
- `{artifactDir}/ticket_id.txt`
- `{artifactDir}/files_changed.txt`
