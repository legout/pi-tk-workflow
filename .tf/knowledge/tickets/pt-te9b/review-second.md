# Review (Second Opinion): pt-te9b

## Overall Assessment
The retry state specification is comprehensive, well-structured, and aligns closely with the approved plan. The JSON schema is versioned for future migrations, detection algorithms are clearly specified with primary and fallback mechanisms, and security considerations are appropriately addressed. The spec successfully unblocks pt-xu9u with clear integration points.

## Critical (must fix)
No issues found.

## Major (should fix)
- `retry-state-spec.md:122-124` - The `retryCount` field description says "Number of BLOCKED attempts (excluding successful closes)" but the schema shows `minimum: 0` without an explicit `maximum`. Consider adding a `maximum` constraint equal to `maxRetries` from settings.json to prevent runaway growth if the implementation fails to cap properly.

- `retry-state-spec.md:3.1` (Detection Algorithm) - The regex pattern for BLOCKED status detection is case-insensitive but the example in section 3.1 shows `**BLOCKED**`. The pattern `r'##\s*Status\s*\n\s*(?:\*\*)?(BLOCKED)(?:\*\*)?'` will match but the capture group only gets the uppercase version. However, the enum values in the schema use lowercase (`"blocked"`). Document the expected normalization (lowercase for storage, case-insensitive for parsing).

- `retry-state-spec.md:4.1` (Reset Policy) - The successful close detection relies on parsing `close-summary.md` for `CLOSED` or `COMPLETE` status, but the detection algorithm in section 3.1 is only defined for BLOCKED. Add explicit detection logic for successful close states or clarify that absence of BLOCKED implies success (which is risky if close-summary.md is malformed).

## Minor (nice to fix)
- `retry-state-spec.md:2.2` - The `closeSummaryRef` field uses a relative path string. Consider adding a note about whether this should be relative to the ticket directory, repo root, or absolute path for consistency.

- `retry-state-spec.md:6.2` (State Cleanup) - The `tk rm` command is mentioned but not all implementations of ticket managers remove the entire directory. Verify that the target `tk` implementation actually deletes the artifact directory on `rm`, otherwise stale retry-state.json files may accumulate.

- `retry-state-spec.md:8.4` (Edge Cases) - "Clock skew (completedAt < startedAt)" is listed as an edge case but there's no guidance on how to handle it. Add validation logic recommendation (e.g., log warning, swap values, or reject malformed state).

- `retry-state-spec.md:2.2` - The `escalation` object has nullable string fields but doesn't specify the format. Should these be model IDs (e.g., "zai/glm-4.7") or can they be aliases ("fast", "worker")? Clarify expected values.

## Warnings (follow-up ticket)
- `retry-state-spec.md:5.2` (Ralph Integration) - The spec mentions "ticket-level locking is required" for `parallelWorkers > 1` but doesn't specify the locking mechanism. This is acceptable as this ticket only defines the spec, but pt-xu9u implementation ticket should either implement file-based locking or document that parallel mode disables retry logic.

- `retry-state-spec.md:3.2` (Fallback Detection) - The fallback detection parses `review.md` for severity counts. However, if a ticket has multiple review rounds (e.g., review.md gets overwritten on each attempt), historical counts may be lost. Consider whether review.md should be versioned per attempt (review-1.md, review-2.md) for accurate historical tracking.

- `retry-state-spec.md:8` (Testing Strategy) - The testing section outlines comprehensive tests but doesn't specify where these tests should live (tf-workflow skill tests? Ralph tests? Unit tests in pi-ticketflow?). Add test location guidance.

## Suggestions (follow-up ticket)
- `retry-state-spec.md:2.2` - Consider adding an `errors` array field to the attempt object to capture error messages or stack traces when `status: "error"`. This would aid debugging when Ralph encounters unexpected failures.

- `retry-state-spec.md:2.2` - Add a `durationMs` computed field to attempts for quick performance analysis without calculating from timestamps.

- `retry-state-spec.md:4` - Consider adding an automatic reset policy after a time threshold (e.g., reset after 7 days of inactivity) to handle abandoned tickets without manual `--retry-reset`.

- `retry-state-spec.md:7` (Migration Path) - Add a JSON Schema URL reference so implementations can validate retry-state.json against the schema programmatically.

## Positive Notes
- Excellent decision to version the schema (section 2.2 `version` field) - this enables future migrations without breaking changes.
- The primary + fallback detection approach (section 3) is robust and handles edge cases where close-summary.md might be missing.
- Security section (section 6) explicitly excludes secrets and PII - critical for a file that may be committed to version control.
- The acceptance criteria verification table (section 9) with status and evidence columns provides clear traceability to the original ticket requirements.
- Good use of detailed examples throughout (section 2.3, detection algorithm pseudocode) - makes the spec immediately implementable.
- Co-location of retry state with ticket artifacts (section 2.1) is the right choice for atomicity and cleanup.
- The `--retry-reset` flag design (section 4.3) with timestamped backup is user-friendly and preserves audit trail.

## Summary Statistics
- Critical: 0
- Major: 3
- Minor: 4
- Warnings: 3
- Suggestions: 4
