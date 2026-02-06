# Implementation: pt-paih

## Summary
Implemented `tf kb delete <topic-id>` command for permanent deletion of knowledge base topics.

## Files Changed
- `tf_cli/kb_cli.py` - Added `cmd_delete` function and CLI integration

## Key Changes

### 1. Added `cmd_delete` function
- Deletes topics from both active (`topics/`) and archive (`archive/topics/`) locations
- Removes entry from `index.json` if present
- Returns exit code 1 if topic not found
- Prints deleted paths and index removal confirmation

### 2. Updated CLI dispatcher
- Added `delete` subcommand handler
- Proper error handling for missing topic ID argument

### 3. Updated usage documentation
- Added delete command to help text

## Implementation Details
- Uses `shutil.rmtree()` for directory deletion
- Idempotent: can delete topics that exist in either or both locations
- Handles partial failures (if active deletion fails but archive exists)

## Tests Run
- Syntax check: `python3 -m py_compile tf_cli/kb_cli.py` ✓
- Existing tests: `pytest tests/test_kb_helpers.py` (33 passed) ✓
- Manual tests:
  - Delete active topic: ✓
  - Delete archived topic: ✓
  - Error on non-existent topic (exit code 1): ✓

## Verification
```bash
# Test delete active topic
tf kb delete <topic-id>
# Output: Deleted: topics/<topic-id>
#         Removed index entry for '<topic-id>'

# Test delete archived topic
tf kb delete <archived-topic-id>
# Output: Deleted: archive/topics/<topic-id>

# Test error case
tf kb delete nonexistent-topic
# Output: Error: Topic 'nonexistent-topic' not found in knowledge base.
# Exit code: 1
```
