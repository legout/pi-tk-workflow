"""Tests for retry state management.

This module tests:
- Retry state persistence (load/save)
- Blocked status detection from close-summary.md and review.md
- Escalation model resolution based on attempt number
- Retry counter behavior and reset policies
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tf.retry_state import (
    DEFAULT_ESCALATION_CONFIG,
    SCHEMA_VERSION,
    BlockedResult,
    CloseResult,
    EscalatedModels,
    RetryState,
    detect_blocked_from_close_summary,
    detect_blocked_from_review,
    detect_close_status,
    detect_quality_gate_blocked,
    load_escalation_config,
)


class TestRetryStatePersistence:
    """Tests for retry state loading and saving."""

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Loading from non-existent directory returns None."""
        result = RetryState.load(tmp_path)
        assert result is None

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Loading invalid JSON returns None."""
        state_file = tmp_path / "retry-state.json"
        state_file.write_text("not valid json")
        result = RetryState.load(tmp_path)
        assert result is None

    def test_load_missing_required_fields(self, tmp_path: Path) -> None:
        """Loading JSON without required fields returns None."""
        state_file = tmp_path / "retry-state.json"
        state_file.write_text(json.dumps({"version": 1, "ticketId": "pt-123"}))
        result = RetryState.load(tmp_path)
        assert result is None

    def test_load_valid_state(self, tmp_path: Path) -> None:
        """Loading valid state returns RetryState instance."""
        state_file = tmp_path / "retry-state.json"
        data = {
            "version": 1,
            "ticketId": "pt-123",
            "attempts": [],
            "lastAttemptAt": "2026-02-10T12:00:00Z",
            "status": "active",
            "retryCount": 0,
        }
        state_file.write_text(json.dumps(data))

        state = RetryState.load(tmp_path)
        assert state is not None
        assert state.ticket_id == "pt-123"
        assert state.get_retry_count() == 0

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Saving creates parent directories if needed."""
        nested_dir = tmp_path / "nested" / "deep" / "dir"
        state = RetryState(nested_dir, ticket_id="pt-123")
        state.save()

        assert (nested_dir / "retry-state.json").exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Saved state can be loaded back correctly."""
        state = RetryState(tmp_path, ticket_id="pt-456")
        state.start_attempt(trigger="initial")
        state.complete_attempt(status="blocked")
        state.save()

        loaded = RetryState.load(tmp_path)
        assert loaded is not None
        assert loaded.ticket_id == "pt-456"
        assert loaded.get_attempt_number() == 1
        assert loaded.get_retry_count() == 1

    def test_atomic_save(self, tmp_path: Path) -> None:
        """Save is atomic (uses temp file + rename)."""
        state = RetryState(tmp_path, ticket_id="pt-789")
        state.save()

        # Should never leave temp files
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0


class TestRetryCounter:
    """Tests for retry counter behavior."""

    def test_initial_retry_count(self, tmp_path: Path) -> None:
        """New state has zero retry count."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        assert state.get_retry_count() == 0

    def test_retry_count_increments_on_blocked(self, tmp_path: Path) -> None:
        """Retry count increments when attempt is blocked."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        assert state.get_retry_count() == 1

    def test_retry_count_increments_multiple_blocked(self, tmp_path: Path) -> None:
        """Retry count accumulates across multiple blocked attempts."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        for _ in range(3):
            state.start_attempt()
            state.complete_attempt(status="blocked")

        assert state.get_retry_count() == 3

    def test_retry_count_resets_on_closed(self, tmp_path: Path) -> None:
        """Retry count resets to zero on successful close."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        # First blocked attempt
        state.start_attempt()
        state.complete_attempt(status="blocked")
        assert state.get_retry_count() == 1

        # Second attempt succeeds
        state.start_attempt(trigger="retry")
        state.complete_attempt(status="closed")
        assert state.get_retry_count() == 0

    def test_attempt_number_tracking(self, tmp_path: Path) -> None:
        """Attempt numbers are sequential and 1-indexed."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        assert state.get_attempt_number() == 0

        num1 = state.start_attempt()
        assert num1 == 1
        assert state.get_attempt_number() == 1

        state.complete_attempt(status="blocked")

        num2 = state.start_attempt()
        assert num2 == 2
        assert state.get_attempt_number() == 2


class TestBlockedStatus:
    """Tests for blocked status detection."""

    def test_is_blocked_no_attempts(self, tmp_path: Path) -> None:
        """No attempts means not blocked."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        assert not state.is_blocked()

    def test_is_blocked_in_progress(self, tmp_path: Path) -> None:
        """In-progress attempt is not blocked."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        assert not state.is_blocked()

    def test_is_blocked_after_blocked(self, tmp_path: Path) -> None:
        """Blocked attempt shows as blocked."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        assert state.is_blocked()

    def test_is_blocked_after_closed(self, tmp_path: Path) -> None:
        """Closed attempt shows as not blocked."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="closed")
        assert not state.is_blocked()


class TestMaxRetriesSkip:
    """Tests for max retry skip logic."""

    def test_should_skip_at_limit(self, tmp_path: Path) -> None:
        """Should skip when retry count equals maxRetries."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        for _ in range(3):
            state.start_attempt()
            state.complete_attempt(status="blocked")

        assert state.should_skip(max_retries=3)

    def test_should_skip_exceeds_limit(self, tmp_path: Path) -> None:
        """Should skip when retry count exceeds maxRetries."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        for _ in range(5):
            state.start_attempt()
            state.complete_attempt(status="blocked")

        assert state.should_skip(max_retries=3)

    def test_should_not_skip_below_limit(self, tmp_path: Path) -> None:
        """Should not skip when retry count is below maxRetries."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        state.start_attempt()
        state.complete_attempt(status="blocked")

        assert not state.should_skip(max_retries=3)

    def test_should_not_skip_zero_retries(self, tmp_path: Path) -> None:
        """Should not skip with zero retries."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        assert not state.should_skip(max_retries=3)


class TestEscalationResolution:
    """Tests for escalation model resolution."""

    def test_escalation_disabled(self, tmp_path: Path) -> None:
        """When escalation is disabled, no models are escalated."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")

        config = {"enabled": False, "models": {"fixer": "strong-model"}}
        base_models = {"fixer": "base-fixer"}

        result = state.resolve_escalation(config, base_models)
        assert result.fixer is None
        assert result.reviewerSecondOpinion is None

    def test_attempt_1_no_escalation(self, tmp_path: Path) -> None:
        """First attempt has no escalation."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        config = {"enabled": True, "models": {"fixer": "strong-fixer"}}
        base_models = {"fixer": "base-fixer"}

        result = state.resolve_escalation(config, base_models)
        assert result.fixer is None

    def test_attempt_2_escalates_fixer(self, tmp_path: Path) -> None:
        """Second attempt escalates fixer only."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        state.start_attempt(trigger="retry")

        config = {"enabled": True, "models": {"fixer": "strong-fixer"}}
        base_models = {"fixer": "base-fixer"}

        result = state.resolve_escalation(config, base_models)
        assert result.fixer == "strong-fixer"
        assert result.reviewerSecondOpinion is None

    def test_attempt_2_uses_base_if_no_config(self, tmp_path: Path) -> None:
        """Second attempt uses base model if no escalation configured."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        state.start_attempt(trigger="retry")

        config = {"enabled": True, "models": {"fixer": None}}
        base_models = {"fixer": "base-fixer"}

        result = state.resolve_escalation(config, base_models)
        assert result.fixer == "base-fixer"

    def test_attempt_3_escalates_reviewer(self, tmp_path: Path) -> None:
        """Third attempt escalates reviewer-second-opinion."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        # Attempt 1 - blocked
        state.start_attempt()
        state.complete_attempt(status="blocked")

        # Attempt 2 - blocked
        state.start_attempt(trigger="retry")
        state.complete_attempt(status="blocked")

        # Attempt 3
        state.start_attempt(trigger="retry")

        config = {
            "enabled": True,
            "models": {
                "fixer": "strong-fixer",
                "reviewerSecondOpinion": "strong-reviewer",
            },
        }
        base_models = {"fixer": "base-fixer", "reviewerSecondOpinion": "base-reviewer"}

        result = state.resolve_escalation(config, base_models)
        assert result.fixer == "strong-fixer"
        assert result.reviewerSecondOpinion == "strong-reviewer"

    def test_attempt_3_escalates_worker_if_configured(self, tmp_path: Path) -> None:
        """Third attempt escalates worker if explicitly configured."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        for _ in range(2):
            state.start_attempt()
            state.complete_attempt(status="blocked")
        state.start_attempt(trigger="retry")

        config = {
            "enabled": True,
            "models": {
                "fixer": "strong-fixer",
                "reviewerSecondOpinion": "strong-reviewer",
                "worker": "strong-worker",
            },
        }
        base_models = {}

        result = state.resolve_escalation(config, base_models)
        assert result.worker == "strong-worker"


class TestReset:
    """Tests for retry state reset."""

    def test_reset_creates_backup(self, tmp_path: Path) -> None:
        """Reset with backup=True creates timestamped backup."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        state.save()

        state.reset(backup=True)

        # Should have a backup file
        backups = list(tmp_path.glob("retry-state.json.bak.*"))
        assert len(backups) == 1

    def test_reset_without_backup(self, tmp_path: Path) -> None:
        """Reset with backup=False doesn't create backup."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")
        state.save()

        state.reset(backup=False)

        backups = list(tmp_path.glob("retry-state.json.bak.*"))
        assert len(backups) == 0

    def test_reset_clears_attempts(self, tmp_path: Path) -> None:
        """Reset clears all attempt history."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.complete_attempt(status="blocked")

        state.reset(backup=False)

        assert state.get_attempt_number() == 0
        assert state.get_retry_count() == 0
        assert not state.is_blocked()


class TestCloseSummaryDetection:
    """Tests for close-summary.md BLOCKED detection."""

    def test_detect_blocked_explicit(self, tmp_path: Path) -> None:
        """Detects explicit BLOCKED status."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("""
# Close Summary

## Status
**BLOCKED**

## Summary Statistics
- Critical: 2
- Major: 1
- Minor: 0
""")

        result = detect_blocked_from_close_summary(close_summary)
        assert result is not None
        assert result.status == "blocked"
        assert result.source == "close-summary.md"
        assert result.counts["Critical"] == 2
        assert result.counts["Major"] == 1

    def test_detect_blocked_lowercase(self, tmp_path: Path) -> None:
        """Detects lowercase 'blocked' status."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("""
## Status
blocked
""")

        result = detect_blocked_from_close_summary(close_summary)
        assert result is not None
        assert result.status == "blocked"

    def test_detect_not_blocked_closed(self, tmp_path: Path) -> None:
        """Does not detect CLOSED as blocked."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("""
## Status
**CLOSED**
""")

        result = detect_blocked_from_close_summary(close_summary)
        assert result is None

    def test_detect_not_blocked_complete(self, tmp_path: Path) -> None:
        """Does not detect COMPLETE as blocked."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("""
## Status
COMPLETE
""")

        result = detect_blocked_from_close_summary(close_summary)
        assert result is None

    def test_detect_missing_file(self, tmp_path: Path) -> None:
        """Returns None for missing file."""
        result = detect_blocked_from_close_summary(tmp_path / "nonexistent.md")
        assert result is None

    def test_detect_extracts_all_severities(self, tmp_path: Path) -> None:
        """Extracts all severity counts from summary statistics."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("""
## Status
BLOCKED

## Summary Statistics
- Critical: 5
- Major: 3
- Minor: 2
- Warnings: 1
- Suggestions: 0
""")

        result = detect_blocked_from_close_summary(close_summary)
        assert result is not None
        assert result.counts["Critical"] == 5
        assert result.counts["Major"] == 3
        assert result.counts["Minor"] == 2
        assert result.counts["Warnings"] == 1
        assert result.counts["Suggestions"] == 0


class TestReviewDetection:
    """Tests for review.md BLOCKED detection."""

    def test_detect_blocked_from_review_counts(self, tmp_path: Path) -> None:
        """Detects blocked from nonzero failOn severity counts."""
        review = tmp_path / "review.md"
        review.write_text("""
# Review

## Critical (must fix)
- `file.ts:42` - Issue 1
- `file.ts:43` - Issue 2

## Summary Statistics
- Critical: 2
- Major: 0
""")

        result = detect_blocked_from_review(review, fail_on=["Critical", "Major"])
        assert result is not None
        assert result.status == "blocked"
        assert result.counts["Critical"] == 2

    def test_detect_not_blocked_zero_counts(self, tmp_path: Path) -> None:
        """Does not detect blocked when counts are zero."""
        review = tmp_path / "review.md"
        review.write_text("""
## Critical (must fix)

*No critical issues found*

## Summary Statistics
- Critical: 0
- Major: 0
""")

        result = detect_blocked_from_review(review, fail_on=["Critical", "Major"])
        assert result is None

    def test_detect_blocked_from_items_no_stats(self, tmp_path: Path) -> None:
        """Detects blocked from section items when no stats available."""
        review = tmp_path / "review.md"
        review.write_text("""
## Critical

- Issue 1
- Issue 2
""")

        result = detect_blocked_from_review(review, fail_on=["Critical"])
        assert result is not None
        assert result.counts["Critical"] == 1  # Falls back to 1 if items exist

    def test_empty_fail_on_list(self, tmp_path: Path) -> None:
        """Empty fail_on list means no blocking."""
        review = tmp_path / "review.md"
        review.write_text("""
## Critical
- Critical: 5
""")

        result = detect_blocked_from_review(review, fail_on=[])
        assert result is None

    def test_missing_review_file(self, tmp_path: Path) -> None:
        """Returns None for missing file."""
        result = detect_blocked_from_review(tmp_path / "nonexistent.md", fail_on=["Critical"])
        assert result is None


class TestUnifiedDetection:
    """Tests for unified quality gate detection."""

    def test_prefers_close_summary_over_review(self, tmp_path: Path) -> None:
        """Uses close-summary.md when available."""
        # Create both files
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("## Status\nBLOCKED\n\n**Critical**: 5")

        review = tmp_path / "review.md"
        review.write_text("## Critical\n- Critical: 10")

        result = detect_quality_gate_blocked(tmp_path, fail_on=["Critical"])
        assert result is not None
        assert result.source == "close-summary.md"
        assert result.counts["Critical"] == 5  # From close-summary, not review

    def test_fallback_to_review(self, tmp_path: Path) -> None:
        """Falls back to review.md when close-summary not available."""
        review = tmp_path / "review.md"
        review.write_text("## Critical\n- Critical: 3")

        result = detect_quality_gate_blocked(tmp_path, fail_on=["Critical"])
        assert result is not None
        assert result.source == "review.md"

    def test_no_block_when_neither_present(self, tmp_path: Path) -> None:
        """Returns None when no files present."""
        result = detect_quality_gate_blocked(tmp_path, fail_on=["Critical"])
        assert result is None


class TestCloseStatusDetection:
    """Tests for close status detection."""

    def test_detect_closed_success(self, tmp_path: Path) -> None:
        """Detects successful close."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("## Status\n**CLOSED**")

        result = detect_close_status(close_summary)
        assert result.success is True
        assert result.status == "closed"

    def test_detect_complete_success(self, tmp_path: Path) -> None:
        """Detects COMPLETE as success."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("## Status\nCOMPLETE")

        result = detect_close_status(close_summary)
        assert result.success is True
        assert result.status == "complete"

    def test_detect_blocked_failure(self, tmp_path: Path) -> None:
        """Detects BLOCKED as failure."""
        close_summary = tmp_path / "close-summary.md"
        close_summary.write_text("## Status\n**BLOCKED**\n\nCritical: 2")

        result = detect_close_status(close_summary)
        assert result.success is False
        assert result.status == "blocked"
        assert result.counts is not None
        assert result.counts["Critical"] == 2

    def test_missing_file_unknown(self, tmp_path: Path) -> None:
        """Missing file returns unknown status."""
        result = detect_close_status(tmp_path / "nonexistent.md")
        assert result.success is False
        assert result.status == "unknown"


class TestEscalationConfigLoading:
    """Tests for escalation config loading from settings.json."""

    def test_load_default_config(self, tmp_path: Path) -> None:
        """Returns defaults when settings.json doesn't exist."""
        result = load_escalation_config(tmp_path / "nonexistent.json")
        assert result == DEFAULT_ESCALATION_CONFIG

    def test_load_merges_with_defaults(self, tmp_path: Path) -> None:
        """User config is merged with defaults."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "workflow": {
                "escalation": {
                    "enabled": True,
                    "maxRetries": 5,
                }
            }
        }))

        result = load_escalation_config(settings)
        assert result["enabled"] is True
        assert result["maxRetries"] == 5
        # Defaults preserved
        assert result["models"]["fixer"] is None

    def test_load_merges_nested_models(self, tmp_path: Path) -> None:
        """Nested models dict is properly merged."""
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "workflow": {
                "escalation": {
                    "models": {
                        "fixer": "custom-fixer",
                    }
                }
            }
        }))

        result = load_escalation_config(settings)
        assert result["models"]["fixer"] == "custom-fixer"
        assert result["models"]["reviewerSecondOpinion"] is None  # Default

    def test_invalid_json_returns_defaults(self, tmp_path: Path) -> None:
        """Invalid JSON returns default config."""
        settings = tmp_path / "settings.json"
        settings.write_text("invalid json")

        result = load_escalation_config(settings)
        assert result == DEFAULT_ESCALATION_CONFIG


class TestSchemaValidation:
    """Tests for retry state schema validation."""

    def test_valid_schema_accepted(self, tmp_path: Path) -> None:
        """Valid schema passes validation."""
        data = {
            "version": 1,
            "ticketId": "pt-123",
            "attempts": [],
            "lastAttemptAt": "2026-02-10T12:00:00Z",
            "status": "active",
        }
        state_file = tmp_path / "retry-state.json"
        state_file.write_text(json.dumps(data))

        state = RetryState.load(tmp_path)
        assert state is not None

    def test_missing_version_rejected(self, tmp_path: Path) -> None:
        """Missing version field is rejected."""
        data = {
            "ticketId": "pt-123",
            "attempts": [],
            "lastAttemptAt": "2026-02-10T12:00:00Z",
            "status": "active",
        }
        state_file = tmp_path / "retry-state.json"
        state_file.write_text(json.dumps(data))

        state = RetryState.load(tmp_path)
        assert state is None

    def test_missing_ticket_id_rejected(self, tmp_path: Path) -> None:
        """Missing ticketId field is rejected."""
        data = {
            "version": 1,
            "attempts": [],
            "lastAttemptAt": "2026-02-10T12:00:00Z",
            "status": "active",
        }
        state_file = tmp_path / "retry-state.json"
        state_file.write_text(json.dumps(data))

        state = RetryState.load(tmp_path)
        assert state is None


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_complete_attempt_without_start(self, tmp_path: Path) -> None:
        """Completing without starting raises error."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        with pytest.raises(ValueError, match="No in-progress attempt"):
            state.complete_attempt(status="closed")

    def test_state_survives_process_restart(self, tmp_path: Path) -> None:
        """State persists across process boundaries."""
        # Simulate first process
        state1 = RetryState(tmp_path, ticket_id="pt-123")
        state1.start_attempt()
        state1.complete_attempt(status="blocked")
        state1.save()

        # Simulate second process (fresh load)
        state2 = RetryState.load(tmp_path)
        assert state2 is not None
        assert state2.get_retry_count() == 1
        assert state2.is_blocked()

    def test_concurrent_modifications_safe(self, tmp_path: Path) -> None:
        """Atomic save prevents corrupted state."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.save()

        # Simulate concurrent modification by directly editing file
        state_file = tmp_path / "retry-state.json"
        original = json.loads(state_file.read_text())
        original["retryCount"] = 999
        state_file.write_text(json.dumps(original))

        # Load should succeed (no corruption from our save)
        loaded = RetryState.load(tmp_path)
        assert loaded is not None
        assert loaded.get_retry_count() == 999

    def test_timestamp_format_iso8601(self, tmp_path: Path) -> None:
        """Timestamps are in ISO 8601 format."""
        state = RetryState(tmp_path, ticket_id="pt-123")
        state.start_attempt()
        state.save()

        data = json.loads((tmp_path / "retry-state.json").read_text())
        # Should be valid ISO 8601
        ts = data["lastAttemptAt"]
        datetime.fromisoformat(ts.replace("Z", "+00:00"))


class TestIntegration:
    """Integration tests for full retry flow."""

    def test_full_retry_flow(self, tmp_path: Path) -> None:
        """Complete retry flow from initial to blocked to reset."""
        # Initial attempt
        state = RetryState(tmp_path, ticket_id="pt-integration")
        attempt_num = state.start_attempt(trigger="initial")
        assert attempt_num == 1

        # Simulate work and blocked close
        state.complete_attempt(status="blocked")
        assert state.get_retry_count() == 1
        assert state.is_blocked()
        state.save()

        # Next Ralph iteration - load and retry
        loaded = RetryState.load(tmp_path)
        assert loaded is not None

        # Check escalation for attempt 2
        config = {
            "enabled": True,
            "models": {"fixer": "gpt-5.3-codex"},
        }
        base_models = {"fixer": "base-model"}
        escalation = loaded.resolve_escalation(config, base_models)

        loaded.start_attempt(
            trigger="quality_gate",
            escalation={"fixer": escalation.fixer},
        )
        assert loaded.get_attempt_number() == 2

        # Blocked again
        loaded.complete_attempt(status="blocked")
        assert loaded.get_retry_count() == 2
        state.save()

        # Check if should skip after max retries
        assert loaded.should_skip(max_retries=2)

        # User resets manually
        loaded.reset(backup=True)
        assert loaded.get_retry_count() == 0
        assert not loaded.is_blocked()

    def test_successful_close_resets_counter(self, tmp_path: Path) -> None:
        """Successful close resets retry counter for future failures."""
        state = RetryState(tmp_path, ticket_id="pt-123")

        # First ticket fails twice
        for _ in range(2):
            state.start_attempt()
            state.complete_attempt(status="blocked")

        assert state.get_retry_count() == 2

        # Third attempt succeeds
        state.start_attempt()
        state.complete_attempt(status="closed")
        assert state.get_retry_count() == 0

        # New work on same ticket fails - should start from 0
        state.start_attempt()
        state.complete_attempt(status="blocked")
        assert state.get_retry_count() == 1  # Not 3!
