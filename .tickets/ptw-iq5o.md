---
id: ptw-iq5o
status: open
deps: []
links: []
created: 2026-02-05T14:44:27Z
type: task
priority: 3
assignee: legout
tags: [tf, followup]
---
# Increase pytest coverage threshold from 4% to 80%

## Origin
From review of: ptw-0un2
File: pyproject.toml

## Issue
The current coverage threshold is set to 4% to reflect the project's current state. As the project matures and more tests are added, this threshold should be incrementally increased toward a target of 80%+.

## Current State
- Coverage threshold: 4%
- Actual coverage: ~4.1%
- Only doctor_new.py module has tests

## Acceptance Criteria
- [ ] Add tests for additional modules
- [ ] Incrementally increase fail_under threshold
- [ ] Target 80%+ coverage

