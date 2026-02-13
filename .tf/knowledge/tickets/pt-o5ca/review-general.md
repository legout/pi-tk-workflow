# Review: pt-o5ca

## Overall Assessment
The decision document is clear and well-structured, and it provides concrete mapping examples for key `/tf` flags. However, it currently introduces compatibility regressions versus the existing `tf-workflow` contract around research enablement and retry reset behavior. Those two gaps should be resolved before downstream implementation tickets consume this design.

## Critical (must fix)
- No issues found.

## Major (should fix)
- `.tf/knowledge/tickets/pt-o5ca/implementation.md:44-46` - The proposed default mapping always includes `tf-research`, which conflicts with current behavior where research is conditional on `workflow.enableResearcher` unless `--with-research` is set (`skills/tf-workflow/SKILL.md:70-71`, `skills/tf-workflow/SKILL.md:231`). This breaks the stated backward-compatibility goal and can increase runtime/cost unexpectedly for configurations that intentionally disable research.
- `.tf/knowledge/tickets/pt-o5ca/implementation.md:88-90` - `--retry-reset` is marked as unsupported with no compatibility bridge, while current workflow explicitly supports it (`skills/tf-workflow/SKILL.md:75`, `skills/tf-workflow/SKILL.md:92-94`). Dropping this behavior risks operational regressions in retry/escalation flows and makes it harder to recover from stale retry state.

## Minor (nice to fix)
- `.tf/knowledge/tickets/pt-o5ca/implementation.md:45-46` - The design does not define precedence when both `--no-research` and `--with-research` are provided. Without an explicit rule, wrapper implementations may diverge, causing inconsistent behavior across environments.

## Warnings (follow-up ticket)
- `.tf/knowledge/tickets/pt-o5ca/implementation.md:79` - Post-chain actions are delegated to “wrapper (or closer phase)” without a strict sequencing contract for partial-chain failures. This is a maintainability risk: future implementers may trigger follow-up commands after failed/aborted chains unless failure gating is explicitly standardized.

## Suggestions (follow-up ticket)
- `.tf/knowledge/tickets/pt-o5ca/implementation.md:92-129` - Add a small flag-resolution test matrix (or executable examples) covering default, `--no-research`, `--with-research`, combined optional post-chain flags, and conflicting flags. This would reduce regressions in pt-mdl0 by making expected behavior unambiguous.

## Positive Notes
- The hybrid strategy cleanly separates chain selection from optional post-chain actions and is easy to reason about.
- The mapping tables and concrete command examples make the proposal implementation-friendly.
- Dependency links to pt-74hd / pt-qmhr / pt-mdl0 are clearly identified, which helps sequencing.

## Summary Statistics
- Critical: 0
- Major: 2
- Minor: 1
- Warnings: 1
- Suggestions: 1
