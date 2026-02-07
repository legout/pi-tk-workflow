"""Tests for priority_reclassify command."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from tf_cli import priority_reclassify as pr


class TestParseTicketShow:
    """Test parsing tk show output."""

    def test_parse_basic_ticket(self):
        """Test parsing a basic ticket."""
        output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [bug, fix]
---
# Fix the bug

Description of the bug fix."""
        
        ticket = pr.parse_ticket_show(output)
        assert ticket["id"] == "abc-1234"
        assert ticket["priority"] == "P2"
        assert ticket["status"] == "open"
        assert ticket["type"] == "task"
        assert ticket["tags"] == ["bug", "fix"]
        assert ticket["title"] == "Fix the bug"
        assert "Description" in ticket["description"]

    def test_parse_closed_ticket(self):
        """Test parsing a closed ticket."""
        output = """---
id: xyz-9999
priority: P3
status: closed
type: task
tags: [docs]
---
# Update documentation"""
        
        ticket = pr.parse_ticket_show(output)
        assert ticket["status"] == "closed"


class TestClassifyPriority:
    """Test priority classification logic."""

    def test_security_keyword_p0(self):
        """Security keywords should classify as P0."""
        ticket = {
            "title": "Fix security vulnerability",
            "description": "",
            "tags": [],
            "type": "bug",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P0"
        assert "security" in reason.lower() or "critical" in reason.lower()

    def test_crash_keyword_p0(self):
        """Crash keywords should classify as P0."""
        ticket = {
            "title": "App crashes on startup",
            "description": "",
            "tags": [],
            "type": "bug",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P0"

    def test_blocker_keyword_p1(self):
        """Blocker keywords should classify as P1."""
        ticket = {
            "title": "Blocking release issue",
            "description": "",
            "tags": [],
            "type": "bug",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P1"

    def test_feature_keyword_p2(self):
        """Feature keywords should classify as P2."""
        ticket = {
            "title": "Add user profile page",
            "description": "",
            "tags": [],
            "type": "feature",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P2"

    def test_docs_tag_p4(self):
        """Docs tag should classify as P4."""
        ticket = {
            "title": "Update README",
            "description": "",
            "tags": ["docs"],
            "type": "task",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P4"

    def test_refactor_keyword_p4(self):
        """Refactor keywords should classify as P4."""
        ticket = {
            "title": "Refactor utility functions",
            "description": "",
            "tags": [],
            "type": "task",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P4"

    def test_performance_keyword_p3(self):
        """Performance keywords should classify as P3."""
        ticket = {
            "title": "Improve query performance",
            "description": "",
            "tags": [],
            "type": "task",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P3"


class TestFormatPriority:
    """Test priority formatting."""

    def test_format_p0(self):
        assert pr.format_priority("p0") == "P0"
        assert pr.format_priority("P0") == "P0"
        assert pr.format_priority("0") == "P0"

    def test_format_already_formatted(self):
        assert pr.format_priority("P2") == "P2"


class TestGetTicketIds:
    """Test ticket ID collection functions."""

    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_get_ticket_ids_from_ready(self, mock_run):
        """Test getting ready ticket IDs."""
        mock_run.return_value = (0, "abc-1234  Feature description\nxyz-5678  Another feature", "")
        
        ids = pr.get_ticket_ids_from_ready()
        assert "abc-1234" in ids
        assert "xyz-5678" in ids
        mock_run.assert_called_once_with(["ready"])

    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_get_ticket_ids_from_ready_empty(self, mock_run):
        """Test getting ready tickets when none exist."""
        mock_run.return_value = (0, "", "")
        
        ids = pr.get_ticket_ids_from_ready()
        assert ids == []

    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_get_ticket_ids_by_status(self, mock_run):
        """Test getting tickets by status."""
        mock_run.return_value = (0, "abc-1234  open  Feature\nxyz-5678  open  Bug", "")
        
        ids = pr.get_ticket_ids_by_status("open")
        assert "abc-1234" in ids
        mock_run.assert_called_once_with(["ls", "--status", "open"])

    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_get_ticket_ids_by_tag(self, mock_run):
        """Test getting tickets by tag."""
        mock_run.return_value = (0, "abc-1234  open  Feature\nxyz-5678  open  Bug", "")
        
        ids = pr.get_ticket_ids_by_tag("bug")
        assert len(ids) > 0
        mock_run.assert_called_once_with(["ls", "--tag", "bug"])


class TestMainArgumentParsing:
    """Test main argument parsing and validation."""

    @patch("shutil.which")
    def test_no_tk_available(self, mock_which):
        """Test error when tk is not available."""
        mock_which.return_value = None
        
        result = pr.main(["--ids", "abc-1234"])
        assert result == 1

    @patch("shutil.which")
    def test_no_project_found(self, mock_which):
        """Test error when no project found."""
        mock_which.return_value = "/usr/bin/tk"
        
        with patch("tf_cli.priority_reclassify.find_project_root") as mock_find:
            mock_find.return_value = None
            result = pr.main(["--ids", "abc-1234"])
            assert result == 1

    @patch("shutil.which")
    def test_missing_required_args(self, mock_which):
        """Test error when no ticket selection args provided."""
        mock_which.return_value = "/usr/bin/tk"
        
        with patch("tf_cli.priority_reclassify.find_project_root") as mock_find:
            mock_find.return_value = Path("/tmp/project")
            result = pr.main([])
            assert result == 1


class TestClosedTicketHandling:
    """Test closed ticket exclusion/inclusion."""

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_closed_tickets_excluded_by_default(
        self, mock_run, mock_find, mock_which, capsys
    ):
        """Test that closed tickets are excluded by default."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        
        # Return a closed ticket
        closed_ticket = """---
id: closed-123
priority: P3
status: closed
type: task
tags: []
---
# Closed ticket

Description."""
        mock_run.return_value = (0, closed_ticket, "")
        
        result = pr.main(["--ids", "closed-123"])
        
        # Should return 0 with message that no tickets to process
        assert result == 0
        captured = capsys.readouterr()
        assert "No tickets to process" in captured.out

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    @patch("tf_cli.priority_reclassify.print_results")
    @patch("tf_cli.priority_reclassify.write_audit_trail")
    def test_closed_tickets_included_with_flag(
        self, mock_audit, mock_print, mock_run, mock_find, mock_which
    ):
        """Test that closed tickets are included with --include-closed."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        
        # Return a closed ticket
        closed_ticket = """---
id: closed-123
priority: P3
status: closed
type: task
tags: [docs]
---
# Closed ticket

Description."""
        mock_run.return_value = (0, closed_ticket, "")
        
        result = pr.main(["--ids", "closed-123", "--include-closed"])
        
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert len(call_args) == 1  # Closed ticket should be processed
        assert call_args[0]["id"] == "closed-123"


class TestTicketSelection:
    """Test ticket selection methods."""

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_explicit_ids(self, mock_run, mock_find, mock_which):
        """Test selecting tickets by explicit IDs."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        
        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Test ticket"""
        mock_run.return_value = (0, ticket_output, "")
        
        with patch("tf_cli.priority_reclassify.print_results") as mock_print:
            with patch("tf_cli.priority_reclassify.write_audit_trail"):
                pr.main(["--ids", "abc-1234,def-5678"])
                
                # Should call tk show for each ID
                assert mock_run.call_count == 2
                mock_run.assert_any_call(["show", "abc-1234"])
                mock_run.assert_any_call(["show", "def-5678"])

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.get_ticket_ids_from_ready")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_ready_flag(self, mock_run, mock_ready, mock_find, mock_which):
        """Test selecting tickets with --ready."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        mock_ready.return_value = ["ready-1", "ready-2"]
        
        ticket_output = """---
id: ready-1
priority: P2
status: open
type: task
tags: []
---
# Ready ticket"""
        mock_run.return_value = (0, ticket_output, "")
        
        with patch("tf_cli.priority_reclassify.print_results") as mock_print:
            with patch("tf_cli.priority_reclassify.write_audit_trail"):
                pr.main(["--ready"])
                
                mock_ready.assert_called_once()
                assert mock_run.call_count == 2

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.get_ticket_ids_by_status")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_status_filter(self, mock_run, mock_status, mock_find, mock_which):
        """Test selecting tickets by status."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        mock_status.return_value = ["open-1"]
        
        ticket_output = """---
id: open-1
priority: P2
status: open
type: task
tags: []
---
# Open ticket"""
        mock_run.return_value = (0, ticket_output, "")
        
        with patch("tf_cli.priority_reclassify.print_results") as mock_print:
            with patch("tf_cli.priority_reclassify.write_audit_trail"):
                pr.main(["--status", "open"])
                
                mock_status.assert_called_once_with("open")

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.get_ticket_ids_by_tag")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_tag_filter(self, mock_run, mock_tag, mock_find, mock_which):
        """Test selecting tickets by tag."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        mock_tag.return_value = ["bug-1"]
        
        ticket_output = """---
id: bug-1
priority: P1
status: open
type: bug
tags: [bug]
---
# Bug ticket"""
        mock_run.return_value = (0, ticket_output, "")
        
        with patch("tf_cli.priority_reclassify.print_results") as mock_print:
            with patch("tf_cli.priority_reclassify.write_audit_trail"):
                pr.main(["--tag", "bug"])
                
                mock_tag.assert_called_once_with("bug")


class TestAuditTrail:
    """Test audit trail writing."""

    def test_write_audit_trail(self, tmp_path):
        """Test writing audit trail file."""
        results = [
            {
                "id": "abc-1234",
                "current": "P2",
                "proposed": "P1",
                "reason": "Bug fix",
            },
            {
                "id": "xyz-5678",
                "current": "P3",
                "proposed": "P3",
                "reason": "No change",
            },
        ]
        
        pr.write_audit_trail(tmp_path, results, apply=False)
        
        # Check that audit file was created
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        audit_files = list(knowledge_dir.glob("priority-reclassify-*.md"))
        assert len(audit_files) == 1
        
        content = audit_files[0].read_text()
        assert "abc-1234" in content
        assert "xyz-5678" in content
        assert "DRY RUN" in content


class TestJsonOutput:
    """Test JSON output functionality."""

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_json_output_format(self, mock_run, mock_find, mock_which, capsys):
        """Test JSON output contains expected fields."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [bug]
---
# Test bug ticket

This is a security vulnerability."""
        mock_run.return_value = (0, ticket_output, "")

        result = pr.main(["--ids", "abc-1234", "--json"])
        assert result == 0

        captured = capsys.readouterr()
        import json
        output = json.loads(captured.out)

        assert "mode" in output
        assert "tickets" in output
        assert "summary" in output
        assert output["mode"] == "dry-run"
        assert len(output["tickets"]) == 1

        ticket = output["tickets"][0]
        assert "id" in ticket
        assert "title" in ticket
        assert "current" in ticket
        assert "proposed" in ticket
        assert "bucket" in ticket
        assert "reason" in ticket
        assert "confidence" in ticket
        assert "would_change" in ticket

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_json_output_with_apply(self, mock_run, mock_find, mock_which, capsys):
        """Test JSON output shows correct mode with --apply."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Test ticket"""
        mock_run.return_value = (0, ticket_output, "")

        result = pr.main(["--ids", "abc-1234", "--json", "--apply", "--yes"])
        assert result == 0

        captured = capsys.readouterr()
        import json
        output = json.loads(captured.out)

        assert output["mode"] == "apply"


class TestReportFlag:
    """Test --report flag for optional report generation."""

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_no_report_by_default(self, mock_run, mock_find, mock_which, capsys, tmp_path):
        """Test that report is not written without --report flag."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = tmp_path

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Test ticket"""
        mock_run.return_value = (0, ticket_output, "")

        # Create .tf directory structure
        (tmp_path / ".tf" / "knowledge").mkdir(parents=True, exist_ok=True)

        result = pr.main(["--ids", "abc-1234"])
        assert result == 0

        # No report files should be created
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        report_files = list(knowledge_dir.glob("priority-reclassify-*.md"))
        assert len(report_files) == 0

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_report_written_with_flag(self, mock_run, mock_find, mock_which, capsys, tmp_path):
        """Test that report is written when --report flag is used."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = tmp_path

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [bug]
---
# Test bug ticket"""
        mock_run.return_value = (0, ticket_output, "")

        # Create .tf directory structure
        (tmp_path / ".tf" / "knowledge").mkdir(parents=True, exist_ok=True)

        result = pr.main(["--ids", "abc-1234", "--report"])
        assert result == 0

        # Report file should be created
        knowledge_dir = tmp_path / ".tf" / "knowledge"
        report_files = list(knowledge_dir.glob("priority-reclassify-*.md"))
        assert len(report_files) == 1

        # Verify report content
        content = report_files[0].read_text()
        assert "Priority Reclassification Audit" in content
        assert "abc-1234" in content


class TestSafetyUX:
    """Test safety UX features: --yes, --max-changes, --force."""

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_apply_requires_yes_in_non_interactive_mode(self, mock_run, mock_find, mock_which, capsys):
        """Test that --apply requires --yes when not in a TTY."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [security]
---
# Security issue

This is a security vulnerability."""
        mock_run.return_value = (0, ticket_output, "")

        # Without --yes, should fail in non-interactive mode
        result = pr.main(["--ids", "abc-1234", "--apply"])
        assert result == 1

        captured = capsys.readouterr()
        assert "requires --yes flag" in captured.err

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_apply_with_yes_succeeds(self, mock_run, mock_find, mock_which, capsys):
        """Test that --apply with --yes works in non-interactive mode."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Test ticket"""
        mock_run.return_value = (0, ticket_output, "")

        # With --yes, should succeed
        result = pr.main(["--ids", "abc-1234", "--apply", "--yes"])
        assert result == 0

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_max_changes_limits_updates(self, mock_run, mock_find, mock_which, capsys, tmp_path):
        """Test that --max-changes caps the number of updates."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = tmp_path

        # Create ticket files for realistic update scenario
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir(parents=True)
        
        for i, tag in enumerate(["security", "security", "security"]):  # All P0
            ticket_file = tickets_dir / f"abc-{i:04d}.md"
            ticket_file.write_text(f"""---
id: abc-{i:04d}
priority: P2
status: open
type: task
tags: [{tag}]
---
# Ticket {i}
""")

        def mock_ticket_show(args):
            ticket_id = args[1]
            content = f"""---
id: {ticket_id}
priority: P2
status: open
type: task
tags: [security]
---
# Security issue"""
            return (0, content, "")

        mock_run.side_effect = mock_ticket_show

        result = pr.main(["--ids", "abc-0000,abc-0001,abc-0002", "--apply", "--yes", "--max-changes", "2"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Limiting to 2 changes" in captured.out or "Applied priority changes to 2" in captured.out

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_force_applies_unknown_priorities(self, mock_run, mock_find, mock_which, capsys):
        """Test that --force applies even unknown priority classifications."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        # Ticket with no clear classification
        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Ambiguous ticket

Description with no keywords."""
        mock_run.return_value = (0, ticket_output, "")

        result = pr.main(["--ids", "abc-1234", "--apply", "--yes", "--force"])
        assert result == 0

        captured = capsys.readouterr()
        # Should apply the unknown priority when --force is used
        assert "Applied" in captured.out or "unknown" in captured.out

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    def test_unknown_skipped_without_force(self, mock_run, mock_find, mock_which, capsys):
        """Test that unknown priorities are skipped without --force."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")

        # Ticket with no clear classification
        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: []
---
# Ambiguous ticket

Description with no keywords."""
        mock_run.return_value = (0, ticket_output, "")

        result = pr.main(["--ids", "abc-1234", "--apply", "--yes"])
        assert result == 0

        captured = capsys.readouterr()
        # Should indicate skipped unknown
        assert "skipped" in captured.out.lower() or "unknown" in captured.out.lower()

    @patch("shutil.which")
    @patch("tf_cli.priority_reclassify.find_project_root")
    @patch("tf_cli.priority_reclassify.run_tk_command")
    @patch("tf_cli.priority_reclassify.is_interactive")
    @patch("tf_cli.priority_reclassify.confirm_changes")
    def test_interactive_confirmation(self, mock_confirm, mock_is_tty, mock_run, mock_find, mock_which):
        """Test that interactive mode prompts for confirmation."""
        mock_which.return_value = "/usr/bin/tk"
        mock_find.return_value = Path("/tmp/project")
        mock_is_tty.return_value = True
        mock_confirm.return_value = False  # User cancels

        ticket_output = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [security]
---
# Security issue"""
        mock_run.return_value = (0, ticket_output, "")

        result = pr.main(["--ids", "abc-1234", "--apply"])
        assert result == 0  # Returns 0 on cancellation (not an error)
        mock_confirm.assert_called_once()


class TestRubricMappingComprehensive:
    """Comprehensive tests for rubric mapping and keyword rules."""

    def test_p0_security_keywords_all(self):
        """Test all P0 security keywords trigger P0 classification."""
        security_keywords = [
            "security vulnerability",
            "CVE-2024-1234",
            "exploit in authentication",
            "data breach detected",
            "XSS vulnerability found",
            "SQL injection possible",
            "auth bypass vulnerability",
            "unauthorized access",
        ]
        for kw in security_keywords:
            ticket = {"title": f"Fix {kw}", "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P0", f"Expected P0 for '{kw}', got {priority}"

    def test_p0_data_keywords(self):
        """Test P0 data loss/corruption keywords."""
        data_keywords = [
            "data loss in production",
            "database corruption detected",
            "need rollback immediately",
            "data recovery required",
            "data integrity violation",
        ]
        for kw in data_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P0", f"Expected P0 for '{kw}', got {priority}"

    def test_p0_system_keywords(self):
        """Test P0 system outage/crash keywords."""
        system_keywords = [
            "system outage",
            "service is down",
            "app crashes on launch",
            "server crashing repeatedly",
            "OOM killer activated",
            "deadlock in production",
            "panic in main thread",
            "segfault in library",
            "infinite loop detected",
        ]
        for kw in system_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P0", f"Expected P0 for '{kw}', got {priority}"

    def test_p0_compliance_keywords(self):
        """Test P0 compliance/regulatory keywords."""
        compliance_keywords = [
            "GDPR violation",
            "legal requirement not met",
            "compliance violation found",
            "regulatory audit failure",
        ]
        for kw in compliance_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P0", f"Expected P0 for '{kw}', got {priority}"

    def test_p1_user_impact_keywords(self):
        """Test P1 user-facing impact keywords."""
        impact_keywords = [
            "user-facing bug in checkout",
            "customer reported issue",
            "regression in payment flow",
            "broken login button",
            "feature not working",
        ]
        for kw in impact_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P1", f"Expected P1 for '{kw}', got {priority}"

    def test_p1_release_blocker_keywords(self):
        """Test P1 release blocker keywords."""
        blocker_keywords = [
            "release blocker for v2.0",
            "milestone requirement",
            "launch blocking issue",
            "blocking release deployment",
        ]
        for kw in blocker_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P1", f"Expected P1 for '{kw}', got {priority}"

    def test_p1_performance_keywords(self):
        """Test P1 performance degradation keywords."""
        perf_keywords = [
            "slow response times",
            "request timeout errors",
            "memory leak detected",
            "high CPU usage",
            "performance degradation observed",
        ]
        for kw in perf_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P1", f"Expected P1 for '{kw}', got {priority}"

    def test_p1_correctness_keywords(self):
        """Test P1 correctness/data accuracy keywords."""
        correctness_keywords = [
            "wrong results in calculations",
            "calculation error in totals",
            "data inconsistency detected",
        ]
        for kw in correctness_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "bug"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P1", f"Expected P1 for '{kw}', got {priority}"

    def test_p2_standard_work_keywords(self):
        """Test P2 standard feature work keywords."""
        feature_keywords = [
            "implement new dashboard",
            "add support for webhooks",
            "enhancement to user profile",
            "new capability for exports",
        ]
        for kw in feature_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "feature"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P2", f"Expected P2 for '{kw}', got {priority}"

    def test_p2_integration_keywords(self):
        """Test P2 integration/API keywords."""
        integration_keywords = [
            "API endpoint needed",
            "webhook integration",
            "export to CSV",
            "import from external system",
            "third-party integration",
        ]
        for kw in integration_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "feature"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P2", f"Expected P2 for '{kw}', got {priority}"

    def test_p3_quality_keywords(self):
        """Test P3 code quality/architecture keywords."""
        quality_keywords = [
            ("address tech debt", "P3"),
            ("improve architecture design", "P3"),
            ("redesign module structure", "P3"),
        ]
        for kw, expected in quality_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == expected, f"Expected {expected} for '{kw}', got {priority}"

    def test_p3_dx_keywords(self):
        """Test P3 developer experience keywords."""
        dx_keywords = [
            "improve DX for new devs",
            "optimize dev workflow",
            "reduce build time",
            "improve CI/CD pipeline",
            "better developer experience",
        ]
        for kw in dx_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P3", f"Expected P3 for '{kw}', got {priority}"

    def test_p3_observability_keywords(self):
        """Test P3 observability keywords."""
        obs_keywords = [
            "add metrics collection",
            "improve logging",
            "distributed tracing",
            "monitoring dashboard",
            "alerting rules",
        ]
        for kw in obs_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P3", f"Expected P3 for '{kw}', got {priority}"

    def test_p3_testing_keywords(self):
        """Test P3 testing infrastructure keywords."""
        # Note: "integration" and "API" are P2 keywords, so mixed phrases
        # will match P2 first before P3's "testing" keyword
        testing_keywords = [
            ("improve test coverage", "P3"),
            ("add integration tests", "P2"),  # "integration" matches P2 first
            ("load tests for API", "P2"),  # "API" matches P2 first
            ("test infrastructure improvements", "P3"),
        ]
        for kw, expected in testing_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == expected, f"Expected {expected} for '{kw}', got {priority}"

    def test_p4_polish_keywords(self):
        """Test P4 polish/cosmetic keywords."""
        polish_keywords = [
            "fix typo in README",
            "formatting cleanup",
            "lint fixes",
            "naming convention updates",
            "cosmetic changes only",
            "whitespace cleanup",
        ]
        for kw in polish_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P4", f"Expected P4 for '{kw}', got {priority}"

    def test_p4_docs_keywords(self):
        """Test P4 documentation keywords."""
        docs_keywords = [
            "update docs",
            "improve README",
            "add code comments",
            "docstrings for modules",
            "documentation improvements",
        ]
        for kw in docs_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P4", f"Expected P4 for '{kw}', got {priority}"

    def test_p4_types_keywords(self):
        """Test P4 type hints/typing keywords."""
        type_keywords = [
            "add type hints",
            "fix mypy errors",
            "improve type safety",
            "typing annotations",
        ]
        for kw in type_keywords:
            ticket = {"title": kw, "description": "", "tags": [], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == "P4", f"Expected P4 for '{kw}', got {priority}"

    def test_tag_map_comprehensive(self):
        """Test all TAG_MAP entries work correctly."""
        tag_tests = [
            ("security", "P0"),
            ("cve", "P0"),
            ("critical", "P0"),
            ("data-loss", "P0"),
            ("outage", "P0"),
            ("bug", "P1"),
            ("regression", "P1"),
            ("performance", "P1"),
            ("blocker", "P1"),
            ("feature", "P2"),
            ("enhancement", "P2"),
            ("refactor", "P3"),
            ("tech-debt", "P3"),
            ("dx", "P3"),
            ("ci/cd", "P3"),
            ("testing", "P3"),
            ("docs", "P4"),
            ("documentation", "P4"),
            ("typo", "P4"),
            ("style", "P4"),
            ("typing", "P4"),
        ]
        for tag, expected_priority in tag_tests:
            ticket = {"title": "Test", "description": "", "tags": [tag], "type": "task"}
            priority, reason = pr.classify_priority(ticket)
            assert priority == expected_priority, f"Expected {expected_priority} for tag '{tag}', got {priority}"

    def test_type_defaults(self):
        """Test TYPE_DEFAULTS mapping."""
        type_tests = [
            ("bug", "P1"),
            ("feature", "P2"),
            ("enhancement", "P2"),
            ("task", "P3"),
            ("chore", "P3"),
            ("docs", "P4"),
        ]
        for ticket_type, expected_priority in type_tests:
            ticket = {"title": "Test", "description": "", "tags": [], "type": ticket_type}
            priority, reason = pr.classify_priority(ticket)
            assert priority == expected_priority, f"Expected {expected_priority} for type '{ticket_type}', got {priority}"

    def test_priority_override_tags_take_precedence(self):
        """Test that tags take precedence over description keywords."""
        # Description says "security" but tag says "docs" -> should be P4
        ticket = {
            "title": "Security review",
            "description": "critical security vulnerability",
            "tags": ["docs"],
            "type": "task",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "P4", f"Tags should take precedence: expected P4, got {priority}"
        assert "Tag match" in reason

    def test_unknown_when_ambiguous(self):
        """Test that ambiguous tickets return unknown."""
        ticket = {
            "title": "Some work item",
            "description": "Description with no clear indicators",
            "tags": [],
            "type": "",
        }
        priority, reason = pr.classify_priority(ticket)
        assert priority == "unknown"
        assert "No clear rubric match" in reason


class TestFrontmatterPreservation:
    """Tests that frontmatter patching preserves unrelated fields."""

    def test_parse_frontmatter_basic(self):
        """Test parsing frontmatter from ticket content."""
        content = """---
id: abc-1234
priority: P2
status: open
type: task
tags: [bug, fix]
custom_field: custom_value
---
# Title

Description here."""
        
        frontmatter, frontmatter_text, body = pr.parse_frontmatter(content)
        
        assert frontmatter["id"] == "abc-1234"
        assert frontmatter["priority"] == "P2"
        assert frontmatter["status"] == "open"
        assert frontmatter["custom_field"] == "custom_value"
        assert "id:" in frontmatter_text
        assert "priority:" in frontmatter_text
        assert "# Title" in body
        assert "Description here" in body

    def test_parse_frontmatter_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = """# Just a title

No frontmatter here."""
        
        frontmatter, frontmatter_text, body = pr.parse_frontmatter(content)
        
        assert frontmatter == {}
        assert frontmatter_text == ""
        assert "# Just a title" in body

    def test_update_frontmatter_priority_preserves_other_fields(self):
        """Test that updating priority preserves other frontmatter fields."""
        frontmatter_text = """id: abc-1234
priority: P2
status: open
type: task
tags: [bug, fix]
custom_field: custom_value
another_field: another_value"""
        
        updated = pr.update_frontmatter_priority(frontmatter_text, "P1")
        
        assert "priority: P1" in updated
        assert "id: abc-1234" in updated
        assert "status: open" in updated
        assert "type: task" in updated
        assert "tags: [bug, fix]" in updated
        assert "custom_field: custom_value" in updated
        assert "another_field: another_value" in updated

    def test_update_frontmatter_priority_preserves_indentation(self):
        """Test that updating priority preserves indentation."""
        frontmatter_text = """  id: abc-1234
  priority: P2
  status: open"""
        
        updated = pr.update_frontmatter_priority(frontmatter_text, "P0")
        
        assert "  priority: P0" in updated
        assert "  id: abc-1234" in updated
        assert "  status: open" in updated

    def test_update_frontmatter_adds_priority_if_missing(self):
        """Test that priority is added if not present in frontmatter."""
        frontmatter_text = """id: abc-1234
status: open
type: task"""
        
        updated = pr.update_frontmatter_priority(frontmatter_text, "P2")
        
        assert "priority: P2" in updated
        assert "id: abc-1234" in updated
        assert "status: open" in updated

    def test_add_note_to_ticket_body_new_section(self):
        """Test adding audit note when no Notes section exists."""
        body = """# Title

Description of the ticket."""
        
        note = "Priority changed from P2 to P1"
        updated = pr.add_note_to_ticket_body(body, note)
        
        assert "## Notes" in updated
        assert note in updated
        assert "Description of the ticket" in updated

    def test_add_note_to_ticket_body_existing_section(self):
        """Test adding audit note to existing Notes section."""
        body = """# Title

Description.

## Notes

Previous note here."""
        
        note = "Priority changed from P2 to P1"
        updated = pr.add_note_to_ticket_body(body, note)
        
        assert updated.count("## Notes") == 1  # Only one Notes section
        assert note in updated
        assert "Previous note here" in updated

    def test_update_ticket_priority_preserves_all_fields(self, tmp_path):
        """Integration test: update_ticket_priority preserves all frontmatter fields."""
        # Create temp tickets directory
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        # Create a ticket file with multiple custom fields
        ticket_content = """---
id: test-1234
priority: P3
status: open
type: task
tags: [bug, urgent]
custom_field: preserved_value
assignee: developer
due_date: 2024-12-31
---
# Test Ticket

This is a test ticket.

## Notes

Initial note."""
        
        ticket_file = tickets_dir / "test-1234.md"
        ticket_file.write_text(ticket_content)
        
        # Update the priority
        success, error = pr.update_ticket_priority(
            ticket_id="test-1234",
            old_priority="P3",
            new_priority="P1",
            reason="Security issue",
            project_root=tmp_path,
        )
        
        assert success, f"Update failed: {error}"
        
        # Read updated content
        updated_content = ticket_file.read_text()
        
        # Verify priority was updated
        assert "priority: P1" in updated_content
        
        # Verify all other fields are preserved
        assert "id: test-1234" in updated_content
        assert "status: open" in updated_content
        assert "type: task" in updated_content
        assert "tags: [bug, urgent]" in updated_content
        assert "custom_field: preserved_value" in updated_content
        assert "assignee: developer" in updated_content
        assert "due_date: 2024-12-31" in updated_content
        
        # Verify audit note was added
        assert "Priority reclassified: P3 → P1" in updated_content
        assert "Reason: Security issue" in updated_content
        assert "Initial note" in updated_content  # Original note preserved

    def test_update_ticket_priority_no_notes_section(self, tmp_path):
        """Test updating ticket without existing Notes section."""
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        ticket_content = """---
id: test-5678
priority: P4
status: open
type: task
tags: [docs]
---
# Documentation Update

Update the README."""
        
        ticket_file = tickets_dir / "test-5678.md"
        ticket_file.write_text(ticket_content)
        
        success, error = pr.update_ticket_priority(
            ticket_id="test-5678",
            old_priority="P4",
            new_priority="P3",
            reason="More complex than expected",
            project_root=tmp_path,
        )
        
        assert success, f"Update failed: {error}"
        
        updated_content = ticket_file.read_text()
        assert "priority: P3" in updated_content
        assert "## Notes" in updated_content
        assert "Priority reclassified: P4 → P3" in updated_content

    def test_update_ticket_priority_file_not_found(self, tmp_path):
        """Test handling when ticket file doesn't exist."""
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        success, error = pr.update_ticket_priority(
            ticket_id="nonexistent",
            old_priority="P2",
            new_priority="P1",
            reason="Test",
            project_root=tmp_path,
        )
        
        assert not success
        assert "not found" in error.lower()


class TestTempTicketsIntegration:
    """Integration tests with temporary .tickets/ directory."""

    def test_full_workflow_with_temp_tickets(self, tmp_path):
        """End-to-end test with temp tickets directory and real files."""
        # Set up temp project structure
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        # Create multiple ticket files
        tickets = [
            {
                "id": "sec-001",
                "priority": "P2",
                "tags": ["security"],
                "title": "Security vulnerability",
                "expected_new": "P0",
            },
            {
                "id": "bug-002",
                "priority": "P3",
                "tags": ["bug"],  # bug tag -> P1
                "title": "User reported bug",
                "expected_new": "P1",
            },
            {
                "id": "feat-003",
                "priority": "P3",
                "tags": ["feature"],
                "title": "New dashboard feature",
                "expected_new": "P2",
            },
            {
                "id": "doc-004",
                "priority": "P2",
                "tags": ["docs"],
                "title": "Update README",
                "expected_new": "P4",
            },
        ]
        
        for t in tickets:
            # Format tags as YAML list [tag1, tag2]
            tags_str = "[" + ", ".join(t['tags']) + "]" if t['tags'] else "[]"
            content = f"""---
id: {t['id']}
priority: {t['priority']}
status: open
type: task
tags: {tags_str}
---
# {t['title']}

Description here."""
            (tickets_dir / f"{t['id']}.md").write_text(content)
        
        # Test classification by reading files directly
        for t in tickets:
            content = (tickets_dir / f"{t['id']}.md").read_text()
            ticket = pr.parse_ticket_show(content)
            priority, reason = pr.classify_priority(ticket)
            assert priority == t['expected_new'], f"Expected {t['expected_new']} for {t['id']}, got {priority}"
    
    def test_apply_mode_with_temp_directory(self, tmp_path):
        """Test apply mode updates files correctly in temp directory."""
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        # Create a ticket file
        ticket_content = """---
id: apply-test
priority: P2
status: open
type: task
tags: [security]
created: 2024-01-01T00:00:00Z
---
# Security Issue

Critical security vulnerability needs fixing."""
        
        ticket_file = tickets_dir / "apply-test.md"
        ticket_file.write_text(ticket_content)
        
        # Parse and classify
        ticket = pr.parse_ticket_show(ticket_content)
        priority, reason = pr.classify_priority(ticket)
        
        assert priority == "P0", f"Security tag should yield P0, got {priority}"
        
        # Apply the update
        success, error = pr.update_ticket_priority(
            ticket_id="apply-test",
            old_priority="P2",
            new_priority="P0",
            reason="Security classification",
            project_root=tmp_path,
        )
        
        assert success
        
        # Verify file was updated
        updated_content = ticket_file.read_text()
        assert "priority: P0" in updated_content
        assert "created: 2024-01-01T00:00:00Z" in updated_content  # Preserved
        assert "Priority reclassified: P2 → P0" in updated_content
    
    def test_classifier_determinism(self, tmp_path):
        """Test that classifier produces deterministic results."""
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        # Create identical tickets
        ticket_content = """---
id: det-test
priority: P2
status: open
type: task
tags: [security]
---
# Security Bug

Vulnerability in auth system."""
        
        # Classify same ticket multiple times
        results = []
        for _ in range(5):
            ticket = pr.parse_ticket_show(ticket_content)
            priority, reason = pr.classify_priority(ticket)
            results.append((priority, reason))
        
        # All results should be identical
        first = results[0]
        for r in results[1:]:
            assert r == first, f"Classifier not deterministic: {r} != {first}"
    
    def test_multiple_tag_precedence(self, tmp_path):
        """Test that highest priority tag wins when multiple tags present."""
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        
        # Ticket with both security (P0) and docs (P4) tags
        ticket_content = """---
id: multi-tag
priority: P3
status: open
type: task
tags: [docs, security]
---
# Security Documentation

Document the security fix."""
        
        ticket_file = tickets_dir / "multi-tag.md"
        ticket_file.write_text(ticket_content)
        
        ticket = pr.parse_ticket_show(ticket_content)
        priority, reason = pr.classify_priority(ticket)
        
        # Security tag (P0) should take precedence over docs (P4)
        assert priority == "P0", f"Security tag should win, expected P0 got {priority}"


class TestIntegration:
    """Integration tests requiring actual tk."""

    @pytest.mark.skipif(
        subprocess.run(["which", "tk"], capture_output=True).returncode != 0,
        reason="tk not available"
    )
    def test_help_output(self):
        """Test that help includes all selection options."""
        result = subprocess.run(
            ["python", "-m", "tf_cli.priority_reclassify", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--ids" in result.stdout
        assert "--ready" in result.stdout
        assert "--status" in result.stdout
        assert "--tag" in result.stdout
        assert "--include-closed" in result.stdout
        assert "--apply" in result.stdout
        assert "--yes" in result.stdout
        assert "--max-changes" in result.stdout
        assert "--force" in result.stdout
        assert "--json" in result.stdout
        assert "--report" in result.stdout