# Commands Reference

Read this file when you need the full flag reference for an `acli` command.

Risk levels: `-` safe/read-only, `!` reversible mutation, `!!` hard to reverse.

## View Work Item `-`

```bash
acli jira workitem view MYPROJECT-1455 --fields "summary,comment"
```

**Flags:**
- `-f, --fields string` - Comma-separated list of fields to return
  - `*all` - returns all fields
  - `*navigable` - returns navigable fields
  - `summary,comment` - returns only summary and comments
  - `-description` - excludes description from default fields
  - Default: `key,issuetype,summary,status,assignee,description`

## Create Work Item `!`

```bash
acli jira workitem create \
  --summary "Return actionable MCP response when the application is closed" \
  --project "MYPROJECT" \
  --type "Bug" \
  --assignee "user@example.com" \
  --label "bug" \
  --description-file <(mdadf --compact <<'MD'
**Short Description**
When the application is closed, MCP clients report a generic disconnect error instead of an actionable response.

**Steps to Reproduce**
1. Quit the application completely.
2. Open an MCP client.
3. Invoke a tool endpoint.

**Expected Behavior**
The client should receive a response explaining the application must be opened first.

**Actual Behavior**
The client reports: `MCP server: Server disconnected.`

**Impact**
Users see a generic error and do not know the next recovery step.

**Environment**
- App version: unknown
MD
)
```

**Flags:**
- `-s, --summary string` - Work item summary (required)
- `-p, --project string` - Project key (required)
- `-t, --type string` - Work item type: Bug, Task, Story, Epic
- `-a, --assignee string` - Assign by email or account ID. Use `@me` to self-assign, `default` for project default
- `-d, --description string` - Description in plain text or ADF
- `--description-file string` - Description file in plain text or ADF
- `-l, --label strings` - Labels (comma-separated)

## Edit Work Item `!!`

Before editing, fetch and display the current content so the user can verify nothing is lost (Safety Rule 3).

```bash
acli jira workitem edit \
  --key "MYPROJECT-457" \
  --description-file <(mdadf --compact <<'MD'
# Updated context

This still affects current sprint work and needs follow-up.
MD
) \
  --yes
```

**Flags:**
- `-k, --key string` - Work item key(s)
- `-s, --summary string` - Edit summary
- `-d, --description string` - Edit description in plain text or ADF
- `--description-file string` - Read the description in plain text or ADF from a file
- `-a, --assignee string` - Change assignee
- `-t, --type string` - Change work item type
- `-l, --labels string` - Edit labels
- `--remove-labels string` - Remove specific labels
- `--remove-assignee` - Remove assignee
- `-y, --yes` - Confirm without prompting

## Create Comment `!`

```bash
acli jira workitem comment create \
  --key "MYPROJECT-1455" \
  --body-file <(mdadf --compact <<'MD'
## Update

- reproduced in dev
- waiting on backend logs
MD
)
```

**Flags:**
- `-b, --body string` - Comment body in plain text or ADF
- `-F, --body-file string` - Comment body file in plain text or ADF
- `--editor` - Open an editor for the body instead of passing content directly

## Update Comment `!!`

```bash
acli jira workitem comment update \
  --key "MYPROJECT-1455" \
  --id "10001" \
  --body-adf <(mdadf --compact <<'MD'
## Resolution

The fix is ready for verification.
MD
)
```

**Flags:**
- `-b, --body string` - Comment body text
- `--body-adf string` - Comment body in ADF JSON file
- `-F, --body-file string` - Comment body in plain text file

## Search Work Items `-`

```bash
acli jira workitem search --jql "project = MYPROJECT AND assignee = currentUser() AND sprint in openSprints()"
```

**Common JQL Patterns:**
- `project = MYPROJECT` - Filter by project
- `assignee = currentUser()` - My assigned items
- `status = "In Progress"` - Filter by status
- `sprint in openSprints()` - Current sprint items
- `created >= -7d` - Created in last 7 days
- `type = Bug AND priority = High` - High priority bugs

For complex queries (historical operators, date functions, linked issues, team membership), read [jql-patterns.md](jql-patterns.md).

## Transition Work Item `!`

Before transitioning, fetch the current status with `acli jira workitem view <KEY> --fields "status"` to confirm the target state is reachable (Safety Rule 1).

```bash
acli jira workitem transition --key "MYPROJECT-733" --status "In Review"
```

## Assign Work Item `!`

```bash
acli jira workitem assign --key "MYPROJECT-801" --assignee "alex@example.com"
```

## Quick Reference

| Intent | Command |
|--------|---------|
| View ticket | `acli jira workitem view MYPROJECT-1455 --fields "summary,comment"` |
| My open sprint items | `acli jira workitem search --jql "project = MYPROJECT AND assignee = currentUser() AND sprint in openSprints()"` |
| Create a bug | `acli jira workitem create --summary "Bug title" --project "MYPROJECT" --type "Bug" --description-file <(mdadf --compact <<'MD' ... MD)` |
| Edit a description | `acli jira workitem edit --key "MYPROJECT-457" --description-file <(mdadf --compact <<'MD' ... MD) --yes` |
| Add a comment | `acli jira workitem comment create --key "MYPROJECT-801" --body-file <(mdadf --compact <<'MD' ... MD)` |
| Update a comment | `acli jira workitem comment update --key "MYPROJECT-801" --id "10001" --body-adf <(mdadf --compact <<'MD' ... MD)` |
| Transition | `acli jira workitem transition --key "MYPROJECT-733" --status "In Review"` |
| Assign | `acli jira workitem assign --key "MYPROJECT-801" --assignee "user@example.com"` |
