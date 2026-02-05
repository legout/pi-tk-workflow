---
id: ptw-9ze6
status: closed
deps: []
links: []
created: 2026-02-05T14:17:14Z
type: task
priority: 2
assignee: legout
tags: [tf, feature, ptw-5pax-followup]
---
# Add --dry-run flag to tf doctor for previewing fixes without making changes - Shows what --fix would change without actually writing files. Useful for CI pipelines to verify VERSION file consistency without side effects.


## Notes

**2026-02-05T14:35:12Z**

Implemented --dry-run flag for tf doctor

Changes:
- Added --dry-run argument to tf new doctor command
- Shows what --fix would change without writing files
- Returns failure (exit code 1) when VERSION inconsistency detected
- Suitable for CI pipelines to verify VERSION file consistency

Critical bugs found in review and fixed:
- Fixed: dry-run now returns False on VERSION drift (was returning True)
- Fixed: dry-run now returns False on missing VERSION file

Commit: 3dc5a02
