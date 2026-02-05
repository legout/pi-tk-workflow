---
id: ptw-g8z8
status: open
deps: []
links: []
created: 2026-02-05T14:17:13Z
type: task
priority: 2
assignee: legout
tags: [tf, enhancement, ptw-5pax-followup]
---
# Add error handling for VERSION file read errors in doctor command - get_version_file_version() silently returns None on any exception. File permission errors or encoding issues would go unnoticed. Consider logging/warning when VERSION file exists but can't be read.

