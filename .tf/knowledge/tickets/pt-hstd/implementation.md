# Implementation: pt-hstd

## Summary
Implemented subprocess timeout handling with safe termination for the `pi run` subprocess in Ralph. The previous implementation used `subprocess.run()` which could leave zombie processes when timeouts occurred.

## Changes Made

### File: `tf_cli/ralph.py`

#### Added `_run_with_timeout()` helper function
- Uses `subprocess.Popen` for fine-grained process control
- Implements safe termination sequence:
  1. `proc.terminate()` - Send SIGTERM for graceful shutdown
  2. `proc.wait(timeout=5.0)` - Wait 5 seconds for graceful exit
  3. `proc.kill()` - Send SIGKILL if still running
  4. `proc.wait()` - Always reap the process to prevent zombies
- Returns `(-1, True)` on timeout for distinct error handling
- Returns `(return_code, False)` on normal completion

#### Refactored `run_ticket()` function
- Replaced all `subprocess.run()` calls with `_run_with_timeout()`
- Maintains support for all output modes:
  - `inherit` - Pass output through to terminal
  - `file` - Redirect output to log file
  - `discard` - Suppress output
  - JSON capture mode (with/without file output)
- Properly handles the timed_out flag and returns -1 for timeout

## Key Design Decisions

1. **Consistent return code -1 for timeout**: Regardless of whether SIGTERM or SIGKILL was used, timeout always returns -1. This allows the restart loop (ticket pt-hfqc) to distinguish timeouts from other failures.

2. **Graceful then forceful termination**: SIGTERM is tried first with a 5-second grace period, then SIGKILL if needed. This gives the subprocess a chance to clean up.

3. **Always reap processes**: `proc.wait()` is called after both SIGTERM and SIGKILL to ensure the child process is reaped and doesn't become a zombie.

4. **Backward compatibility**: All existing output capture modes continue to work exactly as before.

## Tests Performed

1. **Normal execution**: `echo hello` completes successfully with return code 0
2. **Timeout handling**: `sleep 10` with 0.5s timeout correctly returns -1 and timed_out=True
3. **No zombies verified**: After timeout, no sleep processes remain in process list

## Acceptance Criteria Status

- [x] When timeout is configured, the `pi` subprocess is terminated after the timeout (terminate/kill as needed)
- [x] Return code / error reason indicates timeout distinctly (returns -1 for timeout)
- [x] Output capture modes remain correct (`--pi-output=file/discard/inherit`, `--capture-json`)
- [x] Must not leave zombie processes (always wait after kill)

## Files Changed
- `tf_cli/ralph.py` - Added `_run_with_timeout()` helper and refactored `run_ticket()`
