# Review: pt-qmhr

## Critical (must fix)
- No issues found.

## Major (should fix)
- `implementation.md:75` - Race condition in state file access: Multiple subagents reading/writing retry-state.json but no file locking specified. Could cause corruption when parallel workers > 1.
- `implementation.md:89-94` - Incomplete flag propagation: Flag table omits --dry-run, --create-followups, --simplify-tickets, --final-review-loop from current /tf behavior.
- `implementation.md:97-102` - Mid-chain resume ambiguity: Unclear how to detect phase completion status for smart resume.
- `implementation.md:107` - Flag handling incomplete: Missing --dry-run, --no-clarify, --create-followups, --simplify-tickets, --final-review-loop.
- `implementation.md:77,99,119` - Retry-state lifecycle inconsistent: "error" status mentioned but not in schema.
- `implementation.md:147` - Config option workflow.chainMode not in settings schema.

## Minor (nice to fix)
- `implementation.md:65` - Escalation context example missing reviewer-second-opinion model.
- `implementation.md:90,75` - chain-context.json introduced but not in state file table.
- `implementation.md:58-63` - Phase model override precedence unclear when frontmatter vs injected escalation conflict.
- `implementation.md:108-113` - Quality gate location confusion between tf-fix and tf-close.
- `implementation.md:170` - Missing rollback/cleanup for partial implementation failures.

## Warnings (follow-up ticket)
- `implementation.md:45` - Circular dependency risk: pt-qmhr blocks pt-74hd, but pt-74hd may depend on this design.
- `implementation.md:75-82` - State file bloat: attempts array grows unbounded.
- `implementation.md:156` - Backwards compatibility claim (chainMode: false) untested.
- `implementation.md:57` - No explicit concurrency safeguards for parallel workers > 1.

## Suggestions (follow-up ticket)
- `implementation.md:131-137` - Consider idempotency keys for phase execution.
- `implementation.md:75` - Consider append-only event log for auditability.
- `implementation.md:97` - Add explicit phase checksums for smart resume.
- `implementation.md:184` - Expand verification with mid-chain failure/corrupted state tests.
- `implementation.md:109` - Define flag precedence for conflicting flags (e.g., --no-research + --with-research).

## Summary Statistics
- Critical: 0
- Major: 6
- Minor: 5
- Warnings: 4
- Suggestions: 5

## Positive Notes
- Good architectural decision to keep retry/escalation centralized in orchestrator.
- Well-structured specification with clear state file table.
- Architecture aligns with acceptance criteria.
- Explicitly addresses mid-chain failure and quality gate integration.
