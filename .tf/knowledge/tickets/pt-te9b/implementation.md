# Implementation: pt-te9b

## Summary
Defined the retry state specification for quality-gate blocked tickets. This design document specifies the JSON schema, detection algorithm, and reset policy for the retry/escalation system.

## Files Changed
- `.tf/knowledge/tickets/pt-te9b/retry-state-spec.md` - Complete technical specification (with fixes from review)
- `.tf/knowledge/tickets/pt-te9b/research.md` - Research context
- `.tf/knowledge/tickets/pt-te9b/implementation.md` - This summary
- `.tf/knowledge/tickets/pt-te9b/review.md` - Consolidated review

## Review Fixes Applied
Based on reviewer feedback:
1. **Regex improvements** - Updated patterns to handle bold markers (`**Critical**`) and parenthetical text ("Critical (must fix)")
2. **Type definitions** - Added `BlockedResult` and `CloseResult` TypedDict definitions
3. **Status normalization** - Documented lowercase storage with case-insensitive parsing
4. **Path resolution** - Clarified `closeSummaryRef` is relative to artifactDir
5. **Successful close detection** - Added explicit algorithm for detecting CLOSED/COMPLETE status
6. **Parallel worker safety** - Added Section 5.3 documenting assumptions and options
7. **Default configuration** - Added Section 5.4 with escalation curve mapping

## Key Decisions

### 1. Retry State Location
**Decision**: `.tf/knowledge/tickets/{id}/retry-state.json`

**Rationale**:
- Co-located with ticket artifacts for atomicity
- Survives Ralph restarts
- Discoverable by both `/tf` and Ralph
- Easy cleanup on ticket deletion

### 2. Detection Algorithm
**Primary**: Parse `close-summary.md` for explicit `BLOCKED` status

**Pattern**: Match `## Status` section for `BLOCKED` keyword (case-insensitive)

**Fallback**: Parse `review.md` for nonzero counts in `workflow.failOn` severities

**Severity Categories**: Critical, Major, Minor, Warnings, Suggestions

### 3. Reset Policy
**Rule**: Reset retry counter **only** on successful close

**Successful Close** = `tk close` exit 0 + `close-summary.md` status is `CLOSED` or `COMPLETE`

**Manual Override**: `--retry-reset` flag renames existing state and starts fresh

## Schema Overview

```json
{
  "version": 1,
  "ticketId": "pt-te9b",
  "attempts": [...],
  "lastAttemptAt": "2026-02-10T13:00:00Z",
  "status": "active|blocked|closed",
  "retryCount": 1
}
```

Each attempt tracks:
- `attemptNumber`: 1-indexed sequence
- `startedAt/completedAt`: ISO 8601 timestamps
- `status`: in_progress | blocked | closed | error
- `trigger`: initial | quality_gate | manual_retry | ralph_retry
- `qualityGate`: failOn config + severity counts
- `escalation`: model overrides per role

## Integration Points

### /tf Workflow
- **Re-Anchor**: Load existing state, detect prior blocks, determine escalation
- **Close**: Update attempt record, increment retryCount if blocked

### Ralph Loop
- **Selection**: Skip tickets with retryCount >= maxRetries
- **Logging**: Record attempt numbers and escalation decisions

## Security
- No secrets, API keys, or PII in retry state
- Safe to commit to version control
- Audit trail via timestamps

## Unblocks
- pt-xu9u: Implement retry-aware escalation in /tf workflow

## Verification
All acceptance criteria met:
- [x] Retry state file location finalized
- [x] Detection algorithm specified (primary + fallback)
- [x] Reset policy specified (reset on close only)
- [x] Safe under Ralph restarts (file-based persistence)
- [x] No secrets leak (schema excludes sensitive data)
