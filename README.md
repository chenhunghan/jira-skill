# jira-skill

An [Agent Skill](https://agentskills.io) for managing Jira work items with [Atlassian CLI (`acli`)](https://developer.atlassian.com/cloud/acli/) and [`mdadf`](https://github.com/chenhunghan/mdadf) for Markdown-to-ADF conversion.

## What it does

- **View, create, edit, search, transition, assign, and comment** on Jira work items using Atlassian's own CLI ([`acli`](https://developer.atlassian.com/cloud/acli/guides/install-acli/))
- **Rich text that works** — write Markdown, get proper Jira formatting via [`mdadf`](https://github.com/chenhunghan/mdadf). No raw JSON or plain text.
- **Safe by default** — won't modify Jira unless you ask. Shows current state before edits. Checks status before transitions.
- **Zero setup** — asks for your project key on first use. No Python, no Docker, no config files required.
- **Cross-platform** — macOS, Linux, and Windows PowerShell

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
