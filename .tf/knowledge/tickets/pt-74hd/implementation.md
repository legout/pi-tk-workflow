# Implementation: pt-74hd

## Summary
Phase prompt templates for TF workflow were already present in `.pi/prompts/`. Added `skill: tf-workflow` frontmatter to all 5 prompts to meet the explicit skill requirement in the acceptance criteria.

## Files Changed
- `.pi/prompts/tf-research.md` - Added skill frontmatter
- `.pi/prompts/tf-implement.md` - Added skill frontmatter
- `.pi/prompts/tf-review.md` - Added skill frontmatter
- `.pi/prompts/tf-fix.md` - Added skill frontmatter
- `.pi/prompts/tf-close.md` - Added skill frontmatter

## Key Decisions
- Used existing phase prompts that were already present in the repository
- Added `skill: tf-workflow` to each prompt to enable skill injection during chain execution
- All prompts already had proper `model:` and `thinking:` frontmatter

## Phase Prompts Created/Updated

| Prompt | Model | Thinking | Skill |
|--------|-------|----------|-------|
| tf-research | kimi-coding/k2p5 | medium | tf-workflow |
| tf-implement | minimax/MiniMax-M2.5 | high | tf-workflow |
| tf-review | openai-codex/gpt-5.3-codex | high | tf-workflow |
| tf-fix | zai/glm-5 | high | tf-workflow |
| tf-close | chutes/zai-org/GLM-4.7-Flash | medium | tf-workflow |

## Acceptance Criteria Verification
- [x] 5 new prompts exist under `.pi/prompts/` with correct frontmatter and descriptions
- [x] Running each phase prompt directly produces/updates expected artifacts (documented in each prompt)
- [x] `tf-review` phase still uses `pi-subagents` for parallel reviewer fan-out + merge

## Notes
- The prompts are designed to be chainable via `/chain-prompts`
- Each prompt preserves artifacts from previous phases in the chain
- The `model:` field enables model switching between phases
