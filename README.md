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

## What Makes This Skill Stand Out

We compared this skill against 8 popular Jira skills on [skills.sh](https://skills.sh/?q=jira) and GitHub:

| Skill | Approach | Backend | Scripts/Code | Evals |
|-------|----------|---------|-------------|-------|
| **This skill** | acli + mdadf pipeline | Official Atlassian CLI | 0 (doc-only, delegates to acli) | 38 (12 task + 26 trigger) |
| [SpillwaveSolutions/jira](https://github.com/SpillwaveSolutions/jira) | MCP guidance | Atlassian MCP | 0 | 0 |
| [grandcamel/JIRA-Assistant-Skills](https://github.com/grandcamel/JIRA-Assistant-Skills) | Hub-and-spoke router | External `jira-as` PyPI lib | 0 in-repo (external lib) | YAML golden sets |
| [netresearch/jira-skill](https://github.com/netresearch/jira-skill) | Python CLI scripts | REST API via `atlassian-python-api` | ~14 Python scripts | 10 evals + unit tests |
| [davila7/claude-code-templates](https://skills.sh/davila7/claude-code-templates/jira) | Dual backend (CLI+MCP) | jira-cli or Atlassian MCP | 0 | 0 |
| [code-and-sorts/jira-cli](https://skills.sh/code-and-sorts/awesome-copilot-agents/jira-cli) | CLI reference | jira-cli (ankitpokhrel) | 0 | 0 |
| [skillcreatorai/jira-issues](https://skills.sh/skillcreatorai/ai-agent-skills/jira-issues) | REST API or MCP | Direct REST or MCP | 0 | 0 |
| [claude-office-skills/jira-automation](https://github.com/claude-office-skills/skills/tree/main/jira-automation) | MCP automation | Atlassian MCP | 0 | 0 |
| [membranedev/jira](https://skills.sh/membranedev/application-skills/jira) | Membrane CLI | Membrane connector | 0 | 0 |

### Key differentiators

1. **Official Atlassian CLI (`acli`)** — the only skill built on Atlassian's own CLI rather than third-party wrappers (jira-cli), raw REST calls, or MCP-only guidance. `acli` is maintained by Atlassian Labs, receives first-party updates, and handles auth, pagination, and field resolution natively.

2. **Dedicated Markdown-to-ADF pipeline (`mdadf`)** — competitors either skip rich text, inline raw ADF JSON, or rely on MCP servers to handle conversion. This skill pipes Markdown through `mdadf --compact` using POSIX process substitution (`<(...)`) for zero temp files on macOS/Linux, with automatic temp-file fallback on Windows PowerShell.

3. **Bug template with bold section labels** — uses `**Short Description**` instead of `## Short Description`. This is a Jira-specific insight: Markdown headings become ADF headings that pollute Jira's outline/table-of-contents. Bold labels render clean, scannable bug reports without side effects. No other skill documents this pattern.

4. **Constraint-based safety model** — explicit mutation-intent requirement (won't change Jira unless the user asks), read-only for projects (never modifies project config), and key-first targeting (prefers direct key commands over JQL for single items). Competitors either lack safety rules entirely or document them as informal guidance.

5. **5-level project resolution** — issue key prefix → explicit project name → workspace `.jira-skill.json` → user-global `~/.config/jira-skill/config.json` → ask user (with offer to save). Workspace-local config means different repos get different defaults. Most competitors require the project every time or assume a single hardcoded default.

6. **Dual-layer eval suite (38 cases)** — 12 task-level behavioral evals + 26 trigger-level evals (12 true, 14 false). The false-positive trigger tests are unique: they verify the skill does NOT activate for GitHub PRs, Confluence, auth setup, REST scripting, dashboards, automation rules, or non-Jira trackers. No other surveyed skill has trigger-boundary testing.

7. **Smallest footprint** — one `SKILL.md` (~350 lines), one `config.json`, and eval files. No Python runtime, no Docker, no external libraries beyond `acli` and `mdadf`. Competitors range from 14 Python scripts (netresearch) to 245 external scripts (grandcamel) to multi-container setups.


## License

MIT
