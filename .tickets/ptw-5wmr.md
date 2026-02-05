---
id: ptw-5wmr
status: closed
deps: []
links: []
created: 2026-02-05T13:38:20Z
type: task
priority: 2
assignee: legout
external-ref: seed-add-versioning
tags: [tf, backlog]
---
# Add optional version consistency check (code vs metadata)

## Task
Add a lightweight check that detects version inconsistencies (e.g., `tf doctor` warning if metadata versions don’t match).

## Context
Seed mentions “release hygiene” and validating version in code matches metadata to reduce confusion.

## Acceptance Criteria
- [ ] A check exists (standalone script or integrated into `tf doctor`) that compares relevant version sources.
- [ ] On mismatch, prints a clear warning with remediation steps.
- [ ] Check is safe to run offline and doesn’t break workflows.

## Constraints
- No CI gate required for MVP; warning-only is fine.

## References
- Seed: seed-add-versioning


## Notes

**2026-02-05T14:09:13Z**

Implemented version consistency check for tf doctor.

Changes:
- Added get_package_version() - reads version from package.json using existing read_json() helper
- Added get_version_file_version() - reads version from VERSION file
- Added check_version_consistency() - compares versions and prints warnings on mismatch
- Integrated into run_doctor() with clear status messages

Features:
- Uses package.json as canonical version source
- Validates version is non-empty string
- Handles missing/invalid files gracefully
- Prints clear warnings with remediation steps
- Safe to run offline (no network calls)

Commit: 399db77
