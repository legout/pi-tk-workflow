# Implementation: ptw-7zri

## Summary
Optimized `normalize_version` function in `tf_cli/doctor_new.py` to use `version.startswith(("v", "V"))` instead of `version.lower().startswith("v")`.

## Files Changed
- `tf_cli/doctor_new.py` - Changed line 175: Replaced `version.lower().startswith("v")` with `version.startswith(("v", "V"))`

## Key Decisions
- Used tuple-based startswith: `version.startswith(("v", "V"))` is more direct than creating a lowercase copy of the string
- This is a micro-optimization that avoids allocating a temporary lowercase string
- The behavior is identical - both approaches strip leading 'v' or 'V' prefixes

## Tests Run
```bash
python3 -m pytest tests/test_doctor_version.py -v
```

Results: **38 passed, 0 failed**

All test cases covered:
- Plain versions ("1.2.3") - unchanged
- Lowercase v prefix ("v1.2.3") - stripped
- Uppercase V prefix ("V1.2.3") - stripped
- Empty strings - unchanged
- Prerelease versions with v prefix ("v1.0.0-alpha") - stripped
- Versions with v in middle ("v1.0.0v2") - only leading v stripped

## Verification
The change is functionally equivalent but more efficient:
- Old: Creates lowercase copy of string, then checks startswith
- New: Directly checks startswith against tuple of prefixes
