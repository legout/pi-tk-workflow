---
id: ptw-q4f4
status: open
deps: []
links: []
created: 2026-02-05T14:44:27Z
type: task
priority: 3
assignee: legout
tags: [tf, followup]
---
# Add more pytest markers for test categorization

## Origin
From review of: ptw-0un2
File: pyproject.toml

## Issue
Consider adding more markers for test categorization (e.g., unit, e2e, smoke) to enable better test filtering.

## Current Markers
- slow
- integration

## Proposed Additional Markers
- unit: fast unit tests
- e2e: end-to-end tests
- smoke: quick smoke tests

## Acceptance Criteria
- [ ] New markers defined in pyproject.toml
- [ ] Existing tests categorized with appropriate markers

