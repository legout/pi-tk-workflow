# Implementation: ptw-5wmr

## Summary
Added a lightweight version consistency check to `tf doctor` that detects version mismatches between `package.json` and an optional `VERSION` file.

## Files Changed
- `tf_cli/doctor_new.py` - Added version check functions and integrated into `run_doctor()`

## Key Decisions
1. **Source of truth**: `package.json` is treated as the canonical version source
2. **Extensible design**: Added `get_version_file_version()` for future VERSION file support
3. **Offline-safe**: No network calls, only local file reads
4. **Warning-only**: Does not fail the doctor check, just prints warnings
5. **Clear remediation**: Warning message includes fix instructions

## Implementation Details

### New Functions Added
- `get_package_version(project_root)` - Reads version from package.json
- `get_version_file_version(project_root)` - Reads version from VERSION file
- `check_version_consistency(project_root)` - Compares versions and prints warnings

### Check Behavior
- If no `package.json`: prints `[info] No package.json found, skipping version check`
- If `package.json` exists: prints `[ok] package.json version: X.Y.Z`
- If `VERSION` file exists and matches: prints `[ok] VERSION file matches`
- If `VERSION` file exists and mismatches: prints `[warn]` with remediation steps

## Tests Run
```bash
# Test 1: Normal case (no VERSION file)
$ python3 -m tf_cli.doctor_new
Version consistency:
[ok] package.json version: 0.1.0

# Test 2: VERSION file mismatch
$ echo "0.2.0" > VERSION && python3 -m tf_cli.doctor_new
Version consistency:
[ok] package.json version: 0.1.0
[warn] VERSION file (0.2.0) does not match package.json (0.1.0)
       To fix: update VERSION file to match package.json, or remove VERSION file
```

## Verification
The check:
- ✅ Runs offline (no network calls)
- ✅ Is safe (doesn't break workflows)
- ✅ Prints clear warnings with remediation
- ✅ Handles missing files gracefully
