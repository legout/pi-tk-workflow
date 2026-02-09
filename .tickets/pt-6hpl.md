---
id: pt-6hpl
status: closed
deps: []
links: [pt-4y31]
created: 2026-02-09T13:26:39Z
type: task
priority: 2
assignee: legout
external-ref: spike-datastar-py-sanic-datastar-tf-web-ui
tags: [tf, backlog, component:config, component:docs]
---
# Setup datastar-py dependency (pin version) for web UI

## Task
Add `datastar-py` to Ticketflow dependencies and pin to a compatible version with the currently pinned Datastar JS bundle.

## Context
Ticketflow’s web UI uses Datastar JS (`v1.0.0-RC.7`) but currently returns plain HTML fragments from Sanic. datastar-py will be used to generate SSE events and framework-specific responses.

## Acceptance Criteria
- [ ] `datastar-py` is added to `pyproject.toml` dependencies (version pinned).
- [ ] Basic import check passes: `python -c "import datastar_py"` (in project env).
- [ ] A short note is added to docs/comments explaining the version pin rationale.

## Constraints
- Keep current Datastar JS pin (`v1.0.0-RC.7`) unless explicitly changed.

## References
- Spike: spike-datastar-py-sanic-datastar-tf-web-ui



## Notes

**2026-02-09T13:32:08Z**

Implemented datastar-py dependency setup.

Changes:
- Added datastar-py>=0.7.0,<0.8.0 to pyproject.toml dependencies
- Added module docstring to tf_cli/web_ui.py explaining version pin rationale

Version rationale:
- 0.7.0 selected because 0.8.0 requires Python >=3.10 (project supports >=3.9)
- Both 0.7.0 and 0.8.0 are compatible with Datastar JS v1.0.0-RC.7
- Upper bound <0.8.0 prevents accidental Python 3.9 breakage

Verification:
- Import check passes: uv run python -c 'import datastar_py'
- Package installed via uv sync

Commit: 86d2a9c
