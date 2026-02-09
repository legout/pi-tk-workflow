---
id: pt-za25
status: open
deps: [pt-m387]
links: [pt-m387, pt-pbpm]
created: 2026-02-09T13:26:39Z
type: task
priority: 2
assignee: legout
external-ref: spike-datastar-py-sanic-datastar-tf-web-ui
tags: [tf, backlog, component:api, component:config, component:workflow]
---
# Add server-side search/filter using Datastar signals (read_signals)

## Task
Add a basic search/filter input using Datastar signals and implement server-side filtering by reading signals via datastar-py `read_signals()`.

## Context
datastar-py can parse the current signal state from requests. This enables implementing filters without building a separate JSON API.

## Acceptance Criteria
- [ ] Board page has a search input wired as a Datastar signal (e.g. `$search`).
- [ ] `/api/refresh` (and/or stream endpoint) reads signals and filters tickets by title (simple contains-match is fine).
- [ ] Filtering does not break navigation to ticket detail pages.

## Constraints
- Keep filtering logic simple and fast; no full-text search needed.

## References
- Spike: spike-datastar-py-sanic-datastar-tf-web-ui


