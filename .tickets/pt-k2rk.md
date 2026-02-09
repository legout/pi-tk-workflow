---
id: pt-k2rk
status: closed
deps: []
links: [pt-m06z, pt-ce2e]
created: 2026-02-09T16:25:09Z
type: task
priority: 2
assignee: legout
external-ref: plan-refactor-tf-cli-to-tf
tags: [tf, backlog, plan, component:cli, component:config, component:docs, component:workflow]
---
# Inventory current packaging + entrypoints for tf_cli

## Task
Document the current CLI entrypoints, module layout, and import graph to de-risk the tf_cli → tf move.

## Context
We want to rename the canonical Python namespace to `tf` without breaking the `tf` command or existing imports.

## Acceptance Criteria
- [ ] Identify current console-script entrypoints in pyproject.toml
- [ ] Identify key modules/packages that must move first (dispatcher + shared utils)
- [ ] Note any import cycles / tricky boundaries

## Constraints
- Keep output as short notes in the ticket (or a small doc) for later reference

## References
- Plan: plan-refactor-tf-cli-to-tf


## Notes

**2026-02-09T16:31:59Z**

## Completed: Inventory of tf_cli packaging structure

### Summary
Analyzed current packaging structure to de-risk the tf_cli → tf namespace migration.

### Key Findings
1. **Console script entrypoint**:  (pyproject.toml)
2. **Module entrypoint**: Ticketflow CLI

Usage:
  tf --version | -v | -V
  tf install [--global] [--force-local]
  tf setup
  tf login
  tf init [--project <path>]
  tf sync [--project <path>]
  tf doctor [--project <path>] [--fix]
  tf update
  tf next
  tf backlog-ls [topic-id-or-path]
  tf track <path>
  tf priority-reclassify [--apply] [--ids ...] [--ready] [--status ...] [--tag ...]
  tf ralph <subcommand> ...
  tf agentsmd <subcommand> ...
  tf seed ...
  tf kb ...
  tf ui

Commands:
  install           Install the Ticketflow CLI shim
  setup             Run interactive setup wizard
  login             Authenticate with ticket storage service
  init              Initialize a project for Ticketflow
  sync              Sync tickets with external service
  doctor            Diagnose and fix common issues
  update            Update the CLI to latest version
  next              Show next recommended ticket to work on
  backlog-ls        List tickets in backlog by topic
  track             Track file changes for a ticket
  priority-reclassify  Reclassify ticket priorities
  ralph             Ralph loop management commands
  agentsmd          AGENTS.md management commands
  seed              Create seed topics from ideas
  kb                Knowledge base management commands
  ui                Launch the interactive Kanban TUI

Run 'tf <command> --help' for more information on a command.

(You can also use: tf new <command> ... for the old subcommand namespace.) → 
3. **Critical modules to move first**: cli.py, version.py, ticket_loader.py, utils.py
4. **Import cycles**: None detected (clean DAG)

### Artifacts
- Research: 
- Implementation: 

### Commit
f9014ee - pt-k2rk: Inventory tf_cli packaging and entrypoints

### Review
- Critical: 0 | Major: 0 | Minor: 0 | Warnings: 0
- No code changes required (documentation/analysis task)
