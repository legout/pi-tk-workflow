# MVP Scope: backlog-deps-and-tags

## In scope
- Add dependency inference for `/tf-backlog` (seed mode first)
  - Chain tickets in creation order as a default fallback
  - Use explicit ordering when detectable from seed content
- Add component tag detection and assignment
  - Simple keyword matching in ticket titles
  - Standard components: cli, api, docs, tests, config
- Link related tickets using `tk link`
  - Link tickets with same component that are created sequentially
  - Keep linking conservative (better to under-link than over-link)
- Update `backlog.md` to show dependencies, components, and links
- Document the new behavior
- Note: `/tf-deps-sync` and `/tf-tags-suggest` already exist as manual fallbacks

## Out of scope (for MVP)
- Complex dependency graphs with multiple parents
- Machine learning for component classification
- Retroactive application to existing tickets
- Plan/baseline mode dependency inference (can be added later)
- Custom component taxonomies per project
