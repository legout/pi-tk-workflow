# Implementation: pt-pbpm

## Summary
Added a stable DOM target (`id="board-stats"`) to the board statistics section in the Kanban template, enabling independent Datastar patching of ticket counts.

## Files Changed
- `tf_cli/templates/_board.html` - Added `id="board-stats"` attribute to the `.board-stats` div

## Change Details

### Before:
```html
<div class="board-stats">
    <span>Ready: {{ counts.ready }}</span>
    <span>Blocked: {{ counts.blocked }}</span>
    <span>In Progress: {{ counts.in_progress }}</span>
    <span>Closed: {{ counts.closed }}</span>
</div>
```

### After:
```html
<div id="board-stats" class="board-stats">
    <span>Ready: {{ counts.ready }}</span>
    <span>Blocked: {{ counts.blocked }}</span>
    <span>In Progress: {{ counts.in_progress }}</span>
    <span>Closed: {{ counts.closed }}</span>
</div>
```

## Key Decisions
- Used `id="board-stats"` as specified in the ticket requirements
- Kept the existing `class="board-stats"` to maintain CSS styling compatibility
- Made minimal localized change as per constraints - only added the id attribute

## Verification
The change is purely additive (adding an id attribute) and does not affect:
- Visual rendering (no visual regression)
- Existing CSS styling (class attribute preserved)
- Template logic or data binding
- Server-side rendering

## Acceptance Criteria Status
- [x] The counts section is wrapped in an element with a stable id (`id="board-stats"`)
- [x] Refreshing the board can update counts without full page reload (hook is in place)
- [x] No visual regression in the existing board page (class preserved, only added id)
