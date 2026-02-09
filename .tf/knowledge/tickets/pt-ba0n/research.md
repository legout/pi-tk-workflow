# Research: pt-ba0n

## Status
Research enabled. Explored existing codebase patterns.

## Context Reviewed

### Existing Web UI Architecture
- **Framework**: Sanic (backend) + Datastar v1.0.0-RC.7 (frontend)
- **Template Engine**: Jinja2 with autoescape enabled
- **Base Template**: `tf_cli/templates/base.html` includes Datastar CDN bundle
- **Datastar Pattern**: Uses SSE for server-side updates, `data-on:*` for events, `data-signals` for state

### TopicIndexLoader (tf_cli/ui.py)
Already provides:
- `load()` - Load topics from `.tf/knowledge/index.json`
- `get_by_type(type)` - Filter by type (seed, plan, spike, baseline)
- `search(query)` - Search in title, keywords, ID
- `get_by_id(id)` - Get single topic
- Properties: `available_docs`, `topic_type`, `title`, `keywords`

### Datastar Patterns in Project
From `base.html`:
```html
<script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.0-RC.7/bundles/datastar.js"></script>
```

Key Datastar attributes for this implementation:
- `data-signals:search="''"` - Initialize signal
- `data-bind:search` - Two-way bind input to signal
- `data-on:click="@get('/path')"` - Trigger GET request
- `data-on:input="@get('/api/topics?search=' + $search)"` - Real-time search

### Knowledge Base Structure
- Topics stored in `.tf/knowledge/topics/{topic-id}/`
- `index.json` contains metadata for all topics
- Document types: overview, sources, plan, backlog
- Topic types derived from ID prefix: seed-, plan-, spike-, baseline-

## Implementation Approach
1. Add `/topics` route in web_ui.py using TopicIndexLoader
2. Add `/api/topics` endpoint for search/filter (optional - can do client-side)
3. Create `topics.html` template with Datastar signals
4. Add navigation link in base.html header
5. Style consistently with existing board design

## References
- Datastar docs: https://data-star.dev
- Datastar signals: https://data-star.dev/reference/attributes#data-signals
- `tf_cli/ui.py` - TopicIndexLoader class
- `tf_cli/web_ui.py` - Existing Sanic routes
- `tf_cli/templates/base.html` - Base template with Datastar
