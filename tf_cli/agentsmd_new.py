import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional


PACKAGE_MANAGERS = [
    ("uv", ["uv.lock"], "[tool.uv]"),
    ("poetry", ["poetry.lock"], "[tool.poetry]"),
    ("pipenv", ["Pipfile"], None),
    ("pip", ["requirements.txt", "setup.py", "setup.cfg"], None),
    ("pnpm", ["pnpm-lock.yaml"], None),
    ("yarn", ["yarn.lock"], None),
    ("npm", ["package-lock.json"], None),
    ("bun", ["bun.lockb"], None),
    ("cargo", ["Cargo.toml"], None),
    ("go", ["go.mod"], None),
    ("bundle", ["Gemfile"], None),
]


def detect_package_manager(target_dir: Path) -> str:
    for name, files, marker in PACKAGE_MANAGERS:
        for filename in files:
            if (target_dir / filename).exists():
                return name
        if marker and (target_dir / "pyproject.toml").exists():
            content = (target_dir / "pyproject.toml").read_text(encoding="utf-8")
            if marker in content:
                return name
    if (target_dir / "pyproject.toml").exists():
        return "uv"
    return "unknown"


def get_default_commands(pm: str) -> List[str]:
    return {
        "uv": [
            "run: uv run python",
            "test: uv run pytest",
            "lint: uv run ruff check .",
            "format: uv run ruff format .",
            "typecheck: uv run mypy .",
        ],
        "poetry": [
            "run: poetry run python",
            "test: poetry run pytest",
            "lint: poetry run ruff check .",
        ],
        "pipenv": ["run: pipenv run python", "test: pipenv run pytest"],
        "pip": ["run: python", "test: pytest"],
        "pnpm": ["run: pnpm dev", "build: pnpm build", "test: pnpm test", "lint: pnpm lint"],
        "npm": ["run: npm run dev", "build: npm run build", "test: npm test", "lint: npm run lint"],
        "yarn": ["run: yarn dev", "build: yarn build", "test: yarn test"],
        "bun": ["run: bun run dev", "build: bun run build", "test: bun test"],
        "cargo": ["build: cargo build", "test: cargo test", "run: cargo run"],
        "go": ["build: go build", "test: go test", "run: go run ."],
        "bundle": ["run: bundle exec ruby", "test: bundle exec rspec"],
    }.get(pm, [])


def init_agentsmd(target_dir: Path) -> int:
    target_dir = target_dir.resolve()
    agents_file = target_dir / "AGENTS.md"

    print("Initializing AGENTS.md...")
    print(f"Target directory: {target_dir}")

    if agents_file.exists():
        print("\n⚠️  AGENTS.md already exists at:")
        print(f"   {agents_file}\n")
        overwrite = input("Overwrite? (y/N) ").strip().lower().startswith("y")
        if not overwrite:
            print("Cancelled.")
            return 0
        backup = agents_file.with_name(f"AGENTS.md.backup.{datetime_stamp()}")
        shutil.move(str(agents_file), str(backup))
        print("Backed up existing file.")

    pm = detect_package_manager(target_dir)
    print(f"Detected package manager: {pm}")

    project_name = target_dir.name
    input_name = input(f"\nProject name [{project_name}]: ").strip()
    if input_name:
        project_name = input_name

    description = input("\nOne-sentence description: ").strip()
    if not description:
        description = f"A {project_name} project."

    lines = [f"# {project_name}", "", description, "", "## Quick Commands"]

    for cmd in get_default_commands(pm):
        lines.append(f"- {cmd}")

    if pm == "uv":
        lines += ["", "This project uses `uv` for Python package management.", "See: https://docs.astral.sh/uv/"]
    elif pm == "poetry":
        lines += ["", "This project uses `poetry` for Python package management."]
    elif pm == "pnpm":
        lines += ["", "This project uses `pnpm` for Node.js package management."]

    lines += [
        "",
        "## Conventions",
        "",
        "<!-- Add links to convention docs as needed: -->",
        "<!-- - TypeScript: See [docs/TYPESCRIPT.md](./docs/TYPESCRIPT.md) -->",
        "<!-- - Testing: See [docs/TESTING.md](./docs/TESTING.md) -->",
        "",
        "## Notes",
        "",
        "<!-- Project-specific notes for AI agents -->",
        "",
    ]

    agents_file.write_text("\n".join(lines), encoding="utf-8")

    print("\n✓ Created AGENTS.md at:")
    print(f"  {agents_file}")
    size = agents_file.stat().st_size
    print(f"\nFile size: {size} bytes")
    print("\nNext steps:\n  1. Review and customize the description\n  2. Add convention docs to docs/ folder if needed\n  3. Run 'tf new agentsmd validate' to check")

    cl_path = target_dir / "CLAUDE.md"
    if not cl_path.exists():
        create_link = input("\nCreate CLAUDE.md symlink for Claude Code? (y/N) ").strip().lower().startswith("y")
        if create_link:
            try:
                cl_path.symlink_to(agents_file.name)
                print("Created CLAUDE.md → AGENTS.md symlink")
            except Exception as exc:
                print(f"Failed to create symlink: {exc}")

    return 0


def status_agentsmd(target_dir: Path) -> int:
    agents_file = target_dir / "AGENTS.md"

    print("=== AGENTS.md Status ===\n")
    if not agents_file.exists():
        print(f"❌ No AGENTS.md found at: {agents_file}\n")
        print("Create one with:\n  tf new agentsmd init")
        return 1

    size = agents_file.stat().st_size
    lines = agents_file.read_text(encoding="utf-8").splitlines()

    print(f"File: {agents_file}")
    print(f"Size: {size} bytes")
    print(f"Lines: {len(lines)}\n")

    if size < 2048:
        print("✓ Size: Good (under 2KB)")
    elif size < 5120:
        print(f"⚠️  Size: Moderate ({size} bytes) - consider using progressive disclosure")
    else:
        print("❌ Size: Large (>5KB) - recommend refactoring")

    print("")
    cl_path = target_dir / "CLAUDE.md"
    if cl_path.is_symlink():
        print("✓ CLAUDE.md symlink exists")
    elif cl_path.exists():
        print("⚠️  CLAUDE.md exists (separate file, not symlinked)")
    else:
        print("○ CLAUDE.md not found (optional, for Claude Code users)")

    print("\nNested AGENTS.md files:")
    nested = []
    for path in target_dir.rglob("AGENTS.md"):
        if path != agents_file:
            nested.append(path)
    if not nested:
        print("  (none found)")
    else:
        for path in nested:
            rel = path.relative_to(target_dir)
            print(f"  - {rel} ({path.stat().st_size} bytes)")

    print("\n=== Content Preview ===")
    preview_lines = lines[:20]
    for line in preview_lines:
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")

    return 0


def validate_agentsmd(target_dir: Path) -> int:
    agents_file = target_dir / "AGENTS.md"

    print("=== AGENTS.md Validation ===\n")
    if not agents_file.exists():
        print(f"❌ AGENTS.md not found at: {agents_file}")
        return 1

    issues = 0
    warnings = 0
    content = agents_file.read_text(encoding="utf-8")
    size = agents_file.stat().st_size

    print(f"File size: {size} bytes")
    if size > 5120:
        print("❌ File is large (>5KB). Consider progressive disclosure.")
        issues += 1
    elif size > 2048:
        print("⚠️  File is moderate size. Monitor for growth.")
        warnings += 1
    else:
        print("✓ File size is good")

    print("\nChecking referenced paths...")
    path_pattern = re.compile(r"\b(src|lib|docs|test|tests|app|bin|scripts)/[a-zA-Z0-9_./-]+\.[a-z]+")
    paths = [m.group(0) for m in path_pattern.finditer("\n".join(line for line in content.splitlines() if not line.strip().startswith("<")))]
    stale_paths = []
    for path in paths:
        if not (target_dir / path).exists() and not Path(path).exists():
            stale_paths.append(path)

    if stale_paths:
        print("⚠️  Potentially stale paths found:")
        for path in stale_paths:
            print(f"   - {path} (not found)")
        warnings += 1
    else:
        print("✓ No obviously stale paths detected")

    print("\nChecking for anti-patterns...")
    platitudes = [
        "write clean code",
        "follow best practices",
        "keep it simple",
        "don't repeat yourself",
        "write good code",
    ]
    found_platitudes = [p for p in platitudes if re.search(p, content, re.IGNORECASE)]
    if found_platitudes:
        print("⚠️  Vague platitudes found (not actionable):")
        for phrase in found_platitudes:
            print(f"   - \"{phrase}\"")
        warnings += 1
    else:
        print("✓ No vague platitudes found")

    absolutes = re.findall(r"^\s*[-*]?\s*(always|never)\s+.+", content, re.IGNORECASE | re.MULTILINE)
    if absolutes:
        print("⚠️  Absolute statements found (may cause contradictions):")
        lines = re.findall(r"^\s*[-*]?\s*(?:always|never)\s+.+", content, re.IGNORECASE | re.MULTILINE)
        for line in lines[:3]:
            print(f"   {line.strip()}")
        if len(lines) > 3:
            print(f"   ... ({len(lines)} more)")
        warnings += 1
    else:
        print("✓ No absolute statements found")

    if re.search(r"(directory structure|folder structure|file structure|project structure)", content, re.IGNORECASE):
        print("⚠️  File structure documentation found - this goes stale quickly")
        warnings += 1

    print("\n=== Summary ===")
    if issues == 0 and warnings == 0:
        print("✓ All checks passed!")
        return 0

    print(f"Issues: {issues}, Warnings: {warnings}")
    if issues > 0:
        print("Run 'tf new agentsmd fix' to attempt auto-fixes")
    return 1 if issues > 0 else 0


def fix_agentsmd(target_dir: Path) -> int:
    agents_file = target_dir / "AGENTS.md"

    print("=== AGENTS.md Auto-Fix ===\n")
    if not agents_file.exists():
        print(f"❌ AGENTS.md not found at: {agents_file}")
        return 1

    backup = agents_file.with_name(f"AGENTS.md.backup.{datetime_stamp()}")
    shutil.copy2(agents_file, backup)
    print(f"✓ Backup created: {backup}\n")

    fixes = 0
    content = agents_file.read_text(encoding="utf-8")

    if not re.search(r"(package manager|uv|poetry|pip|npm|pnpm|yarn)", content, re.IGNORECASE):
        pm = detect_package_manager(target_dir)
        if pm != "unknown":
            insertion = f"\n## Package Manager\n\nThis project uses `{pm}`.\n\n"
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                if line.startswith("# "):
                    lines.insert(idx + 1, insertion.rstrip())
                    content = "\n".join(lines)
                    fixes += 1
                    break

    lines = [line.rstrip() for line in content.splitlines()]
    if lines != content.splitlines():
        content = "\n".join(lines)
        fixes += 1
        print("✓ Removed trailing whitespace")

    if content and not content.endswith("\n"):
        content += "\n"
        fixes += 1
        print("✓ Added trailing newline")

    agents_file.write_text(content, encoding="utf-8")

    if fixes == 0:
        print("No auto-fixes applied.")
    else:
        print(f"Applied {fixes} fix(es).")
    print(f"\nReview changes with: git diff {agents_file}")
    return 0


def update_agentsmd(target_dir: Path) -> int:
    agents_file = target_dir / "AGENTS.md"
    if not agents_file.exists():
        print("AGENTS.md not found. Run: tf new agentsmd init")
        return 1

    backup = agents_file.with_name(f"AGENTS.md.backup.{datetime_stamp()}")
    shutil.copy2(agents_file, backup)

    content = agents_file.read_text(encoding="utf-8")
    if "## Tool Preferences" in content:
        print("Found Tool Preferences section - review manually")
        return 0

    addition = "\n\n## Tool Preferences\n- Use `rg` instead of `grep` for searching\n- Use `ast-grep` for semantic code search when available\n"
    agents_file.write_text(content + addition, encoding="utf-8")
    print("Added Tool Preferences section")
    print(f"Review changes: git diff {agents_file}")
    return 0


def datetime_stamp() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="tf new agentsmd")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("path", nargs="?", default=str(Path.cwd()))

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("path", nargs="?", default=str(Path.cwd()))

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", nargs="?", default=str(Path.cwd()))

    fix_parser = subparsers.add_parser("fix")
    fix_parser.add_argument("path", nargs="?", default=str(Path.cwd()))

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("path", nargs="?", default=str(Path.cwd()))

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return init_agentsmd(Path(args.path))
    if args.command == "status":
        return status_agentsmd(Path(args.path))
    if args.command == "validate":
        return validate_agentsmd(Path(args.path))
    if args.command == "fix":
        return fix_agentsmd(Path(args.path))
    if args.command == "update":
        return update_agentsmd(Path(args.path))

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
