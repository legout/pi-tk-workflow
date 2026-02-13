# Review: pt-74hd

## Overall Assessment
The implementation correctly adds `skill: tf-workflow` frontmatter to all 5 phase prompts. However, several edge cases around chain execution safety, state management, and error handling could cause silent failures or data loss when these prompts are used in production workflows.

## Critical (must fix)
- `.pi/prompts/tf-implement.md:53` - The retry reset backup filename uses `{timestamp}` without format specification. If two resets occur within the same second, the previous backup is overwritten. Use `timestamp + random suffix` or append to a backups list instead.
- `.pi/prompts/tf-review.md:48-52` - The parallel reviewer fan-out assumes all reviewers complete successfully. There's no timeout or partial failure handling. If one reviewer hangs, the entire chain blocks indefinitely. Add explicit timeout guidance and handling for partial results.
- `.pi/prompts/tf-close.md:89-93` - The git commit step has no error handling for common failure modes: missing user.email/user.name, GPG signing failures, or pre-commit hooks rejecting the commit. A failed commit should not be silently ignored.

## Major (should fix)
- `.pi/prompts/tf-research.md:34` - Backwards compatibility migration path is vague ("migrate to {artifactDir}/research.md"). Specify whether to copy, move, or symlink, and what to do if both files exist with different content.
- `.pi/prompts/tf-implement.md:87-90` - The `files_changed.txt` tracking relies on the agent's memory. If the agent crashes mid-implementation, this file may be incomplete or missing, causing the close phase to miss files in the commit. Suggest atomic writes or intermediate checkpoints.
- `.pi/prompts/tf-fix.md:37-41` - The guidance to "fix in priority order" doesn't address what happens if a fix introduces new issues (regression). There's no rollback mechanism or re-review trigger after fixes are applied.
- `.pi/prompts/tf-close.md:32-36` - The post-fix verification manual fallback calculates `post_fix = max(0, pre_fix - fixed)` but this arithmetic assumes 1:1 fix-to-issue mapping. A single fix might resolve multiple issues, or one issue might require multiple fix attempts. The calculation could misrepresent actual quality gate status.

## Minor (nice to fix)
- `.pi/prompts/tf-review.md:62-66` - The deduplication logic ("file path + line number + description similarity") is underspecified. What similarity threshold? What if the same issue is described differently by two reviewers? Consider adding explicit guidance on fuzzy matching.
- `.pi/prompts/tf-close.md:101-105` - The retry state JSON structure is not documented. Different phases may write incompatible structures if not carefully coordinated. Consider providing a schema or example.
- `.pi/prompts/tf-research.md:18-20` - The `--no-research` and `--with-research` flags are documented but there's no guidance on what to do if both are provided (conflicting flags). Define precedence.

## Warnings (follow-up ticket)
- `.pi/prompts/tf-close.md:71` - The quality gate configuration (`workflow.failOn`) determines which severities block closure, but there's no validation that this configuration is sensible (e.g., blocking on Suggestions but not Critical would be a misconfiguration). Consider adding a config validation step.
- All prompts - The `skill: tf-workflow` frontmatter assumes this skill exists and is loadable. There's no graceful degradation if the skill is missing or renamed. The prompts would fail with potentially cryptic errors.

## Suggestions (follow-up ticket)
- `.pi/prompts/tf-review.md:44` - Consider adding a `maxReviewers` limit or circuit breaker pattern. If 10 reviewers are configured, the parallel execution could overwhelm rate limits or resource constraints.
- `.pi/prompts/tf-close.md:82-85` - The artifact staging uses `git add -A -- "{artifactDir}"` which could accidentally stage untracked files if the artifact directory overlaps with source directories. Consider using explicit file lists instead of directory adds.
- All phase prompts - Consider adding an `onError` or `cleanup` hook pattern for consistent error handling across the chain. Currently each phase implements its own error handling differently.

## Positive Notes
- Good frontmatter consistency across all 5 prompts with proper model/thinking/skill declarations
- Clear preservation rules for cross-phase artifacts ensure chain continuity
- The retry state mechanism shows good consideration for escalation workflows
- Well-structured markdown with clear section headers and execution flow

## Summary Statistics
- Critical: 3
- Major: 4
- Minor: 3
- Warnings: 2
- Suggestions: 3
