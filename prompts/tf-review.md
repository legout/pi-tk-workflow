---
description: Review phase for TF workflow [tf-review-phase]
model: openai-codex/gpt-5.3-codex
thinking: high
skill: tf-review-phase
---

# /tf-review

Execute the Review phase for TF workflow ticket implementation.

## Input
- Ticket ID: `$1`
- Args: `$@`

## Execution

Follow the **tf-review-phase** skill procedure to:

1. Load context (implementation.md, retry state)
2. Determine reviewers from config
3. Resolve repo root
4. Execute parallel subagents (reviewer-general, reviewer-spec-audit, reviewer-second-opinion)
5. Handle skipped reviews
6. Merge reviews into consolidated `{artifactDir}/review.md`

## Usage

```
/tf-review <ticket-id>
```

## Output

- `{artifactDir}/review.md` - Consolidated review
- `{artifactDir}/review-general.md` - General review (from subagent)
- `{artifactDir}/review-spec.md` - Spec audit (from subagent)
- `{artifactDir}/review-second.md` - Second opinion (from subagent)
