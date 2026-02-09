# Implementation: pt-k2rk

## Summary
Completed inventory of current packaging structure and entrypoints for the `tf_cli → tf` namespace migration.

## Files Changed
No code changes - this is a documentation/analysis task. Created research artifact:
- `.tf/knowledge/tickets/pt-k2rk/research.md` - Full inventory analysis

## Key Findings

### 1. Console Script Entrypoint
```toml
[project.scripts]
tf = "tf_cli.cli:main"
```
Target: `tf_cli/cli.py::main()` function

### 2. Module Entrypoint
- `python -m tf_cli` → `tf_cli/__main__.py` → `cli.main()`

### 3. Critical Modules for Migration
| Priority | Module | Reason |
|----------|--------|--------|
| 1 | `cli.py` | Console script target - must move first |
| 2 | `version.py` | Imported by cli and __init__ |
| 3 | `__init__.py` | Re-exports ticket_factory - needs shim |
| 4 | `utils.py` | Shared utility functions |
| 5 | `ticket_loader.py` | Central dependency for 8+ modules |

### 4. No Import Cycles
The import graph is clean (DAG). No circular dependencies to untangle.

### 5. Migration Order Recommended
1. Create `tf/` package skeleton (pt-ce2e)
2. Move dispatcher to `tf/cli.py` with backwards-compat shim
3. Update console script entrypoint
4. Keep `tf_cli/` as re-export shim during transition
5. Update tests (pt-m06z)

## Acceptance Criteria Verification
- [x] Console script entrypoint identified: `tf_cli.cli:main`
- [x] Key modules identified: cli.py, version.py, ticket_loader.py, utils.py
- [x] Import cycles checked: None found

## Verification
Run these commands to verify the findings:
```bash
# Check console script entrypoint
grep -A1 "\[project.scripts\]" pyproject.toml

# Check module count in tf_cli
ls tf_cli/*.py | wc -l

# Check main imports
grep "^from tf_cli" tf_cli/*.py | cut -d: -f2 | sort | uniq -c | sort -rn | head -10
```
