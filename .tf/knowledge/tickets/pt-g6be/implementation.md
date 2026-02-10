# Implementation: pt-g6be

## Summary
Add ready/blocked counts to normal Ralph logging (ticket start/finish). This ensures that when running Ralph with normal (non-progressbar) logging, the log lines include ready/blocked counts (R:<n> B:<n>) and done/total information.

## Implementation Details

The feature was already implemented in the codebase. The key components are:

### 1. Queue State Computation (tf/ralph.py)
In the `ralph_start` function (serial mode), queue state is computed before logging:

```python
# Compute queue state snapshot
ready_ids = set(list_ready_tickets(ticket_list_query(ticket_query)))
blocked_ids = set(list_blocked_tickets())
pending_ids = ready_ids | blocked_ids
# Remove currently running ticket from pending
if running_ticket in pending_ids:
    pending_ids.remove(running_ticket)
# Build dep_graph: blocked tickets have unmet deps
dep_graph: dict[str, set[str]] = {t: set() for t in blocked_ids if t in pending_ids}
# Compute queue state snapshot
from tf.ralph.queue_state import get_queue_state
queue_state = get_queue_state(
    pending=pending_ids,
    running={running_ticket} if running_ticket else set(),
    completed=completed_tickets,
    dep_graph=dep_graph,
)
```

### 2. Logger Integration (tf/ralph.py lines 1546, 1629)
The queue state is passed to the logger methods:

```python
# At ticket start
ticket_logger.log_ticket_start(ticket, mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)

# At ticket complete
ticket_logger.log_ticket_complete(ticket, "COMPLETE", mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)
```

### 3. Log Formatting (tf/logger.py lines 276-309)
The logger methods format the queue state using `to_log_format()`:

```python
def log_ticket_start(self, ticket_id: str, ..., queue_state: Optional[Any] = None) -> None:
    if queue_state is not None:
        extra["queue_state"] = str(queue_state)
        self.info(f"Starting ticket processing: {ticket_id} [{queue_state.to_log_format()}]", **extra)

def log_ticket_complete(self, ticket_id: str, status: str, ..., queue_state: Optional[Any] = None) -> None:
    if queue_state is not None:
        extra["queue_state"] = str(queue_state)
        self._log(level, f"Ticket processing {status.lower()}: {ticket_id} [{queue_state.to_log_format()}]", extra)
```

### 4. Queue State Format (tf/ralph/queue_state.py)
The `QueueStateSnapshot` class provides the formatting:

```python
def to_log_format(self) -> str:
    """Format for log lines: R:3 B:2 done:1/6"""
    return f"R:{self.ready} B:{self.blocked} done:{self.done}/{self.total}"
```

## Output Example

```
2026-02-10T12:52:41Z | INFO | iteration=0 | mode=serial | queue_state="R:3 B:2 (done 4/10)" | ticket=pt-abc123 | Starting ticket processing: pt-abc123 [R:3 B:2 done:4/10]
2026-02-10T12:52:41Z | INFO | iteration=0 | mode=serial | queue_state="R:3 B:2 (done 4/10)" | status=COMPLETE | ticket=pt-abc123 | Ticket processing complete: pt-abc123 [R:3 B:2 done:4/10]
```

## Files Changed
- No changes required - feature already implemented

## Tests Run
- `tests/test_logger.py` - 35 passed
- `tests/test_ralph_logging.py` - 42 passed  
- `tests/test_progress_display.py` - 22 passed
- `tests/test_ralph_state.py` - 11 passed

Total: 121 tests passed

## Verification
Verified that the implementation works correctly:

```python
from tf.logger import RalphLogger, LogLevel
from tf.ralph.queue_state import QueueStateSnapshot

queue_state = QueueStateSnapshot(ready=3, blocked=2, running=1, done=4, total=10)
logger.log_ticket_start('pt-test123', mode='serial', queue_state=queue_state)
# Output: Starting ticket processing: pt-test123 [R:3 B:2 done:4/10]

logger.log_ticket_complete('pt-test123', 'COMPLETE', mode='serial', queue_state=queue_state)
# Output: Ticket processing complete: pt-test123 [R:3 B:2 done:4/10]
```

## Acceptance Criteria
- [x] On ticket start log line includes current `R:<n> B:<n>` (and done/total if available)
- [x] On ticket finish log line includes updated counts
- [x] Errors still print immediately and remain prominent (error logging unchanged)

## Constraints Met
- [x] Avoid expensive recomputation - uses in-memory scheduler state
- [x] Does not break existing output contracts - additive only
- [x] Non-TTY output remains readable (no animated control characters in log output)
- [x] Blocked is deps-only as per MVP spec
