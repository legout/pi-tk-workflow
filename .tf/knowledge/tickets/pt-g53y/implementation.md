# Implementation: pt-g53y

## Summary
Implemented the v1 JSON schema for planning sessions and an atomic read/write store module (`tf_cli/session_store.py`). The store provides idempotent operations for managing planning session state files under the TF knowledge directory.

## Files Changed
- `tf_cli/session_store.py` (new) - Complete session store implementation

## Key Decisions

### Schema Design (v1)
Based on the approved plan document, the session schema includes:
- `schema_version: 1` - For future migration support
- `session_id` - Format: `{seed_id}@{YYYY-MM-DDTHH-MM-SSZ}` (filename-safe)
- `state` - One of: "active", "completed", "archived"
- `root_seed` - The seed topic ID this session belongs to
- `spikes` - List of attached spike IDs
- `plan` - Single plan ID (or null)
- `backlog` - Object with topic, backlog_md path, and tickets list
- `created`, `updated`, `completed_at` - ISO 8601 timestamps

### Atomic Write Implementation
Used `tempfile.mkstemp()` + `os.rename()` pattern:
- Creates temp file in same directory as target
- Writes JSON atomically
- Renames to final path (atomic on POSIX systems)
- Cleans up temp file on failure

### Idempotency Guarantees
- `add_spike_to_session()` - Checks for existing entry before adding
- `set_backlog_for_session()` - Deduplicates ticket IDs while preserving order
- Safe to call multiple times without creating duplicates

### Environment Support
- `TF_KNOWLEDGE_DIR` environment variable overrides default path
- Falls back to `{cwd}/.tf/knowledge`
- All functions accept optional `knowledge_dir` parameter

## API Surface

### Session Lifecycle
- `create_session(seed_id)` - Create new session dict
- `save_active_session(session)` - Write to `.active-planning.json`
- `load_active_session()` - Read active session (validates schema_version)
- `clear_active_session()` - Remove active session file
- `archive_session(session)` - Write to `sessions/{session_id}.json`
- `archive_and_create_session(seed_id)` - Archive + switch atomically

### Query Operations
- `list_archived_sessions(seed_id?)` - List sessions, optionally filtered
- `load_archived_session(session_id)` - Load specific archived session
- `find_latest_session_for_seed(seed_id)` - Get most recent for seed
- `get_active_session_info()` - Get display-friendly summary

### Session Updates (Idempotent)
- `add_spike_to_session(spike_id)` - Attach spike to active session
- `set_plan_for_session(plan_id)` - Set plan for active session
- `set_backlog_for_session(...)` - Complete and deactivate session

### Utilities
- `generate_session_id(seed_id)` - Create filename-safe session ID
- `parse_session_id(session_id)` - Parse into (seed_id, timestamp)

## Tests Run
- Syntax check: `python -m py_compile` ✓
- Import test: All exports load correctly ✓
- Functional tests: All core operations verified ✓
- Existing test suite: 248 tests passed ✓

## Verification
To verify the implementation:

```python
from tf_cli.session_store import create_session, save_active_session, load_active_session
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    kd = Path(tmp)
    session = create_session("my-seed", kd)
    save_active_session(session, kd)
    loaded = load_active_session(kd)
    assert loaded["schema_version"] == 1
    assert loaded["root_seed"] == "my-seed"
    print("Session store working correctly!")
```

## Next Steps for Ticket pt-cqbn
The blocking ticket `pt-cqbn` (Implement /tf-seed session activation + archive+switch + --no-session) can now use:
- `archive_and_create_session(seed_id)` for `/tf-seed` default behavior
- `clear_active_session()` for `/tf-seed --no-session`
- `list_archived_sessions()` for `/tf-seed --sessions`
- `resume_session(session_id)` for `/tf-seed --resume`
- `get_active_session_info()` for `/tf-seed --active`
