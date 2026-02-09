# Implementation: pt-mu0s - tf_cli Deprecation Strategy

## Summary

Defined the deprecation strategy for the `tf_cli` → `tf` namespace transition, including timeline, warning behavior, and documentation updates.

## Decisions Made

### 1. Deprecation Timeline

| Milestone | Version | Date Target |
|-----------|---------|-------------|
| Policy defined | 0.3.0 | 2026-02-09 |
| `tf` package introduced | 0.4.0 | TBD |
| `tf_cli` shim available | 0.4.x | Ongoing |
| `tf_cli` removal | 0.5.0 | Target |

**Rationale**: One full release cycle (0.4.x) provides sufficient migration time while keeping the timeline predictable. Version-based removal is clearer than time-based for a package.

### 2. Warning Behavior

**Decision**: Warnings are **opt-in via environment variable** (default: off)

```python
# In tf_cli/__init__.py and other shim modules
import os
import warnings

if os.environ.get("TF_CLI_DEPRECATION_WARN"):
    warnings.warn(
        "tf_cli is deprecated. Use 'tf' package instead. "
        "See docs/migration-guide.md for details.",
        DeprecationWarning,
        stacklevel=2,
    )
```

**Rationale**:
- Avoids CI/test noise (constraint from ticket)
- Users who want warnings can enable them
- Matches existing pattern of env-based feature flags in codebase

### 3. Documentation Strategy

Updated `docs/deprecation-policy.md` with a new section covering `tf_cli` → `tf` transition.

## Files Changed

1. `docs/deprecation-policy.md` - Added Section 3.4 "tf_cli Package Namespace"

## Key Decisions Documented

### For Downstream Implementers (pt-hpme)

The shim implementation should:

1. **Keep `tf_cli/` directory** with thin re-export modules
2. **Use conditional warnings** based on `TF_CLI_DEPRECATION_WARN` env var
3. **Preserve all public exports** from current `tf_cli/__init__.py`:
   - `TicketDef`, `CreatedTicket`
   - `apply_dependencies`, `apply_links`
   - `create_tickets`, `print_created_summary`
   - `score_tickets`, `write_backlog_md`
   - `get_version`, `__version__`

4. **Console script** `tf` should point to `tf.cli:main` (not tf_cli)
5. **Module execution** `python -m tf` should work (via `tf/__main__.py`)

### Migration Path for Users

```python
# Old (deprecated from 0.4.0, removed in 0.5.0)
from tf_cli.ticket_factory import TicketDef
from tf_cli import get_version

# New (preferred from 0.4.0+)
from tf.ticket_factory import TicketDef
from tf import get_version
```

```bash
# CLI usage unchanged
tf --help
tf doctor

# Module execution (new in tf package)
python -m tf --help
```

## Verification

- [x] Policy documented in deprecation-policy.md
- [x] Timeline defined (supported through 0.4.x, removal in 0.5.0)
- [x] Warning behavior specified (env-gated, default off)
- [x] Migration path documented
- [x] Links to related tickets captured

## Related Artifacts

- Research: `.tf/knowledge/tickets/pt-mu0s/research.md`
- Updated Policy: `docs/deprecation-policy.md` (Section 3.4)
