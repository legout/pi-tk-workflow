# Research: pt-1fsy

## Status
Research completed using existing project knowledge base.

## Context Reviewed

### 1. Priority Rubric Documentation
- **Location**: `.tf/knowledge/topics/priority-rubric.md`
- **Content**: Canonical P0-P4 mapping with detailed classification keywords

**Key Rubric Categories:**
| Priority | Numeric | Categories |
|----------|---------|------------|
| P0 | 0 | Security, data loss, corruption, OOM, crashes, compliance violations |
| P1 | 1 | User-facing bugs, performance issues, release blockers, regressions |
| P2 | 2 | Product features, enhancements, integrations (default for new work) |
| P3 | 3 | Engineering quality, DX, CI/CD, observability, testing |
| P4 | 4 | Docs, cosmetics, typing, style, minor refactors |

### 2. Existing Implementation
- **File**: `tf_cli/priority_reclassify_new.py`
- **Status**: Basic implementation exists with simple keyword matching
- **Missing**: Rubric bucket output, "unknown" classification, comprehensive keyword coverage

### 3. Test Requirements
- **File**: `tests/test_priority_reclassify.py`
- Tests expect: `classify_priority(ticket) -> (priority, reason)`
- Coverage: P0 security/crash, P1 blocker, P2 feature, P3 performance, P4 docs/refactor

### 4. CLI Integration
- Command registered in `cli.py` as `priority-reclassify`
- Args: `--apply`, `--ids`, `--ready`, `--status`, `--tag`, `--include-closed`

## Implementation Approach

1. **Expand rubric rules** to match full priority-rubric.md specification
2. **Add rubric bucket** field to output (security/data/etc)
3. **Add "unknown" classification** for ambiguous tickets
4. **Add skip behavior** for unknown priorities (with flag to override)
5. **Ensure conservative classification** - prefer unknown over wrong changes

## Sources
- `.tf/knowledge/topics/priority-rubric.md`
- `tf_cli/priority_reclassify_new.py` (existing)
- `tests/test_priority_reclassify.py` (test requirements)
- `tf_cli/cli.py` (command registration)
