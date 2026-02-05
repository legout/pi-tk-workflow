---
id: ptw-u91i
status: open
deps: []
links: []
created: 2026-02-05T14:44:27Z
type: task
priority: 3
assignee: legout
tags: [tf, followup]
---
# Add HTML coverage report to pytest defaults

## Origin
From review of: ptw-0un2
File: pyproject.toml

## Issue
Consider adding coverage HTML reports to the default addopts for easier local debugging of coverage gaps.

## Proposed Change
Add '--cov-report=html' to [tool.pytest.ini_options] addopts

## Acceptance Criteria
- [ ] HTML coverage report generated on test runs
- [ ] Report directory added to .gitignore

