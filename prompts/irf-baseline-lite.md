---
description: Capture brownfield status quo into baseline artifacts. Lite version - no subagent, uses model-switch.
---

# IRF Baseline (Lite)

Capture a status-quo baseline for an existing project. This version runs inline with model-switch instead of spawning a subagent.

## Invocation

```
/irf-baseline-lite <optional focus>
```

Focus is optional - can specify a subsystem or area to emphasize.

## Prerequisites

Verify `switch_model` tool is available. If not, suggest using `/irf-baseline` (original) instead.

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

### Step 3: Determine Topic ID

```bash
repo_name=$(basename $(pwd))
topic_id="baseline-${repo_name}"
```

Convert to lowercase, replace non-alphanumeric with dashes.

### Step 4: Create Topic Directory

```bash
mkdir -p "${knowledgeDir}/topics/${topic_id}"
```

### Step 5: Scan Project

**Read high-signal files (if they exist):**
- `README.md`
- `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`
- `requirements.txt` / `Pipfile`
- `Makefile` / `justfile`
- `docker-compose.yml` / `Dockerfile`
- `.github/workflows/*.yml`
- `tsconfig.json` / `setup.py` / `setup.cfg`

**Scan for structure:**
```bash
# Entry points
find . -maxdepth 3 -name "main.*" -o -name "app.*" -o -name "index.*" -o -name "server.*" 2>/dev/null | head -20

# Tests
find . -type d -name "test*" -o -name "__tests__" -o -name "spec" 2>/dev/null | head -10

# Source directories
find . -maxdepth 2 -type d -name "src" -o -name "lib" -o -name "pkg" 2>/dev/null
```

**If focus area specified in `$@`:**
- Prioritize scanning that area
- Note it in the baseline

### Step 6: Write Baseline Artifacts

Write to `${knowledgeDir}/topics/${topic_id}/`:

**overview.md:**
```markdown
# Baseline: ${repo_name}

Brief summary of the project based on README and structure.

## Keywords
- keyword1
- keyword2

## Focus Area
${focus from $@ or "Full project"}
```

**baseline.md:**
```markdown
# Project Baseline: ${repo_name}

Date: ${today}

## Project Type
${e.g., "TypeScript CLI application", "Python web service"}

## Architecture Overview
${High-level description of structure}

## Key Components
- Component 1: description
- Component 2: description

## Entry Points
- ${path}: ${purpose}

## Build & Run
${Commands from package.json scripts, Makefile, etc.}

## Current State
${Observations about code quality, completeness}
```

**risk-map.md:**
```markdown
# Risk Map: ${repo_name}

## Technical Risks
| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| ${risk1} | High/Medium/Low | High/Medium/Low | ${mitigation} |

## Dependency Risks
- ${dep risk 1}
- ${dep risk 2}

## Knowledge Risks
- ${areas with unclear ownership or documentation}
```

**test-inventory.md:**
```markdown
# Test Inventory: ${repo_name}

## Test Directories
- ${path}: ${type of tests}

## Test Commands
- `${command}`: ${description}

## Coverage
${Observations or "Unknown - no coverage tool configured"}

## Gaps
- ${untested area 1}
- ${untested area 2}
```

**dependency-map.md:**
```markdown
# Dependency Map: ${repo_name}

## Runtime Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| ${pkg} | ${version} | ${purpose} |

## Dev Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| ${pkg} | ${version} | ${purpose} |

## External Services
- ${service}: ${purpose}

## Concerns
- ${outdated deps, security issues, etc.}
```

**sources.md:**
```markdown
# Sources

- Project files scanned: ${list}
- Date captured: ${today}
```

### Step 7: Update Knowledge Index

Read `${knowledgeDir}/index.json`, add or update topic entry:

```json
{
  "id": "${topic_id}",
  "title": "Baseline: ${repo_name}",
  "keywords": ["baseline", "${repo_name}", ...],
  "overview": "topics/${topic_id}/overview.md",
  "sources": "topics/${topic_id}/sources.md"
}
```

### Step 8: Report Results

```
Created baseline for ${repo_name} in ${knowledgeDir}/topics/${topic_id}/:
- overview.md
- baseline.md
- risk-map.md
- test-inventory.md
- dependency-map.md
- sources.md

Key findings:
- ${summary of architecture}
- ${key risks identified}
- ${test coverage status}

Next steps:
- Review and refine baseline artifacts
- Use /irf-seed-lite for new feature ideas
- Use /irf-lite <ticket> for implementation
```

## Comparison to /irf-baseline

| Aspect | /irf-baseline | /irf-baseline-lite |
|--------|---------------|-------------------|
| Subagents | 1 (irf-planner) | 0 |
| Model change | Via subagent | Via switch_model |
| Reliability | Lower | Higher |
