# Review: ptw-f4

## Critical (must fix)
No issues found.

## Major (should fix)
- `prompts/tf-backlog.md:51` - The hint-based example is missing `define`/`design` keywords in the detected keywords list. The Execution section documents 5 categories but the example only lists 3. This could mislead users about what hints are detected.

## Minor (nice to fix)
- `prompts/tf-backlog.md:35-36` - The comment "# Seed contains: ..." format could be clearer as plain text rather than shell-comment style.
- `prompts/tf-backlog.md:44` - Header case consistency: "--no-deps Example" uses title case; consider sentence case for consistency with other subsections.

## Warnings (follow-up ticket)
No warnings.

## Suggestions (follow-up ticket)
- `prompts/tf-backlog.md:38-41` - Consider adding a cross-reference link to the Execution section (step 6, Seed mode) for readers wanting deeper context on hint-based logic.

## Summary Statistics
- Critical: 0
- Major: 1
- Minor: 2
- Warnings: 0
- Suggestions: 1

## Reviewers
- reviewer-general: Major(1), Minor(1)
- reviewer-spec-audit: All clear
- reviewer-second-opinion: Minor(1), Suggestion(1)
