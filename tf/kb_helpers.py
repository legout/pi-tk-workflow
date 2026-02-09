"""Knowledge base helper functions for tf kb commands.

Provides:
- resolve_knowledge_dir: Resolve knowledgeDir from config with CLI override support
- atomic_read_index: Atomically read and parse index.json
- atomic_write_index: Atomically write index.json using tmp + rename
- get_topic_type: Derive topic type from topic ID prefix
- is_topic_archived: Check if a topic is archived
- get_topic_docs: Get documentation paths for a topic

All operations use stdlib only (no external dependencies).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional


def resolve_knowledge_dir(
    project_path: Optional[Path] = None,
    knowledge_dir_override: Optional[Path] = None,
) -> Path:
    """Resolve the knowledge directory from config or default.

    Resolution order (highest priority first):
    1. knowledge_dir_override parameter (from --knowledge-dir CLI flag)
    2. TF_KNOWLEDGE_DIR environment variable
    3. workflow.knowledgeDir from local .tf/config/settings.json
    4. Default: .tf/knowledge (relative to repo root or cwd)

    Args:
        project_path: Optional explicit project path
        knowledge_dir_override: Optional CLI override (--knowledge-dir)

    Returns:
        Resolved Path to the knowledge directory
    """
    # 1. CLI override (--knowledge-dir)
    if knowledge_dir_override:
        return knowledge_dir_override.expanduser().resolve()

    # 2. Environment variable
    env_dir = os.environ.get("TF_KNOWLEDGE_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()

    # 3. Find repo root first, then check for local config
    repo_root = _find_repo_root()
    if repo_root:
        # Check for local config in repo
        local_config = repo_root / ".tf" / "config" / "settings.json"
        if local_config.is_file():
            try:
                with open(local_config, "r", encoding="utf-8") as f:
                    config = json.load(f)
                knowledge_dir = config.get("workflow", {}).get("knowledgeDir")
                if knowledge_dir:
                    path = Path(knowledge_dir).expanduser()
                    if path.is_absolute():
                        return path.resolve()
                    # Relative to repo root
                    return (repo_root / path).resolve()
            except (json.JSONDecodeError, IOError):
                pass
        # Default to .tf/knowledge in repo root
        return (repo_root / ".tf" / "knowledge").resolve()

    # 4. Explicit project path (used internally)
    if project_path:
        return (project_path / ".tf" / "knowledge").resolve()

    # 5. Fallback: .tf/knowledge in current directory
    return (Path.cwd() / ".tf" / "knowledge").resolve()


def _find_repo_root() -> Optional[Path]:
    """Find the repository root by looking for .tf directory with project markers."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        tf_dir = parent / ".tf"
        if tf_dir.is_dir():
            # Verify this looks like a ticketflow project
            has_tickets = (tf_dir / "tickets").is_dir()
            has_ralph = (tf_dir / "ralph").is_dir()
            has_bin = (tf_dir / "bin").is_dir()
            # Also check for pyproject.toml or AGENTS.md in parent
            has_pyproject = (parent / "pyproject.toml").is_file()
            has_agents = (parent / "AGENTS.md").is_file()

            # Must have at least one strong marker
            if has_tickets or has_ralph or has_bin or (has_pyproject and has_agents):
                return parent
    return None


def atomic_read_index(knowledge_dir: Path) -> Optional[dict[str, Any]]:
    """Atomically read and parse the index.json file.

    This function reads the index file in a way that is safe even if
    concurrent writes are happening (the write uses atomic tmp+rename).

    Args:
        knowledge_dir: Path to the knowledge directory

    Returns:
        Parsed JSON dict with 'topics' key, or None if file doesn't exist
        Returns empty topics list if file is corrupted

    Raises:
        PermissionError: If file exists but cannot be read
    """
    index_path = knowledge_dir / "index.json"

    if not index_path.exists():
        return None

    try:
        # Simple read - atomic writes use tmp+rename so we always see complete data
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize to dict with topics
        if isinstance(data, dict):
            if "topics" not in data:
                data["topics"] = []
            return data
        elif isinstance(data, list):
            # Handle legacy array format - assume it's topics
            return {"topics": data}
        else:
            # Invalid format, return empty
            return {"topics": []}

    except json.JSONDecodeError:
        # Corrupted JSON - return empty structure
        return {"topics": []}
    except IOError:
        # File not readable - re-raise as PermissionError for clarity
        raise PermissionError(f"Cannot read index file: {index_path}")


def atomic_write_index(knowledge_dir: Path, data: dict[str, Any]) -> Path:
    """Atomically write index.json using tmp + rename pattern.

    This ensures that readers never see partially written data.
    The write sequence is:
    1. Write to temp file in same directory
    2. fsync to ensure data is on disk
    3. Atomic rename over target file

    Args:
        knowledge_dir: Path to the knowledge directory
        data: Dictionary to serialize to JSON (should have 'topics' key)

    Returns:
        Path to the written index.json file

    Raises:
        PermissionError: If directory is not writable
        OSError: If atomic write fails
    """
    index_path = knowledge_dir / "index.json"

    # Ensure knowledge directory exists
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Serialize to JSON with pretty printing
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

    # Create temp file in same directory for atomic rename
    fd = -1
    tmp_path = None
    try:
        # Create temp file with restrictive permissions (owner read/write only)
        fd, tmp_path_str = tempfile.mkstemp(
            dir=knowledge_dir,
            prefix=".index.json.tmp-",
            suffix=".tmp"
        )
        tmp_path = Path(tmp_path_str)

        try:
            # Write data
            os.write(fd, json_bytes)

            # Ensure data is flushed to disk
            os.fsync(fd)
        finally:
            os.close(fd)
            fd = -1

        # Atomic rename - this is atomic on POSIX systems
        # On Windows, this may fail if destination exists and is open
        tmp_path.replace(index_path)

        # Sync the directory to ensure the rename is persisted
        dir_fd = os.open(knowledge_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        return index_path

    except Exception:
        # Clean up temp file on failure
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def ensure_index_exists(knowledge_dir: Path) -> dict[str, Any]:
    """Ensure index.json exists, creating it if necessary.

    Args:
        knowledge_dir: Path to the knowledge directory

    Returns:
        The index data (existing or newly created)
    """
    data = atomic_read_index(knowledge_dir)
    if data is None:
        data = {"topics": []}
        atomic_write_index(knowledge_dir, data)
    return data


def get_topic_type(topic_id: str) -> str:
    """Derive topic type from topic ID prefix.
    
    Args:
        topic_id: The topic ID (e.g., "seed-add-versioning", "plan-kb-management-cli")
        
    Returns:
        The topic type: "seed", "plan", "spike", "baseline", or "unknown"
    """
    if topic_id.startswith("seed-"):
        return "seed"
    elif topic_id.startswith("plan-"):
        return "plan"
    elif topic_id.startswith("spike-"):
        return "spike"
    elif topic_id.startswith("baseline-"):
        return "baseline"
    else:
        return "unknown"


def is_topic_archived(knowledge_dir: Path, topic_id: str) -> bool:
    """Check if a topic is archived.
    
    A topic is considered archived if it exists in the archive directory.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID to check
        
    Returns:
        True if the topic is archived, False otherwise
    """
    archive_dir = knowledge_dir / "archive" / "topics" / topic_id
    return archive_dir.exists() and archive_dir.is_dir()


def get_topic_docs(
    knowledge_dir: Path,
    topic_id: str,
    archived: bool = False,
) -> dict[str, dict[str, Any]]:
    """Get documentation paths for a topic.
    
    Args:
        knowledge_dir: Path to the knowledge directory
        topic_id: The topic ID
        archived: Whether the topic is archived
        
    Returns:
        Dictionary mapping doc type to {"path": str, "exists": bool}
    """
    docs = {}
    
    if archived:
        topic_dir = knowledge_dir / "archive" / "topics" / topic_id
    else:
        topic_dir = knowledge_dir / "topics" / topic_id
    
    # Standard doc types to check
    doc_types = ["overview", "sources", "plan", "backlog"]
    
    for doc_type in doc_types:
        # Check for .md file
        doc_path = topic_dir / f"{doc_type}.md"
        rel_path = doc_path.relative_to(knowledge_dir) if doc_path.exists() else None
        
        docs[doc_type] = {
            "path": str(rel_path) if rel_path else f"topics/{topic_id}/{doc_type}.md",
            "exists": doc_path.exists(),
        }
    
    return docs
