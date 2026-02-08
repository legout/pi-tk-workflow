# Review (Spec Audit): pt-hstd

## Overall Assessment
The implementation correctly adds subprocess timeout handling with safe termination for the `pi run` subprocess in Ralph's serial mode. All acceptance criteria are satisfied: timeout with SIGTERM/SIGKILL, distinct return code (-1) for timeout detection, and all output capture modes remain functional. The implementation prevents zombie processes by always calling `proc.wait()` after termination signals. The scope is correctly limited to serial mode (MVP), as confirmed by related ticket pt-hfqc.

## Critical
No critical issues found.

## Major
No major issues found.

## Minor
- `tf_cli/ralph.py:322` - The final `proc.wait()` call after `proc.kill()` (line 322) is not wrapped in exception handling. While this is unlikely to cause issues in practice (SIGKILL terminates immediately), wrapping it in a try-except block would improve robustness against edge cases like ChildProcessError if the process has already been reaped.

## Warnings
- `tf_cli/ralph.py:1615-1620` - Parallel mode does NOT use `_run_with_timeout()` and therefore has no timeout protection. This is acceptable for MVP per pt-hfqc ("MVP applies to serial mode; parallel behavior must remain functional (may disable retries with a warning)"), but parallel mode will need timeout support in a future ticket to ensure stuck tickets can be terminated in parallel execution.

## Suggestions
- Consider adding automated tests for timeout behavior (e.g., using `sleep` commands to trigger timeouts) to verify zombie process prevention and correct return code handling, similar to the manual tests documented in implementation.md.
- Consider logging the termination method used (SIGTERM vs SIGKILL) to aid debugging of timeout behavior.
- Consider making the 5-second grace period for SIGTERM configurable if different workloads require different cleanup times.

## Positive Notes
- `_run_with_timeout()` (lines 275-325) correctly implements the two-phase termination sequence (SIGTERM with 5-second grace, then SIGKILL)
- `proc.wait()` is called after both `proc.terminate()` and `proc.kill()` to prevent zombie processes
- Return code -1 consistently indicates timeout across all code paths, enabling clear restart logic
- All output capture modes (inherit, file, discard, JSON capture) correctly use `_run_with_timeout()`
- Restart loop in `ralph_run()` (lines 1218-1245) correctly distinguishes timeout (rc == -1) from other failures
- Timeout is correctly calculated from milliseconds to seconds with proper handling of 0 = no timeout
- Logging clearly indicates timeout threshold when configured
- Implementation is well-documented with docstrings explaining the termination sequence

## Summary Statistics
- Critical: 0
- Major: 0
- Minor: 1
- Warnings: 1
- Suggestions: 3

## Spec Coverage
- Spec/plan sources consulted:
  - Ticket pt-hstd (acceptance criteria, constraints, context)
  - Ticket pt-4qvw (defines timeout/restart configuration surface, confirms `-1` return code)
  - Ticket pt-hfqc (confirms MVP scope is serial mode only)
  - Seed: seed-add-ralph-loop-timeout-restarts (vision, constraints, success criteria)
  - Implementation.md (design decisions, test notes)
  - Research.md (problem analysis, solution approach)
- Missing specs: none
