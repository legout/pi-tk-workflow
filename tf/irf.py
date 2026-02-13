from __future__ import annotations

import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .utils import find_project_root


KNOWN_FLAGS = {
    "--auto",
    "--no-clarify",
    "--no-research",
    "--with-research",
    "--plan",
    "--dry-run",
    "--create-followups",
    "--simplify-tickets",
    "--final-review-loop",
    "--retry-reset",
}

PHASE_PASSTHROUGH_FLAGS = {
    "--auto",
    "--no-clarify",
    "--retry-reset",
}


@dataclass
class ResolvedIrfPlan:
    ticket_id: str
    chain_steps: List[str]
    shared_args: List[str]
    post_chain_commands: List[str]
    plan_only: bool
    research_entry: str


@dataclass
class WorkflowConfig:
    enable_researcher: bool = True
    knowledge_dir: str = ".tf/knowledge"


def _load_workflow_config(project_root: Path) -> WorkflowConfig:
    # Prefer project runtime config, fallback to repo config.
    candidates = [
        project_root / ".tf" / "config" / "settings.json",
        project_root / "config" / "settings.json",
    ]

    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
            return WorkflowConfig(
                enable_researcher=bool(workflow.get("enableResearcher", True)),
                knowledge_dir=str(workflow.get("knowledgeDir", ".tf/knowledge")),
            )
        except Exception:
            continue

    return WorkflowConfig()


def _parse_args(argv: List[str]) -> tuple[str, List[str]]:
    if not argv:
        raise ValueError("Missing ticket id. Usage: tf irf <ticket-id> [flags]")

    ticket_id: Optional[str] = None
    flags: List[str] = []

    for token in argv:
        if token.startswith("--"):
            if token not in KNOWN_FLAGS:
                raise ValueError(f"Unknown flag: {token}")
            flags.append(token)
            continue

        if ticket_id is None:
            ticket_id = token
        else:
            raise ValueError(f"Unexpected positional argument: {token}")

    if not ticket_id:
        raise ValueError("Missing ticket id. Usage: tf irf <ticket-id> [flags]")

    return ticket_id, flags


def resolve_irf_plan(argv: List[str], project_root: Optional[Path] = None) -> ResolvedIrfPlan:
    ticket_id, flags = _parse_args(argv)

    root = project_root or find_project_root() or Path.cwd()
    cfg = _load_workflow_config(root)

    # Default based on config; then apply conflicting flags in-order (last wins).
    research_entry = "tf-research" if cfg.enable_researcher else "tf-implement"
    for flag in flags:
        if flag == "--no-research":
            research_entry = "tf-implement"
        elif flag == "--with-research":
            research_entry = "tf-research"

    chain_steps = ["tf-implement", "tf-review", "tf-fix", "tf-close"]
    if research_entry == "tf-research":
        chain_steps = ["tf-research", *chain_steps]

    shared_args = [ticket_id, *[f for f in flags if f in PHASE_PASSTHROUGH_FLAGS]]

    plan_only = "--plan" in flags or "--dry-run" in flags

    knowledge_dir = Path(cfg.knowledge_dir)
    if not knowledge_dir.is_absolute():
        knowledge_dir = root / knowledge_dir
    artifact_dir = knowledge_dir / "tickets" / ticket_id

    post_chain_commands: List[str] = []
    if "--create-followups" in flags:
        post_chain_commands.append(f"/tf-followups {shlex.quote(str(artifact_dir / 'review.md'))}")
    if "--simplify-tickets" in flags:
        post_chain_commands.append("/simplify --create-tickets --last-implementation")
    if "--final-review-loop" in flags:
        post_chain_commands.append("/review-start")

    return ResolvedIrfPlan(
        ticket_id=ticket_id,
        chain_steps=chain_steps,
        shared_args=shared_args,
        post_chain_commands=post_chain_commands,
        plan_only=plan_only,
        research_entry=research_entry,
    )


def _build_chain_command(plan: ResolvedIrfPlan) -> str:
    chain = " -> ".join(plan.chain_steps)
    shared = " ".join(shlex.quote(arg) for arg in plan.shared_args)
    return f"/chain-prompts {chain} -- {shared}".strip()


def _run_pi(prompt: str, cwd: Path) -> int:
    proc = subprocess.run(["pi", "-p", prompt], cwd=cwd)
    return proc.returncode


def _print_plan(plan: ResolvedIrfPlan) -> None:
    print("## Resolved IRF Plan")
    print(f"Ticket: {plan.ticket_id}")
    print(f"Research entry: {plan.research_entry}")
    print(f"Chain: {' -> '.join(plan.chain_steps)}")
    print(f"Chain command: {_build_chain_command(plan)}")
    if plan.post_chain_commands:
        print("Post-chain commands:")
        for cmd in plan.post_chain_commands:
            print(f"- {cmd}")
    else:
        print("Post-chain commands: (none)")


def run_irf(argv: List[str]) -> int:
    root = find_project_root() or Path.cwd()

    try:
        plan = resolve_irf_plan(argv, project_root=root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if plan.plan_only:
        _print_plan(plan)
        return 0

    chain_cmd = _build_chain_command(plan)
    chain_rc = _run_pi(chain_cmd, cwd=root)
    if chain_rc != 0:
        print(
            f"IRF chain failed with exit code {chain_rc}; skipping post-chain commands.",
            file=sys.stderr,
        )
        return chain_rc

    for post_cmd in plan.post_chain_commands:
        rc = _run_pi(post_cmd, cwd=root)
        if rc != 0:
            print(
                f"Warning: post-chain command failed ({post_cmd}) with exit code {rc}",
                file=sys.stderr,
            )

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = argv or []
    if not args or args[0] in {"-h", "--help", "help"}:
        print(
            """Usage:
  tf irf <ticket-id> [--auto] [--no-clarify] [--no-research] [--with-research]
         [--plan|--dry-run] [--create-followups] [--simplify-tickets]
         [--final-review-loop] [--retry-reset]

Runs the deterministic /chain-prompts IRF workflow wrapper.
"""
        )
        return 0

    return run_irf(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
