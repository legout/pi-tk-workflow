"""Knowledge base management CLI commands.

Implements the tf kb command for managing the knowledge base:
- ls: List topics from index.json with filtering options
- show: Show a specific topic with metadata and doc paths
- archive: Move a topic to the archive
- restore: Restore a topic from the archive
- delete: Permanently delete a topic (active or archived)
- validate: Validate knowledge base integrity and detect index drift
"""

from __future__ import annotations

import datetime
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

from tf.kb_helpers import (
    atomic_read_index,
    atomic_write_index,
    resolve_knowledge_dir,
    is_topic_archived,
    get_topic_docs,
    get_topic_type,
)


def cmd_ls(
    knowledge_dir: Path,
    format_json: bool = False,
    topic_type: Optional[str] = None,
    include_archived: bool = False,
) -> int:
    """List knowledge base topics from index.json.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        format_json: Output in JSON format
        topic_type: Filter by topic type (seed, plan, spike, baseline)
        include_archived: Include archived topics in listing
    """
    data = atomic_read_index(knowledge_dir)

    if data is None:
        if format_json:
            print(json.dumps({"topics": []}))
        else:
            print("No knowledge base index found.")
            print(f"Expected: {knowledge_dir / 'index.json'}")
        return 0

    topics = data.get("topics", [])

    # Filter by type if specified
    if topic_type:
        topics = [t for t in topics if get_topic_type(t.get("id", "")) == topic_type]

    # Get archived topics if requested
    archived_topics = []
    if include_archived:
        archive_dir = knowledge_dir / "archive" / "topics"
        if archive_dir.exists():
            for topic_dir in archive_dir.iterdir():
                if topic_dir.is_dir():
                    topic_id = topic_dir.name
                    # Skip if already in active topics
                    if not any(t.get("id") == topic_id for t in topics):
                        archived_topics.append({
                            "id": topic_id,
                            "title": "(archived)",
                            "archived": True,
                        })

    # Combine active and archived topics
    all_topics = list(topics) + archived_topics

    if format_json:
        output = {
            "topics": [
                {
                    "id": t.get("id", "unknown"),
                    "title": t.get("title", "Untitled"),
                    "type": get_topic_type(t.get("id", "")),
                    "archived": t.get("archived", False) or is_topic_archived(knowledge_dir, t.get("id", "")),
                }
                for t in all_topics
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        if not all_topics:
            print("Knowledge base is empty.")
        else:
            active_count = len(topics)
            archived_count = len(archived_topics)
            
            if include_archived:
                print(f"Knowledge base topics ({active_count} active, {archived_count} archived):")
            else:
                print(f"Knowledge base topics ({active_count} active):")
            print()
            
            for topic in all_topics:
                topic_id = topic.get("id", "unknown")
                title = topic.get("title", "Untitled")
                ttype = get_topic_type(topic_id)
                archived_marker = " [ARCHIVED]" if topic.get("archived") or is_topic_archived(knowledge_dir, topic_id) else ""
                print(f"  {topic_id} [{ttype}]{archived_marker} - {title}")

    return 0


def cmd_show(
    knowledge_dir: Path,
    topic_id: str,
    format_json: bool = False,
) -> int:
    """Show a specific knowledge base topic.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID to show
        format_json: Output in JSON format
    """
    data = atomic_read_index(knowledge_dir)

    if data is None:
        print(f"Error: Knowledge base index not found at {knowledge_dir / 'index.json'}", file=sys.stderr)
        return 1

    topics = data.get("topics", [])

    # Find topic by id
    topic = None
    for t in topics:
        if isinstance(t, dict) and t.get("id") == topic_id:
            topic = t
            break

    # Check if topic is archived
    archived = False
    archive_path = None
    
    if topic is None:
        # Try to find in archive
        archive_topic_dir = knowledge_dir / "archive" / "topics" / topic_id
        if archive_topic_dir.exists():
            archived = True
            archive_path = archive_topic_dir
            # Create minimal topic info from archive
            topic = {"id": topic_id, "title": "(archived - not in index)"}
        else:
            print(f"Error: Topic '{topic_id}' not found in knowledge base.", file=sys.stderr)
            return 1
    else:
        # Check if topic is archived even if found in index
        archived = is_topic_archived(knowledge_dir, topic_id)
        if archived:
            archive_path = knowledge_dir / "archive" / "topics" / topic_id

    # Get doc paths
    docs = get_topic_docs(knowledge_dir, topic_id, archived)

    if format_json:
        output = dict(topic)
        output["type"] = get_topic_type(topic_id)
        output["archived"] = archived
        if archive_path:
            output["archive_path"] = str(archive_path.relative_to(knowledge_dir))
        output["docs"] = docs
        print(json.dumps(output, indent=2))
    else:
        print(f"ID: {topic.get('id', 'unknown')}")
        print(f"Type: {get_topic_type(topic_id)}")
        print(f"Title: {topic.get('title', 'Untitled')}")
        
        if archived:
            print(f"Status: ARCHIVED")
            if archive_path:
                print(f"Archive path: {archive_path.relative_to(knowledge_dir)}")
        else:
            print(f"Status: active")
        
        if "overview" in topic:
            print(f"Overview: {topic['overview']}")
        if "sources" in topic:
            print(f"Sources: {topic['sources']}")
        if "keywords" in topic:
            print(f"Keywords: {', '.join(topic['keywords'])}")
        
        if docs:
            print(f"\nDocuments:")
            for doc_type, doc_path in docs.items():
                exists_marker = "✓" if doc_path.get("exists") else "✗"
                print(f"  [{exists_marker}] {doc_type}: {doc_path.get('path', 'N/A')}")

    return 0


def cmd_index_status(knowledge_dir: Path, format_json: bool = False) -> int:
    """Show knowledge base index status."""
    index_path = knowledge_dir / "index.json"
    data = atomic_read_index(knowledge_dir)

    if data is None:
        if format_json:
            print(json.dumps({"status": "not_found", "path": str(index_path), "topics": 0}))
        else:
            print(f"Knowledge base index: NOT FOUND")
            print(f"Expected path: {index_path}")
        return 1

    topics = data.get("topics", [])
    topic_count = len(topics)

    # Count archived topics
    archive_dir = knowledge_dir / "archive" / "topics"
    archived_count = 0
    if archive_dir.exists():
        archived_count = len([d for d in archive_dir.iterdir() if d.is_dir()])

    if format_json:
        print(json.dumps({
            "status": "ok",
            "path": str(index_path),
            "topics": topic_count,
            "archived_topics": archived_count,
        }))
    else:
        print(f"Knowledge base index: OK")
        print(f"Path: {index_path}")
        print(f"Active topics: {topic_count}")
        if archived_count > 0:
            print(f"Archived topics: {archived_count}")
    return 0


def cmd_archive(
    knowledge_dir: Path,
    topic_id: str,
    reason: Optional[str] = None,
) -> int:
    """Archive a knowledge base topic.
    
    Moves the topic directory from topics/ to archive/topics/ and
    removes the entry from index.json. Idempotent - if already archived,
    prints a message and returns success.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID to archive
        reason: Optional reason for archiving
        
    Returns:
        0 on success, 1 on error
    """
    # Check if already archived (idempotent)
    if is_topic_archived(knowledge_dir, topic_id):
        print(f"Topic '{topic_id}' is already archived.")
        return 0
    
    # Check if topic exists in active topics
    topic_dir = knowledge_dir / "topics" / topic_id
    if not topic_dir.exists():
        print(f"Error: Topic '{topic_id}' not found in active topics.", file=sys.stderr)
        return 1
    
    # Create archive directory
    archive_dir = knowledge_dir / "archive" / "topics" / topic_id
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Move topic to archive
    try:
        topic_dir.rename(archive_dir)
    except OSError as e:
        print(f"Error: Failed to move topic to archive: {e}", file=sys.stderr)
        return 1
    
    # Read and update index.json
    data = atomic_read_index(knowledge_dir)
    if data is not None:
        topics = data.get("topics", [])
        original_count = len(topics)
        # Filter out the archived topic
        topics = [t for t in topics if isinstance(t, dict) and t.get("id") != topic_id]
        
        if len(topics) < original_count:
            data["topics"] = topics
            atomic_write_index(knowledge_dir, data)
    
    # Write archive.md with timestamp and reason
    timestamp = datetime.datetime.now().isoformat()
    archive_content = f"""# Archive Record: {topic_id}

**Archived**: {timestamp}
"""
    if reason:
        archive_content += f"\n**Reason**: {reason}\n"
    archive_md = archive_dir / "archive.md"
    archive_md.write_text(archive_content, encoding="utf-8")
    
    print(f"Archived topic '{topic_id}' to {archive_dir.relative_to(knowledge_dir)}")
    return 0


def cmd_restore(
    knowledge_dir: Path,
    topic_id: str,
) -> int:
    """Restore an archived knowledge base topic.
    
    Moves the topic directory from archive/topics/ back to topics/ and
    re-adds the entry to index.json. Idempotent - if already active,
    prints a message and returns success.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID to restore
        
    Returns:
        0 on success, 1 on error
    """
    # Check if already active (idempotent)
    topic_dir = knowledge_dir / "topics" / topic_id
    if topic_dir.exists():
        print(f"Topic '{topic_id}' is already active.")
        return 0
    
    # Check if topic exists in archive
    archive_dir = knowledge_dir / "archive" / "topics" / topic_id
    if not archive_dir.exists():
        print(f"Error: Topic '{topic_id}' not found in archive.", file=sys.stderr)
        return 1
    
    # Create topics directory
    topic_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Move topic from archive to active
    try:
        archive_dir.rename(topic_dir)
    except OSError as e:
        print(f"Error: Failed to restore topic from archive: {e}", file=sys.stderr)
        return 1
    
    # Read and update index.json
    data = atomic_read_index(knowledge_dir)
    if data is None:
        data = {"topics": []}
    
    topics = data.get("topics", [])
    
    # Check if already in index (shouldn't happen if properly archived, but handle it)
    if not any(isinstance(t, dict) and t.get("id") == topic_id for t in topics):
        # Reconstruct minimal topic entry
        # Try to read from archive.md for metadata
        archive_md = topic_dir / "archive.md"
        title = topic_id  # Default to ID as title
        
        # Try to find a title from existing docs
        for doc_name in ["overview.md", "plan.md", "sources.md"]:
            doc_path = topic_dir / doc_name
            if doc_path.exists():
                content = doc_path.read_text(encoding="utf-8")
                # Extract first heading as title
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                break
        
        new_topic = {
            "id": topic_id,
            "title": title,
        }
        topics.append(new_topic)
        data["topics"] = topics
        atomic_write_index(knowledge_dir, data)
    
    print(f"Restored topic '{topic_id}' to active topics")
    return 0


def cmd_delete(
    knowledge_dir: Path,
    topic_id: str,
) -> int:
    """Permanently delete a knowledge base topic.
    
    Removes the topic directory (from active or archive) and
    removes the entry from index.json. Permanent deletion.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID to delete
        
    Returns:
        0 on success, 1 on error (topic not found)
    """
    # Determine if topic is active, archived, or doesn't exist
    topic_dir = knowledge_dir / "topics" / topic_id
    archive_dir = knowledge_dir / "archive" / "topics" / topic_id
    
    deleted_paths = []
    was_in_index = False
    
    # Delete from active topics if exists
    if topic_dir.exists():
        try:
            shutil.rmtree(topic_dir)
            deleted_paths.append(str(topic_dir.relative_to(knowledge_dir)))
        except OSError as e:
            print(f"Error: Failed to delete active topic: {e}", file=sys.stderr)
            return 1
    
    # Delete from archive if exists
    if archive_dir.exists():
        try:
            shutil.rmtree(archive_dir)
            deleted_paths.append(str(archive_dir.relative_to(knowledge_dir)))
        except OSError as e:
            print(f"Error: Failed to delete archived topic: {e}", file=sys.stderr)
            return 1
    
    # If neither location had the topic, it's not found
    if not deleted_paths:
        print(f"Error: Topic '{topic_id}' not found in knowledge base.", file=sys.stderr)
        return 1
    
    # Remove from index.json if present
    data = atomic_read_index(knowledge_dir)
    if data is not None:
        topics = data.get("topics", [])
        original_count = len(topics)
        topics = [t for t in topics if isinstance(t, dict) and t.get("id") != topic_id]
        
        if len(topics) < original_count:
            was_in_index = True
            data["topics"] = topics
            atomic_write_index(knowledge_dir, data)
    
    # Print deleted paths
    for path in deleted_paths:
        print(f"Deleted: {path}")
    if was_in_index:
        print(f"Removed index entry for '{topic_id}'")
    
    return 0


def _extract_title_from_frontmatter(topic_dir: Path) -> Optional[str]:
    """Extract title from frontmatter in topic markdown files.
    
    Looks for title in order: first # heading, frontmatter title field.
    
    Args:
        topic_dir: Path to the topic directory
        
    Returns:
        Extracted title or None if not found
    """
    # Check common doc files in order of priority
    doc_files = ["overview.md", "plan.md", "sources.md", "backlog.md"]
    
    for doc_name in doc_files:
        doc_path = topic_dir / doc_name
        if not doc_path.exists():
            continue
            
        try:
            content = doc_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            # Skip frontmatter if present
            in_frontmatter = False
            frontmatter_title = None
            
            for line in lines:
                stripped = line.strip()
                
                # Detect frontmatter start/end
                if stripped == "---":
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        in_frontmatter = False
                        continue
                
                # Extract title from frontmatter
                if in_frontmatter and stripped.startswith("title:"):
                    frontmatter_title = stripped[6:].strip().strip('"\'')
                    continue
                
                # Look for first # heading (outside frontmatter)
                if not in_frontmatter and stripped.startswith("# "):
                    return stripped[2:].strip()
            
            # If we found a title in frontmatter but no heading, use it
            if frontmatter_title:
                return frontmatter_title
                
        except (IOError, OSError):
            continue
    
    return None


def cmd_rebuild_index(
    knowledge_dir: Path,
    dry_run: bool = False,
    format_json: bool = False,
) -> int:
    """Rebuild the knowledge base index from filesystem.
    
    Scans the topics/ directory and regenerates index.json with canonical
    entries. Preserves existing metadata when available. Outputs entries
    in stable order by topic ID.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        dry_run: If True, print what would change without writing
        format_json: Output dry-run results in JSON format
        
    Returns:
        0 on success, 1 on error
    """
    topics_dir = knowledge_dir / "topics"
    
    if not topics_dir.exists():
        if dry_run:
            if format_json:
                print(json.dumps({
                    "dry_run": True,
                    "would_write": False,
                    "reason": "topics directory does not exist",
                    "topics": [],
                }))
            else:
                print("Dry-run: topics directory does not exist, would create empty index")
            return 0
        else:
            print(f"Error: Topics directory not found: {topics_dir}", file=sys.stderr)
            return 1
    
    # Read existing index for metadata preservation
    existing_data = atomic_read_index(knowledge_dir)
    existing_topics = {}
    if existing_data and isinstance(existing_data, dict):
        for t in existing_data.get("topics", []):
            if isinstance(t, dict) and "id" in t:
                existing_topics[t["id"]] = t
    
    # Discover all topic directories
    discovered_topics: list[dict[str, Any]] = []
    
    for topic_dir in sorted(topics_dir.iterdir()):
        if not topic_dir.is_dir():
            continue
            
        topic_id = topic_dir.name
        
        # Start with existing metadata if available
        if topic_id in existing_topics:
            topic_entry = dict(existing_topics[topic_id])
        else:
            # Create new entry
            topic_entry = {"id": topic_id}
            
            # Try to extract title
            title = _extract_title_from_frontmatter(topic_dir)
            if title:
                topic_entry["title"] = title
            else:
                # Default title from ID
                topic_entry["title"] = topic_id.replace("-", " ").replace("_", " ").title()
        
        # Ensure standard doc paths exist
        doc_types = ["overview", "sources", "plan", "backlog"]
        for doc_type in doc_types:
            doc_path = topic_dir / f"{doc_type}.md"
            if doc_path.exists():
                rel_path = f"topics/{topic_id}/{doc_type}.md"
                topic_entry[doc_type] = rel_path
            elif doc_type in topic_entry:
                # Remove stale path reference if file doesn't exist
                del topic_entry[doc_type]
        
        discovered_topics.append(topic_entry)
    
    # Sort by topic ID for stable ordering
    discovered_topics.sort(key=lambda t: t.get("id", ""))
    
    # Build new index data
    new_data = {
        "topics": discovered_topics,
        "updated": datetime.datetime.now().isoformat(),
    }
    
    # Calculate changes for dry-run output
    existing_ids = set(existing_topics.keys())
    new_ids = {t.get("id") for t in discovered_topics}
    
    added_ids = new_ids - existing_ids
    removed_ids = existing_ids - new_ids
    unchanged_ids = existing_ids & new_ids
    
    if dry_run:
        if format_json:
            output = {
                "dry_run": True,
                "would_write": True,
                "knowledge_dir": str(knowledge_dir),
                "current_topics": len(existing_topics),
                "new_topics": len(discovered_topics),
                "added": sorted(added_ids),
                "removed": sorted(removed_ids),
                "unchanged": sorted(unchanged_ids),
                "proposed_index": new_data,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Dry-run: Would rebuild index at {knowledge_dir / 'index.json'}")
            print(f"  Current topics: {len(existing_topics)}")
            print(f"  New topics: {len(discovered_topics)}")
            
            if added_ids:
                print(f"\n  Added ({len(added_ids)}):")
                for tid in sorted(added_ids):
                    topic = next((t for t in discovered_topics if t.get("id") == tid), None)
                    title = topic.get("title", "Untitled") if topic else "Unknown"
                    print(f"    + {tid} - {title}")
            
            if removed_ids:
                print(f"\n  Removed ({len(removed_ids)}):")
                for tid in sorted(removed_ids):
                    old_topic = existing_topics.get(tid, {})
                    title = old_topic.get("title", "Untitled")
                    print(f"    - {tid} - {title}")
            
            if unchanged_ids:
                print(f"\n  Unchanged ({len(unchanged_ids)}):")
                for tid in sorted(unchanged_ids):
                    print(f"    = {tid}")
            
            if not added_ids and not removed_ids:
                print("\n  No changes detected.")
        
        return 0
    
    # Perform the write
    try:
        atomic_write_index(knowledge_dir, new_data)
        print(f"Rebuilt index: {len(discovered_topics)} topics")
        
        if added_ids:
            print(f"  Added: {len(added_ids)}")
        if removed_ids:
            print(f"  Removed: {len(removed_ids)}")
        
        return 0
    except (OSError, PermissionError) as e:
        print(f"Error: Failed to write index: {e}", file=sys.stderr)
        return 1


def cmd_validate(
    knowledge_dir: Path,
    format_json: bool = False,
) -> int:
    """Validate knowledge base integrity and detect index drift.
    
    Checks for:
    - Missing files referenced by index entries (overview, sources, etc.)
    - Orphan directories under topics/* not referenced in index
    - Duplicate topic IDs in index
    
    Args:
        knowledge_dir: Path to the knowledge directory
        format_json: Output in JSON format
        
    Returns:
        0 if no issues found, 1 if errors detected
    """
    from collections import Counter
    
    data = atomic_read_index(knowledge_dir)
    
    if data is None:
        if format_json:
            print(json.dumps({
                "valid": False,
                "errors": ["Knowledge base index not found"],
                "warnings": [],
                "orphan_dirs": [],
                "missing_files": [],
                "duplicate_ids": []
            }))
        else:
            print("Error: Knowledge base index not found.", file=sys.stderr)
            print(f"Expected: {knowledge_dir / 'index.json'}", file=sys.stderr)
        return 1
    
    topics = data.get("topics", [])
    errors: list[str] = []
    warnings: list[str] = []
    missing_files: list[dict[str, Any]] = []
    orphan_dirs: list[str] = []
    duplicate_ids: list[str] = []
    
    # Check for duplicate topic IDs
    topic_ids = [t.get("id", "") for t in topics if isinstance(t, dict)]
    id_counts = Counter(topic_ids)
    duplicates = {tid: count for tid, count in id_counts.items() if count > 1}
    if duplicates:
        for tid, count in duplicates.items():
            duplicate_ids.append(tid)
            errors.append(f"Duplicate topic ID '{tid}' appears {count} times in index")
    
    # Check for missing files referenced by index entries
    for topic in topics:
        if not isinstance(topic, dict):
            continue
        topic_id = topic.get("id", "")
        if not topic_id:
            continue
            
        # Check referenced files
        for field in ["overview", "sources", "plan", "backlog"]:
            if field in topic:
                file_path = knowledge_dir / topic[field]
                if not file_path.exists():
                    missing_files.append({
                        "topic_id": topic_id,
                        "field": field,
                        "path": topic[field]
                    })
                    errors.append(f"Missing file: {topic[field]} (referenced by '{topic_id}')")
    
    # Check for orphan directories (not in index but exists in topics/)
    topics_dir = knowledge_dir / "topics"
    if topics_dir.exists():
        indexed_ids = set(topic_ids)
        for topic_dir in topics_dir.iterdir():
            if topic_dir.is_dir():
                topic_id = topic_dir.name
                if topic_id not in indexed_ids:
                    orphan_dirs.append(topic_id)
                    warnings.append(f"Orphan directory: topics/{topic_id} (not in index)")
    
    # Output results
    has_errors = len(errors) > 0
    has_warnings = len(warnings) > 0
    
    if format_json:
        output = {
            "valid": not has_errors,
            "knowledge_dir": str(knowledge_dir),
            "topics_count": len(topics),
            "errors": errors,
            "warnings": warnings,
            "missing_files": missing_files,
            "orphan_dirs": orphan_dirs,
            "duplicate_ids": duplicate_ids,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Knowledge base validation: {'PASSED' if not has_errors else 'FAILED'}")
        print(f"Knowledge directory: {knowledge_dir}")
        print(f"Topics in index: {len(topics)}")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for error in errors:
                print(f"  ✗ {error}")
        
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        if not errors and not warnings:
            print("\nNo issues found.")
        
        print()  # Blank line at end
    
    return 1 if has_errors else 0


def usage() -> None:
    """Print usage information."""
    print(
        """Knowledge base management commands.

Usage:
  tf kb ls [--json] [--type <type>] [--archived] [--knowledge-dir <path>]
  tf kb show <topic-id> [--json] [--knowledge-dir <path>]
  tf kb index [--json] [--knowledge-dir <path>]
  tf kb validate [--json] [--knowledge-dir <path>]
  tf kb rebuild-index [--dry-run] [--json] [--knowledge-dir <path>]
  tf kb archive <topic-id> [--reason TEXT] [--knowledge-dir <path>]
  tf kb restore <topic-id> [--knowledge-dir <path>]
  tf kb delete <topic-id> [--knowledge-dir <path>]
  tf kb --help

Commands:
  ls             List all knowledge base topics
                 --type seed|plan|spike|baseline  Filter by topic type
                 --archived                       Include archived topics
  show           Show details for a specific topic
  index          Show index status and statistics
  validate       Validate knowledge base integrity
                 Detects missing files, orphan dirs, and duplicate IDs
  rebuild-index  Regenerate index.json from filesystem
                 --dry-run  Preview changes without writing
  archive        Move a topic to the archive
                 --reason TEXT  Optional reason for archiving
  restore        Restore a topic from the archive
  delete         Permanently delete a topic (active or archived)

Options:
  --json      Output in JSON format
  --knowledge-dir <path>  Use specific knowledge directory
"""
    )


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for kb CLI."""
    if argv is None:
        argv = sys.argv[1:]
    
    # Handle help/usage
    if not argv or argv[0] in {"-h", "help", "--help"}:
        usage()
        return 0
    
    # Parse global options
    knowledge_dir_override: Optional[Path] = None
    format_json = False
    topic_type: Optional[str] = None
    include_archived = False
    dry_run = False
    
    # Extract global flags before subcommand parsing
    filtered_argv = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            format_json = True
        elif arg == "--dry-run":
            dry_run = True
        elif arg == "--knowledge-dir" and i + 1 < len(argv):
            knowledge_dir_override = Path(argv[i + 1]).expanduser()
            i += 1
        elif arg == "--type" and i + 1 < len(argv):
            topic_type = argv[i + 1]
            i += 1
        elif arg == "--archived":
            include_archived = True
        else:
            filtered_argv.append(arg)
        i += 1
    
    if not filtered_argv:
        usage()
        return 0
    
    command = filtered_argv[0]
    rest = filtered_argv[1:]
    
    # Resolve knowledge directory with CLI override support
    knowledge_dir = resolve_knowledge_dir(knowledge_dir_override=knowledge_dir_override)
    
    # Dispatch commands
    if command == "ls":
        return cmd_ls(
            knowledge_dir,
            format_json=format_json,
            topic_type=topic_type,
            include_archived=include_archived,
        )
    
    if command == "show":
        if not rest or rest[0].startswith("-"):
            print("Error: Topic ID required for 'show' command", file=sys.stderr)
            print("Usage: tf kb show <topic-id>", file=sys.stderr)
            return 1
        topic_id = rest[0]
        return cmd_show(knowledge_dir, topic_id, format_json=format_json)
    
    if command == "index":
        return cmd_index_status(knowledge_dir, format_json=format_json)
    
    if command == "validate":
        return cmd_validate(knowledge_dir, format_json=format_json)
    
    if command == "rebuild-index":
        return cmd_rebuild_index(knowledge_dir, dry_run=dry_run, format_json=format_json)
    
    if command == "archive":
        if not rest or rest[0].startswith("-"):
            print("Error: Topic ID required for 'archive' command", file=sys.stderr)
            print("Usage: tf kb archive <topic-id> [--reason TEXT]", file=sys.stderr)
            return 1
        topic_id = rest[0]
        # Parse --reason flag
        reason: Optional[str] = None
        i = 1
        while i < len(rest):
            if rest[i] == "--reason" and i + 1 < len(rest):
                reason = rest[i + 1]
                i += 1
            i += 1
        return cmd_archive(knowledge_dir, topic_id, reason=reason)
    
    if command == "restore":
        if not rest or rest[0].startswith("-"):
            print("Error: Topic ID required for 'restore' command", file=sys.stderr)
            print("Usage: tf kb restore <topic-id>", file=sys.stderr)
            return 1
        topic_id = rest[0]
        return cmd_restore(knowledge_dir, topic_id)
    
    if command == "delete":
        if not rest or rest[0].startswith("-"):
            print("Error: Topic ID required for 'delete' command", file=sys.stderr)
            print("Usage: tf kb delete <topic-id>", file=sys.stderr)
            return 1
        topic_id = rest[0]
        return cmd_delete(knowledge_dir, topic_id)
    
    print(f"Unknown 'kb' subcommand: {command}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
