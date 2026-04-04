# jira-skill

An [Agent Skill](https://agentskills.io) for managing Jira work items with [Atlassian CLI (`acli`)](https://developer.atlassian.com/cloud/acli/) and [`mdadf`](https://github.com/chenhunghan/mdadf) for Markdown-to-ADF conversion.

## What it does

- View, create, edit, search, transition, assign, and comment on Jira work items
- Convert Markdown descriptions and comments to Atlassian Document Format (ADF) via `mdadf --compact`
- Resolve the target project from issue keys, explicit project names, or a configurable default
- Structured bug templates with bold section labels
- Cross-platform: POSIX process substitution on macOS/Linux, temp files on Windows PowerShell

## Prerequisites

- [`acli`](https://developer.atlassian.com/cloud/acli/guides/install-acli/) — Atlassian CLI
- [`mdadf`](https://github.com/chenhunghan/mdadf) — Markdown to ADF converter

## Install

```sh
npx skills add chenhunghan/jira-skill
```

## Configuration

No setup needed. The skill will ask for your Jira project key on first use and save it automatically.

To set it ahead of time, create `.jira-skill.json` in your repo:

```json
{ "defaultProject": "YOUR_PROJECT_KEY" }
```

## Why this skill

- **Uses Atlassian's own CLI (`acli`)** — not a third-party wrapper or MCP-only guidance. First-party auth, pagination, and field handling out of the box.
- **Rich text that works** — write Markdown, get proper Jira formatting. `mdadf` converts to ADF so descriptions and comments render correctly, not as raw JSON or plain text.
- **Safe by default** — won't modify Jira unless you ask. Shows you what it'll do before mutating. Checks status before transitions.
- **Zero setup** — asks for your project key on first use. No Python, no Docker, no config files required to get started.
- **Tested** — 38 evals verify correct commands, safety rules, and that the skill only triggers for Jira work (not GitHub PRs, Confluence, etc.).

Compared against [8 other Jira skills](https://skills.sh/?q=jira) — see the [competitive analysis](https://github.com/chenhunghan/jira-skill/commit/12684e0) for details.


## License

MIT
