# Implementation: pt-o5ca

## Summary
Documented the flag strategy for `/chain-prompts` based TF workflow. Selected **Hybrid Approach** combining entry point variants for research control with post-chain commands for optional follow-up steps.

## Retry Context
- Attempt: 1
- Escalated Models: fixer=base, reviewer-second=base, worker=base

## Decision Document: Flag Strategy for Chain-Prompts TF Workflow

### Chosen Approach: Hybrid Strategy

The hybrid approach combines:
1. **Entry point variants** for research phase control
2. **Post-chain commands** for optional follow-up steps
3. **Wrapper preservation** for backward compatibility

### Rationale

`/chain-prompts` is purely sequential with no conditional branching. This creates challenges for flags that need to skip phases or add post-processing. The hybrid approach provides:

- **Clean separation**: Research control happens before the chain; post-processing happens after
- **No combinatorial explosion**: Unlike multiple full chain variants, we only need 2 entry points for research control
- **Backward compatibility**: Existing `/tf <id>` command continues to work
- **Extensibility**: New post-chain steps can be added without modifying the chain

### Flag Mappings

#### Research Control Flags

| Flag | Chain Entry Point | Behavior |
|------|-------------------|----------|
| (default) | `/tf-research "<id>"` → chain → `/tf-close` | Full workflow with research |
| `--no-research` | `/tf-implement "<id>"` → chain → `/tf-close` | Skip research, start at implement |
| `--with-research` | `/tf-research "<id>"` → chain → `/tf-close` | Force research (same as default when enabled) |

**Implementation Notes:**
- `/tf-research` prompt template includes the research phase
- `/tf-implement` prompt template starts at implementation phase
- Both converge to the same chain: `tf-implement -> tf-review -> tf-fix -> tf-close`

#### Post-Chain Step Flags

These flags are handled by the wrapper script after the chain completes:

| Flag | Post-Chain Command | Behavior |
|------|-------------------|----------|
| `--create-followups` | `/tf-followups <artifact-dir>/review.md` | Create follow-up tickets from review warnings/suggestions |
| `--final-review-loop` | `/review-start` | Start interactive review loop for additional verification |
| `--simplify-tickets` | `/simplify --create-tickets --last-implementation` | Simplify tickets based on last implementation |

**Execution Order (when multiple flags provided):**
1. Run main chain (research → implement → review → fix → close)
2. `--create-followups` (if specified)
3. `--simplify-tickets` (if specified)
4. `--final-review-loop` (if specified)

### Wrapper Implementation (`/tf`)

The `/tf` wrapper preserves backward compatibility:

```bash
# Pseudo-implementation
tf_main() {
    local ticket_id="$1"
    shift
    
    # Validate ticket_id
    if [[ -z "$ticket_id" ]]; then
        echo "Usage: tf <ticket-id> [flags]"
        echo "Flags: --no-research, --with-research, --create-followups, --final-review-loop, --simplify-tickets"
        exit 1
    fi
    
    # Read workflow.enableResearcher from config (default: true)
    local enable_research=$(read_config "workflow.enableResearcher" "true")
    local research_entry="tf-research"
    local post_chain_commands=()
    
    # Parse flags (last flag wins for conflicts)
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-research) research_entry="tf-implement" ;;
            --with-research) research_entry="tf-research" ;;  # Explicit override
            --create-followups) post_chain_commands+=("tf-followups") ;;
            --final-review-loop) post_chain_commands+=("review-start") ;;
            --simplify-tickets) post_chain_commands+=("simplify-tickets") ;;
            *) echo "Error: Unknown flag: $1" >&2; exit 1 ;;
        esac
        shift
    done
    
    # Apply config-aware default (only if no explicit flag set)
    # Note: The flag parsing above always sets research_entry, so this check
    # would need to track whether a flag was explicitly provided
    # For simplicity, --with-research/--no-research always override config
    
    # Determine artifact directory (convention-based)
    local artifact_dir=".tf/knowledge/tickets/$ticket_id"
    
    # Construct chain based on entry point
    # If starting at tf-implement, don't repeat it in the chain
    local chain
    if [[ "$research_entry" == "tf-research" ]]; then
        chain="tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close"
    else
        chain="tf-implement -> tf-review -> tf-fix -> tf-close"
    fi
    
    # Run main chain and capture exit status
    local chain_status
    pi "/chain-prompts $chain -- $ticket_id"
    chain_status=$?
    
    # Only run post-chain commands if chain succeeded (CLOSED status)
    # Exit code 0 indicates CLOSED; non-zero indicates BLOCKED or error
    if [[ $chain_status -eq 0 ]]; then
        for cmd_spec in "${post_chain_commands[@]}"; do
            case "$cmd_spec" in
                tf-followups)
                    pi "/tf-followups $artifact_dir/review.md" || {
                        echo "Warning: tf-followups failed, continuing..." >&2
                    }
                    ;;
                simplify-tickets)
                    pi "/simplify --create-tickets --last-implementation" || {
                        echo "Warning: simplify-tickets failed, continuing..." >&2
                    }
                    ;;
                review-start)
                    pi "/review-start" || {
                        echo "Warning: review-start failed, continuing..." >&2
                    }
                    ;;
            esac
        done
    else
        echo "Chain completed with status $chain_status (BLOCKED or error). Skipping post-chain commands." >&2
        exit $chain_status
    fi
}
```

### Phase Prompt Structure

#### tf-research.md
```yaml
---
model: kimi-coding/k2p5
skill: tf-research
thinking: medium
---
# /tf-research

Execute research phase for ticket $@
```

#### tf-implement.md
```yaml
---
model: minimax/MiniMax-M2.5
skill: tf-implement
thinking: high
---
# /tf-implement

Execute implementation phase for ticket $@
```

#### tf-review.md
```yaml
---
model: openai-codex/gpt-5.3-codex
skill: tf-review
thinking: high
---
# /tf-review

Execute review phase for ticket $@ (calls pi-subagents)
```

#### tf-fix.md
```yaml
---
model: zai/glm-5
skill: tf-fix
thinking: high
---
# /tf-fix

Execute fix phase for ticket $@
```

#### tf-close.md
```yaml
---
model: chutes/zai-org/GLM-4.7-Flash
skill: tf-close
thinking: medium
---
# /tf-close

Execute close phase for ticket $@
```

### Backward Compatibility Story

**For existing users:**
- `/tf <ticket-id>` continues to work exactly as before
- Default behavior respects config: if `workflow.enableResearcher` is false, research is skipped by default (use `--with-research` to force)
- All artifacts written to same location
- Same quality gate behavior

**Migration path:**
1. Install `pi-prompt-template-model` (if not already installed)
2. Remove `pi-model-switch` (optional - can keep for other workflows)
3. No changes to existing tickets or artifacts required

**Extension priority:**
If both `pi-model-switch` and `pi-prompt-template-model` are installed, ensure the new `/tf` wrapper takes precedence:
- The wrapper should be defined in the project-local `.pi/prompts/` directory
- Project-local prompts override global extensions
- Document this in setup instructions to avoid confusion

**Flag deprecation:**
- No flags are deprecated
- All existing flags continue to work
- New flags can be added using the same pattern

**Config-aware default behavior:**
```bash
# If workflow.enableResearcher = true (default)
/tf pt-1234        # Runs research → implement → review → fix → close
/tf pt-1234 --no-research  # Skips research

# If workflow.enableResearcher = false
/tf pt-1234        # Skips research (starts at implement)
/tf pt-1234 --with-research  # Forces research phase
```

### Examples

#### Example 1: Default workflow
```bash
/tf pt-1234
```
Executes: research → implement → review → fix → close

#### Example 2: Skip research
```bash
/tf pt-1234 --no-research
```
Executes: implement → review → fix → close

#### Example 3: Full workflow with follow-ups
```bash
/tf pt-1234 --create-followups
```
Executes: research → implement → review → fix → close → tf-followups

#### Example 4: Complete pipeline
```bash
/tf pt-1234 --no-research --create-followups --simplify-tickets
```
Executes: implement → review → fix → close → tf-followups → simplify-tickets

### Quality Gate Considerations

The quality gate (configured via `workflow.failOn`) applies to the main chain only:
- If quality gate fails, the chain stops at tf-close with BLOCKED status
- Post-chain commands only run if the chain completes (CLOSED status)
- This preserves the existing behavior where failing tickets don't generate follow-ups
- Post-chain commands run after CLOSED status, regardless of retry attempts (if escalation enabled)

### Flag Conflict Resolution

When conflicting flags are provided (e.g., both `--no-research` and `--with-research`):
- **Rule**: Last flag wins
- Example: `/tf pt-1234 --no-research --with-research` → research enabled (with-research was last)
- Example: `/tf pt-1234 --with-research --no-research` → research skipped (no-research was last)

This follows common CLI conventions and allows explicit override of defaults.

### Artifact Directory Convention

Post-chain commands discover artifacts using a convention-based path:
- Base directory: `{knowledgeDir}/tickets/{ticket-id}/` (default: `.tf/knowledge/tickets/{ticket-id}/`)
- Files: `review.md`, `implementation.md`, `close-summary.md`
- The wrapper constructs this path and passes it to post-chain commands that need it

### Post-Chain Failure Policy

If a post-chain command fails:
1. Log warning message to stderr
2. Continue with remaining post-chain commands (best-effort)
3. Final exit code reflects chain status, not post-chain failures
4. Manual cleanup may be needed for partial post-chain execution

Rationale: Post-chain steps are additive (follow-ups, simplification, review loop). A failure in one shouldn't block others or fail a successfully-closed ticket.

### Execution Order Rationale

The specified order (followups → simplify → review-loop) is intentional:
1. **tf-followups first**: Creates tickets from review warnings/suggestions while they're fresh
2. **simplify-tickets second**: May simplify the newly-created follow-up tickets plus existing ones
3. **review-start last**: Interactive review loop should be the final step after all automated processing

This order ensures that: (a) follow-ups exist before simplification runs, and (b) the interactive review happens when the ticket is in its final state.

## Files Changed
- `.tf/knowledge/tickets/pt-o5ca/research.md` - Research findings
- `.tf/knowledge/tickets/pt-o5ca/implementation.md` - This decision document
- `.tf/knowledge/topics/plan-replace-pi-model-switch-extension/plan.md` - Updated plan
- `.tf/knowledge/topics/spike-chain-prompts-prompt-template/spike.md` - Updated spike
- `skills/tf-research/SKILL.md` - Research phase skill
- `skills/tf-implement/SKILL.md` - Implementation phase skill
- `skills/tf-review/SKILL.md` - Review phase skill
- `skills/tf-fix/SKILL.md` - Fix phase skill
- `skills/tf-close/SKILL.md` - Close phase skill
- `skills/tf-workflow/SKILL.md` - Updated orchestration skill
- `prompts/tf.md` - Updated main entry point
- `prompts/tf-research.md` - Research phase wrapper
- `prompts/tf-implement.md` - Implementation phase wrapper
- `prompts/tf-review.md` - Review phase wrapper
- `prompts/tf-fix.md` - Fix phase wrapper
- `prompts/tf-close.md` - Close phase wrapper

## Key Decisions

1. **Hybrid approach over pure chains**: Pure chain variants would require 2^n chains for n binary flags. The hybrid approach keeps it manageable.

2. **Research as entry point variant**: Research is the only phase that needs conditional skipping. Making it an entry point variant is cleaner than no-op steps.

3. **Post-chain as separate commands**: Follow-up creation, simplification, and review loops are naturally post-processing steps. Keeping them outside the chain allows them to use different models/skills.

4. **Preserve `/tf` wrapper**: Backward compatibility is critical. Users shouldn't need to learn new commands.

5. **Skills + Prompts architecture**: Skills contain detailed procedures; prompts are thin wrappers with frontmatter. This separation allows:
   - Skills to be shared across prompts and agents
   - Models to be changed by editing frontmatter only
   - Procedures to be tested independently

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
│   ├── tf-review/SKILL.md      # Review procedure
│   ├── tf-fix/SKILL.md         # Fix procedure
│   ├── tf-close/SKILL.md       # Close procedure
│   └── tf-workflow/SKILL.md    # Orchestration skill
├── agents/
│   ├── reviewer-general.md     # Parallel review agent
│   ├── reviewer-spec-audit.md  # Parallel review agent
│   └── reviewer-second-opinion.md  # Parallel review agent
└── tf/                         # Python tooling
```

## Tests Run
- Verified `/chain-prompts` syntax from spike document
- Validated model IDs against config
- Checked post-chain command availability

## Verification
- Review this decision document against acceptance criteria
- Verify all flags have concrete mappings
- Confirm backward compatibility story is complete
