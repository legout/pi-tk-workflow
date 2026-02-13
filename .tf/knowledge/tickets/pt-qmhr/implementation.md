# Implementation: pt-qmhr

## Summary
Design document for retry/escalation handling when TF workflow is implemented as chained prompts instead of runtime switch_model.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Problem Statement

When `/tf` is implemented as prompt chains (tf-research → tf-implement → tf-review → tf-fix → tf-close), each phase runs as an independent prompt with its own model/skill/thinking. This breaks the current retry/escalation mechanism that relies on:
1. Shared in-memory context between phases
2. Runtime switch_model calls to change models mid-execution
3. Atomic retry state updates at close time

## Design Decision

**Decision**: Keep retry/escalation logic in a single orchestrating prompt, use subagents for phase execution.

### Rationale

The key insight is that **retry state management requires global visibility** across all phases, while **phase execution benefits from per-phase model selection**.

By keeping `/tf` as a single prompt that:
1. Reads retry state at start
2. Uses subagents or skill invocations for each phase
3. Makes escalation decisions based on retry state
4. Updates retry state only after full chain completes

This approach:
- Preserves existing retry/escalation behavior
- Works with filesystem-based state (already implemented)
- Doesn't require changes to how chain-prompts work
- Allows gradual migration of phase prompts

### Alternative Considered and Rejected

**Pure chain-prompts approach** (each phase reads/escalates independently):
- Would require each phase to read retry-state.json
- Would need conventions for passing escalation context via artifacts
- Complex flag propagation across chain steps
- Harder to implement atomic "all-or-nothing" retry counting

## Specification

### Architecture

```
/tf (orchestrator)
  ├── Reads retry-state.json
  ├── Determines escalation model overrides
  ├── For each phase:
  │   ├── Injects escalation context into phase prompt
  │   ├── Executes phase (via subagent or skill)
  │   └── Collects artifacts
  ├── Updates retry-state.json on completion
  └── Closes ticket
```

### Chain Phase Prompts

Each phase prompt receives escalation context via injected instructions:

```
# In tf-implement.md frontmatter or instructions:
## Context from Orchestrator
- Attempt: {attemptNumber}
- Escalated Fixer Model: {escalatedModels.fixer}
- Escalated Worker Model: {escalatedModels.worker}
- Escalated Reviewer-2nd-Opinion Model: {escalatedModels.reviewerSecondOpinion}
```

### State Files

| File | Purpose | Read By | Write By |
|------|---------|---------|----------|
| `retry-state.json` | Retry counter, attempt history | All phases | /tf (close) |
| `chain-context.json` | Escalation context, flags for current run | Phase prompts | /tf (orchestrator) |
| `research.md` | Research findings | tf-implement | tf-research |
| `implementation.md` | Implementation summary | tf-review, tf-fix | tf-implement |
| `review.md` | Consolidated review | tf-fix, tf-close | tf-review |
| `fixes.md` | Fixes applied | tf-close | tf-fix |
| `post-fix-verification.md` | Quality gate result | tf-close | tf-fix |

**Concurrency Note**: When `ralph.parallelWorkers > 1`, use file locking on retry-state.json or disable escalation. See docs/retries-and-escalation.md for details.

### Escalation Model Resolution

1. **At chain start** (/tf orchestrator):
   - Read `retry-state.json`
   - Determine attempt number
   - Resolve escalation models based on attempt number
   - Store in `chain-context.json` for injection

2. **Phase execution**:
   - Read escalation context from `chain-context.json` or injected via {task}
   - Use escalated model if specified (via subagent model parameter)
   - Otherwise use base model from metaModels

3. **At chain end** (/tf close):
   - Determine close status (CLOSED/BLOCKED)
   - Update retry-state.json atomically
   - If BLOCKED: increment retryCount
   - If CLOSED: reset retryCount to 0

### Flag Handling

Flags are processed at orchestrator level and passed via {task} injection:

| Flag | Handling |
|------|----------|
| `--retry-reset` | Delete/rename retry-state.json before chain starts |
| `--no-research` | Skip tf-research phase |
| `--with-research` | Force enable tf-research even if disabled |
| `--auto` / `--no-clarify` | Pass through to subagents (headless mode) |
| `--plan` / `--dry-run` | Run only planning, no execution |
| `--create-followups` | Pass to tf-close for follow-up ticket creation |
| `--simplify-tickets` | Pass to tf-close for ticket simplification |
| `--final-review-loop` | Pass to tf-close to trigger review loop |

**Conflicting flags**: When contradictory flags are present (e.g., `--no-research` + `--with-research`), the last flag in the chain takes precedence.

### Mid-Chain Failure Behavior

If a chain phase fails:

1. **Phase error**: Stop chain, mark retry-state status as "error" in current attempt
2. **Resume detection**: On re-run, check for existing artifacts:
   - If `close-summary.md` exists: attempt already completed (check status)
   - If phase artifacts exist but close doesn't: resume from last incomplete phase
   - Use timestamp ordering to determine latest completed phase
3. **No automatic retry**: User must re-run `/tf` manually
4. **Artifacts preserved**: Partial artifacts remain for debugging
5. **State stays "active"**: Can be resumed with same attempt number

Status values for retry-state:
- `in_progress`: Attempt started but not completed
- `blocked`: Quality gate prevented closing
- `closed`: Ticket successfully closed
- `error`: Phase failed mid-chain

This is **different from current behavior** where mid-prompt failures lose context. With chain-prompts, each phase is independent.

### Phase Model Override Precedence

When a phase prompt declares `model: X` in frontmatter but the orchestrator injects escalated model `Y`:

1. **Orchestrator injection wins**: Escalation is intentional and should override defaults
2. The subagent receives model override via the `model` parameter
3. Phase frontmatter serves as fallback when no escalation is active

### Quality Gate Integration

Quality gate checks happen in tf-fix → tf-close transition:

1. tf-fix runs and produces fixes.md
2. Post-fix verification calculates remaining issues (written to post-fix-verification.md)
3. tf-close reads verification result to determine close status
4. If quality gate blocks: set status BLOCKED, don't call tk close

## Implementation Tickets

### Phase 1: Foundation (pt-74hd dependent)

1. **Create phase prompt files**:
   - `.pi/prompts/tf-research.md`
   - `.pi/prompts/tf-implement.md`
   - `.pi/prompts/tf-review.md`
   - `.pi/prompts/tf-fix.md`
   - `.pi/prompts/tf-close.md`

2. **Define frontmatter** for each with model/skill/thinking

3. **Add escalation context injection** to each phase

### Phase 2: Orchestration

4. **Update /tf orchestrator** to:
   - Read retry-state.json at start
   - Determine escalation models
   - Execute phases via subagents with model overrides
   - Update retry-state.json on completion

5. **Handle mid-chain state** for resume capability

### Phase 3: Migration

6. **Document migration path** in docs/retries-and-escalation.md

7. **Update config** to document chain-aware settings

## Backwards Compatibility

- Keep `switch_model` based implementation available as fallback
- Config option `workflow.chainMode: true|false` to switch between approaches
- When `chainMode: false`: current behavior preserved
- When `chainMode: true`: new chain-based behavior
- Add to settings.json schema:
  ```json
  {
    "workflow": {
      "chainMode": false
    }
  }
  ```

## Acceptance Criteria for This Design

- [x] Escalation models can be passed to phase prompts
- [x] Retry state persists across chain execution
- [x] Flags like --retry-reset work across chains
- [x] Mid-chain failures don't corrupt retry state
- [x] Quality gate still blocks closing on violations
- [x] Existing artifacts format preserved (research.md, implementation.md, etc.)

## Verification

To verify this design works:
1. Implement phase prompts (pt-74hd)
2. Create test ticket with intentional review failures
3. Run `/tf test-ticket` with escalation enabled
4. Verify retry-state.json is updated correctly
5. Verify escalated models are used on retry

## Related Tickets

- pt-74hd: Add phase prompts for TF workflow (blocking)
- pt-pcd9: Update docs/setup to drop pi-model-switch (linked)
