# Retry State Specification

**Ticket**: pt-te9b  
**Status**: Design Complete  
**Related**: plan-retry-logic-quality-gate-blocked, pt-xu9u

---

## 1. Overview

This specification defines:
1. The **retry state file format** for tracking ticket retry attempts
2. The **detection algorithm** for determining quality-gate blocks
3. The **reset policy** for clearing retry state

The goal is to enable deterministic, auditable retry tracking for tickets that fail to close due to quality gate violations.

---

## 2. Retry State File

### 2.1 Location

```
.tf/knowledge/tickets/{ticket-id}/retry-state.json
```

**Rationale**: Co-locating retry state with ticket artifacts ensures:
- Survival across Ralph restarts
- Discoverability by both `/tf` and Ralph
- Easy cleanup when tickets are deleted
- Atomicity with other ticket artifacts

### 2.2 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "ticketId", "attempts", "lastAttemptAt", "status"],
  "properties": {
    "version": {
      "type": "integer",
      "const": 1,
      "description": "Schema version for future migrations"
    },
    "ticketId": {
      "type": "string",
      "pattern": "^[a-z]+-[a-z0-9]+$",
      "description": "Ticket identifier (e.g., pt-te9b)"
    },
    "attempts": {
      "type": "array",
      "description": "Chronological list of retry attempts",
      "items": {
        "type": "object",
        "required": ["attemptNumber", "startedAt", "status", "trigger"],
        "properties": {
          "attemptNumber": {
            "type": "integer",
            "minimum": 1,
            "description": "Sequential attempt number (1-indexed)"
          },
          "startedAt": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp when attempt started"
          },
          "completedAt": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp when attempt completed (if finished)"
          },
          "status": {
            "type": "string",
            "enum": ["in_progress", "blocked", "closed", "error"],
            "description": "Outcome of this attempt"
          },
          "trigger": {
            "type": "string",
            "enum": ["initial", "quality_gate", "manual_retry", "ralph_retry"],
            "description": "Why this attempt was started"
          },
          "qualityGate": {
            "type": "object",
            "description": "Quality gate state at attempt time (if applicable)",
            "properties": {
              "failOn": {
                "type": "array",
                "items": { "type": "string" },
                "description": "Severity levels configured to fail"
              },
              "counts": {
                "type": "object",
                "properties": {
                  "Critical": { "type": "integer" },
                  "Major": { "type": "integer" },
                  "Minor": { "type": "integer" },
                  "Warnings": { "type": "integer" },
                  "Suggestions": { "type": "integer" }
                }
              }
            }
          },
          "escalation": {
            "type": "object",
            "description": "Model escalation applied for this attempt",
            "properties": {
              "fixer": { "type": ["string", "null"] },
              "reviewerSecondOpinion": { "type": ["string", "null"] },
              "worker": { "type": ["string", "null"] }
            }
          },
          "closeSummaryRef": {
            "type": "string",
            "description": "Relative path from artifactDir to close-summary.md (e.g., 'close-summary.md'). Always relative to ticket's artifact directory for portability across worktrees."
          }
        }
      }
    },
    "lastAttemptAt": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp of most recent attempt start"
    },
    "status": {
      "type": "string",
      "enum": ["active", "blocked", "closed"],
      "description": "Current aggregate status"
    },
    "retryCount": {
      "type": "integer",
      "minimum": 0,
      "description": "Number of BLOCKED attempts (excluding successful closes). Must be <= maxRetries from config."
    }
  }
}
```

### 2.3 Example

```json
{
  "version": 1,
  "ticketId": "pt-te9b",
  "attempts": [
    {
      "attemptNumber": 1,
      "startedAt": "2026-02-10T12:30:00Z",
      "completedAt": "2026-02-10T12:45:00Z",
      "status": "blocked",
      "trigger": "initial",
      "qualityGate": {
        "failOn": ["Critical", "Major"],
        "counts": {
          "Critical": 0,
          "Major": 2,
          "Minor": 3,
          "Warnings": 1,
          "Suggestions": 0
        }
      },
      "escalation": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      },
      "closeSummaryRef": ".tf/knowledge/tickets/pt-te9b/close-summary.md"
    },
    {
      "attemptNumber": 2,
      "startedAt": "2026-02-10T13:00:00Z",
      "status": "in_progress",
      "trigger": "quality_gate",
      "qualityGate": {
        "failOn": ["Critical", "Major"],
        "counts": {
          "Critical": 0,
          "Major": 2,
          "Minor": 3,
          "Warnings": 1,
          "Suggestions": 0
        }
      },
      "escalation": {
        "fixer": "zai/glm-4.7",
        "reviewerSecondOpinion": null,
        "worker": null
      }
    }
  ],
  "lastAttemptAt": "2026-02-10T13:00:00Z",
  "status": "active",
  "retryCount": 1
}
```

---

## 3. Detection Algorithm

### 3.1 Primary Detection (close-summary.md)

The primary detection mechanism parses `close-summary.md` for an explicit BLOCKED status.

**Algorithm**:

```python
from typing import TypedDict

class BlockedResult(TypedDict):
    """Result of blocked detection."""
    source: str  # "close-summary.md" or "review.md"
    status: str  # Always "blocked" (normalized lowercase)
    counts: dict[str, int]  # Severity counts

def detect_blocked_from_close_summary(close_summary_path: Path) -> BlockedResult | None:
    """
    Parse close-summary.md for BLOCKED status.
    Returns BlockedResult if blocked, None if not found/closed.
    Status is normalized to lowercase ('blocked') for consistency.
    """
    if not close_summary_path.exists():
        return None

    content = close_summary_path.read_text()

    # Pattern: Explicit status line with BLOCKED (case-insensitive)
    # Matches: ## Status\n**BLOCKED**, ## Status\nBLOCKED, or variations with formatting
    status_match = re.search(
        r'##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?(BLOCKED)(?:\*\*)?(?:\s|$)',
        content,
        re.IGNORECASE
    )

    if not status_match:
        return None

    # Extract review counts from Summary Statistics section
    # Handles formats: "Critical: 0", "**Critical**: 0 issues", "- **Critical**: 0"
    counts = {}
    for severity in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
        sev_match = re.search(
            rf'(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)',
            content,
            re.IGNORECASE | re.MULTILINE
        )
        counts[severity] = int(sev_match.group(1)) if sev_match else 0

    return BlockedResult(
        source="close-summary.md",
        status="blocked",  # Normalized to lowercase for consistency
        counts=counts
    )
```

### 3.2 Fallback Detection (review.md)

If `close-summary.md` doesn't exist or doesn't show BLOCKED, check `review.md` for nonzero failOn severity counts.

**Algorithm**:

```python
def detect_blocked_from_review(review_path: Path, fail_on: list[str]) -> BlockedResult | None:
    """
    Parse review.md for nonzero failOn severity counts.
    Returns BlockedResult if any failOn severity has count > 0.
    """
    if not review_path.exists():
        return None

    if not fail_on:
        return None  # Quality gate disabled

    content = review_path.read_text()

    counts = {}
    blocked = False

    for severity in fail_on:
        # Match: ## Critical (must fix) or ## Critical
        # Account for parenthetical text, bold markers, and varying formats
        # Examples: "## Critical (must fix)", "## **Critical**: 0 issues"
        pattern = rf'^##\s*(?:\*\*)?{re.escape(severity)}(?:\*\*)?(?:\s*\([^)]+\))?(?:\s*:\s*\d+.*)?$'
        section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

        if section_match:
            # Check if section has any items (lines starting with -)
            section_start = section_match.end()
            next_header = re.search(r'\n^##\s', content[section_start:], re.MULTILINE)
            section_end = section_start + next_header.start() if next_header else len(content)
            section = content[section_start:section_end]
            has_items = bool(re.search(r'\n-\s', section))

            # Check summary stats - match formats: "Critical: 0", "**Critical**: 0", "- Critical: 0"
            stat_match = re.search(
                rf'(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)',
                content,
                re.IGNORECASE | re.MULTILINE
            )
            count = int(stat_match.group(1)) if stat_match else (1 if has_items else 0)
            counts[severity] = count

            if count > 0:
                blocked = True

    if not blocked:
        return None

    return BlockedResult(
        source="review.md",
        status="blocked",  # Normalized to lowercase
        counts=counts
    )
```

### 3.3 Unified Detection

```python
def detect_quality_gate_blocked(
    artifact_dir: Path,
    fail_on: list[str]
) -> BlockedResult | None:
    """
    Detect if a ticket is blocked by the quality gate.

    Detection order:
    1. Parse close-summary.md for explicit BLOCKED status
    2. Fallback to review.md failOn severity counts
    3. Return None if neither indicates a block
    """
    close_summary = artifact_dir / "close-summary.md"
    review = artifact_dir / "review.md"

    # Primary: close-summary.md
    result = detect_blocked_from_close_summary(close_summary)
    if result:
        return result

    # Fallback: review.md
    result = detect_blocked_from_review(review, fail_on)
    if result:
        return result

    return None
```

### 3.4 Successful Close Detection

For the reset policy, we need to detect successful closes (to reset the retry counter). This is the inverse of blocked detection.

**Algorithm**:

```python
class CloseResult(TypedDict):
    """Result of close detection."""
    success: bool  # True if CLOSED/COMPLETE, False if BLOCKED
    status: str    # "closed", "complete", "blocked", or "unknown"
    counts: dict[str, int] | None  # Severity counts if available

def detect_close_status(close_summary_path: Path) -> CloseResult:
    """
    Parse close-summary.md to determine close status.

    Returns:
        CloseResult with success=True for CLOSED/COMPLETE
        CloseResult with success=False for BLOCKED
        CloseResult with success=False, status="unknown" if file missing
    """
    if not close_summary_path.exists():
        return CloseResult(success=False, status="unknown", counts=None)

    content = close_summary_path.read_text()

    # Check for BLOCKED first
    blocked_match = re.search(
        r'##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?BLOCKED(?:\*\*)?(?:\s|$)',
        content,
        re.IGNORECASE
    )

    if blocked_match:
        # Extract counts for blocked case
        counts = {}
        for severity in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
            sev_match = re.search(
                rf'(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)',
                content,
                re.IGNORECASE | re.MULTILINE
            )
            counts[severity] = int(sev_match.group(1)) if sev_match else 0

        return CloseResult(success=False, status="blocked", counts=counts)

    # Check for successful close states
    success_match = re.search(
        r'##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?(CLOSED|COMPLETE)(?:\*\*)?(?:\s|$)',
        content,
        re.IGNORECASE
    )

    if success_match:
        status = success_match.group(1).lower()
        return CloseResult(success=True, status=status, counts=None)

    # Unknown status - treat as not closed
    return CloseResult(success=False, status="unknown", counts=None)
```

**Status Normalization**:
- All status values are normalized to lowercase in code (`"blocked"`, `"closed"`, `"complete"`)
- Parsing is case-insensitive to handle variations in markdown formatting
- Schema enums use lowercase consistently

---

## 4. Reset Policy

### 4.1 Reset Trigger

**Retry counter resets ONLY on successful ticket close.**

A "successful close" is defined as:
- `tk close {ticket-id}` returns exit code 0
- `close-summary.md` contains status `CLOSED` or `COMPLETE` (not `BLOCKED`)

### 4.2 No-Reset Conditions

Retry state is **NOT** reset when:
- Ralph restarts (state persists)
- Ticket is edited/modified manually
- Time passes (no TTL)
- `--retry-reset` flag is used (see below)

### 4.3 Manual Reset

The `--retry-reset` flag allows users to force a fresh attempt:

```bash
/tf pt-te9b --retry-reset
```

**Behavior**:
1. Rename existing `retry-state.json` to `retry-state.json.bak.{timestamp}`
2. Start with fresh attempt #1
3. Log the reset action in Ralph logs

### 4.4 State Cleanup

When a ticket is deleted via `tk rm`:
```bash
tk rm pt-te9b  # Should also remove .tf/knowledge/tickets/pt-te9b/
```

The entire artifact directory (including `retry-state.json`) should be removed.

---

## 5. Integration Points

### 5.1 /tf Workflow Integration

At **Re-Anchor Context** phase:
1. Check for existing `retry-state.json`
2. If exists, load and validate schema version
3. If last attempt was BLOCKED, increment retry count
4. Determine escalation models based on `workflow.escalation` config

At **Close Ticket** phase:
1. Update attempt with completion timestamp and status
2. If status is CLOSED, set aggregate status to closed
3. If status is BLOCKED, increment retry count, keep aggregate as active

### 5.2 Ralph Integration

Before ticket selection:
1. Check `retry-state.json` for `status: blocked` and `retryCount >= maxRetries`
2. If exceeded, skip ticket in `tk ready` results
3. Log skip decision with ticket ID and retry count

During iteration:
1. Log attempt number at iteration start
2. Log escalation decisions with model names
3. Update progress.md with retry context

### 5.3 Parallel Worker Safety

**Assumption**: Retry logic assumes `ralph.parallelWorkers: 1` (default). When parallel workers > 1:
- **Option A**: Implement file-based locking on `retry-state.json` (e.g., using `filelock` or atomic rename)
- **Option B**: Disable retry logic and log a warning about potential race conditions

The default behavior when `parallelWorkers > 1` without locking should be to disable retry logic to prevent:
- Lost updates to retry counter
- Duplicate attempt numbers
- Inconsistent escalation decisions

### 5.4 Default Configuration

Default `workflow.escalation` configuration in `settings.json`:

```json
{
  "workflow": {
    "escalation": {
      "enabled": false,
      "maxRetries": 3,
      "models": {
        "fixer": null,
        "reviewerSecondOpinion": null,
        "worker": null
      }
    }
  }
}
```

**Escalation Curve Mapping**:

| Attempt | Fixer | Reviewer-2nd-Opinion | Worker |
|---------|-------|---------------------|--------|
| 1 | Base model | Base model | Base model |
| 2 | `escalation.models.fixer` or base | Base model | Base model |
| 3+ | `escalation.models.fixer` or base | `escalation.models.reviewerSecondOpinion` or base | `escalation.models.worker` (if configured) or base |

**Notes**:
- `null` means "use base model from `agents` config" (no escalation)
- To enable escalation, set `enabled: true` and specify models
- `maxRetries` is the maximum BLOCKED attempts before giving up

---

## 6. Security Considerations

1. **No secrets in retry state**: The JSON must not contain API keys, tokens, or credentials
2. **Safe to commit**: retry-state.json can be committed to version control
3. **No PII**: Ticket titles and descriptions are not stored in retry state
4. **Audit trail**: All attempts are logged with timestamps for forensic analysis

---

## 7. Migration Path

### Version 1 (Current)
- Schema version: 1
- No migrations needed yet

### Future Versions
When schema changes:
1. Read `version` field
2. Apply sequential migrations (1→2→3)
3. Back up original as `retry-state.json.v1`
4. Write migrated data with new version

---

## 8. Testing Strategy

### Unit Tests
1. **Schema validation**: Test valid/invalid JSON against schema
2. **Detection accuracy**: Test parsing with various close-summary.md formats
3. **Reset logic**: Test reset conditions and --retry-reset behavior
4. **Escalation resolution**: Test model selection based on attempt number

### Integration Tests
1. **End-to-end retry**: Simulate BLOCKED close, verify retry counter increments
2. **Ralph integration**: Verify skip logic for maxRetries exceeded
3. **State persistence**: Verify survival across process restarts

### Edge Cases
1. Corrupted retry-state.json (malformed JSON)
2. Missing close-summary.md but review.md exists
3. Empty failOn list (quality gate disabled)
4. Clock skew (completedAt < startedAt)
5. Concurrent access (parallelWorkers > 1)

---

## 9. Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Retry state file location finalized | ✅ | Section 2.1: `.tf/knowledge/tickets/{id}/retry-state.json` |
| Detection algorithm specified | ✅ | Section 3: Primary (close-summary.md) + Fallback (review.md) |
| Reset policy specified | ✅ | Section 4: Reset on successful close only |
| Safe under Ralph restarts | ✅ | State in file system, not memory |
| No secrets in artifacts | ✅ | Section 6: JSON schema excludes sensitive data |

---

## 10. Related Artifacts

- **Blocks**: pt-xu9u (Implement retry-aware escalation in /tf workflow)
- **Plan**: plan-retry-logic-quality-gate-blocked
- **Seed**: seed-add-retry-logic-on-failed-tickets
