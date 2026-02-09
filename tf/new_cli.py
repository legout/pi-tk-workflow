from __future__ import annotations

import sys
from typing import Optional, List

from tf import (
    agentsmd,
    backlog_ls,
    doctor,
    init,
    login,
    next,
    priority_reclassify,
    ralph,
    setup,
    sync,
    tags_suggest,
    track,
    update,
)
from tf import get_version


def usage() -> None:
    print(
        """Ticketflow (new Python CLI)

Usage:
  tf new agentsmd <subcommand> [path]
  tf new backlog-ls [topic-id-or-path]
  tf new doctor [--project <path>] [--fix]
  tf new init [--project <path>]
  tf new login [--project <path>] [--global]
  tf new next [--project <path>]
  tf new priority-reclassify [--apply] [--ids ...] [--ready] [--status ...] [--tag ...]
  tf new ralph <subcommand> [options]
  tf new setup [--project <path>] [--global]
  tf new sync [--project <path>] [--global]
  tf new tags-classify <text> [--json] [--rationale]
  tf new tags-keywords
  tf new tags-suggest [--ticket <id>] [title] [--json] [--rationale]
  tf new track <path> [--file <files_changed_path>]
  tf new update [--project <path>] [--global]

Commands:
  agentsmd            AGENTS.md management (init/status/validate/fix/update)
  backlog-ls          List backlog status for seed/baseline/plan topics
  doctor              Preflight checks for tk/pi/extensions/checkers
  init                Create .tf project scaffolding
  login               Configure API keys for web search and MCP servers
  next                Print the next ready ticket id
  priority-reclassify Reclassify ticket priorities using P0-P4 rubric
  ralph               Python implementation of Ralph loop (start/run)
  setup               Install Pi/TF assets and extensions
  sync                Sync model frontmatter from config
  tags-classify       Classify text and suggest component tags
  tags-keywords       Show keyword mapping for component classification
  tags-suggest        Suggest component tags for a ticket
  track               Append a file to files_changed.txt
  update              Download latest agents/skills/prompts
"""
    )


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"-h", "--help", "help"}:
        usage()
        return 0

    if argv[0] in {"--version", "-v", "-V"}:
        print(get_version())
        return 0

    command = argv[0]
    rest = argv[1:]

    if command == "agentsmd":
        return agentsmd.main(rest)
    if command == "backlog-ls":
        return backlog_ls.main(rest)
    if command == "doctor":
        return doctor.main(rest)
    if command == "init":
        return init.main(rest)
    if command == "login":
        return login.main(rest)
    if command == "next":
        return next.main(rest)
    if command == "priority-reclassify":
        return priority_reclassify.main(rest)
    if command == "ralph":
        return ralph.main(rest)
    if command == "setup":
        return setup.main(rest)
    if command == "sync":
        return sync.main(rest)
    if command == "tags-classify":
        return tags_suggest.classify_main(rest)
    if command == "tags-keywords":
        return tags_suggest.keywords_main(rest)
    if command == "tags-suggest":
        return tags_suggest.suggest_main(rest)
    if command == "track":
        return track.main(rest)
    if command == "update":
        return update.main(rest)

    print(f"Unknown 'new' subcommand: {command}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
