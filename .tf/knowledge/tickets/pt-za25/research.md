# Research: pt-za25 - Server-side search/filter using Datastar signals

## Status
Research complete. Implementation approach confirmed using datastar-py `read_signals()`.

## Key Findings

### datastar-py read_signals() API
- Location: `datastar_py.sanic.read_signals(request)`
- Returns: `dict[str, Any] | None` - parsed signal state or None if not a Datastar request
- Datastar sends signal state as:
  - GET requests: `datastar` query parameter containing JSON-encoded signals
  - POST/PUT: JSON body when Content-Type is `application/json`
- Header check: Requires `Datastar-Request` header (automatically sent by Datastar)

### Current Web UI Structure
- **web_ui.py**: Sanic app with `/api/refresh` and `/api/stream` endpoints
- **index.html**: Main board page with Datastar SSE stream subscription
- **_board.html**: Partial template rendered for refresh/stream updates
- **base.html**: Base template with Datastar v1.0.0-RC.7 CDN

### Datastar Signal Binding Pattern
To wire a search input as a signal:
```html
<input data-bind="$search" placeholder="Search tickets..." />
```
This creates a signal named `$search` that Datastar tracks and sends back on requests.

### Filtering Approach
1. Frontend: Add search input with `data-bind="$search"`
2. Frontend: Trigger refresh on input with `data-on:input="@get('/api/refresh')"`
3. Backend: Use `read_signals(request)` to get signal state
4. Backend: Filter tickets by title (case-insensitive contains match)
5. Backend: Return filtered board HTML

### Navigation Preservation
- Ticket cards use `data-on:click="@get('/ticket/{id}')"` for navigation
- Search filtering must not interfere with this event handling
- Datastar handles events independently - click will still work during filtering

## Implementation Plan
1. Modify `_board.html` to add search input with signal binding
2. Modify `web_ui.py` `/api/refresh` endpoint to:
   - Import and use `read_signals` from datastar_py.sanic
   - Extract `$search` signal value
   - Filter tickets before building columns data
3. Test that ticket detail navigation still works

## References
- datastar-py Sanic module: `/home/volker/coding/pi-ticketflow/.venv/lib/python3.13/site-packages/datastar_py/sanic.py`
- Current web UI: `/home/volker/coding/pi-ticketflow/tf_cli/web_ui.py`
- Spike research: `/home/volker/coding/pi-ticketflow/.tf/knowledge/topics/spike-datastar-py-sanic-datastar-tf-web-ui/spike.md`
