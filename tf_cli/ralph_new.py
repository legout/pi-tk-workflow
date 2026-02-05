import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULTS: Dict[str, Any] = {
    "maxIterations": 50,
    "maxIterationsPerTicket": 5,
    "ticketQuery": "tk ready | head -1 | awk '{print $1}'",
    "completionCheck": "tk ready | grep -q .",
    "sleepBetweenTickets": 5000,
    "sleepBetweenRetries": 10000,
    "workflow": "/tf",
    "workflowFlags": "--auto",
    "promiseOnComplete": True,
}


def usage() -> None:
    print(
        """Ralph (new Python CLI)

Usage:
  tf new ralph run [ticket-id] [--dry-run] [--flags '...']
  tf new ralph start [--max-iterations N] [--dry-run] [--flags '...']

Notes:
  - This is the new Python implementation (parallel execution not yet supported).
"""
    )


def find_project_root() -> Optional[Path]:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return None


def load_config(ralph_dir: Path) -> Dict[str, Any]:
    config_path = ralph_dir / "config.json"
    data: Dict[str, Any] = {}
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    config = dict(DEFAULTS)
    if isinstance(data, dict):
        config.update(data)
    return config


def run_shell(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def select_ticket(ticket_query: str) -> Optional[str]:
    result = run_shell(ticket_query)
    output = (result.stdout or "").strip()
    if not output:
        return None
    return output.split()[0]


def backlog_empty(completion_check: str) -> bool:
    result = run_shell(completion_check)
    return result.returncode != 0


def ensure_pi() -> bool:
    return shutil.which("pi") is not None


def run_ticket(ticket: str, workflow: str, flags: str, dry_run: bool) -> int:
    if not ticket:
        print("No ticket specified.", file=sys.stderr)
        return 1
    if not ensure_pi():
        print("pi not found in PATH; cannot run workflow.", file=sys.stderr)
        return 1

    cmd = f"{workflow} {ticket}".strip()
    if flags:
        cmd = f"{cmd} {flags}".strip()

    if dry_run:
        print(f"Dry run: pi -c \"{cmd}\"")
        return 0

    print(f"Running: pi -c \"{cmd}\"")
    result = subprocess.run(["pi", "-c", cmd])
    return result.returncode


def parse_flags(args: list[str]) -> tuple[Optional[str], bool, Optional[str]]:
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


def ralph_run(args: list[str]) -> int:
    try:
        ticket_override, dry_run, flags_override = parse_flags(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
        return 1

    ralph_dir = project_root / ".tf/ralph"
    config = load_config(ralph_dir)

    ticket_query = str(config.get("ticketQuery", DEFAULTS["ticketQuery"]))
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))
    if flags_override:
        workflow_flags = f"{workflow_flags} {flags_override}".strip()

    ticket = ticket_override or select_ticket(ticket_query)
    if not ticket:
        print("No ready tickets found.", file=sys.stderr)
        return 1

    return run_ticket(ticket, workflow, workflow_flags, dry_run)


def ralph_start(args: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--flags")
    parser.add_argument("--help", "-h", action="store_true")
    parsed, extra = parser.parse_known_args(args)
    if parsed.help:
        usage()
        return 0
    if extra:
        print(f"Unknown option for ralph start: {' '.join(extra)}", file=sys.stderr)
        return 1

    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.", file=sys.stderr)
        return 1

    ralph_dir = project_root / ".tf/ralph"
    config = load_config(ralph_dir)

    max_iterations = parsed.max_iterations or int(config.get("maxIterations", DEFAULTS["maxIterations"]))
    sleep_between = int(config.get("sleepBetweenTickets", DEFAULTS["sleepBetweenTickets"]))
    sleep_retries = int(config.get("sleepBetweenRetries", DEFAULTS["sleepBetweenRetries"]))
    ticket_query = str(config.get("ticketQuery", DEFAULTS["ticketQuery"]))
    completion_check = str(config.get("completionCheck", DEFAULTS["completionCheck"]))
    workflow = str(config.get("workflow", DEFAULTS["workflow"]))
    workflow_flags = str(config.get("workflowFlags", DEFAULTS["workflowFlags"]))
    promise_on_complete = bool(config.get("promiseOnComplete", DEFAULTS["promiseOnComplete"]))

    if parsed.flags:
        workflow_flags = f"{workflow_flags} {parsed.flags}".strip()

    for _ in range(max_iterations):
        ticket = select_ticket(ticket_query)
        if not ticket:
            if backlog_empty(completion_check):
                print("Backlog empty.")
                if promise_on_complete:
                    print("<promise>COMPLETE</promise>")
                return 0
            time.sleep(sleep_retries / 1000)
            continue

        rc = run_ticket(ticket, workflow, workflow_flags, parsed.dry_run)
        if parsed.dry_run:
            return rc
        if rc != 0:
            print(f"Ticket failed (exit {rc}).", file=sys.stderr)
        time.sleep(sleep_between / 1000)

    print(f"Max iterations reached ({max_iterations}).")
    if promise_on_complete:
        print("<promise>COMPLETE</promise>")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
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
