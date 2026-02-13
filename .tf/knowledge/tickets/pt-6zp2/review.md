# Review: pt-6zp2

## Overall Assessment
The new tests add direct coverage for fixer meta-model selection and meet all acceptance criteria. However, the escalation tests have integration gaps (they don't exercise the actual config-to-model resolution pipeline) and a subtle off-by-one error in attempt number simulation. Additionally, a pre-existing bug in worker role escalation fallback was identified. The tests pass but require strengthening to provide true regression protection.

## Critical (must fix)
None within the scope of this ticket's changes. (Note: A pre-existing bug in `tf/retry_state.py` worker escalation fallback was flagged as a separate follow-up.)

## Major (should fix)
- `tests/test_sync.py:218-271` – The three escalation tests (`test_escalation_overrides_fixer_model`, `test_escalation_fallback_to_base_when_no_override`, `test_escalation_disabled_uses_base_model`) do not integrate with `sync.resolve_meta_model`. They pass a hand-crafted `base_models` dict directly to `RetryState.resolve_escalation`, bypassing the actual meta-model lookup and fallback logic. This means regressions in configuration resolution would not be caught. Please derive `base_models` from a real config via `sync.resolve_meta_model` or load through the full pipeline.
- `tests/test_sync.py:218` and `:243` – The escalation tests create a `RetryState`, start attempt 2, and then call `resolve_escalation()` without `next_attempt_number`. The method calculates `attempt = self.get_attempt_number() + 1`, yielding 3 instead of 2. This off-by-one error means the tests are not verifying the exact boundary condition they intend. Either avoid starting the next attempt before resolving, or pass `next_attempt_number` explicitly.
- `tests/test_sync.py:259` – While not strictly required by AC, adding a test for the scenario where escalation is enabled but `attempt = 1` would close a small coverage gap (the early return path in `resolve_escalation` is currently only exercised implicitly).

## Minor (nice to fix)
- `tests/test_sync.py:182` – `test_fixer_resolves_to_general_when_configured` uses an alternative agent name `my_fixer` to avoid resolution ambiguity. The comment explains, but the test could be made more direct by instead testing the exact configuration `agents.fixer="general"` with `metaModels.fixer` absent (see Suggestions).
- `tests/test_sync.py:259` – Docstring says "uses base model" but the assertion checks `result.fixer is None`, which is technically correct for the escalation API but potentially misleading; consider clarifying or adjusting wording.

## Warnings (follow-up ticket)
- `tf/retry_state.py:247` – Worker escalation does not fall back to the base model when no explicit override is configured. The fixer and reviewerSecondOpinion roles use `models_config.get(role) or base_models.get(role)`, but worker only sets if an override exists. This violates the documented escalation contract and could lead to `None` worker model on retries even when a base worker model is defined.
- Consider adding a dedicated ticket to audit and unify escalation fallback behavior across all roles.

## Suggestions (follow-up ticket)
- `tests/test_sync.py:199` – Add an explicit backward-compatibility test for the real `fixer` agent: config with `agents.fixer="general"` and no `metaModels.fixer`, asserting that `sync.resolve_meta_model(config, "fixer")` returns `metaModels.general`. This would increase confidence for the exact configuration users deploy.
- `tests/test_sync.py:218` – Refactor the escalation tests to derive `base_models` from `sync.resolve_meta_model` on a test config, ensuring the entire resolution chain is covered.
- `tests/test_sync.py:218` – Add a test verifying that on attempt 3+, `reviewerSecondOpinion` escalation applies (and does not apply on attempt 2).
- `tests/test_sync.py:218` – Add a test for worker escalation on attempt 3+ with and without an explicit override, verifying fallback to base.
- Consider splitting the large `TestFixerMetaModelSelection` class into sub-classes (e.g., `TestBaseResolution`, `TestEscalation`) for maintainability.

## Positive Notes
- The test class is well-organized, with clear docstrings linking each test to acceptance criteria.
- All new tests pass and cover the core fixer meta-model selection scenarios (presence, fallback, backward compat via `general`).
- The fallback behavior for missing meta-models (literal model ID) is correctly captured and documented.
- The implementation does not break existing `tests/test_sync.py` tests; full module suite remains green (25 passed).
- Good use of fixtures and realistic config structures that mirror user scenarios.

## Summary Statistics
- Critical: 0
- Major: 3
- Minor: 2
- Warnings: 2
- Suggestions: 4
