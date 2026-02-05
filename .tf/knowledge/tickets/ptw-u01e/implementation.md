# Implementation: ptw-u01e

## Summary
Extended version check in `tf doctor` to support git tags as a third version source. This allows verifying that package.json version matches the git tag for release validation.

## Files Changed

### 1. `tf_cli/doctor_new.py`
- Added `get_git_tag_version()` function that reads version from current git tag using `git describe --tags --exact-match`
- Updated `check_version_consistency()` to include git tag validation
- Git tags are normalized (v/V prefix stripped) for consistent comparison with manifest versions
- Shows `[ok] Git tag matches: X.Y.Z` when tag matches canonical version
- Shows `[warn] Git tag (X) does not match package.json (Y)` when there's a mismatch
- Git tag check is skipped when not on a tagged commit

### 2. `tests/test_doctor_version.py`
- Added import for `get_git_tag_version`
- Added `TestGetGitTagVersion` class with 4 tests:
  - `test_returns_tag_when_on_tagged_commit` - verifies tag detection and normalization
  - `test_returns_none_when_not_on_tagged_commit` - verifies no tag case
  - `test_returns_none_when_not_git_repo` - verifies non-git repo handling
  - `test_normalizes_v_prefix` - verifies V prefix normalization
- Added `TestGitTagVersionCheck` class with 3 tests:
  - `test_shows_ok_when_git_tag_matches` - verifies [ok] message when tag matches
  - `test_shows_warning_when_git_tag_mismatches` - verifies [warn] message on mismatch
  - `test_no_git_tag_check_when_not_tagged` - verifies skip when not tagged

## Key Decisions

1. **Normalization**: Git tags with `v` or `V` prefix (e.g., `v1.2.3`) are normalized to `1.2.3` for comparison, matching the existing behavior for VERSION files.

2. **Warning only**: Git tag mismatches produce warnings but don't fail the check. This is consistent with how manifest mismatches are handled - they warn but don't block.

3. **Silent skip**: When not on a tagged commit, the git tag check is silently skipped (no output). This avoids noise during normal development.

4. **Tag priority**: Git tag is checked after manifests but alongside VERSION file. It's treated as a validation source, not a canonical source.

## Tests Run

```bash
python -m pytest tests/test_doctor_version.py -v
# 71 tests passed
```

All existing tests continue to pass, and 7 new tests cover the git tag functionality.

## Verification

To verify the implementation works:

1. In a git repo with a tag matching the package version:
   ```
   $ tf doctor
   Version consistency:
   [ok] package.json version: 0.1.0
   [ok] Git tag matches: 0.1.0
   [ok] VERSION file matches: 0.1.0
   ```

2. In a git repo with a mismatched tag:
   ```
   $ tf doctor
   Version consistency:
   [ok] package.json version: 0.1.0
   [warn] Git tag (0.2.0) does not match package.json (0.1.0)
   ...
   ```

3. When not on a tagged commit, no git tag message appears (silent skip).
