# Research: pt-xu9u

## Status
Research complete. Context gathered from specifications and existing implementation.

## Context Reviewed

### Primary Sources
1. **Ticket pt-xu9u**: Implement retry-aware escalation in /tf workflow
   - Acceptance criteria define retry attempt loading, escalation at attempt 2 and 3+
   - Must record attempt number and escalated roles/models in artifacts

2. **Specification pt-te9b/retry-state-spec.md**:
   - Retry state location: `.tf/knowledge/tickets/{id}/retry-state.json`
   - Schema includes: version, ticketId, attempts[], lastAttemptAt, status, retryCount
   - Detection algorithm: Primary (close-summary.md BLOCKED) + Fallback (review.md failOn counts)
   - Reset policy: Reset on successful close only
   - Escalation curve: Attempt 1=base, 2=fixer only, 3+=fixer + reviewer-second-opinion (+ optional worker)

3. **Current SKILL.md** (tf-workflow):
   - Uses model switching via `switch_model` tool
   - Model resolution: agents.{role} → metaModels.{key}.model → model ID
   - Procedures: Re-Anchor, Research, Implement, Parallel Reviews, Merge Reviews, Fix Issues, Close Ticket
   - Key models: worker (implement), fixer (fix), reviewer-second-opinion (review)

## Key Implementation Points

### Retry State Loading (Re-Anchor Context)
- Check for `{artifactDir}/retry-state.json`
- If exists and last attempt was BLOCKED → increment retry count
- Parse escalation config from `workflow.escalation` in settings.json

### Model Escalation Logic
```
Attempt 1: Use base models from config
Attempt 2: Escalate fixer model (if escalation.models.fixer configured)
Attempt 3+: Escalate fixer + reviewer-second-opinion (+ worker if configured)
```

### Detection Algorithm Integration
- Add to Close Ticket procedure: detect BLOCKED status from close-summary.md
- Update retry-state.json with attempt result
- If BLOCKED → set aggregate status to "blocked", increment retryCount
- If CLOSED → set aggregate status to "closed", reset retryCount

### New Flags to Support
- `--retry-reset`: Force fresh attempt (rename existing state file)

### Config Extension
Add to settings.json under `workflow`:
```json
{
  "escalation": {
    "enabled": false,
    "maxRetries": 3,
    "models": {
      "fixer": null,
      "reviewerSecondOpinion": null,
      "worker": null
    }
  }
}
```

### Artifacts to Update
- `retry-state.json` - New: tracks attempts and escalation
- `implementation.md` - Record attempt number and escalated models
- `close-summary.md` - Already has BLOCKED status support

## Decisions

1. **Escalation is opt-in**: Default `enabled: false` - no behavior change unless explicitly enabled
2. **Null means base model**: Escalation config uses `null` to mean "use base model from agents config"
3. **Parallel safety**: Document assumption of ralph.parallelWorkers=1 (as per spec)
4. **Model resolution order**: escalation model → base model from agents → metaModels lookup

## Sources
- `.tf/knowledge/tickets/pt-te9b/retry-state-spec.md`
- `.pi/skills/tf-workflow/SKILL.md`
- `.tf/config/settings.json`
- `tk show pt-xu9u`
- `tk show pt-te9b`
