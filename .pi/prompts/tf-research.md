---
description: Research phase for TF workflow - gather context and knowledge for ticket implementation [tf-research]
model: kimi-coding/k2p5
thinking: medium
skill: tf-research
---

# /tf-research

Execute the Research phase for TF workflow ticket implementation.

## Usage

```
/tf-research <ticket-id> [--no-research] [--with-research]
```

## Arguments

- `<ticket-id>` - The ticket to research (e.g., `pt-1234`)

## Flags

| Flag | Description |
|------|-------------|
| `--no-research` | Skip research even if enabled in config |
| `--with-research` | Force enable research step |

## Execution

Follow the **Research** procedure from tf-workflow skill:

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.tf/ralph/AGENTS.md`
   - If referenced, read `.tf/ralph/AGENTS.md` for lessons learned

2. **Prepare ticket artifact directory**
   - Resolve `knowledgeDir` from config (default `.tf/knowledge`)
   - Set `artifactDir = {knowledgeDir}/tickets/{ticket-id}/`
   - `mkdir -p {artifactDir}`

3. **Get ticket details**
   - Run `tk show {ticket}` to get full ticket description

4. **Parse planning references**:
   - "OpenSpec Change: {id}" → `openspec/changes/{id}/`
   - "IRF Seed: {topic}" → `{knowledgeDir}/topics/{topic}/`
   - "Spike: {topic}" → `{knowledgeDir}/topics/{topic}/`

### Step 2: Check Research Prerequisites

Skip if: `--no-research` flag OR (`workflow.enableResearcher` is false AND `--with-research` not set)

**Flag precedence**: If both `--no-research` and `--with-research` are provided, `--with-research` takes precedence (research runs).

### Step 3: Conduct Research

**With existing research:**
- If `{artifactDir}/research.md` exists and is sufficient, use it
- Back-compat: if `{knowledgeDir}/tickets/{ticket}.md` exists, read it and **copy** its contents to `{artifactDir}/research.md` (preserving both files). If both files exist with different content, prefer the new artifact path and log a warning.

**Fresh research (best effort):**
1. **Prefer pi-web-access when available** (tools: `web_search`, `fetch_content`, `get_search_content`).
2. **Fallback to MCP tools** when pi-web-access is unavailable.
   - Check available MCP tools (context7, exa, grep_app, zai-web-search).
3. Synthesize findings

### Step 4: Write research.md

Write to `{artifactDir}/research.md`:

```markdown
# Research: {ticket-id}

## Status
Research completed / Research enabled. No additional external research was performed.

## Rationale
- Why research was done / why not needed

## Context Reviewed
- `tk show {ticket-id}`
- Repo docs / existing topic knowledge
- External sources (if any)

## Sources
- List of sources consulted
```

**Non-negotiable artifact rule**: If the research step is active, you **MUST** ensure a research artifact exists at `{artifactDir}/research.md`.

## Output

**Always written:**
- `{artifactDir}/research.md` - Research findings

**Preserve across chain:**
- `{artifactDir}/ticket_id.txt` - Ticket ID
