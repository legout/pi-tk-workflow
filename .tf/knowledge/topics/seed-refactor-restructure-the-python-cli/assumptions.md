# Assumptions: seed-refactor-restructure-the-python-cli

- The project wants the canonical namespace to align with the CLI name (`tf`).
- We can accept a short transition period where both `tf` and `tf_cli` exist.
- The packaging setup (pyproject) can be adjusted without breaking installation.
- Minimum supported Python version stays the same (currently >= 3.9).
