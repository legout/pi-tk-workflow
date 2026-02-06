# Implementation: pt-9zhm

## Summary
Add session UX flags to `/tf-seed`: `--active`, `--sessions`, and `--resume`.

## Changes Made

### 1. Created `tf_cli/seed_cli.py` (new file)
A new CLI module that implements the three session UX commands:

- **`--active`**: Prints current active session info or "none"
  - Shows session_id, root seed, state, spikes count, plan/backlog status
  
- **`--sessions [seed-id]`**: Lists archived sessions
  - Without argument: lists all archived sessions
  - With seed-id: filters to sessions for that seed
  - Shows creation time, update time, progress summary
  
- **`--resume <id>`**: Resumes an archived session
  - Accepts either a seed-id (resumes latest session for that seed)
  - Or a full session-id for specific session
  - Archives current active session before resuming

### 2. Updated `tf_cli/cli.py`
Added routing for the `seed` subcommand:
```python
if argv and argv[0] == "seed":
    from . import seed_cli
    return seed_cli.main(argv[1:])
```

### 3. Updated `scripts/tf_legacy.sh`
- Added `seed_cmd()` function that delegates to Python CLI
- Updated usage documentation with seed subcommands
- Added `seed` to the commands that pass options through
- Added case handler for `seed)` command

## Files Changed
- `tf_cli/seed_cli.py` (new - 194 lines)
- `tf_cli/cli.py` (modified - 4 lines added)
- `scripts/tf_legacy.sh` (modified - added seed_cmd function and case handler)

## Verification

Tested all three commands:

```bash
# Check active session
$ tf seed --active
none

# List all sessions
$ tf seed --sessions
All archived sessions:
  seed-test-session@2026-02-06T12-57-17Z
    root: seed-test-session
    ...
Total: 2 session(s)

# Resume a session
$ tf seed --resume seed-test-session
[tf] Resumed planning session: seed-test-session@2026-02-06T12-57-17Z (root: seed-test-session)
```

All acceptance criteria met:
- [x] `--active` prints the current active session or "none"
- [x] `--sessions` lists archived/completed session snapshots
- [x] `--sessions [seed-id]` supports optional seed-id filter
- [x] `--resume` reactivates the latest session for a seed-id
- [x] `--resume` works with specific session-id
- [x] Resuming archives the currently active session first
