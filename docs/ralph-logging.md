# Ralph Logging

Ralph provides structured, actionable logging to help you understand what the autonomous loop is doing and diagnose issues when they occur.

---

## Quick Start

### Normal Mode (Default)

```bash
tf ralph start
```

Shows lifecycle events: ticket selection, phase transitions, completions, and errors.

**Output goes to stderr** (so it doesn't mix with stdout data pipes).

### Verbose Mode

```bash
tf ralph start --verbose
# or
RALPH_VERBOSE=1 tf ralph start
```

Adds detailed diagnostics: command execution, timing metrics, subagent activity.

### Quiet Mode

```bash
tf ralph start --quiet
# or
RALPH_QUIET=1 tf ralph start
```

Minimal output: start, end, and errors only. Useful for CI.

---

## Log Format

```
TIMESTAMP | LEVEL | key=value ... | message
```

**Example:**
```
2026-02-06T17:45:12Z | INFO | ticket=pt-abc123 iteration=3 mode=serial | Starting ticket processing: pt-abc123
```

---

## Log Levels

| Level | Description | Shown In |
|-------|-------------|----------|
| `ERROR` | Failures that stop or may stop processing | All modes |
| `WARN`  | Recoverable issues, unusual conditions | All modes |
| `INFO`  | Normal lifecycle events | Normal, Verbose |
| `DEBUG` | Detailed diagnostics | Verbose only |

---

## Key Events

### Loop Lifecycle

| Event | Description |
|-------|-------------|
| `loop_start` | Ralph initialized with config |
| `loop_complete` | Ralph terminated (complete/max_iter/error) |
| `no_ticket_selected` | No ready ticket found, sleeping |

### Ticket Lifecycle

| Event | Description |
|-------|-------------|
| `batch_selected` | Tickets chosen for parallel processing |
| `worktree_operation` | Git worktree add/remove (parallel mode) |
| `command_executed` | Pi workflow command completed |

### Logged via Logger Methods

- `log_ticket_start()` - Ticket processing begins
- `log_ticket_complete()` - Ticket processing ends
- `log_command_executed()` - Command result with exit code
- `log_error_summary()` - Error with artifact path
- `log_loop_start()` - Loop initialization
- `log_loop_complete()` - Loop termination
- `log_no_ticket_selected()` - Retry/sleep event
- `log_batch_selected()` - Parallel batch selection
- `log_worktree_operation()` - Worktree management

---

## Grepping Logs

```bash
# Find all errors
grep "| ERROR" .tf/ralph/logs/*.jsonl

# Find specific ticket activity
grep "ticket=pt-abc123" .tf/ralph/logs/*.jsonl

# Find completed tickets
grep "status=COMPLETE" .tf/ralph/logs/*.jsonl

# Find failed tickets
grep "status=FAILED" .tf/ralph/logs/*.jsonl
```

---

## Security & Privacy

### Redaction

Sensitive data is automatically redacted:

- **API keys, tokens, passwords** → `[REDACTED]`
- **Environment variables** with `KEY`, `TOKEN`, `SECRET` → `[REDACTED]`
- **Long paths** truncated in normal mode (full in verbose)

### Never Logged

Even in verbose mode:
- Full Pi prompt content
- Complete review outputs
- Internal session data

---

## Log Files

When JSON capture is enabled (`RALPH_CAPTURE_JSON=1` or set `captureJson: true` in `.tf/ralph/config.json`):

- **Path**: `.tf/ralph/logs/{ticket-id}.jsonl`
- **Format**: One JSON object per line (structured events from Pi `--mode json`)
- **Use case**: Post-mortem analysis of tool calls and responses

**Note**: JSONL capture is opt-in. The format is subject to change (experimental feature).

---

## Troubleshooting

### "No ready tickets found"

Check `tk ready` - are there tickets with unmet dependencies?

### Loop stops early

Check `.tf/ralph/progress.md` for failures and last state.

### Too much output

Use `--quiet` mode or filter with grep:
```bash
tf ralph start 2>&1 | grep -E "(ERROR|loop_|Ticket completed)"
```

### Debug a specific ticket

Run single ticket with verbose:
```bash
tf ralph run pt-abc123 --verbose
```

### Where to look after failures

When a ticket fails, Ralph logs include an `artifact_path` pointing to:

```
.tf/knowledge/tickets/<ticket-id>/
```

This directory contains:

| File | Contains |
|------|----------|
| `implementation.md` | What was implemented, files changed |
| `review.md` | Consolidated review findings |
| `fixes.md` | Fixes applied after review |
| `close-summary.md` | Final status and commit info |
| `files_changed.txt` | List of modified file paths |

**Example error log with artifact pointer:**
```
2026-02-06T18:00:35Z | ERROR | artifact_path=.tf/knowledge/tickets/pt-abc123 | error="Command failed" | ticket=pt-abc123 | Error summary
```

**Quick inspection:**
```bash
# See what happened for a failed ticket
ls .tf/knowledge/tickets/pt-abc123/

# Read the close summary
cat .tf/knowledge/tickets/pt-abc123/close-summary.md

# Check what files were modified
cat .tf/knowledge/tickets/pt-abc123/files_changed.txt
```

### Session traces

Pi session files (when `sessionDir` is configured):

- **Location**: `.tf/ralph/sessions/<ticket-id>.jsonl`
- **Format**: Pi session format (configurable via `sessionPerTicket`)
- **Use case**: Reviewing Pi tool calls and responses

Configure in `.tf/ralph/config.json`:
```json
{
  "sessionDir": ".tf/ralph/sessions",
  "sessionPerTicket": true
}
```

---

## Specification

For the full technical specification, see:
- `../.tf/knowledge/tickets/pt-l6yb/ralph-logging-spec.md` (from this docs directory)

This defines:
- Complete event reference
- Redaction rules
- Phase values
- Error context format
- Implementation notes for developers
