---
description: Research spike on a topic [tf-planning +codex-mini]
model: openai-codex/gpt-5.1-codex-mini
thinking: medium
skill: tf-planning
---

# /tf-spike

Run a focused research spike on a topic and store results.

## Usage

```
/tf-spike <topic> [--parallel]
```

## Arguments

- `$@` - Topic to research (exclude --parallel flag)

## Flags

| Flag | Description |
|------|-------------|
| `--parallel` | Use parallel subagents for faster research |

## Examples

```
/tf-spike "React Server Components vs Next.js App Router"
/tf-spike "PostgreSQL partitioning strategies" --parallel
```

## Execution

Follow the **IRF Planning Skill** "Research Spike" procedure:

1. Parse topic from `$@` (excluding --parallel)
2. Create topic ID: `spike-{slug}`
3. Check available MCP tools:
   - context7 (documentation)
   - exa (web search)
   - grep_app (code search)
   - zai-web-search
4. Research:
   - **Sequential** (default): Query tools inline
   - **Parallel** (--parallel flag): Spawn 3 `researcher-fetch` subagents
5. Synthesize findings
6. Write artifacts:
   - `overview.md` - Summary + quick answer
   - `sources.md` - All URLs and tools used
   - `spike.md` - Full analysis with findings, options, recommendation
7. Update `index.json`

## Output

Created artifacts in `.pi/knowledge/topics/{topic-id}/`:
- overview.md
- sources.md
- spike.md

## Output Includes

- **Summary**: 2-3 paragraph overview
- **Key Findings**: 3-5 major discoveries
- **Options Considered**: Pros/cons of alternatives
- **Recommendation**: Clear guidance
- **Risks & Unknowns**: What to watch for
- **Next Steps**: Suggested actions

## Research Methods

| Mode | Subagents | Speed | Reliability |
|------|-----------|-------|-------------|
| Sequential | 0 | Slower | Higher |
| Parallel (--parallel) | 3 | Faster | Medium |
