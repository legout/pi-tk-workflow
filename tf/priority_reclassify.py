from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from .utils import find_project_root


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def confirm_changes(results: List[dict], max_changes: Optional[int] = None) -> bool:
    """Prompt user to confirm changes.
    
    Returns True if user confirms, False otherwise.
    """
    changes = [r for r in results if r["current"] != r["proposed"] and r["proposed"] != "unknown"]
    unknowns = [r for r in results if r["proposed"] == "unknown"]
    
    print(f"\n{'='*60}")
    print("CONFIRM PRIORITY CHANGES")
    print(f"{'='*60}")
    print(f"\nTickets to update: {len(changes)}")
    if unknowns:
        print(f"Tickets with unknown priority (will be skipped): {len(unknowns)}")
    if max_changes and len(changes) > max_changes:
        print(f"(Capped by --max-changes: only first {max_changes} will be applied)")
    
    print(f"\n{'Ticket':<12} {'Current':<10} {'New':<10} {'Reason'}")
    print("-" * 60)
    
    for r in changes[:max_changes] if max_changes else changes:
        print(f"{r['id']:<12} {r['current']:<10} {r['proposed']:<10} {r['reason'][:30]}")
    
    print(f"\n{'='*60}")
    
    try:
        response = input("\nApply these changes? [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return False


@dataclass
class ClassificationResult:
    """Result of priority classification."""
    priority: str  # P0-P4 or "unknown"
    bucket: str  # rubric bucket name
    reason: str  # human-readable explanation
    confidence: str  # high/medium/low/unknown


# Rubric definitions with keywords and bucket names
RUBRIC = {
    "P0": {
        "bucket": "critical-risk",
        "description": "System down, data loss, security breach, blocking all work",
        "keywords": {
            "security": ["security", "vulnerability", "cve", "exploit", "breach", "xss", "injection", "auth bypass", "unauthorized"],
            "data": ["data loss", "corruption", "rollback", "recovery", "data integrity"],
            "system": ["outage", "down", "crash", "crashes", "crashing", "crash loop", "oom", "deadlock", "panic", "segfault", "infinite loop"],
            "compliance": ["gdpr", "legal", "compliance violation", "regulatory"],
        },
    },
    "P1": {
        "bucket": "high-impact",
        "description": "Major feature, significant bug affecting users, performance degradation",
        "keywords": {
            "user_impact": ["user-facing", "customer reported", "regression", "broken", "not working"],
            "features": ["release blocker", "milestone", "launch", "blocking release"],
            "performance": ["slow", "timeout", "memory leak", "high cpu", "performance degradation"],
            "correctness": ["wrong results", "calculation error", "data inconsistency"],
        },
    },
    "P2": {
        "bucket": "product-feature",
        "description": "Standard product features, routine enhancements",
        "keywords": {
            "standard_work": ["feature", "implement", "add support", "enhancement", "new capability"],
            "integration": ["api", "webhook", "export", "import", "integration"],
        },
    },
    "P3": {
        "bucket": "engineering-quality",
        "description": "Engineering quality, dev workflow improvements, tech debt",
        "keywords": {
            "quality": ["refactor", "cleanup", "tech debt", "architecture", "redesign"],
            "dx": ["dx", "dev workflow", "build time", "ci/cd", "developer experience"],
            "observability": ["metrics", "logging", "tracing", "monitoring", "alerting"],
            "testing": ["test coverage", "integration tests", "load tests", "test infra"],
        },
    },
    "P4": {
        "bucket": "maintenance-polish",
        "description": "Code cosmetics, refactors, docs polish, test typing",
        "keywords": {
            "polish": ["typo", "formatting", "lint", "style", "naming", "cosmetic", "whitespace"],
            "docs": ["docs", "readme", "comments", "docstrings", "documentation"],
            "types": ["type hints", "mypy", "type safety", "typing"],
            "minor": ["imports cleanup", "unused code", "minor refactor", "refactor"],
        },
    },
}

# Tag-based classifications (tags take precedence over description)
TAG_MAP = {
    "P0": ["security", "cve", "critical", "data-loss", "outage"],
    "P1": ["bug", "regression", "performance", "blocker"],
    "P2": ["feature", "enhancement"],
    "P3": ["refactor", "tech-debt", "dx", "ci/cd", "testing"],
    "P4": ["docs", "documentation", "typo", "style", "typing"],
}

# Type-based defaults when no clear indicators found
TYPE_DEFAULTS = {
    "bug": "P1",
    "feature": "P2",
    "enhancement": "P2",
    "task": "P3",
    "chore": "P3",
    "docs": "P4",
}


def run_tk_command(args: List[str]) -> Tuple[int, str, str]:
    """Run a tk command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["tk"] + args,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def get_ticket_ids_from_ready() -> List[str]:
    """Get list of ready ticket IDs."""
    returncode, stdout, _ = run_tk_command(["ready"])
    if returncode != 0:
        return []
    
    ids = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line:
            parts = line.split()
            if parts:
                ids.append(parts[0])
    return ids


def get_ticket_ids_by_status(status: str) -> List[str]:
    """Get ticket IDs filtered by status."""
    returncode, stdout, _ = run_tk_command(["ls", "--status", status])
    if returncode != 0:
        return []
    
    ids = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("-"):
            parts = line.split()
            if parts and not parts[0].startswith("-"):
                ids.append(parts[0])
    return ids


def get_ticket_ids_by_tag(tag: str) -> List[str]:
    """Get ticket IDs filtered by tag."""
    returncode, stdout, _ = run_tk_command(["ls", "--tag", tag])
    if returncode != 0:
        return []
    
    ids = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("-"):
            parts = line.split()
            if parts and not parts[0].startswith("-"):
                ids.append(parts[0])
    return ids


def parse_ticket_show(output: str) -> dict:
    """Parse tk show output into a dictionary."""
    ticket = {
        "id": "",
        "title": "",
        "priority": "",
        "status": "",
        "tags": [],
        "description": "",
        "type": "",
    }
    
    lines = output.strip().split("\n")
    in_header = True
    description_lines = []
    
    for line in lines:
        line = line.rstrip()
        
        if in_header:
            if line.startswith("id:"):
                ticket["id"] = line.split(":", 1)[1].strip()
            elif line.startswith("priority:"):
                ticket["priority"] = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                ticket["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                ticket["type"] = line.split(":", 1)[1].strip()
            elif line.startswith("tags:"):
                tags_str = line.split(":", 1)[1].strip()
                tags_match = re.findall(r'\[([^\]]*)\]', tags_str)
                if tags_match:
                    ticket["tags"] = [t.strip() for t in tags_match[0].split(",") if t.strip()]
            elif line.startswith("# ") and ticket["id"]:
                ticket["title"] = line[2:].strip()
                in_header = False
            elif line == "---":
                continue
        else:
            description_lines.append(line)
    
    ticket["description"] = "\n".join(description_lines).strip()
    return ticket


def find_matching_keywords(text: str, keyword_dict: dict) -> List[Tuple[str, str]]:
    """Find which keywords match in text. Returns list of (category, keyword)."""
    text_lower = text.lower()
    matches = []
    for category, keywords in keyword_dict.items():
        for kw in keywords:
            if kw in text_lower:
                matches.append((category, kw))
    return matches


def classify_priority(ticket: dict) -> Tuple[str, str]:
    """
    Classify ticket priority using comprehensive rubric.
    
    Returns (priority, reason) tuple where priority is P0-P4 or "unknown".
    Ambiguous tickets return "unknown" priority.
    
    Backward compatible: returns tuple for existing test expectations.
    Use classify_priority_full() for complete ClassificationResult.
    """
    result = classify_priority_full(ticket)
    return result.priority, result.reason


def classify_priority_full(ticket: dict) -> ClassificationResult:
    """
    Classify ticket priority using comprehensive rubric.
    
    Returns ClassificationResult with priority, bucket, reason, and confidence.
    Ambiguous tickets return "unknown" priority.
    """
    title = ticket.get("title", "").lower()
    description = ticket.get("description", "").lower()
    tags = [t.lower() for t in ticket.get("tags", [])]
    ticket_type = ticket.get("type", "").lower()
    full_text = f"{title} {description}"
    
    # Check tags first (explicit intent takes precedence)
    for priority, tag_list in TAG_MAP.items():
        matching_tags = [t for t in tags if t in tag_list]
        if matching_tags:
            bucket = RUBRIC[priority]["bucket"]
            return ClassificationResult(
                priority=priority,
                bucket=bucket,
                reason=f"Tag match: {matching_tags[0]} -> {bucket}",
                confidence="high"
            )
    
    # Collect keyword matches for each priority level
    priority_scores = {}
    for priority, config in RUBRIC.items():
        matches = []
        for category, keywords in config["keywords"].items():
            for kw in keywords:
                if kw in full_text:
                    matches.append((category, kw))
        if matches:
            priority_scores[priority] = matches
    
    # If we have matches, use the highest priority for P0-P2 (conservative)
    # For P3/P4, prefer lower priority (P4 over P3) as these are maintenance
    if priority_scores:
        # Priority order: P0 > P1 > P2 (conservative for critical/important)
        for priority in ["P0", "P1", "P2"]:
            if priority in priority_scores:
                matches = priority_scores[priority]
                bucket = RUBRIC[priority]["bucket"]
                categories = list(set(m[0] for m in matches))
                keywords = [m[1] for m in matches[:2]]  # Show first 2 keywords
                return ClassificationResult(
                    priority=priority,
                    bucket=bucket,
                    reason=f"{categories[0]}: matches '{keywords[0]}'" +
                           (f", '{keywords[1]}'" if len(keywords) > 1 else ""),
                    confidence="medium" if len(matches) == 1 else "high"
                )
        # For P3/P4, prefer P4 (maintenance) over P3 (engineering quality)
        for priority in ["P4", "P3"]:
            if priority in priority_scores:
                matches = priority_scores[priority]
                bucket = RUBRIC[priority]["bucket"]
                categories = list(set(m[0] for m in matches))
                keywords = [m[1] for m in matches[:2]]  # Show first 2 keywords
                return ClassificationResult(
                    priority=priority,
                    bucket=bucket,
                    reason=f"{categories[0]}: matches '{keywords[0]}'" +
                           (f", '{keywords[1]}'" if len(keywords) > 1 else ""),
                    confidence="medium" if len(matches) == 1 else "high"
                )
    
    # Check for type-based defaults (low confidence)
    if ticket_type in TYPE_DEFAULTS:
        default_priority = TYPE_DEFAULTS[ticket_type]
        bucket = RUBRIC[default_priority]["bucket"]
        return ClassificationResult(
            priority=default_priority,
            bucket=bucket,
            reason=f"Default for type '{ticket_type}': {bucket}",
            confidence="low"
        )
    
    # Ambiguous - return unknown
    return ClassificationResult(
        priority="unknown",
        bucket="ambiguous",
        reason="No clear rubric match; insufficient keywords or indicators",
        confidence="unknown"
    )


def format_priority(p: str) -> str:
    """Normalize priority format."""
    if not p:
        return ""
    p = p.strip().upper()
    if p.startswith("P") and p[1:].isdigit():
        return p
    if p.isdigit() and 0 <= int(p) <= 4:
        return f"P{p}"
    return p


def print_results(results: List[dict], apply: bool, include_unknown: bool = False, json_output: bool = False) -> None:
    """Print classification results in a table or JSON format."""
    if json_output:
        # JSON output for scripting
        import json
        output = {
            "mode": "apply" if apply else "dry-run",
            "tickets": [
                {
                    "id": r["id"],
                    "title": r.get("ticket", {}).get("title", ""),
                    "current": r["current"],
                    "proposed": r["proposed"],
                    "bucket": r.get("bucket", "-"),
                    "reason": r["reason"],
                    "confidence": r.get("confidence", "-"),
                    "would_change": r["current"] != r["proposed"] and r["proposed"] != "unknown",
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "would_change": sum(1 for r in results if r["current"] != r["proposed"] and r["proposed"] != "unknown"),
                "unknown": sum(1 for r in results if r["proposed"] == "unknown"),
                "unchanged": len(results) - sum(1 for r in results if r["current"] != r["proposed"] and r["proposed"] != "unknown") - sum(1 for r in results if r["proposed"] == "unknown"),
            }
        }
        print(json.dumps(output, indent=2))
        return
    
    # Human-readable table output
    print()
    if apply:
        print("Priority Reclassification Results (APPLIED):")
    else:
        print("Priority Reclassification Results (DRY RUN):")
    print()
    
    # Header
    print(f"{'Ticket':<12} {'Current':<10} {'Proposed':<10} {'Bucket':<20} {'Reason':<35}")
    print("-" * 95)
    
    for r in results:
        ticket_id = r["id"]
        current = r["current"]
        proposed = r["proposed"]
        bucket = r.get("bucket", "-")
        reason = r["reason"]
        
        # Truncate long fields
        bucket_display = bucket[:17] + "..." if len(bucket) > 20 else bucket
        reason_display = reason[:32] + "..." if len(reason) > 35 else reason
        
        change_marker = "*" if current != proposed else " "
        print(f"{change_marker}{ticket_id:<11} {current:<10} {proposed:<10} {bucket_display:<20} {reason_display}")
    
    print()
    changed = sum(1 for r in results if r["current"] != r["proposed"] and r["proposed"] != "unknown")
    unknown_count = sum(1 for r in results if r["proposed"] == "unknown")
    skipped = unknown_count if not include_unknown else 0
    
    print(f"Total: {len(results)} tickets, {changed} would change, {unknown_count} unknown")
    if skipped > 0:
        print(f"({skipped} unknown tickets skipped - use --include-unknown to show)")
    
    if not apply and changed > 0:
        print()
        print("Run with --apply to make these changes.")


def get_tickets_dir(project_root: Path) -> Path:
    """Get the tickets directory path."""
    return project_root / ".tickets"


def parse_frontmatter(content: str) -> Tuple[dict, str, str]:
    """Parse frontmatter from ticket content.
    
    Returns (frontmatter_dict, frontmatter_text, body_text).
    """
    lines = content.split("\n")
    frontmatter_lines = []
    body_lines = []
    in_frontmatter = False
    frontmatter_started = False
    
    for line in lines:
        if line.strip() == "---":
            if not frontmatter_started:
                frontmatter_started = True
                in_frontmatter = True
                continue
            elif in_frontmatter:
                in_frontmatter = False
                continue
        
        if in_frontmatter:
            frontmatter_lines.append(line)
        else:
            body_lines.append(line)
    
    # Parse frontmatter key:value pairs
    frontmatter = {}
    for line in frontmatter_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()
    
    return frontmatter, "\n".join(frontmatter_lines), "\n".join(body_lines)


def update_frontmatter_priority(frontmatter_text: str, new_priority: str) -> str:
    """Update priority in frontmatter text while preserving format."""
    lines = frontmatter_text.split("\n")
    new_lines = []
    priority_updated = False
    
    for line in lines:
        if line.strip().startswith("priority:"):
            # Preserve indentation
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}priority: {new_priority}")
            priority_updated = True
        else:
            new_lines.append(line)
    
    # If priority wasn't found, add it
    if not priority_updated:
        new_lines.append(f"priority: {new_priority}")
    
    return "\n".join(new_lines)


def add_note_to_ticket_body(body: str, note_content: str) -> str:
    """Add an audit note to the ticket body."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    note_entry = f"""

**{timestamp}**

{note_content}"""
    
    # Check if Notes section exists
    if "## Notes" in body:
        # Append to existing Notes section
        parts = body.split("## Notes", 1)
        before_notes = parts[0].rstrip()
        after_notes = parts[1]
        return f"{before_notes}\n\n## Notes{note_entry}{after_notes}"
    else:
        # Create new Notes section at end
        body = body.rstrip()
        return f"{body}\n\n\n## Notes\n\n{note_entry.lstrip()}"


def update_ticket_priority(
    ticket_id: str,
    old_priority: str,
    new_priority: str,
    reason: str,
    project_root: Path,
) -> Tuple[bool, str]:
    """Update ticket priority and add audit note.
    
    Returns (success, error_message).
    """
    tickets_dir = get_tickets_dir(project_root)
    ticket_path = tickets_dir / f"{ticket_id}.md"
    
    if not ticket_path.exists():
        return False, f"Ticket file not found: {ticket_path}"
    
    try:
        content = ticket_path.read_text(encoding="utf-8")
        
        # Parse frontmatter and body
        frontmatter, frontmatter_text, body = parse_frontmatter(content)
        
        # Update priority in frontmatter
        new_frontmatter = update_frontmatter_priority(frontmatter_text, new_priority)
        
        # Add audit note
        note_content = f"Priority reclassified: {old_priority} → {new_priority}\n\nReason: {reason}"
        new_body = add_note_to_ticket_body(body, note_content)
        
        # Reconstruct file content
        new_content = f"---\n{new_frontmatter}\n---\n{new_body.lstrip()}"
        
        # Write back atomically
        temp_path = ticket_path.with_suffix(".md.tmp")
        temp_path.write_text(new_content, encoding="utf-8")
        temp_path.replace(ticket_path)
        
        return True, ""
    except Exception as e:
        return False, str(e)


def write_audit_trail(project_root: Path, results: List[dict], apply: bool) -> None:
    """Write audit trail to knowledge directory."""
    knowledge_dir = project_root / ".tf" / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"priority-reclassify-{timestamp}.md"
    filepath = knowledge_dir / filename
    
    lines = [
        "# Priority Reclassification Audit",
        "",
        f"**Timestamp:** {datetime.now().isoformat()}",
        f"**Mode:** {'APPLY' if apply else 'DRY RUN'}",
        "",
        "## Results",
        "",
        "| Ticket | Current | Proposed | Bucket | Confidence | Applied | Reason |",
        "|--------|---------|----------|--------|------------|---------|--------|",
    ]
    
    for r in results:
        applied = "Yes" if (apply and r["current"] != r["proposed"] and r["proposed"] != "unknown") else "No"
        bucket = r.get("bucket", "-")
        confidence = r.get("confidence", "-")
        lines.append(f"| {r['id']} | {r['current']} | {r['proposed']} | {bucket} | {confidence} | {applied} | {r['reason']} |")
    
    lines.extend([
        "",
        "## Summary",
        "",
    ])
    
    changed = sum(1 for r in results if r["current"] != r["proposed"] and r["proposed"] != "unknown")
    unknown_count = sum(1 for r in results if r["proposed"] == "unknown")
    lines.append(f"- Total tickets processed: {len(results)}")
    lines.append(f"- Priorities changed: {changed}")
    lines.append(f"- Unknown/ambiguous: {unknown_count}")
    lines.append(f"- Unchanged: {len(results) - changed - unknown_count}")
    
    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nAudit trail written to: {filepath}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tf priority-reclassify",
        description="Reclassify ticket priorities using P0-P4 rubric with rationale generation",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply priority changes (default is dry-run)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (required with --apply in non-interactive mode)",
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        metavar="N",
        help="Maximum number of tickets to modify (safety cap)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Apply changes even for ambiguous/unknown classifications",
    )
    parser.add_argument(
        "--ids",
        help="Comma-separated list of ticket IDs to process",
    )
    parser.add_argument(
        "--ready",
        action="store_true",
        help="Process all ready tickets",
    )
    parser.add_argument(
        "--status",
        help="Filter by ticket status",
    )
    parser.add_argument(
        "--tag",
        help="Filter by tag",
    )
    parser.add_argument(
        "--project",
        help="Operate on project at <path>",
    )
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include closed tickets in processing (default: excluded)",
    )
    parser.add_argument(
        "--include-unknown",
        action="store_true",
        help="Include tickets with unknown/ambiguous priority in output (default: skipped)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON for scripting",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write report file to .tf/knowledge/ (default: disabled)",
    )
    
    args = parser.parse_args(argv)
    
    # Check tk is available
    if shutil.which("tk") is None:
        print("tk not found in PATH; cannot query tickets.", file=sys.stderr)
        return 1
    
    # Resolve project root
    if args.project:
        project_root = Path(args.project).expanduser()
    else:
        project_root = find_project_root()
    
    if not project_root:
        print("No .tf project found. Run from a project directory or use --project.", file=sys.stderr)
        return 1
    
    # Collect ticket IDs
    ticket_ids: List[str] = []
    
    if args.ids:
        ticket_ids = [t.strip() for t in args.ids.split(",") if t.strip()]
    elif args.ready:
        ticket_ids = get_ticket_ids_from_ready()
        if not ticket_ids:
            print("No ready tickets found.", file=sys.stderr)
            return 0
    elif args.status:
        ticket_ids = get_ticket_ids_by_status(args.status)
        if not ticket_ids:
            print(f"No tickets with status '{args.status}' found.", file=sys.stderr)
            return 0
    elif args.tag:
        ticket_ids = get_ticket_ids_by_tag(args.tag)
        if not ticket_ids:
            print(f"No tickets with tag '{args.tag}' found.", file=sys.stderr)
            return 0
    else:
        parser.print_help()
        print("\nError: Must specify one of --ids, --ready, --status, or --tag", file=sys.stderr)
        return 1
    
    # Process tickets
    results = []
    
    for ticket_id in ticket_ids:
        returncode, stdout, stderr = run_tk_command(["show", ticket_id])
        if returncode != 0:
            print(f"Warning: Could not fetch ticket {ticket_id}: {stderr}", file=sys.stderr)
            continue
        
        ticket = parse_ticket_show(stdout)
        if not ticket["id"]:
            ticket["id"] = ticket_id
        
        # Skip closed tickets unless --include-closed is set
        if ticket.get("status") == "closed" and not args.include_closed:
            continue
        
        # Classify using rubric
        classification = classify_priority_full(ticket)
        current = format_priority(ticket.get("priority", ""))
        
        results.append({
            "id": ticket_id,
            "current": current or "(none)",
            "proposed": classification.priority,
            "bucket": classification.bucket,
            "reason": classification.reason,
            "confidence": classification.confidence,
            "ticket": ticket,
        })
    
    if not results:
        print("No tickets to process.")
        return 0
    
    # Filter out unknown priorities unless --include-unknown is set
    display_results = results
    if not args.include_unknown:
        display_results = [r for r in results if r["proposed"] != "unknown"]
        skipped = len(results) - len(display_results)
        if skipped > 0:
            print(f"\nNote: {skipped} ticket(s) with ambiguous priority skipped (use --include-unknown to show)")
    
    # Safety: Check for --yes requirement in non-interactive mode
    changes_to_make = []
    if args.apply:
        changes_to_make = [r for r in results if r["current"] != r["proposed"]]
        # Without --force, skip unknown priorities
        if not args.force:
            changes_to_make = [r for r in changes_to_make if r["proposed"] != "unknown"]
        
        if changes_to_make:
            # Check if we need confirmation
            if not args.yes:
                if is_interactive():
                    # Interactive mode: prompt for confirmation
                    if not confirm_changes(changes_to_make, args.max_changes):
                        print("\nOperation cancelled by user.")
                        return 0
                else:
                    # Non-interactive mode: require --yes
                    print("Error: --apply in non-interactive mode requires --yes flag", file=sys.stderr)
                    print("Run with --yes to confirm, or use --max-changes to limit scope", file=sys.stderr)
                    return 1
            
            # Apply max-changes limit
            if args.max_changes and len(changes_to_make) > args.max_changes:
                print(f"\nNote: Limiting to {args.max_changes} changes (out of {len(changes_to_make)} total)")
                changes_to_make = changes_to_make[:args.max_changes]
    
    # Apply changes if requested
    applied_count = 0
    failed_updates = []
    if args.apply and changes_to_make:
        for r in changes_to_make:
            success, error = update_ticket_priority(
                ticket_id=r["id"],
                old_priority=r["current"],
                new_priority=r["proposed"],
                reason=r["reason"],
                project_root=project_root,
            )
            if success:
                applied_count += 1
            else:
                failed_updates.append((r["id"], error))
        
        if applied_count > 0 and not args.json:
            print(f"\nApplied priority changes to {applied_count} ticket(s).")
        if failed_updates:
            print(f"\nFailed to update {len(failed_updates)} ticket(s):", file=sys.stderr)
            for ticket_id, error in failed_updates:
                print(f"  - {ticket_id}: {error}", file=sys.stderr)
    
    # Output results
    if display_results:
        print_results(display_results, args.apply, args.include_unknown, args.json)
    
    # Write report file if requested (includes all results, even unknown)
    if args.report:
        write_audit_trail(project_root, results, args.apply)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
