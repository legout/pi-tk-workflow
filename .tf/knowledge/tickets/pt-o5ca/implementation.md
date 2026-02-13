# Implementation: pt-o5ca

## Summary
Decided on flag strategy for chain-prompts TF workflow: use separate entry points for mutually-exclusive flag combinations (research control), and run post-chain steps as separate commands after the main chain completes.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Decision

### Approach: Hybrid Strategy

1. **Research Control** — Multiple chain variants (entry points)
2. **Post-chain steps** — Run as separate commands after chain completes
3. **Backward compatibility** — Keep `/tf <id>` as the main entry point

### Rationale

`/chain-prompts` has **no native conditional branching**. The spike document evaluated:
- Option A: Keep `pi-model-switch` (runtime switching, conditional inside skill)
- Option B: Replace with `/chain-prompts` (declarative, no conditionals)

For flags, the options were:
1. **Multiple entry points** (`/tf`, `/tf-no-research`, etc.) — explicit, no conditionals
2. **Wrapper that constructs chain dynamically** — complex, may not work with static parsing
3. **Push conditionals into phase prompts** — each phase checks flags in artifacts

The **hybrid approach** combines:
- Entry point variants for mutually-exclusive research control
- Post-chain commands for optional follow-up steps

This is the cleanest because:
- Users can see exactly what chain runs (explicit)
- No conditional logic inside prompts (simpler)
- Post-chain steps don't need to be in the chain (they're optional)

## Flag Mapping

### Research Control Flags

| Original Flag | Chain Variant | Notes |
|---------------|---------------|-------|
| `/tf <id>` (default) | **Config-dependent**: If `workflow.enableResearcher: true` → `tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close`; else → `tf-implement -> tf-review -> tf-fix -> tf-close` | Respects current config |
| `/tf <id> --no-research` | `tf-implement -> tf-review -> tf-fix -> tf-close` | Skip research phase (overrides config) |
| `/tf <id> --with-research` | `tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close` | Force research (overrides config) |

**Implementation**: The `/tf` wrapper reads `workflow.enableResearcher` from config and selects the appropriate chain:

```markdown
---
description: TF workflow entry point (selects chain based on args and config)
model: kimi-coding
skill: tf/k2p5-workflow
---

# /tf

Execute TF workflow. Parses flags and config, then invokes appropriate chain.

## Flag Precedence

1. Explicit flags override config: `--no-research` > `--with-research` > config > defaults
2. If both `--no-research` and `--with-research` are provided, error or warn and use `--with-research`

## Flag to Chain Mapping

| Flag | Config `enableResearcher` | Chain |
|------|--------------------------|-------|
| (none) | true | tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close |
| (none) | false | tf-implement -> tf-review -> tf-fix -> tf-close |
| --no-research | any | tf-implement -> tf-review -> tf-fix -> tf-close |
| --with-research | any | tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close |

The wrapper can use `/chain-prompts` to invoke the selected chain.

### Post-Chain Flags

| Flag | Chain-Compatible Approach |
|------|---------------------------|
| `--create-followups` | Run `/tf-followups <artifact-dir>/review.md` **after** chain completes |
| `--final-review-loop` | Run `/review-start` **after** chain completes |
| `--simplify-tickets` | Run `/simplify --create-tickets --last-implementation` **after** chain completes |

**Implementation**: These are **not part of the chain**. Instead, the `/tf` wrapper (or the closer phase) invokes them as separate commands after the main chain succeeds. This is already how the current skill handles them.

### Execution Mode Flags

| Flag | Handling |
|------|----------|
| `--auto` / `--no-clarify` | Passed to each phase prompt; phases use for subagent confirmation |
| `--plan` / `--dry-run` | Print the resolved chain and exit (no execution) |
| `--retry-reset` | **Partial support**: Wrapper reads flag and passes to closer phase. The closer phase writes retry state, but mid-chain retry requires pt-qmhr design. |

**Implementation for `--retry-reset`**: Since pt-qmhr (retry/escalation design) is a blocker for pt-74hd (phase prompts), the chain-based approach initially inherits the existing retry-state.json mechanism. The wrapper passes `--retry-reset` to the closer phase, which handles it as before. Full mid-chain retry support requires the pt-qmhr design.

## Concrete Mapping Examples

### Example 1: Full workflow (default)
```
/tf pt-123
```
Invokes:
```
/chain-prompts tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close -- pt-123
```

### Example 2: No research
```
/tf pt-123 --no-research
```
Invokes:
```
/chain-prompts tf-implement -> tf-review -> tf-fix -> tf-close -- pt-123
```

### Example 3: With follow-ups
```
/tf pt-123 --create-followups
```
Invokes chain, then runs:
```
/tf-followups .tf/knowledge/tickets/pt-123/review.md
```

### Example 4: Complex (no research + follow-ups + simplify)
```
/tf pt-123 --no-research --create-followups --simplify-tickets
```
Invokes chain without research, then runs:
```
/tf-followups .tf/knowledge/tickets/pt-123/review.md
/simplify --create-tickets --last-implementation
```

## Backward Compatibility

| Current Behavior | Chain-Compatible Replacement |
|-------------------|------------------------------|
| `/tf <id>` | `/tf <id>` (wrapper selects full chain) |
| `/tf <id> --no-research` | `/tf <id> --no-research` (wrapper selects no-research chain) |
| `/tf <id> --create-followups` | Chain runs, then `/tf-followups` invoked |
| `/tf <id> --plan` | Prints resolved chain (could be `/chain-prompts --plan ...`) |

The user-facing commands stay the same. The implementation changes from runtime model-switching to prompt-chaining.

## Dependencies

- **pt-74hd**: Create phase prompts (`tf-research`, `tf-implement`, `tf-review`, `tf-fix`, `tf-close`)
- **pt-qmhr**: Design retry/escalation for chained phases (blocks pt-74hd)
- **pt-mdl0**: Implement `/tf` as chain-prompts wrapper (depends on pt-74hd)

## Artifact Files

This decision should be referenced by:
- Phase prompt designs (pt-74hd)
- Retry/escalation design (pt-qmhr)
- Wrapper implementation (pt-mdl0)
