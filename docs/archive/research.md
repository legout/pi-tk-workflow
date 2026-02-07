# Research: pi-tk-workflow-context

## Knowledge Used
- .tf/knowledge/topics/pi-tk-workflow-pi-extensions/

## Summary
- Ticket lookup via `tk show pi-tk-workflow-context` failed (ticket not found), so context was gathered from repo documentation and existing extension notes.
- pi-tk-workflow is a Pi workflow package that installs agents/prompts into `~/.pi/agent` or `<project>/.pi` and uses the `subagent` chain tool to run implement → review → fix → close.
- Required Pi extensions referenced: `pi-subagents` and `pi-model-switch`; optional: `pi-review-loop` (used by the `--final-review-loop` flag) and `pi-mcp-adapter` for MCP tooling. `bin/tf setup` installs these and can configure MCP servers (context7/exa/grep_app + optional ZAI endpoints).

## Sources
- README.md
- config/workflows/tf/README.md
- config/settings.json
- prompts/tf.md
- bin/tf
- agents/researcher.md
- https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/coding-agent/examples/extensions/subagent/README.md
- https://github.com/nicobailon/pi-interactive-shell
- https://github.com/nicobailon/pi-mcp-adapter
- https://raw.githubusercontent.com/can1357/oh-my-pi/main/README.md
