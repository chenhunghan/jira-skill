# Why `jira-skill` saves you tokens (and money)

Using `jira-skill` instead of the [Atlassian MCP server](https://support.atlassian.com/rovo/docs/getting-started-with-the-atlassian-remote-mcp-server/) cuts **~80% of Jira-related tokens** on a typical day — about **$0.95/day per user**, or **~$240/user/year** at [Claude Opus 4.7](https://www.anthropic.com/pricing#api) standard input pricing ($15 / MTok, April 2026). A team of 10 saves **~$2,400/year**. At the 1M-context tier, all dollar figures double.

## Where the savings come from

| Everyday task | `jira-skill` | Atlassian MCP | You save |
|---|---:|---:|---:|
| Starting a session (Jira capability loaded in context) | 1,932 tok | 7,421 tok | **74%** |
| Viewing one ticket | 1,022 tok | 1,865 tok | **45%** |
| Listing your 5 most recent tickets | 618 tok | 10,032 tok | **94%** |
| Creating a ticket with a rich markdown body | 269 tok | 1,016 tok | **74%** |

Numbers are per operation, from real sanitized fixtures in this repo. See [METHODOLOGY.md](./METHODOLOGY.md) for how they're captured and measured.

## A day in the life

A realistic workday: 1 session + 10 ticket views + 5 JQL searches + 3 issue creates with a rich markdown description.

| | Tokens (one day) | Cost @ $15/MTok |
|---|---:|---:|
| `jira-skill` | ~16,000 | **$0.24** |
| Atlassian MCP (default) | ~79,000 | **$1.19** |
| **Difference** | **63,000 fewer tokens (~80%)** | **$0.95/day saved** |

Projected: **$4.75/week, ~$240/year** per user. A team of 10: **~$2,400/year**. And that's just the dollar line — tokens saved also keep more of your context window free for actual reasoning.

## Why the gap is this wide

- **Reads.** Every MCP response embeds ~7 KB of metadata per issue — self-URLs, 4-size avatar URLs, cloudId-laden links — regardless of how small the issue is. That overhead compounds linearly: 1 issue is bad, 10 issues is dire. `acli` returns a flat table that stays ~4 KB whether you pull 1 row or 100.
- **Writes.** MCP defaults to Atlassian Document Format (ADF) for descriptions, so the agent has to emit verbose structural JSON for every heading, table, code block, and link. `jira-skill` pipes markdown through `mdadf --compact` in a subprocess, so the agent only ever emits raw markdown — regardless of how rich the body is.
- **Startup.** Enabling Atlassian's MCP loads **31 tool schemas** (Jira + Confluence) into context before you do anything. `jira-skill` is one `SKILL.md` file; reference pages load only when the agent needs them.

## Caveats, briefly

- Token counts are approximations (character count ÷ 4); ratios are stable.
- MCP can reach near-parity on create if the agent remembers to set `contentFormat: "markdown"` on every call — the skill gets you there by default.
- Agent reasoning and final-answer output tokens aren't measured; the real gap is likely a bit bigger.

Full method and reproduction steps: [METHODOLOGY.md](./METHODOLOGY.md).
