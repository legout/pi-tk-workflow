# Research: pt-uo6h

## Status
Research complete. Implementation approach determined from codebase analysis.

## Context Reviewed
- `tk show pt-uo6h` - ticket requirements
- Seed topic: `seed-add-more-logging-to-ralph-loop` - context for Ralph logging
- `tf_cli/logger.py` - RalphLogger implementation (pt-rvpi)
- `tf_cli/ralph_new.py` - Ralph loop implementation
- `tests/test_ralph_logging.py` - test patterns
- Pi CLI help - `--mode json` option confirmed

## Key Findings

### Pi JSON Mode
Pi supports `--mode json` which emits a JSONL event stream. This can be combined with `-p` (non-interactive mode).

Example: `pi -p --mode json "/tf TICKET-123"`

### Ralph Execution Points
Two places where Pi is executed:
1. `run_ticket()` function (line ~218) - serial mode
2. Parallel mode execution (line ~1024) - uses subprocess.Popen

### Existing Config Structure
DEFAULTS dict in ralph_new.py contains:
- `logLevel` - for verbosity control
- `sessionDir` - for session files
- Similar pattern can be used for `captureJson`

### Logger Pattern
The RalphLogger from pt-rvpi provides structured logging with:
- Context fields (ticket, mode, iteration)
- Redaction for sensitive data
- Methods like `log_command_executed()`

## Implementation Plan
1. Add `captureJson` to DEFAULTS (default: False)
2. Add `--capture-json` CLI flag and `RALPH_CAPTURE_JSON` env var
3. Ensure `.tf/ralph/logs/` directory exists
4. Modify `run_ticket()` to capture JSONL when enabled
5. Modify parallel mode execution similarly
6. Add log message indicating JSONL location
7. Write tests for the new feature

## Sources
- Pi CLI: `pi --help` shows `--mode <mode>` option
- Ralph implementation: `tf_cli/ralph_new.py`
- Logger implementation: `tf_cli/logger.py`
