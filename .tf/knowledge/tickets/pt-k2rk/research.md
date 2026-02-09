# Research: pt-k2rk - Inventory tf_cli packaging + entrypoints

## Status
Research completed. This is a documentation/analysis ticket - no external research required.

## Current Packaging Structure

### 1. Console Script Entrypoint (pyproject.toml)

```toml
[project.scripts]
tf = "tf_cli.cli:main"
```

**Current flow:**
1. `tf` command → console script → `tf_cli.cli:main()`
2. Module execution: `python -m tf_cli` → `tf_cli/__main__.py` → `cli.main()`

### 2. Package Structure

```
tf_cli/                          # 39 Python modules
├── __init__.py                  # Re-exports version + ticket_factory
├── __main__.py                  # Entry point for `python -m tf_cli`
├── cli.py                       # Main dispatcher (console script target)
├── version.py                   # Version utilities (imported by cli, __init__)
├── ticket_factory.py            # Core ticket creation (imported by __init__)
├── ticket_loader.py             # Ticket parsing (imported by many modules)
├── utils.py                     # Shared utilities (find_project_root, etc.)
├── kb_helpers.py                # Knowledge base helpers
├── session_store.py             # Session management
├── logger.py                    # Logging utilities
├── board_classifier.py          # Classification logic
├── component_classifier.py      # Component tagging
├── frontmatter.py               # Markdown frontmatter
└── [30+ command modules]        # Individual subcommands
```

### 3. Key Import Graph Analysis

**Core shared modules (imported by many):**
| Module | Imported By | Purpose |
|--------|-------------|---------|
| `version` | `cli.py`, `__init__.py` | Version info |
| `ticket_loader` | 8+ modules | Ticket parsing |
| `utils` | Multiple | Project root finding |
| `kb_helpers` | `kb_cli.py`, `ralph.py` | Knowledge base ops |
| `session_store` | `ralph.py`, `seed_cli.py` | Session management |
| `logger` | `ralph.py` | Logging |
| `board_classifier` | `ui.py`, `workflow_status.py` | Kanban board |
| `component_classifier` | `tags_suggest.py` | Tagging |

**Import relationships:**
```
cli.py (entrypoint)
  ├── version
  ├── [command modules - lazy imported]
  │     ├── ticket_loader
  │     ├── utils
  │     └── kb_helpers
  └── __init__ (re-exports ticket_factory)
        ├── version
        └── ticket_factory
              └── ticket_loader
```

### 4. Potential Issues / Tricky Boundaries

**No import cycles detected** - The import graph is a DAG.

**Key observations:**
1. **`__init__.py` re-exports** - `tf_cli/__init__.py` re-exports `ticket_factory` members. External code might do `from tf_cli import TicketDef`.

2. **`utils.py` is shared** - Contains `find_project_root()` used by multiple modules. This is stateless/functional - safe to move.

3. **`ticket_loader` is central** - Imported by 8+ modules. Changes to this will have broad impact.

4. **Console script target** - `tf_cli.cli:main` is hardcoded in pyproject.toml. This must continue to work during migration.

5. **Lazy imports in cli.py** - Command modules are imported lazily inside `main()`. This allows the `tf` command to start quickly.

## Migration Path Notes

**Order of operations:**
1. Create `tf/` package skeleton (pt-ce2e)
2. Move `tf_cli/cli.py` dispatcher to `tf/cli.py` with backwards-compat shim
3. Update console script to point to `tf.cli:main`
4. Keep `tf_cli/` as re-export shim for existing imports
5. Wire packaging (pt-62g6)
6. Update tests (pt-m06z)

**Risk areas:**
- `__init__.py` re-exports need shim
- Console script change needs coordination with pip install
- External code doing `from tf_cli import X` needs deprecation warning period

## Sources
- `/home/volker/coding/pi-ticketflow/pyproject.toml`
- `/home/volker/coding/pi-ticketflow/tf_cli/cli.py`
- `/home/volker/coding/pi-ticketflow/tf_cli/__init__.py`
- `/home/volker/coding/pi-ticketflow/tf_cli/__main__.py`
- Import graph analysis via grep
