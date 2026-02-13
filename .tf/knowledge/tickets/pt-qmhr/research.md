# Research: pt-qmhr

## Status
Research completed. Design task for chained prompt implementation.

## Context Reviewed
- Ticket: pt-qmhr - Design retry/escalation handling for chained TF phases
- External Ref: plan-replace-pi-model-switch-extension
- Blocking: pt-74hd (Add phase prompts for TF workflow)

## Current Implementation Analysis

### Runtime switch_model approach (current)
- Single `/tf` prompt invokes `switch_model` tool between phases
- Retry state stored in `.tf/knowledge/tickets/{id}/retry-state.json`
- Escalation determined at runtime based on attempt number
- All phases share context within single prompt execution

### Planned chain-prompts approach
- Each phase becomes separate prompt: tf-research, tf-implement, tf-review, tf-fix, tf-close
- Chain executes: tf-research → tf-implement → tf-review → tf-fix → tf-close
- Each prompt declares own model/skill/thinking in frontmatter
- Context passed via `{previous}` variable and file artifacts

## Key Challenges Identified

1. **Escalation communication**: How does tf-fix know if escalation is needed?
   - Current: Runtime check of retry-state.json
   - Challenge: Each chain step runs independently - needs to read state from filesystem

2. **Retry detection**: How does tf-close determine if ticket is blocked?
   - Current: Reviews are available in memory
   - Challenge: tf-review artifacts (review.md) must be readable by tf-close

3. **Flag propagation**: How to pass flags like `--retry-reset` across chain steps?
   - Current: All flags processed in single prompt
   - Challenge: Each prompt only sees its own frontmatter + {task}

4. **Attempt tracking**: How to increment retry count only after full chain completes?
   - Current: Single atomic operation at close
   - Challenge: Each step could fail mid-chain; need transaction-like behavior

## Proposed Solutions

### Solution A: State Files + Conventions
Each chain step reads/writes to well-known artifact files:
- `retry-state.json` - read at start of each phase
- `chain-context.json` - flags and context passed between phases
- Each phase reads previous artifacts to determine behavior

### Solution B: Wrapper Prompt with State Machine
Create `/tf-chain` that orchestrates based on state:
- Single orchestrator prompt reads state
- Dynamically determines which chain steps to run
- Passes escalation context via {task} injection

### Solution C: Hybrid (Recommended)
Keep single `/tf` prompt but refactor internal phases:
- Use prompt chaining internally via subagents
- Maintain unified retry/escalation logic
- Gradual migration path

## References
- docs/retries-and-escalation.md - Current retry design
- .tf/knowledge/topics/plan-replace-pi-model-switch-extension/plan.md - Migration plan
- .pi/prompts/tf.md - Current entry point

## Sources
- Local docs and prompts
- Configuration at .tf/config/settings.json
