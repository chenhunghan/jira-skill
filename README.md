# jira-skill

CLI-first, markdown-first Jira skill — ~80% fewer tokens than Atlassian MCP on everyday tasks.

An [Agent Skill](https://agentskills.io) for managing Jira work items with [Atlassian CLI (`acli`)](https://developer.atlassian.com/cloud/acli/) and [`mdadf`](https://github.com/chenhunghan/mdadf) for Markdown-to-ADF conversion.

## What it does

- **Zero setup** — asks for your project name on first use. No Python, no Docker, no config files required.
- **Rich text that works** — write Markdown, get proper Jira formatting via [`mdadf`](https://github.com/chenhunghan/mdadf). No raw JSON or plain text.
- **View, create, edit, search, transition, assign, and comment**

## vs Atlassian MCP

Saves **~80%** of Jira-related tokens on everyday tasks — more context room for actual work, fewer rate-limit hits, lower API cost.

Top wins per operation:

- Listing tickets: **94%** fewer tokens
- Session startup: **74%** fewer
- Rich-markdown creates: **74%** fewer

Full numbers, methodology, and cost translation: [`benchmark/README.md`](./benchmark/README.md).

## Install

```sh
npx skills add chenhunghan/jira-skill
```

Requires [`acli`](https://developer.atlassian.com/cloud/acli/guides/install-acli/) and [`mdadf`](https://github.com/chenhunghan/mdadf) — the skill will check for both on first run.

On first use the skill asks which Jira project to use and where to save the config — no manual setup needed. If you prefer to pre-configure:

```sh
# Global — shared across all repos (recommended for most users)
mkdir -p ~/.config/jira-skill
echo '{ "defaultProject": "YOUR_PROJECT_KEY" }' > ~/.config/jira-skill/config.json

# Per-repo — overrides the global config for this repo only
echo '{ "defaultProject": "YOUR_PROJECT_KEY" }' > .jira-skill.json
```


## License

MIT
