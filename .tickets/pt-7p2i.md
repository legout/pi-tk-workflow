---
id: pt-7p2i
status: closed
deps: [pt-bsuf]
links: [pt-bsuf]
created: 2026-02-09T13:42:03Z
type: task
priority: 2
assignee: legout
external-ref: spike-modern-simple-css-dashboard-kanban
tags: [tf, backlog, component:api]
---
# Add a small design-token layer (CSS variables) + fluid spacing via clamp()

## Task
Introduce a minimal set of CSS variables for surface/border/shadow/radius and use `clamp()` for responsive gaps/padding.

## Context
A small token layer keeps the UI consistent and modern without adopting a full utility framework. `clamp()` reduces breakpoint bloat.

## Acceptance Criteria
- [ ] `:root` defines tokens: surface colors, border, shadow, radius, and `--gap` using `clamp()`.
- [ ] Board layout uses tokenized `gap` and paddings.
- [ ] No regressions on mobile widths (columns stack appropriately).

## Constraints
- Keep token set small (≈10–15 variables).

## References
- Spike: spike-modern-simple-css-dashboard-kanban
- clamp() patterns: https://blog.openreplay.com/flexible-spacing-css-clamp/
- Utopia calculators: https://utopia.fyi/type/calculator/



## Notes

**2026-02-09T13:49:33Z**

Implemented CSS design-token layer with 18 CSS variables using clamp() for fluid spacing.

Changes:
- base.html: Added :root tokens (surface, brand, border, shadow, radius, fluid gaps/padding)
- index.html: Board layout uses tokenized gap and paddings
- ticket.html: Updated to use design tokens
- topics.html: Updated to use design tokens  
- topic_detail.html: Updated to use design tokens

All templates now use CSS custom properties for consistent theming. Mobile responsiveness preserved with columns stacking at 1024px and 640px breakpoints.

Review: 0 Critical, 0 Major (after fixes), 16 Minor (hardcoded colors for badges/status)
Commit: fde2319
