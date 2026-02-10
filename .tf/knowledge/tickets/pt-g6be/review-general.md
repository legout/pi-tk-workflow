# Review: pt-g6be

## Overall Assessment
The implementation correctly adds ready/blocked counts to normal Ralph logging for ticket start and complete events. The code is well-structured with a dedicated `QueueStateSnapshot` dataclass and proper integration into the existing logger. However, there is no test coverage for the queue state logging functionality, and the failure path is inconsistent with the success path regarding queue state logging.

## Critical (must fix)
No issues found

## Major (should fix)
No issues found

## Minor (nice to fix)
- `tf/ralph.py:1622` - On ticket failure, `log_error_summary()` is called instead of `log_ticket_complete()`, which means the failure log line does not include the queue state (R:<n> B:<n> done:<n>/<n>). This is inconsistent with the success path and the acceptance criteria which states "On ticket finish log line includes updated counts" (finish includes both success and failure). Consider adding queue_state parameter to `log_error_summary()` or calling `log_ticket_complete()` with FAILED status before/after the error summary.

## Warnings (follow-up ticket)
- `tests/` - No tests exist for the queue state logging functionality (`QueueStateSnapshot`, `get_queue_state()`, or the queue_state parameter in logger methods). The implementation.md claims 121 tests passed, but none of them verify that queue state is actually included in log output. A follow-up ticket should add tests for:
  - `QueueStateSnapshot.to_log_format()` returns correct format
  - `get_queue_state()` computes counts correctly from scheduler state
  - `log_ticket_start()` includes queue state in output when provided
  - `log_ticket_complete()` includes queue state in output when provided
  - Queue state invariant validation (total equals sum of all states)

## Suggestions (follow-up ticket)
- `tf/logger.py:276-309` - The `log_ticket_start()` and `log_ticket_complete()` methods have duplicated logic for handling queue_state. Consider extracting a helper method to format the message with optional queue state suffix to reduce duplication.

## Positive Notes
- Clean separation of concerns with `QueueStateSnapshot` in its own module (`tf/ralph/queue_state.py`)
- Proper validation in `QueueStateSnapshot.__post_init__()` ensures data integrity
- Good documentation with docstrings explaining the queue state semantics
- The `to_log_format()` method provides a clean, readable format (R:3 B:2 done:4/10)
- Implementation correctly avoids expensive recomputation by using in-memory scheduler state
- Progress display and logger both receive queue state for consistent UI/logging

## Summary Statistics
- Critical: 0
- Major: 0
- Minor: 1
- Warnings: 1
- Suggestions: 1
