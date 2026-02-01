# pi-tk-workflow

IRF workflow toolkit for Pi - ticket management, agent orchestration, and review loops.

## Quick Commands

- Run CLI: `./bin/irf <command>`
- Create ticket: `tk create "description"`
- List ready tickets: `tk ready`
- Start Ralph loop: `/ralph-start`

## Conventions

- Agents are markdown files with YAML frontmatter
- Skills follow the SKILL.md format
- Prompts are single markdown files for Pi command entry points
- Use bash for CLI tools, Python for complex logic

## Capabilities

- Workflow management via `./bin/irf`
- Ralph loop for autonomous ticket processing
- Agent definitions for IRF (Implement-Review-Fix) workflow
- Skills for planning, config, and workflow orchestration
