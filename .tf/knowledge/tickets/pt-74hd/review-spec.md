# Review: pt-74hd

## Overall Assessment
The updated phase prompts now include skill frontmatter and preserve the detailed artifact-writing guidance for each step, but they all still point at the shared `tf-workflow` skill instead of the distinct per-phase personas the approved plan requires.

## Critical (must fix)
- No issues found

## Major (should fix)
- `.pi/prompts/tf-research.md:5`, `.pi/prompts/tf-implement.md:5`, `.pi/prompts/tf-review.md:5`, `.pi/prompts/tf-fix.md:5`, `.pi/prompts/tf-close.md:5` – Every prompt currently declares `skill: tf-workflow`, whereas plan-replace-pi-model-switch-extension `plan.md:20-26` explicitly requires each phase to expose its own skill (`tf-research`, `tf-implement`, `tf-review`, `tf-fix`, `tf-close`). The plan’s key insight is that the chain runs different personas per phase, so pointing every prompt at `tf-workflow` violates the specification and prevents per-phase behavior or configuration that would rely on those unique skills.

## Minor (nice to fix)
- No issues found

## Warnings (follow-up ticket)
- No issues found

## Suggestions (follow-up ticket)
- No issues found

## Positive Notes
- `.pi/prompts/tf-implement.md:12-116` retains explicit instructions for artifact creation, retry handling, and quality checks so that the implementation phase still writes `implementation.md`, `ticket_id.txt`, and `files_changed.txt` in the expected format.
- `.pi/prompts/tf-review.md:47-122` documents the required `pi-subagents` fan-out/merge pattern and consolidates inputs from all reviewers, satisfying the acceptance criteria that `tf-review` continues to use the parallel review + merge workflow.

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 0
- Warnings: 0
- Suggestions: 0
