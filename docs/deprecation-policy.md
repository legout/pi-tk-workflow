# Deprecation Policy

This document tracks active deprecations and migration guidance for `pi-tk-workflow`.

## Status Snapshot

- **Canonical Python package:** `tf`
- **Compatibility package:** `tf_cli` (deprecated shim in 0.4.x)
- **Legacy shell runtime (`scripts/tf_legacy.sh`):** removed

## Active Deprecation: `tf_cli` -> `tf`

### Why

The user-facing CLI command is `tf`. Using `tf` as the Python package keeps imports and docs consistent.

### Timeline

| Phase | Versions | Behavior |
|---|---|---|
| Notice | 0.4.x | `tf` is canonical, `tf_cli` works as shim |
| Removal | 0.5.0 | `tf_cli` shim is removed |

### Import Migration

```python
# Old (deprecated)
from tf_cli.ticket_factory import TicketDef
from tf_cli import get_version
from tf_cli.doctor import run_doctor

# New (preferred)
from tf.ticket_factory import TicketDef
from tf import get_version
from tf.doctor import run_doctor
```

### CLI Impact

No CLI migration is required. The command remains:

```bash
tf <command>
```

### Optional Warning Mode

To surface deprecation warnings for `tf_cli` imports:

```bash
export TF_CLI_DEPRECATION_WARN=1
python -c "from tf_cli import get_version"
```

## Removed Legacy Runtime

### `scripts/tf_legacy.sh`

- Removed from active runtime path.
- `tf` Python CLI is the supported runtime.
- Historical recovery is possible via git history if needed.

## Migration Checklist

1. Replace `from tf_cli...` imports with `from tf...`.
2. Replace `python -m tf_cli` usage with `python -m tf` where module execution is used.
3. Ensure internal docs/snippets reference `tf` as canonical package namespace.

## Verification Commands

```bash
# Find deprecated imports
rg "from tf_cli|import tf_cli" --glob "*.py"

# Validate canonical module entrypoint
python -m tf --help
```

## Notes

- `tf_cli` shim support in 0.4.x is compatibility-only.
- New code and new documentation should target `tf` exclusively.
