# Seed: add versioning

## Vision
Users should always know **which version** of the toolkit they are running, what changed between versions, and whether an update is breaking. Versioning should enable reliable releases and reduce “mystery regressions”.

## Core Concept
Introduce a single source of truth for the project version (e.g., `package.json` + optional `VERSION` file) and expose it consistently via CLI output and docs (e.g., `tf --version`). Optionally add lightweight automation for bumping versions and maintaining a changelog.

## Key Features
1. **Expose version to users**
   - `tf --version` (and any other relevant entry points) prints the current version.
2. **Define versioning scheme**
   - Adopt SemVer (MAJOR.MINOR.PATCH) and document how to bump versions.
3. **Changelog basics**
   - Maintain `CHANGELOG.md` and a minimal workflow for adding entries.
4. **Release hygiene (optional / later)**
   - Tag releases in git (e.g., `v1.2.3`).
   - Validate that version in code matches `package.json`.

## Open Questions
- Where should the canonical version live (only `package.json`, or also `VERSION`)?
- Should the CLI show build metadata/commit SHA in dev builds?
- Do we need a `tf version bump <major|minor|patch>` helper, or keep it manual?
- How should we handle versioning for non-npm distribution (if any)?
