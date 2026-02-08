# Manual Test Recipe: /tf-followups-scan

This document provides a practical verification checklist for testing `/tf-followups-scan` behavior.

## Prerequisites

- `tk` CLI installed and functional
- `/tf-followups-scan` prompt configured in `.pi/prompts/`
- Sample ticket directories under `.tf/knowledge/tickets/`

---

## Test Case 1: Dry-Run Mode (Default)

**Purpose:** Verify dry-run produces no side effects.

**Steps:**

1. Ensure at least one ticket directory exists with:
   - `close-summary.md` present (indicates implemented)
   - `review.md` with some Warnings/Suggestions
   - **No** `followups.md` (clean state for test)

2. Run:
   ```bash
   /tf-followups-scan
   ```

3. **Verify:**
   - [ ] Output shows `[DRY-RUN]` prefix for actions
   - [ ] No new tickets appear in `tk list`
   - [ ] No `followups.md` files were created
   - [ ] Summary shows counts but no actual changes

---

## Test Case 2: Apply Mode - Creates Tickets and Artifacts

**Purpose:** Verify `--apply` actually creates tickets and writes files.

**Steps:**

1. Set up a test ticket directory:
   ```bash
   mkdir -p .tf/knowledge/tickets/test-scan-001
   ```

2. Create `close-summary.md`:
   ```markdown
   # Close Summary: test-scan-001

   ## Status
   COMPLETE

   ## Commit
   abc1234
   ```

3. Create `review.md` with sample warnings:
   ```markdown
   # Review: test-scan-001

   ## Warnings
   - `src/utils.py:42` - Consider caching this expensive operation

   ## Suggestions
   - Add docstrings to public functions
   ```

4. Run (dry-run first):
   ```bash
   /tf-followups-scan
   ```

5. **Verify dry-run output:**
   - [ ] Shows ticket `test-scan-001` as eligible
   - [ ] Shows 1 Warning and 1 Suggestion would be processed
   - [ ] No files created yet

6. Run with apply:
   ```bash
   /tf-followups-scan --apply
   ```

7. **Verify:**
   - [ ] `followups.md` exists in `.tf/knowledge/tickets/test-scan-001/`
   - [ ] `tk list` shows 2 new follow-up tickets (tags: `tf,followup`)
   - [ ] Ticket descriptions reference `test-scan-001`

8. **Clean up test tickets:**
   ```bash
   tk delete <followup-ticket-id-1>
   tk delete <followup-ticket-id-2>
   rm -rf .tf/knowledge/tickets/test-scan-001
   ```

---

## Test Case 3: Idempotency - Second Run Does Nothing

**Purpose:** Verify re-running skips already-processed tickets.

**Steps:**

1. Use an existing ticket that already has `followups.md`:
   ```bash
   ls .tf/knowledge/tickets/*/followups.md
   ```

2. Run:
   ```bash
   /tf-followups-scan
   ```

3. **Verify:**
   - [ ] Ticket appears in "Skipped" count
   - [ ] No `[DRY-RUN]` lines for that ticket
   - [ ] Output indicates "already have followups.md"

4. Run with `--apply`:
   ```bash
   /tf-followups-scan --apply
   ```

5. **Verify:**
   - [ ] Same skipped count
   - [ ] No duplicate tickets created
   - [ ] `followups.md` unchanged (check timestamp)

---

## Test Case 4: No Review.md - Graceful Handling

**Purpose:** Verify tickets without `review.md` are handled gracefully.

**Steps:**

1. Create test directory:
   ```bash
   mkdir -p .tf/knowledge/tickets/test-no-review
   ```

2. Create only `close-summary.md` (no `review.md`):
   ```markdown
   # Close Summary: test-no-review
   Status: COMPLETE
   ```

3. Run:
   ```bash
   /tf-followups-scan --apply
   ```

4. **Verify:**
   - [ ] Ticket is eligible (has close-summary, no followups)
   - [ ] `followups.md` is created with "No review.md present" note
   - [ ] No crash or error
   - [ ] No tickets created (nothing to create from)

5. **Clean up:**
   ```bash
   rm -rf .tf/knowledge/tickets/test-no-review
   ```

---

## Test Case 5: Empty Review - "None Needed" Record

**Purpose:** Verify empty reviews (no Warnings/Suggestions) produce proper record.

**Steps:**

1. Create test directory:
   ```bash
   mkdir -p .tf/knowledge/tickets/test-empty-review
   ```

2. Create `close-summary.md` and empty `review.md`:
   ```markdown
   # Review: test-empty-review

   ## Critical
   - (none)

   ## Major
   - (none)

   ## Minor
   - (none)

   ## Warnings
   - (none)

   ## Suggestions
   - (none)
   ```

3. Run:
   ```bash
   /tf-followups-scan --apply
   ```

4. **Verify:**
   - [ ] `followups.md` created with "No follow-ups needed" message
   - [ ] No tickets created
   - [ ] Ticket won't be re-processed on future runs

5. **Clean up:**
   ```bash
   rm -rf .tf/knowledge/tickets/test-empty-review
   ```

---

## Test Case 6: Multiple Tickets - Batch Processing

**Purpose:** Verify scan handles multiple tickets correctly.

**Steps:**

1. Create 3 test tickets with varying states:
   - `test-batch-1`: Has close-summary + review with warnings (no followups)
   - `test-batch-2`: Has close-summary + review with warnings (no followups)
   - `test-batch-3`: Has close-summary + review (already has followups.md)

2. Run:
   ```bash
   /tf-followups-scan
   ```

3. **Verify summary format:**
   ```
   === Follow-ups Scan Summary ===
   Scanned: 3 ticket directories
   Eligible: 2 tickets
   Processed: 2 tickets
     - Follow-up tickets would be created: N
   Skipped: 1 tickets (already have followups.md)
   ```

4. Run with `--apply` and verify all 3 tickets handled correctly.

5. **Clean up test artifacts.**

---

## Regression Checklist

Before marking `/tf-followups-scan` as verified:

- [ ] Dry-run mode never creates side effects
- [ ] `--apply` creates tickets with correct tags (`tf,followup`)
- [ ] `--apply` creates tickets with correct priority (3)
- [ ] Second run on same tickets is a no-op
- [ ] Tickets without `close-summary.md` are not processed
- [ ] Tickets with existing `followups.md` are skipped
- [ ] Summary output is clear and accurate
- [ ] Created `followups.md` files follow the format spec

---

## Notes for Maintainers

- These tests are **manual** by design for MVP
- No brittle end-to-end automation required
- Test directories can be created/deleted safely - they won't conflict with real tickets
- Use `test-*` prefix for all test ticket IDs to make cleanup easy
