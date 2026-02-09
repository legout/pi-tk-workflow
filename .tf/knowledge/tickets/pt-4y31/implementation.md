# Implementation: pt-4y31

## Summary
Changed the Sanic `/api/refresh` endpoint to return a `DatastarResponse` with SSE events that patch both the board and the counts using datastar-py's `ServerSentEventGenerator.patch_elements()`.

## Files Changed
- `examples/web-ui-poc/sanic-datastar/web_app.py` - Updated `/api/refresh` endpoint to use `DatastarResponse` with multi-target SSE patches
- `examples/web-ui-poc/sanic-datastar/templates/index.html` - Added `id="board-stats"` to stats container
- `examples/web-ui-poc/sanic-datastar/templates/_board_stats.html` - New template for stats fragment

## Key Decisions
1. **Multi-target SSE approach**: Using `DatastarResponse([board_event, stats_event])` enables updating both `#board` and `#board-stats` from a single endpoint call.
2. **Separate template for stats**: Created `_board_stats.html` to keep the stats rendering DRY between the main page and the refresh endpoint.
3. **Error handling**: On board load failure, returns a `DatastarResponse` with status 500 containing an error SSE event, maintaining consistent Datastar handling.
4. **No JS changes**: The existing `data-on:click="@get('/api/refresh')"` works unchanged because Datastar handles SSE responses automatically.

## Implementation Details

The `/api/refresh` endpoint now:
1. Loads board data via `get_board_data()`
2. Renders two fragments:
   - `_board.html` with ticket columns → patches `#board`
   - `_board_stats.html` with counts → patches `#board-stats`
3. Creates SSE events using `ServerSentEventGenerator.patch_elements()`
4. Returns `DatastarResponse([board_event, stats_event])`

## Tests Run
- Syntax check: `python3 -m py_compile web_app.py` - OK
- Import verification: DatastarResponse and ServerSentEventGenerator import correctly
- Template loading: Both `_board.html` and `_board_stats.html` load successfully
- SSE format verification: Response body contains correct `datastar-patch-elements` events

## Verification
To verify:
1. Run the Sanic app: `python examples/web-ui-poc/sanic-datastar/web_app.py`
2. Open http://127.0.0.1:8080/
3. Click the Refresh button
4. Both board and stats should update via SSE
