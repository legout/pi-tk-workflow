---
id: pt-p2dq
status: closed
deps: [pt-tpz9]
links: [pt-n2dw]
created: 2026-02-09T09:31:35Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:docs, component:workflow]
---
# Handle document viewing in web UI (replace $PAGER)

## Task
Implement inline document viewing for knowledge base documents.

## Status
**CLOSED as duplicate** - Consolidated into pt-n2dw. See pt-sd01 for stack decision (Sanic+Datastar).

## Context
In the terminal TUI, documents are opened via $PAGER (less, vim). In web mode, we need to render documents inline in the browser instead of spawning external processes.

## Acceptance Criteria
- [ ] Read and render markdown documents inline
- [ ] Support syntax highlighting for code blocks
- [ ] Handle missing documents gracefully (show "not found" message)
- [ ] Support documents: overview.md, sources.md, plan.md, backlog.md
- [ ] Add navigation between documents for a topic
- [ ] Render document with styling consistent with web UI

## Constraints
- Must not spawn external pager/editor processes
- Use existing resolve_knowledge_dir() for path resolution
- Documents must be rendered safely (no XSS)

## References
- Seed: seed-tf-ui-web-app
- **Consolidated into**: pt-n2dw (Sanic+Datastar implementation)
- **Stack decision**: pt-sd01
- tf_cli/ui.py - _open_doc method, resolve_knowledge_dir function
