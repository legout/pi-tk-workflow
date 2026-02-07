# Critical Review and Cleanup Plan
## pi-ticketflow Project

**Date:** 2026-02-06
**Review Scope:** Complete project audit for legacy code, duplicates, and simplification opportunities

---

## Executive Summary

The pi-ticketflow project shows signs of significant evolution with several areas needing cleanup:

1. **Legacy Bash Implementation** (`tf_legacy.sh`) - A massive 4000+ line bash script that has been superseded by Python CLI
2. **Code Duplication** - `find_project_root()` and related helper functions duplicated across 6+ files
3. **Incomplete `.gitignore`** - Missing standard Python build artifacts
4. **Obsolete/Deprecated Files** - Multiple files from previous architecture iterations
5. **Naming Inconsistencies** - `_new.py` suffix indicates incomplete migration
6. **Documentation Duplication** - Similar content across multiple markdown files
7. **Seed Topics Possibly Obsolete** - Some seed topics may represent completed work

**Estimated Cleanup Impact:**
- Code reduction: ~20-30% in CLI modules
- Improved maintainability through centralized utilities
- Clearer project structure
- Better onboarding experience

---

## Findings by Category

### 1. CRITICAL: Massive Legacy Bash Implementation

**File:** `scripts/tf_legacy.sh` (106,950 bytes, ~4000+ lines)

**Issue:** This appears to be a complete CLI implementation in bash that has been superseded by the Python CLI implementation in `tf_cli/`. The file contains:

- Full command implementations (setup, init, login, sync, doctor, next, etc.)
- Helper functions for version retrieval, config management, etc.
- Comprehensive argument parsing

**Evidence:**
```bash
# The cli.py has this code to fall back to legacy:
def find_legacy_script() -> Optional[Path]:
    # ... looks for tf_legacy.sh
    return None  # Returns None, meaning it's not currently being used
```

**Recommendation:**
- **DELETE** `scripts/tf_legacy.sh` entirely
- Remove all legacy-related code from `cli.py`:
  - `find_legacy_script()` function
  - `run_legacy()` function
  - The `"legacy"` command case in main()
- Keep `scripts/tf_config.py` (it's Python and actively used)

**Risk:** LOW - This code is not being invoked by any current path

---

### 2. HIGH: Code Duplication - Project Root Resolution

**Duplicated across 6+ files:**
- `tf_cli/backlog_ls_new.py`
- `tf_cli/doctor_new.py`
- `tf_cli/next_new.py`
- `tf_cli/priority_reclassify_new.py`
- `tf_cli/ralph_new.py`
- `tf_cli/sync_new.py`

**Pattern:**
```python
def find_project_root() -> Optional[Path]:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir():
            return parent
    return None
```

**Variations:**
- `sync_new.py` includes `.pi` directory as well
- Most don't accept parameters
- Some are inline, some are separate functions

**Recommendation:**
Create `tf_cli/common.py` with shared utilities:

```python
# tf_cli/common.py (NEW FILE)
from pathlib import Path
from typing import Optional

def find_project_root(start: Optional[Path] = None) -> Optional[Path]:
    """Find project root by searching for .tf or .pi directory."""
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".tf").is_dir() or (parent / ".pi").is_dir():
            return parent
    return None

def resolve_project_root(args: argparse.Namespace) -> Path:
    """Resolve project root from args or auto-detect."""
    if getattr(args, "global_install", False):
        print("This command is project-local; do not use --global.", file=sys.stderr)
        raise SystemExit(1)
    if args.project:
        return Path(args.project).expanduser()
    root = find_project_root()
    return root if root else Path.cwd()
```

Then update all 6 files to import and use these functions.

**Files to Refactor:**
1. `backlog_ls_new.py` - Replace inline `find_project_root()`
2. `doctor_new.py` - Replace inline `find_project_root()`
3. `next_new.py` - Replace inline `find_project_root()`
4. `priority_reclassify_new.py` - Replace inline `find_project_root()`
5. `ralph_new.py` - Replace inline `find_project_root()`
6. `sync_new.py` - Remove duplicated implementation, import from common

---

### 3. HIGH: Incomplete `.gitignore`

**Current `.gitignore`:**
```
.coverage
htmlcov/
.tf/ralph/sessions/
```

**Missing Standard Entries:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project-specific
.tf/ralph/sessions/
.tf/knowledge/sessions/
EOF  # binary file
```

**Recommendation:** Update `.gitignore` with comprehensive standard Python entries.

**Risk:** LOW - Just adds more ignored patterns

---

### 4. MEDIUM: Naming Inconsistencies - "_new" Suffix

**Files with `_new.py` suffix:**
- `tf_cli/init_new.py`
- `tf_cli/setup_new.py`
- `tf_cli/sync_new.py`
- `tf_cli/update_new.py`
- `tf_cli/doctor_new.py`
- `tf_cli/next_new.py`
- `tf_cli/backlog_ls_new.py`
- `tf_cli/track_new.py`
- `tf_cli/priority_reclassify_new.py`
- `tf_cli/ralph_new.py`
- `tf_cli/agentsmd_new.py`
- `tf_cli/tags_suggest_new.py`
- `tf_cli/login_new.py`

**Files without suffix (comparable):**
- `tf_cli/cli.py`
- `tf_cli/kb_cli.py`
- `tf_cli/seed_cli.py`
- `tf_cli/component_classifier.py`
- `tf_cli/project_bundle.py`
- `tf_cli/ticket_factory.py`
- `tf_cli/logger.py`
- `tf_cli/session_store.py`
- `tf_cli/kb_helpers.py`
- `tf_cli/version.py`

**Issue:** The `_new` suffix suggests an incomplete migration where old versions were deleted but files weren't renamed.

**Recommendation:**
Rename all `_new.py` files to remove the suffix:

```bash
init_new.py → init.py
setup_new.py → setup.py  # But conflicts with setuptools setup.py
sync_new.py → sync.py
update_new.py → update.py
doctor_new.py → doctor.py
next_new.py → next.py
backlog_ls_new.py → backlog_ls.py
track_new.py → track.py
priority_reclassify_new.py → priority_reclassify.py
ralph_new.py → ralph.py
agentsmd_new.py → agentsmd.py
tags_suggest_new.py → tags_suggest.py
login_new.py → login.py
```

**Special Case:** `setup_new.py` should become `setup_cmd.py` to avoid confusion with `setup.py` (setuptools).

**Update `cli.py` imports accordingly.**

**Risk:** MEDIUM - Requires updating imports and ensuring backward compatibility isn't needed

---

### 5. MEDIUM: Duplicate/Obsolete Documentation

#### 5.1 `ticket_factory.md` vs `ticket_factory_refactoring.md`

**Issue:** Two files documenting the ticket_factory module with overlapping content:
- `docs/ticket_factory.md` (242 lines) - Module documentation
- `docs/ticket_factory_refactoring.md` (179 lines) - Historical refactoring notes

**Recommendation:**
- Keep `docs/ticket_factory.md` as the primary documentation
- Consider merging relevant historical notes into `docs/ticket_factory.md` in a "History" section
- DELETE `docs/ticket_factory_refactoring.md` if historical notes are not valuable

#### 5.2 `docs/AGENTS.md.template` vs `AGENTS.md`

**Issue:** These serve different purposes:
- `AGENTS.md` - Actual project AGENTS.md for this codebase
- `docs/AGENTS.md.template` - Generic template for other projects

**Recommendation:** Keep both - they serve different purposes. The template is used by `install.sh`.

#### 5.3 Root-Level Proposals and Research

**Files:**
- `proposal-irf-improvements.md` (6570 bytes)
- `research.md` (1173 bytes)
- `reviewer-subagent-failure-report.md` (5233 bytes)

**Issue:** These appear to be historical documents that may represent completed work.

**Recommendation:**
- Review each to determine if the proposed improvements have been implemented
- Move completed proposals to `docs/history/` or DELETE if no longer relevant
- Keep `reviewer-subagent-failure-report.md` if it documents a known issue pattern

---

### 6. MEDIUM: Obsolete Seed Topics

**Directory:** `.tf/knowledge/topics/`

**Topics to Review:**
1. `seed-add-versioning/` - Versioning appears to be implemented (VERSION file exists)
2. `seed-add-more-logging-to-ralph-loop/` - Ralph logging exists in `logger.py`
3. `seed-automatic-planning-sessions-linkage/` - Need to verify if implemented
4. `seed-backlog-deps-and-tags/` - Dependencies and tags are implemented
5. `seed-kb-management-commands/` - KB commands exist in `kb_cli.py`
6. `seed-pi-command-reclassify-priorities/` - Priority reclassify exists

**Plan Topics:**
- `plan-auto-planning-sessions-linkage/` - Check if implemented
- `plan-kb-management-cli/` - KB CLI exists
- `plan-simple-kanban-ui-for-tf/` - Need to verify status

**Spike:**
- `spike-pi-non-interactive-logs/` - Check if findings were incorporated

**Recommendation:**
1. Create a script to verify which features have been implemented
2. Archive completed seed/plan topics to `.tf/knowledge/topics/completed/`
3. Update any incomplete seeds with current status
4. Keep `priority-rubric.md` - it's actively used reference material

---

### 7. MEDIUM: Example File in Source Tree

**File:** `tf_cli/ticket_factory_example.py` (158 lines)

**Issue:** Example code in the source tree. This should either be:
- Moved to `examples/` directory
- Moved to documentation
- Converted to a test

**Recommendation:** Move to `examples/ticket_factory_example.py` or integrate as documentation example.

---

### 8. LOW: Build Artifacts in Repository

**Artifacts Found:**
- `htmlcov/` - Coverage reports (partial .gitignore)
- `pi_tk_workflow.egg-info/` - Python package build artifacts
- `tests/__pycache__/` - Python bytecode cache (20 directories)
- `tf_cli/__pycache__/` - Python bytecode cache

**Recommendation:** Ensure `.gitignore` covers these (covered in #3).

---

### 9. LOW: Duplicate Frontmatter Update Logic

**Files:** `sync_new.py`

**Functions:**
- `update_agent_frontmatter()` - Updates YAML frontmatter in agent files
- `update_prompt_frontmatter()` - Updates YAML frontmatter in prompt files

**Issue:** These functions are nearly identical and use a shared `_update_frontmatter()` helper, but could be more generalized.

**Recommendation:** Consolidate into a single function:

```python
def update_frontmatter(file_path: Path, config: dict, name: str) -> bool:
    """Update YAML frontmatter with model/thinking from config."""
    content = file_path.read_text(encoding="utf-8")
    resolved = resolve_meta_model(config, name)
    model = resolved.get("model", "openai-codex/gpt-5.1-codex-mini")
    thinking = resolved.get("thinking", "medium")

    new_content = _update_frontmatter(content, model, thinking)
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False
```

---

### 10. LOW: Utility Function Duplication

**Read JSON Helper:**
```python
# Found in: sync_new.py, scripts/tf_config.py
def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
```

**Recommendation:** Move to `tf_cli/common.py`.

**Merge Helper:**
```python
# Found in: scripts/tf_config.py
def merge(a, b):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out
```

**Recommendation:** Move to `tf_cli/common.py` as `deep_merge_dicts()`.

---

## Detailed Cleanup Plan

### Phase 1: High-Impact, Low-Risk (Week 1)

**Goal:** Remove obvious legacy and fix critical issues

1. **Delete `scripts/tf_legacy.sh`**
   - Remove 4000+ lines of unused code
   - Remove legacy support from `cli.py`
   - Test: Run all commands to ensure nothing breaks

2. **Update `.gitignore`**
   - Add comprehensive Python build artifacts
   - Test: `git status` to verify build artifacts are ignored

3. **Create `tf_cli/common.py`**
   - Add `find_project_root()`
   - Add `resolve_project_root()`
   - Add `read_json()`
   - Add `deep_merge_dicts()`
   - Test: Import and use in one module

4. **Refactor 6 CLI modules to use `common.py`**
   - `backlog_ls_new.py`
   - `doctor_new.py`
   - `next_new.py`
   - `priority_reclassify_new.py`
   - `ralph_new.py`
   - `sync_new.py`
   - Test: Run each CLI command

5. **Move `ticket_factory_example.py`**
   - Move to `examples/ticket_factory_example.py`
   - Update any references

### Phase 2: Code Organization (Week 2)

**Goal:** Improve naming consistency

6. **Rename `_new.py` files**
   - Create migration script to handle renaming
   - Update all imports in `cli.py`
   - Update test imports
   - Test: Full test suite

7. **Consolidate frontmatter update logic**
   - Merge `update_agent_frontmatter()` and `update_prompt_frontmatter()`
   - Test: Run `tf sync` on a test project

8. **Review and clean up documentation**
   - Consolidate `ticket_factory.md` docs
   - Review and archive completed seed topics
   - Update `AGENTS.md` template if needed

### Phase 3: Deep Cleanup (Week 3)

**Goal:** Polish and optimize

9. **Audit seed/plan topics**
   - Verify implementation status of each topic
   - Archive completed work
   - Document outstanding items

10. **Review proposals and research**
    - Determine if `proposal-irf-improvements.md` items are implemented
    - Archive or delete completed proposals
    - Update any remaining TODOs

11. **Code quality improvements**
    - Run pylint/flake8 to identify issues
    - Add type hints where missing
    - Improve docstrings

### Phase 4: Maintenance Improvements (Week 4)

**Goal:** Prevent future accumulation of technical debt

12. **Add pre-commit hooks**
    - Black formatter
    - Flake8 linter
    - MyPy type checking

13. **Update documentation**
    - Add contribution guidelines
    - Document file structure
    - Add architectural decision records (ADRs) for major decisions

14. **Add cleanup checklist to release process**
    - Update `.gitignore` review
    - Remove deprecated files
    - Archive completed topics

---

## Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Delete `tf_legacy.sh` | LOW | Code path already returns None |
| Update `.gitignore` | LOW | Only adds patterns, safe |
| Create `common.py` | LOW | New file, no existing impact |
| Rename `_new.py` files | MEDIUM | Update all imports, test thoroughly |
| Consolidate frontmatter logic | LOW | Same behavior, less code |
| Archive seed topics | MEDIUM | Review implementation status first |
| Delete proposals | LOW | Move to `docs/history/` first |

---

## Success Metrics

**Code Quality:**
- Reduce code duplication by 30%
- Reduce total lines of code by 15-20%
- Improve maintainability index

**Project Clarity:**
- Clear file naming (no `_new` suffix)
- Consistent utility functions
- Well-organized documentation

**Developer Experience:**
- Faster onboarding
- Easier to understand code structure
- Less confusion about which files to use

---

## Next Steps

1. **Immediate (This Week):**
   - Delete `scripts/tf_legacy.sh`
   - Update `.gitignore`
   - Create `tf_cli/common.py`

2. **Short-term (Next 2 Weeks):**
   - Refactor CLI modules to use common utilities
   - Rename `_new.py` files
   - Move example file

3. **Long-term (Next Month):**
   - Audit and archive seed/plan topics
   - Consolidate documentation
   - Add maintenance processes

---

## Appendix: File Inventory

**Total Files:**
- Python source files: 28 (in `tf_cli/`)
- Test files: 19 (in `tests/`)
- Documentation: 15 markdown files
- Prompts: 19 markdown files
- Agents: 9 markdown files
- Skills: 5 SKILL.md files

**Large Files (>500 lines):**
- `scripts/tf_legacy.sh` - ~4000 lines (DELETE)
- `ralph_new.py` - 1200 lines
- `kb_cli.py` - 942 lines
- `priority_reclassify_new.py` - 828 lines
- `doctor_new.py` - 643 lines
- `ticket_factory.py` - 583 lines
- `logger.py` - 567 lines

**Directories to Clean:**
- `htmlcov/` - Should be gitignored
- `pi_tk_workflow.egg-info/` - Should be gitignored
- `__pycache__/` directories (20 total) - Should be gitignored

---

**End of Critical Review and Cleanup Plan**
