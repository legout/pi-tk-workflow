# Implement → Review → Fix → Close (TF) Workflow

This workflow runs a full ticket implementation chain using `/chain-prompts` and project-local assets.

## Trigger

```bash
/tf <ticket-id> [flags]
```

`/tf` delegates to deterministic Python orchestration:

```bash
tf irf <ticket-id> [flags]
```

## Phase Sequence

1. `tf-research` (optional)
2. `tf-implement`
3. `tf-review` (phase orchestrator)
4. `tf-fix`
5. `tf-close`

Reviewer fan-out inside review phase:
- `reviewer-general`
- `reviewer-spec-audit`
- `reviewer-second-opinion`

## Files & Locations

**Project assets (canonical):**
- `<project>/prompts/*.md`
- `<project>/skills/*/SKILL.md`
- `<project>/agents/*.md`

**Project config/state:**
- `<project>/.tf/config/settings.json`
- `<project>/.tf/knowledge/...`
- `<project>/.tf/ralph/...`

## Flags

- `--auto` / `--no-clarify`
- `--plan` / `--dry-run`
- `--no-research`
- `--with-research`
- `--create-followups`
- `--simplify-tickets`
- `--final-review-loop`
- `--retry-reset`

## Required Extensions

```bash
pi install npm:pi-prompt-template-model
pi install npm:pi-subagents
```

Optional:
```bash
pi install npm:pi-review-loop
pi install npm:pi-mcp-adapter
pi install npm:pi-web-access
```

## Knowledge Storage

```
.tf/knowledge/
  topics/<topic-id>/
  tickets/<ticket-id>/
    research.md
    implementation.md
    review.md
    fixes.md
    close-summary.md
    chain-summary.md
    files_changed.txt
    ticket_id.txt
```

## Sync Models

After editing `.tf/config/settings.json`:

```bash
tf sync
# or
/tf-sync
```
