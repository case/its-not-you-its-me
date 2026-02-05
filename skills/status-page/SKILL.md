---
name: status-page
description: Check service status pages for incidents
---

# Status Page Checker

Check if a service has any ongoing incidents.

## Usage

```bash
python3 ~/.claude/skills/status-page/scripts/check_status.py $ARGUMENTS
```

## Available Services

- `claude` (aliases: `anthropic`, `claude-code`) - **default**
- `github` (aliases: `gh`)

## Examples

- `/status-page` - Check Claude/Anthropic status (default)
- `/status-page gh` - Check GitHub status
