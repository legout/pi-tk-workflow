---
id: pt-sd01
status: closed
deps: [pt-7t1n]
links: [pt-7t1n, pt-aoq0]
created: 2026-02-09T12:00:00Z
type: spike
priority: 1
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, spike, web-ui, sanic, datastar]
---
# Spike: Switch web UI stack to Sanic+Datastar

## Decision
Switch web UI stack from **FastAPI+HTMX** to **Sanic+Datastar** for the `tf ui --web` implementation.

## Rationale
- **Datastar's SSE-first architecture** enables cleaner real-time updates and server-push UI patterns
- **Signals-based reactivity** reduces frontend complexity vs HTMX's request/response model
- **Single 11KB library** (Datastar) vs HTMX+Alpine combo
- **Sanic's native async** fits well with Datastar's server-push model
- Team preference for cutting-edge hypermedia approach

## Stack Lock (Version Pinning)
To manage Datastar's RC status, we pin versions:

| Component | Version | Notes |
|-----------|---------|-------|
| Datastar | v1.0.0-RC.7 | Pinned CDN bundle |
| Sanic | Latest stable | 25.x+ (Python 3.10+) |
| Attribute syntax | Colon-delimited | `data-on:click` (not `data-on-click`) |
| SSE events | `datastar-patch-elements` | Per RC.7 spec |

## Migration Impact

### Tickets Updated
- pt-fo58 → Web server CLI (Sanic instead of FastAPI)
- pt-1d6c → Kanban view (Datastar attributes)
- pt-ba0n → Topic browser (Datastar attributes)
- pt-c4lo → Ticket detail (Datastar attributes)
- pt-n2dw → Document viewing (Datastar attributes)

### Duplicates Closed
- pt-1x64 (dup of pt-fo58)
- pt-znph (dup of pt-1d6c)
- pt-pdha (dup of pt-ba0n)
- pt-tpz9 (dup of pt-c4lo)
- pt-p2dq (dup of pt-n2dw)

### Superseded
- pt-aoq0 (evaluated textual-web vs FastAPI+HTMX - no longer relevant)
- pt-7t1n spike findings (FastAPI+HTMX decision overridden)

## Key Syntax Changes

| Pattern | HTMX | Datastar |
|---------|------|----------|
| Click handler | `hx-get="/url" hx-target="#id"` | `data-on:click="@get('/url')"` |
| Auto-load | `hx-trigger="load"` | `data-init` or `data-on:load` |
| Partial updates | `hx-swap` | Server sends `datastar-patch-elements` SSE |
| Signals | Not built-in | `data-signals:foo="'bar'"` then `$foo` |

## References
- Research spike: `.tf/knowledge/topics/spike-sanic-datastar-vs-fastapi-htmx/`
- Datastar docs: https://data-star.dev
- Sanic docs: https://sanic.dev/
- Datastar Python SDK: https://github.com/starfederation/datastar/tree/main/sdk/python

## Notes

**2026-02-09T12:00:00Z** - Decision made to proceed with Sanic+Datastar. All open tickets updated. POC created at `examples/web-ui-poc/sanic-datastar/`.
