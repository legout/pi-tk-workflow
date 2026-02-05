# Constraints: backlog-deps-and-tags

- Must not break existing `/tf-backlog` workflows
- Dependency inference should be conservative (fewer deps is better than wrong deps)
- Component tags must not conflict with existing tags
- Keep implementation lightweight—no external ML services
- Ralph loop compatibility: component tags must match Ralph's expected format
- Leverage existing `/tf-deps-sync` and `/tf-tags-suggest` commands where possible (avoid duplicating logic)
