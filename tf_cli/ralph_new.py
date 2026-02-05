from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
}


def usage() -> None:
    print(
        """Ralph (new Python CLI)

Usage:
  tf new ralph run [ticket-id] [--dry-run] [--flags '...']
  tf new ralph start [--max-iterations N] [--parallel N] [--no-parallel] [--dry-run] [--flags '...']

Notes:
  - Parallel mode uses git worktrees + component tags (same as legacy).
"""
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_project_root() -> Optional[Path]:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return None


def ensure_ralph_dir(project_root: Path) -> Optional[Path]:
    ralph_dir = project_root / ".tf/ralph"
    if not ralph_dir.is_dir():
        print("Ralph not initialized. Run: tf ralph init", file=sys.stderr)
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


def sanitize_ticket_query(query: str) -> str:
    if re.search(r"(^|\s)tf\s+next(\s|$)", query):
        print("[warn] ticketQuery uses 'tf next' (recursive). Using default tk-ready query.", file=sys.stderr)
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


def prompt_exists(project_root: Path) -> bool:
    local_prompt = project_root / ".pi/prompts/tf.md"
    global_prompt = Path.home() / ".pi/agent/prompts/tf.md"
    if local_prompt.is_file() or global_prompt.is_file():
        return True
    print("Missing /tf prompt. Install via: tf setup --project <path> or tf setup --global", file=sys.stderr)
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
) -> int:
    if not ticket:
        print("No ticket specified.", file=sys.stderr)
        return 1
    if not ensure_pi():
        print("pi not found in PATH; cannot run workflow.", file=sys.stderr)
        return 1
    if cwd is None:
        project_root = find_project_root()
        if project_root and not prompt_exists(project_root):
            return 1
    else:
        if not prompt_exists(cwd):
            return 1

    cmd = build_cmd(workflow, ticket, flags)
    session_flag = f" --session {session_path}" if session_path else ""

    if dry_run:
        prefix = " (worktree)" if cwd else ""
        print(f"Dry run: pi -p{session_flag} \"{cmd}\"{prefix}")
        return 0

    print(f"Running: pi -p{session_flag} \"{cmd}\"")
    args = ["pi", "-p"]
    if session_path:
        args += ["--session", str(session_path)]
    args.append(cmd)
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


def lock_acquire(ralph_dir: Path) -> bool:
    lock_path = ralph_dir / "lock"
    if lock_path.exists():
        try:
            pid_text = lock_path.read_text(encoding="utf-8").strip().split()[0]
            pid = int(pid_text)
            os.kill(pid, 0)
            print(f"Ralph loop already running (pid {pid}). Remove {lock_path} if stale.", file=sys.stderr)
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


def extract_ticket_title(ticket: str) -> str:
    if shutil.which("tk") is None:
        return ticket
    proc = subprocess.run(["tk", "show", ticket], capture_output=True, text=True)
    if proc.returncode != 0:
        return ticket
    in_front = False
    for line in proc.stdout.splitlines():
        if line.strip() == "---":
            in_front = not in_front
            continue
        if in_front:
            continue
        if line.startswith("# "):
            return line[2:].strip()
    return ticket


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


def parse_run_args(args: List[str]) -> Tuple[Optional[str], bool, Optional[str]]:
    ticket_override: Optional[str] = None
    dry_run = False
    flags_override: Optional[str] = None
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--dry-run":
            dry_run = True
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
    return ticket_override, dry_run, flags_override


def parse_start_args(args: List[str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {
        "max_iterations": None,
        "dry_run": False,
        "parallel_override": None,
        "no_parallel": False,
        "flags_override": None,
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
        ticket_override, dry_run, flags_override = parse_run_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
        return 1

    ralph_dir = ensure_ralph_dir(project_root)
    if not ralph_dir:
        return 1

    config = load_config(ralph_dir)

    ticket_query = sanitize_ticket_query(str(config.get("ticketQuery", DEFAULTS["ticketQuery"])))
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))
    if flags_override:
        workflow_flags = f"{workflow_flags} {flags_override}".strip()

    session_dir = resolve_session_dir(project_root, config)
    session_per_ticket = parse_bool(
        config.get("sessionPerTicket", DEFAULTS["sessionPerTicket"]),
        DEFAULTS["sessionPerTicket"],
    )

    ticket = ticket_override or select_ticket(ticket_query)
    if not ticket:
        print("No ready tickets found.", file=sys.stderr)
        return 1

    session_path = None
    if session_dir:
        if session_per_ticket:
            session_path = session_dir / f"{ticket}.jsonl"
        else:
            session_path = session_dir / f"loop-{utc_now()}.jsonl"

    rc = run_ticket(ticket, workflow, workflow_flags, dry_run, session_path=session_path)
    if dry_run:
        return rc

    if rc != 0:
        update_state(ralph_dir, project_root, ticket, "FAILED", f"pi -p failed (exit {rc})")
        return rc

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

    ralph_dir = ensure_ralph_dir(project_root)
    if not ralph_dir:
        return 1

    config = load_config(ralph_dir)

    max_iterations = options["max_iterations"] or int(config.get("maxIterations", DEFAULTS["maxIterations"]))
    sleep_between = int(config.get("sleepBetweenTickets", DEFAULTS["sleepBetweenTickets"]))
    sleep_retries = int(config.get("sleepBetweenRetries", DEFAULTS["sleepBetweenRetries"]))
    ticket_query = sanitize_ticket_query(str(config.get("ticketQuery", DEFAULTS["ticketQuery"])))
    completion_check = str(config.get("completionCheck", DEFAULTS["completionCheck"]))
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))
    promise_on_complete = parse_bool(
        config.get("promiseOnComplete", DEFAULTS["promiseOnComplete"]),
        DEFAULTS["promiseOnComplete"],
    )

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
            print("[warn] git repo not found; falling back to serial.", file=sys.stderr)
            use_parallel = 1

    if use_parallel > 1 and session_dir and not session_per_ticket:
        print("[warn] sessionPerTicket=false with parallel execution; using per-ticket sessions.", file=sys.stderr)
        session_per_ticket = True

    lock_acquired = False
    if not options["dry_run"]:
        if not lock_acquire(ralph_dir):
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
                    print("No ready tickets. Ralph loop complete.")
                    if not options["dry_run"]:
                        set_state(ralph_dir, "COMPLETE")
                    if promise_on_complete:
                        print("<promise>COMPLETE</promise>")
                    return 0

                ticket = select_ticket(ticket_query)
                if not ticket:
                    time.sleep(sleep_retries / 1000)
                    continue

                session_path = None
                if session_dir:
                    if session_per_ticket:
                        session_path = session_dir / f"{ticket}.jsonl"
                    else:
                        session_path = loop_session_path

                rc = run_ticket(
                    ticket,
                    workflow,
                    workflow_flags,
                    options["dry_run"],
                    session_path=session_path,
                )
                if not options["dry_run"]:
                    if rc != 0:
                        update_state(ralph_dir, project_root, ticket, "FAILED", f"pi -p failed (exit {rc})")
                        return rc
                    update_state(ralph_dir, project_root, ticket, "COMPLETE", "")

                iteration += 1
                time.sleep(sleep_between / 1000)

            print(f"Max iterations reached ({max_iterations}).")
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

        if not ensure_pi() or not prompt_exists(project_root):
            return 1

        while iteration < max_iterations:
            if backlog_empty(completion_check):
                print("No ready tickets. Ralph loop complete.")
                if not options["dry_run"]:
                    set_state(ralph_dir, "COMPLETE")
                if promise_on_complete:
                    print("<promise>COMPLETE</promise>")
                return 0

            remaining = max_iterations - iteration
            batch_size = min(use_parallel, remaining)
            ready = list_ready_tickets(list_query)
            selected = select_parallel_tickets(ready, batch_size, allow_untagged, tag_prefix)

            if not selected:
                fallback_ticket = select_ticket(ticket_query)
                if not fallback_ticket:
                    time.sleep(sleep_retries / 1000)
                    continue
                selected = [fallback_ticket]

            if options["dry_run"]:
                for ticket in selected:
                    cmd = build_cmd(workflow, ticket, workflow_flags)
                    session_note = f" --session {session_dir / (ticket + '.jsonl')}" if session_dir else ""
                    print(f"Dry run: pi -p{session_note} \"{cmd}\" (worktree)")
                iteration += len(selected)
                time.sleep(sleep_between / 1000)
                continue

            processes: List[Tuple[subprocess.Popen, str, Path]] = []
            for ticket in selected:
                worktree_path = worktrees_dir / ticket
                subprocess.run(["git", "-C", str(repo_root), "worktree", "remove", "-f", str(worktree_path)], capture_output=True)
                add = subprocess.run(
                    ["git", "-C", str(repo_root), "worktree", "add", "-B", f"ralph/{ticket}", str(worktree_path), "HEAD"],
                    capture_output=True,
                )
                if add.returncode != 0:
                    update_state(ralph_dir, project_root, ticket, "FAILED", "worktree add failed", repo_root / ".tf/knowledge")
                    continue

                session_path = None
                if session_dir:
                    session_path = session_dir / f"{ticket}.jsonl"

                cmd = build_cmd(workflow, ticket, workflow_flags)
                args = ["pi", "-p"]
                if session_path:
                    args += ["--session", str(session_path)]
                args.append(cmd)
                proc = subprocess.Popen(args, cwd=worktree_path)
                processes.append((proc, ticket, worktree_path))

            for proc, ticket, worktree_path in processes:
                rc = proc.wait()
                if rc != 0:
                    update_state(
                        ralph_dir,
                        project_root,
                        ticket,
                        "FAILED",
                        f"pi -p failed (exit {rc})",
                        worktree_path / ".tf/knowledge",
                    )
                    return rc

                update_state(ralph_dir, project_root, ticket, "COMPLETE", "", worktree_path / ".tf/knowledge")

                if not keep_worktrees:
                    remove = subprocess.run(
                        ["git", "-C", str(repo_root), "worktree", "remove", "-f", str(worktree_path)],
                        capture_output=True,
                    )
                    if remove.returncode != 0:
                        shutil.rmtree(worktree_path, ignore_errors=True)

            iteration += len(selected)
            time.sleep(sleep_between / 1000)

        print(f"Max iterations reached ({max_iterations}).")
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
