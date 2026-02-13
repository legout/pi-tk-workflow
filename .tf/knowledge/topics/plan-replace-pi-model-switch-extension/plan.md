---
id: plan-replace-pi-model-switch-extension
status: approved
last_updated: 2026-02-13
---

# Plan: Replace pi-model-switch with /chain-prompts

Replace the runtime `switch_model` extension (`pi-model-switch`) in pi-ticketflow with the `/chain-prompts` feature from `pi-prompt-template-model`. This simplifies the required extensions from 3 to 2 while maintaining the full IRF (Implement → Review → Fix → Close) workflow.

The key insight is that each phase prompt declares its own model/skill/thinking in frontmatter, so runtime switching becomes unnecessary. **Skills contain detailed procedures; prompts are thin wrappers.**

## Inputs / Related Topics

- Root Seed: [seed-replace-pi-model-switch-extension-by](topics/seed-replace-pi-model-switch-extension-by/seed.md)
- Session: seed-replace-pi-model-switch-extension-by@2026-02-13T14-17-29Z
- Related Spikes:
  - [spike-chain-prompts-prompt-template](topics/spike-chain-prompts-prompt-template/spike.md)

## Requirements

### 1. Phase Skills (Project-Level)

Create detailed skills in `skills/` directory for each workflow phase:

- `skills/tf-research/SKILL.md` - Research procedure (context loading, research execution, artifact writing)
- `skills/tf-implement/SKILL.md` - Implementation procedure (coding, quality checks, artifact writing)
- `skills/tf-review/SKILL.md` - Shared reviewer subagent contract
- `skills/tf-review-phase/SKILL.md` - Review phase orchestration (parallel subagents + merge)
- `skills/tf-fix/SKILL.md` - Fix procedure (issue analysis, fixes, artifact writing)
- `skills/tf-close/SKILL.md` - Close procedure (quality gate, commit, close)

### 2. Phase Prompts (Project-Level)

Create thin prompt wrappers in `prompts/` directory with frontmatter:

| Prompt | Model | Thinking | Skill |
|--------|-------|----------|-------|
| `prompts/tf-research.md` | kimi-coding/k2p5 | medium | tf-research |
| `prompts/tf-implement.md` | minimax/MiniMax-M2.5 | high | tf-implement |
| `prompts/tf-review.md` | openai-codex/gpt-5.3-codex | high | tf-review-phase |
| `prompts/tf-fix.md` | zai/glm-5 | high | tf-fix |
| `prompts/tf-close.md` | chutes/zai-org/GLM-4.7-Flash | medium | tf-close |

Each prompt is a thin wrapper that:
- Declares model/thinking/skill in frontmatter
- References the skill procedure
- Specifies input/output artifacts

### 3. Reviewer Agents (Keep Existing)

Keep existing agents in `agents/` for parallel reviews:
- `agents/reviewer-general.md`
- `agents/reviewer-spec-audit.md`
- `agents/reviewer-second-opinion.md`

These are needed for `pi-subagents` parallel execution with different models.

### 4. Deterministic Entry Point (`tf` Python tooling)

Keep `/tf` as the user-facing command, but delegate orchestration to Python tooling:

```bash
# Prompt wrapper
/tf ...

# Deterministic backend
tf irf <ticket-id> [flags]
```

`tf irf` is responsible for:
- strict flag parsing and validation
- config-aware research entry selection
- deterministic `/chain-prompts` command construction
- post-chain command execution only on successful chain completion

### 5. Flag Handling

| Flag | Behavior |
|------|----------|
| `--no-research` | Start chain at `tf-implement` |
| `--with-research` | Start chain at `tf-research` (default) |
| `--create-followups` | Post-chain: run `tf-followups` |
| `--simplify-tickets` | Post-chain: run `simplify` |
| `--final-review-loop` | Post-chain: run `review-start` |

### 6. Remove Dependency

Remove `pi-model-switch` from required extensions list in docs/setup.

## Constraints

- Keep user-facing `/tf <ticket-id>` contract
- Preserve existing artifact directories under `.tf/knowledge/tickets/<id>/`
- Must work in non-interactive mode (`pi -p "/tf <ticket>"`)
- Minimal duplication — shared logic stays in Python modules (`tf/`)

## Project Structure

```
pi-ticketflow/
├── prompts/
│   ├── tf.md              # Main entry point (chain invocation)
│   ├── tf-research.md     # Research phase wrapper
│   ├── tf-implement.md    # Implementation phase wrapper
│   ├── tf-review.md       # Review phase wrapper
│   ├── tf-fix.md          # Fix phase wrapper
│   └── tf-close.md        # Close phase wrapper
├── skills/
│   ├── tf-research/SKILL.md    # Research procedure
│   ├── tf-implement/SKILL.md   # Implementation procedure
│   ├── tf-review/SKILL.md      # Reviewer subagent contract
│   ├── tf-review-phase/SKILL.md # Review phase orchestration
│   ├── tf-fix/SKILL.md         # Fix procedure
│   └── tf-close/SKILL.md       # Close procedure
├── agents/
│   ├── reviewer-general.md     # Parallel review agent
│   ├── reviewer-spec-audit.md  # Parallel review agent
│   └── reviewer-second-opinion.md  # Parallel review agent
└── tf/                         # Python tooling
    └── ...
```

## Work Plan (phases / tickets)

### Phase 1: Foundation

1. Create phase skills in `skills/` with detailed procedures
2. Create phase prompts in `prompts/` with frontmatter
3. Test each phase prompt in isolation

### Phase 2: Orchestration

4. Update `prompts/tf.md` to delegate to `tf irf`
5. Validate full IRF workflow runs end-to-end
6. Verify artifact outputs match expected format

### Phase 3: Migration & Docs

7. Update required extensions list (remove `pi-model-switch`)
8. Add migration section to docs
9. Update AGENTS.md if needed

### Phase 4: Rollback (if needed)

10. Keep `pi-model-switch` installable but optional

## Acceptance Criteria

- [ ] `/tf <ticket-id>` completes full IRF workflow with correct models per phase
- [ ] Each phase prompt has correct model/skill/thinking from frontmatter
- [ ] Skills contain detailed procedures; prompts are thin wrappers
- [ ] Artifacts (research.md, implementation.md, review.md, fixes.md, close-summary.md) match existing format
- [ ] Documentation updated — `pi-model-switch` no longer required
- [ ] Non-interactive mode (`pi -p "/tf <ticket>"`) works
- [ ] No regression in existing TF functionality

---

## Consultant Notes (Metis)

- 2026-02-13: Plan captures the core idea well. Key gaps identified:
  - Flag handling strategy: **Hybrid approach selected** - entry points for research control, post-chain for follow-ups
  - Retry/escalation state: Handled via `{artifactDir}/retry-state.json` passed through chain context
  - Artifact persistence: Each phase writes to `{artifactDir}/` which is read by subsequent phases

## Reviewer Notes (Momus)

- 2026-02-13: PASS
  - Blockers: None
  - Required changes:
    - Address flag handling and retry state in Phase 1 before proceeding to Phase 2
