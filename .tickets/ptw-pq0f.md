---
id: ptw-pq0f
status: open
deps: []
links: []
created: 2026-02-05T14:44:27Z
type: task
priority: 3
assignee: legout
tags: [tf, followup]
---
# Add coverage fail-under to pytest addopts

## Origin
From review of: ptw-0un2
File: pyproject.toml

## Issue
Consider adding '--cov-fail-under=4' to the pytest addopts to make coverage failures happen during regular test runs, not just when explicitly checking coverage.

## Proposed Change
Add '--cov-fail-under=4' to [tool.pytest.ini_options] addopts (or use fail_under from coverage config)

## Acceptance Criteria
- [ ] Coverage check runs with pytest by default
- [ ] Tests fail if coverage drops below threshold

