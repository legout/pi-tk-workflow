# Spike: How `/chain-prompts` works in `pi-prompt-template-model` (latest)

## Summary

`pi-prompt-template-model` originally added support for `model:`, `skill:`, and `thinking:` in prompt template frontmatter so that a *single* slash command could temporarily switch to a specific model and inject a specific skill, then auto-restore.

As of **v0.3.0 (2026-02-08)** it also adds **`/chain-prompts`**, which orchestrates multiple such templates **sequentially** in one command invocation. The key property is: **each step runs with its own frontmatter-defined model/skill/thinking**, while the *overall chain* restores the original model/thinking at the end (and also restores on mid-chain failure).

## Key Findings

1. **Only templates with `model:` frontmatter participate.** Templates without `model` are handled by Pi core and are *not* visible to this extension, so they can't be chained.
2. **Chain restores original model/thinking, ignoring per-template `restore:`.** The chain captures `(originalModel, originalThinking)` and restores those when done; individual template restore settings are effectively irrelevant during chain execution.
3. **Argument handling supports both shared args and per-step args.** Shared args come after ` -- ` and are passed into every step unless a step supplies its own args.
4. **Execution model is "send user message, wait for idle".** Internally, each chain step expands the template, sends it as a user message, waits for the agent to complete, then proceeds to the next step.
5. **Failure behavior**: if switching to a step's model fails (e.g., no auth / can't resolve), the chain aborts and restores original model/thinking.

## How to Use `/chain-prompts`

### Basic syntax

```text
/chain-prompts templateA -> templateB -> templateC -- shared args
```

- `->` separates steps.
- ` -- ` (with spaces!) separates the templates list from a *shared args string*.

From the upstream implementation:
- It looks specifically for the substring **`" -- "`** to split shared args.
- It splits steps on the substring **`"->"`**.

### Per-step args

Each step segment is parsed as: `templateName [args...]`.

Examples (from upstream README):

```text
/chain-prompts analyze-code -> fix-plan -> summarize -- src/main.ts
```

```text
/chain-prompts analyze-code "look at error handling" -> fix-plan "focus on perf" -> summarize
```

Mixed:

```text
/chain-prompts analyze-code "error handling" -> fix-plan -> summarize -- src/main.ts
```

Rules:
- If a step has explicit args, those become that step's `$@` (and `$1`, `$2`, …).
- If a step has **no** explicit args, it uses the shared args from after `--`.

### What gets substituted in the template

The extension expands templates via simple placeholder replacement:
- `$1`, `$2`, … positional arguments
- `$@` and `$ARGUMENTS` for the full arg string

There is no special `{previous}` variable mechanism in this extension; the "context flow" is purely via *conversation history* (the next step sees the prior agent output in the chat context).

## Models, skills, thinking, and restore semantics

### Model switching

- `model:` frontmatter can be a single model or a comma-separated fallback list.
- Bare model IDs (e.g., `claude-sonnet-...`) are resolved across providers; if multiple matches exist, provider preference is `anthropic` → `github-copilot` → `openrouter`.

### Thinking level

- `thinking:` frontmatter is applied per step.
- Valid values: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`.

### Skill injection per step

- `skill:` frontmatter sets a `pendingSkill` which is injected into the system prompt in the `before_agent_start` hook.
- Skill resolution is **project-first** then user:
  1. `<cwd>/skills/<name>/SKILL.md` (project-level)
  2. `<cwd>/.pi/skills/<name>/SKILL.md` (local pi config)
  3. `~/.pi/agent/skills/<name>/SKILL.md` (user-level)

### Restore behavior (important)

- Chain captures the current model + thinking level **once**, at chain start.
- After the chain finishes, it restores both.
- If any step cannot resolve/switch its model, the chain restores immediately and stops.
- While chain is active, a `chainActive` flag prevents the normal per-command `agent_end` restore logic from interfering.

## Limitations / Gotchas (from upstream README + code)

- **Restart required** after adding/modifying templates: the extension loads templates at startup (and refreshes on `session_start`).
- **Only templates with a `model` field can be chained.**
- **Literal `->` inside per-step args is unsafe** because step splitting is done via `templatesPart.split("->")`. If a per-step arg contains `->`, it will be interpreted as a step separator. Workaround: pass that content via shared args (`-- ...`) or put it into a file and reference it.
- Shared args separator requires spaces: it searches for **`" -- "`** not just `--`.

## pi-ticketflow Architecture Decision

### Selected Approach: Skills + Prompts

**Architecture**:
- **Skills** (`skills/`): Contain detailed procedures for each workflow phase
- **Prompts** (`prompts/`): Thin wrappers with frontmatter (model, thinking, skill)
- **Agents** (`agents/`): Keep existing reviewer agents for parallel reviews

**Rationale**:
1. Skills can be shared across prompts and agents
2. Prompts are declarative - just specify model/thinking/skill
3. Procedures are centralized in skills, not duplicated in prompts
4. Easy to test skills independently
5. Models can be changed by editing frontmatter only

### Phase Structure

```
skills/
├── tf-research/SKILL.md      # Research procedure
├── tf-implement/SKILL.md     # Implementation procedure
├── tf-review/SKILL.md        # Reviewer subagent contract
├── tf-review-phase/SKILL.md  # Review phase orchestration
├── tf-fix/SKILL.md           # Fix procedure
└── tf-close/SKILL.md         # Close procedure

prompts/
├── tf.md                   # Entry point (chain invocation)
├── tf-research.md          # Wrapper: model=k2p5, thinking=medium, skill=tf-research
├── tf-implement.md         # Wrapper: model=MiniMax-M2.5, thinking=high, skill=tf-implement
├── tf-review.md            # Wrapper: model=gpt-5.3, thinking=high, skill=tf-review-phase
├── tf-fix.md               # Wrapper: model=glm-5, thinking=high, skill=tf-fix
└── tf-close.md             # Wrapper: model=GLM-4.7-Flash, thinking=medium, skill=tf-close
```

### Chain Invocation

```bash
# Deterministic wrapper (recommended)
tf irf pt-1234 [flags]

# Under the hood (resolved command)
/chain-prompts tf-research -> tf-implement -> tf-review -> tf-fix -> tf-close -- pt-1234
```

The wrapper handles flag parsing and post-chain commands in Python instead of prompt text.

### Context Flow Between Steps

Each phase writes artifacts to `{artifactDir}/`:
1. **tf-research** → writes `research.md`
2. **tf-implement** → reads `research.md`, writes `implementation.md`, `files_changed.txt`
3. **tf-review** → reads `implementation.md`, writes `review.md`
4. **tf-fix** → reads `review.md`, writes `fixes.md`
5. **tf-close** → reads all, writes `close-summary.md`, commits

The conversation context carries forward between steps, but key state is persisted to files for reliability.

## Risks & Unknowns

- **Flags/conditionals**: `/chain-prompts` has no conditional branching. Solved via:
  - Entry point variants (tf-research vs tf-implement)
  - Post-chain commands (follow-ups, simplify, review-loop)
- **Long chains**: Token accumulation across 5 steps. Mitigated by writing artifacts to files.
- **Interrupt handling**: If chain is interrupted, artifacts may be partial. Mitigated by each phase writing its own artifacts.

## Next Steps

- [x] Create phase skills in `skills/`
- [x] Create phase prompts in `prompts/`
- [ ] Test each phase in isolation
- [ ] Test full chain end-to-end
- [ ] Update documentation to remove `pi-model-switch` requirement
