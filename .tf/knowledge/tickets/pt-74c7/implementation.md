# Implementation: pt-74c7

## Summary
Implemented `tf kb archive <topic-id>` and `tf kb restore <topic-id>` commands as specified in the plan document.

## Files Changed
- `tf_cli/kb_cli.py` - Added `cmd_archive()` and `cmd_restore()` functions, updated usage and main dispatch

## Implementation Details

### cmd_archive()
- Moves topic directory from `.tf/knowledge/topics/<id>/` to `.tf/knowledge/archive/topics/<id>/`
- Removes topic entry from `index.json` using atomic read/write helpers
- Creates `archive.md` in the archived topic directory with timestamp and optional reason
- **Idempotent**: If topic is already archived, prints message and returns success (exit 0)
- Returns exit 1 on errors (topic not found, move failed)

### cmd_restore()
- Moves topic directory from `.tf/knowledge/archive/topics/<id>/` back to `.tf/knowledge/topics/<id>/`
- Re-adds topic entry to `index.json` with minimal metadata (extracts title from first markdown heading if available)
- **Idempotent**: If topic is already active, prints message and returns success (exit 0)
- Returns exit 1 on errors (topic not in archive, move failed)

### CLI Interface
```
tf kb archive <topic-id> [--reason TEXT] [--knowledge-dir <path>]
tf kb restore <topic-id> [--knowledge-dir <path>]
```

## Key Decisions
- Used existing `atomic_write_index()` and `atomic_read_index()` helpers for safe index.json manipulation
- Archive record includes ISO timestamp and optional user-provided reason
- On restore, title is extracted from first `# ` heading found in overview.md, plan.md, or sources.md
- Both operations use `Path.rename()` for atomic directory moves

## Tests Run
- All 33 existing `test_kb_helpers.py` tests pass
- Manual testing confirmed:
  - Archive moves directory and updates index
  - Restore moves directory back and updates index
  - Idempotency works for both operations
  - Error handling works for missing topics

## Verification
```bash
# Archive a topic
python -m tf_cli.cli kb archive seed-add-versioning --reason "No longer needed"

# Restore a topic
python -m tf_cli.cli kb restore seed-add-versioning

# Both are idempotent - running twice produces expected messages
```
