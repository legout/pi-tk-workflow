# Research: pt-hstd

## Status
Research completed. Code analysis performed on existing implementation.

## Context Reviewed
- `tk show pt-hstd` - Ticket requirements
- `tf_cli/ralph.py:run_ticket()` - Current subprocess execution

## Current Implementation Analysis

The `run_ticket()` function currently uses `subprocess.run()` with a timeout parameter:

```python
result = subprocess.run(args, cwd=cwd, timeout=timeout_secs)
```

When timeout expires, it catches `subprocess.TimeoutExpired` and returns -1:

```python
except subprocess.TimeoutExpired:
    log.error(f"Attempt timed out after {timeout_ms}ms", ticket=ticket)
    return -1
```

## Problem Identified

**Critical Issue**: The current code does NOT terminate the subprocess on timeout. When `subprocess.TimeoutExpired` is raised, the child process continues running in the background, becoming a zombie/orphan process.

## Solution Approach

To implement safe termination:

1. Use `subprocess.Popen` instead of `subprocess.run` for timeout control
2. On timeout:
   - Send SIGTERM first (graceful termination)
   - Wait briefly for process to exit
   - If still running, send SIGKILL (force kill)
   - Always call `wait()` to reap the process and prevent zombies
3. Return -1 to indicate timeout for restart logic

## Key Requirements

- Must work with all output modes: inherit, file, discard, JSON capture
- Must not break existing output capture functionality
- Must always reap child processes (wait after kill)
- Return code -1 must indicate timeout distinctly

## References
- Python subprocess docs: https://docs.python.org/3/library/subprocess.html
- Ticket pt-4qvw: Defines timeout + restart configuration surface
