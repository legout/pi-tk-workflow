# MVP Scope: seed-refactor-restructure-the-python-cli

## In Scope (MVP)

- Create `tf/` package and move a small, coherent slice of functionality first (CLI entry + core modules).
- Add `tf_cli` shim modules that re-export from `tf`.
- Update `pyproject.toml` / entrypoints as needed to keep `tf` command stable.
- Update tests to import from `tf`.
- Update docs to reference the new canonical namespace.

## Out of Scope (for MVP)

- Large-scale API redesign of internal modules.
- Removing `tf_cli` entirely.
- Major behavioral changes to CLI commands.
