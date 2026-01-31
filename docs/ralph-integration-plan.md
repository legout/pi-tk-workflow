# Implementation Plan: Ralph Loop Integration for pi-tk-workflow

## Overview

This plan integrates the Ralph Loop methodology into the IRF workflow, enabling autonomous ticket processing with:
- **Re-anchoring**: Fresh context per iteration
- **Lessons Learned**: Persistent wisdom in `.pi/ralph/AGENTS.md`
- **Progress Tracking**: External state in `.pi/ralph/progress.md`
- **Promise Sigil**: Completion signal for loop termination

---

## Directory Structure

```
.pi/
├── ralph/
│   ├── AGENTS.md           # Lessons learned (referenced from root)
│   ├── progress.md         # Current loop state and history
│   ├── config.json         # Ralph loop configuration
│   └── runs/               # Per-run artifacts (optional)
│       └── <run-id>/
│           ├── started.txt
│           ├── completed.txt
│           └── summary.md
├── knowledge/              # Existing knowledge base
│   ├── index.json
│   ├── topics/
│   └── tickets/
└── workflows/
    └── implement-review-fix-close/
        └── config.json
```

---

## Phase 1: Foundation

### 1.1 Create Ralph Directory Structure

**Files to create:**

**`.pi/ralph/AGENTS.md`** (template):
```markdown
# Ralph Loop: Lessons Learned

This file contains lessons learned during autonomous ticket processing.
It is read by the implementer at the start of each iteration.

## Project Patterns
<!-- Discovered patterns and conventions -->

## Gotchas
<!-- Things that caused issues and how to avoid them -->

## Successful Strategies
<!-- Approaches that worked well -->

## Technical Debt Notes
<!-- Known issues to address later -->

---
<!-- Entries below are auto-appended by the closer agent -->
```

**`.pi/ralph/progress.md`** (template):
```markdown
# Ralph Loop Progress

## Current State
- Status: IDLE | RUNNING | PAUSED | COMPLETE
- Current ticket: (none)
- Started: (not started)

## Statistics
- Tickets completed: 0
- Tickets failed: 0
- Total iterations: 0

## History
<!-- Auto-appended entries -->
```

**`.pi/ralph/config.json`**:
```json
{
  "maxIterations": 50,
  "maxIterationsPerTicket": 5,
  "ticketQuery": "tk list --status ready --limit 1 --id-only",
  "completionQuery": "tk list --status ready | grep -q .",
  "sleepBetweenTickets": 5000,
  "sleepBetweenRetries": 10000,
  "writeProgressAfterEach": true,
  "writeLessonsAfterEach": true,
  "includeKnowledgeBase": true,
  "includePlanningDocs": true,
  "promiseOnComplete": true
}
```

### 1.2 Update Root AGENTS.md Reference

Add to root `AGENTS.md`:
```markdown
## Ralph Loop Context

When running in a Ralph loop, read `.pi/ralph/AGENTS.md` for:
- Lessons learned from previous iterations
- Project-specific patterns discovered during implementation
- Known gotchas and successful strategies

Check `.pi/ralph/progress.md` for current loop state.
```

---

## Phase 2: Agent Updates

### 2.1 Update `implementer.md`

**Add to "Required Steps" after step 2:**

```markdown
3. **Read Ralph context** (if present):
   - Check if `.pi/ralph/AGENTS.md` exists
   - If yes, read it for lessons learned and patterns
   - Apply any relevant guidance to the implementation
```

**Add to existing "Check knowledge base" step:**

```markdown
2. **Check knowledge base and planning docs**:
   - Read relevant docs from `.pi/knowledge/tickets/{ticket}.md` if exists
   - Check ticket description for OpenSpec references (look for "OpenSpec Change:" in description)
   - If OpenSpec reference found, read the linked `proposal.md`, `design.md`, and `tasks.md`
   - Read any IRF planning docs referenced (seed.md, baseline.md, spike.md)
```

### 2.2 Update `closer.md`

**Add new steps before "Close ticket":**

```markdown
### Update Ralph Progress (if Ralph loop active)

Check if `.pi/ralph/progress.md` exists. If yes:

1. Read current progress
2. Update statistics:
   - Increment "Tickets completed" or "Tickets failed"
   - Increment "Total iterations"
3. Append to History section:

```markdown
### {ticket-id} - {timestamp}
- Status: CLOSED | FAILED
- Summary: {one-line summary}
- Issues fixed: {count}
- Duration: {if available}
```

### Synthesize Lessons Learned

If `.pi/ralph/AGENTS.md` exists:

1. Review the implementation and review artifacts
2. Identify any lessons worth preserving:
   - New patterns discovered
   - Gotchas encountered
   - Successful strategies
   - Technical debt noted
3. If lessons exist, append to `.pi/ralph/AGENTS.md`:

```markdown
## Lesson from {ticket-id} ({date})

**Context:** {brief context}

**Lesson:** {what was learned}

**Recommendation:** {how to apply in future}
```

### Output Promise Sigil

After successful ticket closure, if all acceptance criteria met:
```
<promise>TICKET_COMPLETE</promise>
```

If this was the last ticket in the queue (no more "ready" tickets):
```
<promise>COMPLETE</promise>
```
```

### 2.3 Update `fixer.md`

**Add to output format:**

```markdown
## Lessons for Future Iterations

If any fixes required understanding project-specific patterns or working around gotchas, note them here for inclusion in `.pi/ralph/AGENTS.md`:

- Pattern: {description}
- Gotcha: {description}
```

---

## Phase 3: Prompt Updates

### 3.1 Create `/ralph-start` Prompt

**File: `prompts/ralph-start.md`**

```markdown
---
description: Start a Ralph loop to process tickets autonomously until backlog is empty.
---

# Ralph Loop Start

Initialize and run a Ralph loop for autonomous ticket processing.

## Invocation

```
/ralph-start [--max-iterations N] [--ticket-filter QUERY] [--dry-run]
```

## Prerequisites

1. Verify `.pi/ralph/` directory exists, create if not
2. Verify `tk` CLI is available
3. Check for pending tickets: `tk list --status ready`

## Execution

### Step 1: Initialize Ralph State

Create/update `.pi/ralph/progress.md`:
```markdown
## Current State
- Status: RUNNING
- Started: {timestamp}
- Max iterations: {N}

## Queue
{output of tk list --status ready}
```

### Step 2: Run Loop

Use the `ralph_loop` tool:

```json
{
  "conditionCommand": "tk list --status ready | grep -q . && echo true || echo false",
  "task": "Pick the next ready ticket and run /irf-lite on it with --auto flag. After completion, check if more tickets remain.",
  "maxIterations": {N from args or config},
  "sleepMs": 5000
}
```

Or manual loop logic:
```
while tk list --status ready | grep -q .; do
  TICKET=$(tk list --status ready --limit 1 --id-only)
  
  # Re-anchor: Read current state
  Read .pi/ralph/AGENTS.md for lessons
  Read .pi/ralph/progress.md for context
  
  # Execute
  /irf-lite $TICKET --auto
  
  # Check for promise sigil in output
  if output contains "<promise>COMPLETE</promise>"; then
    break
  fi
done
```

### Step 3: Finalize

Update `.pi/ralph/progress.md`:
```markdown
## Current State
- Status: COMPLETE
- Finished: {timestamp}
- Total tickets processed: {count}
```

Output:
```
<promise>COMPLETE</promise>

Ralph loop finished. Processed {N} tickets.
See .pi/ralph/progress.md for details.
```
```

### 3.2 Create `/ralph-status` Prompt

**File: `prompts/ralph-status.md`**

```markdown
---
description: Check Ralph loop status and progress.
---

# Ralph Status

Show current Ralph loop state.

## Invocation

```
/ralph-status
```

## Execution

1. Read `.pi/ralph/progress.md`
2. Read `.pi/ralph/AGENTS.md` (count lessons)
3. Query ticket queue: `tk list --status ready`

## Output

```
## Ralph Loop Status

State: {IDLE|RUNNING|COMPLETE}
Tickets in queue: {count}
Tickets completed: {count}
Lessons learned: {count}

### Recent History
{last 5 entries from progress.md}

### Next Ticket
{tk show {next-ticket-id} --brief}
```
```

### 3.3 Update `/irf-lite` for Ralph Awareness

**Add to `prompts/irf-lite.md`:**

```markdown
## Ralph Loop Integration

When running inside a Ralph loop (`.pi/ralph/progress.md` exists with status RUNNING):

1. **Re-anchor at start:**
   - Read `.pi/ralph/AGENTS.md` for lessons learned
   - Read `.pi/ralph/progress.md` for context
   - Read `.pi/knowledge/tickets/{ticket}.md` if exists

2. **Check for planning doc references:**
   - Parse ticket description for "OpenSpec Change:" reference
   - If found, read linked OpenSpec artifacts
   - Parse for "Seed:" or "Spike:" references to IRF planning docs
   - Read any linked planning artifacts from `.pi/knowledge/topics/`

3. **Update progress on completion:**
   - Append to `.pi/ralph/progress.md`
   - Synthesize lessons to `.pi/ralph/AGENTS.md` if applicable

4. **Output promise sigil:**
   - `<promise>TICKET_COMPLETE</promise>` after successful close
```

---

## Phase 4: Planning Doc Integration

### 4.1 Enhance Ticket Descriptions with References

**Update `/irf-from-openspec-lite.md` ticket description template:**

```markdown
## Origin
OpenSpec Change: ${change_id}
OpenSpec Path: ${change_dir}
Task from: ${change_dir}/tasks.md

## Planning References
- Proposal: ${change_dir}/proposal.md
- Design: ${change_dir}/design.md
- Scope: ${change_dir}/scope.md (if exists)

## Description
${task description}
```

**Update `/irf-backlog-lite.md` ticket description template:**

```markdown
## Origin
IRF Seed: ${topic_id}
Seed Path: ${knowledgeDir}/topics/${topic_id}/seed.md

## Planning References
- Seed: ${seed_path}
- MVP Scope: ${mvp_scope_path}
- Success Metrics: ${metrics_path}

## Description
${task description}
```

### 4.2 Create Knowledge Base Link in Tickets

**Update all ticket creation to include:**

```markdown
## Knowledge Base
- Ticket Brief: .pi/knowledge/tickets/{ticket-id}.md (created after research)
- Related Topics: (populated by researcher)
```

---

## Phase 5: Enhanced Traceability

### 5.1 Ticket → Planning Doc Traceability

| Source | Ticket Tag | Description Field | Files Referenced |
|--------|------------|-------------------|------------------|
| `/irf-from-openspec` | `openspec` | "OpenSpec Change: {id}" | proposal.md, design.md, tasks.md |
| `/irf-backlog` | `backlog` | "IRF Seed: {topic-id}" | seed.md, mvp-scope.md |
| `/irf-followups` | `followup` | "From Review: {ticket-id}" | review.md |
| `/irf-spike` | `spike` | "Spike: {topic-id}" | spike.md |

### 5.2 Implementer Context Loading

```
On ticket start:
1. Parse description for "OpenSpec Change:", "IRF Seed:", "Spike:", "From Review:"
2. Load referenced planning docs
3. Load .pi/knowledge/tickets/{ticket-id}.md if exists
4. Load .pi/ralph/AGENTS.md for lessons
5. Proceed with implementation
```

---

## Phase 6: File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `.pi/ralph/AGENTS.md` | Lessons learned storage |
| `.pi/ralph/progress.md` | Loop state and history |
| `.pi/ralph/config.json` | Ralph loop configuration |
| `prompts/ralph-start.md` | Start Ralph loop |
| `prompts/ralph-status.md` | Check Ralph status |

### Updated Files

| File | Changes |
|------|---------|
| `agents/implementer.md` | Read Ralph context, load planning docs |
| `agents/closer.md` | Update progress, synthesize lessons, output promise |
| `agents/fixer.md` | Note lessons for future iterations |
| `prompts/irf-lite.md` | Ralph loop awareness, re-anchoring |
| `prompts/irf-from-openspec-lite.md` | Enhanced ticket description with paths |
| `prompts/irf-backlog-lite.md` | Enhanced ticket description with paths |
| `prompts/irf-followups-lite.md` | Enhanced ticket description with paths |
| `install.sh` | Create .pi/ralph/ directory |
| `bin/irf` | Add ralph-init command |

---

## Phase 7: Implementation Order

### Sprint 1: Foundation (Essential)
1. Create `.pi/ralph/` directory structure and templates
2. Update `implementer.md` to read Ralph context
3. Update `closer.md` to write progress and lessons
4. Update `closer.md` to output promise sigil

### Sprint 2: Loop Control
5. Create `prompts/ralph-start.md`
6. Create `prompts/ralph-status.md`
7. Update `prompts/irf-lite.md` for Ralph awareness

### Sprint 3: Traceability
8. Enhance ticket descriptions in all planning prompts
9. Update `implementer.md` to parse and load planning docs
10. Add OpenSpec path references to ticket creation

### Sprint 4: Polish
11. Update `install.sh` and `bin/irf` for Ralph initialization
12. Add `bin/irf ralph-init` command
13. Documentation updates
14. Testing and validation

---

## Open Questions

1. **Should lessons be auto-pruned?** 
   - Risk: `.pi/ralph/AGENTS.md` grows indefinitely
   - Option: Keep last N lessons, or summarize periodically

2. **Should failed tickets be retried?**
   - Current: Move on to next ticket
   - Option: Retry with backoff, max retries in config

3. **Should we track token/cost metrics?**
   - Option: Add to progress.md per-ticket cost estimates

4. **Should planning docs be copied into ticket brief?**
   - Current: Reference by path
   - Option: Extract key sections into `.pi/knowledge/tickets/{id}.md`

5. **Multi-agent Ralph (future)?**
   - Run multiple IRF chains in parallel on different tickets
   - Requires ticket locking mechanism
