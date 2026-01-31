---
description: Research spike into knowledge base. Lite version - no subagent wrapper, optional parallel fetch.
---

# IRF Spike (Lite)

Run a focused research spike on a topic and store results in the knowledge base. This version runs inline with model-switch, with optional parallel research fetch.

## Invocation

```
/irf-spike-lite <topic> [--parallel]
```

- If `$@` is empty, ask for a spike topic and stop
- `--parallel` flag: use parallel subagents for MCP fetches (faster, but 3 subagent spawns)

## Prerequisites

1. Verify `switch_model` tool is available
2. For research: verify MCP tools available (context7, exa, grep_app) OR inform user research will be limited

If switch_model unavailable, suggest using `/irf-spike` (original) instead.

## Execution

### Step 1: Switch to Planning Model

```
Use switch_model tool with action="switch", search="gpt-5.1-codex-mini" (or config model)
```

### Step 2: Load Config

Read workflow config (project overrides global):
- `.pi/workflows/implement-review-fix-close/config.json`
- `~/.pi/agent/workflows/implement-review-fix-close/config.json`

Extract `workflow.knowledgeDir` (default: `.pi/knowledge`).

### Step 3: Create Topic Structure

1. Parse topic from `$@` (excluding `--parallel` flag)
2. Create `topic-id` slug:
   - Lowercase, replace spaces with dashes
   - Max 40 characters
   - Prefix with `spike-`
   - Example: "React Server Components vs Next.js App Router" → `spike-react-server-components-vs-nextjs`

3. Create topic directory:
   ```bash
   mkdir -p "${knowledgeDir}/topics/${topic_id}"
   ```

### Step 4: Research

**Check which MCP tools are available:**
- `context7` - documentation search
- `exa` - web search  
- `grep_app` - code search
- `zai-web-search` / `zai-web-reader` - alternative web search

**If `--parallel` flag is set:**

Use parallel subagents for faster research:

```json
{
  "tasks": [
    {
      "agent": "researcher-fetch",
      "task": "Documentation search for: ${topic}. Use context7 to find official docs."
    },
    {
      "agent": "researcher-fetch",
      "task": "Web search for: ${topic}. Use exa or zai-web-search for articles and discussions."
    },
    {
      "agent": "researcher-fetch",
      "task": "Code search for: ${topic}. Use grep_app to find real-world examples."
    }
  ]
}
```

Read outputs from the three parallel tasks.

**If `--parallel` flag is NOT set (default):**

Do sequential research in the main agent:

1. **Docs search:**
   - Use context7 tool to search for official documentation
   - Note key findings

2. **Web search:**
   - Use exa or zai-web-search for articles, blog posts, discussions
   - Note key findings and URLs

3. **Code search:**
   - Use grep_app to find real implementations
   - Note relevant code patterns and repositories

If a tool is unavailable, skip it and note in sources.

### Step 5: Synthesize Findings

Combine research from all sources into coherent spike artifacts.

### Step 6: Write Spike Artifacts

Write to `${knowledgeDir}/topics/${topic_id}/`:

**overview.md:**
```markdown
# Spike: ${topic}

Brief 2-3 sentence summary of the research findings.

## Keywords
- keyword1
- keyword2
- keyword3

## Quick Answer
${One paragraph summary answering the core question}
```

**sources.md:**
```markdown
# Sources: ${topic}

## Documentation
- ${doc_url_1}: ${description}
- ${doc_url_2}: ${description}

## Articles & Discussions
- ${article_url_1}: ${description}
- ${article_url_2}: ${description}

## Code Examples
- ${repo_url_1}: ${description}
- ${repo_url_2}: ${description}

## Tools Used
- context7: ${used/unavailable}
- exa: ${used/unavailable}
- grep_app: ${used/unavailable}

## Date Researched
${today}
```

**spike.md:**
```markdown
# Spike: ${topic}

Date: ${today}
Research method: ${parallel or sequential}

## Question
${The core question being investigated}

## Summary
${2-3 paragraph summary of findings}

## Key Findings

### Finding 1: ${title}
${Details and evidence}

### Finding 2: ${title}
${Details and evidence}

### Finding 3: ${title}
${Details and evidence}

## Options Considered

### Option A: ${name}
- **Pros:** ${list}
- **Cons:** ${list}
- **When to use:** ${guidance}

### Option B: ${name}
- **Pros:** ${list}
- **Cons:** ${list}
- **When to use:** ${guidance}

## Recommendation
${Clear recommendation with justification}

## Risks & Unknowns
- Risk 1: ${description}
- Risk 2: ${description}
- Unknown: ${what couldn't be determined}

## Next Steps
- ${Suggested action 1}
- ${Suggested action 2}

## References
See sources.md for full source list.
```

### Step 7: Update Knowledge Index

Read `${knowledgeDir}/index.json`, add new topic entry:

```json
{
  "id": "${topic_id}",
  "title": "Spike: ${topic}",
  "keywords": ["spike", "keyword1", "keyword2", ...],
  "overview": "topics/${topic_id}/overview.md",
  "sources": "topics/${topic_id}/sources.md"
}
```

Update the `updated` field to today's date.

### Step 8: Report Results

```
Completed spike research for: ${topic}

Created artifacts in ${knowledgeDir}/topics/${topic_id}/:
- overview.md (summary)
- sources.md (${source_count} sources)
- spike.md (full analysis)

Key finding: ${one-line summary}

Recommendation: ${brief recommendation}

Research method: ${parallel subagents | sequential in-agent}
MCP tools used: ${list}
```

## Comparison to /irf-spike

| Aspect | /irf-spike | /irf-spike-lite | /irf-spike-lite --parallel |
|--------|------------|-----------------|---------------------------|
| Subagents | 4 (planner + 3 fetch) | 0 | 3 (fetch only) |
| Research speed | Fast (parallel) | Slower (sequential) | Fast (parallel) |
| Reliability | Lower | Higher | Medium |
| Nesting | 2 levels deep | None | 1 level |
