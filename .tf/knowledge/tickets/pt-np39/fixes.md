# Fixes: pt-np39

## Critical Issues Fixed

### 1. tf_cli/new_cli.py
- Updated 13 imports from `*_new` to stable names (`agentsmd`, `backlog_ls`, `doctor`, `init`, `login`, `next`, `priority_reclassify`, `ralph`, `setup`, `sync`, `tags_suggest`, `track`, `update`)
- Updated 13 dispatch calls to use renamed modules
- The `tf new <command>` backward-compatibility namespace now works correctly

### 2. tf_cli/setup.py
- Fixed import of `login_new` → `login`
- Fixed call from `login_new.main([])` → `login.main([])`
- The `tf setup` command's "Configure API keys" option now works

### 3. tests/test_priority_reclassify.py
- Fixed import `priority_reclassify_new as pr` → `priority_reclassify as pr`
- Updated all `@patch` decorators from `tf_cli.priority_reclassify_new` → `tf_cli.priority_reclassify`

### 4. tests/test_doctor_version.py
- Fixed import `doctor_new` → `doctor`
- Updated docstring reference

### 5. tests/test_doctor_version_integration.py
- Fixed import `doctor_new` → `doctor`

### 6. tests/test_json_capture.py
- Fixed import `ralph_new` → `ralph`

### 7. tf_cli/component_classifier.py
- Fixed docstring reference `tags_suggest_new` → `tags_suggest`

## Test Results After Fixes

```bash
python -m pytest tests/ -v
```
Result: **579 passed**

## Files Changed During Fix Phase
- tf_cli/new_cli.py
- tf_cli/setup.py
- tests/test_priority_reclassify.py
- tests/test_doctor_version.py
- tests/test_doctor_version_integration.py
- tests/test_json_capture.py
- tf_cli/component_classifier.py
