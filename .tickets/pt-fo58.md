---
id: pt-fo58
status: closed
deps: []
links: [pt-sd01]
created: 2026-02-09T09:32:03Z
type: task
priority: 2
assignee: legout
external-ref: seed-tf-ui-web-app
tags: [tf, backlog, component:cli, component:workflow]
---
# Implement web server CLI command for tf ui (Sanic)

## Task
Add web server command to serve tf ui via browser using **Sanic**.

## Context
Based on the spike decision (pt-sd01), implement the web UI using **Sanic+Datastar**. This includes adding the CLI command and basic Sanic server infrastructure.

## Acceptance Criteria
- [ ] Add `pip install sanic` dependency (update pyproject.toml)
- [ ] Add `tf ui --web` flag to start Sanic web server
- [ ] Implement Sanic app with configurable host/port (default: 127.0.0.1:8000)
- [ ] Add `--host` and `--port` CLI options
- [ ] Implement graceful shutdown with Ctrl+C handling (Sanic's built-in)
- [ ] Add basic logging for server events (Sanic access logs)
- [ ] Ensure existing `tf ui` (terminal mode) continues to work unchanged
- [ ] Add error handling for port conflicts and startup failures
- [ ] Add Datastar CDN include to base template (v1.0.0-RC.7 pinned)

## Sanic-Specific Implementation Notes
- Use `Sanic(__name__)` app factory
- Use `app.route()` decorators for routing
- Use `sanic.response.html()` for HTML responses
- Use Jinja2 directly (not FastAPI's wrapper) for templating
- Run with `app.run(host, port)` or `sanic` CLI

## Constraints
- Server must bind to localhost by default (security)
- Port must be configurable to avoid conflicts
- Must not break existing terminal TUI functionality
- Use existing business logic from tf_cli/ui.py where possible
- Pin Datastar CDN version to avoid breaking changes

## References
- Seed: seed-tf-ui-web-app
- Decision: pt-sd01 (Sanic+Datastar)
- Sanic docs: https://sanic.dev/
- Datastar docs: https://data-star.dev

## Notes

**2026-02-09T12:43:14Z**

Completed all acceptance criteria:
- Added --web, --host, --port CLI options to tf ui command
- Created tf_cli/web_ui.py with Sanic web server
- Copied templates to tf_cli/templates/ with Datastar CDN (v1.0.0-RC.7)
- Implemented graceful shutdown (Sanic built-in)
- Added basic logging (Sanic access logs)
- Error handling for port conflicts (OSError with errno 98/48)
- Terminal TUI (--web flag not specified) continues to work unchanged
- Default: 127.0.0.1:8000

Usage: tf ui --web [--host HOST] [--port PORT]
