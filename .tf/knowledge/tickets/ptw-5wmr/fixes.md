# Fixes: ptw-5wmr

## Major Issues Fixed

### 1. Inconsistent JSON parsing pattern (doctor_new.py:170-177)
**Issue**: `get_package_version()` was reimplementing JSON parsing logic instead of using the existing `read_json()` helper.

**Fix**: Refactored to use `read_json(package_file)` instead of `json.loads(package_file.read_text(...))`.

### 2. No validation for falsy version values (doctor_new.py:176)
**Issue**: If package.json had `"version": ""` or `"version": null`, the code would print `[ok] package.json version:` which is confusing.

**Fix**: Added validation to ensure version is a non-empty string:
```python
if not isinstance(version, str) or not version.strip():
    return None
return version.strip()
```

## Minor Issues Fixed

### 3. Misleading info message for missing version field
**Issue**: The message "No package.json found" was misleading when the file exists but has no version field.

**Fix**: Split the check to distinguish between:
- "No package.json found, skipping version check" (file doesn't exist)
- "package.json found but version field is missing or invalid" (file exists but no valid version)

### 4. Empty VERSION file handling
**Issue**: VERSION file with empty/whitespace-only content would pass `is not None` check but produce confusing output.

**Fix**: Added validation in `get_version_file_version()`:
```python
content = version_file.read_text(encoding="utf-8").strip()
return content if content else None
```

### 5. Type safety for version values
**Issue**: `package_data.get("version")` could return non-string types (e.g., numbers).

**Fix**: Added `isinstance(version, str)` check before returning.

## Verification

All edge cases tested:
- ✅ Normal case: `[ok] package.json version: 0.1.0`
- ✅ VERSION mismatch: `[warn] VERSION file (0.2.0) does not match package.json (0.1.0)`
- ✅ Empty VERSION file: Treated as non-existent (no warning)
- ✅ Missing version field: `[info] package.json found but version field is missing or invalid`
