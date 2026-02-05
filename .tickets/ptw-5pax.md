---
id: ptw-5pax
status: closed
deps: []
links: []
created: 2026-02-05T14:09:28Z
type: task
priority: 2
assignee: legout
tags: [tf, feature, ptw-5wmr-followup]
---
# Consider tf doctor --fix to auto-sync VERSION file


## Notes

**2026-02-05T14:16:58Z**

Implemented tf doctor --fix flag to auto-sync VERSION file.

Changes:
- Added --fix argument to tf new doctor command
- Added sync_version_file() helper function
- Updated check_version_consistency() to support fix mode
- Fixed help text to document --fix flag

The --fix flag will:
- Create VERSION file if missing (with package.json version)
- Update VERSION file if it doesn't match package.json
- Show [fixed] message when changes are made

Commit: 1dd2cee
