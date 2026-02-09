# Seed: Refactor/restructure the Python CLI (move from `tf_cli` to `tf`)

## Vision

Today the user-facing command is `tf`, but the Python package/module namespace is `tf_cli`. This mismatch makes the project harder to understand, harder to embed as a library, and a little awkward to run as a module (e.g. `python -m ...`).

Refactor the codebase so the primary Python package becomes `tf/` (or equivalent), while preserving compatibility for existing imports and tooling.

## Core Concept

- Introduce a top-level `tf` Python package as the canonical home for the CLI and supporting modules.
- Keep `tf_cli` as a **compatibility shim** for at least one release cycle (re-exports + deprecation warnings where appropriate).
- Update packaging/entrypoints so `tf` continues to work and `python -m tf` becomes the natural module invocation.

## Key Features

1. New canonical package namespace (`tf`) for the CLI implementation
2. Backwards-compatible `tf_cli` shim layer (imports continue to work)
3. Updated entrypoints and docs (recommended imports/usage)
4. Tests updated to import from `tf` (while still covering shim behavior)

## Open Questions

- How long do we keep `tf_cli` as a supported compatibility layer?
- Do we want to emit `DeprecationWarning` on `tf_cli` imports (and how to avoid noisy test output)?
- What is the desired public API surface for embedding (if any), vs “CLI-only” modules?
- Should we provide a `tf/__main__.py` so `python -m tf` works consistently?
