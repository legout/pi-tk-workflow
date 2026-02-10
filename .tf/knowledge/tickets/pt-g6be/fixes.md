# Fixes: pt-g6be

## Issues Fixed

### Minor Issue: Inconsistent Failure Path Logging
**Location:** `tf/ralph.py:1622`

**Issue:** On ticket failure, `log_error_summary()` was called instead of `log_ticket_complete()`, which meant the failure log line did not include the queue state (R:<n> B:<n> done:<n>/<n>). This was inconsistent with the success path and the acceptance criteria.

**Fix:** Added a call to `log_ticket_complete()` with FAILED status before the `log_error_summary()` call to ensure queue state is logged on both success and failure paths.

**Before:**
```python
knowledge_dir = resolve_knowledge_dir(project_root)
artifact_path = str(knowledge_dir / "tickets" / ticket)
ticket_logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration, ticket_title=ticket_title)
update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
```

**After:**
```python
knowledge_dir = resolve_knowledge_dir(project_root)
artifact_path = str(knowledge_dir / "tickets" / ticket)
ticket_logger.log_ticket_complete(ticket, "FAILED", mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)
ticket_logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration, ticket_title=ticket_title)
update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
```

## Verification
- All 121 tests pass
- The fix ensures both success and failure paths log queue state consistently
