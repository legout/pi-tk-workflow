# Review: pt-xu9u

## Critical (must fix)

- **Attempt numbering is inconsistent / off-by-one** (reviewer-general, reviewer-second-opinion, reviewer-spec-audit)
  - The Load Retry State algorithm sets `retryAttempt = retryCount + 1` for BLOCKED prior runs, but then artifacts write `attemptNumber: {retryAttempt + 1}` and implementation.md prints `Attempt: {retryAttempt + 1}`. With `retryCount` already incremented on BLOCKED close, this double +1 causes second attempts to be labeled as 3, shifting the escalation curve.
  - Files: `SKILL.md` Load Retry State, Close Ticket, and implementation template sections

- **Config schema example has wrong JSON shape** (reviewer-general, reviewer-second-opinion)
  - The example shows `{ "escalation": { ... } }` at root, but actual location is `workflow.escalation`. Following the example would lead to misconfiguration.
  - File: `SKILL.md` Escalation config format section

- **Detection algorithm missing `has_items` fallback logic** (reviewer-spec-audit)
  - Spec requires checking for bullet items in review.md sections when summary stats are missing. Implementation only extracts summary stats, missing the fallback count method.
  - File: `SKILL.md` Detect Quality Gate Blocked procedure

- **Missing Ralph skip logic for maxRetries exceeded** (reviewer-spec-audit)
  - Spec requires checking retry-state.json before ticket selection and skipping tickets with `retryCount >= maxRetries`. Implementation only updates progress.md without skip logic.
  - File: `SKILL.md` Ralph Integration section

- **Missing parallel worker safety mechanism** (reviewer-spec-audit)
  - Spec requires either file-based locking or disabling retry logic when `ralph.parallelWorkers > 1`. Implementation only documents the assumption without enforcement.
  - File: `SKILL.md` Parallel Worker Safety section

- **Missing qualityGate.counts population in BLOCKED case** (reviewer-spec-audit)
  - When close is BLOCKED, the retry state attempt entry must include `qualityGate.counts`. Implementation describes creating the entry but doesn't show extracting counts from review.md.
  - File: `SKILL.md` Close Ticket procedure, Update Retry State procedure

## Major (should fix)

- **Base model resolution is ambiguous** (reviewer-general, reviewer-second-opinion)
  - Agent keys use kebab-case (`reviewer-second-opinion`) while escalation fields use camelCase (`reviewerSecondOpinion`). The mapping between these should be explicit to avoid mis-implementation.
  - File: `SKILL.md` Load Retry State section

- **maxRetries semantics are unclear** (reviewer-general, reviewer-second-opinion)
  - Algorithm warns when `retryAttempt >= maxRetries`, but it's unclear if this means "max total attempts" or "max BLOCKED attempts". The doc should clarify and match the comparison to the definition.
  - File: `SKILL.md` Load Retry State section

- **Missing successful close detection specification** (reviewer-spec-audit)
  - The spec defines a `detect_close_status` function that checks for CLOSED/COMPLETE vs BLOCKED vs unknown. Implementation describes this in prose without the algorithmic clarity of the spec.
  - File: `SKILL.md` Close Ticket procedure

- **Missing retry-state.json schema validation** (reviewer-spec-audit)
  - Implementation validates schema version but doesn't validate required fields (version, ticketId, attempts, lastAttemptAt, status). Corrupted state files could cause runtime errors.
  - File: `SKILL.md` Load Retry State procedure

- **No atomic write or backup for retry-state.json** (reviewer-spec-audit)
  - Updates write directly without atomic replace (write to temp then rename). Process crash mid-write could corrupt state.
  - File: `SKILL.md` Update Retry State procedure

- **Fallback BLOCKED detection for review.md is fragile** (reviewer-second-opinion)
  - Keys off section headers before extracting counts. If review.md ever outputs only Summary Statistics, this could incorrectly treat blocked as not blocked.
  - File: `SKILL.md` Detect Quality Gate Blocked procedure

## Minor (nice to fix)

- **Duplicated source-of-truth risk** (reviewer-general)
  - Both `skills/tf-workflow/SKILL.md` and `.pi/skills/tf-workflow/SKILL.md` exist. Consider adding a note about which is authoritative.

- **Severity count extraction regex is very permissive** (reviewer-general)
  - Pattern `(?:^|\s|[-*]\s*)...` can match unintended places. Tightening to match Summary Statistics list items specifically would reduce false positives.

- **Escalation table mixes 0-based and 1-based terminology** (reviewer-second-opinion)
  - Labels "Attempt 1 (or 0)" invites confusion. Choose one convention and stick to it.

- **Missing explicit check for attempts array length** (reviewer-spec-audit)
  - Load Retry State logic could be clearer about checking `retryCount < maxRetries` before proceeding.

- **closeSummaryRef path clarity** (reviewer-spec-audit)
  - Should explicitly be relative to artifactDir (e.g., just "close-summary.md") for portability.

## Warnings (follow-up ticket)

- **Concurrency is only documented, not enforced** (reviewer-general, reviewer-second-opinion, reviewer-spec-audit)
  - Parallel worker safety acknowledges race conditions but doesn't implement concrete mitigation. If parallel workers are enabled, this needs locking or per-ticket worker assignment.

- **Post-fix re-review not implemented** (reviewer-spec-audit)
  - Plan explicitly upgraded post-fix re-review to mandatory when quality gate is enabled. Create follow-up ticket to implement this.

- **Ralph integration incomplete for tk ready filtering** (reviewer-spec-audit)
  - No mechanism to prevent Ralph from picking blocked tickets again. Need filter in ticket selection.

- **Detection algorithm edge cases need unit tests** (reviewer-spec-audit)
  - Complex regex patterns may fail on edge cases. Ensure pt-7lrp includes comprehensive tests.

## Suggestions (follow-up ticket)

- **Add end-to-end state transition example** (reviewer-second-opinion)
  - Show `retryCount`, `retryAttempt`, and `attemptNumber` values at each step for initial → blocked → retry → closed.

- **Clarify retry-state.json write behavior when escalation disabled** (reviewer-second-opinion)
  - Document whether state should be written for observability or only when enabled.

- **Add invalid/legacy retry-state.json handling policy** (reviewer-general)
  - Define behavior when validation fails (backup + reset vs strict fail).

- **Clarify --retry-reset behavior** (reviewer-general)
  - Provide concrete example of before/after file names and whether it resets retryAttempt to 0.

## Positive Notes

- Good separation of concerns across Re-Anchor/Implement/Review/Fix/Close phases
- Escalation configuration is opt-in with safe defaults (`enabled: false`)
- Retry reset flag (`--retry-reset`) is implemented as specified
- Artifacts include retry context in implementation.md
- Model resolution order is clearly documented
- Integration points are identified across all phases
- Follows spec's overall architecture

## Summary Statistics
- Critical: 6
- Major: 6
- Minor: 5
- Warnings: 4
- Suggestions: 4
