---
id: pt-oyjt
status: closed
deps: [pt-d9rg]
links: []
created: 2026-02-09T09:04:18Z
type: task
priority: 2
assignee: legout
external-ref: seed-fix-tui-doc-opening
tags: [tf, backlog, component:docs, component:workflow]
---
# Move action methods from TopicBrowser to TicketflowApp

## Task
Move or delegate action methods for document opening from TopicBrowser class to TicketflowApp class.

## Context
The key bindings (o, 1, 2, 3, 4) are defined in TicketflowApp.BINDINGS, but the action methods (action_open_doc, action_open_overview, action_open_sources, action_open_plan, action_open_backlog) are currently in TopicBrowser. Textual looks for action methods on the class where bindings are defined, so these keys currently do nothing.

## Acceptance Criteria
- [ ] Add action_open_doc method to TicketflowApp that delegates to TopicBrowser
- [ ] Add action_open_overview method to TicketflowApp that delegates to TopicBrowser
- [ ] Add action_open_sources method to TicketflowApp that delegates to TopicBrowser
- [ ] Add action_open_plan method to TicketflowApp that delegates to TopicBrowser
- [ ] Add action_open_backlog method to TicketflowApp that delegates to TopicBrowser
- [ ] Keys o, 1, 2, 3, 4 now trigger the corresponding actions

## Constraints
- Keep existing TopicBrowser methods unchanged (just delegate from TicketflowApp)
- Ensure proper error handling when no topic is selected

## References
- Seed: seed-fix-tui-doc-opening


## Notes

**2026-02-09T09:27:31Z**

Implementation complete.

## Changes
Added 5 action methods to TicketflowApp that delegate to TopicBrowser:
- action_open_doc() - opens first available document (key 'o')
- action_open_overview() - opens overview (key '1')
- action_open_sources() - opens sources (key '2')
- action_open_plan() - opens plan (key '3')
- action_open_backlog() - opens backlog (key '4')

## Verification
- Syntax check passed
- All 14 UI smoke tests pass

## Notes
TopicBrowser methods remain unchanged as per constraints. Keys will now work when Topics tab is active.

Commit: fbe1fdc
