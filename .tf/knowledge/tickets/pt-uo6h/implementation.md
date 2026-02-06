# Implementation: pt-uo6h

## Summary
Added optional Pi JSON mode capture for deeper debugging in Ralph loop. When enabled, Pi runs with `--mode json` and the JSONL output is captured to `.tf/ralph/logs/<ticket>.jsonl`.

## Files Changed

### 1. `tf_cli/ralph_new.py`
- Added `captureJson` to DEFAULTS (default: False)
- Updated `usage()` to document `--capture-json` flag and `RALPH_CAPTURE_JSON` env var
- Updated `parse_run_args()` to parse `--capture-json` flag
- Updated `parse_start_args()` to parse `--capture-json` flag
- Updated `run_ticket()` signature and implementation to support JSON capture:
  - Added `capture_json` and `logs_dir` parameters
  - When enabled, runs Pi with `--mode json`
  - Captures output to JSONL file
  - Logs JSONL path after execution
- Updated `ralph_run()` to resolve `capture_json` from CLI flag, env var, or config
- Updated `ralph_start()` to:
  - Resolve `capture_json` from CLI flag, env var, or config
  - Create logs directory when enabled
  - Pass `capture_json` and `logs_dir` to serial mode `run_ticket()`
  - Handle JSON capture in parallel mode with per-worktree log files

## Key Decisions

1. **Priority order**: CLI flag > env var > config file > default
   - Allows quick experimentation via CLI without config changes
   - Env var enables CI/CD workflows to enable capture globally

2. **Log location**: `.tf/ralph/logs/<ticket>.jsonl`
   - Centralized location for all Ralph-related logs
   - Predictable path for post-mortem analysis
   - In parallel mode, stored in worktree at `.tf/ralph/logs/<ticket>.jsonl`

3. **Opt-in behavior**: Default is False
   - JSONL may contain file paths or snippets (security consideration)
   - Only enabled when explicitly requested

4. **Mode indicator in logs**: When enabled, log shows `pi -p --mode json "..."`
   - Makes it clear when JSON capture is active
   - Dry-run mode also shows the flag

## Tests

Created `tests/test_json_capture.py` with comprehensive tests for:
- CLI flag parsing (--capture-json)
- Environment variable handling (RALPH_CAPTURE_JSON)
- Config file integration
- Priority resolution (CLI > env > config)
- Logs directory creation
- Dry-run mode indication

## Verification

```bash
# Test the feature
tf ralph run TICKET-123 --capture-json --dry-run

# Or use env var
RALPH_CAPTURE_JSON=1 tf ralph run TICKET-123 --dry-run
```

## Acceptance Criteria

- [x] A flag/env toggle enables JSON mode capture (default off)
- [x] JSONL is written to a predictable location (`.tf/ralph/logs/<ticket>.jsonl`)
- [x] Log output indicates where the JSONL trace was written
