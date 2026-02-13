---
name: tf-review
description: Shared code review procedure for TF reviewer subagents. Use for reviewer-general, reviewer-spec-audit, and reviewer-second-opinion.
---

# TF Review Skill

Shared review contract for all TF reviewer agents.

## Inputs

- Task input contains the ticket ID.
- Agent wrapper provides:
  - review lens (general/spec/second-opinion)
  - output filename

## Required Procedure

1. Resolve `knowledgeDir`:
   - If `.tf/config/settings.json` exists, read `workflow.knowledgeDir`.
   - Default to `.tf/knowledge`.
2. Resolve artifact directory:
   - `{knowledgeDir}/tickets/<ticket-id>/`
3. Read implementation context:
   - Read `{artifactDir}/implementation.md`.
   - Read all referenced source files from the implementation summary.
4. Apply review lens:
   - `general`: bugs, correctness, security, performance, maintainability, test coverage.
   - `spec-audit`: run `tk show <ticket-id>`, compare implementation against ticket requirements and referenced plans/specs.
   - `second-opinion`: focus on edge cases and non-obvious risks missed by typical review passes.
5. Write the final review to the exact output path specified by the agent wrapper.

## Output Format

```markdown
# Review: <ticket-id>

## Overall Assessment
2-3 sentence summary.

## Critical (must fix)
- `path:line` - issue and impact

## Major (should fix)
- `path:line` - issue and impact

## Minor (nice to fix)
- `path:line` - issue and impact

## Warnings (follow-up ticket)
- `path:line` - deferred risk

## Suggestions (follow-up ticket)
- `path:line` - optional improvement

## Positive Notes
- concrete strengths

## Summary Statistics
- Critical: {count}
- Major: {count}
- Minor: {count}
- Warnings: {count}
- Suggestions: {count}
```

## Rules

- Use concrete file paths and line references.
- Explain why each issue matters.
- Do not fix code in this step; report only.
- If no issues, state `No issues found` in `Critical`.
- Use one complete `write` call for final output.
