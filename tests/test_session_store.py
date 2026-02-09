"""Unit tests for session_store module.

Tests cover planning session lifecycle and idempotency:
- Seed activates session
- Second seed archives previous
- Spike attaches (idempotent)
- Resume latest session
- Backlog completes and deactivates
- No duplicate entries in session JSON (spikes[], backlog tickets)
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest

from tf.session_store import (
    ACTIVE_SESSION_FILE,
    SCHEMA_VERSION,
    SESSIONS_DIR,
    STATE_ACTIVE,
    STATE_ARCHIVED,
    STATE_COMPLETED,
    add_spike_to_session,
    archive_and_create_session,
    archive_session,
    clear_active_session,
    create_session,
    find_latest_session_for_seed,
    generate_session_id,
    get_active_session_info,
    load_active_session,
    load_archived_session,
    list_archived_sessions,
    parse_session_id,
    resume_session,
    save_active_session,
    set_backlog_for_session,
    set_plan_for_session,
)


@pytest.fixture
def temp_kb_dir() -> Generator[Path, None, None]:
    """Create a temporary knowledge directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        kb_dir = Path(tmp) / ".tf" / "knowledge"
        kb_dir.mkdir(parents=True)
        yield kb_dir


@pytest.fixture
def fixed_timestamp() -> datetime:
    """Return a fixed timestamp for deterministic tests."""
    return datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc)


class TestSessionIdGeneration:
    """Tests for session ID generation and parsing."""

    def test_generate_session_id_with_timestamp(self, fixed_timestamp: datetime) -> None:
        """Generate session ID with provided timestamp."""
        session_id = generate_session_id("seed-test", fixed_timestamp)
        assert session_id == "seed-test@2026-02-06T12-00-00Z"

    def test_generate_session_id_uses_current_time_by_default(self) -> None:
        """Generate session ID uses current time when no timestamp provided."""
        session_id = generate_session_id("seed-test")
        assert session_id.startswith("seed-test@")
        assert len(session_id) > len("seed-test@")

    def test_parse_session_id_valid(self, fixed_timestamp: datetime) -> None:
        """Parse valid session ID into seed_id and timestamp."""
        session_id = "seed-test@2026-02-06T12-00-00Z"
        seed_id, timestamp = parse_session_id(session_id)
        assert seed_id == "seed-test"
        assert timestamp == fixed_timestamp

    def test_parse_session_id_invalid_format(self) -> None:
        """Raise ValueError for invalid session ID format."""
        with pytest.raises(ValueError, match="Invalid session_id format"):
            parse_session_id("invalid-no-at-sign")

    def test_parse_session_id_invalid_timestamp(self) -> None:
        """Raise ValueError for invalid timestamp in session ID."""
        with pytest.raises(ValueError, match="Invalid timestamp"):
            parse_session_id("seed-test@invalid-timestamp")


class TestSessionCreation:
    """Tests for create_session function."""

    def test_create_session_structure(self, fixed_timestamp: datetime) -> None:
        """Create session returns properly structured session dict."""
        session = create_session("seed-test", timestamp=fixed_timestamp)

        assert session["schema_version"] == SCHEMA_VERSION
        assert session["session_id"] == "seed-test@2026-02-06T12-00-00Z"
        assert session["state"] == STATE_ACTIVE
        assert session["root_seed"] == "seed-test"
        assert session["spikes"] == []
        assert session["plan"] is None
        assert session["backlog"] is None
        assert session["created"] == "2026-02-06T12:00:00Z"
        assert session["updated"] == "2026-02-06T12:00:00Z"
        assert session["completed_at"] is None

    def test_create_session_uses_current_time_by_default(self) -> None:
        """Create session uses current time when no timestamp provided."""
        before = datetime.now(timezone.utc).replace(microsecond=0)
        session = create_session("seed-test")
        after = datetime.now(timezone.utc).replace(microsecond=0)

        assert session["root_seed"] == "seed-test"
        assert session["state"] == STATE_ACTIVE
        # Verify timestamps parse correctly and are within expected range
        created = datetime.fromisoformat(session["created"].replace("Z", "+00:00"))
        assert before <= created <= after


class TestSessionSaveAndLoad:
    """Tests for saving and loading active sessions."""

    def test_save_active_session_creates_file(self, temp_kb_dir: Path) -> None:
        """Save active session creates JSON file."""
        session = create_session("seed-test")
        active_path = save_active_session(session, temp_kb_dir)

        assert active_path.exists()
        assert active_path.name == ACTIVE_SESSION_FILE

    def test_save_active_session_updates_timestamp(self, temp_kb_dir: Path) -> None:
        """Save updates the 'updated' timestamp to current time."""
        before = datetime.now(timezone.utc).replace(microsecond=0)
        session = create_session("seed-test")
        # Set an old timestamp to verify it gets updated
        session["updated"] = "2020-01-01T00:00:00Z"

        save_active_session(session, temp_kb_dir)
        after = datetime.now(timezone.utc).replace(microsecond=0)

        # Verify timestamp was refreshed to current time range
        updated_dt = datetime.fromisoformat(session["updated"].replace("Z", "+00:00"))
        assert before <= updated_dt <= after

    def test_load_active_session_returns_none_when_missing(self, temp_kb_dir: Path) -> None:
        """Load returns None when no active session exists."""
        result = load_active_session(temp_kb_dir)
        assert result is None

    def test_load_active_session_returns_data(self, temp_kb_dir: Path) -> None:
        """Load returns session data when file exists."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        loaded = load_active_session(temp_kb_dir)
        assert loaded is not None
        assert loaded["root_seed"] == "seed-test"
        assert loaded["state"] == STATE_ACTIVE

    def test_load_active_session_invalid_schema_returns_none(self, temp_kb_dir: Path) -> None:
        """Load returns None when schema version doesn't match."""
        active_path = temp_kb_dir / ACTIVE_SESSION_FILE
        invalid_session = {
            "schema_version": 999,  # Invalid version
            "session_id": "test",
            "state": STATE_ACTIVE,
        }
        active_path.write_text(json.dumps(invalid_session))

        result = load_active_session(temp_kb_dir)
        assert result is None

    def test_load_active_session_invalid_json_returns_none(self, temp_kb_dir: Path) -> None:
        """Load returns None when JSON is invalid."""
        active_path = temp_kb_dir / ACTIVE_SESSION_FILE
        active_path.write_text("{invalid json")

        result = load_active_session(temp_kb_dir)
        assert result is None


class TestClearActiveSession:
    """Tests for clearing active session."""

    def test_clear_active_session_removes_file(self, temp_kb_dir: Path) -> None:
        """Clear removes active session file."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        result = clear_active_session(temp_kb_dir)
        assert result is True
        assert not (temp_kb_dir / ACTIVE_SESSION_FILE).exists()

    def test_clear_active_session_returns_false_when_missing(self, temp_kb_dir: Path) -> None:
        """Clear returns False when no active session exists."""
        result = clear_active_session(temp_kb_dir)
        assert result is False


class TestArchiveSession:
    """Tests for archiving sessions."""

    def test_archive_session_creates_file(self, temp_kb_dir: Path) -> None:
        """Archive creates file in sessions directory."""
        session = create_session("seed-test")
        archive_path = archive_session(session, temp_kb_dir)

        assert archive_path.exists()
        assert archive_path.parent.name == SESSIONS_DIR
        assert archive_path.name.endswith(".json")

    def test_archive_session_requires_session_id(self, temp_kb_dir: Path) -> None:
        """Archive raises ValueError when session has no session_id."""
        session = {"state": STATE_ACTIVE}  # No session_id

        with pytest.raises(ValueError, match="session_id"):
            archive_session(session, temp_kb_dir)


class TestSessionLifecycle:
    """Tests for complete session lifecycle: activate, archive, resume, complete."""

    def test_seed_activates_session(self, temp_kb_dir: Path) -> None:
        """First seed activation creates active session."""
        session = create_session("seed-first")
        save_active_session(session, temp_kb_dir)

        loaded = load_active_session(temp_kb_dir)
        assert loaded is not None
        assert loaded["root_seed"] == "seed-first"
        assert loaded["state"] == STATE_ACTIVE

    def test_second_seed_archives_previous(self, temp_kb_dir: Path) -> None:
        """Second seed activation archives previous session."""
        # First seed
        session1 = create_session("seed-first")
        save_active_session(session1, temp_kb_dir)

        # Second seed - archive and create
        new_session, previous, archive_path = archive_and_create_session(
            "seed-second", temp_kb_dir
        )

        # Verify previous was archived
        assert previous is not None
        assert previous["root_seed"] == "seed-first"
        assert previous["state"] == STATE_ARCHIVED
        assert archive_path is not None
        assert archive_path.exists()

        # Verify new session is active
        assert new_session["root_seed"] == "seed-second"
        assert new_session["state"] == STATE_ACTIVE

        loaded = load_active_session(temp_kb_dir)
        assert loaded["root_seed"] == "seed-second"

    def test_spike_attaches_to_session(self, temp_kb_dir: Path) -> None:
        """Spike ID is added to active session."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        result = add_spike_to_session("spike-research-topic", temp_kb_dir)
        assert result is True

        loaded = load_active_session(temp_kb_dir)
        assert "spike-research-topic" in loaded["spikes"]
        assert len(loaded["spikes"]) == 1

    def test_spike_attach_no_active_session(self, temp_kb_dir: Path) -> None:
        """Add spike returns False when no active session."""
        result = add_spike_to_session("spike-test", temp_kb_dir)
        assert result is False

    def test_resume_latest_session(self, temp_kb_dir: Path) -> None:
        """Resume makes archived session active, archives current."""
        # Create first session and archive it
        session1 = create_session("seed-first")
        save_active_session(session1, temp_kb_dir)
        archive_session(session1, temp_kb_dir)

        # Create second session (active)
        session2 = create_session("seed-second")
        save_active_session(session2, temp_kb_dir)

        # Resume first session
        resumed = resume_session(session1["session_id"], temp_kb_dir)

        assert resumed is not None
        assert resumed["session_id"] == session1["session_id"]
        assert resumed["state"] == STATE_ACTIVE

        # Verify second session was archived
        archived_session2 = load_archived_session(session2["session_id"], temp_kb_dir)
        assert archived_session2 is not None
        assert archived_session2["state"] == STATE_ARCHIVED

    def test_backlog_completes_and_deactivates(self, temp_kb_dir: Path) -> None:
        """Setting backlog completes session and clears active."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        result = set_backlog_for_session(
            "test-topic",
            "backlog.md",
            ["TKT-1", "TKT-2"],
            temp_kb_dir
        )

        assert result is True

        # Active session should be cleared
        active = load_active_session(temp_kb_dir)
        assert active is None

        # Session should be archived as completed
        archived = load_archived_session(session["session_id"], temp_kb_dir)
        assert archived is not None
        assert archived["state"] == STATE_COMPLETED
        assert archived["backlog"] is not None
        assert archived["backlog"]["topic"] == "test-topic"
        assert archived["backlog"]["tickets"] == ["TKT-1", "TKT-2"]
        assert archived["completed_at"] is not None

    def test_backlog_no_active_session(self, temp_kb_dir: Path) -> None:
        """Set backlog returns False when no active session."""
        result = set_backlog_for_session(
            "test-topic",
            "backlog.md",
            ["TKT-1"],
            temp_kb_dir
        )
        assert result is False


class TestIdempotency:
    """Tests for idempotency: no duplicates in session JSON."""

    def test_no_duplicate_spikes_in_session_json(self, temp_kb_dir: Path) -> None:
        """Adding same spike twice results in single entry."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        # Add same spike twice
        add_spike_to_session("spike-research", temp_kb_dir)
        add_spike_to_session("spike-research", temp_kb_dir)

        loaded = load_active_session(temp_kb_dir)
        assert loaded["spikes"].count("spike-research") == 1
        assert len(loaded["spikes"]) == 1

    def test_multiple_unique_spikes_allowed(self, temp_kb_dir: Path) -> None:
        """Adding different spikes creates multiple entries."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        add_spike_to_session("spike-research-1", temp_kb_dir)
        add_spike_to_session("spike-research-2", temp_kb_dir)

        loaded = load_active_session(temp_kb_dir)
        assert len(loaded["spikes"]) == 2
        assert "spike-research-1" in loaded["spikes"]
        assert "spike-research-2" in loaded["spikes"]

    def test_no_duplicate_tickets_in_backlog(self, temp_kb_dir: Path) -> None:
        """Duplicate ticket IDs are deduplicated in backlog."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        # Create backlog with duplicate tickets
        set_backlog_for_session(
            "test-topic",
            "backlog.md",
            ["TKT-1", "TKT-2", "TKT-1", "TKT-3", "TKT-2"],  # Duplicates
            temp_kb_dir
        )

        archived = load_archived_session(session["session_id"], temp_kb_dir)
        tickets = archived["backlog"]["tickets"]

        # Should be deduplicated while preserving order
        assert tickets == ["TKT-1", "TKT-2", "TKT-3"]
        assert len(tickets) == 3


class TestPlanManagement:
    """Tests for plan attachment to session."""

    def test_set_plan_for_session(self, temp_kb_dir: Path) -> None:
        """Set plan ID for active session."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        result = set_plan_for_session("plan-my-feature", temp_kb_dir)
        assert result is True

        loaded = load_active_session(temp_kb_dir)
        assert loaded["plan"] == "plan-my-feature"

    def test_set_plan_no_active_session(self, temp_kb_dir: Path) -> None:
        """Set plan returns False when no active session."""
        result = set_plan_for_session("plan-test", temp_kb_dir)
        assert result is False


class TestListAndFindSessions:
    """Tests for listing and finding archived sessions."""

    def test_list_archived_sessions_sorted(self, temp_kb_dir: Path) -> None:
        """List returns sessions sorted by created time (newest first)."""
        # Create and archive multiple sessions with explicit timestamps
        ts1 = datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc)
        session1 = create_session("seed-first", timestamp=ts1)
        archive_session(session1, temp_kb_dir)

        ts2 = datetime(2026, 2, 3, 10, 0, 0, tzinfo=timezone.utc)
        session2 = create_session("seed-second", timestamp=ts2)
        archive_session(session2, temp_kb_dir)

        ts3 = datetime(2026, 2, 2, 10, 0, 0, tzinfo=timezone.utc)
        session3 = create_session("seed-third", timestamp=ts3)
        archive_session(session3, temp_kb_dir)

        sessions = list_archived_sessions(knowledge_dir=temp_kb_dir)

        assert len(sessions) == 3
        # Should be sorted newest first: second, third, first
        assert sessions[0]["root_seed"] == "seed-second"
        assert sessions[1]["root_seed"] == "seed-third"
        assert sessions[2]["root_seed"] == "seed-first"

    def test_list_archived_sessions_filter_by_seed(self, temp_kb_dir: Path) -> None:
        """List filters sessions by seed_id."""
        session1 = create_session("seed-alpha")
        archive_session(session1, temp_kb_dir)

        session2 = create_session("seed-beta")
        archive_session(session2, temp_kb_dir)

        sessions = list_archived_sessions(seed_id="seed-alpha", knowledge_dir=temp_kb_dir)

        assert len(sessions) == 1
        assert sessions[0]["root_seed"] == "seed-alpha"

    def test_list_archived_sessions_empty_when_none(self, temp_kb_dir: Path) -> None:
        """List returns empty list when no sessions exist."""
        sessions = list_archived_sessions(knowledge_dir=temp_kb_dir)
        assert sessions == []

    def test_find_latest_session_for_seed(self, temp_kb_dir: Path) -> None:
        """Find returns most recent session for seed."""
        # Create multiple sessions for same seed with explicit timestamps
        ts1 = datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc)
        session1 = create_session("seed-test", timestamp=ts1)
        archive_session(session1, temp_kb_dir)

        ts2 = datetime(2026, 2, 3, 10, 0, 0, tzinfo=timezone.utc)
        session2 = create_session("seed-test", timestamp=ts2)
        archive_session(session2, temp_kb_dir)

        latest = find_latest_session_for_seed("seed-test", temp_kb_dir)

        assert latest is not None
        assert latest["session_id"] == session2["session_id"]

    def test_find_latest_session_returns_none_when_missing(self, temp_kb_dir: Path) -> None:
        """Find returns None when no sessions for seed."""
        result = find_latest_session_for_seed("nonexistent-seed", temp_kb_dir)
        assert result is None

    def test_load_archived_session_returns_none_when_missing(self, temp_kb_dir: Path) -> None:
        """Load archived returns None when session doesn't exist."""
        result = load_archived_session("nonexistent-session", temp_kb_dir)
        assert result is None


class TestGetActiveSessionInfo:
    """Tests for get_active_session_info helper."""

    def test_get_info_returns_none_when_no_session(self, temp_kb_dir: Path) -> None:
        """Get info returns None when no active session."""
        result = get_active_session_info(temp_kb_dir)
        assert result is None

    def test_get_info_returns_summary(self, temp_kb_dir: Path) -> None:
        """Get info returns session summary."""
        session = create_session("seed-test")
        session["spikes"] = ["spike-1", "spike-2"]
        session["plan"] = "plan-feature"
        save_active_session(session, temp_kb_dir)

        info = get_active_session_info(temp_kb_dir)

        assert info is not None
        assert info["session_id"] == session["session_id"]
        assert info["root_seed"] == "seed-test"
        assert info["state"] == STATE_ACTIVE
        assert info["spike_count"] == 2
        assert info["has_plan"] is True
        assert info["has_backlog"] is False
        assert info["ticket_count"] == 0

    def test_get_info_with_backlog(self, temp_kb_dir: Path) -> None:
        """Get info returns correct ticket count with backlog."""
        session = create_session("seed-test")
        session["backlog"] = {
            "topic": "test",
            "backlog_md": "backlog.md",
            "tickets": ["TKT-1", "TKT-2", "TKT-3"]
        }
        save_active_session(session, temp_kb_dir)

        info = get_active_session_info(temp_kb_dir)

        assert info["has_backlog"] is True
        assert info["ticket_count"] == 3


class TestResumeSession:
    """Tests for resume_session function."""

    def test_resume_session_returns_none_when_missing(self, temp_kb_dir: Path) -> None:
        """Resume returns None when session doesn't exist."""
        result = resume_session("nonexistent", temp_kb_dir)
        assert result is None

    def test_resume_updates_timestamps(self, temp_kb_dir: Path) -> None:
        """Resume updates the session timestamps to current time."""
        # Create and archive a session with old timestamp
        ts = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        session = create_session("seed-test", timestamp=ts)
        archive_session(session, temp_kb_dir)

        before = datetime.now(timezone.utc).replace(microsecond=0)
        # Resume the session
        resumed = resume_session(session["session_id"], temp_kb_dir)
        after = datetime.now(timezone.utc).replace(microsecond=0)

        # Verify timestamp was refreshed to current time range
        updated_dt = datetime.fromisoformat(resumed["updated"].replace("Z", "+00:00"))
        assert before <= updated_dt <= after


class TestAtomicOperations:
    """Tests for atomic write/read operations."""

    def test_atomic_write_no_partial_files(self, temp_kb_dir: Path) -> None:
        """Atomic write leaves no temp files behind on success."""
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        # Should only have the active session file, no .tmp files
        json_files = list(temp_kb_dir.glob("*.json"))
        tmp_files = list(temp_kb_dir.glob("*.tmp"))

        assert len(json_files) == 1
        assert len(tmp_files) == 0

    def test_atomic_writes_produce_valid_readable_files(self, temp_kb_dir: Path) -> None:
        """Atomic writes produce complete, valid files that can be read successfully."""
        # Write a valid session
        session = create_session("seed-test")
        save_active_session(session, temp_kb_dir)

        # Reader should see complete valid data (atomicity ensures no partial reads)
        loaded = load_active_session(temp_kb_dir)
        assert loaded is not None
        assert loaded["schema_version"] == SCHEMA_VERSION
        assert "session_id" in loaded
