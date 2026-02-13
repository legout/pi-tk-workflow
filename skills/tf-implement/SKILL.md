---
name: tf-implement
description: Implementation phase for TF workflow - code changes with quality checks. Use after research to implement the ticket requirements.
---

# TF Implement Skill

Implementation phase for the IRF (Implement → Review → Fix → Close) workflow.

## When to Use This Skill

- After research phase completes
- When implementing code changes for a ticket
- Before parallel reviews

## Prerequisites

- Research phase completed (or skipped)
- `{artifactDir}/research.md` exists (may be stub)
- `tk show {ticket}` succeeds

## Procedure

### Step 1: Load Context

1. **Read previous phase artifacts**:
   - `{artifactDir}/research.md` - Research findings
   - `{artifactDir}/ticket_id.txt` - Ticket ID

2. **Get ticket details**: `tk show {ticket}`

3. **Load retry state** (if escalation enabled):
   - Check `{artifactDir}/retry-state.json`
   - Get `attemptNumber` and `escalatedModels.worker`

### Step 2: Explore Codebase

1. Use `find` and `grep` to locate relevant files
2. Follow existing patterns from AGENTS.md
3. Review related code for consistency

### Step 3: Implement Changes

1. **Make focused, single-responsibility changes**
2. **Track changed files** for `files_changed.txt`
3. **Follow project patterns** exactly

### Step 4: Run Quality Checks

Load checkers from config (`.tf/config/settings.json`):

| Language | Lint | Format | TypeCheck |
|----------|------|--------|-----------|
| Python | `ruff check {files} --fix` | `ruff format {files}` | `ty check .` |
| TypeScript | `eslint {files} --fix` | `prettier --write {files}` | `tsc --noEmit` |
| Rust | `cargo clippy --fix` | `cargo fmt` | `cargo check` |

### Step 5: Run Tests

```bash
# Python
pytest tests/ -v

# TypeScript
npm test

# Rust
cargo test
```

### Step 6: Write implementation.md

Write to `{artifactDir}/implementation.md`:

```markdown
# Implementation: {ticket-id}

## Summary
Brief description of changes

## Retry Context
- Attempt: {attemptNumber}
- Escalated Models: worker={escalatedModels.worker or 'base'}

## Files Changed
- `path/to/file.ts` - what changed

## Key Decisions
- Why approach X was chosen

## Tests Run
- Commands and results

## Verification
- How to verify it works
```

### Step 7: Track Changed Files

```bash
tf track {file1} {file2} --file {artifactDir}/files_changed.txt
```

## Output Artifacts

| File | Description |
|------|-------------|
| `{artifactDir}/implementation.md` | Implementation summary |
| `{artifactDir}/files_changed.txt` | Tracked changed files |
| `{artifactDir}/ticket_id.txt` | Ticket ID |

## Error Handling

- If quality checks fail, fix issues before proceeding
- If tests fail, document in implementation.md
- Continue workflow even if tests have known failures
