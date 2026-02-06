# Close Summary: pt-uo6h

## Status
CLOSED - Implementation complete and tested

## Summary
Implemented optional Pi JSON mode capture for deeper debugging in Ralph loop. The feature is opt-in via `--capture-json` flag, `RALPH_CAPTURE_JSON` env var, or config file setting.

## Changes Committed
- `tf_cli/ralph_new.py` - Core implementation
- `tests/test_json_capture.py` - 17 comprehensive tests
- `.tf/knowledge/tickets/pt-uo6h/` - Artifacts (research.md, implementation.md, etc.)

## Acceptance Criteria Verification
- [x] A flag/env toggle enables JSON mode capture (default off)
  - CLI: `--capture-json`
  - Env: `RALPH_CAPTURE_JSON=1`
  - Config: `captureJson: true`
  - Priority: CLI > env > config > default(False)

- [x] JSONL is written to a predictable location
  - Serial mode: `.tf/ralph/logs/<ticket>.jsonl`
  - Parallel mode: `<worktree>/.tf/ralph/logs/<ticket>.jsonl`

- [x] Log output indicates where the JSONL trace was written
  - Logger outputs: `JSONL trace written to: <path>`

## Test Results
- 17 new tests in `test_json_capture.py` - all passing
- 495 total tests in suite - all passing

## Usage Examples
```bash
# Via CLI flag
tf ralph run TICKET-123 --capture-json

# Via env var
RALPH_CAPTURE_JSON=1 tf ralph start

# Via config (ralph config.json)
{"captureJson": true}
```

## Notes
- JSON capture is experimental as noted in the ticket
- JSONL may contain file paths or snippets (security consideration)
- Feature is fully backward compatible (default off)
