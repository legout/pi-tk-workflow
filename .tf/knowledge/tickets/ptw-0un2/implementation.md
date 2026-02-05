# Implementation: ptw-0un2

## Summary
Added pytest coverage configuration to pyproject.toml with a minimum threshold of 4%.

## Files Changed
- `pyproject.toml` - Added comprehensive pytest and coverage configuration sections

## Configuration Added

### [tool.pytest.ini_options]
- `testpaths = ["tests"]` - Test directory location
- `python_files` patterns for test discovery
- `addopts` with `--strict-markers`, `--disable-warnings`, `-v`
- Custom markers for slow and integration tests

### [tool.coverage.run]
- `source = ["tf_cli"]` - Source package to measure
- `omit` - Excludes tests, cache, and entry point
- `branch = true` - Enable branch coverage

### [tool.coverage.report]
- `exclude_lines` - Common patterns to exclude (pragmas, repr, TYPE_CHECKING)
- `show_missing = true` - Show line numbers for missing coverage
- `precision = 1` - One decimal place for percentages
- `fail_under = 4` - Minimum 4% coverage threshold (reflects current project state)

## Key Decisions
- Used pyproject.toml (PEP 621 standard) instead of separate pytest.ini or .coveragerc
- Set threshold to 4% (current coverage is 4.1%) to reflect actual project state
- Threshold should be increased as more tests are added
- Branch coverage enabled for more thorough measurement

## Tests Run
```bash
python3 -m pytest --cov=tf_cli --cov-report=term-missing tests/
```
Result: 38 passed, coverage 4.09% meets threshold of 4.0%

## Verification
Run tests with coverage: `pytest --cov=tf_cli tests/`
Coverage report shows: Required test coverage of 4.0% reached. Total coverage: 4.09%
