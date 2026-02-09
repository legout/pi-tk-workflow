# Implement → Review → Fix → Close (TF) Workflow

This workflow runs a full ticket implementation chain:

1. **Research** (`researcher`, optional)
2. **Implement** (worker model)
3. **Parallel reviews** (`reviewer-general`, `reviewer-spec-audit`, `reviewer-second-opinion`)
4. **Merge reviews** (`review-merge`)
5. **Fix** (`fixer`, only if Critical/Major/Minor issues exist)
6. **Close** (`closer`)
7. **Chain summary** (`chain-summary.md` written by `closer`)

The chain is triggered by:
```
/tf <ticket-id> [flags]
```

---

## Files & Locations

**Config (project):**
- `<project>/.tf/config/settings.json`

**Prompt template (project-local):**
- `<project>/.pi/prompts/tf.md`

**Agent files (project-local):**
- `<project>/.pi/agents/reviewer-general.md`
- `<project>/.pi/agents/reviewer-spec-audit.md`
- `<project>/.pi/agents/reviewer-second-opinion.md`
- `<project>/.pi/agents/researcher.md`
- `<project>/.pi/agents/researcher-fetch.md`
- `<project>/.pi/agents/review-merge.md`
- `<project>/.pi/agents/fixer.md`
- `<project>/.pi/agents/closer.md`

**Sync command:**
- `<project>/.pi/prompts/tf-sync.md` (run `/tf-sync`) or run `tf sync`

---

## Prerequisites

- Ticket system CLI (`tk`) available in PATH
- Project repo checked out and writable
- Required tools installed for your languages (see below)

---

## Optional Tools (recommended)

### Python
- `ruff` (lint + format)
- `mypy` (type checking)

### JS/TS
- `eslint` (lint)
- `prettier` (format)
- `tsc` (type checking)

### Rust
- `cargo clippy` (lint)
- `cargo fmt` (format)
- `cargo check` (type checking)

### Go
- `gofmt` (format)
- `go test` (type checking/compile)

### Docs / Markup
- `markdownlint` (Markdown lint)
- `prettier` (JSON/YAML/HTML/Markdown/CSS formatting)
- `shfmt` (Shell formatting)

---

## Flags

- `--auto` / `--no-clarify` → run headless
- `--plan` / `--dry-run` → show resolved chain, do not run agents
- `--create-followups` → run `/tf-followups` on merged review
- `--simplify-tickets` → run `/simplify --create-tickets --last-implementation` after chain (if available)
- `--final-review-loop` → run `/review-start` after chain (if available)
- `--with-research` → force enable research step
- `--no-research` → force disable research step

## Related planning commands

- `/tf-seed <idea>`
- `/tf-spike <topic>`
- `/tf-backlog <optional seed path or topic-id>`
- `/tf-backlog-from-openspec <change-id or path>`
- `/tf-baseline <optional focus>`
- `/tf-followups <review path or ticket-id>`

---

## Review Severity & Fixer Behavior

Reviews use these categories:
- **Critical** (must fix)
- **Major** (should fix)
- **Minor** (nice to fix)
- **Warnings** (follow-up ticket)
- **Suggestions** (follow-up ticket)

The fixer **only handles Critical/Major/Minor**. Warnings/Suggestions should be ticketized separately. If there are no Critical/Major/Minor issues, the fixer writes a "No fixes needed" stub and makes no changes.

If `workflow.enableQualityGate` is true and any severity in `workflow.failOn` is present, the close step is skipped and the ticket remains open.

---

## Configuration

Edit the config file to customize:

- **Models** per agent and prompt role (planning/config)
- **Checkers** per language (lint/format/typecheck)
- **Workflow toggles** (enable/disable research, reviewers, fixer, closer, quality gate)
- **Fail-on severities** (`workflow.failOn`, list of severities that block closing)
- **Research parallelism** (`workflow.researchParallelAgents`)
- **Knowledge directory** (`workflow.knowledgeDir`, default `.tf/knowledge`)
- **MCP servers** (`workflow.mcpServers`, list of server ids to configure)
- **Exclude globs** for generated files

Example (partial):
```json
{
  "metaModels": {
    "worker": {
      "model": "kimi-coding/k2p5",
      "thinking": "high"
    },
    "planning": {
      "model": "openai-codex/gpt-5.2",
      "thinking": "medium"
    },
    "fast": {
      "model": "zai/glm-4.7-flash",
      "thinking": "medium"
    }
  },
  "agents": {
    "reviewer-general": "review-general",
    "reviewer-spec-audit": "review-spec",
    "fixer": "general"
  },
  "checkers": {
    "python": {
      "files": "\\.(py|pyi)$",
      "lint": "ruff check {files} --fix",
      "format": "ruff format {files}",
      "typecheck": "mypy ."
    }
  },
  "workflow": {
    "enableQualityGate": false,
    "failOn": ["Critical"]
  }
}
```

---

## Knowledge storage

Research and ticket artifacts are stored in:
```
.tf/knowledge/
  index.json
  topics/<topic-id>/
  tickets/<ticket-id>/
    research.md            # ticket research
    implementation.md
    review.md
    fixes.md
    followups.md
    close-summary.md
    chain-summary.md
    files_changed.txt
    ticket_id.txt
```

Per-ticket research can reference shared topics to avoid duplication.

---

## Applying Model Changes

Model changes are applied via:
```
/tf-sync
```

This updates the `model:` frontmatter in workflow agent **and prompt** files.

---

## Notes

- Agents must live in `~/.pi/agent/agents` or `.pi/agents` for Pi to discover them.
- Prompt templates load from `~/.pi/agent/prompts` or `.pi/prompts`.
- Config files are read manually by the prompt/agents (Pi does not auto‑apply custom settings).
- `chain-summary.md` is written in `.tf/knowledge/tickets/<ticket-id>/` by the closer.
- The close step stages/commits only paths listed in `files_changed.txt`.
