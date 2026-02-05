---
id: ptw-azum
status: closed
deps: []
links: []
created: 2026-02-05T14:00:22Z
type: task
priority: 2
assignee: legout
external-ref: seed-backlog-deps-and-tags
tags: [tf, backlog]
---
# Add conservative component classifier (keyword mapping)

## Task
Implement a small, conservative component classifier used by /tf-backlog and /tf-tags-suggest.

## Context
For MVP we want simple, explainable tagging such as mapping keywords in title/description to components (cli/docs/tests/config/api).

## Acceptance Criteria
- [ ] A documented mapping exists (keywords -> component tag).
- [ ] Classifier returns 0..N component tags with rationale (for debug output).
- [ ] Classifier is easy to extend without touching core logic.

## Constraints
- No external services; keep logic deterministic.

## References
- Seed: seed-backlog-deps-and-tags


## Notes

**2026-02-05T14:55:58Z**

--message 
## Implementation Complete

Implemented conservative component classifier with keyword mapping.

### Changes
- tf_cli/component_classifier.py - Core classifier with DEFAULT_KEYWORD_MAP
- tf_cli/tags_suggest_new.py - CLI commands (tags-suggest, tags-classify, tags-keywords)
- tests/test_component_classifier.py - 24 tests covering all components
- tf_cli/new_cli.py - Added new CLI commands

### Features
- 7 component tags: cli, api, docs, tests, config, workflow, agents
- Rationale output for debug/traceability
- Extensible via custom_keywords parameter
- No external dependencies, deterministic matching

### Verification
All 62 tests pass (24 new + 38 existing).

Commit: 95b5ebe

