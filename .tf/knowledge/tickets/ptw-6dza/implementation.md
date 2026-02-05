# Implementation: ptw-6dza

## Summary
Enhanced `/tf-backlog` (seed mode) to infer and apply ticket dependencies via `tk dep`. Added a `--no-deps` escape hatch and implemented hint-based ordering for logical task sequences.

## Files Changed
- `prompts/tf-backlog.md` - Updated Usage section with `--no-deps` flag, added Options section, and expanded dependency inference to include seed mode with default chain and hint-based overrides
- `skills/tf-planning/SKILL.md` - Updated Backlog Generation procedure (step 9) to include seed mode dependency inference with conservative default chain and keyword-based ordering hints

## Key Decisions
1. **Default chain approach**: Implemented a simple linear dependency chain (ticket N depends on ticket N-1) as the conservative default for seed backlogs. This ensures `tk ready` and `tk blocked` show a meaningful work order immediately after backlog creation.

2. **Hint-based override**: Added keyword detection ("setup", "configure", "define", "design", "implement", "test") to allow logical reordering when the seed content suggests a different sequence than creation order.

3. **Escape hatch**: Added `--no-deps` flag to allow users to opt out of automatic dependency inference when they want full manual control.

4. **Conservative principle**: The implementation prioritizes fewer/correct deps over potentially wrong deps. If the order is ambiguous, it falls back to the default chain.

## Changes Detail

### prompts/tf-backlog.md
- Added `[--no-deps]` to Usage syntax
- Added Options section documenting `--no-deps` flag
- Rewrote step 7 (Infer dependencies) to:
  - Separate logic for Plan mode, Seed mode, and Baseline mode
  - Document default chain for seed mode
  - Document hint-based keyword override
  - Keep baseline mode unchanged (skip deps unless explicitly stated)

### skills/tf-planning/SKILL.md
- Rewrote step 9 (Infer dependencies) to:
  - Structure as separate sections for each mode
  - Add seed mode logic with default chain and hint-based override
  - Document keyword hierarchy: Setup/Configure → Define/Design → Implement → Test
  - Emphasize conservative approach (prefer default chain over uncertain deps)

## Tests Run
- Verified file syntax with grep/read commands
- Confirmed markdown structure is valid
- Checked that both files have consistent changes

## Verification
1. Run `/tf-backlog seed-<topic>` and verify dependencies are created in order
2. Run `/tf-backlog seed-<topic> --no-deps` and verify no dependencies are created
3. Check that `tk ready` shows tickets in dependency order after backlog creation
