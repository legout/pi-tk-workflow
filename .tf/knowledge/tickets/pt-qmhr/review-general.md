# Review: pt-qmhr

## Overall Assessment
The design makes a strong architectural call by keeping retry/escalation decisions centralized in a single orchestrator, which is the right direction for preserving global retry semantics. The document is clear and implementation-oriented, but there are a couple of contract inconsistencies that could cause retry-state bugs and user-visible flag regressions during migration. Tightening those now will reduce rework in follow-up implementation tickets.

## Critical (must fix)
- No issues found.

## Major (should fix)
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:77`, `.tf/knowledge/tickets/pt-qmhr/implementation.md:99`, `.tf/knowledge/tickets/pt-qmhr/implementation.md:119` - Retry-state lifecycle is internally inconsistent: state is defined as written by `/tf (close)` only, but mid-chain failures also "mark retry-state as error." Without an explicit schema/update rule for where `error` lives (attempt vs top-level), resume logic can misclassify attempts or reject state (`docs/retries-and-escalation.md:280` top-level status does not include `error`).
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:107` vs `.pi/prompts/tf.md:19` - Flag handling contract is incomplete relative to current `/tf` behavior. The design table omits currently documented flags/aliases (`--dry-run`, `--no-clarify`, `--create-followups`, `--simplify-tickets`, `--final-review-loop`), creating a regression risk where existing workflows silently stop working.

## Minor (nice to fix)
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:65` - Escalation context example includes fixer/worker but not reviewer-second-opinion, which is part of the configured escalation curve. This can lead to incomplete implementation of attempt 3+ behavior.
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:90` and `.tf/knowledge/tickets/pt-qmhr/implementation.md:75` - `chain-context.json` is introduced as a mechanism but not listed in the state/artifact table. Missing ownership/retention guidance makes debugging and resume behavior harder.

## Warnings (follow-up ticket)
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:57` - The design does not explicitly carry forward concurrency safeguards for retry-state writes (lock or forced disable), even though existing docs call out races when parallel workers > 1 (`docs/retries-and-escalation.md:165`). If parallelism expands, this can cause lost updates.

## Suggestions (follow-up ticket)
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:184` - Expand verification beyond happy-path retries: add explicit tests for mid-chain failure/resume, corrupted `retry-state.json`, and `--retry-reset` during a previously errored attempt.
- `.tf/knowledge/tickets/pt-qmhr/implementation.md:109` - Define precedence when conflicting flags are present (e.g., `--no-research` + `--with-research`) so orchestrator behavior is deterministic.

## Positive Notes
- The decision to keep retry/escalation logic centralized is well justified and aligns with atomic state-management requirements.
- The architecture section is easy to implement from and keeps artifact compatibility front-and-center.
- The design explicitly addresses mid-chain failure behavior and quality gate integration, which were key acceptance criteria.

## Summary Statistics
- Critical: 0
- Major: 2
- Minor: 2
- Warnings: 1
- Suggestions: 2
