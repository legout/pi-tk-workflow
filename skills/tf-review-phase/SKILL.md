---
name: tf-review-phase
description: Review phase orchestrator for TF workflow. Runs parallel reviewer subagents and merges results.
---

# TF Review Phase Skill

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

1. Read previous phase artifacts:
   - `{artifactDir}/implementation.md`
   - `{artifactDir}/files_changed.txt`
2. Load retry state (if escalation enabled) for `reviewer-second-opinion` model override.

### Step 2: Determine Reviewers

From `.tf/config/settings.json`:
- Use `workflow.enableReviewers` when set.
- Default: `reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`.
- If empty list, write a stub review and return.

### Step 3: Resolve Repo Root

```bash
git rev-parse --show-toplevel
```

### Step 4: Execute Parallel Subagents

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

### Step 5: Merge Reviews (reuse merge agent)

Delegate consolidation to the existing merge agent:

```json
{
  "agent": "review-merge",
  "task": "{ticket}",
  "agentScope": "project"
}
```

The merge agent reads reviewer outputs and writes consolidated `{artifactDir}/review.md`.

## Output Artifacts

- `{artifactDir}/review.md`
- reviewer outputs preserved in artifact dir

## Error Handling

- If one reviewer fails/times out, continue with available outputs.
- If none run, write a stub consolidated review.
