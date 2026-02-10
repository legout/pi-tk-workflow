# Fixes: pt-xu9u

## Issues Fixed

### Critical Fixes

1. **Attempt Number Consistency** (reviewer-general, reviewer-second-opinion, reviewer-spec-audit)
   - Changed from `retryAttempt` (0-indexed) to `attemptNumber` (1-indexed) throughout
   - Escalation curve now uses clear 1-based indexing: Attempt 1 = base, Attempt 2 = fixer escalated, Attempt 3+ = full escalation
   - Fixed implementation template to use `{attemptNumber}` instead of `{retryAttempt + 1}`
   - Fixed retry-state.json write to use `{attemptNumber}` instead of `{retryAttempt + 1}`

2. **Config Schema Example** (reviewer-general, reviewer-second-opinion)
   - Fixed JSON example to show `workflow.escalation` nested inside `workflow` object
   - Before: `{ "escalation": { ... } }`
   - After: `{ "workflow": { "escalation": { ... } } }`

3. **Detection Algorithm Missing has_items Fallback** (reviewer-spec-audit)
   - Added `has_items` check to fallback detection in review.md
   - If summary stats are missing but bullet items exist, count = 1 (indicating issues present)
   - Added section boundary detection to accurately count items per severity section

4. **Missing qualityGate.counts in BLOCKED Case** (reviewer-spec-audit)
   - Added explicit severity count extraction algorithm to Close Ticket procedure
   - `blocked_counts` now populated with actual failOn severity counts when BLOCKED
   - Shows how to extract counts from review.md using regex

### Major Fixes

5. **Base Model Resolution Ambiguity** (reviewer-general, reviewer-second-opinion)
   - Clarified base model resolution: `agents.{role}` → meta-model key → `metaModels.{key}.model`
   - Added explicit note about kebab-case vs camelCase mapping in Load Retry State

6. **maxRetries Semantics** (reviewer-general, reviewer-second-opinion)
   - Clarified that `maxRetries` means "maximum BLOCKED attempts" not total attempts
   - Comparison now checks `retryCount >= maxRetries` after incrementing

7. **Missing Ralph Skip Logic** (reviewer-spec-audit)
   - Added "Check Skip Conditions" subsection to Ralph Integration procedure
   - Skip tickets with `status: blocked` and `retryCount >= maxRetries`
   - Log skip decision with ticket ID and retry count

8. **Missing Parallel Worker Safety** (reviewer-spec-audit)
   - Added "Parallel Worker Safety" subsection to Retry Escalation section
   - Documents Option A (file locking with filelock) and Option B (disable retry logic)
   - Default behavior: disable retry logic when `parallelWorkers > 1` without locking

9. **No Atomic Write for retry-state.json** (reviewer-spec-audit)
   - Added atomic write procedure: write to temp file, then `os.replace()` for atomic rename
   - Prevents corruption from mid-write crashes

10. **Model Escalation in Parallel Reviews** (reviewer-general)
    - Added back model escalation note for reviewer-second-opinion
    - Documents how escalated model is passed to subagent

## Files Changed

- `.pi/skills/tf-workflow/SKILL.md` - All fixes applied

## Verification

- Validated SKILL.md markdown structure
- Verified all `{attemptNumber}` references are consistent
- Confirmed atomic write pattern is correct Python
- Checked that escalation curve logic matches specification

## Remaining Items (Follow-up Tickets)

The following items from review were noted but not fixed in this ticket (as they belong to follow-up work or pt-7lrp):

- Post-fix re-review (mandatory per plan) - requires new ticket
- Ralph tk ready filtering for blocked tickets - requires Ralph changes
- Detection algorithm unit tests - belongs to pt-7lrp
- Invalid/legacy retry-state.json handling policy - can be added later
- End-to-end state transition examples - documentation enhancement
