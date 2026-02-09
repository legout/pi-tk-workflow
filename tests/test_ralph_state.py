"""Tests for Ralph update_state function (lessons learned persistence to AGENTS.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tf import ralph as ralph_module


class TestUpdateStateLessonsLearned:
    """Tests for update_state() lessons learned persistence to .tf/ralph/AGENTS.md."""

    def test_first_lesson_creates_agentsmd_with_template(self, tmp_path: Path) -> None:
        """Test: first lesson creates .tf/ralph/AGENTS.md with template + appended lesson."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-001"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md with Lessons Learned section
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-001

## Summary
Test implementation complete.

## Lessons Learned

**Context**: Testing lesson extraction
**Lesson**: Always write tests first
**Apply when**: Creating new features
""")
        
        # Create progress.md template
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state directly
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-001",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md was created
        agents_path = ralph_dir / "AGENTS.md"
        assert agents_path.exists(), "AGENTS.md should be created"
        
        content = agents_path.read_text()
        # Verify template structure
        assert "# Ralph Lessons Learned" in content
        assert "## Patterns" in content
        assert "## Gotchas" in content
        # Verify lesson was appended
        assert "## Lesson from TEST-001" in content
        assert "**Context**: Testing lesson extraction" in content
        assert "**Lesson**: Always write tests first" in content

    def test_second_lesson_appends_not_overwrites(self, tmp_path: Path) -> None:
        """Test: second lesson appends (does not overwrite) existing AGENTS.md."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        
        # Pre-populate AGENTS.md with existing lesson
        agents_path = ralph_dir / "AGENTS.md"
        agents_path.write_text("""# Ralph Lessons Learned

## Patterns

## Gotchas

## Lesson from TEST-001 (2026-02-08T10:00:00Z)

**Context**: First lesson context
**Lesson**: First lesson content
**Apply when**: First lesson application
""")
        
        # Create second ticket artifact with Lessons Learned
        artifact_dir = knowledge_dir / "tickets" / "TEST-002"
        artifact_dir.mkdir(parents=True)
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-002

## Summary
Second test implementation.

## Lessons Learned

**Context**: Second lesson context
**Lesson**: Second lesson content
**Apply when**: Second lesson application
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 1
- Tickets failed: 0
- Total iterations: 1

## History

<!-- Auto-appended entries below -->
- TEST-001: COMPLETE (2026-02-08T10:00:00Z)
  - Summary: First test
  - Issues: Critical(0)/Major(0)/Minor(0)
  - Status: COMPLETE
""")
        
        # Store original content for comparison
        original_content = agents_path.read_text()
        
        # Call update_state for second ticket
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-002",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md still exists
        assert agents_path.exists(), "AGENTS.md should still exist"
        
        content = agents_path.read_text()
        # Verify first lesson is preserved
        assert "## Lesson from TEST-001" in content
        assert "**Context**: First lesson context" in content
        # Verify second lesson was appended
        assert "## Lesson from TEST-002" in content
        assert "**Context**: Second lesson context" in content
        assert "**Lesson**: Second lesson content" in content
        # Verify content grew (not replaced)
        assert len(content) > len(original_content)

    def test_no_lessons_section_does_not_create_agentsmd(self, tmp_path: Path) -> None:
        """Test: when no Lessons Learned section exists, AGENTS.md is unchanged/not created."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-003"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md WITHOUT Lessons Learned section
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-003

## Summary
Test implementation without lessons.

## Changes
- Fixed bug
- Added feature
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-003",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md was NOT created
        agents_path = ralph_dir / "AGENTS.md"
        assert not agents_path.exists(), "AGENTS.md should not be created when no lessons exist"

    def test_no_lessons_section_does_not_modify_existing_agentsmd(self, tmp_path: Path) -> None:
        """Test: when no Lessons Learned section exists, existing AGENTS.md is unchanged."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-004"
        artifact_dir.mkdir(parents=True)
        
        # Pre-populate AGENTS.md with existing content
        agents_path = ralph_dir / "AGENTS.md"
        original_content = """# Ralph Lessons Learned

## Patterns

## Gotchas

## Lesson from TEST-OLD (2026-02-08T09:00:00Z)

**Context**: Old lesson context
**Lesson**: Old lesson content
**Apply when**: Old lesson application
"""
        agents_path.write_text(original_content)
        
        # Create close-summary.md WITHOUT Lessons Learned section
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-004

## Summary
Test implementation without lessons.
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-004",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md content is unchanged
        current_content = agents_path.read_text()
        assert current_content == original_content, "AGENTS.md should not be modified when no lessons exist"

    def test_empty_lessons_section_does_not_create_agentsmd(self, tmp_path: Path) -> None:
        """Test: empty Lessons Learned section does not create AGENTS.md."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-005"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md with EMPTY Lessons Learned section
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-005

## Summary
Test implementation.

## Lessons Learned

""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-005",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md was NOT created
        agents_path = ralph_dir / "AGENTS.md"
        assert not agents_path.exists(), "AGENTS.md should not be created for empty lessons section"

    def test_lesson_extracted_from_correct_heading_level(self, tmp_path: Path) -> None:
        """Test: Lessons Learned section is extracted from ## (H2) heading level."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        
        # Test with ## heading
        artifact_dir = knowledge_dir / "tickets" / "TEST-H2"
        artifact_dir.mkdir(parents=True)
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-H2

## Lessons Learned

**Context**: H2 level lesson
**Lesson**: This lesson is under H2
**Apply when**: Testing H2 extraction
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-H2",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify lesson was extracted
        agents_path = ralph_dir / "AGENTS.md"
        assert agents_path.exists(), "AGENTS.md should be created for H2 Lessons Learned"
        content = agents_path.read_text()
        assert "**Context**: H2 level lesson" in content

    def test_lesson_extraction_stops_at_next_section(self, tmp_path: Path) -> None:
        """Test: Lesson extraction stops when next ## or ### section starts."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-SECTION"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md with Lessons Learned followed by another section
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-SECTION

## Lessons Learned

**Context**: Before next section
**Lesson**: This should be captured
**Apply when**: Testing section boundaries

## Next Section

This content should not be captured.
- Item 1
- Item 2
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-SECTION",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify only lesson content was extracted
        agents_path = ralph_dir / "AGENTS.md"
        assert agents_path.exists()
        content = agents_path.read_text()
        assert "**Lesson**: This should be captured" in content
        assert "Next Section" not in content
        assert "This content should not be captured" not in content

    def test_no_close_summary_does_not_create_agentsmd(self, tmp_path: Path) -> None:
        """Test: when close-summary.md doesn't exist, AGENTS.md is not created."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-NO-SUMMARY"
        artifact_dir.mkdir(parents=True)
        
        # Note: NOT creating close-summary.md
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state (should not crash)
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-NO-SUMMARY",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify AGENTS.md was NOT created
        agents_path = ralph_dir / "AGENTS.md"
        assert not agents_path.exists(), "AGENTS.md should not be created when close-summary.md doesn't exist"


class TestUpdateStateProgress:
    """Tests for update_state() progress.md update functionality."""

    def test_progress_updated_with_ticket_entry(self, tmp_path: Path) -> None:
        """Test: progress.md is updated with ticket completion entry."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-PROG"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-PROG

## Summary
Test progress update.
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-PROG",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify progress.md was updated
        content = progress_path.read_text()
        assert "TEST-PROG: COMPLETE" in content
        assert "- Tickets completed: 1" in content
        assert "- Total iterations: 1" in content

    def test_failed_status_updates_failed_count(self, tmp_path: Path) -> None:
        """Test: FAILED status increments failed count, not completed."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-FAIL"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-FAIL

## Summary
Test failure case.
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state with FAILED status
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-FAIL",
            status="FAILED",
            error_msg="Test error message",
            artifact_root=knowledge_dir,
        )
        
        # Verify progress.md shows failure
        content = progress_path.read_text()
        assert "TEST-FAIL: FAILED" in content
        assert "- Tickets failed: 1" in content
        assert "- Tickets completed: 0" in content
        assert "Error: Test error message" in content

    def test_issue_counts_extracted_from_review(self, tmp_path: Path) -> None:
        """Test: issue counts are extracted from review.md if present."""
        # Set up directory structure
        ralph_dir = tmp_path / ".tf" / "ralph"
        ralph_dir.mkdir(parents=True)
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        artifact_dir = knowledge_dir / "tickets" / "TEST-ISSUES"
        artifact_dir.mkdir(parents=True)
        
        # Create close-summary.md
        close_summary = artifact_dir / "close-summary.md"
        close_summary.write_text("""# Close Summary: TEST-ISSUES

## Summary
Test with issues.
""")
        
        # Create review.md with issue counts
        review_path = artifact_dir / "review.md"
        review_path.write_text("""# Review: TEST-ISSUES

## Critical (must fix)
- Issue 1

## Major (should fix)
- Issue 2
- Issue 3

## Minor (nice to fix)
- Issue 4

## Summary Statistics
- Critical: 1
- Major: 2
- Minor: 1
""")
        
        # Create progress.md
        progress_path = ralph_dir / "progress.md"
        progress_path.write_text("""# Ralph Loop Progress

## Current State

- Status: RUNNING
- Current ticket: (none)
- Started: 2026-02-08T10:00:00Z
- Last updated: 2026-02-08T10:00:00Z

## Statistics

- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History

<!-- Auto-appended entries below -->
""")
        
        # Call update_state
        ralph_module.update_state(
            ralph_dir=ralph_dir,
            project_root=tmp_path,
            ticket="TEST-ISSUES",
            status="COMPLETE",
            error_msg="",
            artifact_root=knowledge_dir,
        )
        
        # Verify issue counts in progress
        content = progress_path.read_text()
        assert "Issues: Critical(1)/Major(2)/Minor(1)" in content
