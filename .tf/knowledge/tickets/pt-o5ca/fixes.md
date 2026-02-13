# Fixes: pt-o5ca

## Summary
Fixed two Major issues identified in review:
1. Default chain now respects `workflow.enableResearcher` config (not always including tf-research)
2. Added partial support documentation for `--retry-reset` flag

## Fixes by Severity

### Critical (must fix)
- No critical issues found.

### Major (should fix)
- [x] `.tf/knowledge/tickets/pt-o5ca/implementation.md:44-46` - Fixed default mapping to be config-dependent: now reads `workflow.enableResearcher` from config and selects appropriate chain. Added explicit flag precedence rules.
- [x] `.tf/knowledge/tickets/pt-o5ca/implementation.md:88-90` - Added partial support documentation for `--retry-reset`, noting it passes to closer phase and acknowledging full mid-chain retry support depends on pt-qmhr.

### Minor (nice to fix)
- [x] `.tf/knowledge/tickets/pt-o5ca/implementation.md:45-46` - Added explicit flag precedence rule: "If both --no-research and --with-research are provided, error or warn and use --with-research"

### Warnings (follow-up)
- Not fixed (deferred to follow-up): Post-chain actions lack strict sequencing contract for partial-chain failures

### Suggestions (follow-up)
- Not fixed (deferred to follow-up): Add flag-resolution test matrix

## Summary Statistics
- **Critical**: 0
- **Major**: 2
- **Minor**: 1
- **Warnings**: 1
- **Suggestions**: 1

## Verification
- Re-read implementation.md to verify fixes are properly integrated
- Flag precedence rules now explicitly documented
- --retry-reset documented with pt-qmhr dependency noted
