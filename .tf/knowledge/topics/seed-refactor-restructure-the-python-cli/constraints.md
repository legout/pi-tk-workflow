# Constraints: seed-refactor-restructure-the-python-cli

- Do not break the `tf` console script / CLI UX.
- Preserve Python version support (>= 3.9).
- Keep the refactor incremental: small, reviewable steps.
- Avoid forcing downstream users to update imports immediately (provide shim).
- Keep Ralph/TF workflow commands working during the refactor.
