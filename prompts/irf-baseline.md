---
description: Capture brownfield project status quo [irf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: irf-planning
---

# /irf-baseline

Capture a status-quo baseline for an existing project.

## Usage

```
/irf-baseline [focus-area]
```

## Arguments

- `$@` - Optional focus area (subsystem to emphasize)

## Examples

```
/irf-baseline
/irf-baseline "authentication system"
```

## Execution

Follow the **IRF Planning Skill** "Baseline Capture" procedure:

1. Determine topic ID: `baseline-{repo-name}`
2. Scan project:
   - Read high-signal files (README.md, package.json, etc.)
   - Find entry points, tests, source directories
3. If focus area specified: prioritize scanning that area
4. Write artifacts:
   - `overview.md` - Project summary
   - `baseline.md` - Architecture, components, entry points
   - `risk-map.md` - Technical, dependency, knowledge risks
   - `test-inventory.md` - Test structure and gaps
   - `dependency-map.md` - Dependencies and external services
   - `sources.md` - Files scanned
5. Update `index.json`

## Output

Created artifacts in `.pi/knowledge/topics/{topic-id}/`:
- overview.md
- baseline.md
- risk-map.md
- test-inventory.md
- dependency-map.md
- sources.md

## Use Cases

- Before major refactoring: document current state
- Handoff documentation: capture tribal knowledge
- Risk assessment: identify fragile areas
- Test planning: identify coverage gaps

## Next Steps

- Review baseline artifacts
- Use `/irf-seed` for improvement ideas
- Create tickets via `/irf-backlog`
