---
id: pt-d9rg
status: closed
deps: [pt-ooda]
links: []
created: 2026-02-09T09:04:18Z
type: task
priority: 2
assignee: legout
external-ref: seed-fix-tui-doc-opening
tags: [tf, backlog, component:api, component:cli, component:config, component:docs, component:tests, component:workflow]
---
# Add terminal suspend when opening documents in TUI

## Task
Wrap the os.system() call in _open_doc method with self.app.suspend() context manager.

## Context
Even after fixing the action methods, the document opening won't work correctly because Textual has the terminal in raw/cooked mode. External pagers like less or editors like vim need the terminal in normal mode. Without suspending the Textual app first, the pager receives garbled input or appears unresponsive.

## Acceptance Criteria
- [ ] Locate the _open_doc method in tf_cli/ui.py (around line 588)
- [ ] Wrap the os.system(cmd) call with `with self.app.suspend():`
- [ ] Test document opening with less pager
- [ ] Test document opening with vim editor
- [ ] Verify TUI resumes correctly after closing pager/editor

## Constraints
- Must work with $PAGER and $EDITOR environment variables
- Must handle the case where neither is set (fallback to less/more/cat)
- Graceful error handling if suspend fails

## References
- Seed: seed-fix-tui-doc-opening
- Textual docs: https://textual.textualize.io/guide/app/#suspending-the-app


## Notes

**2026-02-09T09:24:42Z**

Implementation complete. Wrapped os.system() call in _open_doc method with self.app.suspend() context manager for proper terminal handling when opening external pagers/editors. Added error handling for suspend failures.\n\nCommit: 5f1b2ef\n\nReview Summary:\n- Critical: 0\n- Major: 1 (doc suggestion for unrelated function)\n- Minor: 4\n- Warnings: 1\n- Suggestions: 3\n\nManual testing required:\n- Test with less pager\n- Test with vim editor\n- Verify TUI resumes correctly
