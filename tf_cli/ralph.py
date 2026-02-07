from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import new logger
from tf_cli.logger import LogLevel, RalphLogger, RedactionHelper, create_logger

# Import shared utilities
from tf_cli.utils import find_project_root

# Module-level cache for ticket titles to avoid repeated tk show calls
_ticket_title_cache: dict[str, Optional[str]] = {}


DEFAULTS: Dict[str, Any] = {
    "maxIterations": 50,
    "maxIterationsPerTicket": 5,
    "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
    "completionCheck": "tk ready | grep -q .",
    "sleepBetweenTickets": 5000,
    "sleepBetweenRetries": 10000,
    "workflow": "/tf",
    "workflowFlags": "--auto",
    "includeKnowledgeBase": True,
    "includePlanningDocs": True,
    "promiseOnComplete": True,
    "lessonsMaxCount": 50,
    "sessionDir": ".tf/ralph/sessions",
    "sessionPerTicket": True,
    "parallelWorkers": 1,
    "parallelWorktreesDir": ".tf/ralph/worktrees",
    "parallelAllowUntagged": False,
    "componentTagPrefix": "component:",
    "parallelKeepWorktrees": False,
    "parallelAutoMerge": True,
    "logLevel": "normal",  # quiet, normal, verbose, debug
    "captureJson": False,  # Capture Pi JSON mode output for debugging
}


def usage() -> None:
    # Usage goes to stdout as it's user-facing help text
    print(
        """Ralph (new Python CLI)

Usage:
  tf ralph run [ticket-id] [--dry-run] [--verbose|--debug|--quiet] [--capture-json] [--flags '...']
  tf ralph start [--max-iterations N] [--parallel N] [--no-parallel] [--dry-run] [--verbose|--debug|--quiet] [--capture-json] [--flags '...']

Verbosity Options:
  --verbose         Enable verbose output (INFO + DEBUG events)
  --debug           Alias for --verbose (maximum detail)
  --quiet           Minimal output (errors only)
  (default)         Normal output (INFO events only)

JSON Capture Options:
  --capture-json    Capture Pi JSON mode output to .tf/ralph/logs/<ticket>.jsonl
                    (experimental, for debugging tool execution)

Environment Variables:
  RALPH_LOG_LEVEL       Set log level: quiet, normal, verbose, debug
  RALPH_VERBOSE         Set to 1 to enable verbose mode
  RALPH_DEBUG           Set to 1 to enable debug mode
  RALPH_QUIET           Set to 1 to enable quiet mode
  RALPH_CAPTURE_JSON    Set to 1 to enable JSON mode capture (same as --capture-json)

Notes:
  - CLI flags take precedence over environment variables
  - Parallel mode uses git worktrees + component tags (same as legacy).
  - JSON capture is opt-in; JSONL may contain file paths or snippets.
"""
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_ralph_dir(project_root: Path, logger: Optional[RalphLogger] = None) -> Optional[Path]:
    ralph_dir = project_root / ".tf/ralph"
    if not ralph_dir.is_dir():
        msg = "Ralph not initialized. Run: tf ralph init"
        if logger:
            logger.error(msg)
        else:
            print(msg, file=sys.stderr)
        return None
    return ralph_dir


def load_config(ralph_dir: Path) -> Dict[str, Any]:
    config_path = ralph_dir / "config.json"
    data: Dict[str, Any] = {}
    if config_path.exists():
        try:
            data = json_load(config_path)
        except Exception:
            data = {}
    config = dict(DEFAULTS)
    if isinstance(data, dict):
        config.update(data)
    return config


def json_load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_shell(cmd: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)


def sanitize_ticket_query(query: str, logger: Optional[RalphLogger] = None) -> str:
    if re.search(r"(^|\s)tf\s+next(\s|$)", query):
        msg = "ticketQuery uses 'tf next' (recursive). Using default tk-ready query."
        if logger:
            logger.warn(msg)
        else:
            print(f"[warn] {msg}", file=sys.stderr)
        return DEFAULTS["ticketQuery"]
    return query


def ticket_list_query(ticket_query: str) -> str:
    if "tk ready" in ticket_query:
        simplified = re.sub(r"\|\s*head -1", "", ticket_query)
        simplified = re.sub(r"\|\s*awk .*", "", simplified)
        return simplified.strip()
    return "tk ready"


def select_ticket(ticket_query: str) -> Optional[str]:
    result = run_shell(ticket_query)
    output = (result.stdout or "").strip()
    if not output:
        return None
    return output.split()[0]


def list_ready_tickets(list_query: str) -> List[str]:
    result = run_shell(list_query)
    lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    return [line.split()[0] for line in lines]


def backlog_empty(completion_check: str) -> bool:
    result = run_shell(completion_check)
    return result.returncode != 0


def ensure_pi() -> bool:
    return shutil.which("pi") is not None


def prompt_exists(project_root: Path, logger: Optional[RalphLogger] = None) -> bool:
    local_prompt = project_root / ".pi/prompts/tf.md"
    global_prompt = Path.home() / ".pi/agent/prompts/tf.md"
    if local_prompt.is_file() or global_prompt.is_file():
        return True
    msg = "Missing /tf prompt. Run 'tf init' in the project to install prompts (or 'tf sync' to re-ensure)."
    if logger:
        logger.error(msg)
    else:
        print(msg, file=sys.stderr)
    return False


def build_cmd(workflow: str, ticket: str, flags: str) -> str:
    cmd = f"{workflow} {ticket}".strip()
    if flags:
        cmd = f"{cmd} {flags}".strip()
    return cmd


def run_ticket(
    ticket: str,
    workflow: str,
    flags: str,
    dry_run: bool,
    session_path: Optional[Path] = None,
    cwd: Optional[Path] = None,
    logger: Optional[RalphLogger] = None,
    mode: str = "serial",
    capture_json: bool = False,
    logs_dir: Optional[Path] = None,
    ticket_title: Optional[str] = None,
) -> int:
    log = logger or create_logger(mode=mode, ticket_id=ticket, ticket_title=ticket_title)
    if not ticket:
        log.error("No ticket specified")
        return 1
    if not ensure_pi():
        log.error("pi not found in PATH; cannot run workflow")
        return 1
    if cwd is None:
        project_root = find_project_root()
        if project_root and not prompt_exists(project_root, log):
            return 1
    else:
        if not prompt_exists(cwd, log):
            return 1

    cmd = build_cmd(workflow, ticket, flags)
    session_flag = f" --session {session_path}" if session_path else ""

    # Determine JSON capture path if enabled
    jsonl_path: Optional[Path] = None
    if capture_json and logs_dir:
        jsonl_path = logs_dir / f"{ticket}.jsonl"

    if dry_run:
        prefix = " (worktree)" if cwd else ""
        json_flag = " --mode json" if capture_json else ""
        log.info(f"Dry run: pi -p{json_flag}{session_flag} \"{cmd}\"{prefix}", ticket=ticket)
        return 0

    json_flag_str = " --mode json" if capture_json else ""
    log.info(f"Running: pi -p{json_flag_str}{session_flag} \"{cmd}\"", ticket=ticket)
    args = ["pi", "-p"]
    if capture_json:
        args.append("--mode")
        args.append("json")
    if session_path:
        args += ["--session", str(session_path)]
    args.append(cmd)

    if jsonl_path:
        # Ensure logs directory exists
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            result = subprocess.run(args, cwd=cwd, stdout=jsonl_file, stderr=subprocess.STDOUT)
        log.info(f"JSONL trace written to: {jsonl_path}", ticket=ticket, jsonl_path=str(jsonl_path))
    else:
        result = subprocess.run(args, cwd=cwd)
    return result.returncode


def extract_components(ticket_id: str, tag_prefix: str, allow_untagged: bool) -> Optional[set]:
    try:
        proc = subprocess.run(["tk", "show", ticket_id], capture_output=True, text=True, check=False)
    except Exception:
        return None
    text = proc.stdout
    in_front = False
    tags: List[str] = []
    for line in text.splitlines():
        if line.strip() == "---":
            in_front = not in_front
            continue
        if in_front and line.startswith("tags:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            tags = [t.strip() for t in value.split(",") if t.strip()]
            break
    components = [t for t in tags if t.startswith(tag_prefix)]
    if not components:
        if not allow_untagged:
            return None
        return {"__untagged__"}
    return set(components)


def select_parallel_tickets(ready: List[str], max_parallel: int, allow_untagged: bool, tag_prefix: str) -> List[str]:
    selected: List[str] = []
    used: set = set()
    for ticket in ready:
        comps = extract_components(ticket, tag_prefix, allow_untagged)
        if comps is None:
            continue
        if comps & used:
            continue
        selected.append(ticket)
        used.update(comps)
        if len(selected) >= max_parallel:
            break
    return selected


def git_repo_root() -> Optional[Path]:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    path = result.stdout.strip()
    return Path(path) if path else None


def parse_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return default


def resolve_log_level(
    cli_level: Optional[LogLevel] = None,
    config: Optional[Dict[str, Any]] = None,
) -> LogLevel:
    """Resolve log level from CLI flags, env vars, and config (in that priority order).

    Priority:
    1. CLI flags (--verbose, --debug, --quiet)
    2. Environment variables (RALPH_LOG_LEVEL, RALPH_VERBOSE, RALPH_DEBUG, RALPH_QUIET)
    3. Config file (logLevel setting)
    4. Default (normal)
    """
    # CLI flags take highest priority
    if cli_level is not None:
        return cli_level

    # Environment variables
    env_level = os.environ.get("RALPH_LOG_LEVEL", "").strip().lower()
    if env_level:
        return LogLevel.from_string(env_level)

    if os.environ.get("RALPH_DEBUG", "").strip() == "1":
        return LogLevel.DEBUG
    if os.environ.get("RALPH_VERBOSE", "").strip() == "1":
        return LogLevel.VERBOSE
    if os.environ.get("RALPH_QUIET", "").strip() == "1":
        return LogLevel.QUIET

    # Config file
    if config is not None:
        config_level = config.get("logLevel", DEFAULTS["logLevel"])
        if isinstance(config_level, str):
            return LogLevel.from_string(config_level)

    # Default
    return LogLevel.NORMAL


def log_level_to_flag(level: LogLevel) -> str:
    """Convert LogLevel to a workflow flag string."""
    mapping = {
        LogLevel.QUIET: "--quiet",
        LogLevel.NORMAL: "",
        LogLevel.VERBOSE: "--verbose",
        LogLevel.DEBUG: "--debug",
    }
    return mapping.get(level, "")


def resolve_session_dir(project_root: Path, config: Dict[str, Any]) -> Optional[Path]:
    value = config.get("sessionDir", DEFAULTS["sessionDir"])
    if value in (None, "", False):
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = project_root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_knowledge_dir(project_root: Path) -> Path:
    settings_path = project_root / ".tf/config/settings.json"
    if settings_path.exists():
        try:
            data = json_load(settings_path)
            workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
            knowledge_dir = workflow.get("knowledgeDir", ".tf/knowledge") if isinstance(workflow, dict) else ".tf/knowledge"
        except Exception:
            knowledge_dir = ".tf/knowledge"
    else:
        knowledge_dir = ".tf/knowledge"

    knowledge_path = Path(str(knowledge_dir)).expanduser()
    if not knowledge_path.is_absolute():
        knowledge_path = project_root / knowledge_path
    return knowledge_path


def lock_acquire(ralph_dir: Path, logger: Optional[RalphLogger] = None) -> bool:
    lock_path = ralph_dir / "lock"
    if lock_path.exists():
        try:
            pid_text = lock_path.read_text(encoding="utf-8").strip().split()[0]
            pid = int(pid_text)
            os.kill(pid, 0)
            msg = f"Ralph loop already running (pid {pid}). Remove {lock_path} if stale."
            if logger:
                logger.error(msg)
            else:
                print(msg, file=sys.stderr)
            return False
        except Exception:
            pass
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(f"{os.getpid()} {utc_now()}\n", encoding="utf-8")
    return True


def lock_release(ralph_dir: Path) -> None:
    lock_path = ralph_dir / "lock"
    if lock_path.exists():
        lock_path.unlink()


def ensure_progress(progress_path: Path) -> None:
    if progress_path.exists():
        return
    now = utc_now()
    template = (
        "# Ralph Loop Progress\n\n"
        "## Current State\n\n"
        f"- Status: RUNNING\n"
        f"- Current ticket: (none)\n"
        f"- Started: {now}\n"
        f"- Last updated: {now}\n\n"
        "## Statistics\n\n"
        "- Tickets completed: 0\n"
        "- Tickets failed: 0\n"
        "- Total iterations: 0\n\n"
        "## History\n\n"
        "<!-- Auto-appended entries below -->\n"
    )
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(template, encoding="utf-8")


def set_state(ralph_dir: Path, state: str) -> None:
    progress_path = ralph_dir / "progress.md"
    if not progress_path.exists():
        return
    now = utc_now()
    text = progress_path.read_text(encoding="utf-8")
    if "## Current State" not in text:
        return
    lines = text.splitlines()
    out: List[str] = []
    for line in lines:
        if line.startswith("- Status:"):
            out.append(f"- Status: {state}")
            continue
        if line.startswith("- Current ticket:"):
            out.append("- Current ticket: (none)")
            continue
        if line.startswith("- Started:"):
            if "(not started)" in line:
                out.append(f"- Started: {now}")
            else:
                out.append(line)
            continue
        if line.startswith("- Last updated:"):
            out.append(f"- Last updated: {now}")
            continue
        out.append(line)
    progress_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def clear_ticket_title_cache() -> None:
    """Clear the ticket title cache.

    Should be called at the start of each Ralph run to ensure fresh data.
    """
    _ticket_title_cache.clear()


def extract_ticket_title(ticket: str, use_cache: bool = True) -> Optional[str]:
    """Extract the ticket title from the ticket file.

    Args:
        ticket: The ticket ID to look up
        use_cache: Whether to use the cache (default: True)

    Returns:
        The ticket title if found, None otherwise (enables graceful omission in logs)
    """
    # Check cache first
    if use_cache and ticket in _ticket_title_cache:
        return _ticket_title_cache[ticket]

    if shutil.which("tk") is None:
        _ticket_title_cache[ticket] = None
        return None
    proc = subprocess.run(["tk", "show", ticket], capture_output=True, text=True)
    if proc.returncode != 0:
        _ticket_title_cache[ticket] = None
        return None
    in_front = False
    title: Optional[str] = None
    for line in proc.stdout.splitlines():
        line_stripped = line.strip()
        # Toggle frontmatter state when we see ---
        if line_stripped == "---":
            # If we've found a title and now entering frontmatter, we can return
            if title is not None:
                result = title if title else None
                _ticket_title_cache[ticket] = result
                return result
            in_front = not in_front
            continue
        # Title appears before frontmatter (H1 heading)
        if not in_front and line.startswith("# "):
            title = line[2:].strip()
    # Return title if found at end of file, else None
    result = title if title else None
    _ticket_title_cache[ticket] = result
    return result


def extract_ticket_titles(tickets: List[str]) -> Dict[str, Optional[str]]:
    """Fetch titles for multiple tickets efficiently.

    Uses the ticket title cache to avoid repeated tk show calls.

    Returns a dict mapping ticket_id -> title (or None if not found).
    """
    titles: Dict[str, Optional[str]] = {}
    for ticket in tickets:
        titles[ticket] = extract_ticket_title(ticket)
    return titles


def extract_summary_and_commit(close_summary: Path, fallback_summary: str) -> Tuple[str, str]:
    summary = fallback_summary
    commit = ""
    if close_summary.exists():
        text = close_summary.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = re.match(r"\s*[-*]?\s*Summary\s*:\s*(.+)$", line)
            if match:
                summary = match.group(1).strip()
                break
        for line in text.splitlines():
            match = re.match(r"\s*[-*]?\s*Commit\s*:\s*(.+)$", line)
            if match:
                commit = match.group(1).strip()
                break
    return summary, commit


def extract_issue_counts(review_path: Path) -> Tuple[int, int, int]:
    crit = maj = minor = 0
    if review_path.exists():
        for line in review_path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*[-*]?\s*Critical\s*:\s*(\d+)", line, re.IGNORECASE)
            if match:
                crit = int(match.group(1))
            match = re.match(r"\s*[-*]?\s*Major\s*:\s*(\d+)", line, re.IGNORECASE)
            if match:
                maj = int(match.group(1))
            match = re.match(r"\s*[-*]?\s*Minor\s*:\s*(\d+)", line, re.IGNORECASE)
            if match:
                minor = int(match.group(1))
    return crit, maj, minor


def extract_lesson_block(close_summary: Path) -> str:
    if not close_summary.exists():
        return ""
    lines = close_summary.read_text(encoding="utf-8").splitlines()
    in_lessons = False
    buffer: List[str] = []
    for line in lines:
        if re.match(r"^#{2,3}\s+Lessons Learned", line):
            in_lessons = True
            continue
        if in_lessons and re.match(r"^#{2,3}\s+", line):
            break
        if in_lessons:
            buffer.append(line.rstrip())
    return "\n".join(buffer).strip()


def update_state(
    ralph_dir: Path,
    project_root: Path,
    ticket: str,
    status: str,
    error_msg: str = "",
    artifact_root: Optional[Path] = None,
) -> None:
    progress_path = ralph_dir / "progress.md"
    agents_path = ralph_dir / "AGENTS.md"

    knowledge_dir = artifact_root if artifact_root is not None else resolve_knowledge_dir(project_root)
    artifact_dir = knowledge_dir / "tickets" / ticket
    close_summary = artifact_dir / "close-summary.md"
    review_path = artifact_dir / "review.md"

    fallback_summary = extract_ticket_title(ticket)
    summary, commit = extract_summary_and_commit(close_summary, fallback_summary)
    crit, maj, minor = extract_issue_counts(review_path)
    lesson_block = extract_lesson_block(close_summary)

    ensure_progress(progress_path)
    now = utc_now()

    lines = progress_path.read_text(encoding="utf-8").splitlines()
    completed = failed = total = 0
    for line in lines:
        match = re.match(r"- Tickets completed: (\d+)", line)
        if match:
            completed = int(match.group(1))
        match = re.match(r"- Tickets failed: (\d+)", line)
        if match:
            failed = int(match.group(1))
        match = re.match(r"- Total iterations: (\d+)", line)
        if match:
            total = int(match.group(1))

    if status == "FAILED":
        failed += 1
    else:
        completed += 1
    total += 1

    out: List[str] = []
    for line in lines:
        if line.startswith("- Status:"):
            out.append("- Status: RUNNING")
            continue
        if line.startswith("- Current ticket:"):
            out.append("- Current ticket: (none)")
            continue
        if line.startswith("- Started:"):
            if "(not started)" in line:
                out.append(f"- Started: {now}")
            else:
                out.append(line)
            continue
        if line.startswith("- Last updated:"):
            out.append(f"- Last updated: {now}")
            continue
        if line.startswith("- Tickets completed:"):
            out.append(f"- Tickets completed: {completed}")
            continue
        if line.startswith("- Tickets failed:"):
            out.append(f"- Tickets failed: {failed}")
            continue
        if line.startswith("- Total iterations:"):
            out.append(f"- Total iterations: {total}")
            continue
        out.append(line)

    entry_lines = [
        f"- {ticket}: {status} ({now})",
        f"  - Summary: {summary}",
        f"  - Issues: Critical({crit})/Major({maj})/Minor({minor})",
        f"  - Status: {status}",
    ]
    if commit:
        entry_lines.append(f"  - Commit: {commit}")
    if error_msg:
        entry_lines.append(f"  - Error: {error_msg}")
    entry = "\n".join(entry_lines)

    marker = "<!-- Auto-appended entries below -->"
    if marker in out:
        idx = out.index(marker)
        out = out[: idx + 1] + [entry] + out[idx + 1 :]
    else:
        out.append(entry)

    progress_path.write_text("\n".join(out) + "\n", encoding="utf-8")

    if lesson_block and agents_path.exists():
        header = f"\n## Lesson from {ticket} ({now})\n\n"
        agents_path.write_text(agents_path.read_text(encoding="utf-8") + header + lesson_block + "\n", encoding="utf-8")


def parse_run_args(args: List[str]) -> Tuple[Optional[str], bool, Optional[str], Optional[LogLevel], bool]:
    ticket_override: Optional[str] = None
    dry_run = False
    flags_override: Optional[str] = None
    log_level: Optional[LogLevel] = None
    capture_json = False
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--dry-run":
            dry_run = True
            idx += 1
        elif arg == "--capture-json":
            capture_json = True
            idx += 1
        elif arg == "--verbose":
            log_level = LogLevel.VERBOSE
            idx += 1
        elif arg == "--debug":
            log_level = LogLevel.DEBUG
            idx += 1
        elif arg == "--quiet":
            log_level = LogLevel.QUIET
            idx += 1
        elif arg == "--flags":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --flags")
            flags_override = args[idx + 1]
            idx += 2
        elif arg.startswith("--flags="):
            flags_override = arg.split("=", 1)[1]
            idx += 1
        elif arg in {"--help", "-h"}:
            usage()
            raise SystemExit(0)
        else:
            if ticket_override is None:
                ticket_override = arg
                idx += 1
            else:
                raise ValueError("Too many arguments for ralph run")
    return ticket_override, dry_run, flags_override, log_level, capture_json


def parse_start_args(args: List[str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {
        "max_iterations": None,
        "dry_run": False,
        "parallel_override": None,
        "no_parallel": False,
        "flags_override": None,
        "log_level": None,
        "capture_json": False,
    }
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--max-iterations":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --max-iterations")
            options["max_iterations"] = int(args[idx + 1])
            idx += 2
        elif arg.startswith("--max-iterations="):
            options["max_iterations"] = int(arg.split("=", 1)[1])
            idx += 1
        elif arg == "--parallel":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --parallel")
            options["parallel_override"] = int(args[idx + 1])
            idx += 2
        elif arg.startswith("--parallel="):
            options["parallel_override"] = int(arg.split("=", 1)[1])
            idx += 1
        elif arg == "--no-parallel":
            options["no_parallel"] = True
            idx += 1
        elif arg == "--dry-run":
            options["dry_run"] = True
            idx += 1
        elif arg == "--verbose":
            options["log_level"] = LogLevel.VERBOSE
            idx += 1
        elif arg == "--debug":
            options["log_level"] = LogLevel.DEBUG
            idx += 1
        elif arg == "--quiet":
            options["log_level"] = LogLevel.QUIET
            idx += 1
        elif arg == "--capture-json":
            options["capture_json"] = True
            idx += 1
        elif arg == "--flags":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --flags")
            options["flags_override"] = args[idx + 1]
            idx += 2
        elif arg.startswith("--flags="):
            options["flags_override"] = arg.split("=", 1)[1]
            idx += 1
        elif arg in {"--help", "-h"}:
            usage()
            raise SystemExit(0)
        else:
            raise ValueError(f"Unknown option for ralph start: {arg}")
    return options


def ralph_run(args: List[str]) -> int:
    try:
        ticket_override, dry_run, flags_override, cli_log_level, cli_capture_json = parse_run_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
        return 1

    # Create logger early for consistent logging
    # We need to load config first to get the default log level
    temp_config = load_config(project_root / ".tf/ralph")
    log_level = resolve_log_level(cli_log_level, temp_config)
    logger = create_logger(level=log_level, mode="serial")

    ralph_dir = ensure_ralph_dir(project_root, logger)
    if not ralph_dir:
        return 1

    # Clear ticket title cache at the start of each run
    clear_ticket_title_cache()

    config = load_config(ralph_dir)

    # Resolve capture_json from CLI flag, env var, or config (in that order)
    capture_json = cli_capture_json
    if not capture_json:
        env_capture = os.environ.get("RALPH_CAPTURE_JSON", "").strip()
        if env_capture in ("1", "true", "yes"):
            capture_json = True
    if not capture_json:
        capture_json = parse_bool(config.get("captureJson", DEFAULTS["captureJson"]), DEFAULTS["captureJson"])

    ticket_query = sanitize_ticket_query(str(config.get("ticketQuery", DEFAULTS["ticketQuery"])), logger)
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))

    # Add verbosity flag to workflow flags if set
    level_flag = log_level_to_flag(log_level)
    if level_flag:
        workflow_flags = f"{workflow_flags} {level_flag}".strip()

    if flags_override:
        workflow_flags = f"{workflow_flags} {flags_override}".strip()

    session_dir = resolve_session_dir(project_root, config)
    session_per_ticket = parse_bool(
        config.get("sessionPerTicket", DEFAULTS["sessionPerTicket"]),
        DEFAULTS["sessionPerTicket"],
    )

    # Set up logs directory for JSON capture
    logs_dir: Optional[Path] = None
    if capture_json:
        logs_dir = ralph_dir / "logs"

    ticket = ticket_override or select_ticket(ticket_query)
    if not ticket:
        logger.error("No ready tickets found")
        return 1

    # Fetch ticket title only in verbose mode (DEBUG or VERBOSE)
    ticket_title: Optional[str] = None
    if log_level in (LogLevel.DEBUG, LogLevel.VERBOSE):
        ticket_title = extract_ticket_title(ticket)
        logger = logger.with_context(ticket=ticket, ticket_title=ticket_title)
    else:
        logger = logger.with_context(ticket=ticket)
    logger.log_ticket_start(ticket, mode="serial", ticket_title=ticket_title)

    session_path = None
    if session_dir:
        if session_per_ticket:
            session_path = session_dir / f"{ticket}.jsonl"
        else:
            session_path = session_dir / f"loop-{utc_now()}.jsonl"

    rc = run_ticket(
        ticket,
        workflow,
        workflow_flags,
        dry_run,
        session_path=session_path,
        logger=logger,
        mode="serial",
        capture_json=capture_json,
        logs_dir=logs_dir,
        ticket_title=ticket_title,
    )
    if dry_run:
        logger.log_ticket_complete(ticket, "DRY_RUN", mode="serial", ticket_title=ticket_title)
        return rc

    if rc != 0:
        error_msg = f"pi -p failed (exit {rc})"
        logger.log_error_summary(ticket, error_msg, ticket_title=ticket_title)
        update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
        return rc

    logger.log_ticket_complete(ticket, "COMPLETE", mode="serial", ticket_title=ticket_title)
    update_state(ralph_dir, project_root, ticket, "COMPLETE", "")
    return 0


def ralph_start(args: List[str]) -> int:
    try:
        options = parse_start_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
        return 1

    # Create logger early for consistent logging
    temp_config = load_config(project_root / ".tf/ralph")
    log_level = resolve_log_level(options.get("log_level"), temp_config)
    logger = create_logger(level=log_level, mode="serial")

    ralph_dir = ensure_ralph_dir(project_root, logger)
    if not ralph_dir:
        return 1

    # Clear ticket title cache at the start of each run
    clear_ticket_title_cache()

    config = load_config(ralph_dir)

    # Resolve capture_json from CLI flag, env var, or config (in that order)
    capture_json = options.get("capture_json", False)
    if not capture_json:
        env_capture = os.environ.get("RALPH_CAPTURE_JSON", "").strip()
        if env_capture in ("1", "true", "yes"):
            capture_json = True
    if not capture_json:
        capture_json = parse_bool(config.get("captureJson", DEFAULTS["captureJson"]), DEFAULTS["captureJson"])

    # Set up logs directory for JSON capture
    logs_dir: Optional[Path] = None
    if capture_json:
        logs_dir = ralph_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

    max_iterations = options["max_iterations"] or int(config.get("maxIterations", DEFAULTS["maxIterations"]))
    sleep_between = int(config.get("sleepBetweenTickets", DEFAULTS["sleepBetweenTickets"]))
    sleep_retries = int(config.get("sleepBetweenRetries", DEFAULTS["sleepBetweenRetries"]))
    ticket_query = sanitize_ticket_query(str(config.get("ticketQuery", DEFAULTS["ticketQuery"])), logger)
    completion_check = str(config.get("completionCheck", DEFAULTS["completionCheck"]))
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))
    promise_on_complete = parse_bool(
        config.get("promiseOnComplete", DEFAULTS["promiseOnComplete"]),
        DEFAULTS["promiseOnComplete"],
    )

    # Add verbosity flag to workflow flags if set
    level_flag = log_level_to_flag(log_level)
    if level_flag:
        workflow_flags = f"{workflow_flags} {level_flag}".strip()

    if options["flags_override"]:
        workflow_flags = f"{workflow_flags} {options['flags_override']}".strip()

    session_dir = resolve_session_dir(project_root, config)
    session_per_ticket = parse_bool(
        config.get("sessionPerTicket", DEFAULTS["sessionPerTicket"]),
        DEFAULTS["sessionPerTicket"],
    )

    parallel_workers = int(config.get("parallelWorkers", DEFAULTS["parallelWorkers"]))
    if options["parallel_override"] is not None:
        parallel_workers = options["parallel_override"]
    if options["no_parallel"]:
        parallel_workers = 1

    use_parallel = parallel_workers
    repo_root = None
    if use_parallel > 1:
        repo_root = git_repo_root()
        if repo_root is None:
            logger.warn("git repo not found; falling back to serial")
            use_parallel = 1

    if use_parallel > 1 and session_dir and not session_per_ticket:
        logger.warn("sessionPerTicket=false with parallel execution; using per-ticket sessions")
        session_per_ticket = True

    mode = "parallel" if use_parallel > 1 else "serial"
    logger = logger.with_context(mode=mode)
    logger.log_loop_start(mode=mode, max_iterations=max_iterations, parallel_workers=use_parallel if use_parallel > 1 else None)

    lock_acquired = False
    if not options["dry_run"]:
        if not lock_acquire(ralph_dir, logger):
            return 1
        lock_acquired = True
        set_state(ralph_dir, "RUNNING")

    try:
        iteration = 0

        loop_session_path: Optional[Path] = None
        if session_dir and not session_per_ticket:
            loop_session_path = session_dir / f"loop-{utc_now()}.jsonl"

        if use_parallel <= 1:
            while iteration < max_iterations:
                if backlog_empty(completion_check):
                    logger.log_loop_complete(reason="backlog_empty", iterations_completed=iteration, mode=mode)
                    if not options["dry_run"]:
                        set_state(ralph_dir, "COMPLETE")
                    if promise_on_complete:
                        print("<promise>COMPLETE</promise>")
                    return 0

                ticket = select_ticket(ticket_query)
                if not ticket:
                    sleep_sec = sleep_retries / 1000
                    logger.log_no_ticket_selected(sleep_seconds=sleep_sec, reason="no_ready_tickets", mode=mode, iteration=iteration)
                    time.sleep(sleep_sec)
                    continue

                # Fetch ticket title only in verbose mode (DEBUG or VERBOSE)
                ticket_title: Optional[str] = None
                if log_level in (LogLevel.DEBUG, LogLevel.VERBOSE):
                    ticket_title = extract_ticket_title(ticket)
                    ticket_logger = logger.with_context(ticket=ticket, ticket_title=ticket_title, iteration=iteration)
                else:
                    ticket_logger = logger.with_context(ticket=ticket, iteration=iteration)
                ticket_logger.log_ticket_start(ticket, mode="serial", iteration=iteration, ticket_title=ticket_title)

                session_path = None
                if session_dir:
                    if session_per_ticket:
                        session_path = session_dir / f"{ticket}.jsonl"
                    else:
                        session_path = loop_session_path

                cmd = build_cmd(workflow, ticket, workflow_flags)
                rc = run_ticket(
                    ticket,
                    workflow,
                    workflow_flags,
                    options["dry_run"],
                    session_path=session_path,
                    logger=ticket_logger,
                    mode="serial",
                    capture_json=capture_json,
                    logs_dir=logs_dir,
                    ticket_title=ticket_title,
                )
                ticket_logger.log_command_executed(ticket, cmd, rc, mode="serial", iteration=iteration, ticket_title=ticket_title)
                if not options["dry_run"]:
                    if rc != 0:
                        error_msg = f"pi -p failed (exit {rc})"
                        knowledge_dir = resolve_knowledge_dir(project_root)
                        artifact_path = str(knowledge_dir / "tickets" / ticket)
                        ticket_logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration, ticket_title=ticket_title)
                        update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
                        return rc
                    ticket_logger.log_ticket_complete(ticket, "COMPLETE", mode="serial", iteration=iteration, ticket_title=ticket_title)
                    update_state(ralph_dir, project_root, ticket, "COMPLETE", "")

                iteration += 1
                time.sleep(sleep_between / 1000)

            logger.log_loop_complete(reason="max_iterations_reached", iterations_completed=iteration, mode=mode)
            if not options["dry_run"]:
                set_state(ralph_dir, "COMPLETE")
            if promise_on_complete:
                print("<promise>COMPLETE</promise>")
            return 0

        worktrees_dir = Path(str(config.get("parallelWorktreesDir", DEFAULTS["parallelWorktreesDir"])))
        if not worktrees_dir.is_absolute():
            worktrees_dir = repo_root / worktrees_dir
        allow_untagged = parse_bool(
            config.get("parallelAllowUntagged", DEFAULTS["parallelAllowUntagged"]),
            DEFAULTS["parallelAllowUntagged"],
        )
        tag_prefix = str(config.get("componentTagPrefix", DEFAULTS["componentTagPrefix"]))
        keep_worktrees = parse_bool(
            config.get("parallelKeepWorktrees", DEFAULTS["parallelKeepWorktrees"]),
            DEFAULTS["parallelKeepWorktrees"],
        )

        worktrees_dir.mkdir(parents=True, exist_ok=True)
        list_query = ticket_list_query(ticket_query)

        if not ensure_pi() or not prompt_exists(project_root, logger):
            return 1

        while iteration < max_iterations:
            if backlog_empty(completion_check):
                logger.log_loop_complete(reason="backlog_empty", iterations_completed=iteration, mode=mode)
                if not options["dry_run"]:
                    set_state(ralph_dir, "COMPLETE")
                if promise_on_complete:
                    print("<promise>COMPLETE</promise>")
                return 0

            remaining = max_iterations - iteration
            batch_size = min(use_parallel, remaining)
            ready = list_ready_tickets(list_query)
            selected = select_parallel_tickets(ready, batch_size, allow_untagged, tag_prefix)

            used_fallback = False
            if not selected:
                fallback_ticket = select_ticket(ticket_query)
                if not fallback_ticket:
                    sleep_sec = sleep_retries / 1000
                    logger.log_no_ticket_selected(sleep_seconds=sleep_sec, reason="no_ready_tickets", mode=mode, iteration=iteration)
                    time.sleep(sleep_sec)
                    continue
                selected = [fallback_ticket]
                used_fallback = True

            # Build component tags map for logging
            component_tags: Dict[str, List[str]] = {}
            for ticket in selected:
                comps = extract_components(ticket, tag_prefix, allow_untagged)
                if comps:
                    # Remove __untagged__ marker for display, show as empty/untagged
                    display_comps = [c for c in comps if c != "__untagged__"]
                    component_tags[ticket] = display_comps
                else:
                    component_tags[ticket] = []

            # Fetch ticket titles only in verbose mode (DEBUG or VERBOSE)
            ticket_titles: Dict[str, Optional[str]] = {}
            if log_level in (LogLevel.DEBUG, LogLevel.VERBOSE):
                ticket_titles = extract_ticket_titles(selected)

            reason = "fallback" if used_fallback else "component_diversity"
            logger.log_batch_selected(selected, component_tags, reason=reason, mode=mode, iteration=iteration)

            if options["dry_run"]:
                for ticket in selected:
                    cmd = build_cmd(workflow, ticket, workflow_flags)
                    session_note = f" --session {session_dir / (ticket + '.jsonl')}" if session_dir else ""
                    json_note = " --mode json" if capture_json else ""
                    ticket_title = ticket_titles.get(ticket) if ticket_titles else None
                    if ticket_title:
                        logger.info(f"Dry run: pi -p{json_note}{session_note} \"{cmd}\" (worktree)", ticket=ticket, ticket_title=ticket_title)
                    else:
                        logger.info(f"Dry run: pi -p{json_note}{session_note} \"{cmd}\" (worktree)", ticket=ticket)
                iteration += len(selected)
                time.sleep(sleep_between / 1000)
                continue

            processes: List[Tuple[subprocess.Popen, str, Path, Optional[Any]]] = []
            for ticket in selected:
                worktree_path = worktrees_dir / ticket
                # Get ticket title for verbose logging (only if fetched)
                ticket_title = ticket_titles.get(ticket) if ticket_titles else None
                # Remove any existing worktree first
                remove = subprocess.run(["git", "-C", str(repo_root), "worktree", "remove", "-f", str(worktree_path)], capture_output=True)
                if remove.returncode == 0:
                    if ticket_title:
                        logger.log_worktree_operation(
                            ticket, "remove", str(worktree_path), success=True, mode=mode, iteration=iteration, ticket_title=ticket_title
                        )
                    else:
                        logger.log_worktree_operation(
                            ticket, "remove", str(worktree_path), success=True, mode=mode, iteration=iteration
                        )
                # Add new worktree
                add = subprocess.run(
                    ["git", "-C", str(repo_root), "worktree", "add", "-B", f"ralph/{ticket}", str(worktree_path), "HEAD"],
                    capture_output=True,
                )
                if add.returncode != 0:
                    error_msg = add.stderr.decode("utf-8", errors="replace") if add.stderr else "worktree add failed"
                    if ticket_title:
                        logger.log_worktree_operation(
                            ticket, "add", str(worktree_path), success=False, error=error_msg, mode=mode, iteration=iteration, ticket_title=ticket_title
                        )
                        logger.log_error_summary(ticket, f"worktree add failed: {error_msg}", iteration=iteration, ticket_title=ticket_title)
                    else:
                        logger.log_worktree_operation(
                            ticket, "add", str(worktree_path), success=False, error=error_msg, mode=mode, iteration=iteration
                        )
                        logger.log_error_summary(ticket, f"worktree add failed: {error_msg}", iteration=iteration)
                    update_state(ralph_dir, project_root, ticket, "FAILED", f"worktree add failed: {error_msg}", repo_root / ".tf/knowledge")
                    continue
                if ticket_title:
                    logger.log_worktree_operation(
                        ticket, "add", str(worktree_path), success=True, mode=mode, iteration=iteration, ticket_title=ticket_title
                    )
                else:
                    logger.log_worktree_operation(
                        ticket, "add", str(worktree_path), success=True, mode=mode, iteration=iteration
                    )

                session_path = None
                if session_dir:
                    session_path = session_dir / f"{ticket}.jsonl"

                # Determine JSON capture path if enabled
                jsonl_path: Optional[Path] = None
                if capture_json and logs_dir:
                    jsonl_path = logs_dir / f"{ticket}.jsonl"

                cmd = build_cmd(workflow, ticket, workflow_flags)
                args = ["pi", "-p"]
                if capture_json:
                    args.append("--mode")
                    args.append("json")
                if session_path:
                    args += ["--session", str(session_path)]
                args.append(cmd)

                if jsonl_path:
                    # Ensure logs directory exists (per-worktree path for parallel mode)
                    worktree_logs = worktree_path / ".tf/ralph/logs"
                    worktree_logs.mkdir(parents=True, exist_ok=True)
                    jsonl_file = open(worktree_logs / f"{ticket}.jsonl", "w", encoding="utf-8")
                    proc = subprocess.Popen(args, cwd=worktree_path, stdout=jsonl_file, stderr=subprocess.STDOUT)
                    processes.append((proc, ticket, worktree_path, jsonl_file))
                else:
                    proc = subprocess.Popen(args, cwd=worktree_path)
                    processes.append((proc, ticket, worktree_path, None))

            for proc, ticket, worktree_path, jsonl_file in processes:
                rc = proc.wait()
                # Get ticket title for verbose logging (only if fetched)
                ticket_title = ticket_titles.get(ticket) if ticket_titles else None
                if jsonl_file is not None:
                    jsonl_file.close()
                    # Log where the JSONL was written (relative to worktree)
                    jsonl_path = worktree_path / ".tf/ralph/logs" / f"{ticket}.jsonl"
                    if ticket_title:
                        logger.info(f"JSONL trace written to: {jsonl_path}", ticket=ticket, ticket_title=ticket_title, jsonl_path=str(jsonl_path), mode="parallel")
                    else:
                        logger.info(f"JSONL trace written to: {jsonl_path}", ticket=ticket, jsonl_path=str(jsonl_path), mode="parallel")
                cmd = build_cmd(workflow, ticket, workflow_flags)
                if ticket_title:
                    logger.log_command_executed(ticket, cmd, rc, mode="parallel", iteration=iteration, ticket_title=ticket_title)
                else:
                    logger.log_command_executed(ticket, cmd, rc, mode="parallel", iteration=iteration)
                if rc != 0:
                    error_msg = f"pi -p failed (exit {rc})"
                    artifact_path = str(worktree_path / ".tf/knowledge" / "tickets" / ticket)
                    if ticket_title:
                        logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration, ticket_title=ticket_title)
                    else:
                        logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration)
                    update_state(
                        ralph_dir,
                        project_root,
                        ticket,
                        "FAILED",
                        error_msg,
                        worktree_path / ".tf/knowledge",
                    )
                    return rc

                if ticket_title:
                    logger.log_ticket_complete(ticket, "COMPLETE", mode="parallel", iteration=iteration, ticket_title=ticket_title)
                else:
                    logger.log_ticket_complete(ticket, "COMPLETE", mode="parallel", iteration=iteration)
                artifact_root = worktree_path / ".tf/knowledge"
                update_state(ralph_dir, project_root, ticket, "COMPLETE", "", artifact_root)

                if not keep_worktrees:
                    remove = subprocess.run(
                        ["git", "-C", str(repo_root), "worktree", "remove", "-f", str(worktree_path)],
                        capture_output=True,
                    )
                    if remove.returncode == 0:
                        if ticket_title:
                            logger.log_worktree_operation(
                                ticket, "remove", str(worktree_path), success=True, mode=mode, iteration=iteration, ticket_title=ticket_title
                            )
                        else:
                            logger.log_worktree_operation(
                                ticket, "remove", str(worktree_path), success=True, mode=mode, iteration=iteration
                            )
                    else:
                        error_msg = remove.stderr.decode("utf-8", errors="replace") if remove.stderr else "unknown error"
                        if ticket_title:
                            logger.log_worktree_operation(
                                ticket, "remove", str(worktree_path), success=False, error=error_msg, mode=mode, iteration=iteration, ticket_title=ticket_title
                            )
                        else:
                            logger.log_worktree_operation(
                                ticket, "remove", str(worktree_path), success=False, error=error_msg, mode=mode, iteration=iteration
                            )
                        shutil.rmtree(worktree_path, ignore_errors=True)

            iteration += len(selected)
            time.sleep(sleep_between / 1000)

        logger.log_loop_complete(reason="max_iterations_reached", iterations_completed=iteration, mode=mode)
        if not options["dry_run"]:
            set_state(ralph_dir, "COMPLETE")
        if promise_on_complete:
            print("<promise>COMPLETE</promise>")
        return 0
    finally:
        if lock_acquired:
            lock_release(ralph_dir)


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in {"help", "--help", "-h"}:
        usage()
        return 0

    subcmd = argv[0]
    rest = argv[1:]

    if subcmd == "run":
        return ralph_run(rest)
    if subcmd == "start":
        return ralph_start(rest)

    print(f"Unknown ralph subcommand: {subcmd}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
