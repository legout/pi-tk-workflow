import sys
from typing import Optional, List

from . import (
    agentsmd_new,
    backlog_ls_new,
    doctor_new,
    init_new,
    login_new,
    next_new,
    ralph_new,
    setup_new,
    sync_new,
    tags_suggest_new,
    track_new,
    update_new,
)
from .version import get_version


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
  tf new ralph <subcommand> [options]
  tf new setup [--project <path>] [--global]
  tf new sync [--project <path>] [--global]
  tf new tags-classify <text> [--json] [--rationale]
  tf new tags-keywords
  tf new tags-suggest [--ticket <id>] [title] [--json] [--rationale]
  tf new track <path> [--file <files_changed_path>]
  tf new update [--project <path>] [--global]

Commands:
  agentsmd       AGENTS.md management (init/status/validate/fix/update)
  backlog-ls     List backlog status for seed/baseline/plan topics
  doctor         Preflight checks for tk/pi/extensions/checkers
  init           Create .tf project scaffolding
  login          Configure API keys for web search and MCP servers
  next           Print the next ready ticket id
  ralph          Python implementation of Ralph loop (start/run)
  setup          Install Pi/TF assets and extensions
  sync           Sync model frontmatter from config
  tags-classify  Classify text and suggest component tags
  tags-keywords  Show keyword mapping for component classification
  tags-suggest   Suggest component tags for a ticket
  track          Append a file to files_changed.txt
  update         Download latest agents/skills/prompts
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
        return agentsmd_new.main(rest)
    if command == "backlog-ls":
        return backlog_ls_new.main(rest)
    if command == "doctor":
        return doctor_new.main(rest)
    if command == "init":
        return init_new.main(rest)
    if command == "login":
        return login_new.main(rest)
    if command == "next":
        return next_new.main(rest)
    if command == "ralph":
        return ralph_new.main(rest)
    if command == "setup":
        return setup_new.main(rest)
    if command == "sync":
        return sync_new.main(rest)
    if command == "tags-classify":
        return tags_suggest_new.classify_main(rest)
    if command == "tags-keywords":
        return tags_suggest_new.keywords_main(rest)
    if command == "tags-suggest":
        return tags_suggest_new.suggest_main(rest)
    if command == "track":
        return track_new.main(rest)
    if command == "update":
        return update_new.main(rest)

    print(f"Unknown 'new' subcommand: {command}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
