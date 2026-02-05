# Implementation: ptw-5yxe

## Summary
Updated documentation to clearly describe the fallback workflow when `/tf-backlog` inference is incomplete. Added documentation for manual correction tools (`/tf-tags-suggest`, `/tf-deps-sync`) and manual linking via `tk link`.

## Files Changed
- `docs/workflows.md` - Added Step 6 to Greenfield Development section
- `docs/commands.md` - Added fallback workflow note to `/tf-backlog`, added full documentation for `/tf-tags-suggest` and `/tf-deps-sync`

## Key Decisions
- Added the fallback workflow as Step 6 in the Greenfield Development section to position it right after backlog generation and before autonomous processing
- Documented the typical sequence: `/tf-backlog` → `/tf-tags-suggest --apply` → `/tf-deps-sync --apply`
- Added `/tf-tags-suggest` and `/tf-deps-sync` as new command sections in commands.md for complete coverage
- Included manual linking via `tk link` as a fallback when automatic sync misses dependencies

## Changes Made

### docs/workflows.md
- Added "Step 6: Refine Backlog (Optional)" to Greenfield Development workflow
- Documents when to run the correction tools
- Provides clear examples and explains what each tool does

### docs/commands.md
- Added "Fallback Workflow" section to `/tf-backlog` command
- Added new `/tf-tags-suggest` command documentation with flags and examples
- Added new `/tf-deps-sync` command documentation with flags and examples
- Both new commands include purpose, flags table, and manual fallback guidance

## Tests Run
- `ruff check` - All checks passed
- `prettier --check` - No formatting issues

## Verification
- Documentation is short and actionable as required
- Typical sequence clearly documented
- Manual linking via `tk link` mentioned
- Guidance matches actual behavior of the tools
