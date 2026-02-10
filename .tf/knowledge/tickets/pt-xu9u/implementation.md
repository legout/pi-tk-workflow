# Implementation: pt-xu9u

## Summary
Implemented retry-aware escalation in the /tf workflow by updating the tf-workflow SKILL.md with comprehensive retry state management, model escalation logic, and detection algorithms.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Files Changed
- `skills/tf-workflow/SKILL.md` - Added retry-aware escalation support
  - Added `--retry-reset` flag handling
  - Updated Re-Anchor Context to load retry state and detect BLOCKED attempts
  - Added Load Retry State sub-procedure with detection algorithms
  - Updated Implement to record attempt number and escalated models
  - Updated Parallel Reviews to use escalated reviewer-second-opinion model
  - Updated Fix Issues to use escalated fixer model
  - Updated Close Ticket to update retry-state.json with attempt results
  - Added Retry Escalation configuration section
  - Updated Output Artifacts to include retry-state.json
- `.pi/skills/tf-workflow/SKILL.md` - Synced changes

## Key Decisions
1. **Escalation is opt-in**: Default `enabled: false` - no behavior change unless explicitly configured
2. **Null means base model**: Escalation config uses `null` to mean "use base model from agents config"
3. **Detection order**: Primary detection from close-summary.md (explicit BLOCKED status), fallback to review.md failOn counts
4. **Reset policy**: Counter resets only on successful close (CLOSED status)
5. **State location**: Co-located with ticket artifacts at `{artifactDir}/retry-state.json`

## Escalation Curve Implemented
- Attempt 1: Base models (no escalation)
- Attempt 2: Escalate fixer model only
- Attempt 3+: Escalate fixer + reviewer-second-opinion (+ worker if configured)

## Detection Algorithms
- Primary: Parse close-summary.md for explicit `## Status\n**BLOCKED**` pattern
- Fallback: Parse review.md for nonzero counts in failOn severities
- Status normalized to lowercase for consistency

## Tests Run
- N/A - Documentation/skill update

## Verification
- Verified SKILL.md structure and cross-references
- Confirmed escalation config schema matches settings.json
- Verified retry-state.json schema matches pt-te9b specification
