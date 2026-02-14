# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.5.1] - 2026-02-14

### Fixed

- **`tf init` in workflow repo** - Fixed `.pi/` folder creation when running `tf init` in the pi-ticketflow workflow repo itself. Assets are now correctly routed to `.pi/agents`, `.pi/prompts`, `.pi/skills` when initializing the workflow development environment, while regular projects still use project root directories.

## [0.5.0] - 2026-02-13

### Changed

#### Deterministic `/tf` Orchestration
- **`tf irf` CLI command** - New deterministic backend for `/tf` workflow
  - Strict flag parsing and validation
  - Config-aware research entry selection
  - Deterministic `/chain-prompts` command construction
  - Post-chain command execution only on successful chain completion
  - `--plan`/`--dry-run` support for plan inspection
- **`/tf` as thin wrapper** - `/tf` now delegates to `tf irf` for all orchestration
- **Removed `pi-model-switch` dependency** - No longer required; each phase has its own `model:` frontmatter

#### Project-Root Asset Layout
- **Canonical paths** - `agents/`, `prompts/`, `skills/` at project root (not `.pi/`)
- **Updated tooling** - `tf init`, `tf sync`, `tf asset_planner`, `tf ralph` updated for new layout
- **Legacy fallback** - `.pi/` still supported as fallback for backward compatibility

#### Phase Skills & Prompts Architecture
- **`tf-review` skill restored** - Shared reviewer subagent contract (used by reviewer agents)
- **`tf-review-phase` skill added** - Review phase orchestration (parallel fan-out + merge)
- **Phase prompts** - `/tf-research`, `/tf-implement`, `/tf-review`, `/tf-fix`, `/tf-close` as thin wrappers with frontmatter
- **Removed post-chain from close phase** - Post-chain logic now in `tf irf`

### Added

#### New CLI Commands
- **`tf irf <ticket-id> [flags]`** - Deterministic `/chain-prompts` IRF workflow wrapper

#### New Pi Prompts
- `/tf-research` - Research phase prompt
- `/tf-implement` - Implementation phase prompt  
- `/tf-review` - Review phase prompt (uses `tf-review-phase` skill)
- `/tf-fix` - Fix phase prompt
- `/tf-close` - Close phase prompt

#### New Skills
- `tf-research` - Research phase procedure
- `tf-implement` - Implementation phase procedure
- `tf-review` - Shared reviewer subagent contract
- `tf-review-phase` - Review phase orchestration
- `tf-fix` - Fix phase procedure
- `tf-close` - Close phase procedure

### Fixed

- **Critical regression** - `tf-review` skill collision between reviewer contract and phase orchestration
- **Asset routing** - Manifest now routes to project-root `agents/`, `prompts/`, `skills/`
- **Model sync** - `tf sync` now supports both project-root and legacy `.pi/` layouts
- **Ralph prompt discovery** - Checks both `prompts/tf.md` and legacy `.pi/prompts/tf.md`
- **Doctor checks** - Removed `pi-model-switch` from required extensions

### Removed

- **`pi-model-switch` as required extension** - No longer needed; each phase has its own `model:` frontmatter

### Documentation

- Updated all docs for deterministic workflow and project-root asset layout
- Added smoke-test procedure to `docs/workflows.md`
- Added `tf irf` command documentation to `docs/commands.md`
- Updated model strategy tables to match current config defaults
- Removed stale runtime model-switch guidance

### Migration Notes

Users upgrading from 0.4.0:
1. Run `tf init` to install new project-root assets
2. Run `tf sync` to update model frontmatter
3. Remove `pi-model-switch` if only used for TF: `pi uninstall npm:pi-model-switch`
4. Optional: Clean up `.pi/agents/`, `.pi/prompts/`, `.pi/skills/` after migration

## [0.4.0] - 2026-02-09

### Added

#### Canonical tf Package Namespace
- **New `tf/` package** - 32 modules migrated from `tf_cli` to canonical `tf` namespace
- **CLI dispatcher** - Entry points now use `tf.cli:main` as canonical implementation
- **Core utilities** - utils, frontmatter, logger, ticket_loader, component_classifier, ticket_factory in tf/
- **All CLI commands** - setup, login, init, sync, doctor, ralph, ui, and 20+ more commands in tf/
- **Backward compatibility shim** - `tf_cli` package re-exports from `tf` for compatibility

#### Test Suite Updates
- **Migrated 24+ test files** - All tests now import from `tf.*` namespace
- **Shim regression tests** - Comprehensive tests in `test_tf_cli_shim.py` verify backward compatibility
- **Mock path fixes** - All mock.patch() paths updated to match new import namespace

#### Documentation
- **Migration guide** - Added deprecation timeline and migration notes to README
- **Namespace documentation** - Clear documentation of tf vs tf_cli usage

### Deprecated

- **`tf_cli` package namespace** - The `tf_cli` Python package is deprecated in favor of `tf`. The `tf_cli` package serves as a compatibility shim re-exporting from `tf` and will be removed in version 0.5.0. See [docs/deprecation-policy.md](docs/deprecation-policy.md) for migration guide and timeline. Set `TF_CLI_DEPRECATION_WARN=1` to enable deprecation warnings.

### Fixed

- Fixed mock.patch() paths in tests to use `tf.*` namespace instead of `tf_cli.*`
- Fixed incomplete import migrations in test files
- Fixed docstring references from `tf_cli` to `tf`

## [0.3.0] - 2026-02-09

### Added

#### Web UI (Sanic + Datastar)
- **`tf ui --web`** - Print textual serve command for browser-based UI
- **Sanic web server** - Full web UI with Sanic and Datastar integration
- **Kanban board view** - Interactive kanban board with drag-and-drop
- **Topic browser** - Browse knowledge topics in web interface
- **Ticket detail view** - Full ticket details with markdown rendering
- **Server-side search/filter** - Real-time search using Datastar signals
- **Live board updates** - SSE endpoint for real-time board refresh
- **Dark mode toggle** - Toggle between light and dark themes
- **Accessibility improvements** - ARIA labels and keyboard navigation
- **Board stats DOM** - Datastar patching for statistics

#### TUI Improvements
- **Description expand/collapse** - Press 'e' to toggle full description view
- **Increased description limit** - From 500 to 2500 characters
- **Document opening keys** - Fixed TUI document opening with o, 1, 2, 3, 4 keys
- **Terminal suspend handling** - Proper terminal restoration after opening docs

#### Ralph Loop Enhancements
- **Timestamped progress** - Timestamps in Ralph --progress output
- **Progress total computation** - Correct total for parallel processing
- **Improved error messages** - Better Textual import error with uv guidance
- **Session management** - Removed --session forwarding, uses sessionDir config

#### Documentation
- **zai-vision documentation** - Clarified Node.js/npx requirement for local MCP server
- **Ralph logging docs** - Updated for simplified sessionDir config
- **Configuration docs** - Updated for command-based zai-vision MCP

### Changed

- **Config**: Updated review-spec model to gpt-5.3-codex
- **Config**: Changed tf-plan-revise and tf-plan-review categories
- **gitignore**: Removed .tf/ to track knowledge base artifacts
- **Skills**: Removed obsolete Follow-ups Scan procedure from tf-planning

### Fixed

- Textual import error now suggests `uv run tf ui` as alternative
- TUI document opening keys now work correctly
- Ralph progress display shows correct totals

### Security

- Security audit for web-served UI styling and assets

## [0.2.0] - 2026-02-08

### Added

#### Core CLI Features
- **`tf install`** - New global installation system with uvx support and offline mode (`--force-local`)
- **`tf setup`** - Interactive setup wizard for configuring Pi extensions and MCP tools
- **`tf login`** - Authentication with ticket storage service
- **`tf init`** - Project initialization with asset installation and configuration
- **`tf sync`** - Sync tickets with external service and update models from config
- **`tf doctor`** - Comprehensive diagnostics with version checking, fix suggestions, and multi-language project support
- **`tf update`** - Self-update mechanism for the CLI
- **`tf --version`** / `-v` / `-V` - Version flag support across all entry points

#### Ralph Autonomous Loop
- **`tf ralph`** - Full autonomous ticket processing loop with:
  - Serial and parallel processing modes
  - Configurable timeout and restart settings (`attemptTimeoutMs`, `maxRestarts`)
  - Progress display with per-ticket status tracking
  - Session management with Pi-standard session directory
  - Ticket title caching for verbose logging
  - Bounded restart loops for timed-out attempts
  - Subprocess output routing (inherit/file/discard modes)
  - Progress and `pi-output` CLI flags

#### Interactive TUI (Textual)
- **`tf ui`** - Interactive Kanban board TUI with:
  - Ready/Blocked board classification
  - Ticket search and filtering
  - Topic browser with `$PAGER`/`$EDITOR` integration
  - Knowledge topic index loader
  - Lazy ticket body loading from frontmatter

#### Knowledge Base & Planning
- **`tf kb`** - Knowledge base management commands
- **`tf seed`** - Seed topic creation from ideas
- **`tf backlog-ls`** - List tickets in backlog by topic
- **`tf track`** - Track file changes for tickets
- **`tf priority-reclassify`** - Automated priority reclassification with filters
- **`tf next`** - Show next recommended ticket to work on

#### Agent & Prompt Management
- **`tf agentsmd`** - AGENTS.md management commands
- **Frontmatter handling** - Shared module for model synchronization
- **Asset planning** - Converged install/update flow for workflow assets
- **Version synchronization** - Automatic sync between `VERSION` file and `package.json`

#### New Prompts
- `/tf-followups-scan` - Scan for missing followups.md files
- `/tf-followups` - Generate follow-up tickets with consistent format
- `/ralph-start` - Launch Ralph autonomous loop
- `/tf-priority-reclassify` - Priority reclassification prompt

#### New Skills
- `ralph` - Autonomous ticket processing skill
- Enhanced `tf-planning` with Follow-ups Scan procedure
- Enhanced `tf-config` with version sync and validation helpers

#### Testing & Quality
- Comprehensive pytest test suite with 35% coverage gate
- Smoke tests for critical commands (`tf --version`, `tf ui`)
- Unit tests for Ralph state management, timeout behavior, and progress display
- Integration tests for version retrieval and doctor checks
- CI/pre-commit guardrails for oversized and forbidden artifact paths

#### Documentation
- `VERSIONING.md` - Version source of truth and release process documentation
- `AGENTS.md` - Updated conventions for agents, skills, and prompts
- Workflow documentation in `config/workflows/tf/README.md`
- Archived historical docs to `docs/archive/` with traceability

### Changed

- **CLI Architecture**: Refactored to consume shared utility modules (`utils.py`, `frontmatter.py`)
- **Ralph Configuration**: Default sessionDir changed to Pi sessions directory (`~/.pi/agent/sessions`)
- **Agent Configurations**: Updated `fixer.md` and other agents with refined instructions and model configs
- **Prompt Templates**: Refined `tf-backlog.md`, `tf-seed.md`, `ralph-start.md` with improved workflows
- **Skill Documentation**: Enhanced `tf-config/SKILL.md` with comprehensive setup/sync procedures
- **Project Structure**: Renamed `*_new.py` modules to stable names
- **Coverage Requirements**: Raised coverage gate to 35% with additional tests

### Removed

- Deprecated Ralph configuration files (`.pi/ralph/AGENTS.md`, `.pi/ralph/config.json`)
- Obsolete topic documentation from knowledge base
- Old proposal and research files (`proposal-irf-improvements.md`, `research.md`, `reviewer-subagent-failure-report.md`)
- Runtime/build artifacts from git tracking (per expanded `.gitignore`)

### Fixed

- Version synchronization between `VERSION` file and `package.json`
- Test suite compatibility with updated CLI components
- Ticket title retrieval in Ralph verbose logging
- Doctor version integration for multi-language projects
- Parallel mode safety checks for timeout/restart settings

## [0.1.0] - 2026-02-05

### Added

- Initial release of `pi-tk-workflow` (Ticketflow CLI).
- Core CLI commands: `create`, `ready`, `next`, `show`, `close`, `add-note`, `link`.
- Ticket management system with YAML-based storage.
- Seed-driven planning workflow for capturing and refining ideas.
- Research phase with support for external spec references (OpenSpec).
- IRF (Implement-Review-Fix) workflow with parallel reviews.
- Subagent-based reviewer system with general, spec-audit, and second-opinion reviewers.
- Fixer agent for addressing review findings.
- Quality gate with configurable severity thresholds.
- Ralph autonomous loop for batch ticket processing.
- Progress tracking and lessons learned capture.
- Python CLI with Click framework.
- pytest-based test suite with coverage reporting.
- Configuration system via `.tf/config/settings.json`.

[unreleased]: https://github.com/volker/pi-tk-workflow/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/volker/pi-tk-workflow/releases/tag/v0.3.0
[0.2.0]: https://github.com/volker/pi-tk-workflow/releases/tag/v0.2.0
[0.1.0]: https://github.com/volker/pi-tk-workflow/releases/tag/v0.1.0
