# Review: pt-xu9u

## Overall Assessment
The retry-aware escalation addition is well-structured and clearly documented, and the opt-in default minimizes risk. However, there are a couple of internal inconsistencies (especially around attempt numbering) that would cause the workflow to mis-report attempt numbers and potentially escalate at the wrong time.

## Critical (must fix)
- `skills/tf-workflow/SKILL.md:137-143, 275-276, 436-437` - **Attempt numbering is inconsistent / likely off-by-one.** The Load Retry State algorithm sets `retryAttempt = retryCount + 1` for a BLOCKED prior run (line 141), but later artifacts/state write `attemptNumber: {retryAttempt + 1}` (line 436) and implementation template prints `Attempt: {retryAttempt + 1}` (line 275). With `retryCount` already incremented on a BLOCKED close, this double `+1` will cause second attempts to be labeled as 3, etc., and can shift the escalation curve (attempt 2 vs 3+).
- `skills/tf-workflow/SKILL.md:121-132` - **Config schema example is incorrect/incomplete.** The snippet under “Escalation config format” shows `{ "escalation": { ... } }` at the root, but elsewhere the documented/actual location is `workflow.escalation` (and settings.json uses `workflow.escalation`). This will mislead users into configuring the wrong JSON shape.

## Major (should fix)
- `skills/tf-workflow/SKILL.md:152, 334-339` - **“Base model resolution” is underspecified and can be interpreted incorrectly.** It states `agents.{role} → metaModels.{key}.model` (line 152), but the roles are not consistently named across the doc (`reviewerSecondOpinion` vs agent key `reviewer-second-opinion`). This is easy to mis-implement in any future automation and could lead to selecting the wrong base model.
- `skills/tf-workflow/SKILL.md:142` - **`maxRetries` comparison/semantics are unclear.** The algorithm warns when `retryAttempt >= maxRetries`, which means it will warn on the last allowed attempt (if maxRetries is intended as “maximum attempts”) rather than only when exceeding the limit. The doc should define whether `maxRetries` means “max BLOCKED attempts” vs “max total attempts”, and the inequality should match that.
- `skills/tf-workflow/SKILL.md:437` - **`startedAt` is referenced but not defined anywhere in the procedure.** The Close Ticket step writes `startedAt: "{start_timestamp}"`, but there is no earlier instruction to capture that timestamp (e.g., at the beginning of Re-Anchor/Implement). This makes the schema hard to follow and increases the chance of inconsistent state being written.

## Minor (nice to fix)
- `skills/tf-workflow/SKILL.md` and `.pi/skills/tf-workflow/SKILL.md` (entire file) - **Duplicated source-of-truth risk.** Maintaining two copies invites drift. If both are required by the tooling, consider adding a short note describing which is authoritative and how syncing is performed.
- `skills/tf-workflow/SKILL.md:162-168, 166` - **Severity count extraction regex is very permissive.** The pattern `(?:^|\s|[-*]\s*)...` can match unintended places in the document (especially for “Major/Minor” words in prose). Tightening it to match the Summary Statistics list items specifically would reduce false positives.

## Warnings (follow-up ticket)
- `skills/tf-workflow/SKILL.md:606-613` - **Concurrency is only documented, not enforced.** The “Parallel Worker Safety” section acknowledges race conditions when `ralph.parallelWorkers > 1`, but the workflow doesn’t specify a concrete mitigation beyond options. If parallel workers are ever enabled, this should become an implemented safeguard (locking or per-ticket worker assignment).

## Suggestions (follow-up ticket)
- `skills/tf-workflow/SKILL.md:135-190` - Add an explicit “invalid/legacy retry-state.json handling” policy (e.g., backup + reset, or strict fail). Right now it says “validate schema version” but doesn’t say what to do if validation fails.
- `skills/tf-workflow/SKILL.md:76-80, 86-93` - Provide a short concrete example of `--retry-reset` behavior (before/after file names) and clarify whether reset also resets `retryAttempt` to 0 even if close-summary indicates BLOCKED.

## Positive Notes
- `skills/tf-workflow/SKILL.md` - Good separation of concerns: Re-Anchor/Implement/Review/Fix/Close steps are clear and the escalation logic is isolated in a dedicated sub-procedure.
- `skills/tf-workflow/SKILL.md:556-604` - The escalation configuration is opt-in with sensible defaults (`enabled: false`, null = base), reducing risk of accidental behavior change.

## Summary Statistics
- Critical: 2
- Major: 4
- Minor: 2
- Warnings: 1
- Suggestions: 2
