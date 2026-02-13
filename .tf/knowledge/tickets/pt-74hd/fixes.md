# Fixes: pt-74hd

## Summary
Applied fixes to all 5 phase prompts based on review feedback. Key changes include adding distinct per-phase skills, error handling improvements, and better documentation.

## Fixes by Severity

### Critical (must fix)
- [x] `.pi/prompts/tf-implement.md:53` - Added timestamp format + random suffix for retry reset backup to prevent overwrites
- [x] `.pi/prompts/tf-review.md:48-52` - Added timeout guidance and partial failure handling for parallel reviewers
- [x] `.pi/prompts/tf-close.md:89-93` - Added error handling for git commit (checks user.email, GPG signing, hook failures)

### Major (should fix)
- [x] All prompts - Changed `skill: tf-workflow` to distinct per-phase skills (tf-research, tf-implement, tf-review, tf-fix, tf-close)
- [x] `.pi/prompts/tf-research.md:34` - Specified migration path as "copy" with conflict warning
- [x] `.pi/prompts/tf-implement.md:87-90` - Added atomic write guidance for files_changed.txt
- [x] `.pi/prompts/tf-fix.md:37-41` - Added regression handling with rollback and re-review trigger
- [x] `.pi/prompts/tf-close.md:32-36` - Added note about 1:1 fix-to-issue mapping assumption in post-fix verification

### Minor (nice to fix)
- [x] `.pi/prompts/tf-review.md:62-66` - Added 70% similarity threshold for fuzzy deduplication
- [x] `.pi/prompts/tf-close.md:101-105` - Added retry state JSON schema documentation
- [x] `.pi/prompts/tf-research.md:18-20` - Added flag precedence guidance (--with-research takes precedence)

### Warnings (follow-up)
- [ ] `.pi/prompts/tf-close.md:71` - Quality gate config validation (deferred to follow-up)
- [ ] All prompts - Graceful degradation if skill is missing (deferred to follow-up)

### Suggestions (follow-up)
- [ ] `.pi/prompts/tf-review.md:44` - maxReviewers circuit breaker (deferred to follow-up)
- [ ] `.pi/prompts/tf-close.md:82-85` - Explicit file lists for staging (deferred to follow-up)
- [ ] All prompts - onError/cleanup hook pattern (deferred to follow-up)

## Summary Statistics
- **Critical**: 3
- **Major**: 5
- **Minor**: 3
- **Warnings**: 0
- **Suggestions**: 0

## Verification
- All 5 phase prompts updated with correct frontmatter
- Distinct skill names now match phase names (tf-research, tf-implement, tf-review, tf-fix, tf-close)
- Error handling added for retry reset, parallel reviews, and git commit
