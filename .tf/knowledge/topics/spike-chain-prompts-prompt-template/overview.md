# spike-chain-prompts-prompt-template

Research spike on the **`/chain-prompts`** feature added in **pi-prompt-template-model v0.3.0**.

## Quick Answer

`/chain-prompts` lets you run multiple *prompt templates* (markdown files with `model:` frontmatter handled by `pi-prompt-template-model`) **sequentially in one command**. Each step can switch to its own model, set its own thinking level, inject its own skill, and then the extension restores the original model/thinking level at the end (or on mid-chain failure).

## Keywords

- pi
- extension
- pi-prompt-template-model
- chain-prompts
- prompt-chaining
- model-switching
- skill-injection
