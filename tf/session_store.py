"""Planning session storage with atomic read/write operations.

This module provides idempotent, atomic operations for managing planning
session state files under the TF knowledge directory.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Schema version for session files
SCHEMA_VERSION = 1

# Default knowledge directory (can be overridden via env/config)
DEFAULT_KNOWLEDGE_DIR = ".tf/knowledge"

# Session state values
STATE_ACTIVE = "active"
STATE_COMPLETED = "completed"
STATE_ARCHIVED = "archived"

# File names
ACTIVE_SESSION_FILE = ".active-planning.json"
SESSIONS_DIR = "sessions"


def _get_knowledge_dir(knowledge_dir: Optional[Path] = None) -> Path:
    """Resolve the knowledge directory path.
    
    Priority:
    1. Explicitly provided path
    2. TF_KNOWLEDGE_DIR environment variable
    3. Current working directory / DEFAULT_KNOWLEDGE_DIR
    """
    if knowledge_dir is not None:
        return knowledge_dir
    
    env_dir = os.environ.get("TF_KNOWLEDGE_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    
    return Path.cwd() / DEFAULT_KNOWLEDGE_DIR


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON to path atomically using temp file + rename.
    
    This ensures readers never see a partially written file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use a temp file in the same directory to ensure rename is atomic
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.rename(temp_path, path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    """Read and parse JSON from path. Returns None if file doesn't exist or is invalid."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def generate_session_id(seed_id: str, timestamp: Optional[datetime] = None) -> str:
    """Generate a session ID from seed_id and timestamp.
    
    Format: {seed_id}@{YYYY-MM-DDTHH-MM-SSZ}
    The timestamp uses filename-safe format (hyphens instead of colons).
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    # Format timestamp with hyphens for filename safety
    ts_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{seed_id}@{ts_str}"


def parse_session_id(session_id: str) -> tuple[str, datetime]:
    """Parse a session ID into (seed_id, timestamp).
    
    Raises ValueError if the session_id format is invalid.
    """
    if "@" not in session_id:
        raise ValueError(f"Invalid session_id format: {session_id}")
    
    seed_id, ts_str = session_id.rsplit("@", 1)
    
    # Parse timestamp (with hyphens instead of colons)
    try:
        timestamp = datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp in session_id: {session_id}") from exc
    
    return seed_id, timestamp


def create_session(
    seed_id: str,
    knowledge_dir: Optional[Path] = None,
    timestamp: Optional[datetime] = None
) -> dict[str, Any]:
    """Create a new active session.
    
    Returns the session data dict. This does NOT check for existing active sessions.
    Use archive_and_create_session() to handle switching from an existing session.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    session_id = generate_session_id(seed_id, timestamp)
    iso_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    session = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "state": STATE_ACTIVE,
        "root_seed": seed_id,
        "spikes": [],
        "plan": None,
        "backlog": None,
        "created": iso_timestamp,
        "updated": iso_timestamp,
        "completed_at": None
    }
    
    return session


def save_active_session(
    session: dict[str, Any],
    knowledge_dir: Optional[Path] = None
) -> Path:
    """Save session as the active session file.
    
    Updates the 'updated' timestamp before saving. Uses atomic write.
    Returns the path to the active session file.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    active_path = kd / ACTIVE_SESSION_FILE
    
    # Update timestamp
    session["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    _atomic_write_json(active_path, session)
    return active_path


def load_active_session(
    knowledge_dir: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    """Load the currently active session, if any.
    
    Returns None if no active session exists.
    Validates schema_version and returns None if mismatch.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    active_path = kd / ACTIVE_SESSION_FILE
    
    data = _read_json(active_path)
    if data is None:
        return None
    
    # Validate schema version
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    
    return data


def clear_active_session(knowledge_dir: Optional[Path] = None) -> bool:
    """Remove the active session file.
    
    Returns True if a file was removed, False if no active session existed.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    active_path = kd / ACTIVE_SESSION_FILE
    
    if active_path.exists():
        active_path.unlink()
        return True
    return False


def archive_session(
    session: dict[str, Any],
    knowledge_dir: Optional[Path] = None
) -> Path:
    """Archive a session to the sessions directory.
    
    Uses atomic write. Returns the path to the archived session file.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    session_id = session.get("session_id")
    
    if not session_id:
        raise ValueError("Session must have a session_id to be archived")
    
    sessions_dir = kd / SESSIONS_DIR
    archive_path = sessions_dir / f"{session_id}.json"
    
    _atomic_write_json(archive_path, session)
    return archive_path


def archive_and_create_session(
    seed_id: str,
    knowledge_dir: Optional[Path] = None,
    timestamp: Optional[datetime] = None
) -> tuple[dict[str, Any], Optional[dict[str, Any]], Optional[Path]]:
    """Archive any existing active session and create a new one.
    
    Returns:
        - New session dict
        - Previous session dict (or None if no active session existed)
        - Path to archived previous session (or None)
    """
    kd = _get_knowledge_dir(knowledge_dir)
    
    # Load and archive existing active session
    previous = load_active_session(kd)
    archive_path: Optional[Path] = None
    
    if previous is not None:
        # Mark as archived and update timestamp
        previous["state"] = STATE_ARCHIVED
        previous["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        archive_path = archive_session(previous, kd)
    
    # Create and save new session
    new_session = create_session(seed_id, kd, timestamp)
    save_active_session(new_session, kd)
    
    return new_session, previous, archive_path


def list_archived_sessions(
    seed_id: Optional[str] = None,
    knowledge_dir: Optional[Path] = None
) -> list[dict[str, Any]]:
    """List archived sessions, optionally filtered by seed_id.
    
    Returns list of session dicts sorted by creation time (newest first).
    """
    kd = _get_knowledge_dir(knowledge_dir)
    sessions_dir = kd / SESSIONS_DIR
    
    if not sessions_dir.exists():
        return []
    
    sessions: list[dict[str, Any]] = []
    
    for path in sessions_dir.glob("*.json"):
        data = _read_json(path)
        if data is None:
            continue
        
        # Validate schema version
        if data.get("schema_version") != SCHEMA_VERSION:
            continue
        
        # Filter by seed_id if specified
        if seed_id is not None and data.get("root_seed") != seed_id:
            continue
        
        sessions.append(data)
    
    # Sort by created timestamp (newest first)
    sessions.sort(key=lambda s: s.get("created", ""), reverse=True)
    return sessions


def load_archived_session(
    session_id: str,
    knowledge_dir: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    """Load a specific archived session by ID.
    
    Returns None if not found or invalid schema version.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    sessions_dir = kd / SESSIONS_DIR
    archive_path = sessions_dir / f"{session_id}.json"
    
    data = _read_json(archive_path)
    if data is None:
        return None
    
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    
    return data


def resume_session(
    session_id: str,
    knowledge_dir: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    """Resume an archived session by making it the active session.
    
    Archives any currently active session first.
    Returns the resumed session dict, or None if session_id not found.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    
    # Load the archived session
    session = load_archived_session(session_id, kd)
    if session is None:
        return None
    
    # Archive current active session if exists
    current = load_active_session(kd)
    if current is not None:
        current["state"] = STATE_ARCHIVED
        current["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        archive_session(current, kd)
    
    # Restore as active
    session["state"] = STATE_ACTIVE
    session["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_active_session(session, kd)
    
    return session


def find_latest_session_for_seed(
    seed_id: str,
    knowledge_dir: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    """Find the most recent archived session for a given seed_id.
    
    Returns None if no sessions found for the seed.
    """
    sessions = list_archived_sessions(seed_id, knowledge_dir)
    return sessions[0] if sessions else None


def add_spike_to_session(
    spike_id: str,
    knowledge_dir: Optional[Path] = None
) -> bool:
    """Add a spike ID to the active session.
    
    Returns True if added (or already present), False if no active session.
    Idempotent: does not add duplicates.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    session = load_active_session(kd)
    
    if session is None:
        return False
    
    spikes = session.setdefault("spikes", [])
    if spike_id not in spikes:
        spikes.append(spike_id)
        save_active_session(session, kd)
    
    return True


def set_plan_for_session(
    plan_id: str,
    knowledge_dir: Optional[Path] = None
) -> bool:
    """Set the plan ID for the active session.
    
    Returns True if set, False if no active session.
    """
    kd = _get_knowledge_dir(knowledge_dir)
    session = load_active_session(kd)
    
    if session is None:
        return False
    
    session["plan"] = plan_id
    save_active_session(session, kd)
    return True


def set_backlog_for_session(
    topic: str,
    backlog_md: str,
    tickets: list[str],
    knowledge_dir: Optional[Path] = None
) -> bool:
    """Set the backlog info and mark session as completed.
    
    Returns True if set, False if no active session.
    After calling this, the active session file is removed (deactivated).
    """
    kd = _get_knowledge_dir(knowledge_dir)
    session = load_active_session(kd)
    
    if session is None:
        return False
    
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    session["backlog"] = {
        "topic": topic,
        "backlog_md": backlog_md,
        "tickets": list(dict.fromkeys(tickets))  # Dedupe while preserving order
    }
    session["state"] = STATE_COMPLETED
    session["completed_at"] = now
    session["updated"] = now
    
    # Archive the completed session
    archive_session(session, kd)
    
    # Clear active session (deactivate)
    clear_active_session(kd)
    
    return True


def get_active_session_info(
    knowledge_dir: Optional[Path] = None
) -> Optional[dict[str, Any]]:
    """Get a summary of the active session for display.
    
    Returns a dict with session_id, root_seed, state, and counts,
    or None if no active session.
    """
    session = load_active_session(knowledge_dir)
    if session is None:
        return None
    
    spikes = session.get("spikes", [])
    backlog = session.get("backlog")
    
    return {
        "session_id": session.get("session_id"),
        "root_seed": session.get("root_seed"),
        "state": session.get("state"),
        "spike_count": len(spikes),
        "has_plan": session.get("plan") is not None,
        "has_backlog": backlog is not None,
        "ticket_count": len(backlog.get("tickets", [])) if backlog else 0,
        "updated": session.get("updated")
    }
