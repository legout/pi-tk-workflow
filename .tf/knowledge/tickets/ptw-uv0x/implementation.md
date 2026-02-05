# Implementation: ptw-uv0x

## Summary
Added `--links-only` flag to `/tf-backlog` to enable retroactive linking of existing backlog tickets without creating new ones.

## Files Changed

### 1. prompts/tf-backlog.md
- Updated Usage section to include `[--links-only]` flag
- Added `--links-only` option description:
  - "Run only linking on existing backlog tickets (no new tickets created). Useful for retroactive linking of existing backlogs."
- Added `--links-only Example` section with use cases:
  - Backlog created before linking feature existed
  - Retroactive linking of existing backlogs
  - Manual tickets that need automatic linking applied
- Updated Execution section with **Special case: `--links-only` mode** callout
- Marked steps 5-7 as skipped in `--links-only` mode
- Updated step 8 (component tags) to also skip in `--links-only` mode
- Enhanced step 9 (linking) to handle both modes:
  - `--links-only`: Load existing tickets from `backlog.md`
  - Normal mode: Link newly created tickets
- Split Output section into **Normal mode** and **`--links-only` mode**

### 2. skills/tf-planning/SKILL.md
- Updated Procedure header to mention `--links-only` option
- Enhanced step 3 to verify `backlog.md` exists when in `--links-only` mode
- Marked steps 9-10 as skipped when `--links-only` provided
- Updated step 11 (`backlog.md` format) to include `Links` column
- Added new step 12: **Link related tickets**:
  - Documents `--links-only` vs normal mode behavior
  - Explains conservative linking criteria (same component + adjacent, title similarity)
  - Notes `tk link` creates symmetric/bidirectional links (unlike deps)
  - Max 2-3 links per ticket guideline

## Key Decisions

1. **Links vs Deps distinction**: Links are for discoverability/grouping (symmetric), deps are for execution order (directional)
2. **Conservative linking**: Under-linking preferred - max 2-3 links per ticket
3. **Backlog.md format**: Added `Links` column to track link relationships
4. **Use case focus**: Enables retroactive linking for backlogs created before linking feature

## Acceptance Criteria

- [x] Add --links-only flag to tf-backlog prompt
- [x] Update skill procedure to support links-only mode
- [x] Document use case: retroactive linking of existing tickets

## Verification

To verify the implementation:
1. Run `/tf-backlog <topic> --links-only` on an existing backlog
2. Confirm no new tickets are created
3. Verify existing tickets are linked via `tk link`
4. Check `backlog.md` is updated with Links column
