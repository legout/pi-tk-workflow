# Fixes: pt-igly

## Issues Fixed

### Critical (1)
1. **Duplicated FRONTMATTER_PATTERN** - Now imports from `tf_cli.ticket_loader` instead of redefining

### Major (3)
1. **Misleading field name** - Changed `recent_closed` to `total_closed` in WorkflowStats NamedTuple
2. **Duplicated parsing logic** - Replaced `_parse_frontmatter_status()` with `TicketLoader` usage
3. **Missing unit tests** - Created `tests/test_workflow_status.py` with 14 test cases

## Changes Made

### tf_cli/workflow_status.py
- Removed local `FRONTMATTER_PATTERN` definition
- Added import: `from tf_cli.ticket_loader import TicketLoader`
- Renamed `recent_closed` → `total_closed` in WorkflowStats
- Replaced custom `_parse_frontmatter_status()` function with `TicketLoader` usage
- Updated `get_knowledge_entries()` to count `.md` files instead of directories
- Removed unused `re` import

### tests/test_workflow_status.py (new file)
- 14 test cases covering:
  - Project root resolution
  - Ticket counting by status
  - Knowledge entry counting
  - WorkflowStats and WorkflowStatus creation

## Verification
```bash
# Run the utility
python tf_cli/workflow_status.py

# Run tests
python -m pytest tests/test_workflow_status.py -v
```

All 14 tests pass.
