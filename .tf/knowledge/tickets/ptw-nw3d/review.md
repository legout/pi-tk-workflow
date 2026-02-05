# Review: ptw-nw3d

## Critical (must fix)
- `tests/test_cli_version.py:1` - Tests import `get_version` from `tf_cli.cli` but the function has been moved to `tf_cli.version`. All mocks target wrong module paths (`tf_cli.cli.resolve_repo_root` doesn't exist, should mock `tf_cli.version._resolve_repo_root`). These tests will fail and need updating to import from the correct module and mock the new internal functions.

## Major (should fix)
- `tf_cli/version.py:15-18` - Module docstring documents fallback order as: 1) repo root, 2) module-relative, 3) "unknown". But the actual code has a 3rd fallback at lines 64-67 checking `cwd / "VERSION"` which is not documented. Update docstring to include the 3rd fallback or remove the undocumented fallback.
- `tf_cli/version.py:51-57` - `_resolve_repo_root()` searches from `Path.cwd()` which could incorrectly find a different project's version if run from within another ticketflow-based project that has `.tf/` directory and VERSION file. Consider starting the search from `Path(__file__)` instead to anchor to the actual installation.

## Minor (nice to fix)
- `tf_cli/_version.py:1-7` - Deprecation note is only a comment; no actual runtime warning emitted. Consider adding `warnings.warn("tf_cli._version is deprecated, use tf_cli.version", DeprecationWarning, stacklevel=2)` to actively inform users.
- `tf_cli/new_cli.py:53` - Handles `-V` flag but `tf_cli/cli.py` does not. The two CLIs have inconsistent version flag support (`-V` only works in new_cli). Consider adding `-V` support to cli.py for consistency.
- `tf_cli/version.py:44` - Redundant exception handling: `IOError` is an alias for `OSError` in Python 3.3+. Can simplify to just `except OSError:`.
- `tf_cli/version.py:88` - Comment says "check if tf_cli is directly in cwd" but the code checks `cwd / "VERSION"`, not `cwd / "tf_cli"`. Update comment to accurately reflect the behavior.

## Warnings (follow-up ticket)
- `tf_cli/version.py:72-76` - The third fallback to cwd/VERSION could be a security concern if a malicious VERSION file is placed in a directory where the CLI is executed. Consider whether this fallback is necessary or if it should be removed.

## Suggestions (follow-up ticket)
- `tf_cli/version.py` - Consider caching the version lookup result in a module-level variable to avoid file I/O on every call when `get_version()` is called multiple times in the same process. The `__version__` constant provides this for direct access, but dynamic callers pay the cost.
- Add unit tests specifically for `tf_cli/version.py` to cover all three fallback scenarios and edge cases (permission errors, malformed VERSION files, etc.).
- `tests/test_cli_version.py:37,46` - Tests mock `Path.is_file` globally which is overly broad; consider mocking only the specific file existence checks or using `tmp_path` fixtures more directly.
- `tf_cli/version.py:91` - Consider removing the cwd/VERSION fallback (3rd option). It's unclear when this would be useful - if the user has a VERSION file in cwd but isn't in the repo and the package is installed, reading an arbitrary VERSION file could be misleading. The two primary fallbacks (repo root and module relative) should cover all legitimate use cases.

## Positive Notes
- Excellent module-level docstring explaining the problem and solution approach
- Clean separation of concerns with private helper functions `_resolve_repo_root()` and `_read_version_file()`
- Good backward compatibility strategy keeping `_version.py` as a thin wrapper
- Proper type hints throughout (`Optional[Path]`, `-> str`)
- Both `get_version()` (dynamic) and `__version__` (cached) exported for different use cases
- Version stripping handles whitespace and newlines correctly
- `new_cli.py` properly integrated with `--version` support using the centralized module
- Implementation fully satisfies all acceptance criteria from the ticket

## Summary Statistics
- Critical: 1
- Major: 2
- Minor: 4
- Warnings: 1
- Suggestions: 4
