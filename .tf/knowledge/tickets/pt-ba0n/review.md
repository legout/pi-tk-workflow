# Review: pt-ba0n

## Critical (must fix)
- `tf_cli/web_ui.py:90-101` - `_topic_to_dict()` references non-existent properties `topic.has_overview`, `topic.has_sources`, `topic.has_plan`, `topic.has_backlog`. The Topic dataclass only has `overview`, `sources`, `plan`, `backlog` attributes (which are Optional[TopicDoc]). This will cause AttributeError when rendering templates. Fix by using `topic.overview is not None and topic.overview.exists` pattern instead.
- `tf_cli/templates/topics.html:62` - **XSS vulnerability in data-signals attribute**: The `data-signals:search="{{ search_query }}"` is vulnerable to HTML attribute injection. If search_query contains a double quote, it will break out of the attribute context. Fix: Use Jinja2's `|e` filter explicitly: `data-signals:search="{{ search_query|e }}"`.
- `tf_cli/templates/_topics_list.html:21` - **Template injection in data-on:click**: The topic ID is embedded directly in a Datastar directive: `data-on:click="@get('/topic/{{ topic.id }}')"`. If a topic ID contains single quotes or backslashes, it will break the JavaScript string context. Fix: URL-encode the topic ID.

## Major (should fix)
- `tf_cli/templates/topics.html:68` - **No debounce on search input**: The search input fires a server request on every keystroke. This creates excessive server load. Fix: Add debouncing to limit request frequency (e.g., 300ms delay).
- `tf_cli/web_ui.py:135` - **No input sanitization on search query**: The search query is passed directly to `loader.search()` without length limits. Fix: Add a maximum length check (e.g., 100 chars) and trim whitespace.
- `tf_cli/templates/topic_detail.html:103` - **Potential XSS via doc_path**: The `{{ topic_obj[doc_type].path }}` renders a filesystem path directly. While autoescape protects against HTML injection, verify this is intentional.

## Minor (nice to fix)
- `tf_cli/web_ui.py:123` - The "unknown" topic type is initialized but never used in template rendering. Consider removing to avoid confusion.
- `tf_cli/web_ui.py:95-98` - **Redundant existence checks**: The `_topic_to_dict` function checks `topic.overview is not None and topic.overview.exists`. Simplify to `topic.overview.exists if topic.overview else False`.
- `tf_cli/templates/topic_detail.html:34` - The doc path display uses `{{ topic_obj[doc_type].path if topic_obj else '' }}` which may fail with Jinja2 undefined error. Use defensive access.

## Warnings (follow-up ticket)
- `tf_cli/web_ui.py:131-133` - No pagination implemented. If knowledge base grows to hundreds of topics, response size and render time will degrade.
- `tf_cli/templates/base.html:10` - Datastar CDN is pinned to `v1.0.0-RC.7`. Monitor for stable v1.0.0 release and plan upgrade path.
- `tf_cli/web_ui.py:137-140` - Silent error handling. Consider providing more user-friendly error details in the UI.

## Suggestions (follow-up ticket)
- `tf_cli/web_ui.py` - Consider caching TopicIndexLoader results to avoid re-reading index.json on every keystroke.
- `tf_cli/templates/topic_detail.html` - Document paths are shown but not clickable/editable. Consider adding links to view documents.
- `tf_cli/templates/topics.html` - Add keyboard navigation following terminal TUI pattern.

## Summary Statistics
- Critical: 3
- Major: 3
- Minor: 3
- Warnings: 3
- Suggestions: 3
