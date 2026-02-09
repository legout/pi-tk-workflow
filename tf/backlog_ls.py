from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

from .utils import find_project_root, read_json


def resolve_knowledge_dir(project_root: Path) -> Path:
    settings_path = project_root / ".tf/config/settings.json"
    knowledge_dir = ".tf/knowledge"
    if settings_path.exists():
        data = read_json(settings_path)
        workflow = data.get("workflow", {}) if isinstance(data, dict) else {}
        if isinstance(workflow, dict):
            knowledge_dir = workflow.get("knowledgeDir", knowledge_dir)
    path = Path(str(knowledge_dir)).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path


def list_topics(topics_dir: Path) -> List[Path]:
    topics: List[Path] = []
    for p in sorted(topics_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("seed-") or p.name.startswith("baseline-") or p.name.startswith("plan-"):
            topics.append(p)
    return topics


def parse_backlog(path: Path) -> List[List[str]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if cells[0].lower() == "id":
            continue
        if set(cells[0]) == {"-"}:
            continue
        if len(cells) < 2:
            continue
        rows.append(cells)
    return rows


def topic_type(name: str) -> str:
    if name.startswith("seed-"):
        return "seed"
    if name.startswith("baseline-"):
        return "baseline"
    if name.startswith("plan-"):
        return "plan"
    return "topic"


def ticket_summary(rows: List[List[str]]) -> str:
    ids = [r[0] for r in rows if r]
    if not ids:
        return "0"
    if len(ids) <= 3:
        return f"{len(ids)} ({', '.join(ids)})"
    return f"{len(ids)} ({', '.join(ids[:3])}, …)"


def resolve_topic(topics_dir: Path, arg: str) -> Path:
    candidate = Path(arg).expanduser()
    if candidate.exists():
        return candidate
    if not candidate.is_absolute():
        rel = Path.cwd() / candidate
        if rel.exists():
            return rel
    return topics_dir / arg


def run_backlog_ls(topic_arg: Optional[str]) -> int:
    project_root = find_project_root()
    if not project_root:
        print("No .tf directory found. Run in a project with .tf/.")
        return 1

    knowledge_dir = resolve_knowledge_dir(project_root)
    topics_dir = knowledge_dir / "topics"

    if not topics_dir.exists():
        print(f"No topics directory found: {topics_dir}")
        return 0

    if topic_arg:
        topic_path = resolve_topic(topics_dir, topic_arg)
        if not topic_path.exists():
            available = [p.name for p in list_topics(topics_dir)]
            print(f"Topic not found: {topic_arg}")
            if available:
                print("Available topics:")
                for name in available:
                    print(f"- {name}")
            return 1
        topics = [topic_path]
    else:
        topics = list_topics(topics_dir)

    if not topics:
        print(f"No seed/baseline/plan topics found in {topics_dir}")
        return 0

    if len(topics) == 1:
        topic = topics[0]
        backlog_path = topic / "backlog.md"
        rows = parse_backlog(backlog_path)
        print(f"Topic: {topic.name} ({topic_type(topic.name)})")
        if backlog_path.exists():
            print(f"Backlog: yes ({len(rows)} tickets)")
            print("")
            print(f"# Backlog: {topic.name}")
            print("| ID | Title | Est. Hours |")
            print("|----|-------|------------|")
            for row in rows:
                est = row[2] if len(row) > 2 else ""
                print(f"| {row[0]} | {row[1]} | {est} |")
        else:
            print("Backlog: no (unticketed)")
            print(f"Run: /tf-backlog {topic.name}")
        return 0

    print("| Topic | Type | Backlog | Tickets |")
    print("|-------|------|---------|---------|")
    for topic in topics:
        backlog_path = topic / "backlog.md"
        rows = parse_backlog(backlog_path)
        backlog_status = "yes" if backlog_path.exists() else "no"
        tickets = ticket_summary(rows) if backlog_path.exists() else "0"
        print(f"| {topic.name} | {topic_type(topic.name)} | {backlog_status} | {tickets} |")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new backlog-ls")
    parser.add_argument("topic", nargs="?", help="Topic id or path")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_backlog_ls(args.topic)


if __name__ == "__main__":
    raise SystemExit(main())
