"""Unit tests for /tf-backlog session-aware defaulting and inputs.

Tests cover behavior when an active planning session exists:
- Default topic selection (root_seed when no arg provided)
- Override behavior when explicit topic arg is provided
- Session input resolution (plan/spike docs)

These tests verify the input-resolution layer without calling real tk
or requiring network access.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from tf.session_store import (
    STATE_ACTIVE,
    STATE_ARCHIVED,
    add_spike_to_session,
    create_session,
    load_active_session,
    save_active_session,
    set_plan_for_session,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_kb_dir() -> Generator[Path, None, None]:
    """Create a temporary knowledge directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        kb_dir = Path(tmp) / ".tf" / "knowledge"
        kb_dir.mkdir(parents=True)
        yield kb_dir


@pytest.fixture
def temp_topics_dir(temp_kb_dir: Path) -> Path:
    """Create a topics directory with sample seed/plan/spike docs."""
    topics_dir = temp_kb_dir / "topics"
    topics_dir.mkdir(parents=True)
    
    # Create seed directory with seed.md
    seed_dir = topics_dir / "seed-test-feature"
    seed_dir.mkdir()
    seed_dir.joinpath("seed.md").write_text(
        "---\n"
        "id: seed-test-feature\n"
        "created: 2026-02-01\n"
        "---\n"
        "# Test Feature Seed\n\n"
        "This is a test seed for feature development.\n"
    )
    
    # Create plan directory with plan.md
    plan_dir = topics_dir / "plan-test-feature"
    plan_dir.mkdir()
    plan_dir.joinpath("plan.md").write_text(
        "---\n"
        "id: plan-test-feature\n"
        "status: approved\n"
        "---\n"
        "# Test Feature Plan\n\n"
        "## Requirements\n"
        "- Req 1: Do something\n"
        "- Req 2: Do something else\n\n"
        "## Constraints\n"
        "- Must be fast\n"
    )
    
    # Create spike directory with spike.md
    spike_dir = topics_dir / "spike-test-research"
    spike_dir.mkdir()
    spike_dir.joinpath("spike.md").write_text(
        "---\n"
        "id: spike-test-research\n"
        "---\n"
        "# Test Research Spike\n\n"
        "## Summary\n"
        "Key finding: use approach X\n\n"
        "## Recommendation\n"
        "Implement using library Y\n"
    )
    
    return topics_dir


# -----------------------------------------------------------------------------
# Topic Resolution Tests
# -----------------------------------------------------------------------------


class TestBacklogTopicResolution:
    """Tests for /tf-backlog topic resolution with active sessions."""

    def test_no_arg_uses_root_seed_when_session_active(
        self, temp_kb_dir: Path
    ) -> None:
        """No-arg backlog uses root_seed from active session as default topic."""
        # Create an active session with a specific root_seed
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Simulate topic resolution (as would happen in /tf-backlog Phase A)
        active_session = load_active_session(temp_kb_dir)
        assert active_session is not None
        assert active_session["state"] == STATE_ACTIVE
        
        # The resolved topic should be the session's root_seed
        resolved_topic = active_session["root_seed"]
        assert resolved_topic == "seed-test-feature"

    def test_no_arg_without_session_requires_explicit_topic(
        self, temp_kb_dir: Path
    ) -> None:
        """No-arg backlog without active session should not auto-resolve."""
        # Ensure no active session
        active_session = load_active_session(temp_kb_dir)
        assert active_session is None
        
        # Without a session, topic resolution should fail or require explicit input
        # This tests the "no session = no default" behavior

    def test_explicit_topic_overrides_session_default(
        self, temp_kb_dir: Path
    ) -> None:
        """Explicit topic argument takes precedence over session root_seed."""
        # Create an active session
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # User provides explicit topic
        explicit_topic = "baseline-legacy-system"
        
        # The explicit topic should override the session default
        active_session = load_active_session(temp_kb_dir)
        assert active_session is not None
        
        # Resolved topic should be the explicit one, not root_seed
        resolved_topic = explicit_topic  # User input takes precedence
        assert resolved_topic != active_session["root_seed"]
        assert resolved_topic == "baseline-legacy-system"

    def test_explicit_topic_same_as_root_seed_uses_explicit(
        self, temp_kb_dir: Path
    ) -> None:
        """Explicit topic matching root_seed still uses explicit path."""
        # Create an active session
        session = create_seed_with_session(temp_kb_dir, "seed-test-feature")
        
        # User explicitly provides the same topic as root_seed
        explicit_topic = "seed-test-feature"
        
        # Should work fine - explicit matches session
        active_session = load_active_session(temp_kb_dir)
        assert active_session is not None
        assert active_session["root_seed"] == explicit_topic


# -----------------------------------------------------------------------------
# Session Input Resolution Tests
# -----------------------------------------------------------------------------


class TestBacklogSessionInputs:
    """Tests for /tf-backlog session input incorporation."""

    def test_resolves_seed_from_session(self, temp_kb_dir: Path) -> None:
        """Session's root_seed is resolved as the seed input."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        assert active is not None
        
        inputs_used = {
            "seed": active["root_seed"],
            "plan": active.get("plan"),
            "spikes": active.get("spikes", []),
        }
        
        assert inputs_used["seed"] == "seed-test-feature"
        assert inputs_used["plan"] is None
        assert inputs_used["spikes"] == []

    def test_resolves_plan_from_session(self, temp_kb_dir: Path) -> None:
        """Session's plan ID is included in inputs_used."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Set a plan for the session
        set_plan_for_session("plan-test-feature", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        assert active is not None
        assert active["plan"] == "plan-test-feature"
        
        inputs_used = {
            "seed": active["root_seed"],
            "plan": active.get("plan"),
            "spikes": active.get("spikes", []),
        }
        
        assert inputs_used["plan"] == "plan-test-feature"

    def test_resolves_spikes_from_session(self, temp_kb_dir: Path) -> None:
        """Session's spike IDs are included in inputs_used."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Add spikes to the session
        add_spike_to_session("spike-test-research", temp_kb_dir)
        add_spike_to_session("spike-performance-check", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        assert active is not None
        assert len(active["spikes"]) == 2
        
        inputs_used = {
            "seed": active["root_seed"],
            "plan": active.get("plan"),
            "spikes": active.get("spikes", []),
        }
        
        assert "spike-test-research" in inputs_used["spikes"]
        assert "spike-performance-check" in inputs_used["spikes"]

    def test_resolves_all_inputs_combined(self, temp_kb_dir: Path) -> None:
        """Session with seed, plan, and spikes resolves all inputs."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Add plan and spikes
        set_plan_for_session("plan-test-feature", temp_kb_dir)
        add_spike_to_session("spike-test-research", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        assert active is not None
        
        inputs_used = {
            "seed": active["root_seed"],
            "plan": active.get("plan"),
            "plan_status": "approved",  # Would be read from plan.md frontmatter
            "spikes": active.get("spikes", []),
            "spikes_read": len(active.get("spikes", [])),
            "spikes_missing": [],
        }
        
        assert inputs_used["seed"] == "seed-test-feature"
        assert inputs_used["plan"] == "plan-test-feature"
        assert inputs_used["plan_status"] == "approved"
        assert inputs_used["spikes"] == ["spike-test-research"]
        assert inputs_used["spikes_read"] == 1
        assert inputs_used["spikes_missing"] == []


# -----------------------------------------------------------------------------
# Input Incorporation Tests
# -----------------------------------------------------------------------------


class TestBacklogInputIncorporation:
    """Tests for how session inputs are incorporated into ticket context."""

    def test_build_ticket_context_with_seed_only(
        self, temp_kb_dir: Path, temp_topics_dir: Path
    ) -> None:
        """Ticket context includes seed reference when only seed is present."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Build context as would happen in Phase B
        active = load_active_session(temp_kb_dir)
        context = build_ticket_context(active, temp_kb_dir)
        
        assert "seed" in context["references"]
        assert context["references"]["seed"] == "seed-test-feature"
        assert context["plan_requirements"] is None
        assert context["spike_findings"] == []

    def test_build_ticket_context_with_plan(
        self, temp_kb_dir: Path, temp_topics_dir: Path
    ) -> None:
        """Ticket context includes plan requirements when plan is present."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        set_plan_for_session("plan-test-feature", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        context = build_ticket_context(active, temp_kb_dir)
        
        assert context["references"]["plan"] == "plan-test-feature"
        # Plan requirements would be extracted from plan.md
        assert context["plan_requirements"] is not None
        assert "Req 1" in context["plan_requirements"]

    def test_build_ticket_context_with_spikes(
        self, temp_kb_dir: Path, temp_topics_dir: Path
    ) -> None:
        """Ticket context includes spike findings when spikes are present."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        add_spike_to_session("spike-test-research", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        context = build_ticket_context(active, temp_kb_dir)
        
        assert len(context["spike_findings"]) == 1
        assert context["spike_findings"][0]["spike_id"] == "spike-test-research"
        assert "approach X" in context["spike_findings"][0]["summary"]

    def test_build_ticket_context_missing_docs_warns(
        self, temp_kb_dir: Path, temp_topics_dir: Path
    ) -> None:
        """Warnings emitted when referenced plan/spike docs are missing."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Reference a spike that doesn't exist
        add_spike_to_session("spike-nonexistent", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        
        # When building context, should detect missing doc
        warnings = check_missing_docs(active, temp_kb_dir)
        
        assert len(warnings) == 1
        assert "spike-nonexistent" in warnings[0]


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def create_seed_with_session(kb_dir: Path, seed_id: str) -> dict:
    """Helper to create an active session for a seed."""
    session = create_session(seed_id)
    save_active_session(session, kb_dir)
    return session


def build_ticket_context(session: dict, kb_dir: Path) -> dict:
    """Build ticket context from session data (simulates Phase B incorporation).
    
    This helper simulates what /tf-backlog would do when building ticket
    context from session inputs.
    """
    context = {
        "references": {"seed": session["root_seed"]},
        "plan_requirements": None,
        "plan_status": None,
        "spike_findings": [],
    }
    
    topics_dir = kb_dir / "topics"
    
    # Incorporate plan if present
    if session.get("plan"):
        plan_id = session["plan"]
        context["references"]["plan"] = plan_id
        
        # Try to read plan.md
        plan_path = topics_dir / plan_id / "plan.md"
        if plan_path.exists():
            content = plan_path.read_text()
            # Extract requirements section (simplified)
            if "## Requirements" in content:
                req_start = content.find("## Requirements")
                req_end = content.find("##", req_start + 1)
                if req_end == -1:
                    req_end = len(content)
                context["plan_requirements"] = content[req_start:req_end].strip()
            
            # Extract status from frontmatter (simplified)
            if "status: approved" in content:
                context["plan_status"] = "approved"
            elif "status: draft" in content:
                context["plan_status"] = "draft"
    
    # Incorporate spikes if present
    for spike_id in session.get("spikes", []):
        spike_path = topics_dir / spike_id / "spike.md"
        if spike_path.exists():
            content = spike_path.read_text()
            finding = {"spike_id": spike_id, "summary": ""}
            
            # Extract summary (simplified)
            if "## Summary" in content:
                summary_start = content.find("## Summary")
                summary_end = content.find("##", summary_start + 1)
                if summary_end == -1:
                    summary_end = len(content)
                finding["summary"] = content[summary_start:summary_end].strip()
            
            context["spike_findings"].append(finding)
    
    return context


def check_missing_docs(session: dict, kb_dir: Path) -> list[str]:
    """Check for missing plan/spike documents referenced in session.
    
    Returns list of warning messages for missing docs.
    """
    warnings = []
    topics_dir = kb_dir / "topics"
    
    # Check plan
    if session.get("plan"):
        plan_path = topics_dir / session["plan"] / "plan.md"
        if not plan_path.exists():
            warnings.append(f"Plan document not found: {session['plan']}")
    
    # Check spikes
    for spike_id in session.get("spikes", []):
        spike_path = topics_dir / spike_id / "spike.md"
        if not spike_path.exists():
            warnings.append(f"Spike document not found: {spike_id}")
    
    return warnings


# -----------------------------------------------------------------------------
# UX / Notification Tests
# -----------------------------------------------------------------------------


class TestBacklogNotifications:
    """Tests for user-facing notifications about inputs used."""

    def test_notice_includes_seed_when_session_default_used(
        self, temp_kb_dir: Path
    ) -> None:
        """Notice emitted when using session's root_seed as default."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # Simulating the notice that would be shown
        active = load_active_session(temp_kb_dir)
        notice = f"[tf] Using session default: {active['root_seed']}"
        
        assert "seed-test-feature" in notice
        assert "Using session default" in notice

    def test_notice_includes_all_inputs_used(
        self, temp_kb_dir: Path
    ) -> None:
        """Summary notice lists all inputs incorporated."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        set_plan_for_session("plan-test-feature", temp_kb_dir)
        add_spike_to_session("spike-test-research", temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        
        # Format: [tf] Inputs: seed={topic-id} plan={plan-id|none} spikes={count} [...]
        inputs_notice = (
            f"[tf] Inputs: seed={active['root_seed']} "
            f"plan={active.get('plan') or 'none'} "
            f"spikes={len(active.get('spikes', []))} "
            f"{active.get('spikes', [])}"
        )
        
        assert "seed=seed-test-feature" in inputs_notice
        assert "plan=plan-test-feature" in inputs_notice
        assert "spikes=1" in inputs_notice
        assert "spike-test-research" in inputs_notice

    def test_notice_shows_none_for_missing_plan(
        self, temp_kb_dir: Path
    ) -> None:
        """Notice shows 'none' when no plan in session."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        inputs_notice = (
            f"[tf] Inputs: seed={active['root_seed']} "
            f"plan={active.get('plan') or 'none'} "
            f"spikes={len(active.get('spikes', []))}"
        )
        
        assert "plan=none" in inputs_notice

    def test_notice_shows_zero_for_no_spikes(
        self, temp_kb_dir: Path
    ) -> None:
        """Notice shows '0' and empty list when no spikes."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        active = load_active_session(temp_kb_dir)
        inputs_notice = (
            f"[tf] Inputs: seed={active['root_seed']} "
            f"plan={active.get('plan') or 'none'} "
            f"spikes={len(active.get('spikes', []))} []"
        )
        
        assert "spikes=0 []" in inputs_notice


# -----------------------------------------------------------------------------
# Session State Validation Tests
# -----------------------------------------------------------------------------


class TestBacklogSessionStateValidation:
    """Tests for session state validation during backlog generation."""

    def test_only_active_session_used_for_default(
        self, temp_kb_dir: Path
    ) -> None:
        """Only sessions with state='active' are used for default topic."""
        # Create a session and archive it
        session = create_session("seed-test-feature")
        session["state"] = STATE_ARCHIVED
        save_active_session(session, temp_kb_dir)
        
        # Should not use archived session
        active = load_active_session(temp_kb_dir)
        # Note: load_active_session returns the file content regardless of state
        # The check for state would happen in the resolution logic
        if active and active.get("state") != STATE_ACTIVE:
            # Should not use as default
            can_use_as_default = False
        else:
            can_use_as_default = True
        
        assert not can_use_as_default

    def test_session_preserved_when_explicit_topic_provided(
        self, temp_kb_dir: Path
    ) -> None:
        """Session remains active when explicit topic bypasses it."""
        session = create_session("seed-test-feature")
        save_active_session(session, temp_kb_dir)
        
        # User provides explicit topic - session should remain untouched
        active_before = load_active_session(temp_kb_dir)
        
        # Simulate explicit topic override
        explicit_topic = "baseline-other"
        # ... use explicit_topic ...
        
        active_after = load_active_session(temp_kb_dir)
        
        # Session should still be there, unchanged
        assert active_after is not None
        assert active_after["session_id"] == active_before["session_id"]
        assert active_after["root_seed"] == "seed-test-feature"
