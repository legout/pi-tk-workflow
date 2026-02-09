# ticket_factory Module

Reusable functions for creating tickets from seed/baseline/plan artifacts.

## Why This Module Exists

Before this module, every `/tf-backlog` command required writing an inline Python script with:
- Repetitive `tk create` subprocess calls
- Manual ticket scoring logic
- Component tag classification boilerplate
- Backlog.md writing code

This module consolidates all that logic into testable, reusable functions.

## Quick Example

```python
from tf.ticket_factory import (
    TicketDef,
    create_tickets,
    write_backlog_md,
    score_tickets,
    apply_dependencies,
    apply_links,
    print_created_summary,
)

# Define tickets
tickets = [
    TicketDef(title="Setup project", description="Initialize repository"),
    TicketDef(title="Implement feature", description="Add the core feature"),
    TicketDef(title="Write tests", description="Add unit tests"),
]

# Score by keyword (setup=10, implement=3, test=1)
scored = score_tickets(tickets)

# Create tickets with auto-component-tags
created = create_tickets(scored, topic_id="seed-foo", mode="seed", component_tags=True)

# Apply dependencies and links
created = apply_dependencies(created, mode="chain")
created = apply_links(created)

# Write backlog.md
write_backlog_md(created, topic_id="seed-foo")

# Print summary
print_created_summary(created)
```

## Key Features

### 1. Automatic Keyword Scoring

Tickets are scored based on keywords in title/description:

| Keyword | Weight | Matches |
|---------|--------|---------|
| setup | 10 | setup, setups, setuping, setuped |
| configure | 8 | configure, configures, configuring, configured |
| define | 6 | define, defines, defining, defined |
| design | 5 | design, designs, designing, designed |
| implement | 3 | implement, implements, implementing, implemented |
| test | 1 | test, tests, testing, tested |

Higher scores = higher priority. Tickets with multiple keywords accumulate scores.

### 2. Automatic Component Tagging

Integrates with `component_classifier` to automatically assign tags like:
- `component:cli` - CLI commands, flags, arguments
- `component:api` - Endpoints, REST, GraphQL
- `component:tests` - Tests, pytest, coverage
- `component:config` - Configuration, settings, env vars
- `component:workflow` - Ralph, loop, tickets, backlog
- `component:agents` - Agents, subagents, prompts

### 3. Duplicate Detection

Automatically skips tickets whose normalized title matches existing tickets:

```python
existing_titles = {"setup project", "write tests"}
created = create_tickets(
    scored,
    topic_id="seed-foo",
    existing_tickets=existing_titles,
    skip_duplicates=True,
)
# Skipped tickets will have `skipped=True` and `skip_reason` set
```

### 4. Dependency Modes

Supports different dependency strategies:

```python
# Chain mode (default): each ticket depends on previous
created = apply_dependencies(created, mode="chain")

# Phases mode: tickets in group N depend on all in group N-1
groups = [[ticket1.id], [ticket2.id, ticket3.id], [ticket4.id]]
created = apply_dependencies(created, dependency_groups=groups, mode="phases")

# No dependencies
created = apply_dependencies(created, mode="none")
```

### 5. Automatic Linking

Links tickets based on:
- Same component tags + adjacent in order
- Title similarity (shared significant words)

Conservative approach (under-linking preferred).

## API Reference

### Classes

#### `TicketDef`

```python
@dataclass
class TicketDef:
    title: str
    description: str
    optional_tags: List[str] = None
```

Definition of a ticket to create.

#### `CreatedTicket`

```python
@dataclass
class CreatedTicket:
    id: str
    title: str
    score: int
    tags: List[str]
    depends_on: List[str] = None
    links: List[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
```

Result of ticket creation.

### Functions

#### `score_tickets(tickets, weights=None)`

Score tickets based on keyword weights.

**Returns:** `List[Tuple[int, TicketDef]]` sorted by score descending

#### `create_tickets(scored_tickets, topic_id, mode="seed", ...)`

Create tickets via `tk create` command.

**Parameters:**
- `scored_tickets`: List from `score_tickets()`
- `topic_id`: Topic ID (e.g., "seed-foo", "plan-bar")
- `mode`: One of "seed", "baseline", "plan", "openspec"
- `base_tags`: Base tags (default: ["tf", "backlog", mode])
- `component_tags`: Whether to auto-assign component tags (default: True)
- `existing_tickets`: Set of normalized titles to skip
- `priority`: Ticket priority (default: 2)
- `dry_run`: Print what would be done without creating

**Returns:** `List[CreatedTicket]`

#### `write_backlog_md(created_tickets, topic_id, output_path=None, knowledge_dir=None)`

Write `backlog.md` file for a topic.

**Returns:** `Path` to the written file

#### `apply_dependencies(created_tickets, dependency_groups=None, mode="chain", dry_run=False)`

Apply dependencies between tickets using `tk dep` command.

**Returns:** Updated `List[CreatedTicket]` with `depends_on` populated

#### `apply_links(created_tickets, dry_run=False)`

Apply links between related tickets using `tk link` command.

**Returns:** Updated `List[CreatedTicket]` with `links` populated

#### `print_created_summary(created_tickets)`

Print a summary of created tickets to stdout.

## Testing

Run tests:

```bash
pytest tests/test_ticket_factory.py
```

## Example Scripts

- `ticket_factory_example.py` - Complete example showing full workflow

## Migration from Inline Scripts

**Before:**

```python
$ python - <<'PY'
 from __future__ import annotations
 import subprocess

 TOPIC_ID = 'seed-foo'

 # ... inline scoring logic ...
 # ... subprocess calls to tk create ...
 # ... manual backlog.md writing ...
PY
```

**After:**

```python
from tf.ticket_factory import (
    TicketDef,
    create_tickets,
    write_backlog_md,
    score_tickets,
)

tickets = [TicketDef(...), ...]
scored = score_tickets(tickets)
created = create_tickets(scored, topic_id=TOPIC_ID, mode="seed")
write_backlog_md(created, topic_id=TOPIC_ID)
```

Much cleaner, testable, and reusable.
