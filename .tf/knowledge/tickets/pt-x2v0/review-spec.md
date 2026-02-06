# Review (Spec Audit): pt-x2v0

## Overall Assessment
The ticket’s core lifecycle and session-JSON idempotency behaviors are covered with pytest unit tests and they run in temp directories without network access. However, one explicit acceptance criterion (“no duplicate lines in `sources.md`”) is not actually tested anywhere, and the “resume latest” behavior is only partially exercised.

## Critical (must fix)
- `tests/test_session_store.py:1-11,342-390` - Acceptance criteria requires verifying “no duplicate lines in `sources.md`”, but the test suite contains only comments/docstrings mentioning `sources.md` and **no assertions** that read/modify/validate any `sources.md` content. This is a direct miss of the ticket’s idempotency requirement beyond session JSON.

## Major (should fix)
- `tests/test_session_store.py:281-303` - The test named “resume latest session” resumes a specific archived session by explicit `session_id` (the first session) rather than validating *latest* selection semantics (e.g., resuming by seed-id chooses the newest archived session). This only partially satisfies the “resume latest” acceptance criterion.
- `tests/test_session_store.py:456-471` - `test_find_latest_session_for_seed` does not assert that *multiple* archived sessions exist on disk for the seed before selecting the latest. Because `create_session("seed-test")` uses second-level timestamps for `session_id`, two sessions created within the same second can share the same `session_id` and overwrite the same archive file, making the test pass without actually exercising “choose latest among multiple sessions”.

## Minor (nice to fix)
- `tests/test_session_store.py:15-20` - Unused imports (`os`) add noise; not a spec violation, but hurts maintainability of the test suite.

## Warnings (follow-up ticket)
- `tf_cli/session_store.py` (module scope) - The plan/spec for planning sessions (referenced by this ticket) includes idempotent cross-linking in `sources.md`, but there is no corresponding implementation surfaced in code here. If `sources.md` updates are performed by agent/prompt instructions rather than code, unit-testing dedupe may require a dedicated helper function or an integration-test harness. Consider clarifying where `sources.md` linking logic lives.

## Suggestions (follow-up ticket)
- `tests/test_session_store.py` - Add a focused test that mimics a “cross-link append if missing” helper (or whichever module owns this behavior) to concretely verify `sources.md` line dedupe, including repeated runs.

## Positive Notes
- `tests/test_session_store.py:226-340` - Lifecycle coverage exists for seed activation, archive+switch, spike attach (including no-active-session case), and backlog completion/deactivation.
- Tests use temp dirs (`tempfile.TemporaryDirectory`) and run quickly under pytest.

## Summary Statistics
- Critical: 1
- Major: 2
- Minor: 1
- Warnings: 1
- Suggestions: 1

## Spec Coverage
- Spec/plan sources consulted: `tk show pt-x2v0`, `.tf/knowledge/topics/plan-auto-planning-sessions-linkage/plan.md`
- Missing specs: none
