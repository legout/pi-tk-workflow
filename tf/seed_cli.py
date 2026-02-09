"""Seed session management CLI commands.

Implements the /tf-seed command with session UX flags:
- --active: Print current active session
- --sessions [seed-id]: List archived sessions
- --resume <id>: Resume an archived session
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from tf.session_store import (
    get_active_session_info,
    list_archived_sessions,
    load_archived_session,
    resume_session,
    find_latest_session_for_seed,
    parse_session_id,
)


def cmd_active(knowledge_dir: Optional[Path] = None) -> int:
    """Print the current active session or 'none'."""
    info = get_active_session_info(knowledge_dir)
    if info is None:
        print("none")
        return 0
    
    session_id = info.get("session_id", "unknown")
    root_seed = info.get("root_seed", "unknown")
    state = info.get("state", "unknown")
    spike_count = info.get("spike_count", 0)
    has_plan = info.get("has_plan", False)
    has_backlog = info.get("has_backlog", False)
    ticket_count = info.get("ticket_count", 0)
    
    # Format: session_id (root_seed) - state [spikes: N, plan: Y/N, backlog: Y/N (N tickets)]
    parts = [f"{session_id} (root: {root_seed}) - {state}"]
    
    details = []
    details.append(f"spikes: {spike_count}")
    details.append(f"plan: {'yes' if has_plan else 'no'}")
    details.append(f"backlog: {'yes' if has_backlog else 'no'}")
    if has_backlog:
        details.append(f"tickets: {ticket_count}")
    
    parts.append(f"[{', '.join(details)}]")
    print(" ".join(parts))
    return 0


def cmd_sessions(seed_id: Optional[str] = None, knowledge_dir: Optional[Path] = None) -> int:
    """List archived sessions, optionally filtered by seed-id."""
    sessions = list_archived_sessions(seed_id, knowledge_dir)
    
    if not sessions:
        if seed_id:
            print(f"No archived sessions found for seed: {seed_id}")
        else:
            print("No archived sessions found")
        return 0
    
    # Header
    if seed_id:
        print(f"Archived sessions for {seed_id}:")
    else:
        print("All archived sessions:")
    print()
    
    # List sessions
    for session in sessions:
        session_id = session.get("session_id", "unknown")
        root_seed = session.get("root_seed", "unknown")
        state = session.get("state", "archived")
        created = session.get("created", "unknown")
        updated = session.get("updated", "unknown")
        
        spikes = session.get("spikes", [])
        plan = session.get("plan")
        backlog = session.get("backlog")
        
        # Count items
        spike_count = len(spikes)
        has_plan = "yes" if plan else "no"
        has_backlog = "yes" if backlog else "no"
        ticket_count = len(backlog.get("tickets", [])) if backlog else 0
        
        print(f"  {session_id}")
        print(f"    root: {root_seed}")
        print(f"    created: {created}")
        print(f"    updated: {updated}")
        print(f"    state: {state}")
        print(f"    progress: {spike_count} spikes, plan: {has_plan}, backlog: {has_backlog} ({ticket_count} tickets)")
        print()
    
    print(f"Total: {len(sessions)} session(s)")
    return 0


def cmd_resume(session_or_seed_id: str, knowledge_dir: Optional[Path] = None) -> int:
    """Resume an archived session by seed-id or session-id."""
    # First try to load as a session ID directly
    session = load_archived_session(session_or_seed_id, knowledge_dir)
    
    if session is None:
        # Try to find the latest session for this seed
        session = find_latest_session_for_seed(session_or_seed_id, knowledge_dir)
        
        if session is None:
            print(f"Error: No session found for '{session_or_seed_id}'", file=sys.stderr)
            print("Use 'tf seed --sessions' to list available sessions.", file=sys.stderr)
            return 1
        
        # Use the session ID from the found session
        session_id = session.get("session_id")
        print(f"Found latest session for {session_or_seed_id}: {session_id}")
    else:
        session_id = session_or_seed_id
    
    # Resume the session
    resumed = resume_session(session_id, knowledge_dir)
    
    if resumed is None:
        print(f"Error: Failed to resume session '{session_id}'", file=sys.stderr)
        return 1
    
    resumed_id = resumed.get("session_id", "unknown")
    root_seed = resumed.get("root_seed", "unknown")
    
    print(f"[tf] Resumed planning session: {resumed_id} (root: {root_seed})")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for seed CLI."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        prog="tf seed",
        description="Manage planning sessions for tf-seed",
    )
    
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=None,
        help="Path to knowledge directory (default: .tf/knowledge)",
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--active",
        action="store_true",
        help="Print the current active session or 'none'",
    )
    group.add_argument(
        "--sessions",
        nargs="?",
        const="",
        metavar="SEED_ID",
        help="List archived sessions, optionally filtered by seed-id",
    )
    group.add_argument(
        "--resume",
        metavar="ID",
        help="Resume an archived session by seed-id or session-id",
    )
    
    args = parser.parse_args(argv)
    
    # Default to --active if no flags provided
    if not args.active and args.sessions is None and not args.resume:
        args.active = True
    
    if args.active:
        return cmd_active(args.knowledge_dir)
    elif args.sessions is not None:
        seed_id = args.sessions if args.sessions else None
        return cmd_sessions(seed_id, args.knowledge_dir)
    elif args.resume:
        return cmd_resume(args.resume, args.knowledge_dir)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
