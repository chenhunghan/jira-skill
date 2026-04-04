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

Create a `config.local.json` in the skill directory with your Jira project key:

```json
{
  "defaultProject": "YOUR_PROJECT_KEY"
}
```

This file is gitignored and won't be overwritten by `npx skills update`. The shipped `config.json` is a schema reference with a placeholder — don't edit it directly.

The skill will ask for your project key on first use if neither config file is configured, and save your answer to `config.local.json`.

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

5. **4-level project resolution** — issue key prefix → explicit project name → `config.json` default → ask user (with offer to save). Most competitors require the project every time or assume a single hardcoded default.

6. **Dual-layer eval suite (38 cases)** — 12 task-level behavioral evals + 26 trigger-level evals (12 true, 14 false). The false-positive trigger tests are unique: they verify the skill does NOT activate for GitHub PRs, Confluence, auth setup, REST scripting, dashboards, automation rules, or non-Jira trackers. No other surveyed skill has trigger-boundary testing.

7. **Smallest footprint** — one `SKILL.md` (~350 lines), one `config.json`, and eval files. No Python runtime, no Docker, no external libraries beyond `acli` and `mdadf`. Competitors range from 14 Python scripts (netresearch) to 245 external scripts (grandcamel) to multi-container setups.

### What we learned from competitors

| Lesson | Source | How we applied it |
|--------|--------|-------------------|
| Explicit "NEVER" safety rules with reasoning | davila7 | Added 5 safety rules to SKILL.md with explanations |
| Transition verification before status changes | davila7, SpillwaveSolutions | Added pre-transition fetch rule |
| Conditional reference loading (don't bloat context) | davila7 | Already minimal by design; no reference files to load |
| Risk stratification for operations | grandcamel | Added risk levels to commands reference |
| Wiki markup vs Markdown distinction | netresearch | Our mdadf pipeline handles this automatically — no user-facing syntax switching |
| Multi-profile / multi-instance support | netresearch | Deferred — acli handles profiles natively via `acli auth` |
| Hub-and-spoke routing for large skill sets | grandcamel | Not applicable — single focused skill is our design choice |
| Dry-run for write operations | netresearch | acli supports `--yes` flag; added guidance for confirm-before-mutate |

## License

MIT
