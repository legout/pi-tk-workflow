# Review (Spec Audit): pt-xu9u

## Overall Assessment
The retry-aware escalation behavior is documented in the `tf-workflow` skill and broadly matches the intended escalation curve (attempt 2 escalates fixer; attempt 3+ escalates fixer + reviewer-second-opinion + optional worker). However, the repository contains two divergent versions of the `tf-workflow` skill with inconsistent attempt/counter semantics, and the `/tf` prompt documentation does not expose the new retry/reset and retry-state artifacts. These gaps make the workflow’s retry attempt computation and auditability unreliable.

## Critical (must fix)
- `skills/tf-workflow/SKILL.md:135-151, 275-276, 436-437` - Attempt numbering is internally inconsistent and likely off-by-one. The Load Retry State algorithm sets `retryAttempt = retryCount + 1` (line 141) but later records `Attempt: {retryAttempt + 1}` in `implementation.md` (line 275) and writes `attemptNumber: {retryAttempt + 1}` to `retry-state.json` (line 436). This can record attempt 3 on the first retry (attempt 2), violating the requirement that the retry attempt number be correctly recorded in artifacts/logs.
- `skills/tf-workflow/SKILL.md` vs `.pi/skills/tf-workflow/SKILL.md` - The two skill copies are not synced and differ materially (e.g., retry-state algorithm and review parsing). This means `/tf` behavior depends on which copy is used, undermining the ticket’s requirement to “teach the /tf workflow” deterministically.

## Major (should fix)
- `.pi/skills/tf-workflow/SKILL.md:96-99, 137-160, 213` - The Re-Anchor step says to store `retryAttempt` (line 99) but the algorithm computes `attemptNumber` (lines 139-156) and the “Output” still claims it sets `retryAttempt` (line 213). This inconsistency makes it unclear which variable downstream phases should use, and risks incorrect attempt/audit recording.
- `.pi/skills/tf-workflow/SKILL.md:143-146` - The algorithm increments `retryCount` at Re-Anchor (`retryCount = retryCount + 1`) when the last attempt was BLOCKED. The spec schema defines `retryCount` as the number of BLOCKED attempts already recorded; incrementing it at workflow start (and again on BLOCKED close) risks double-counting and premature `maxRetries` exhaustion.
- `.pi/prompts/tf.md:18-39` - `/tf` user-facing flags do not include `--retry-reset` even though the workflow skill now supports it (required by the approved plan’s “Manual /tf behavior” decision). This reduces discoverability of the intended manual reset behavior.

## Minor (nice to fix)
- `skills/tf-workflow/SKILL.md:118-133` - The escalation config example omits the `workflow` wrapper and shows `{ "escalation": ... }`, which does not match the actual settings structure (`workflow.escalation`) and the plan/spec. This can cause misconfiguration.
- `.pi/prompts/tf.md:56-68` - Output artifacts list does not mention `retry-state.json`, despite the ticket requiring attempt/model escalation auditability and the skill now producing this artifact.
- `skills/tf-workflow/SKILL.md:276` / `.pi/skills/tf-workflow/SKILL.md:299` - The implementation template uses `reviewer-second=...` rather than `reviewer-second-opinion` (role name) or `reviewerSecondOpinion` (config key). This is cosmetic but hurts traceability.

## Warnings (follow-up ticket)
- `skills/tf-workflow/SKILL.md:141-143` and `.pi/skills/tf-workflow/SKILL.md:146` - “Max retries exceeded” is only logged as a warning; the plan calls for bounded retries and a clear blocked outcome when exceeded (likely addressed in Ralph integration / selection logic, but not enforced here).
- `.pi/skills/tf-workflow/SKILL.md:556+` (Ralph Integration section) - Ralph progress logging does not include retry attempt number or escalation decisions, which the plan calls out for auditability. This likely belongs in the Ralph integration ticket, but is still a spec-aligned gap.

## Suggestions (follow-up ticket)
- Consider consolidating the skill source of truth (either `skills/` or `.pi/skills/`) and adding a CI check to prevent drift, since this ticket’s behavior is entirely defined by documentation/skill text.
- Add a small example snippet in `/tf` prompt or docs showing how to inspect retry history (e.g., `cat .tf/knowledge/tickets/<id>/retry-state.json`) and how to reset (`/tf <id> --retry-reset`).

## Positive Notes
- The skill documents the intended escalation curve (attempt 2 escalates fixer; attempt 3+ escalates fixer + reviewer-second-opinion + optional worker) and integrates model switching points in Implement / Parallel Reviews / Fix.
- The retry state artifact location matches the approved plan and pt-te9b spec (`.tf/knowledge/tickets/<id>/retry-state.json`).

## Summary Statistics
- Critical: 2
- Major: 3
- Minor: 3
- Warnings: 2
- Suggestions: 2

## Spec Coverage
- Spec/plan sources consulted: 
  - `tk show pt-xu9u` (Acceptance Criteria + Constraints)
  - `.tf/knowledge/topics/plan-retry-logic-quality-gate-blocked/plan.md` (approved plan)
  - `.tf/knowledge/tickets/pt-te9b/retry-state-spec.md` (retry-state schema + integration points)
  - `.tf/config/settings.json` (current `workflow.escalation` defaults)
- Missing specs: none
