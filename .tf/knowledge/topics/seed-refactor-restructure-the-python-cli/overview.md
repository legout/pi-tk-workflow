# seed-refactor-restructure-the-python-cli

Refactor the Ticketflow Python CLI package layout by moving implementation code from `tf_cli/` to a top-level `tf/` package that matches the user-facing `tf` command.

Goal: reduce confusion (package name vs CLI name), simplify imports/entrypoints, and provide a safe transition path via backwards-compatible shims.

## Keywords

- refactor
- restructure
- python
- cli
- packaging
- module-layout
- backwards-compatibility
- deprecation
