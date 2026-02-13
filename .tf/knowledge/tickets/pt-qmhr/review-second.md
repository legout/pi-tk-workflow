# Review: pt-qmhr

## Overall Assessment
The design for chain-prompt retry/escalation handling demonstrates solid architectural thinking with a pragmatic hybrid approach. The decision to centralize state management in an orchestrator while delegating phase execution to subagents is sound. However, several edge cases around state consistency, failure recovery, and configuration interactions need attention before implementation.

## Critical (must fix)
No issues found

## Major (should fix)

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:75` - **Race condition in state file access**: The design specifies multiple subagents reading/writing `retry-state.json` but doesn't specify file locking mechanisms. If tf-fix and tf-close both attempt to read/update state concurrently, corruption is likely. **Impact**: Retry count could be lost or duplicated, leading to incorrect escalation decisions.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:89-94` - **Incomplete flag propagation**: The flag handling table covers 5 flags but `/tf` prompt (as shown in .pi/prompts/tf.md) supports additional flags like `--create-followups`, `--simplify-tickets`, `--final-review-loop`, `--dry-run`. **Impact**: These flags may not propagate correctly through the chain, causing inconsistent behavior between chain-mode and switch_model-mode.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:97-102` - **Mid-chain resume ambiguity**: The design states "State stays 'active' for resume" but doesn't specify how to detect whether a phase completed successfully or partially. **Impact**: Re-running `/tf` could skip phases that partially ran or re-run phases that already completed, causing duplicate work or missed steps.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:147` - **Config option not in settings schema**: The `workflow.chainMode` option is proposed but the existing settings.json (shown in docs context) doesn't include this key. **Impact**: Adding this without schema validation could cause silent failures or unexpected defaults.

## Minor (nice to fix)

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:58-63` - **Phase model override precedence unclear**: When a phase prompt declares `model: X` in frontmatter but the orchestrator injects escalated model `Y`, which wins? **Impact**: Inconsistent model selection could lead to unexpected costs or capability mismatches.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:108-113` - **Quality gate location confusion**: The design places quality gate checks in "tf-fix → tf-close transition" but also mentions tf-close reads verification. Current implementation (per docs/retries-and-escalation.md) has quality gate in the close phase. **Impact**: Unclear responsibility boundary may lead to gate checks being missed or duplicated.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:170` - **Missing rollback specification**: If tf-implement fails after writing files but before completing, there's no mention of cleanup. **Impact**: Partial implementations may leave the codebase in an inconsistent state.

## Warnings (follow-up ticket)

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:45` - **Circular dependency risk**: This ticket (pt-qmhr) blocks on pt-74hd, but pt-74hd's implementation may depend on this design being finalized. **Impact**: Potential deadlock in ticket scheduling. Recommend: Create explicit dependency resolution ticket to sequence work properly.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:75-82` - **State file bloat over time**: The `attempts` array grows unbounded with each retry. **Impact**: Large retry-state.json files could impact performance. Recommend: Add retention policy (e.g., keep only last N attempts) in implementation ticket.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:156` - **Backwards compatibility claim untested**: The claim that `chainMode: false` preserves current behavior requires validation across all flag combinations. **Impact**: Subtle behavior differences could break existing workflows. Recommend: Add regression test ticket.

## Suggestions (follow-up ticket)

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:131-137` - **Consider idempotency keys**: For phase execution, add idempotency keys so re-running a phase with the same inputs produces deterministic outputs. **Impact**: Safer retries and better caching potential.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:75` - **Consider append-only event log**: Instead of updating retry-state.json in place, consider an append-only event log pattern for better auditability and crash recovery. **Impact**: Easier debugging and state reconstruction after failures.

- `.tf/knowledge/tickets/pt-qmhr/implementation.md:97` - **Add explicit phase checksums**: Track checksums of input artifacts for each phase to enable smart resume (skip if inputs unchanged). **Impact**: Faster retries by avoiding redundant work.

## Positive Notes

- **Good architectural decision**: Rejecting the "pure chain-prompts" alternative demonstrates sound judgment about complexity vs. benefit tradeoffs.
- **Well-structured specification**: The state files table clearly documents the data flow between phases.
- **Backwards compatibility consideration**: Including the `chainMode` toggle shows awareness of migration concerns.
- **Acceptance criteria are testable**: The checklist format with verifiable items will make validation straightforward.
- **Clear phase separation**: Using subagents for phases while keeping orchestration centralized is a good separation of concerns.

## Summary Statistics
- Critical: 0
- Major: 4
- Minor: 3
- Warnings: 3
- Suggestions: 3
