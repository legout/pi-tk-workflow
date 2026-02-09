---
id: pt-ba0n
status: closed
deps: [pt-1d6c]
links: [pt-sd01]
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement topic browser in web UI (Datastar)

## Task
Implement the topic browser view for navigating knowledge base topics using **Datastar**.

## Context
Users need to browse and search knowledge base topics (seeds, spikes, plans) in the web UI, similar to the terminal TUI's topic browser. Uses **Datastar** for search/filter interactivity.

## Acceptance Criteria
- [ ] Display list of topics grouped by type (seed, spike, plan, baseline)
- [ ] Add search/filter input for topic titles using `data-bind` + `data-signals`
- [ ] Click topic to view details (using `data-on:click`)
- [ ] Show topic metadata: title, type, keywords
- [ ] Indicate available documents (overview, sources, plan, backlog)
- [ ] Use existing TopicIndexLoader for loading topics

## Datastar-Specific Implementation Notes
- Use `data-signals:search="''"` to hold search query
- Use `data-bind:search` on input for two-way binding
- Filter topics client-side using Datastar signals/expressions
- Or use `data-on:input` to trigger server search via `@get('/api/topics?search={$search}')`

## Example Template Pattern
```html
<div id="topic-browser">
  <input type="text" 
         data-signals:search="''"
         data-bind:search
         data-on:input="@get('/api/topics?search=' + $search)"
         placeholder="Search topics...">
  
  <div id="topic-list">
    {%- for topic in topics %}
    <div class="topic-card" 
         data-on:click="@get('/topics/{{ topic.id }}')">
      <span class="topic-type">{{ topic.type }}</span>
      <span class="topic-title">{{ topic.title }}</span>
      <span class="topic-docs">
        {%- if topic.has_overview %}📄{%- endif %}
        {%- if topic.has_plan %}📋{%- endif %}
      </span>
    </div>
    {%- endfor %}
  </div>
</div>
```

## Constraints
- Reuse existing TopicIndexLoader from tf_cli/ui.py
- Search should filter in real-time or on submit
- Maintain consistency with terminal TUI behavior
- Pin Datastar CDN version to avoid breaking changes

## References
- Seed: seed-tf-ui-web-app
- Decision: pt-sd01 (Sanic+Datastar)
- Datastar docs: https://-data-star.dev
- Datastar signals: https://data-star.dev/reference/attributes#data-signals
- tf_cli/ui.py - TopicIndexLoader class

## Notes

**2026-02-09T13:42:11Z**

Implemented topic browser with Datastar integration.

Changes:
- Added /topics route for topic browser
- Added /api/topics endpoint for real-time search
- Added /topic/<id> route for topic details
- Created templates: topics.html, _topics_list.html, topic_detail.html
- Updated base.html with navigation
- Implemented security fixes: XSS protection, input sanitization, debounced search

Commit: 440cbdf

Artifacts:
- research.md, implementation.md, review.md, fixes.md
