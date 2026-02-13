---
id: pt-6zp2
status: open
deps: [pt-lw9p]
links: [pt-lw9p, pt-u9cj]
created: 2026-02-13T12:44:43Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-a-fixer-model-to-the-metamodels-in-t
tags: [tf, backlog, tests, component:agents, component:docs, component:tests, component:workflow]
---
# Add tests for fixer meta-model selection + backward compatibility

## Task
Add/adjust tests covering fixer model selection.

## Context
We need regression coverage so changing meta-model mappings doesn’t silently change which model is used for fix iterations.

## Acceptance Criteria
- [ ] With `metaModels.fixer` present, fixer resolves to that model.
- [ ] With `metaModels.fixer` absent, fixer follows the documented fallback.
- [ ] If escalation overrides fixer model, that precedence is covered (if implemented).

## References
- Seed: seed-add-a-fixer-model-to-the-metamodels-in-t


