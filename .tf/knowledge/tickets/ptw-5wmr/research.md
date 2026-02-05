# Research: ptw-5wmr

## Status
Research enabled. No additional external research was performed.

## Rationale
This is a straightforward internal task to add a version consistency check to the `tf doctor` command. The relevant information is available in the local repository:

- `package.json` contains the canonical version (0.1.0)
- `tf_cli/doctor_new.py` is the target file for adding the check
- Seed documentation in `.tf/knowledge/topics/seed-add-versioning/` defines the requirements

## Context Reviewed
- `tk show ptw-5wmr` - ticket requirements
- `package.json` - source of truth for version
- `tf_cli/doctor_new.py` - existing doctor implementation
- `.tf/knowledge/topics/seed-add-versioning/seed.md` - versioning vision
- `.tf/knowledge/topics/seed-add-versioning/mvp-scope.md` - MVP scope

## Implementation Plan
1. Add a function to read version from `package.json`
2. Add a function to check version consistency across sources (currently just package.json, extensible for future VERSION file)
3. Integrate into `run_doctor()` to print warning on mismatch
4. Ensure check is offline-safe (no network calls)

## Sources
- (none - local codebase only)
