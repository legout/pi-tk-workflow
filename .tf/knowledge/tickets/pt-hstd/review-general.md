# Review: pt-hstd

## Overall Assessment
The implementation correctly adds timeout handling with safe process termination for serial mode, addressing the zombie process issue. The `_run_with_timeout()` helper function is well-designed with proper SIGTERM/SIGKILL sequence and process reaping. However, parallel mode was not updated with the same timeout handling, creating an inconsistency.

## Critical (must fix)
No critical issues found.

## Major (should fix)
- `tf_cli/ralph.py:1618-1626` - Parallel mode does not use timeout handling. The code directly uses `subprocess.Popen()` without timeout, then calls `proc.wait()` without a timeout parameter (line 1629). This is inconsistent with serial mode which now has full timeout support. Parallel mode tickets can hang indefinitely without timeout enforcement.

## Minor (nice to fix)
- No unit tests for the `_run_with_timeout()` function. Testing would verify: normal completion returns correct code, timeout triggers termination sequence, processes are properly reaped (no zombies), and timeout_ms=0 disables timeout.
- `tf_cli/ralph.py:297-323` - Consider documenting the 5-second grace period for SIGTERM before SIGKILL. This is currently hardcoded; some users might want this configurable for long-running cleanup operations.

## Warnings (follow-up ticket)
- Consider adding timeout support to parallel mode in a follow-up ticket. This would require either: (a) calling `_run_with_timeout()` instead of direct `Popen` usage, or (b) refactoring parallel mode to use `run_ticket()` for consistency. Note that parallel mode launches multiple processes concurrently, so timeout handling needs to wait for all processes or implement per-process timeout monitoring.

## Suggestions (follow-up ticket)
- Consider logging when SIGTERM vs SIGKILL is used. This would help distinguish processes that exited gracefully from those that needed forceful termination, aiding in debugging hung processes.
- Consider making the grace period (5.0 seconds) configurable via a config option like `terminateGracePeriodSecs` in `.tf/ralph/config.json`.

## Positive Notes
- The `_run_with_timeout()` function correctly implements safe process termination with SIGTERM followed by SIGKILL, ensuring processes don't become zombies.
- The function always calls `proc.wait()` after both SIGTERM and SIGKILL, which correctly reaps child processes.
- Consistent return code (-1) for timeouts allows clean integration with restart logic in ticket pt-hfqc.
- All output modes (inherit, file, discard, JSON capture) are properly supported through the new helper function.
- The implementation correctly handles the case where `timeout_ms=0` disables timeout (timeout_secs=None).
- File handles are properly managed using `with` statements, ensuring cleanup even if timeout occurs.

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 2
- Warnings: 1
- Suggestions: 2
