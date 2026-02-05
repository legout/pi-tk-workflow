---
id: ptw-0un2
status: closed
deps: []
links: []
created: 2026-02-05T14:40:00Z
type: task
priority: 2
assignee: legout
---
# Add pytest coverage configuration with minimum threshold


## Notes

**2026-02-05T14:44:45Z**

## Completed

Added pytest coverage configuration to pyproject.toml with:
- pytest settings (testpaths, markers, addopts)
- coverage run settings (source, omit, branch coverage)
- coverage report settings (exclude_lines, show_missing, precision)
- Minimum threshold: 4% (reflects current project coverage of 4.1%)

### Changes
- Modified: pyproject.toml

### Review Results
- Critical: 0
- Major: 1 (fixed: removed redundant skip_covered setting)
- Minor: 2 (fixed: removed default patterns and non-existent file from omit)

### Follow-up Tickets Created
- ptw-iq5o: Increase coverage threshold to 80%
- ptw-u91i: Add HTML coverage report
- ptw-pq0f: Add coverage fail-under to pytest defaults
- ptw-q4f4: Add more test markers

### Commit
307c41a: ptw-0un2: Add pytest coverage configuration with minimum threshold
