# Review (Second Opinion): pt-xu9u

## Overall Assessment
The update is thorough and reads like a complete operating procedure for retry-aware escalation, including state schema, artifact locations, and integration points across phases. However, there are a couple of internal consistency issues (attempt numbering/config shape) that would likely cause incorrect retry attempt reporting and misconfiguration if someone follows the doc literally.

## Critical (must fix)
- `skills/tf-workflow/SKILL.md:135-143, 274-276, 434-452` - **Off-by-one / inconsistent attempt numbering across `retryAttempt`, `retryCount`, and persisted `attemptNumber`.** The skill states `retryAttempt` is “0 for fresh, 1+ for retries” (Re-Anchor step 4), but then sets `retryAttempt = retryCount + 1` on blocked (line 141) and later writes `Attempt: {retryAttempt + 1}` in implementation.md (line 275) and `attemptNumber: {retryAttempt + 1}` in retry-state.json (line 436). Example failure: after first BLOCKED run, `retryCount` becomes 1 (line 457); next run sets `retryAttempt = 2` → implementation prints attempt 3 and state writes attemptNumber 3, even though this is the 2nd attempt. This will confuse escalation curve selection and any downstream tooling reading `attemptNumber`.

## Major (should fix)
- `skills/tf-workflow/SKILL.md:118-133` - **Escalation config example has the wrong JSON shape.** The document says `workflow.escalation.enabled` must be true (line 119), but the example block shows `{ "escalation": { ... } }` (lines 122-132) instead of `{ "workflow": { "escalation": { ... }}}`. Following the example would lead to escalation never activating.
- `skills/tf-workflow/SKILL.md:146-152` - **“Base model resolution: `agents.{role}`” is ambiguous/wrong for this repo’s actual keys.** In `.tf/config/settings.json`, agent keys are `fixer`, `worker`, and `reviewer-second-opinion` (kebab-case) while the escalation override field is `reviewerSecondOpinion` (camelCase). The doc should explicitly map roles to config keys (e.g., `agents.reviewer-second-opinion`) to avoid incorrect lookups.
- `skills/tf-workflow/SKILL.md:140-154` - **“If `status == "blocked"` or last attempt was BLOCKED” is underspecified.** The doc includes detection algorithms (lines 154+), but the Load Retry State algorithm doesn’t clearly state whether the “last attempt was BLOCKED” comes from `retry-state.json`, `close-summary.md`, or `review.md`, nor how conflicts are resolved.
- `skills/tf-workflow/SKILL.md:173-187` - **Fallback BLOCKED detection for `review.md` is fragile** because it keys off the presence of per-severity sections (header regex) before extracting counts. If review merging ever outputs only “Summary Statistics” (or formats section titles differently), this fallback will incorrectly treat a blocked review as not blocked.

## Minor (nice to fix)
- `skills/tf-workflow/SKILL.md:146-150` - The escalation table labels “Attempt 1 (or 0)”, which mixes 0-based and 1-based terminology in a way that invites the off-by-one bug above. Consider choosing one convention and sticking to it end-to-end (state, display, escalation selection).
- `skills/tf-workflow/SKILL.md:142` - The `retryAttempt >= maxRetries` warning is ambiguous: is `maxRetries` intended to cap total attempts, or number of retries after the first attempt, or number of BLOCKED closes? The text says “Maximum BLOCKED attempts” elsewhere; the comparison should match that definition.

## Warnings (follow-up ticket)
- `skills/tf-workflow/SKILL.md:566-572` - The doc notes retry logic assumes `ralph.parallelWorkers: 1` and suggests locking or disabling retry logic for parallelism. If parallel workers are ever enabled in practice, lack of a concrete locking/atomic-update procedure for `retry-state.json` could cause race conditions and corrupted state.

## Suggestions (follow-up ticket)
- `skills/tf-workflow/SKILL.md:114-154, 412-459` - Consider adding a small, explicit pseudo-code example for the end-to-end state transitions (initial → blocked → retry → closed) showing `retryCount`, `retryAttempt`, and `attemptNumber` values at each step. This would make it much easier to validate the logic and prevent future drift.
- `skills/tf-workflow/SKILL.md:421-458` - Consider clarifying whether `retry-state.json` should be written even when escalation is disabled (for observability), or only when enabled (current text says “if escalation enabled”). If only written when enabled, the Load Retry State section could explicitly say it is a no-op when disabled.

## Positive Notes
- `skills/tf-workflow/SKILL.md` - Good separation of phases and clear “artifact must exist” rules, especially for research.md.
- The escalation curve is clearly described, and the doc attempts to keep model diversity in parallel reviews while still allowing escalation.
- Syncing both `skills/tf-workflow/SKILL.md` and `.pi/skills/tf-workflow/SKILL.md` avoids divergence between local and packaged skill locations.

## Summary Statistics
- Critical: 1
- Major: 4
- Minor: 2
- Warnings: 1
- Suggestions: 2
