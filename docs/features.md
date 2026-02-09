# Feature Overview

## 1. Workflow Execution

- `/tf <ticket-id>` runs the Implement -> Review -> Fix -> Close loop
- Optional research and final review-loop integrations
- Artifacts written per ticket under `.tf/knowledge/tickets/<ticket-id>/`

## 2. Planning and Research

- `/tf-seed` captures early ideas
- `/tf-plan`, `/tf-plan-consult`, `/tf-plan-revise`, `/tf-plan-review` support structured planning
- `/tf-plan-chain` runs the full plan lifecycle via prompt chaining when available
- `/tf-spike` and `/tf-baseline` support deep discovery and status mapping

## 3. Backlog Generation and Maintenance

- `/tf-backlog` creates tickets from seed/plan/baseline artifacts
- `/tf-backlog-ls` shows backlog state
- `/tf-tags-suggest` and `/tf-deps-sync` refine tags and dependency integrity

## 4. Autonomous Ticket Processing (Ralph)

- `/ralph-start` processes ready tickets iteratively
- Progress, lessons, and loop state under `.tf/ralph/`
- Configurable ticket query, iteration limits, and session behavior

## 5. Agent-Oriented Review Loop

- Parallel reviewers for general quality, spec compliance, and second-opinion checks
- Shared reviewer core skill (`tf-review`) keeps review contract consistent while models vary per reviewer agent
- Review merge + fixer + closer stages keep output structured and auditable
- Supports quality gate behavior before ticket close

## 6. Project-Scoped Assets and State

- Workflow assets in `.pi/`
- TF-owned runtime/config state in `.tf/`
- Explicit artifact policy for generated vs committed files

## 7. Python API Modules

- Canonical package namespace: `tf`
- Includes reusable modules for ticket creation, classifier logic, CLI utilities, and workflow orchestration
- `tf_cli` exists as a compatibility shim during the 0.4.x line

## Related Docs

- [`commands.md`](commands.md)
- [`workflows.md`](workflows.md)
- [`architecture.md`](architecture.md)
- [`deprecation-policy.md`](deprecation-policy.md)
