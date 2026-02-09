# Review: pt-ba0n

## Overall Assessment
The implementation provides a functional topic browser with Datastar integration, but has a critical bug in the `_topic_to_dict` function that will cause template rendering errors. The code structure follows existing patterns well, but needs fixes for the document availability properties and minor XSS hardening.

## Critical (must fix)
- `tf_cli/web_ui.py:90-101` - `_topic_to_dict()` references non-existent properties `topic.has_overview`, `topic.has_sources`, `topic.has_plan`, `topic.has_backlog`. The Topic dataclass only has `overview`, `sources`, `plan`, `backlog` attributes (which are Optional[TopicDoc]). This will cause AttributeError when rendering templates. Fix by using `topic.overview is not None and topic.overview.exists` pattern instead.

## Major (should fix)
- `tf_cli/templates/topics.html:55` - `data-signals:search="{{ search_query }}"` renders user input directly into HTML attribute without proper escaping. While Jinja2 autoescapes for HTML content, attribute context requires additional care. Use `{{ search_query | e }}` explicitly or ensure quotes are escaped to prevent XSS if search query contains `"`.

## Minor (nice to fix)
- `tf_cli/web_ui.py:123` - The "unknown" topic type is initialized in `topics_by_type` but never used in template rendering (template only iterates over `['plan', 'spike', 'seed', 'baseline']`). Consider removing to avoid confusion, or add handling for unknown types in the template.
- `tf_cli/templates/topics.html:58` - No debouncing on search input means a server request fires on every keystroke. For large topic indexes, this could cause performance issues. Consider adding `data-on:input__debounce.300ms` if Datastar supports it, or document this as a known limitation.
- `tf_cli/templates/topic_detail.html:34` - The doc path display uses `{{ topic_obj[doc_type].path if topic_obj else '' }}` which will fail with a Jinja2 undefined error if topic_obj doesn't have that attribute. Should use `{{ topic_obj.get(doc_type).path if topic_obj and topic_obj.get(doc_type) else '' }}` or similar defensive access.

## Warnings (follow-up ticket)
- `tf_cli/web_ui.py:131-133` - Sorting happens after filtering, which is correct, but no pagination is implemented. If the knowledge base grows to hundreds of topics, the response size and render time will degrade. Consider adding pagination or virtual scrolling in a future enhancement.

## Suggestions (follow-up ticket)
- `tf_cli/templates/topic_detail.html` - The document paths are shown but not clickable/editable. Consider adding links to view or edit documents directly.
- `tf_cli/web_ui.py` - Consider caching the TopicIndexLoader results for a short duration (e.g., 5-10 seconds) to avoid re-reading index.json on every keystroke during search.

## Positive Notes
- Good reuse of existing `TopicIndexLoader` class from `tf_cli/ui.py`, ensuring consistency with terminal TUI
- Proper error handling with try/except blocks in `get_topics_data()` and `topic_detail()`
- Consistent template structure extending base.html with proper block overrides
- Datastar signals pattern (`data-signals:search` + `data-bind:search`) is implemented correctly per Datastar documentation
- Clean separation between full page routes (`/topics`) and fragment endpoints (`/api/topics`) for Datastar updates
- Good use of Jinja2 autoescape in Environment configuration for security

## Summary Statistics
- Critical: 1
- Major: 1
- Minor: 3
- Warnings: 1
- Suggestions: 2
