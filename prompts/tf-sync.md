---
description: Sync TF configuration [tf-config]
model: zai/glm-4.7
thinking: medium
skill: tf-config
---

# /tf-sync

Apply workflow configuration and verify required extensions.

## Usage

```bash
/tf-sync
```

## Execution

Follow the **tf-config** skill procedures:

1. Verify setup (extensions + project assets)
2. Sync model/thinking frontmatter from `.tf/config/settings.json`
3. Report status and recommendations

## Required Extensions

- `pi-prompt-template-model`
- `pi-subagents`

## Optional Extensions

- `pi-review-loop`
- `pi-mcp-adapter`
- `pi-web-access`

## Synced Files

`tf sync` updates frontmatter in:
- `agents/*.md`
- `prompts/*.md`

(legacy fallback: `.pi/agents/*.md` and `.pi/prompts/*.md`)
