# Review: pt-te9b

## Overall Assessment
The retry state specification for pt-te9b is a well-structured design document with clear schema definitions, detection algorithms, and integration points. The spec demonstrates good understanding of the IRF workflow requirements and provides a solid foundation for implementing the retry-aware escalation system. Minor issues exist in the detection algorithm regex patterns and some edge cases need clarification.

## Critical (must fix)
No issues found.

## Major (should fix)
- `retry-state-spec.md:194` - The `detect_blocked_from_review()` regex pattern `rf'##\s*{re.escape(severity)}.*?\n.*?(?:(?:^##)|(?:Summary Statistics))'` may fail to match actual review.md format. The example at `pt-d9rg/review.md:7` shows headers like "## Critical (must fix)" with parenthetical text, which the current pattern doesn't account for. This could cause false negatives in quality gate detection.

- `retry-state-spec.md:159` - The regex for extracting severity counts from close-summary.md only matches formats like "Critical: 0" but `pt-d9rg/close-summary.md:18-22` uses "- **Critical**: 0 issues" format with bold markers. The pattern `rf'{severity}:\s*(\d+)'` won't match this format, causing count extraction to fail.

- `retry-state-spec.md:76` - The `closeSummaryRef` field stores a relative path, but there's no guidance on path resolution when the working directory differs between `/tf` invocations. This could lead to "file not found" errors when Ralph switches worktrees.

## Minor (nice to fix)
- `retry-state-spec.md:88` - The JSON schema allows `retryCount` to be 0 but `minimum: 0` should perhaps be `minimum: 0` with a note that 0 means "never blocked". The semantic difference between "no attempts" (absent file) and "attempted but never blocked" (retryCount: 0) is unclear.

- `retry-state-spec.md:143` - The `BlockResult` dataclass/typed dict is referenced but not defined in the spec. Should include its type definition for implementers.

- `retry-state-spec.md:284` - The concurrent access edge case mentions "parallelWorkers > 1" but doesn't specify file locking strategy. Consider documenting whether atomic writes or advisory locks are expected.

- `retry-state-spec.md:63-67` - The `escalation` object has properties like `fixer`, `reviewerSecondOpinion`, `worker` but these don't match the agent names in settings.json which uses `fixer`, `reviewer-second-opinion`, `worker`. Should be consistent with kebab-case or camelCase convention.

## Warnings (follow-up ticket)
- `retry-state-spec.md:41` - Schema version is hardcoded to 1. Consider how version bumps will be handled when new fields are added (e.g., `ralphSessionId`, `worktreePath`). The migration section mentions backups but doesn't specify who triggers migrations.

- `retry-state-spec.md:300` - No specification for max retries configuration location. The spec mentions "maxRetries" in Ralph integration but doesn't define where this value comes from (settings.json? ticket metadata? hardcoded?).

- `retry-state-spec.md:111` - The `counts` object in `qualityGate` requires all 5 severities but the `failOn` array might only include a subset. Consider making counts sparse (only including failOn severities) to reduce file size and redundancy.

## Suggestions (follow-up ticket)
- `retry-state-spec.md:251` - Consider adding a `durationMs` field to attempts for performance tracking. This would help identify which retry strategies are slowest without needing to parse timestamps.

- `retry-state-spec.md:88` - Add a `ralphRunId` field to track which Ralph session initiated the attempt. Useful for debugging when multiple Ralph instances run concurrently.

- `retry-state-spec.md:42` - Consider adding a `createdAt` top-level field in addition to `lastAttemptAt` for tracking ticket age across retry cycles.

## Positive Notes
- ✓ Clear separation of concerns: detection, reset policy, and integration points are well-organized
- ✓ Schema includes `$schema` reference for IDE validation support
- ✓ Detection algorithm provides both primary and fallback mechanisms (defense in depth)
- ✓ Security section explicitly excludes secrets from the JSON format
- ✓ Reset policy is conservative (reset only on success) preventing accidental data loss
- ✓ Comprehensive acceptance criteria verification table with explicit evidence references
- ✓ Example JSON in section 2.3 is realistic and helps validate the schema design
- ✓ File location choice (`.tf/knowledge/tickets/{id}/`) follows existing project conventions and enables easy cleanup

## Summary Statistics
- Critical: 0
- Major: 3
- Minor: 4
- Warnings: 3
- Suggestions: 3
