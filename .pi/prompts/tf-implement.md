---
description: Implementation phase for TF workflow - implement ticket changes [tf-implement]
model: minimax/MiniMax-M2.5
thinking: high
skill: tf-implement
---

# /tf-implement

Execute the Implementation phase for TF workflow ticket implementation.

## Usage

```
/tf-implement <ticket-id> [--retry-reset]
```

## Arguments

- `<ticket-id>` - The ticket to implement (e.g., `pt-1234`)

## Flags

| Flag | Description |
|------|-------------|
| `--retry-reset` | Force a fresh retry attempt (renames existing retry-state.json) |

## Execution

Follow the **Implement** procedure from tf-workflow skill:

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.tf/ralph/AGENTS.md`
   - If referenced, read `.tf/ralph/AGENTS.md` for lessons learned

2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
   - `mkdir -p {artifactDir}`

3. **Handle retry reset flag** (if `--retry-reset` provided)
   - If `{artifactDir}/retry-state.json` exists, rename to `retry-state.json.bak.{timestamp}.{random_suffix}`
   - Use ISO 8601 timestamp format (e.g., `2026-02-13T15:00:00Z`) plus a random suffix to prevent overwrites
   - Log: "Retry state reset for {ticket-id}"

4. **Load retry state**:
   - Check for `{artifactDir}/retry-state.json`
   - If exists and last attempt was BLOCKED → increment retry count
   - Store `attemptNumber` (1-indexed) and `escalatedModels` for use in subsequent phases

5. **Read knowledge base**
   - Prefer `{artifactDir}/research.md` for ticket-specific research

6. **Get ticket details**
   - Run `tk show {ticket}` to get full ticket description

### Step 2: Explore Codebase

- Use `find` and `grep` to locate relevant files
- Follow existing patterns from AGENTS.md

### Step 3: Implement Changes

1. Make focused, single-responsibility changes
2. Track changed files in memory
3. Follow project patterns exactly

### Step 4: Run Quality Checks

1. Load checkers from config (`.tf/config/settings.json`)
2. Run lint/format on changed files
3. Run typecheck on project
4. Fix any issues found

### Step 5: Run Tests

- Execute relevant tests
- Verify implementation

### Step 6: Write implementation.md

Write to `{artifactDir}/implementation.md`:

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

Also write:
- `{artifactDir}/ticket_id.txt` containing only the ticket ID
- `{artifactDir}/files_changed.txt` with list of changed files (use atomic write: write to temp file then rename)

## Output

**Always written:**
- `{artifactDir}/implementation.md` - Implementation summary
- `{artifactDir}/ticket_id.txt` - Ticket ID
- `{artifactDir}/files_changed.txt` - Tracked changed files
