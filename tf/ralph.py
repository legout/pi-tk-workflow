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
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

# Import new logger
from tf.logger import LogLevel, RalphLogger, RedactionHelper, create_logger

# Import shared utilities
from tf.utils import calculate_timeout_backoff, find_project_root

# Import queue state for progress display
from tf.ralph.queue_state import QueueStateSnapshot, get_queue_state


class ProgressDisplay:
    """Conservative per-ticket progress display for tf ralph (serial mode only).

    Uses stdlib only. Updates at ticket boundaries (start/complete/fail).
    In TTY mode: uses carriage return + clear line for stable progress line.
    In non-TTY mode: plain text output with no control characters.
    """

    def __init__(self, output: TextIO = sys.stderr, is_tty: Optional[bool] = None):
        self.output = output
        self.is_tty = is_tty if is_tty is not None else output.isatty()
        self.current_ticket: Optional[str] = None
        self.completed = 0
        self.failed = 0
        self.total: Union[int, str] = 0
        self._last_line_len = 0

    def start_ticket(
        self,
        ticket_id: str,
        iteration: int,
        total_tickets: Union[int, str],
        queue_state: Optional["QueueStateSnapshot"] = None,
    ) -> None:
        """Called when a ticket starts processing.

        Args:
            ticket_id: The ID of the ticket being processed
            iteration: Current loop iteration (0-indexed)
            total_tickets: Total number of tickets to process (for UI display),
                          can be '?' if ticket listing failed
            queue_state: Optional queue state snapshot with ready/blocked counts
        """
        self.current_ticket = ticket_id
        self.total = total_tickets
        state_str = f" {queue_state}" if queue_state else ""
        self._draw(f"[{iteration + 1}/{total_tickets}]{state_str} Processing {ticket_id}...")

    def complete_ticket(
        self,
        ticket_id: str,
        status: str,
        iteration: int,
        queue_state: Optional["QueueStateSnapshot"] = None,
    ) -> None:
        """Called when a ticket completes (success or failure)."""
        if status == "COMPLETE":
            self.completed += 1
            msg = f"✓ {ticket_id} complete"
        elif status == "FAILED":
            self.failed += 1
            msg = f"✗ {ticket_id} failed"
        else:
            msg = f"? {ticket_id} {status.lower()}"

        self.current_ticket = None
        state_str = f" {queue_state}" if queue_state else ""
        self._draw(f"[{iteration + 1}/{self.total}]{state_str} {msg}", final=True)

    def _draw(self, text: str, final: bool = False) -> None:
        """Draw progress line. In TTY mode, uses carriage return for in-place updates.
        In non-TTY mode, always writes new lines (no control characters).
        """
        # Prefix with timestamp in HH:MM:SS format (per pt-yx8a spec)
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_text = f"{timestamp} {text}"

        if self.is_tty:
            # Clear line and carriage return for stable progress line
            # \x1b[2K clears the entire line
            # \r returns to start of line
            clear_seq = "\x1b[2K\r"
            self.output.write(f"{clear_seq}{full_text}")
            if final:
                self.output.write("\n")
            self.output.flush()
        else:
            # Non-TTY: plain text, no control characters
            if final:
                self.output.write(f"{full_text}\n")
                self.output.flush()
            # In non-TTY mode, we don't show intermediate progress to avoid spam

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
    "sessionDir": "~/.pi/agent/sessions",
    "parallelWorkers": 1,
    "parallelWorktreesDir": ".tf/ralph/worktrees",
    "parallelAllowUntagged": False,
    "componentTagPrefix": "component:",
    "parallelKeepWorktrees": False,
    "parallelAutoMerge": True,
    "logLevel": "normal",  # quiet, normal, verbose, debug
    "captureJson": False,  # Capture Pi JSON mode output for debugging
    "attemptTimeoutMs": 600000,  # 10 minutes default (0 = no timeout). Serial mode only.
    "maxRestarts": 0,  # 0 = no restarts, N = up to N restarts per ticket. Serial mode only.
    # Timeout backoff settings (for linear timeout increase per attempt)
    "timeoutBackoffEnabled": False,  # Enable timeout backoff calculation
    "timeoutBackoffIncrementMs": 150000,  # Default increment per attempt (150s = 2.5min)
    "timeoutBackoffMaxMs": 0,  # Max cap (0 = no cap, use attemptTimeoutMs as base)
    # Execution backend settings (pt-6d99)
    "executionBackend": "dispatch",  # "dispatch" (default) or "subprocess"
    "interactiveShell": {
        "enabled": True,  # Use interactive_shell tool when True
        "mode": "dispatch",  # "dispatch" (headless) or "hands-free" (monitored)
    },
}

# Legacy session directory for backward compatibility detection
LEGACY_SESSION_DIR = ".tf/ralph/sessions"

# Track if legacy warning has been emitted (warn once per run)
_legacy_warning_emitted = False


def usage() -> None:
    # Usage goes to stdout as it's user-facing help text
    print(
        """Ralph (new Python CLI)

Usage:
  tf ralph run [ticket-id] [--dry-run] [--verbose|--debug|--quiet] [--capture-json] [--flags '...']
                            [--progress] [--pi-output MODE] [--pi-output-file PATH]
                            [--dispatch] [--no-interactive-shell]
  tf ralph start [--max-iterations N] [--parallel N] [--no-parallel] [--dry-run] [--verbose|--debug|--quiet]
                 [--capture-json] [--flags '...'] [--progress] [--pi-output MODE] [--pi-output-file PATH]
                 [--dispatch] [--no-interactive-shell]

Execution Backend Options (pt-6d99):
  --dispatch            Use interactive_shell dispatch mode for headless background
                        execution (default). This is the modern execution backend.
  --no-interactive-shell
                        Use legacy subprocess backend (pi -p via subprocess.Popen).
                        This provides backward compatibility for environments where
                        interactive_shell execution is not desired.
  (default)             When neither flag is specified, --dispatch is assumed.

Verbosity Options:
  --verbose         Enable verbose output (INFO + DEBUG events)
  --debug           Alias for --verbose (maximum detail)
  --quiet           Minimal output (errors only)
  (default)         Normal output (INFO events only)

Progress Options:
  --progress, --progressbar
                    Enable progress indicator (serial mode only).
                    Output includes a timestamp prefix (HH:MM:SS format):
                      14:32:05 [1/5] Processing pt-abc123...
                      14:32:15 [1/5] ✓ pt-abc123 complete
                    When used in a TTY, pi output is redirected to a log file
                    to prevent progress bar corruption.

Pi Output Options:
  --pi-output MODE  Control pi subprocess output: inherit (default), file, discard.
                    'inherit' passes output through to terminal.
                    'file' redirects output to .tf/ralph/logs/<ticket>.log.
                    'discard' suppresses pi output entirely.
  --pi-output-file PATH
                    Override the default log file path when --pi-output=file.
                    (default: .tf/ralph/logs/<ticket>.log)

JSON Capture Options:
  --capture-json    Capture Pi JSON mode output to .tf/ralph/logs/<ticket>.jsonl
                    (experimental, for debugging tool execution)

Environment Variables:
  RALPH_LOG_LEVEL           Set log level: quiet, normal, verbose, debug
  RALPH_VERBOSE             Set to 1 to enable verbose mode
  RALPH_DEBUG               Set to 1 to enable debug mode
  RALPH_QUIET               Set to 1 to enable quiet mode
  RALPH_CAPTURE_JSON        Set to 1 to enable JSON mode capture (same as --capture-json)
  RALPH_FORCE_LEGACY_SESSIONS  Set to 1 to force using legacy .tf/ralph/sessions directory
  RALPH_NO_INTERACTIVE_SHELL   Set to 1 to force legacy subprocess backend (same as --no-interactive-shell)

Session Storage:
  By default, Ralph stores session artifacts in Pi's standard session directory:
    ~/.pi/agent/sessions/

  Override via .tf/ralph/config.json:
    {"sessionDir": "/custom/path"}

  Legacy Behavior:
    If .tf/ralph/sessions/ exists and you haven't explicitly configured sessionDir,
    Ralph emits a warning but uses the new default location. To suppress the
    warning or continue using the legacy location, either:
    - Set RALPH_FORCE_LEGACY_SESSIONS=1, or
    - Add {"sessionDir": ".tf/ralph/sessions"} to .tf/ralph/config.json

Configuration (in .tf/ralph/config.json):
  executionBackend      Execution backend to use: "dispatch" (default) or "subprocess".
                        "dispatch" uses interactive_shell tool for headless background execution.
                        "subprocess" uses legacy pi -p via subprocess.Popen.
  interactiveShell      Configuration for interactive shell execution:
                        - enabled: true (default) to use interactive_shell tool
                        - mode: "dispatch" (default) for headless execution
  attemptTimeoutMs      Per-ticket attempt timeout in milliseconds (default: 600000 = 10 min)
                        Set to 0 to disable timeout. Serial mode only.
  maxRestarts           Maximum restarts per ticket on timeout/failure (default: 0)
                        Set to N to allow up to N restarts before marking as failed. Serial mode only.
  timeoutBackoffEnabled Enable linear timeout backoff per restart attempt (default: false)
                        When enabled, each restart gets additional timeout:
                        effective = attemptTimeoutMs + attempt_index * timeoutBackoffIncrementMs
  timeoutBackoffIncrementMs  Additional timeout per restart in ms (default: 150000 = 2.5 min)
  timeoutBackoffMaxMs   Maximum timeout cap in ms (default: 0 = no cap, uses attemptTimeoutMs as base)

Configuration Environment Variables:
  RALPH_ATTEMPT_TIMEOUT_MS     Override attemptTimeoutMs (in milliseconds)
  RALPH_MAX_RESTARTS           Override maxRestarts (integer)
  RALPH_NO_INTERACTIVE_SHELL   Set to 1 to force legacy subprocess backend

Notes:
  - CLI flags take precedence over environment variables
  - Config file settings take precedence over defaults
  - Environment variables take precedence over config file for timeout/restart settings
  - Parallel mode uses git worktrees + component tags (same as legacy).
  - JSON capture is opt-in; JSONL may contain file paths or snippets.
  - --progress is only supported in serial mode (--parallel 1 or default).
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


def list_blocked_tickets() -> List[str]:
    """List tickets blocked by unresolved dependencies."""
    result = run_shell("tk blocked")
    lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
    return [line.split()[0] for line in lines]


_BLOCKED_DEP_SENTINEL = "__unmet_dependency__"


def _refresh_pending_state(
    list_query: str,
    logger: Optional[RalphLogger] = None,
) -> Tuple[set[str], set[str]]:
    """Read ready/blocked ticket IDs once and return them as sets.

    Uses a single refresh point per loop iteration to avoid duplicated full relisting.
    """
    try:
        ready_ids = set(list_ready_tickets(list_query))
    except Exception as exc:
        if logger:
            logger.warn(f"Failed to list ready tickets: {exc}")
        ready_ids = set()

    try:
        blocked_ids = set(list_blocked_tickets())
    except Exception as exc:
        if logger:
            logger.warn(f"Failed to list blocked tickets: {exc}")
        blocked_ids = set()

    return ready_ids, blocked_ids


def _compute_queue_state_snapshot(
    pending_ids: set[str],
    blocked_ids: set[str],
    running_ids: set[str],
    completed_ids: set[str],
) -> QueueStateSnapshot:
    """Build a queue-state snapshot from in-memory ticket ID sets.

    blocked_ids are represented in dep_graph with a sentinel dependency marker so
    get_queue_state() consistently counts them as blocked.
    """
    pending = set(pending_ids)
    running = set(running_ids)
    completed = set(completed_ids)

    # Ensure disjoint state sets before computing queue state.
    pending -= running
    pending -= completed

    blocked_in_pending = pending & set(blocked_ids)
    dep_graph: dict[str, set[str]] = {
        ticket: {_BLOCKED_DEP_SENTINEL} for ticket in blocked_in_pending
    }

    return get_queue_state(
        pending=pending,
        running=running,
        completed=completed,
        dep_graph=dep_graph,
    )


def backlog_empty(completion_check: str) -> bool:
    result = run_shell(completion_check)
    return result.returncode != 0


def ensure_pi() -> bool:
    return shutil.which("pi") is not None


def prompt_exists(project_root: Path, logger: Optional[RalphLogger] = None) -> bool:
    local_prompt = project_root / "prompts" / "tf.md"
    legacy_local_prompt = project_root / ".pi" / "prompts" / "tf.md"
    global_prompt = Path.home() / ".pi/agent/prompts/tf.md"

    if local_prompt.is_file() or legacy_local_prompt.is_file() or global_prompt.is_file():
        return True

    msg = (
        "Missing /tf prompt. Run 'tf init' in the project to install prompts "
        "(or 'tf sync' to re-ensure)."
    )
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


def _run_with_timeout(
    args: List[str],
    cwd: Optional[Path] = None,
    timeout_secs: Optional[float] = None,
    stdout=None,
    stderr=None,
) -> Tuple[int, bool]:
    """Run a subprocess with timeout and safe termination.

    Args:
        args: Command and arguments to run
        cwd: Working directory for the subprocess
        timeout_secs: Timeout in seconds (None = no timeout)
        stdout: File object for stdout redirection
        stderr: File object for stderr redirection

    Returns:
        Tuple of (return_code, timed_out)
        - return_code: Exit code of the process (or -1 if timed out)
        - timed_out: True if the process was terminated due to timeout
    """
    # Start the process
    proc = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
    )

    try:
        # Wait for process to complete with timeout
        return_code = proc.wait(timeout=timeout_secs)
        return return_code, False
    except subprocess.TimeoutExpired:
        # Timeout occurred - need to terminate the process safely
        # Step 1: Try graceful termination (SIGTERM)
        proc.terminate()

        # Step 2: Wait briefly for graceful shutdown
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            # Step 3: Force kill if still running (SIGKILL)
            proc.kill()

        # Step 4: Must wait to reap the process and prevent zombies
        # This ensures we don't leave zombie processes
        proc.wait()

        # Return -1 to indicate timeout distinctly (for restart logic)
        return -1, True


def run_ticket(
    ticket: str,
    workflow: str,
    flags: str,
    dry_run: bool,
    cwd: Optional[Path] = None,
    logger: Optional[RalphLogger] = None,
    mode: str = "serial",
    capture_json: bool = False,
    logs_dir: Optional[Path] = None,
    ticket_title: Optional[str] = None,
    pi_output: str = "inherit",
    pi_output_file: Optional[str] = None,
    timeout_ms: int = 0,
    execution_backend: str = "dispatch",
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

    # Log execution backend (pt-6d99)
    if execution_backend == "dispatch":
        log.info(f"Execution backend: dispatch (interactive_shell) - NOTE: using subprocess fallback until pt-9yjn")
    else:
        log.info(f"Execution backend: subprocess (legacy)")

    # TODO(pt-9yjn): Implement actual dispatch execution via interactive_shell tool
    # For now, both backends use subprocess (this ticket only defines the contract)
    cmd = build_cmd(workflow, ticket, flags)

    # Determine JSON capture path if enabled
    jsonl_path: Optional[Path] = None
    if capture_json and logs_dir:
        jsonl_path = logs_dir / f"{ticket}.jsonl"

    # Determine pi output log path for file mode
    pi_log_path: Optional[Path] = None
    if pi_output == "file":
        if pi_output_file:
            pi_log_path = Path(pi_output_file).expanduser()
        elif logs_dir:
            pi_log_path = logs_dir / f"{ticket}.log"
        else:
            # Fallback to default logs location
            pi_log_path = Path(".tf/ralph/logs") / f"{ticket}.log"

    if dry_run:
        prefix = " (worktree)" if cwd else ""
        json_flag = " --mode json" if capture_json else ""
        output_note = ""
        if pi_output == "file":
            output_note = f" (output to {pi_log_path})"
        elif pi_output == "discard":
            output_note = " (output discarded)"
        log.info(f"Dry run: pi -p{json_flag} \"{cmd}\"{prefix}{output_note}", ticket=ticket)
        return 0

    json_flag_str = " --mode json" if capture_json else ""
    log.info(f"Running: pi -p{json_flag_str} \"{cmd}\"", ticket=ticket)
    args = ["pi", "-p"]
    if capture_json:
        args.append("--mode")
        args.append("json")
    args.append(cmd)

    # Calculate timeout in seconds (0 = no timeout)
    timeout_secs: Optional[float] = timeout_ms / 1000.0 if timeout_ms > 0 else None
    if timeout_secs:
        log.info(f"Attempt timeout: {timeout_ms}ms ({timeout_secs}s)", ticket=ticket)

    # Handle pi output routing
    timed_out = False
    return_code = 0

    if jsonl_path and pi_output == "file":
        # Both JSON capture and pi output to file - combine them
        logs_dir.mkdir(parents=True, exist_ok=True) if logs_dir else None
        pi_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            with open(pi_log_path, "w", encoding="utf-8") as pi_log_file:
                # JSON capture goes to jsonl_file, pi output goes to pi_log_file
                # We need to capture both separately
                return_code, timed_out = _run_with_timeout(
                    args, cwd=cwd, stdout=pi_log_file, stderr=subprocess.STDOUT,
                    timeout_secs=timeout_secs
                )
        log.info(f"JSONL trace written to: {jsonl_path}", ticket=ticket, jsonl_path=str(jsonl_path))
        log.info(f"Pi output written to: {pi_log_path}", ticket=ticket, pi_log_path=str(pi_log_path))
    elif jsonl_path:
        # Only JSON capture
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
            return_code, timed_out = _run_with_timeout(
                args, cwd=cwd, stdout=jsonl_file, stderr=subprocess.STDOUT,
                timeout_secs=timeout_secs
            )
        log.info(f"JSONL trace written to: {jsonl_path}", ticket=ticket, jsonl_path=str(jsonl_path))
    elif pi_output == "file" and pi_log_path:
        # Only pi output to file
        pi_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(pi_log_path, "w", encoding="utf-8") as pi_log_file:
            return_code, timed_out = _run_with_timeout(
                args, cwd=cwd, stdout=pi_log_file, stderr=subprocess.STDOUT,
                timeout_secs=timeout_secs
            )
        log.info(f"Pi output written to: {pi_log_path}", ticket=ticket, pi_log_path=str(pi_log_path))
    elif pi_output == "discard":
        # Discard output
        with open(os.devnull, "w") as devnull:
            return_code, timed_out = _run_with_timeout(
                args, cwd=cwd, stdout=devnull, stderr=subprocess.STDOUT,
                timeout_secs=timeout_secs
            )
    else:
        # inherit - default behavior
        return_code, timed_out = _run_with_timeout(args, cwd=cwd, timeout_secs=timeout_secs)

    # Handle timeout
    if timed_out:
        log.error(f"Attempt timed out after {timeout_ms}ms", ticket=ticket)
        return -1  # Special return code to indicate timeout for restart handling

    # On failure with file capture, print exit code + log path
    if return_code != 0 and pi_output == "file" and pi_log_path:
        log.error(f"Command failed with exit code {return_code}. Output log: {pi_log_path}", ticket=ticket)

    return return_code


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


def resolve_attempt_timeout_ms(config: Dict[str, Any]) -> int:
    """Resolve attempt timeout from env var or config.

    Priority:
    1. RALPH_ATTEMPT_TIMEOUT_MS environment variable
    2. Config file (attemptTimeoutMs)
    3. Default (600000 = 10 minutes)

    Returns:
        Timeout in milliseconds (0 = no timeout)
    """
    # Environment variable takes highest priority
    env_timeout = os.environ.get("RALPH_ATTEMPT_TIMEOUT_MS", "").strip()
    if env_timeout:
        try:
            return int(env_timeout)
        except ValueError:
            pass

    # Config file
    config_timeout = config.get("attemptTimeoutMs", DEFAULTS["attemptTimeoutMs"])
    try:
        return int(config_timeout)
    except (ValueError, TypeError):
        return DEFAULTS["attemptTimeoutMs"]


def resolve_max_restarts(config: Dict[str, Any]) -> int:
    """Resolve max restarts from env var or config.

    Priority:
    1. RALPH_MAX_RESTARTS environment variable
    2. Config file (maxRestarts)
    3. Default (0 = no restarts)

    Returns:
        Maximum number of restarts (0 = no restarts)
    """
    # Environment variable takes highest priority
    env_restarts = os.environ.get("RALPH_MAX_RESTARTS", "").strip()
    if env_restarts:
        try:
            return int(env_restarts)
        except ValueError:
            pass

    # Config file
    config_restarts = config.get("maxRestarts", DEFAULTS["maxRestarts"])
    try:
        return int(config_restarts)
    except (ValueError, TypeError):
        return DEFAULTS["maxRestarts"]


def resolve_timeout_backoff_enabled(config: Dict[str, Any]) -> bool:
    """Resolve timeout backoff enabled from config.

    Returns:
        True if timeout backoff is enabled, False otherwise
    """
    value = config.get("timeoutBackoffEnabled", DEFAULTS["timeoutBackoffEnabled"])
    return parse_bool(value, DEFAULTS["timeoutBackoffEnabled"])


def resolve_timeout_backoff_increment_ms(config: Dict[str, Any]) -> int:
    """Resolve timeout backoff increment from config.

    Returns:
        Increment in milliseconds (default: 150000). Always >= 0.
    """
    value = config.get("timeoutBackoffIncrementMs", DEFAULTS["timeoutBackoffIncrementMs"])
    try:
        result = int(value)
        return max(0, result)
    except (ValueError, TypeError):
        return DEFAULTS["timeoutBackoffIncrementMs"]


def resolve_timeout_backoff_max_ms(config: Dict[str, Any]) -> int:
    """Resolve timeout backoff max cap from config.

    Returns:
        Max timeout in milliseconds (0 = no cap). Always >= 0.
    """
    value = config.get("timeoutBackoffMaxMs", DEFAULTS["timeoutBackoffMaxMs"])
    try:
        result = int(value)
        return max(0, result)
    except (ValueError, TypeError):
        return DEFAULTS["timeoutBackoffMaxMs"]


def calculate_effective_timeout(
    base_timeout_ms: int,
    attempt_index: int,
    backoff_enabled: bool,
    increment_ms: int,
    max_ms: int,
) -> tuple[int, dict[str, Any]]:
    """Calculate effective timeout for a given attempt.

    When backoff is enabled, computes timeout as:
        effective = base_timeout_ms + attempt_index * increment_ms

    When max_ms > 0, caps the result at that value.
    When backoff is disabled, returns base_timeout_ms unchanged.

    Args:
        base_timeout_ms: Base timeout from attemptTimeoutMs config
        attempt_index: Zero-based attempt index (0 = first attempt)
        backoff_enabled: Whether backoff calculation is enabled
        increment_ms: Additional timeout per attempt
        max_ms: Maximum cap (0 = no cap)

    Returns:
        Tuple of (effective_timeout_ms, debug_info) where debug_info contains:
        - base_ms: Base timeout
        - increment_ms: Increment per attempt
        - attempt_index: Current attempt index
        - max_ms: Max cap (0 = no cap)
        - capped: Whether max cap was applied

    Note:
        If configuration is invalid (negative values or max_ms < base_ms),
        falls back to base_timeout_ms to prevent crashes.
    """
    debug_info: dict[str, Any] = {
        "base_ms": base_timeout_ms,
        "increment_ms": increment_ms,
        "attempt_index": attempt_index,
        "max_ms": max_ms if max_ms > 0 else None,
        "capped": False,
    }

    if not backoff_enabled or base_timeout_ms == 0:
        # Backoff disabled or no timeout configured
        return base_timeout_ms, debug_info

    # Validate inputs to prevent crashes from misconfiguration
    if base_timeout_ms < 0:
        return 0, debug_info
    if increment_ms < 0:
        # Invalid increment, fall back to base
        return base_timeout_ms, debug_info
    if max_ms < 0:
        # Invalid max, treat as no cap
        max_ms = 0
        debug_info["max_ms"] = None

    try:
        effective = calculate_timeout_backoff(
            base_ms=base_timeout_ms,
            increment_ms=increment_ms,
            iteration_index=attempt_index,
            max_ms=max_ms if max_ms > 0 else None,
        )
        # Check if capped
        uncapped = base_timeout_ms + attempt_index * increment_ms
        debug_info["capped"] = max_ms > 0 and uncapped > max_ms
        return effective, debug_info
    except ValueError:
        # Configuration error (e.g., max_ms < base_ms after our validation)
        # Fall back to base timeout to prevent crashes
        return base_timeout_ms, debug_info


def resolve_session_dir(
    project_root: Path,
    config: Dict[str, Any],
    raw_config: Optional[Dict[str, Any]] = None,
    logger: Optional[RalphLogger] = None,
) -> Optional[Path]:
    """Resolve session directory with backward compatibility for legacy location.

    Args:
        project_root: Project root path
        config: Merged config (defaults + user config)
        raw_config: Raw user config to detect explicit sessionDir setting
        logger: Optional logger for warnings

    Returns:
        Resolved session directory path or None if disabled
    """
    global _legacy_warning_emitted

    # Check if user explicitly configured sessionDir (not using default)
    raw = raw_config or {}
    user_explicitly_set = "sessionDir" in raw and raw["sessionDir"] not in (None, "")

    # Check for legacy sessions directory
    legacy_path = project_root / LEGACY_SESSION_DIR
    legacy_exists = legacy_path.is_dir() and any(legacy_path.iterdir())

    # Check for force legacy env var
    force_legacy = os.environ.get("RALPH_FORCE_LEGACY_SESSIONS", "").strip().lower() in ("1", "true", "yes")

    # Determine which sessionDir to use
    if force_legacy:
        # User explicitly wants legacy behavior via env var
        path = legacy_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    value = config.get("sessionDir", DEFAULTS["sessionDir"])
    if value in (None, "", False):
        return None

    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = project_root / path

    # Emit warning if legacy exists and user hasn't explicitly configured sessionDir
    if legacy_exists and not user_explicitly_set and not _legacy_warning_emitted:
        _legacy_warning_emitted = True
        warning_msg = (
            f"\n[ralph] Warning: Legacy session directory detected at '{LEGACY_SESSION_DIR}'\n"
            f"[ralph] New default location is: {DEFAULTS['sessionDir']}\n"
            f"[ralph] Options:\n"
            f"[ralph]   1. To use the new location: Move files from {LEGACY_SESSION_DIR} to {DEFAULTS['sessionDir']}\n"
            f"[ralph]   2. To keep using legacy location: Set RALPH_FORCE_LEGACY_SESSIONS=1 or\n"
            f"[ralph]      add '{{\"sessionDir\": \"{LEGACY_SESSION_DIR}\"}}' to .tf/ralph/config.json\n"
        )
        if logger:
            logger.warn(warning_msg.strip())
        else:
            print(warning_msg, file=sys.stderr)

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


def load_retry_state(artifact_dir: Path) -> Optional[Dict[str, Any]]:
    """Load retry state from ticket artifact directory.
    
    Args:
        artifact_dir: Path to ticket artifact directory
        
    Returns:
        Retry state dict if valid, None otherwise
    """
    retry_state_path = artifact_dir / "retry-state.json"
    if not retry_state_path.exists():
        return None
    
    try:
        data = json.loads(retry_state_path.read_text(encoding="utf-8"))
        # Validate schema version and required fields
        if data.get("version") != 1:
            return None
        if not all(k in data for k in ("ticketId", "attempts", "lastAttemptAt", "status")):
            return None
        return data
    except Exception:
        return None


def is_ticket_blocked_by_retries(
    ticket: str,
    knowledge_dir: Path,
    max_retries: int,
    logger: Optional[RalphLogger] = None,
) -> Tuple[bool, int, int]:
    """Check if a ticket has exceeded max retry attempts.
    
    Args:
        ticket: Ticket ID
        knowledge_dir: Base knowledge directory
        max_retries: Maximum allowed retries
        logger: Optional logger
        
    Returns:
        Tuple of (is_blocked, attempt_count, retry_count)
        - is_blocked: True if ticket should be skipped (exceeded max retries)
        - attempt_count: Number of attempts made (0 if no retry state)
        - retry_count: Current retry counter (0 if no retry state)
    """
    artifact_dir = knowledge_dir / "tickets" / ticket
    retry_state = load_retry_state(artifact_dir)
    
    if retry_state is None:
        return False, 0, 0
    
    retry_count = retry_state.get("retryCount", 0)
    attempts = retry_state.get("attempts", [])
    attempt_count = len(attempts)
    
    # Check if max retries exceeded and last attempt was blocked
    # Note: aggregate status is "active" even when blocked, need to check last attempt
    last_attempt_blocked = False
    if attempts:
        last_attempt = attempts[-1]
        last_attempt_blocked = last_attempt.get("status") == "blocked"
    
    is_blocked = retry_count >= max_retries and last_attempt_blocked
    
    if is_blocked and logger:
        logger.warn(
            f"Ticket {ticket} has exceeded max retries ({retry_count}/{max_retries}) - skipping",
            ticket=ticket,
        )
    
    return is_blocked, attempt_count, retry_count


def resolve_max_retries_from_settings(project_root: Path) -> int:
    """Resolve maxRetries from workflow.escalation config.
    
    Args:
        project_root: Project root path
        
    Returns:
        maxRetries value (default: 3)
    """
    settings_path = project_root / ".tf/config/settings.json"
    if not settings_path.exists():
        return 3
    
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
        escalation = workflow.get("escalation", {}) if isinstance(workflow, dict) else {}
        return escalation.get("maxRetries", 3)
    except Exception:
        return 3


def resolve_escalation_enabled(project_root: Path) -> bool:
    """Check if retry escalation is enabled in settings.
    
    Args:
        project_root: Project root path
        
    Returns:
        True if escalation is enabled, False otherwise
    """
    settings_path = project_root / ".tf/config/settings.json"
    if not settings_path.exists():
        return False
    
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
        escalation = workflow.get("escalation", {}) if isinstance(workflow, dict) else {}
        return escalation.get("enabled", False)
    except Exception:
        return False


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
    
    # Load retry state for progress tracking
    retry_state = load_retry_state(artifact_dir)
    attempt_count = len(retry_state.get("attempts", [])) if retry_state else 0
    retry_count = retry_state.get("retryCount", 0) if retry_state else 0

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
        f"  - Attempt: {attempt_count}, Retry Count: {retry_count}",
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

    if lesson_block:
        if not agents_path.exists():
            # Create minimal template if AGENTS.md doesn't exist
            template = (
                "# Ralph Lessons Learned\n\n"
                "## Patterns\n\n"
                "## Gotchas\n"
            )
            agents_path.write_text(template, encoding="utf-8")
        header = f"\n## Lesson from {ticket} ({now})\n\n"
        agents_path.write_text(agents_path.read_text(encoding="utf-8") + header + lesson_block + "\n", encoding="utf-8")


def parse_run_args(
    args: List[str],
) -> Tuple[Optional[str], bool, Optional[str], Optional[LogLevel], bool, bool, str, Optional[str], Optional[str]]:
    """Parse arguments for 'tf ralph run'.

    Returns:
        Tuple of (ticket_override, dry_run, flags_override, log_level, capture_json,
                  progress, pi_output, pi_output_file, execution_backend)
        execution_backend is "dispatch" or "subprocess" or None (use default)
    """
    ticket_override: Optional[str] = None
    dry_run = False
    flags_override: Optional[str] = None
    log_level: Optional[LogLevel] = None
    capture_json = False
    progress = False
    pi_output = "inherit"
    pi_output_file: Optional[str] = None
    execution_backend: Optional[str] = None  # None = use config default
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
        elif arg in ("--progress", "--progressbar"):
            progress = True
            idx += 1
        elif arg == "--pi-output":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --pi-output")
            pi_output = args[idx + 1]
            idx += 2
        elif arg.startswith("--pi-output="):
            pi_output = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--pi-output-file":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --pi-output-file")
            pi_output_file = args[idx + 1]
            idx += 2
        elif arg.startswith("--pi-output-file="):
            pi_output_file = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--flags":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --flags")
            flags_override = args[idx + 1]
            idx += 2
        elif arg.startswith("--flags="):
            flags_override = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--dispatch":
            execution_backend = "dispatch"
            idx += 1
        elif arg == "--no-interactive-shell":
            execution_backend = "subprocess"
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
    return ticket_override, dry_run, flags_override, log_level, capture_json, progress, pi_output, pi_output_file, execution_backend


def parse_start_args(args: List[str]) -> Dict[str, Any]:
    """Parse arguments for 'tf ralph start'."""
    options: Dict[str, Any] = {
        "max_iterations": None,
        "dry_run": False,
        "parallel_override": None,
        "no_parallel": False,
        "flags_override": None,
        "log_level": None,
        "capture_json": False,
        "progress": False,
        "pi_output": "inherit",
        "pi_output_file": None,
        "execution_backend": None,  # None = use config default
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
        elif arg in ("--progress", "--progressbar"):
            options["progress"] = True
            idx += 1
        elif arg == "--pi-output":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --pi-output")
            options["pi_output"] = args[idx + 1]
            idx += 2
        elif arg.startswith("--pi-output="):
            options["pi_output"] = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--pi-output-file":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --pi-output-file")
            options["pi_output_file"] = args[idx + 1]
            idx += 2
        elif arg.startswith("--pi-output-file="):
            options["pi_output_file"] = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--flags":
            if idx + 1 >= len(args):
                raise ValueError("Missing value after --flags")
            options["flags_override"] = args[idx + 1]
            idx += 2
        elif arg.startswith("--flags="):
            options["flags_override"] = arg.split("=", 1)[1]
            idx += 1
        elif arg == "--dispatch":
            options["execution_backend"] = "dispatch"
            idx += 1
        elif arg == "--no-interactive-shell":
            options["execution_backend"] = "subprocess"
            idx += 1
        elif arg in {"--help", "-h"}:
            usage()
            raise SystemExit(0)
        else:
            raise ValueError(f"Unknown option for ralph start: {arg}")
    return options


def _validate_pi_output(pi_output: str) -> bool:
    """Validate --pi-output value."""
    valid = {"inherit", "file", "discard"}
    return pi_output in valid


def ralph_run(args: List[str]) -> int:
    try:
        (
            ticket_override,
            dry_run,
            flags_override,
            cli_log_level,
            cli_capture_json,
            progress,
            pi_output,
            pi_output_file,
            cli_execution_backend,
        ) = parse_run_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # Validate pi_output value
    if not _validate_pi_output(pi_output):
        print(f"Invalid --pi-output value: {pi_output}. Must be one of: inherit, file, discard", file=sys.stderr)
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

    # Resolve execution backend from CLI flag, env var, or config (in that order)
    # Priority: CLI flag > Environment variable > Config > Default
    execution_backend: str = DEFAULTS["executionBackend"]
    if cli_execution_backend:
        execution_backend = cli_execution_backend
    else:
        env_no_interactive = os.environ.get("RALPH_NO_INTERACTIVE_SHELL", "").strip()
        if env_no_interactive in ("1", "true", "yes"):
            execution_backend = "subprocess"
        else:
            config_backend = config.get("executionBackend", DEFAULTS["executionBackend"])
            if isinstance(config_backend, str) and config_backend in ("dispatch", "subprocess"):
                execution_backend = config_backend
            else:
                # Check interactiveShell.enabled config for backward compatibility
                interactive_shell_config = config.get("interactiveShell", {})
                if isinstance(interactive_shell_config, dict):
                    if not parse_bool(interactive_shell_config.get("enabled", True), True):
                        execution_backend = "subprocess"

    # Log execution backend selection (in verbose mode)
    if log_level in (LogLevel.DEBUG, LogLevel.VERBOSE):
        logger.info(f"Execution backend: {execution_backend}")

    ticket_query = sanitize_ticket_query(str(config.get("ticketQuery", DEFAULTS["ticketQuery"])), logger)
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))

    # Add verbosity flag to workflow flags if set
    level_flag = log_level_to_flag(log_level)
    if level_flag:
        workflow_flags = f"{workflow_flags} {level_flag}".strip()

    if flags_override:
        workflow_flags = f"{workflow_flags} {flags_override}".strip()

    # Set up logs directory for JSON capture or pi output file mode
    logs_dir: Optional[Path] = None
    if capture_json or pi_output == "file":
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

    # Resolve timeout and restart configuration
    base_timeout_ms = resolve_attempt_timeout_ms(config)
    max_restarts = resolve_max_restarts(config)
    backoff_enabled = resolve_timeout_backoff_enabled(config)
    backoff_increment_ms = resolve_timeout_backoff_increment_ms(config)
    backoff_max_ms = resolve_timeout_backoff_max_ms(config)

    if dry_run:
        logger.info(f"Dry run config: timeout={base_timeout_ms}ms, max_restarts={max_restarts}", ticket=ticket)

    # Attempt ticket with optional restart loop
    attempt = 0
    max_attempts = max_restarts + 1 if max_restarts > 0 else 1

    while attempt < max_attempts:
        # Calculate effective timeout with optional backoff
        effective_timeout_ms, timeout_debug = calculate_effective_timeout(
            base_timeout_ms=base_timeout_ms,
            attempt_index=attempt,
            backoff_enabled=backoff_enabled,
            increment_ms=backoff_increment_ms,
            max_ms=backoff_max_ms,
        )

        # Build detailed timeout log message
        if backoff_enabled and base_timeout_ms > 0:
            base_info = f"base={timeout_debug['base_ms']}ms"
            increment_info = f"increment={timeout_debug['increment_ms']}ms"
            iteration_info = f"iteration={timeout_debug['attempt_index']}"
            effective_info = f"effective={effective_timeout_ms}ms"
            cap_info = ""
            if timeout_debug.get("max_ms"):
                cap_status = "capped" if timeout_debug.get("capped") else "uncapped"
                cap_info = f" max={timeout_debug['max_ms']}ms ({cap_status})"
            timeout_log = f"Timeout[{iteration_info}]: {base_info} + {increment_info} -> {effective_info}{cap_info}"
        else:
            timeout_log = f"Timeout: {effective_timeout_ms}ms (backoff disabled)"

        if attempt > 0:
            if backoff_enabled:
                logger.info(
                    f"Restart attempt {attempt}/{max_restarts} (timeout: {effective_timeout_ms}ms)",
                    ticket=ticket
                )
            else:
                logger.info(f"Restart attempt {attempt}/{max_restarts}", ticket=ticket)
            # Log detailed timeout info on restart
            logger.info(timeout_log, ticket=ticket)
        elif backoff_enabled and effective_timeout_ms != base_timeout_ms:
            logger.info(f"Initial timeout: {effective_timeout_ms}ms (backoff enabled)", ticket=ticket)
            logger.info(timeout_log, ticket=ticket)
        elif backoff_enabled:
            # First attempt with backoff enabled but no effective change yet
            logger.info(timeout_log, ticket=ticket)

        rc = run_ticket(
            ticket,
            workflow,
            workflow_flags,
            dry_run,
            logger=logger,
            mode="serial",
            capture_json=capture_json,
            logs_dir=logs_dir,
            ticket_title=ticket_title,
            pi_output=pi_output,
            pi_output_file=pi_output_file,
            timeout_ms=effective_timeout_ms,
            execution_backend=execution_backend,
        )

        if dry_run:
            logger.log_ticket_complete(ticket, "DRY_RUN", mode="serial", ticket_title=ticket_title)
            return rc

        # Success case
        if rc == 0:
            logger.log_ticket_complete(ticket, "COMPLETE", mode="serial", ticket_title=ticket_title)
            update_state(ralph_dir, project_root, ticket, "COMPLETE", "")
            return 0

        # Timeout case - check if we should restart
        if rc == -1:  # Timeout
            attempt += 1
            if attempt < max_attempts:
                logger.warn(
                    f"Attempt {attempt} timed out after {effective_timeout_ms}ms, restarting...",
                    ticket=ticket
                )
                continue
            else:
                error_msg = f"Attempt timed out after {attempt} attempt(s) (last timeout: {effective_timeout_ms}ms)"
                logger.log_error_summary(ticket, error_msg, ticket_title=ticket_title)
                update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
                return rc

        # Non-timeout failure - don't restart
        error_msg = f"pi -p failed (exit {rc})"
        logger.log_error_summary(ticket, error_msg, ticket_title=ticket_title)
        update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
        return rc

    return 1


def ralph_start(args: List[str]) -> int:
    try:
        options = parse_start_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # Validate pi_output value
    pi_output = options.get("pi_output", "inherit")
    if not _validate_pi_output(pi_output):
        print(f"Invalid --pi-output value: {pi_output}. Must be one of: inherit, file, discard", file=sys.stderr)
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

    # Resolve execution backend from CLI flag, env var, or config (in that order)
    # Priority: CLI flag > Environment variable > Config > Default
    execution_backend: str = DEFAULTS["executionBackend"]
    cli_execution_backend = options.get("execution_backend")
    if cli_execution_backend:
        execution_backend = cli_execution_backend
    else:
        env_no_interactive = os.environ.get("RALPH_NO_INTERACTIVE_SHELL", "").strip()
        if env_no_interactive in ("1", "true", "yes"):
            execution_backend = "subprocess"
        else:
            config_backend = config.get("executionBackend", DEFAULTS["executionBackend"])
            if isinstance(config_backend, str) and config_backend in ("dispatch", "subprocess"):
                execution_backend = config_backend
            else:
                # Check interactiveShell.enabled config for backward compatibility
                interactive_shell_config = config.get("interactiveShell", {})
                if isinstance(interactive_shell_config, dict):
                    if not parse_bool(interactive_shell_config.get("enabled", True), True):
                        execution_backend = "subprocess"

    # Set up logs directory for JSON capture or pi output file mode
    pi_output = options.get("pi_output", "inherit")
    pi_output_file = options.get("pi_output_file")
    logs_dir: Optional[Path] = None
    if capture_json or pi_output == "file":
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

    # Check if retry escalation is enabled and warn about parallel workers
    escalation_enabled = resolve_escalation_enabled(project_root)
    max_retries = resolve_max_retries_from_settings(project_root)
    if escalation_enabled and use_parallel > 1:
        logger.warn(
            "Retry escalation is enabled but parallelWorkers > 1. "
            "Retry state tracking may have race conditions without ticket-level locking. "
            "Consider setting parallelWorkers=1 or implementing file locking."
        )

    # Safety check: timeout/restart is not supported in parallel mode
    # Per constraint: prefer warn+disable over partial/unsafe behavior
    base_timeout_ms = resolve_attempt_timeout_ms(config)
    max_restarts = resolve_max_restarts(config)
    backoff_enabled = resolve_timeout_backoff_enabled(config)
    backoff_increment_ms = resolve_timeout_backoff_increment_ms(config)
    backoff_max_ms = resolve_timeout_backoff_max_ms(config)

    if use_parallel > 1 and (base_timeout_ms > 0 or max_restarts > 0):
        logger.warn(
            f"Timeout ({base_timeout_ms}ms) and restart ({max_restarts}) settings are not supported in parallel mode. "
            "Falling back to serial mode for safe cleanup semantics."
        )
        use_parallel = 1

    # Validate: --progress is only supported in serial mode
    progress = options.get("progress", False)
    if progress and use_parallel > 1:
        print("Error: --progress is not supported with --parallel > 1 (serial mode only)", file=sys.stderr)
        return 1

    # When --progress is used in TTY mode, force --pi-output=file to prevent progress bar corruption
    if progress and sys.stderr.isatty() and pi_output == "inherit":
        pi_output = "file"
        logs_dir = ralph_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info("--progress in TTY mode: forcing --pi-output=file to prevent progress bar corruption")

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

        if use_parallel <= 1:
            # Initialize progress display if requested
            progress_display = ProgressDisplay(output=sys.stderr) if progress else None

            # Track queue state for ready/blocked counts
            completed_tickets: set[str] = set()
            running_ticket: Optional[str] = None
            list_query = ticket_list_query(ticket_query)
            ready_ids, blocked_ids = _refresh_pending_state(list_query, logger)

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
                    ready_ids, blocked_ids = _refresh_pending_state(list_query, logger)
                    time.sleep(sleep_sec)
                    continue

                # Check if ticket has exceeded max retries (when escalation is enabled)
                if escalation_enabled:
                    knowledge_dir = resolve_knowledge_dir(project_root)
                    is_blocked, attempt_count, retry_count = is_ticket_blocked_by_retries(
                        ticket, knowledge_dir, max_retries, logger
                    )
                    if is_blocked:
                        logger.warn(
                            f"Skipping ticket {ticket}: max retries ({max_retries}) exceeded "
                            f"(retryCount={retry_count})",
                            ticket=ticket,
                        )
                        # Mark as failed in progress and continue
                        if not options["dry_run"]:
                            error_msg = f"Max retries ({max_retries}) exceeded - ticket blocked"
                            update_state(ralph_dir, project_root, ticket, "BLOCKED", error_msg)
                        iteration += 1
                        continue

                # Mark ticket as running and compute queue state from in-memory sets.
                running_ticket = ticket
                pending_ids = ready_ids | blocked_ids
                queue_state = _compute_queue_state_snapshot(
                    pending_ids=pending_ids,
                    blocked_ids=blocked_ids,
                    running_ids={running_ticket},
                    completed_ids=completed_tickets,
                )

                # Update progress display at ticket start
                if progress_display:
                    progress_display.start_ticket(ticket, iteration, str(queue_state.total), queue_state=queue_state)

                # Fetch ticket title only in verbose mode (DEBUG or VERBOSE)
                ticket_title: Optional[str] = None
                if log_level in (LogLevel.DEBUG, LogLevel.VERBOSE):
                    ticket_title = extract_ticket_title(ticket)
                    ticket_logger = logger.with_context(ticket=ticket, ticket_title=ticket_title, iteration=iteration)
                else:
                    ticket_logger = logger.with_context(ticket=ticket, iteration=iteration)
                ticket_logger.log_ticket_start(ticket, mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)

                # Bounded restart loop for timeout handling
                attempt = 0
                max_attempts = max_restarts + 1 if max_restarts > 0 else 1
                ticket_rc = 0

                while attempt < max_attempts:
                    attempt += 1

                    # Calculate effective timeout with optional backoff
                    effective_timeout_ms, timeout_debug = calculate_effective_timeout(
                        base_timeout_ms=base_timeout_ms,
                        attempt_index=attempt - 1,  # 0-indexed for first attempt
                        backoff_enabled=backoff_enabled,
                        increment_ms=backoff_increment_ms,
                        max_ms=backoff_max_ms,
                    )

                    # Build detailed timeout log message
                    if backoff_enabled and base_timeout_ms > 0:
                        base_info = f"base={timeout_debug['base_ms']}ms"
                        increment_info = f"increment={timeout_debug['increment_ms']}ms"
                        iteration_info = f"iteration={timeout_debug['attempt_index']}"
                        effective_info = f"effective={effective_timeout_ms}ms"
                        cap_info = ""
                        if timeout_debug.get("max_ms"):
                            cap_status = "capped" if timeout_debug.get("capped") else "uncapped"
                            cap_info = f" max={timeout_debug['max_ms']}ms ({cap_status})"
                        timeout_log = f"Timeout[{iteration_info}]: {base_info} + {increment_info} -> {effective_info}{cap_info}"
                    else:
                        timeout_log = f"Timeout: {effective_timeout_ms}ms (backoff disabled)"

                    if attempt > 1:
                        if backoff_enabled:
                            ticket_logger.info(
                                f"Restart attempt {attempt - 1}/{max_restarts} for ticket (timeout: {effective_timeout_ms}ms)",
                                ticket=ticket
                            )
                        else:
                            ticket_logger.info(f"Restart attempt {attempt - 1}/{max_restarts} for ticket", ticket=ticket)
                        # Log detailed timeout info on restart
                        ticket_logger.info(timeout_log, ticket=ticket)
                    elif backoff_enabled and effective_timeout_ms != base_timeout_ms:
                        ticket_logger.info(f"Initial timeout: {effective_timeout_ms}ms (backoff enabled)", ticket=ticket)
                        ticket_logger.info(timeout_log, ticket=ticket)
                    elif backoff_enabled:
                        # First attempt with backoff enabled but no effective change yet
                        ticket_logger.info(timeout_log, ticket=ticket)

                    cmd = build_cmd(workflow, ticket, workflow_flags)
                    ticket_rc = run_ticket(
                        ticket,
                        workflow,
                        workflow_flags,
                        options["dry_run"],
                        logger=ticket_logger,
                        mode="serial",
                        capture_json=capture_json,
                        logs_dir=logs_dir,
                        ticket_title=ticket_title,
                        pi_output=pi_output,
                        pi_output_file=pi_output_file,
                        timeout_ms=effective_timeout_ms,
                        execution_backend=execution_backend,
                    )
                    ticket_logger.log_command_executed(ticket, cmd, ticket_rc, mode="serial", iteration=iteration, ticket_title=ticket_title)

                    if options["dry_run"]:
                        break  # Only one attempt in dry-run mode

                    # Success case - exit restart loop
                    if ticket_rc == 0:
                        break

                    # Timeout case (-1) - restart if we haven't exceeded max_restarts
                    if ticket_rc == -1:
                        if attempt < max_attempts:
                            ticket_logger.warn(
                                f"Attempt {attempt} timed out after {effective_timeout_ms}ms, restarting...",
                                ticket=ticket
                            )
                            continue
                        else:
                            # Max restarts exceeded - ticket will be marked FAILED below
                            ticket_logger.error(
                                f"Ticket timed out after {attempt} attempt(s) (last timeout: {effective_timeout_ms}ms)",
                                ticket=ticket
                            )
                            break
                    else:
                        # Non-timeout failure - don't restart
                        break

                # Handle final result after restart loop
                if not options["dry_run"]:
                    # done includes both success and failure per queue-state semantics.
                    completed_tickets.add(ticket)
                    running_ticket = None

                    # Refresh queue state once after completion so blocked->ready transitions
                    # are reflected without duplicate relisting in the same iteration.
                    ready_ids, blocked_ids = _refresh_pending_state(list_query, ticket_logger)
                    pending_ids = ready_ids | blocked_ids
                    queue_state = _compute_queue_state_snapshot(
                        pending_ids=pending_ids,
                        blocked_ids=blocked_ids,
                        running_ids=set(),
                        completed_ids=completed_tickets,
                    )

                    if ticket_rc != 0:
                        if ticket_rc == -1:
                            error_msg = f"Ticket failed after {attempt} attempt(s) due to timeout (last threshold: {effective_timeout_ms}ms)"
                        else:
                            error_msg = f"pi -p failed (exit {ticket_rc})"
                        # Update progress display on failure
                        if progress_display:
                            progress_display.complete_ticket(ticket, "FAILED", iteration, queue_state=queue_state)
                        knowledge_dir = resolve_knowledge_dir(project_root)
                        artifact_path = str(knowledge_dir / "tickets" / ticket)
                        ticket_logger.log_ticket_complete(ticket, "FAILED", mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)
                        ticket_logger.log_error_summary(ticket, error_msg, artifact_path=artifact_path, iteration=iteration, ticket_title=ticket_title)
                        update_state(ralph_dir, project_root, ticket, "FAILED", error_msg)
                        return ticket_rc
                    # Update progress display on success
                    if progress_display:
                        progress_display.complete_ticket(ticket, "COMPLETE", iteration, queue_state=queue_state)
                    ticket_logger.log_ticket_complete(ticket, "COMPLETE", mode="serial", iteration=iteration, ticket_title=ticket_title, queue_state=queue_state)
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
                    json_note = " --mode json" if capture_json else ""
                    ticket_title = ticket_titles.get(ticket) if ticket_titles else None
                    if ticket_title:
                        logger.info(f"Dry run: pi -p{json_note} \"{cmd}\" (worktree)", ticket=ticket, ticket_title=ticket_title)
                    else:
                        logger.info(f"Dry run: pi -p{json_note} \"{cmd}\" (worktree)", ticket=ticket)
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

                # Determine JSON capture path if enabled
                jsonl_path: Optional[Path] = None
                if capture_json and logs_dir:
                    jsonl_path = logs_dir / f"{ticket}.jsonl"

                cmd = build_cmd(workflow, ticket, workflow_flags)
                args = ["pi", "-p"]
                if capture_json:
                    args.append("--mode")
                    args.append("json")
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
