"""Tests for post-fix verification module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tf.post_fix_verification import (
    FixEntry,
    PostFixVerification,
    _canonicalize_severity,
    _count_bullet_with_compound_fixes,
    get_quality_gate_counts,
    parse_fixes_counts,
    parse_review_counts,
    verify_post_fix_state,
    write_post_fix_verification,
)


class TestCanonicalSeverity:
    """Tests for _canonicalize_severity function."""

    def test_lowercase_severities(self) -> None:
        """Normalize lowercase severities."""
        assert _canonicalize_severity("critical") == "Critical"
        assert _canonicalize_severity("major") == "Major"
        assert _canonicalize_severity("minor") == "Minor"
        assert _canonicalize_severity("warnings") == "Warnings"
        assert _canonicalize_severity("suggestions") == "Suggestions"

    def test_uppercase_severities(self) -> None:
        """Handle uppercase severities."""
        assert _canonicalize_severity("CRITICAL") == "Critical"
        assert _canonicalize_severity("MAJOR") == "Major"

    def test_mixed_case_severities(self) -> None:
        """Handle mixed case severities."""
        assert _canonicalize_severity("cRiTiCaL") == "Critical"
        assert _canonicalize_severity("MaJoR") == "Major"

    def test_singular_forms(self) -> None:
        """Handle singular forms."""
        assert _canonicalize_severity("warning") == "Warnings"
        assert _canonicalize_severity("suggestion") == "Suggestions"


class TestCountBulletWithCompoundFixes:
    """Tests for _count_bullet_with_compound_fixes function."""

    def test_single_fixes(self) -> None:
        """Count single bullet items."""
        section = """
- Fixed issue in file.py:10
- Fixed another issue in file.py:20
- Resolved edge case
"""
        assert _count_bullet_with_compound_fixes(section) == 3

    def test_compound_fixes(self) -> None:
        """Count compound fixes like 'Fixed 3 issues'."""
        section = """
- Fixed 3 Critical issues in auth module
- Fixed 2 issues in validation
- Fixed 1 major bug
"""
        assert _count_bullet_with_compound_fixes(section) == 6  # 3 + 2 + 1

    def test_mixed_single_and_compound(self) -> None:
        """Handle mix of single and compound fixes."""
        section = """
- Fixed 2 Critical issues
- Fixed edge case in file.py
- Resolved 3 minor issues
- Fixed typo
"""
        assert _count_bullet_with_compound_fixes(section) == 7  # 2 + 1 + 3 + 1

    def test_no_bullets(self) -> None:
        """Return 0 when no bullets found."""
        section = "No bullet items here"
        assert _count_bullet_with_compound_fixes(section) == 0


class TestParseReviewCounts:
    """Tests for parse_review_counts function."""

    def test_parse_review_with_summary_statistics(self, tmp_path: Path) -> None:
        """Parse counts from standard review.md format."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
# Review: test-123

## Critical (must fix)
- `file.py:10` - Issue 1
- `file.py:20` - Issue 2

## Major (should fix)
- `file.py:30` - Issue 3

## Summary Statistics
- Critical: 2
- Major: 1
- Minor: 3
- Warnings: 0
- Suggestions: 5
""")
        counts = parse_review_counts(review_md)
        assert counts["Critical"] == 2
        assert counts["Major"] == 1
        assert counts["Minor"] == 3
        assert counts["Warnings"] == 0
        assert counts["Suggestions"] == 5

    def test_parse_review_statistics_variant(self, tmp_path: Path) -> None:
        """Parse counts from 'Statistics' section (without 'Summary')."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
# Review: test-123

## Statistics
- Critical: 5
- Major: 2
- Minor: 1
""")
        counts = parse_review_counts(review_md)
        assert counts["Critical"] == 5
        assert counts["Major"] == 2
        assert counts["Minor"] == 1

    def test_parse_review_missing_file(self, tmp_path: Path) -> None:
        """Return zero counts when file doesn't exist."""
        review_md = tmp_path / "nonexistent.md"
        counts = parse_review_counts(review_md)
        assert all(v == 0 for v in counts.values())

    def test_parse_review_no_statistics_section(self, tmp_path: Path) -> None:
        """Return zero counts when no statistics section."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
# Review: test-123

## Critical (must fix)
- `file.py:10` - Issue
""")
        counts = parse_review_counts(review_md)
        assert all(v == 0 for v in counts.values())


class TestParseFixesCounts:
    """Tests for parse_fixes_counts function."""

    def test_parse_fixes_with_summary_statistics(self, tmp_path: Path) -> None:
        """Parse fixed counts from Summary Statistics section."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

## Summary
Brief description of fixes applied

## Fixes by Severity

### Critical (must fix)
- [x] `file.py:10` - Fixed issue 1
- [x] `file.py:20` - Fixed issue 2

### Major (should fix)
- [x] `file.py:30` - Fixed issue 3

## Summary Statistics
- **Critical**: 2
- **Major**: 1
- **Minor**: 0
- **Warnings**: 0
- **Suggestions**: 0
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert counts["Critical"] == 2
        assert counts["Major"] == 1
        assert counts["Minor"] == 0

    def test_parse_fixes_with_sections(self, tmp_path: Path) -> None:
        """Parse fixed counts from fixes.md sections."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

## Critical Fixed
- Fixed issue in `file.py:10`
- Fixed issue in `file.py:20`

## Major Fixed
- Fixed issue in `file.py:30`

## Minor
- Fixed minor issue
- Fixed another minor issue
- Fixed third minor issue
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert counts["Critical"] == 2
        assert counts["Major"] == 1
        assert counts["Minor"] == 3
        assert counts["Warnings"] == 0
        assert counts["Suggestions"] == 0

    def test_parse_fixes_compound_counts(self, tmp_path: Path) -> None:
        """Parse compound fix descriptions."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

## Critical Fixed
- Fixed 3 Critical issues in auth module
- Fixed edge case in validation
- Resolved 2 critical bugs
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert counts["Critical"] == 6  # 3 + 1 + 2

    def test_parse_fixes_no_fixes_needed(self, tmp_path: Path) -> None:
        """Handle 'No fixes needed' marker."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

No fixes needed - all issues were acceptable.
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert all(v == 0 for v in counts.values())
        assert len(warnings) == 0

    def test_parse_fixes_disabled(self, tmp_path: Path) -> None:
        """Handle 'fixer is disabled' marker."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

Fixer is disabled, no fixes applied.
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert all(v == 0 for v in counts.values())

    def test_parse_fixes_missing_file(self, tmp_path: Path) -> None:
        """Return found=False when file doesn't exist."""
        fixes_md = tmp_path / "nonexistent.md"
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is False
        assert all(v == 0 for v in counts.values())

    def test_parse_fixes_malformed_warning(self, tmp_path: Path) -> None:
        """Generate warning when fixes.md exists but no counts parsed."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

Some random content without severity sections or statistics.
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert all(v == 0 for v in counts.values())
        assert len(warnings) == 1
        assert "no recognizable severity sections" in warnings[0]

    def test_parse_fixes_empty_statistics_warning(self, tmp_path: Path) -> None:
        """Generate warning when Summary Statistics has all zeros."""
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
# Fixes: test-123

## Summary Statistics
- Critical: 0
- Major: 0
- Minor: 0
""")
        counts, found, warnings = parse_fixes_counts(fixes_md)
        assert found is True
        assert len(warnings) == 1
        assert "all counts are zero" in warnings[0]


class TestVerifyPostFixState:
    """Tests for verify_post_fix_state function."""

    def test_verify_with_fixes(self, tmp_path: Path) -> None:
        """Calculate post-fix counts correctly."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 5
- Major: 3
- Minor: 2
- Warnings: 1
- Suggestions: 0
""")
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
## Summary Statistics
- Critical: 4
- Major: 2
- Minor: 0
""")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical", "Major"])
        assert result.pre_fix_counts["Critical"] == 5
        assert result.pre_fix_counts["Major"] == 3
        assert result.fixed_counts["Critical"] == 4
        assert result.fixed_counts["Major"] == 2
        assert result.post_fix_counts["Critical"] == 1  # 5 - 4
        assert result.post_fix_counts["Major"] == 1  # 3 - 2
        assert result.post_fix_counts["Minor"] == 2  # unchanged
        assert result.fixes_found is True

    def test_verify_no_fixes_file(self, tmp_path: Path) -> None:
        """Use pre-fix counts when no fixes.md."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 2
- Major: 1
- Minor: 0
- Warnings: 0
- Suggestions: 0
""")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical", "Major"])
        assert result.fixes_found is False
        assert result.post_fix_counts["Critical"] == 2
        assert result.post_fix_counts["Major"] == 1

    def test_verify_gate_passes(self, tmp_path: Path) -> None:
        """Gate passes when no blocking severities remain."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 2
- Major: 1
- Minor: 3
""")
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
## Summary Statistics
- Critical: 2
- Major: 1
""")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical", "Major"])
        assert result.verification_passed is True
        assert result.post_fix_counts["Critical"] == 0
        assert result.post_fix_counts["Major"] == 0

    def test_verify_gate_blocked(self, tmp_path: Path) -> None:
        """Gate blocks when blocking severities remain."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 2
- Major: 1
- Minor: 3
""")
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
## Summary Statistics
- Critical: 1
""")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical", "Major"])
        assert result.verification_passed is False
        assert result.post_fix_counts["Critical"] == 1
        assert result.post_fix_counts["Major"] == 1

    def test_verify_gate_minor_only_blocked(self, tmp_path: Path) -> None:
        """Gate passes when only non-blocking severities remain."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 0
- Major: 0
- Minor: 3
- Warnings: 2
""")
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical", "Major"])
        assert result.verification_passed is True

    def test_verify_overfix_warning(self, tmp_path: Path) -> None:
        """Generate warning when more fixes than issues reported."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 2
""")
        fixes_md = tmp_path / "fixes.md"
        fixes_md.write_text("""
## Summary Statistics
- Critical: 5
""")
        result = verify_post_fix_state(tmp_path, fail_on=["Critical"])
        assert len(result.warnings) == 1
        assert "More Critical fixes" in result.warnings[0]


class TestPostFixVerificationToMarkdown:
    """Tests for PostFixVerification.to_markdown method."""

    def test_to_markdown_with_fixes(self) -> None:
        """Generate correct markdown with fixes."""
        verification = PostFixVerification(
            pre_fix_counts={"Critical": 5, "Major": 3, "Minor": 2, "Warnings": 1, "Suggestions": 0},
            fixed_counts={"Critical": 4, "Major": 2, "Minor": 1, "Warnings": 0, "Suggestions": 0},
            post_fix_counts={"Critical": 1, "Major": 1, "Minor": 1, "Warnings": 1, "Suggestions": 0},
            verification_passed=False,
            fail_on=["Critical", "Major"],
            fixes_found=True,
        )
        markdown = verification.to_markdown("test-123")
        assert "# Post-Fix Verification: test-123" in markdown
        assert "**Status**: FAIL" in markdown
        assert "Pre-Fix Counts" in markdown
        assert "Fixes Applied" in markdown
        assert "Post-Fix Counts" in markdown
        assert "**Critical**: 5" in markdown
        assert "**Critical**: 4" in markdown  # In fixes section
        assert "Based on**: Post-fix counts" in markdown
        assert "BLOCKED by Critical, Major" in markdown

    def test_to_markdown_no_fixes(self) -> None:
        """Generate correct markdown without fixes."""
        verification = PostFixVerification(
            pre_fix_counts={"Critical": 0, "Major": 0, "Minor": 2, "Warnings": 1, "Suggestions": 0},
            fixed_counts={"Critical": 0, "Major": 0, "Minor": 0, "Warnings": 0, "Suggestions": 0},
            post_fix_counts={"Critical": 0, "Major": 0, "Minor": 2, "Warnings": 1, "Suggestions": 0},
            verification_passed=True,
            fail_on=["Critical", "Major"],
            fixes_found=False,
        )
        markdown = verification.to_markdown("test-123")
        assert "**Status**: PASS" in markdown
        assert "Based on**: Pre-fix counts" in markdown
        assert "PASSED - no blocking severities remain" in markdown

    def test_to_markdown_with_warnings(self) -> None:
        """Include warnings section when present."""
        verification = PostFixVerification(
            pre_fix_counts={"Critical": 2, "Major": 0, "Minor": 0, "Warnings": 0, "Suggestions": 0},
            fixed_counts={"Critical": 3, "Major": 0, "Minor": 0, "Warnings": 0, "Suggestions": 0},
            post_fix_counts={"Critical": 0, "Major": 0, "Minor": 0, "Warnings": 0, "Suggestions": 0},
            verification_passed=True,
            fail_on=["Critical"],
            fixes_found=True,
            warnings=["More Critical fixes (3) reported than issues found (2)"],
        )
        markdown = verification.to_markdown("test-123")
        assert "## Warnings" in markdown
        assert "More Critical fixes" in markdown


class TestWritePostFixVerification:
    """Tests for write_post_fix_verification function."""

    def test_writes_file(self, tmp_path: Path) -> None:
        """Write verification file correctly."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 2
- Major: 1
""")
        output_path = write_post_fix_verification(tmp_path, "test-123", ["Critical"])
        assert output_path.exists()
        assert output_path.name == "post-fix-verification.md"
        content = output_path.read_text()
        assert "# Post-Fix Verification: test-123" in content


class TestGetQualityGateCounts:
    """Tests for get_quality_gate_counts function."""

    def test_uses_post_fix_when_available(self, tmp_path: Path) -> None:
        """Prefer post-fix verification counts when available."""
        # Create review.md
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 5
- Major: 3
""")
        # Create post-fix-verification.md
        verification_md = tmp_path / "post-fix-verification.md"
        verification_md.write_text("""
## Post-Fix Counts (calculated)
- **Critical**: 1
- **Major**: 1
- **Minor**: 0
""")
        counts, source = get_quality_gate_counts(tmp_path, ["Critical", "Major"])
        assert source == "post-fix"
        assert counts["Critical"] == 1
        assert counts["Major"] == 1

    def test_falls_back_to_pre_fix(self, tmp_path: Path) -> None:
        """Fall back to review.md when no verification file."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 5
- Major: 3
""")
        counts, source = get_quality_gate_counts(tmp_path, ["Critical", "Major"])
        assert source == "pre-fix"
        assert counts["Critical"] == 5
        assert counts["Major"] == 3

    def test_falls_back_when_verification_empty(self, tmp_path: Path) -> None:
        """Fall back when verification file has no counts."""
        review_md = tmp_path / "review.md"
        review_md.write_text("""
## Summary Statistics
- Critical: 5
- Major: 3
""")
        verification_md = tmp_path / "post-fix-verification.md"
        verification_md.write_text("No counts here")
        counts, source = get_quality_gate_counts(tmp_path, ["Critical", "Major"])
        assert source == "pre-fix"
        assert counts["Critical"] == 5
