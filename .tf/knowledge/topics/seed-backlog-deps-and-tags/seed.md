# Seed: backlog-deps-and-tags

## Vision
When `/tf-backlog` generates tickets, it should do more than just create individual tasks—it should create a **coherent, ready-to-work backlog** with logical dependencies and component classifications already in place. This reduces manual setup work and enables immediate use of features like Ralph parallel processing.

## Core Concept
Extend the `/tf-backlog` command to automatically:
1. **Infer dependencies** between tickets based on seed/baseline/plan content
2. **Add component tags** (e.g., `component:cli`, `component:docs`) for routing and filtering
3. **Link related tickets** using `tk link` for tickets that should be worked on together

## Key Features
1. **Automatic Dependency Inference**
   - For seeds: detect natural ordering (e.g., "define version source" → "implement --version" → "add tests")
   - For baselines: dependencies based on risk severity or file structure
   - For plans: use phase ordering or explicit step sequences
   
2. **Component Tag Assignment**
   - Analyze ticket titles/descriptions to assign component tags
   - Common components: `component:cli`, `component:api`, `component:docs`, `component:tests`, `component:config`
   - Enables Ralph parallel processing (workers pick up tickets by component)
   
3. **Link Related Tickets**
   - Use `tk link` to symmetrically link tickets that are tightly related
   - Example: Link implementation ticket ↔ docs update ticket for same feature
   - Links are advisory (not blocking like dependencies) but help discoverability
   
4. **Configurable Defaults**
   - Allow opting out: `--no-deps`, `--no-component-tags`
   - Configurable component mapping in settings
   
5. **Fallback Commands**
   - If automatic inference fails or needs adjustment, use:
     - `/tf-deps-sync` to re-analyze and set ticket dependencies
     - `/tf-tags-suggest` to re-analyze and set `component:` tags
     - `tk link <id> <id>` to manually link related tickets

## Open Questions
- Should dependencies be strictly linear or allow parallel tracks?
- How to handle circular dependency detection?
- What component taxonomy should be standard across projects?
- Should this apply retroactively to existing open tickets?
