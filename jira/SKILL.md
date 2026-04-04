---
name: jira
description: Use this skill for Jira work items with Atlassian CLI (`acli`). Trigger it whenever the user mentions Jira, JQL, issue or ticket keys like `ABC-123`, assignees, status changes, comments, rich-text Jira descriptions, or Markdown that needs to become Jira ADF. Resolve the project from an explicit issue key first, then `.jira-skill.json` in the working directory, then `~/.config/jira-skill/config.json`, then the in-repo `config.json` placeholder. Do not use it for GitHub PR edits, repo/codebase searches (even if "jira" appears as a package or library name), Confluence, auth setup, REST API scripting, or non-Jira trackers.
compatibility: Requires `acli` and `mdadf` CLI. Uses `zsh` or `bash` process substitution for piping ADF into acli flags. On Windows PowerShell, uses temp files instead.
---

# Jira Work Item Management

Uses Atlassian CLI (`acli`) to view, search, filter, create, and update work items in Jira projects.

## Prerequisites

Check that both dependencies are available before running any commands. Do this once at the start of the session, not before every command.

1. **acli** — run `acli --version`. If missing:
   - macOS: `brew install atlassian-labs/tap/acli`
   - Linux/Windows: download from https://developer.atlassian.com/cloud/acli/guides/install-acli/
   - After install, authenticate with `acli auth login`

2. **mdadf** — run `mdadf --version`. If missing, download the binary for your platform from https://github.com/chenhunghan/mdadf/releases/latest and place it on your PATH:
   - macOS (Apple Silicon): `curl -L -o mdadf.tar.gz https://github.com/chenhunghan/mdadf/releases/latest/download/mdadf-aarch64-apple-darwin.tar.gz && tar xzf mdadf.tar.gz && mv mdadf /usr/local/bin/`
   - macOS (Intel): replace `aarch64-apple-darwin` with `x86_64-apple-darwin`
   - Linux (x86_64): replace with `x86_64-unknown-linux-gnu`
   - Windows: download the `.zip` from the releases page and add to PATH
   - If sudo is needed: install to `$HOME/.local/bin` and ensure it is on PATH.

If either tool is missing and cannot be installed (e.g. no network access), tell the user exactly what commands to run and stop.

## Operating Constraints

- **READ-ONLY for Projects**: Never modify Jira projects themselves. Only create, update, or delete work items within projects.
- **Mutation Intent**: For create, edit, transition, assign, comment, or delete operations, only mutate Jira when the user explicitly asks for that change. If the request is ambiguous, clarify before mutating.
- **Key-First Targeting**: If the user provides a work item key such as `MYPROJECT-1455`, prefer key-based commands over JQL.
- **JQL**: Use `--jql` for selecting, searching, or filtering work items when applicable.
- **Configured Default Project**: If the user does not specify a project, resolve via the Project Resolution chain below (workspace `.jira-skill.json` → user-global `~/.config/jira-skill/config.json` → in-repo `config.json`).
- **Work Item Types**: `Bug`, `Task`, `Story`, `Epic`
- **Rich Text**: Draft Jira descriptions and comment bodies in Markdown first, then convert to ADF with `mdadf --compact` before calling `acli`.

## Project Resolution

Resolve the project key in this order:

1. If the user gives a Jira issue key such as `MYPROJECT-1455`, use its prefix as the project key.
2. If the user explicitly names a project key such as `MYPROJECT`, use that.
3. Otherwise, read `.jira-skill.json` in the current working directory. If it exists and has a valid `defaultProject`, use it. This is the workspace-local config — different repos can have different defaults.
4. Otherwise, read `~/.config/jira-skill/config.json`. This is the user-global fallback, shared across all repos.
5. Otherwise, read `config.json` in this skill's directory (shipped placeholder).
6. If no config has a valid project (missing, placeholder `"MYPROJECT"`, or invalid), ask the user which project key to use. Write their answer to `.jira-skill.json` in the working directory if inside a project, or `~/.config/jira-skill/config.json` if in a global context.

`.jira-skill.json` is workspace-local — add it to `.gitignore` if it should not be shared. `~/.config/jira-skill/config.json` is user-global and survives skill updates. The in-repo `config.json` is a schema reference and ships with a placeholder.

Config schema (both files use the same shape):

```json
{
  "defaultProject": "MYPROJECT"
}
```

## Safety Rules

These rules prevent common Jira mishaps. Follow them without exception.

1. **NEVER transition without fetching current status first.** Jira workflows may require intermediate states (e.g. To Do → In Progress → In Review → Done). Skipping a step fails silently or throws a confusing error. Always run `acli jira workitem view <KEY> --fields "status"` before any transition.

2. **NEVER bulk-modify without explicit user approval.** Each edit notifies watchers. Editing 10 tickets means 10 notification storms. Always confirm with the user before operating on multiple work items.

3. **NEVER edit a description without showing the original.** Jira has no undo. Before replacing a description, display the current content so the user can verify nothing is lost.

4. **NEVER assume transition names are universal.** "Done", "Closed", "Complete", "Resolved" vary by project and workflow scheme. When in doubt, check the current status with `acli jira workitem view <KEY> --fields "status"` and ask the user which target status to use.

5. **NEVER set Priority, Technical Impact, or Business Urgency on new tickets.** These fields are for triage by leads or product. Creating a "Critical" ticket without authorization undermines the triage process. If the user explicitly requests a priority level, acknowledge it and explain that priority is typically set during triage.

## Execution Steps

1. If the request is mutating, review the Safety Rules above. Identify which rules apply before running any command.
2. Resolve the project key using the project resolution rules above.
3. If the request targets a specific work item key, use a key-based command. Use JQL only when searching or targeting multiple work items.
4. If the request needs rich text, write the content in Markdown and convert it to ADF with `mdadf --compact` before running `acli`.
5. Run the appropriate `acli` command.
6. Read and analyze the output. If errors occur, run `acli --help` or the relevant subcommand help for guidance.

## Markdown to ADF

Use `mdadf --compact` to convert Markdown to ADF for any Jira field that accepts ADF.

### POSIX shells (macOS/Linux)

Use process substitution to pipe ADF directly into acli flags:

```bash
acli jira workitem create \
  --summary "Fix the login page" \
  --project "MYPROJECT" \
  --type "Bug" \
  --description-file <(mdadf --compact <<'MD'
**Short Description**
The login page returns a 500 on empty email.
MD
)
```

### Windows PowerShell

Process substitution is not available. Write ADF to a temp file first:

```powershell
mdadf --compact input.md -o $env:TEMP\desc.json
acli jira workitem create `
  --summary "Fix the login page" `
  --project "MYPROJECT" `
  --type "Bug" `
  --description-file $env:TEMP\desc.json
```

### Rules

- Write the intended Jira rich text in Markdown first.
- Keep summaries and titles as plain text.
- Prefer `--key` for single known work items and comments.
- Prefer `--description-file`, `--body-file`, and `--body-adf` over inline JSON arguments.

## Ticket Drafting Format

When creating or rewriting a Jira work item, draft the summary and description from the conversation context first. Use any directly observed code, runtime, or reproduction context only when it is already available. Do not rely on git history or PR links to explain the issue.

### Summary

- Write the summary as a concise, imperative title.
- Prefer the user-facing problem over the proposed fix.
- Use any extra user-provided context to sharpen the title.

Example:

- `Return actionable MCP response when the application is closed`

### Tasks and Stories

For `Task` and `Story` work items:

- Write a 1 to 3 sentence description that focuses on what the problem is and why it matters.
- Do not describe the solution. The implementation or PR can cover that separately.
- Do not include PR links in the description.

### Bugs

For `Bug` work items, use this exact structure in Markdown so the ADF output renders with bold section labels instead of Jira headings:

```md
**Short Description**
[1-2 sentences: what is broken and under what conditions]

**Steps to Reproduce**
1. [First step]
2. [Second step]
3. [Continue until the bug manifests]

**Expected Behavior**
[What should happen when following the steps above]

**Actual Behavior**
[What actually happens. Include the relevant error message when available, truncated to 2000 characters]

**Impact**
[Who is affected and how severely]

**Environment**
- App version: [include if known]
- OS: [include if known, otherwise omit]
```

Bug drafting rules:

- Use bold section labels such as `**Short Description**`, not Markdown headings such as `## Short Description`.
- Derive reproduction steps from the user-provided context and any directly observed behavior.
- If the reproduction steps or expected behavior are too unclear to draft responsibly, ask the user for the missing details before creating the bug.
- Truncate copied error text to 2000 characters.
- Do not set Priority, Technical Impact, or Business Urgency. Leave those for triage.

## Commands Reference

Risk levels: `-` safe/read-only, `!` reversible mutation, `!!` hard to reverse.

### View Work Item `-`

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

### Create Work Item `!`

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

### Edit Work Item `!!`

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

### Create Comment `!`

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

### Update Comment `!!`

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

### Search Work Items `-`

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

### Transition Work Item `!`

Before transitioning, fetch the current status with `acli jira workitem view <KEY> --fields "status"` to confirm the target state is reachable (Safety Rule 1).

```bash
acli jira workitem transition --key "MYPROJECT-733" --status "In Review"
```

### Assign Work Item `!`

```bash
acli jira workitem assign --key "MYPROJECT-801" --assignee "alex@example.com"
```

## Examples

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

## Output Format

When reporting findings, use table format with link to the workitems.
