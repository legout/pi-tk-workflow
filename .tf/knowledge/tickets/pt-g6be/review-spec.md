# Review (Spec Audit): pt-g6be

## Overall Assessment
The implementation fully satisfies the ticket requirements. The ready/blocked counts (`R:<n> B:<n>`) are correctly displayed in normal Ralph logging on both ticket start and ticket finish, with updated counts after completion. Errors remain prominently displayed through the existing error logging mechanism.

## Critical (must fix)
No issues found.

## Major (should fix)
No issues found.

## Minor (nice to fix)
- `tests/test_logger.py` and `tests/test_ralph_logging.py` - Test coverage gap: existing tests for `log_ticket_start()` and `log_ticket_complete()` do not test the `queue_state` parameter. Tests pass without verifying the R:/B:/done: format appears in output.

## Warnings (follow-up ticket)
- `tf/ralph.py:1600-1620` - Queue state is recomputed after ticket completion with `running=set()` (empty), but if multiple tickets are running in parallel mode, this would not reflect other in-flight tickets. Currently only serial mode passes queue_state to logging.
- `tf/ralph.py:1700+` (parallel mode) - Queue state is not passed to `log_ticket_start()` or `log_ticket_complete()` in parallel mode. The feature is only implemented for serial mode, which matches the ticket scope but should be documented as a limitation.

## Suggestions (follow-up ticket)
- `tf/ralph/queue_state.py` - Consider adding unit tests specifically for `QueueStateSnapshot` invariant validation and format methods (`__str__`, `to_log_format()`). No dedicated test file exists for this module.

## Positive Notes
- Requirements correctly implemented: `log_ticket_start()` and `log_ticket_complete()` in `tf/logger.py` both accept `queue_state` parameter and format output using `to_log_format()` method.
- Format matches spec: `R:3 B:2 done:4/10` format is used in logs (via `to_log_format()`), while progress display uses human-readable `R:3 B:2 (done 4/10)` format (via `__str__`).
- Queue state is correctly recomputed after ticket completion to reflect updated counts (completed ticket moved to done).
- Non-TTY output remains clean with no control characters (verified in `ProgressDisplay._draw()`).
- Error logging is unchanged and remains prominent (errors logged via `log_error_summary()` at ERROR level).
- Queue state computation avoids expensive recomputation by using in-memory scheduler state (pending/running/completed sets).

## Summary Statistics
- Critical: 0
- Major: 0
- Minor: 1
- Warnings: 2
- Suggestions: 1

## Spec Coverage
- Spec/plan sources consulted:
  - `.tf/knowledge/topics/seed-show-ready-and-blocked-ticket-count/seed.md` (root seed)
  - `.tf/knowledge/topics/plan-ready-blocked-counts-ralph/plan.md` (implementation plan)
  - `tf/ralph.py` (serial mode implementation)
  - `tf/logger.py` (logging methods)
  - `tf/ralph/queue_state.py` (queue state computation)
- Missing specs: none
