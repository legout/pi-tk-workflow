---
name: tf-review
description: Review phase for TF workflow - parallel reviewers and merge. Use after implementation to get multi-perspective code review.
---

# TF Review Skill

Review phase for the IRF (Implement → Review → Fix → Close) workflow. Runs parallel reviewers and merges results.

## When to Use This Skill

- After implementation phase completes
- When gathering multi-perspective code review
- Before fix phase

## Prerequisites

- Implementation phase completed
- `{artifactDir}/implementation.md` exists
- `pi-subagents` extension available

## Procedure

### Step 1: Load Context

1. **Read previous phase artifacts**:
   - `{artifactDir}/implementation.md` - What was implemented
   - `{artifactDir}/files_changed.txt` - Files to review

2. **Load retry state** (if escalation enabled):
   - Get `escalatedModels.reviewerSecondOpinion` for second-opinion reviewer

### Step 2: Determine Reviewers

From config (`.tf/config/settings.json`):
- If `workflow.enableReviewers` is set, use that list
- Default: `reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`
- If empty list, skip reviews and write stub

### Step 3: Resolve Repo Root

```bash
git rev-parse --show-toplevel
```

### Step 4: Execute Parallel Subagents

Run from repo root:

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

Each reviewer uses a different model from config:
- `reviewer-general` → `metaModels.review-general.model`
- `reviewer-spec-audit` → `metaModels.review-spec.model`
- `reviewer-second-opinion` → `metaModels.review-secop.model` (or escalated model)

### Step 5: Handle Skipped Reviews

If no reviewer outputs exist:
- Write stub `{artifactDir}/review.md` with "No reviews run" in Critical and zero counts
- Return early

### Step 6: Merge Reviews

1. **Read available review outputs**:
   - `{artifactDir}/review-general.md`
   - `{artifactDir}/review-spec.md`
   - `{artifactDir}/review-second.md`

2. **Deduplicate issues**:
   - Match by file path + line number + description similarity
   - Use fuzzy matching: if descriptions >70% similar, consider duplicates
   - Keep highest severity when duplicates found
   - Note source reviewer(s)

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

## Reviewer Focus Areas

| Reviewer | Focus |
|----------|-------|
| reviewer-general | Logic correctness, security, error handling, performance, test gaps |
| reviewer-spec-audit | Ticket/plan compliance, acceptance criteria, specification alignment |
| reviewer-second-opinion | Non-obvious issues, alternative approaches, edge cases |

## Output Artifacts

| File | Description |
|------|-------------|
| `{artifactDir}/review.md` | Consolidated review |
| `{artifactDir}/review-general.md` | General review (from subagent) |
| `{artifactDir}/review-spec.md` | Spec audit (from subagent) |
| `{artifactDir}/review-second.md` | Second opinion (from subagent) |

## Error Handling

- If reviewer times out, continue with available results
- Write partial stub for failed reviewers
- Merge handles missing reviews gracefully
