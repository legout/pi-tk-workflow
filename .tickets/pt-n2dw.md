---
id: pt-n2dw
status: open
deps: [pt-c4lo]
links: [pt-sd01]
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Handle document viewing in web UI (replace $PAGER)

## Task
Implement inline document viewing for knowledge base documents using **Datastar**.

## Context
In the terminal TUI, documents are opened via $PAGER (less, vim). In web mode, we need to render documents inline in the browser instead of spawning external processes. Uses **Datastar** for document navigation.

## Acceptance Criteria
- [ ] Read and render markdown documents inline
- [ ] Support syntax highlighting for code blocks
- [ ] Handle missing documents gracefully (show "not found" message)
- [ ] Support documents: overview.md, sources.md, plan.md, backlog.md
- [ ] Add navigation between documents for a topic using `data-on:click`
- [ ] Render document with styling consistent with web UI

## Datastar-Specific Implementation Notes
- Document navigation uses `data-on:click="@get('/topics/{id}/doc/{doc_type}')"`
- Active document tab highlighted via signals or CSS classes
- For scroll position preservation, use `data-preserve-attr` if needed

## Example Template Pattern
```html
<div id="doc-viewer">
  <div class="doc-tabs">
    <button data-on:click="@get('/topics/{{ topic_id }}/doc/overview')"
            class="{% if doc_type == 'overview' %}active{% endif %}">
      Overview
    </button>
    <button data-on:click="@get('/topics/{{ topic_id }}/doc/sources')"
            class="{% if doc_type == 'sources' %}active{% endif %}">
      Sources
    </button>
    <button data-on:click="@get('/topics/{{ topic_id }}/doc/plan')"
            class="{% if doc_type == 'plan' %}active{% endif %}">
      Plan
    </button>
    <button data-on:click="@get('/topics/{{ topic_id }}/doc/backlog')"
            class="{% if doc_type == 'backlog' %}active{% endif %}">
      Backlog
    </button>
  </div>
  
  <div id="doc-content" class="markdown">
    {%- if content %}
      {{ content_html | safe }}
    {%- else %}
      <p class="not-found">Document not found.</p>
    {%- endif %}
  </div>
</div>
```

## Constraints
- Must not spawn external pager/editor processes
- Use existing resolve_knowledge_dir() for path resolution
- Documents must be rendered safely (no XSS)
- Pin Datastar CDN version to avoid breaking changes

## References
- Seed: seed-tf-ui-web-app
- Decision: pt-sd01 (Sanic+Datastar)
- Datastar docs: https://data-star.dev
- Datastar preserve: https://data-star.dev/reference/attributes#data-preserve-attr
- tf_cli/ui.py - _open_doc method, resolve_knowledge_dir function
