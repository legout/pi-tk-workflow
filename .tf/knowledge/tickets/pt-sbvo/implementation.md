# Implementation: pt-sbvo

## Summary
Add substring search and basic filters (status/tags/assignee/external-ref) to the TUI.

## Changes Made

### tf_cli/ui.py
1. Added Button import to Textual widgets
2. Added filter inputs to TicketBoard:
   - `search-input`: Substring search (title/body)
   - `status-filter`: Status filter input
   - `tag-filter`: Tag filter input
   - `assignee-filter`: Assignee filter input
   - `external-ref-filter`: External reference filter input
   - `clear-filters`: Button to clear all filters

3. Added reactive variables to track filter state:
   - `search_query`: Current search text
   - `status_filter`: Selected status
   - `tag_filter`: Tag filter text
   - `assignee_filter`: Assignee filter text
   - `external_ref_filter`: External ref filter text

4. Added filter handling methods:
   - `on_input_changed()`: Updates reactive state when inputs change
   - `_apply_filters()`: Applies all active filters to ticket list
   - `on_button_pressed()`: Handles clear button press
   - `_clear_filters()`: Resets all filters and restores full ticket set

5. Modified `update_board()` to use filtered tickets
6. Added CSS styling for filter bar and inputs

## Files Changed
- `tf_cli/ui.py` - Added search/filter UI and logic

## Key Decisions
- Placed filters above the board columns in a horizontal row
- Search matches title (case-insensitive substring) and body
- Filters are combined with AND logic
- Clearing filters restores full ticket set
- No indexing engine used (per constraint)

## Tests
- Syntax check passed: `python3 -m py_compile tf_cli/ui.py`
- Import check passed: `python3 -c "from tf_cli.ui import main"`
- Manual verification via `tf ui` command (pending TTY environment)
