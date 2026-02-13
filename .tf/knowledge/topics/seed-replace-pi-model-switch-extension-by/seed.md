# Seed: Replace pi-model-switch with /chain-prompts in pi-prompt-template-model

## Vision

Reduce the number of required Pi extensions for `pi-ticketflow` by replacing runtime model switching (`pi-model-switch`) with prompt-level orchestration using `pi-prompt-template-model`’s new `/chain-prompts` feature.

This should simplify installation/maintenance while keeping (or improving) determinism: each workflow phase runs with the intended model, thinking level, and skill injection.

## Core Concept

Split the current monolithic `/tf` implementation workflow into project-local phase prompts (`prompts/`) plus phase skills (`skills/`):

- `/tf-research`
- `/tf-implement`
- `/tf-review` (still uses `pi-subagents` for parallel reviewers + merge)
- `/tf-fix`
- `/tf-close`

Then keep `/tf` as the user-facing command but delegate deterministically to `tf irf` (Python tooling), which builds `/chain-prompts` sequences. Each phase prompt carries its own `model:`, `thinking:`, and `skill:` frontmatter.

## Key Features

1. Phase-specific prompts with explicit model/skill/thinking frontmatter.
2. `/tf` becomes a declarative chain of prompts instead of a single skill doing runtime switching.
3. Keep `pi-subagents` for reviewer fan-out and merge.
4. Preserve existing TF artifacts under `.tf/knowledge/tickets/<id>/`.
5. Maintain (or improve) non-interactive execution (`pi -p`) and rollback/restore behavior on mid-chain failures.

## Open Questions

- Flags/conditionals: How to support `--no-research`, `--with-research`, `--create-followups`, etc. in a chain world?
- Error handling: What is the desired behavior if a mid-chain step fails (stop, continue, partial artifacts)?
- Retry/escalation: Should retry state/model escalation remain in skill logic, and if so where does it live?
- UX: Should users still type `/tf <id>` or should the chained workflow get a new explicit command name?
- Compatibility: Do we need to keep `switch_model` support as a fallback for older Pi installs?
