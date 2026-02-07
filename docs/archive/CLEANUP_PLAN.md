# pi-ticketflow Cleanup & Simplification Plan

**Generated:** February 7, 2026  
**Review Scope:** Entire project structure, code duplication, legacy artifacts

---

## Executive Summary

The project shows clear signs of **organic evolution** from a bash-first approach to a Python CLI. There's significant **code duplication**, **legacy artifacts**, and **architectural debt** that can be cleaned up.

### Key Statistics
- Total files: 240
- Python code: ~5,500 LOC
- Legacy bash: 4,078 LOC
- Duplicate functions: 10+ instances

---

## Detailed Findings

### 1. Critical: Massive Bash/Python Code Duplication

| File | Lines | Issue |
|------|-------|-------|
| `scripts/tf_legacy.sh` | 4,078 | Contains full implementations of `ralph`, `agentsmd`, `seed`, `track`, `next`, `backlog-ls`, `login`, `sync`, `update`, `doctor` |
| `scripts/tf_config.py` | ~350 | Duplicate of `.tf/scripts/tf_config.py` (identical) |

**Problem:** The entire bash script duplicates functionality now available in Python modules. This is legacy debt that should be removed once the Python CLI is stable.

### 2. Duplicated Utility Functions

Each of these functions appears in 6+ Python modules:

```
find_project_root()  → 6 duplicate implementations
read_json()          → 4 duplicate implementations
```

**Files affected:**
- `tf_cli/backlog_ls_new.py`
- `tf_cli/doctor_new.py`
- `tf_cli/next_new.py`
- `tf_cli/priority_reclassify_new.py`
- `tf_cli/ralph_new.py`
- `tf_cli/sync_new.py`

### 3. Legacy Naming Convention

All Python modules have `_new` suffix, indicating migration from older implementations:

| Current | Status |
|---------|--------|
| `ralph_new.py` | Ready to rename |
| `doctor_new.py` | Ready to rename |
| `sync_new.py` | Ready to rename |
| `init_new.py` | Ready to rename |
| `setup_new.py` | Ready to rename |
| `login_new.py` | Ready to rename |
| `next_new.py` | Ready to rename |
| `track_new.py` | Ready to rename |

### 4. Orphaned/Stale Root Files

| File | Size | Recommendation |
|------|------|----------------|
| `EOF` | 0 bytes | Delete (accidental) |
| `research.md` | 1.2 KB | Move to `.tf/knowledge/` or archive |
| `proposal-irf-improvements.md` | 6.6 KB | Review and archive if implemented |
| `reviewer-subagent-failure-report.md` | 5.2 KB | Archive if historical value exists |

### 5. Documentation Overlap

| File 1 | File 2 | Action |
|--------|--------|--------|
| `docs/ticket_factory.md` | `docs/ticket_factory_refactoring.md` | Merge refactoring docs into main doc |
| `README.md` (25KB) | `docs/architecture.md` | Cross-reference, some consolidation possible |

### 6. Build Artifacts in Repository

These should be in `.gitignore`:

```
htmlcov/                    # Coverage HTML reports
pi_tk_workflow.egg-info/    # Package metadata
tests/__pycache__/          # Python bytecode cache
tf_cli/__pycache__/         # Python bytecode cache
```

### 7. Configuration File Duplication

```
scripts/tf_config.py         # Source (in repo)
.tf/scripts/tf_config.py     # Copied during install
```

The `.tf/scripts/` copy is created at install time. The `scripts/` version should remain the source of truth.

---

## Cleanup & Simplification Plan

### Phase 1: Delete Legacy Artifacts (Quick Wins)

**Goal:** Remove obvious dead code and build artifacts

```bash
# Delete massive legacy bash script (after confirming Python CLI is complete)
rm scripts/tf_legacy.sh

# Delete orphaned files
rm EOF
rm research.md                    # Move to .tf/knowledge/ if needed
rm proposal-irf-improvements.md    # Archive first if desired
rm reviewer-subagent-failure-report.md

# Delete build artifacts
rm -rf htmlcov/
rm -rf pi_tk_workflow.egg-info/

# Update .gitignore
cat >> .gitignore <<'EOF'
# Build artifacts
htmlcov/
*.egg-info/
__pycache__/
*.pyc
EOF
```

**Estimated Effort:** 1-2 hours  
**Risk:** Low (confirm Python CLI works first)

### Phase 2: Consolidate Utility Functions

**Goal:** Eliminate code duplication by creating shared module

**Create `tf_cli/common.py`:**

```python
"""Shared utilities for tf_cli modules - eliminates duplication."""

from pathlib import Path
from typing import Optional, Any
import json
import re


def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Find the .tf project root directory."""
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return None


def read_json(path: Path) -> dict:
    """Safely read JSON file, returning empty dict on error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def atomic_write_json(path: Path, data: dict) -> None:
    """Atomically write JSON file to avoid corruption."""
    import tempfile
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def read_root_file(path: Path) -> str:
    """Safely read text file, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def merge_configs(global_config: dict, local_config: dict) -> dict:
    """Deep merge two configuration dictionaries."""
    out = dict(global_config)
    for k, v in local_config.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge_configs(out[k], v)
        else:
            out[k] = v
    return out
```

**Update affected modules to import from common.py:**

```python
# In each tf_cli/*_new.py file, replace:
from pathlib import Path
import json

def read_json(path: Path):
    # ... 5 lines of code

# With:
from tf_cli.common import read_json
```

**Estimated Effort:** 4-6 hours  
**Risk:** Medium (requires careful testing of all CLI commands)

### Phase 3: Rename `_new` Modules

**Goal:** Clean up naming convention

```bash
# Rename all _new.py files
cd tf_cli
mv ralph_new.py ralph.py
mv doctor_new.py doctor.py
mv sync_new.py sync.py
mv init_new.py init.py
mv setup_new.py setup.py
mv login_new.py login.py
mv next_new.py next.py
mv track_new.py track.py
mv backlog_ls_new.py backlog_ls.py
mv agentsmd_new.py agentsmd.py
mv priority_reclassify_new.py priority_reclassify.py
mv tags_suggest_new.py tags_suggest.py
mv project_bundle_new.py project_bundle.py
```

**Update imports in:**

1. `tf_cli/__init__.py`
2. `tf_cli/new_cli.py` (rename to `router.py`)
3. `tf_cli/cli.py`
4. Any tests referencing these modules

**Estimated Effort:** 2-3 hours  
**Risk:** Medium (requires updating all import statements)

### Phase 4: Simplify CLI Entry Points

**Goal:** Remove legacy detection code

**Before (cli.py):**
```python
def find_legacy_script() -> Optional[Path]:
    # Complex lookup logic for legacy bash script
    
def run_legacy(args: list[str]) -> int:
    legacy = find_legacy_script()
    if not legacy:
        print("ERROR: Legacy shell CLI not found.")
        return 1
    return subprocess.call(["bash", str(legacy), *args])
```

**After (cli.py):**
- Remove `find_legacy_script()` and `run_legacy()` functions
- Merge `new_cli.py` functionality directly into `cli.py`
- Remove legacy detection code paths

**Estimated Effort:** 1-2 hours  
**Risk:** Low (cleanup only, no functionality change)

### Phase 5: Consolidate Documentation

**Goal:** Reduce overlap and stale content

**Actions:**

1. **Merge refactoring docs:**
   - Review `docs/ticket_factory_refactoring.md`
   - Extract any useful patterns to `docs/ticket_factory.md`
   - Delete `docs/ticket_factory_refactoring.md`

2. **Archive stale root files:**
   ```bash
   mkdir -p docs/archive
   mv proposal-irf-improvements.md docs/archive/
   mv reviewer-subagent-failure-report.md docs/archive/
   ```

3. **Update root README:**
   - Add link to `docs/architecture.md`
   - Remove duplicated content

**Estimated Effort:** 1-2 hours  
**Risk:** Low (documentation only)

---

## Impact Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Python LOC | ~5,500 | ~4,800 | -13% |
| Legacy Bash LOC | 4,078 | 0 | -100% |
| Total Files | 240 | ~200 | -17% |
| Duplicate Functions | 10+ instances | 0 | -100% |
| Build Artifacts | 30+ files | 0 | -100% |

---

## Priority Recommendations

| Priority | Task | Effort | Risk |
|----------|------|--------|------|
| **P0** | Verify Python CLI complete replacement | 2h | Medium |
| **P1** | Delete `scripts/tf_legacy.sh` | 5min | Low |
| **P1** | Create `tf_cli/common.py` | 4h | Medium |
| **P2** | Rename `_new` modules | 3h | Medium |
| **P2** | Simplify CLI entry points | 2h | Low |
| **P3** | Archive stale documentation | 1h | Low |

---

## Rollback Plan

If issues arise during cleanup:

1. **Git commits:** Each phase should be a separate commit for easy rollback
2. **Backup legacy script:**
   ```bash
   git mv scripts/tf_legacy.sh archive/tf_legacy.sh.bak
   ```
3. **Keep old module names:** Use git rename to preserve history:
   ```bash
   git mv tf_cli/ralph_new.py tf_cli/ralph.py
   ```

---

## Verification Steps

After each phase, run:

```bash
# Full CLI test
python -m tf_cli.cli --version
python -m tf_cli.cli --help

# Test specific commands
python -m tf_cli.cli ralph --help
python -m tf_cli.cli doctor --help

# Run tests
pytest tests/ -v

# Check for imports
python -c "from tf_cli import *; print('OK')"
```

---

## Open Questions

1. Is the Python CLI fully feature-complete compared to bash version?
2. Are there any users relying on `scripts/tf_legacy.sh` directly?
3. Should stale proposal docs be archived or deleted?
4. Is `project_bundle_new.py` needed or is it experimental?

---

*This plan was generated from a comprehensive code review of the pi-ticketflow project.*
