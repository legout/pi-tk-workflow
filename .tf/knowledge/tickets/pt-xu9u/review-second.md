# Review: pt-xu9u

## Overall Assessment
The retry escalation docs and the new tf.retry_state helper document a solid infrastructure, but there are two sequencing assumptions that will break the curve and treat interrupted attempts as if they were completed retries. These failures only surface when a run dies before closing or when escalation decisions are made before the new attempt is recorded, so they are easy to miss unless you focus on the edge cases.

## Critical (must fix)
- No issues found

## Major (should fix)
- `skills/tf-workflow/SKILL.md:137-149` + `tf/retry_state.py:224-369` - The doctrinal flow says attemptNumber equals len(attempts)+1 and describes resolving escalated models before performing the work, but RetryState.resolve_escalation only looks at self.get_attempt_number (which is just len(attempts)). If the workflow follows the doc literally and defers start_attempt until after it chooses models, the first retry still sees attempt 1 and the fixer never escalates, so the escalation curve never starts. Please either record the new attempt before asking resolve_escalation or make resolve_escalation accept the next attempt number (or add one internally) so attempt 2 actually chooses the stronger fixer as advertised.
- `skills/tf-workflow/SKILL.md:147-150` + `tf/retry_state.py:224-288` - The documentation explicitly says that an in_progress row should be resumed, but nothing in RetryState checks the previous attempt's status: start_attempt always appends a fresh entry and complete_attempt only updates the latest row. When /tf is cancelled or crashes before complete_attempt runs, the next invocation increments attemptNumber, escalates models, and bumps retryCount even though the ticket never actually finished the prior run. We need to detect attempts[-1]['status'] when loading and reuse or reset that row instead of unconditionally starting a new attempt so that aborted executions do not consume retries or trigger escalated models prematurely.

## Minor (nice to fix)
- No issues found

## Warnings (follow-up ticket)
- No issues found

## Suggestions (follow-up ticket)
- No issues found

## Positive Notes
- `tests/test_retry_state.py:604-654` thoroughly exercises escalation config loading, merging user data with defaults, and falling back when settings.json is invalid, which makes it easier to keep the new schema in sync with the documentation.

## Summary Statistics
- Critical: 0
- Major: 2
- Minor: 0
- Warnings: 0
- Suggestions: 0