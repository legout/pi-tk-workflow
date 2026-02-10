"""Retry state management for quality-gate blocked tickets.

This module provides functionality for:
- Loading and saving retry state to JSON files
- Detecting BLOCKED status from close-summary.md and review.md
- Resolving escalation models based on attempt number
- Managing retry counters and reset policies
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict


# Schema version for future migrations
SCHEMA_VERSION = 1

# Default escalation config (matches settings.json schema)
DEFAULT_ESCALATION_CONFIG: dict[str, Any] = {
    "enabled": False,
    "maxRetries": 3,
    "models": {
        "fixer": None,
        "reviewerSecondOpinion": None,
        "worker": None,
    },
}

# Module-level logger
logger = logging.getLogger(__name__)


class QualityGateCounts(TypedDict):
    """Severity counts from quality gate."""

    Critical: int
    Major: int
    Minor: int
    Warnings: int
    Suggestions: int


class QualityGateState(TypedDict, total=False):
    """Quality gate state at attempt time."""

    failOn: list[str]
    counts: QualityGateCounts


class EscalationState(TypedDict, total=False):
    """Model escalation applied for an attempt."""

    fixer: str | None
    reviewerSecondOpinion: str | None
    worker: str | None


class AttemptEntry(TypedDict, total=False):
    """Single retry attempt entry."""

    attemptNumber: int
    startedAt: str
    completedAt: str
    status: str  # "in_progress", "blocked", "closed", "error"
    trigger: str  # "initial", "quality_gate", "manual_retry", "ralph_retry"
    qualityGate: QualityGateState
    escalation: EscalationState
    closeSummaryRef: str


class RetryStateData(TypedDict):
    """Full retry state JSON structure."""

    version: int
    ticketId: str
    attempts: list[AttemptEntry]
    lastAttemptAt: str
    status: str  # "active", "blocked", "closed"
    retryCount: int


@dataclass
class BlockedResult:
    """Result of blocked detection."""

    source: str  # "close-summary.md" or "review.md"
    status: str  # Always "blocked" (normalized lowercase)
    counts: dict[str, int]  # Severity counts


@dataclass
class CloseResult:
    """Result of close detection."""

    success: bool  # True if CLOSED/COMPLETE, False if BLOCKED
    status: str  # "closed", "complete", "blocked", or "unknown"
    counts: dict[str, int] | None  # Severity counts if available


@dataclass
class EscalatedModels:
    """Escalated model IDs for each role."""

    fixer: str | None = None
    reviewerSecondOpinion: str | None = None
    worker: str | None = None


class RetryState:
    """Manages retry state for a single ticket.

    Provides methods to:
    - Load/save retry state from/to JSON files
    - Detect blocked status from artifacts
    - Resolve escalation models
    - Update retry counters

    Example:
        >>> state = RetryState.load(".tf/knowledge/tickets/pt-123")
        >>> if state.is_blocked():
        ...     models = state.resolve_escalation(config)
        ...     print(f"Escalating fixer to: {models.fixer}")
    """

    def __init__(
        self,
        artifact_dir: str | Path,
        ticket_id: str | None = None,
        data: RetryStateData | None = None,
    ):
        """Initialize retry state.

        Args:
            artifact_dir: Path to ticket artifact directory
            ticket_id: Ticket identifier (e.g., "pt-123")
            data: Existing retry state data (or None for new state)
        """
        self.artifact_dir = Path(artifact_dir)
        self.state_path = self.artifact_dir / "retry-state.json"

        if data:
            self._data = data
            self.ticket_id = data["ticketId"]
        elif ticket_id:
            self.ticket_id = ticket_id
            self._data = self._create_empty_state(ticket_id)
        else:
            raise ValueError("Either ticket_id or data must be provided")

    @classmethod
    def load(cls, artifact_dir: str | Path) -> RetryState | None:
        """Load retry state from artifact directory.

        Args:
            artifact_dir: Path to ticket artifact directory

        Returns:
            RetryState instance if file exists and is valid, None otherwise
        """
        path = Path(artifact_dir) / "retry-state.json"
        if not path.exists():
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # Validate required fields
            if not cls._validate_schema(data):
                return None

            ticket_id = data.get("ticketId", path.parent.name)
            return cls(artifact_dir, ticket_id=ticket_id, data=data)
        except (json.JSONDecodeError, IOError):
            return None

    @staticmethod
    def _validate_schema(data: dict[str, Any]) -> bool:
        """Validate retry state schema.

        Args:
            data: Parsed JSON data

        Returns:
            True if schema is valid, False otherwise
        """
        required = ["version", "ticketId", "attempts", "lastAttemptAt", "status"]
        return all(field in data for field in required)

    @staticmethod
    def _create_empty_state(ticket_id: str) -> RetryStateData:
        """Create empty retry state for a new ticket.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Empty retry state data structure
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "version": SCHEMA_VERSION,
            "ticketId": ticket_id,
            "attempts": [],
            "lastAttemptAt": now,
            "status": "active",
            "retryCount": 0,
        }

    def save(self) -> None:
        """Save retry state to file atomically."""
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.state_path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

        os.replace(temp_path, self.state_path)

    def start_attempt(
        self,
        trigger: str = "initial",
        quality_gate: QualityGateState | None = None,
        escalation: EscalationState | None = None,
    ) -> int:
        """Start a new attempt, or resume an in-progress attempt.

        If the last attempt has status "in_progress", resumes that attempt
        instead of creating a duplicate. This handles crashes/restarts.

        Args:
            trigger: Why this attempt was started
            quality_gate: Quality gate configuration and counts
            escalation: Escalation models for this attempt

        Returns:
            Attempt number (1-indexed)
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Check if we should resume an in-progress attempt
        if self._data["attempts"]:
            last_attempt = self._data["attempts"][-1]
            if last_attempt.get("status") == "in_progress":
                # Resume existing attempt - update trigger if provided
                if trigger:
                    last_attempt["trigger"] = trigger
                if quality_gate:
                    last_attempt["qualityGate"] = quality_gate
                if escalation:
                    last_attempt["escalation"] = escalation
                self._data["lastAttemptAt"] = now
                return last_attempt["attemptNumber"]

        attempt_number = len(self._data["attempts"]) + 1

        attempt: AttemptEntry = {
            "attemptNumber": attempt_number,
            "startedAt": now,
            "status": "in_progress",
            "trigger": trigger,
        }

        if quality_gate:
            attempt["qualityGate"] = quality_gate
        if escalation:
            attempt["escalation"] = escalation

        self._data["attempts"].append(attempt)
        self._data["lastAttemptAt"] = now

        return attempt_number

    def complete_attempt(
        self,
        status: str,
        close_summary_ref: str = "close-summary.md",
    ) -> None:
        """Complete the current attempt.

        Args:
            status: Final status ("blocked", "closed", "error")
            close_summary_ref: Path to close summary relative to artifact dir
        """
        if not self._data["attempts"]:
            raise ValueError("No in-progress attempt to complete")

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        attempt = self._data["attempts"][-1]

        attempt["completedAt"] = now
        attempt["status"] = status
        attempt["closeSummaryRef"] = close_summary_ref

        # Update aggregate status
        if status == "closed":
            self._data["status"] = "closed"
            self._data["retryCount"] = 0  # Reset on successful close
        elif status == "blocked":
            self._data["status"] = "active"  # Still active for more retries
            self._data["retryCount"] += 1

    def get_attempt_number(self) -> int:
        """Get current attempt number (1-indexed).

        Returns:
            Current attempt number, or 0 if no attempts yet
        """
        return len(self._data["attempts"])

    def get_retry_count(self) -> int:
        """Get retry count (number of BLOCKED attempts).

        Returns:
            Number of blocked attempts since last successful close
        """
        return self._data["retryCount"]

    def is_blocked(self) -> bool:
        """Check if ticket is currently blocked.

        Returns:
            True if last attempt was blocked
        """
        if not self._data["attempts"]:
            return False
        return self._data["attempts"][-1].get("status") == "blocked"

    def should_skip(self, max_retries: int) -> bool:
        """Check if ticket should be skipped due to max retries exceeded.

        Args:
            max_retries: Maximum allowed retries from config

        Returns:
            True if retry count >= max_retries
        """
        return self._data["retryCount"] >= max_retries

    def resolve_escalation(
        self,
        escalation_config: dict[str, Any],
        base_models: dict[str, str],
        next_attempt_number: int | None = None,
    ) -> EscalatedModels:
        """Resolve escalated models based on attempt number.

        Escalation curve:
        - Attempt 1: Base models (no escalation)
        - Attempt 2: Escalate fixer only
        - Attempt 3+: Escalate fixer + reviewer-second-opinion (+ worker if configured)

        Args:
            escalation_config: Escalation configuration from settings.json
            base_models: Base model IDs keyed by role name
            next_attempt_number: Explicit next attempt number (for blocked retries).
                               If None, uses current attempt count + 1.

        Returns:
            EscalatedModels with resolved model IDs
        """
        if not escalation_config.get("enabled", False):
            return EscalatedModels()

        # Use explicit next attempt number, or calculate from current attempts
        if next_attempt_number is not None:
            attempt = next_attempt_number
        else:
            # For fresh calls, use next attempt number (current count + 1)
            attempt = self.get_attempt_number() + 1

        if attempt <= 1:
            return EscalatedModels()

        models_config = escalation_config.get("models", {})
        result = EscalatedModels()

        # Attempt 2+: Escalate fixer
        if attempt >= 2:
            result.fixer = models_config.get("fixer") or base_models.get("fixer")

        # Attempt 3+: Escalate reviewer-second-opinion and optionally worker
        if attempt >= 3:
            result.reviewerSecondOpinion = (
                models_config.get("reviewerSecondOpinion")
                or base_models.get("reviewerSecondOpinion")
            )
            if models_config.get("worker"):
                result.worker = models_config.get("worker")

        return result

    def reset(self, backup: bool = True) -> None:
        """Reset retry state for a fresh attempt.

        Args:
            backup: If True, backup existing state before resetting
        """
        if backup and self.state_path.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = self.state_path.with_suffix(f".json.bak.{timestamp}")
            shutil.copy2(self.state_path, backup_path)

        self._data = self._create_empty_state(self.ticket_id)
        self.save()

    def to_dict(self) -> RetryStateData:
        """Get underlying state data.

        Returns:
            Copy of retry state data
        """
        # Return a deep copy to prevent external mutation
        return json.loads(json.dumps(self._data))


def detect_blocked_from_close_summary(close_summary_path: Path) -> BlockedResult | None:
    """Parse close-summary.md for BLOCKED status.

    Args:
        close_summary_path: Path to close-summary.md file

    Returns:
        BlockedResult if blocked, None if not found/closed
    """
    if not close_summary_path.exists():
        return None

    content = close_summary_path.read_text(encoding="utf-8")

    # Pattern: Explicit status line with BLOCKED (case-insensitive)
    # Matches: ## Status\n**BLOCKED**, ## Status\nBLOCKED, or variations
    status_match = re.search(
        r"##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?(BLOCKED)(?:\*\*)?(?:\s|$)",
        content,
        re.IGNORECASE,
    )

    if not status_match:
        return None

    # Extract review counts from Summary Statistics section
    counts: dict[str, int] = {}
    for severity in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
        sev_match = re.search(
            rf"(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)",
            content,
            re.IGNORECASE | re.MULTILINE,
        )
        counts[severity] = int(sev_match.group(1)) if sev_match else 0

    return BlockedResult(source="close-summary.md", status="blocked", counts=counts)


def detect_blocked_from_review(
    review_path: Path, fail_on: list[str]
) -> BlockedResult | None:
    """Parse review.md for nonzero failOn severity counts.

    Args:
        review_path: Path to review.md file
        fail_on: List of severity levels that block closing

    Returns:
        BlockedResult if any failOn severity has count > 0, None otherwise
    """
    if not review_path.exists():
        return None

    if not fail_on:
        return None  # Quality gate disabled

    content = review_path.read_text(encoding="utf-8")

    counts: dict[str, int] = {}
    blocked = False

    for severity in fail_on:
        # Match: ## Critical (must fix) or ## Critical
        pattern = (
            rf"^##\s*(?:\*\*)?{re.escape(severity)}(?:\*\*)?(?:\s*\([^)]+\))?"
            rf"(?:\s*:\s*\d+.*)?$"
        )
        section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

        if section_match:
            # Check if section has any items (lines starting with -)
            section_start = section_match.end()
            next_header = re.search(r"\n^##\s", content[section_start:], re.MULTILINE)
            section_end = (
                section_start + next_header.start() if next_header else len(content)
            )
            section = content[section_start:section_end]
            has_items = bool(re.search(r"\n-\s", section))

            # Check summary stats
            stat_match = re.search(
                rf"(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)",
                content,
                re.IGNORECASE | re.MULTILINE,
            )
            count = int(stat_match.group(1)) if stat_match else (1 if has_items else 0)
            counts[severity] = count

            if count > 0:
                blocked = True

    if not blocked:
        return None

    return BlockedResult(source="review.md", status="blocked", counts=counts)


def detect_quality_gate_blocked(
    artifact_dir: Path | str, fail_on: list[str]
) -> BlockedResult | None:
    """Detect if a ticket is blocked by the quality gate.

    Detection order:
    1. Parse close-summary.md for explicit BLOCKED status
    2. Fallback to review.md failOn severity counts
    3. Return None if neither indicates a block

    Args:
        artifact_dir: Path to ticket artifact directory
        fail_on: List of severity levels that block closing

    Returns:
        BlockedResult if blocked, None otherwise
    """
    path = Path(artifact_dir)
    close_summary = path / "close-summary.md"
    review = path / "review.md"

    # Primary: close-summary.md
    result = detect_blocked_from_close_summary(close_summary)
    if result:
        return result

    # Fallback: review.md
    result = detect_blocked_from_review(review, fail_on)
    if result:
        return result

    return None


def detect_close_status(close_summary_path: Path) -> CloseResult:
    """Parse close-summary.md to determine close status.

    Args:
        close_summary_path: Path to close-summary.md file

    Returns:
        CloseResult with success=True for CLOSED/COMPLETE
        CloseResult with success=False for BLOCKED
        CloseResult with success=False, status="unknown" if file missing
    """
    if not close_summary_path.exists():
        return CloseResult(success=False, status="unknown", counts=None)

    content = close_summary_path.read_text(encoding="utf-8")

    # Check for BLOCKED first
    blocked_match = re.search(
        r"##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?BLOCKED(?:\*\*)?(?:\s|$)",
        content,
        re.IGNORECASE,
    )

    if blocked_match:
        # Extract counts for blocked case
        counts: dict[str, int] = {}
        for severity in ["Critical", "Major", "Minor", "Warnings", "Suggestions"]:
            sev_match = re.search(
                rf"(?:^|\s|[-*]\s*)(?:\*\*)?{re.escape(severity)}(?:\*\*)?\s*:\s*(\d+)",
                content,
                re.IGNORECASE | re.MULTILINE,
            )
            counts[severity] = int(sev_match.group(1)) if sev_match else 0

        return CloseResult(success=False, status="blocked", counts=counts)

    # Check for successful close states
    success_match = re.search(
        r"##\s*Status\s*\n\s*(?:[-*]?\s*)?(?:\*\*)?(CLOSED|COMPLETE)(?:\*\*)?(?:\s|$)",
        content,
        re.IGNORECASE,
    )

    if success_match:
        status = success_match.group(1).lower()
        return CloseResult(success=True, status=status, counts=None)

    # Unknown status - treat as not closed
    return CloseResult(success=False, status="unknown", counts=None)


def load_escalation_config(settings_path: Path | str) -> dict[str, Any]:
    """Load escalation config from settings.json.

    Args:
        settings_path: Path to settings.json file

    Returns:
        Escalation config dict with defaults applied
    """
    path = Path(settings_path)
    if not path.exists():
        return dict(DEFAULT_ESCALATION_CONFIG)

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        workflow = data.get("workflow", {})
        escalation = workflow.get("escalation", {})

        # Merge with defaults
        config = dict(DEFAULT_ESCALATION_CONFIG)
        config.update(escalation)

        # Merge nested models dict
        default_models = DEFAULT_ESCALATION_CONFIG["models"].copy()
        default_models.update(escalation.get("models", {}))
        config["models"] = default_models

        return config
    except json.JSONDecodeError:
        # Invalid JSON - return defaults
        return dict(DEFAULT_ESCALATION_CONFIG)
    except IOError as e:
        # File exists but can't be read (permissions, etc.) - log warning and return defaults
        logger.warning(f"Cannot read settings file {path}: {e}. Using default escalation config.")
        return dict(DEFAULT_ESCALATION_CONFIG)
