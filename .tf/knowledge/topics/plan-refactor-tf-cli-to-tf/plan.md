---
id: plan-refactor-tf-cli-to-tf
status: draft
last_updated: 2026-02-09
---

# Plan: Refactor Python package namespace from `tf_cli` → `tf`

## Summary

Align the Python package namespace with the user-facing CLI command (`tf`) by moving the canonical implementation from `tf_cli/` to a new top-level `tf/` package.

Do this in a backwards-compatible way by keeping `tf_cli` as a compatibility shim (re-exporting symbols / delegating entrypoints) for at least one release cycle, with an explicit deprecation strategy.

## Inputs / Related Topics

- Root Seed: [seed-refactor-restructure-the-python-cli](topics/seed-refactor-restructure-the-python-cli/seed.md)
- Session: seed-refactor-restructure-the-python-cli@2026-02-09T16-16-25Z
- Related Spikes:
  - (none yet)

## Requirements

- Canonical Python package becomes `tf`.
- `tf` CLI UX remains unchanged (console script continues to work).
- Provide `python -m tf ...` module execution (add `tf/__main__.py`).
- Preserve compatibility for existing `tf_cli.*` imports via a shim layer.
- Keep tests passing; update internal imports to prefer `tf.*`.
- Document the new canonical namespace and the deprecation timeline.

## Constraints

- Preserve minimum supported Python version (>= 3.9).
- Keep the change incremental and reviewable (avoid a “big bang” rename).
- Avoid breaking Ralph + TF workflow prompts/commands.
- Avoid noisy `DeprecationWarning` output in tests/CI by default.

## Assumptions

- Downstream users (if any) may import `tf_cli` directly.
- It’s acceptable to keep the shim for at least one release cycle.
- The project packaging is driven by `pyproject.toml`.

## Risks & Gaps

- **Import cycles / partial moves**: moving modules gradually can introduce circular imports.
  - Mitigation: move by vertical slice (entrypoints + shared utils) and keep adapters thin.
- **Entry point drift**: console scripts, `python -m ...`, and tests may diverge.
  - Mitigation: add explicit smoke tests for `python -m tf --help` and `tf --help`.
- **Deprecation noise**: warnings could break strict test environments.
  - Mitigation: only warn on explicit `tf_cli` imports (and potentially behind env var), add tests to assert warnings behavior.
- **Third-party integrations**: scripts may import `tf_cli` and pin behavior.
  - Mitigation: ensure shim re-exports are comprehensive for commonly imported modules.

## Work Plan (phases / tickets)

1. **Inventory + target namespace**
   - Decide what becomes public under `tf` (CLI entrypoints vs library surface).
   - Identify top-level modules in `tf_cli` that must move first.

2. **Introduce `tf/` package skeleton**
   - Create `tf/__init__.py` and `tf/__main__.py`.
   - Make `python -m tf --help` run the same CLI as `tf --help`.

3. **Move CLI entry + core wiring**
   - Relocate the CLI command dispatcher to `tf/`.
   - Update packaging/entrypoints as needed.

4. **Compatibility shim for `tf_cli`**
   - Keep `tf_cli/` package but convert modules to thin re-exports/delegators.
   - Add optional `DeprecationWarning` strategy (documented).

5. **Update imports + tests**
   - Update internal imports to `tf.*`.
   - Update tests to import `tf.*`.
   - Add dedicated tests that `import tf_cli` still works.

6. **Docs + release notes**
   - Update README/docs: canonical namespace is `tf`.
   - Add deprecation timeline and migration notes.

## Acceptance Criteria

- [ ] `tf --help` works.
- [ ] `python -m tf --help` works.
- [ ] All tests pass.
- [ ] Internal imports primarily use `tf.*`.
- [ ] `import tf_cli` continues to work (shim).
- [ ] Docs updated with migration guidance + deprecation policy.

## Open Questions

- What is the planned shim removal milestone (version/time)?
- Should warnings be emitted by default, or only when `TF_CLI_DEPRECATION_WARN=1` is set?
- Do we want to keep `tf_cli` as a package directory, or generate it at build time?

---

## Consultant Notes (Metis)

- 2026-02-09: Draft created from seed; no spikes attached yet. Consider a spike to inspect current packaging entrypoints and import graph before moving modules.

## Reviewer Notes (Momus)

- 2026-02-09: FAIL
  - Blockers:
    - (none yet — pending review)
  - Required changes:
    - (none yet — pending review)
