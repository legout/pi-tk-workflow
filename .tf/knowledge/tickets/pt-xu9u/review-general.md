# Review: pt-xu9u

## Overall Assessment
The retry-escalation documentation now captures state updates and triggers in detail, but the workflow cannot run as described because the agent lookup uses names that don't exist in the config and the new config block itself is absent. These two gaps make the escalation path both crash and impossible to configure before any review or close logic executes.

## Critical (must fix)
- `skills/tf-workflow/SKILL.md:150-161` & `.tf/config/settings.json:44-52` - The Load Retry State instructions say to resolve base models by reading `agents.{role}` and the escalation table uses camelCase keys such as `reviewerSecondOpinion`, but the `agents` map only contains `reviewer-second-opinion` (hyphenated). Following the document verbatim causes `agents['reviewerSecondOpinion']` to be missing, so the workflow cannot even determine the reviewer-second-opinion base model and will crash before escalation can happen. The doc needs to use the agent names that actually exist in `settings.json` (or explain how to map camelCase keys to the hyphenated agent IDs) so the reader can write working code.

## Major (should fix)
- `skills/tf-workflow/SKILL.md:46-64` & `.tf/config/settings.json:126-155` - The config section introduces `workflow.escalation` and all retry logic depends on `workflow.escalation.enabled`, `maxRetries`, and the model overrides, but `.tf/config/settings.json` does not define a `workflow.escalation` block at all. Without that block there is no way to enable the feature, the workflow will see `workflow.escalation` as undefined, and `maxRetries` cannot be tuned. Please add a default `workflow.escalation` object (matching the schema described later) or guard the code so that missing config values don’t break the workflow.

## Minor (nice to fix)
- `skills/tf-workflow/SKILL.md:674-695` - The “Parallel Worker Safety” guidance is duplicated twice in a row, which makes the doc harder to maintain and could lead to diverging edits. Deduplicate the repeated paragraph so there is a single authoritative description of the locking/disable options.

## Warnings (follow-up ticket)
- No issues found

## Suggestions (follow-up ticket)
- No issues found

## Positive Notes
- `skills/tf-workflow/SKILL.md:457-503` documents retry-state updates with atomic writes, quality-gate counts, and escalated-model metadata, giving implementers clear guidance on how to keep the state consistent even when retries are blocked.

## Summary Statistics
- Critical: 1
- Major: 1
- Minor: 1
- Warnings: 0
- Suggestions: 0
