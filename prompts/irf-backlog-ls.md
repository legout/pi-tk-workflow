---
description: List backlog status and tickets [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-backlog-ls

Show backlog status and corresponding tickets for seed/baseline/plan topics.

## Usage

```
/irf-backlog-ls [topic-id-or-path]
```

## Arguments

- `$1` - Optional topic ID (`seed-*`, `baseline-*`, or `plan-*`) or path to topic directory
- If omitted: list all seed/baseline/plan topics with backlog status

## Examples

```
/irf-backlog-ls
/irf-backlog-ls seed-build-a-cli
/irf-backlog-ls plan-auth-rewrite
/irf-backlog-ls baseline-myapp
/irf-backlog-ls .pi/knowledge/topics/baseline-myapp/
```

## Execution

Follow the **IRF Planning Skill** "Backlog Listing" procedure:

1. Resolve `knowledgeDir`
2. If topic provided: show full backlog table + summary
3. If no topic: list all seed/baseline/plan topics with backlog status
4. Mark topics without `backlog.md` as **unticketed**
