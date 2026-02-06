# Implementation: pt-1fsy

## Summary
Implemented rubric-based priority classifier with comprehensive P0-P4 classification rules and rationale generation for the `tf priority-reclassify` command.

## Files Changed

### 1. `tf_cli/priority_reclassify_new.py` (Complete Rewrite)
**Changes:**
- Added `ClassificationResult` dataclass to hold priority, bucket, reason, and confidence
- Implemented comprehensive `RUBRIC` dictionary with 5 priority levels covering:
  - **P0 (critical-risk)**: Security, data loss, OOM/crashes, compliance violations
  - **P1 (high-impact)**: User-facing bugs, performance issues, release blockers
  - **P2 (product-feature)**: Standard product features, integrations
  - **P3 (engineering-quality)**: Refactors, DX, CI/CD, observability
  - **P4 (maintenance-polish)**: Docs, cosmetics, typing, minor cleanup
- Added `TAG_MAP` for tag-based classification (tags take precedence)
- Added `TYPE_DEFAULTS` for fallback when no keywords match
- Implemented `classify_priority_full()` returning complete classification result
- Maintained backward-compatible `classify_priority()` returning (priority, reason) tuple
- Added `--include-unknown` flag to show/skip ambiguous tickets
- Updated output table to include rubric bucket column
- Enhanced audit trail with bucket and confidence columns
- Conservative classification: prefers "unknown" over wrong changes

## Key Decisions

### 1. Backward Compatibility
- Kept `classify_priority(ticket) -> (priority, reason)` signature for existing tests
- Added new `classify_priority_full()` for complete results with bucket/confidence

### 2. Classification Precedence
1. **Tags first** - Explicit intent via tags takes highest precedence
2. **P0/P1/P2 keywords** - Critical/important issues detected via keywords
3. **P4 over P3** - For maintenance keywords, prefer lower priority (conservative)
4. **Type defaults** - Use ticket type as low-confidence fallback
5. **Unknown** - Return "unknown" when no indicators found

### 3. Conservative Rules
- Ambiguous tickets return "unknown" instead of guessing
- Skipped by default (use `--include-unknown` to show)
- Multiple indicators use highest priority for P0-P2 (safety-critical)
- P3/P4 conflicts prefer P4 (maintenance over engineering work)

## Tests Run
```bash
$ pytest tests/test_priority_reclassify.py -v
26 passed

$ pytest tests/ -v
372 passed
```

## Verification
Run the classifier on ready tickets:
```bash
tf priority-reclassify --ready
tf priority-reclassify --ready --include-unknown  # show ambiguous tickets
```

## Acceptance Criteria Checklist
- [x] Rules cover: security, data correctness, OOM/resource risk, product features, eng quality/workflow, cosmetics/docs
- [x] Output includes: current priority, proposed priority, rubric bucket, and reason
- [x] Ambiguous tickets return "unknown" and are skipped by default
- [x] Rules are conservative (prefer unknown over wrong changes)
