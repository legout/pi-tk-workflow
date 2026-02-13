---
name: tf-workflow
description: Orchestrate the Implement → Review → Fix → Close workflow. Use as the main entry point skill that delegates to phase-specific skills.
---

# TF Workflow Skill

Orchestration skill for the IRF (Implement → Review → Fix → Close) cycle. This skill provides overview and coordination logic, while detailed procedures are in phase-specific skills.

## When to Use This Skill

- As the main entry point for `/tf` command
- When understanding the full workflow structure
- For flag handling and chain construction

## Phase Skills

Detailed procedures are in separate skills:

| Phase | Skill | Description |
|-------|-------|-------------|
| Research | `tf-research` | Gather context and knowledge |
| Implement | `tf-implement` | Code changes with quality checks |
| Review | `tf-review-phase` | Parallel reviewers and merge |
| Fix | `tf-fix` | Apply fixes from review feedback |
| Close | `tf-close` | Quality gate, commit, close ticket |

## Extension Requirements

| Extension | Purpose |
|-----------|---------|
| `pi-prompt-template-model` | Chain orchestration with per-phase model/skill |
| `pi-subagents` | Parallel reviews |

Install:
```bash
pi install npm:pi-prompt-template-model
pi install npm:pi-subagents
```

## Configuration

Read from `.tf/config/settings.json`:

| Config | Description |
|--------|-------------|
| `workflow.enableResearcher` | Whether research runs by default |
| `workflow.enableReviewers` | Which reviewers to run |
| `workflow.enableFixer` | Whether fix phase runs |
| `workflow.enableCloser` | Whether close phase runs |
| `workflow.enableQualityGate` | Enforce fail-on severities |
| `workflow.failOn` | Severities that block closing |
| `workflow.knowledgeDir` | Artifact directory base |

## Flag Handling

Parse flags to construct the appropriate chain:

| Flag | Chain Entry Point | Notes |
|------|-------------------|-------|
| (default) | `tf-research` | Full workflow |
| `--no-research` | `tf-implement` | Skip research |
| `--with-research` | `tf-research` | Force research |

Post-chain commands (run after chain completes with CLOSED status):

| Flag | Command |
|------|---------|
| `--create-followups` | `tf-followups` |
| `--simplify-tickets` | `simplify` |
| `--final-review-loop` | `review-start` |

## Deterministic Orchestration

`/tf` should delegate to Python tooling:

```bash
tf irf <ticket-id> [flags]
```

`tf irf` resolves flags/config and constructs the `/chain-prompts` command deterministically.

Equivalent chain forms:

```bash
# Default or --with-research
/chain-prompts tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close -- $@

# With --no-research
/chain-prompts tf-implement -> tf-review -> tf-fix -> tf-close -- $@
```

## Context Flow

Each phase writes artifacts to `{artifactDir}/`:

```
tf-research  → research.md, ticket_id.txt
tf-implement → implementation.md, files_changed.txt
tf-review    → review.md (consolidated)
tf-fix       → fixes.md
tf-close     → close-summary.md, chain-summary.md
```

Subsequent phases read artifacts from previous phases.

## Retry Escalation

When `workflow.escalation.enabled: true`:

| Attempt | Worker | Fixer | Reviewer-2nd-Op |
|---------|--------|-------|-----------------|
| 1 | Base | Base | Base |
| 2 | Base | Escalated | Base |
| 3+ | Escalated | Escalated | Escalated |

State persisted in `{artifactDir}/retry-state.json`.

## Error Handling

- Chain failure: Restore original model, stop
- Quality gate blocks: Write BLOCKED status, don't close ticket
- Reviewer timeout: Continue with available reviews
- Post-chain failure: Warn and continue (best-effort)

## Output Artifacts

| File | Phase | Description |
|------|-------|-------------|
| `research.md` | Research | Research findings |
| `implementation.md` | Implement | Implementation summary |
| `review.md` | Review | Consolidated review |
| `fixes.md` | Fix | Fixes applied |
| `close-summary.md` | Close | Final summary with status |
| `chain-summary.md` | Close | Artifact index |
| `files_changed.txt` | Implement | Tracked changed files |
| `ticket_id.txt` | Research | Ticket ID reference |
