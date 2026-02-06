# Review: pt-x2v0

## Overall Assessment
The new test suite is well-structured (fixtures + class grouping) and gives broad coverage of the session lifecycle APIs. However, there are a couple of correctness/coverage gaps and some time-based assumptions that can make the suite flaky and/or give a false sense of coverage.

## Critical (must fix)
- `tests/test_session_store.py:1-11` - The module docstring claims verification of “No duplicate lines in sources.md”, but there are no assertions that read/write any `sources.md` content anywhere in this file. If the ticket’s acceptance criteria includes `sources.md` idempotency, this is currently untested and the test description is misleading.
- `tf_cli/session_store.py:87-99` + `tf_cli/session_store.py:221-225` - `generate_session_id()` only has 1-second resolution. Creating two sessions for the same seed within the same second will produce the same `session_id`, and `archive_session()` will then overwrite `sessions/{session_id}.json`, causing silent data loss. The plan/spec for “multiple sessions per seed” implies uniqueness that this implementation does not guarantee.

## Major (should fix)
- `tests/test_session_store.py:456-470` - `test_find_latest_session_for_seed` creates two sessions for the same seed without supplying distinct timestamps. If both calls happen in the same second, they can produce identical `session_id`s (see critical issue above) and the second archive will overwrite the first, making the test flaky/non-deterministic.
- `tests/test_session_store.py:115-124`, `tests/test_session_store.py:138-149`, `tests/test_session_store.py:533-546` - Several tests rely on wall-clock timing windows ("within 60s" / "within 5s"). On slow CI, under heavy load, or with clock adjustments, these can become flaky. Prefer freezing time (monkeypatch) or asserting monotonic properties (e.g., timestamp changed and parses as ISO-8601) with a larger tolerance.
- `tf_cli/session_store.py:50-74` - `_atomic_write_json()` uses `os.rename()` for the final move. On Windows, `os.rename()` can fail when the destination exists; `os.replace()` is the usual cross-platform atomic “replace” primitive. If this project targets Windows at all, this is a portability bug.

## Minor (nice to fix)
- `tests/test_session_store.py:16` - Unused import `os`.
- `tests/test_session_store.py:564-574` - `test_concurrent_reads_dont_see_partial_writes` doesn’t actually create contention/partial-write scenarios; it’s effectively another “save then load returns valid data” test. Either strengthen it (e.g., monkeypatch `_atomic_write_json` to pause mid-write) or rename it to reflect what it checks.

## Warnings (follow-up ticket)
- `tf_cli/session_store.py:32-48` - `_get_knowledge_dir()` claims “env/config” support in the docstring, but only implements an env var and cwd default. Elsewhere in the codebase (`tf_cli.kb_helpers.resolve_knowledge_dir`) config-based `workflow.knowledgeDir` resolution exists. This inconsistency can lead to commands reading/writing session state in the wrong directory depending on which helper they use.

## Suggestions (follow-up ticket)
- `tests/test_session_store.py` - Add explicit tests for knowledge-dir resolution behavior (explicit arg vs `TF_KNOWLEDGE_DIR` vs cwd default) to prevent drift.
- `tf_cli/session_store.py:87-99` - Consider including higher-resolution timestamps (e.g., milliseconds) or a monotonic/random suffix in `session_id` to guarantee uniqueness, and add a regression test for “two sessions in same second don’t overwrite”.

## Positive Notes
- `tests/test_session_store.py` - Good use of temp directories to avoid touching real user state.
- `tests/test_session_store.py:226-340` - Lifecycle coverage is easy to read and matches the intended UX (activate → archive/switch → resume → complete/deactivate).
- `tests/test_session_store.py:342-390` - Idempotency and ticket dedupe behavior are tested explicitly.

## Summary Statistics
- Critical: 2
- Major: 3
- Minor: 2
- Warnings: 1
- Suggestions: 2
