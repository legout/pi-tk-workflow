# IRF Workflow Simplification: Subagent Analysis

## Problem Statement

The current IRF workflows use many subagents, which introduces fragility:
- Each subagent spawn is a potential failure point
- Nested subagents (e.g., prompt → irf-planner → researcher-fetch ×3) compound the risk
- Many subagents exist only to use a different model, not for parallelism

## Key Insight

**Subagents provide two benefits:**
1. **Parallelism** - run multiple tasks simultaneously (irreplaceable)
2. **Isolation** - separate context/working directory

**If we only need a different model**, `pi-model-switch` is strictly better:
- Faster (no spawn overhead)
- More reliable (no IPC failures)
- Shared context (no file passing needed)

---

## Part 1: Implementation Workflow (`/irf`)

### Analysis

| Step | Current | Why Subagent? | Verdict |
|------|---------|---------------|---------|
| researcher | Subagent spawning 3 sub-subagents | Parallel MCP fetches | **Replace** - Sequential is acceptable |
| implementer | Subagent | Different model | **Replace** - Use model-switch |
| reviewer-general | Subagent (parallel) | **True parallelism** | **Keep** |
| reviewer-spec-audit | Subagent (parallel) | **True parallelism** | **Keep** |
| reviewer-second-opinion | Subagent (parallel) | **True parallelism** | **Keep** |
| review-merge | Subagent | Different model | **Replace** - Use model-switch |
| fixer | Subagent | Different model | **Replace** - Use model-switch |
| closer | Subagent | Different model | **Replace** - Use model-switch |

### Solution: `/irf-lite`

- Uses `pi-model-switch` for sequential model changes
- Keeps subagents **only** for parallel reviews (3 subagents)
- Reduces subagent spawns from 6-8 to 3
- Cuts failure points by ~60%

---

## Part 2: Planning Workflows

### Analysis

| Command | Current Flow | Uses Parallelism? | Subagent Necessary? |
|---------|--------------|-------------------|---------------------|
| `/irf-seed` | prompt → irf-planner | **No** | **No** |
| `/irf-backlog` | prompt → irf-planner | **No** | **No** |
| `/irf-baseline` | prompt → irf-planner | **No** | **No** |
| `/irf-followups` | prompt → irf-planner | **No** | **No** |
| `/irf-from-openspec` | prompt → irf-planner | **No** | **No** |
| `/irf-spike` | prompt → irf-planner → 3× researcher-fetch | **Yes** (nested) | **Partially** |

### Key Finding: `irf-planner` is a "God Agent" Anti-Pattern

The `irf-planner` agent handles 6 different modes via a mode prefix. This design:
- Forces a subagent spawn just to route to the right behavior
- The subagent exists only to use a different model
- All logic could be in the prompt template with model-switch

### Solution: `-lite` Variants

| Command | Subagents Before | Subagents After |
|---------|------------------|-----------------|
| `/irf-seed-lite` | 1 | 0 |
| `/irf-backlog-lite` | 1 | 0 |
| `/irf-baseline-lite` | 1 | 0 |
| `/irf-followups-lite` | 1 | 0 |
| `/irf-from-openspec-lite` | 1 | 0 |
| `/irf-spike-lite` | 4 | 0 (or 3 with `--parallel`) |

**Total planning workflow reduction:** 9 subagents → 0-3 subagents

---

## Summary: Total Subagent Reduction

### Implementation Workflow

| Workflow | Original | Lite |
|----------|----------|------|
| `/irf` | 6-8 subagents | - |
| `/irf-lite` | - | 3 subagents |

### Planning Workflows

| Workflow | Original | Lite |
|----------|----------|------|
| `/irf-seed` | 1 | 0 |
| `/irf-backlog` | 1 | 0 |
| `/irf-baseline` | 1 | 0 |
| `/irf-followups` | 1 | 0 |
| `/irf-from-openspec` | 1 | 0 |
| `/irf-spike` | 4 | 0-3 |

### Grand Total

| Scenario | Max Subagent Spawns |
|----------|---------------------|
| Original workflows | 14-17 |
| Lite workflows | 3-6 |
| **Reduction** | **~70-80%** |

---

## Files Created

### Implementation
- `prompts/irf-lite.md` - Simplified implementation workflow

### Planning
- `prompts/irf-seed-lite.md`
- `prompts/irf-backlog-lite.md`
- `prompts/irf-baseline-lite.md`
- `prompts/irf-followups-lite.md`
- `prompts/irf-from-openspec-lite.md`
- `prompts/irf-spike-lite.md`

### Config
- `config/model-aliases.json` - Example aliases for pi-model-switch

---

## Extension Requirements

### For Lite Workflows (Recommended)

```bash
pi install npm:pi-subagents      # For parallel reviews only
pi install npm:pi-model-switch   # For on-the-fly model switching
pi install npm:pi-mcp-adapter    # Optional, for research MCP tools
```

### For Original Workflows (Fallback)

```bash
pi install npm:pi-subagents      # For all subagent spawns
pi install npm:pi-mcp-adapter    # Optional, for research MCP tools
```

**Finding:** `pi-interactive-shell` is NOT used anywhere in the workflow. It can be removed from requirements.

---

## Migration Path

1. **Test `pi-model-switch`** - Verify it works as expected in your environment
2. **Try `-lite` variants** - Start with `/irf-lite` on a test ticket
3. **Compare reliability** - Track failure rates between original and lite
4. **Migrate gradually** - Switch to lite variants as confidence grows
5. **Deprecate originals** - Once lite is proven, consider removing originals

---

## Original Agents (Kept as Fallback)

The following agents are kept for the original workflows:
- `agents/irf-planner.md` - God agent for planning (used by original prompts)
- `agents/researcher.md` - Research coordinator
- `agents/researcher-fetch.md` - Individual research fetcher

These can be removed once lite workflows are validated and original prompts are deprecated.
