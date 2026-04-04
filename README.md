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

Install with [`npx skills`](https://github.com/vercel-labs/skills):

```sh
npx skills add chenhunghan/jira-skill --skill jira -g -a codex -a claude-code -y
```

Or install directly from the skill path:

```sh
npx skills add https://github.com/chenhunghan/jira-skill/tree/main/jira -g -a codex -a claude-code -y
```

Notes:

- Omit `-g` to install into the current project instead of your user-wide agent config.
- Add or replace `-a` flags for other supported agents.

## Configuration

After installing, edit `config.json` in the skill directory and replace `MYPROJECT` with your Jira project key:

```json
{
  "defaultProject": "YOUR_PROJECT_KEY"
}
```

The skill will ask for your project key on first use if this is not configured.

## License

MIT
