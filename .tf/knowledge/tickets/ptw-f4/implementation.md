# Implementation: ptw-f4

## Summary
Added two new example sections to the `prompts/tf-backlog.md` file to improve documentation clarity:
1. Hint-based override example showing keyword detection behavior
2. `--no-deps` example showing standalone usage

## Files Changed
- `prompts/tf-backlog.md` - Added Examples subsection with hint-based override and --no-deps examples

## Key Decisions
- Placed examples inline after the main examples block for better discoverability
- Used comment-style explanation in the hint-based example to make it clear what the seed contains
- Made the `--no-deps` example standalone and clear about when to use it

## Tests Run
- Verified file syntax is valid markdown
- Confirmed examples align with documented behavior in Execution section

## Verification
- Read the updated Examples section to confirm clarity
- Examples demonstrate the value of these features as requested in the ticket
