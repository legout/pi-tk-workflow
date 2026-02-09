# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Documentation note clarifying that `zai-vision` MCP server runs locally via `npx -y @z_ai/mcp-server` and requires Node.js/npx, while `zai-web-search` and `zai-web-reader` remain remote URL-based services.

### Changed

### Deprecated

### Removed

### Fixed

### Security

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

[unreleased]: https://github.com/volker/pi-tk-workflow/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/volker/pi-tk-workflow/releases/tag/v0.2.0
[0.1.0]: https://github.com/volker/pi-tk-workflow/releases/tag/v0.1.0
