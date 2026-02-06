"""Knowledge base management CLI commands.

Implements the tf kb command for managing the knowledge base:
- ls: List topics from index.json with filtering options
- show: Show a specific topic with metadata and doc paths
- archive: Move a topic to the archive
- restore: Restore a topic from the archive
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Optional

from tf_cli.kb_helpers import (
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


def usage() -> None:
    """Print usage information."""
    print(
        """Knowledge base management commands.

Usage:
  tf kb ls [--json] [--type <type>] [--archived] [--knowledge-dir <path>]
  tf kb show <topic-id> [--json] [--knowledge-dir <path>]
  tf kb index [--json] [--knowledge-dir <path>]
  tf kb archive <topic-id> [--reason TEXT] [--knowledge-dir <path>]
  tf kb restore <topic-id> [--knowledge-dir <path>]
  tf kb --help

Commands:
  ls          List all knowledge base topics
              --type seed|plan|spike|baseline  Filter by topic type
              --archived                       Include archived topics
  show        Show details for a specific topic
  index       Show index status and statistics
  archive     Move a topic to the archive
              --reason TEXT  Optional reason for archiving
  restore     Restore a topic from the archive

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
    
    # Extract global flags before subcommand parsing
    filtered_argv = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            format_json = True
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
    
    print(f"Unknown 'kb' subcommand: {command}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
