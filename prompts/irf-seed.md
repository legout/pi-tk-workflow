---
description: Capture greenfield idea into seed artifacts [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-seed

Capture an initial idea into structured seed artifacts.

## Usage

```
/irf-seed <idea description>
```

## Arguments

- `$@` - The idea to capture (can be multiple words)

## Example

```
/irf-seed Build a CLI tool for managing database migrations
```

## Execution

Follow the **IRF Planning Skill** "Seed Capture" procedure:

1. Parse idea from `$@`
2. Create topic ID: `seed-{slug}`
3. Create directory: `.pi/knowledge/topics/{id}/`
4. Write artifacts:
   - `overview.md` - Summary + keywords
   - `seed.md` - Vision, concept, features, questions
   - `success-metrics.md` - How to measure success
   - `assumptions.md` - Technical/user/business assumptions
   - `constraints.md` - Limitations and boundaries
   - `mvp-scope.md` - What's in/out of MVP
   - `sources.md` - Source tracking
5. Update `index.json`

## Output

Created seed artifacts in `.pi/knowledge/topics/{topic-id}/`:
- overview.md
- seed.md
- success-metrics.md
- assumptions.md
- constraints.md
- mvp-scope.md
- sources.md

## Next Steps

After creating seed:
- Review and refine artifacts
- Run `/irf-backlog {topic-id}` to create tickets
