# Ralph Lessons Learned

## Patterns

## Gotchas

## Lesson from pt-7mvl (2026-02-09T00:15:16Z)

- Decision tickets need explicit "Decision" sections to unblock dependent work
- Analysis should evaluate alternatives against acceptance criteria explicitly
- Clear implementation guidance helps downstream tickets execute efficiently

## Lesson from pt-hpme (2026-02-09T16:47:00Z)

**Context**: When creating compatibility shims that replace existing functionality, the new implementation must maintain behavioral parity with the original.

**Lesson**: When moving version reading logic from `tf_cli/version.py` to `tf/__init__.py`, a simplified implementation broke edge cases (git tag fallback, multiple search paths). The reviewer correctly identified this as critical.

**Apply when**: Moving/copying utility functions between packages during refactoring. Always compare the new implementation against the original for:
- Fallback behavior consistency (e.g., "unknown" vs "0.0.0-dev")
- Edge case handling (permissions, encoding, missing files)
- Full fallback chain (not just the happy path)

**Pattern**: When creating a "canonical" version of existing code, copy the implementation exactly first, then refactor. Don't rewrite from scratch unless specifically required.

## Lesson from pt-tupn (2026-02-09T17:08:00Z)

**Context**: During namespace migration from `tf_cli` to `tf`, several modules were moved but import statements were not fully updated.

**Lesson**: After moving modules between packages, always run a comprehensive check for remaining imports to the old namespace. The `board_classifier.py` file was missed and still imported from `tf_cli.ticket_loader`, defeating the migration goal.

**Apply when**: Performing any namespace migration or package restructuring. Run verification commands like:
```bash
grep -r "from tf_cli" tf/ --include="*.py"
grep -r "import tf_cli" tf/ --include="*.py"
```

**Pattern**: Include a verification step in the migration checklist. Don't assume imports were updated just because files were copied.

## Lesson from pt-m06z (2026-02-09T18:15:00Z)

**Context**: When migrating test imports from `from tf_cli import X` to `from tf import X`, the implementation correctly updated imports but missed updating mock.patch() calls.

**Lesson**: mock.patch() must use the same path as the import namespace being used. When code uses `from tf import X`, patches must use `tf.X.function` not `tf_cli.X.function`. This is because mock.patch() must patch where the function is looked up at runtime, which matches the import path.

**Apply when**: Any test file migration that changes imports. Always search for and update mock.patch() calls to match the new import path. A common pattern:
```bash
# Find potential issues
grep -r "mock.patch.*tf_cli" tests/ --include="*.py"
```

**Pattern**: After importing changes, verify all mock.patch() paths use the same namespace as the import statements. This is a frequent source of test failures during namespace migrations.

## Lesson from abc-123 (2026-02-09T18:03:00Z)

**Context**: Running a Python module directly via `python -m package.module` can trigger a RuntimeWarning about the module being found in sys.modules after import of the package.

**Lesson**: The warning "'module' found in sys.modules after import of package 'package'" occurs when Python imports the module twice during `-m` execution. To fix this, add a `__main__.py` file to the package that imports and calls the CLI logic:

```python
# package/__main__.py
from __future__ import annotations

import sys

from package.module import main_function


def main() -> None:
    """CLI entry point."""
    # CLI logic here
    pass


if __name__ == "__main__":
    main()
```

Then use `python -m package` (without the module name) to avoid the warning.

**Apply when**: Creating CLI tools that can be run as modules. Always provide a `__main__.py` entry point for packages that expose CLI functionality.

**Pattern**: Keep `if __name__ == "__main__"` blocks in individual modules for backward compatibility, but prefer `python -m package` usage to avoid warnings.
