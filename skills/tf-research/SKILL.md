---
name: tf-research
description: Research phase for TF workflow - gather context and knowledge for ticket implementation. Use at the start of workflow to understand the ticket and gather relevant information.
---

# TF Research Skill

Research phase for the IRF (Implement → Review → Fix → Close) workflow.

## When to Use This Skill

- At the start of ticket implementation workflow
- When gathering context and knowledge for a ticket
- Before the implementation phase

## Prerequisites

- `tk` CLI available: `which tk`
- Ticket exists: `tk show <ticket-id>` succeeds

## Procedure

### Step 1: Re-Anchor Context

1. **Read root AGENTS.md** (if exists)
   - Check if it references `.tf/ralph/AGENTS.md`
   - If referenced, read for lessons learned

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

**Flag precedence**: If both `--no-research` and `--with-research` are provided, `--with-research` takes precedence.

### Step 3: Conduct Research

**With existing research:**
- If `{artifactDir}/research.md` exists and is sufficient, use it
- Back-compat: if `{knowledgeDir}/tickets/{ticket}.md` exists, migrate to `{artifactDir}/research.md`

**Fresh research (best effort):**
1. **Prefer pi-web-access when available** (tools: `web_search`, `fetch_content`, `get_search_content`)
2. **Fallback to MCP tools** when pi-web-access is unavailable (context7, exa, zai-web-search)
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

**Non-negotiable artifact rule**: If research step is active, you **MUST** ensure a research artifact exists at `{artifactDir}/research.md`.

## Output Artifacts

| File | Description |
|------|-------------|
| `{artifactDir}/research.md` | Research findings |
| `{artifactDir}/ticket_id.txt` | Ticket ID (preserve for chain) |

## Error Handling

- If research tools unavailable, write stub noting limitations
- If ticket not found, fail fast with error message
