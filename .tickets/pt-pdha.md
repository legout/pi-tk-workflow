---
id: pt-pdha
status: closed
deps: [pt-znph]
links: [pt-ba0n]
created: 2026-02-09T09:31:35Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Implement topic browser in web UI

## Task
Implement the topic browser view for navigating knowledge base topics.

## Status
**CLOSED as duplicate** - Consolidated into pt-ba0n. See pt-sd01 for stack decision (Sanic+Datastar).

## Context
Users need to browse and search knowledge base topics (seeds, spikes, plans) in the web UI, similar to the terminal TUI's topic browser.

## Acceptance Criteria
- [ ] Display list of topics grouped by type (seed, spike, plan, baseline)
- [ ] Add search/filter input for topic titles
- [ ] Click topic to view details
- [ ] Show topic metadata: title, type, keywords
- [ ] Indicate available documents (overview, sources, plan, backlog)
- [ ] Use existing TopicIndexLoader for loading topics

## Constraints
- Reuse existing TopicIndexLoader from tf_cli/ui.py
- Search should filter in real-time or on submit
- Maintain consistency with terminal TUI behavior

## References
- Seed: seed-tf-ui-web-app
- **Consolidated into**: pt-ba0n (Sanic+Datastar implementation)
- **Stack decision**: pt-sd01
- tf_cli/ui.py - TopicIndexLoader class
