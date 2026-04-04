# JQL Patterns Reference

Read this file when the user needs JQL beyond the common patterns in SKILL.md.

## Operators

| Operator | Example | Notes |
|----------|---------|-------|
| `=`, `!=` | `status = "Done"` | Exact match |
| `~`, `!~` | `summary ~ "login"` | Text contains |
| `IN`, `NOT IN` | `status IN ("To Do", "In Progress")` | Multiple values |
| `IS`, `IS NOT` | `assignee IS EMPTY` | Null checks |
| `>`, `>=`, `<`, `<=` | `created >= -7d` | Date/number comparison |
| `WAS`, `WAS NOT` | `status WAS "In Progress"` | Historical state |
| `CHANGED` | `status CHANGED FROM "Open" TO "Done"` | Field change history |

## Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `currentUser()` | Logged-in user | `assignee = currentUser()` |
| `now()` | Current timestamp | `due < now()` |
| `startOfDay()` | Midnight today | `created >= startOfDay()` |
| `startOfWeek()` | Start of current week | `created >= startOfWeek()` |
| `startOfMonth()` | Start of current month | `created >= startOfMonth("-1")` |
| `endOfDay()` | End of today | `due <= endOfDay()` |
| `openSprints()` | Active sprints | `sprint IN openSprints()` |
| `closedSprints()` | Completed sprints | `sprint IN closedSprints()` |
| `membersOf("team")` | Group members | `assignee IN membersOf("dev-team")` |

## Relative dates

- `-1d` — 1 day ago
- `-2w` — 2 weeks ago
- `-1M` — 1 month ago
- `-1y` — 1 year ago
- Combine with functions: `startOfDay("-3d")` = 3 days ago at midnight

## Complex query examples

### Overdue items
```
project = MYPROJECT AND due < now() AND status != "Done"
```

### Stale in-progress (no update in 5+ days)
```
project = MYPROJECT AND status = "In Progress" AND updated < -5d
```

### My items across multiple projects
```
assignee = currentUser() AND project IN ("PROJ-A", "PROJ-B") AND status != "Done" ORDER BY priority DESC
```

### Bugs by severity in current sprint
```
type = Bug AND sprint IN openSprints() AND priority IN ("High", "Critical") ORDER BY priority DESC, created ASC
```

### Items changed status this week
```
project = MYPROJECT AND status CHANGED AFTER startOfWeek()
```

### Unassigned items in backlog
```
project = MYPROJECT AND assignee IS EMPTY AND sprint IS EMPTY AND status = "To Do"
```

### Items blocked by a specific ticket
```
issue IN linkedWorkItems("MYPROJECT-100", "is blocked by")
```

### Recently resolved by my team
```
project = MYPROJECT AND status CHANGED TO "Done" AFTER -7d AND assignee IN membersOf("dev-team")
```

## Ordering

- `ORDER BY created DESC` — newest first
- `ORDER BY priority DESC, created ASC` — highest priority, then oldest
- `ORDER BY updated DESC` — most recently touched

## Common mistakes

- `status = Done` — always quote values for consistency: `status = "Done"` (unquoted single words may work but quoting avoids surprises)
- `assignee = "me"` — use `assignee = currentUser()`, not a string
- `sprint = "Sprint 5"` — use `sprint IN openSprints()` unless targeting a specific named sprint
- `created > "2024-01-01"` — use `created >= "2024-01-01"` for inclusive start (JQL date comparisons exclude the boundary with `>`)
