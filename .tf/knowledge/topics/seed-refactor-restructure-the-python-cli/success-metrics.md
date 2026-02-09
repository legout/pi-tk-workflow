# Success Metrics: seed-refactor-restructure-the-python-cli

- `tf --help` works exactly as before.
- `python -m tf --help` works (if we choose to support module execution).
- All tests pass after the move.
- Internal imports primarily reference `tf.*` (not `tf_cli.*`).
- `tf_cli.*` imports still work (shim) during the transition period.
- Documentation and examples point to the new canonical namespace.
