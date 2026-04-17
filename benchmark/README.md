# Why `jira-skill` saves tokens vs Atlassian MCP

Using `jira-skill` instead of the [Atlassian MCP server](https://support.atlassian.com/rovo/docs/getting-started-with-the-atlassian-remote-mcp-server/) cuts **~80% of Jira-related tokens** on a typical day. Less noise in your context window, fewer rate-limit hits, faster tool-call roundtrips, and lower API cost.

## Per-task savings

| What you're doing | `jira-skill` | Atlassian MCP | You save |
|---|---:|---:|---:|
| Starting a session (SKILL.md only vs full 31-tool MCP) | 1,932 tok | 7,421 tok | **74%** |
| Viewing one ticket (~4 KB description) | 1,022 tok | 1,865 tok | **45%** |
| Viewing a barebones ticket (empty description) | 32 tok | 10,046 tok | **99.7%** |
| Listing your 5 most recent tickets (default fields) | 618 tok | 10,032 tok | **94%** |
| Listing 5 tickets, explicitly projected to `summary, status, type` | 410 tok | 1,535 tok | **73%** |
| Creating a ticket with a rich markdown body (MCP default: ADF) | 269 tok | 1,016 tok | **74%** |

The **barebones** row is the ceiling: even with no description and no comments, MCP ships custom-field metadata, parent expansion, and every field's `self` + avatar URLs — ~10 KB of boilerplate. `acli` shows Key / Type / Summary / Status / Assignee in 127 bytes.

The **projected-listing** row is the *best case for MCP* — when the caller explicitly sets `fields: [...]`. Even then, per-field `self` URLs and nested metadata leave MCP at ~3.7× the skill.

Startup is a range, not a single constant. `jira-skill` starts at **1,932 tok** for `SKILL.md` alone and rises to **5,086 tok** if every reference page is loaded. Atlassian MCP is **3,950 tok** for the Jira-focused subset and **7,421 tok** for the full 31-tool server. The per-day totals below use the default comparison shown in the table; the read-path measurements dominate the overall savings either way.

Numbers are per operation, from real sanitized fixtures in this repo.

## A day in the life

Realistic daily workload: 1 session + 10 ticket views + 5 JQL searches + 3 issue creates with a rich markdown description.

| | Tokens (one day) |
|---|---:|
| `jira-skill` | ~16,000 |
| Atlassian MCP (default) | ~79,000 |
| **Difference** | **~63,000 fewer (~80%)** |

## End-to-end: shipping a ticket

For developers pointing an agent at Jira as execution context, the full loop matters more than any single op. Canonical dev cycle — agent reads the ticket, pulls related context, marks in-progress, comments, opens a PR, links it back:

| # | Step | `jira-skill` | MCP |
|---|---|---:|---:|
| 0 | Session start | 1,932 | 7,421 |
| 1 | Fetch ticket body | 1,022 | 1,865 |
| 2 | List related tickets | 618 | 10,032 |
| 3 | Transition To Do → In Progress | 30 | 130 |
| 4 | Comment: "starting work" | 55 | 710 |
| 5 | Transition In Progress → In Review | 30 | 130 |
| 6 | Comment with PR link | 55 | 710 |
| | **Total per loop** | **3,742** | **20,998** |

**~82% fewer tokens per dev loop (~5.6× lighter). At a 200K context window, `jira-skill` fits ~53 complete loops per session vs MCP's ~9 — ~5.9× more dev cycles before context pressure kicks in.**

Steps 0-2 are measured per-op benchmarks; steps 3-6 are derived from committed fixtures (comment-object size pulled from the barebones fixture) and from `acli`/MCP tool-call shapes — no live mutations performed. Reasoning tokens between tool calls aren't counted, so the real gap is likely larger. Run `bash benchmark/bench.sh measure-loop` to recompute with your own numbers.

## Why the gap is this wide

- **Reads.** Every MCP response embeds repeated per-issue metadata — self-URLs, 4-size avatar URLs, cloudId-laden links, and custom-field slots — regardless of how small the issue is. In the committed fixtures, `acli` stays around **~4 KB** for both a single-issue view (**4,090 bytes**) and a 5-result search (**4,052 bytes**), while MCP grows from **7,459 bytes** for one issue to **40,130 bytes** for five issues. We have not benchmarked 100-result searches yet; the claim here is the measured 1-to-5 result spread plus the repeated metadata visible in the fixtures.
- **Writes.** MCP defaults to Atlassian Document Format (ADF) for descriptions, so the agent has to emit verbose structural JSON for every heading, table, code block, and link. `jira-skill` pipes markdown through `mdadf --compact` in a subprocess, so the agent only ever emits raw markdown — regardless of how rich the body is.
- **Startup.** Enabling Atlassian's MCP loads **31 tool schemas** (Jira + Confluence) into context before you do anything. `jira-skill` is one `SKILL.md` file; reference pages load only when the agent needs them.

## Translated to dollars

At [Claude Opus 4.7](https://www.anthropic.com/pricing#api) standard input pricing ($15 / MTok, April 2026):

| | Cost (one day) |
|---|---:|
| `jira-skill` | $0.24 |
| Atlassian MCP | $1.19 |
| **Saved** | **$0.95/day** |

Projected per user: **~$4.75/week, ~$240/year** (250 workdays). A team of 10 saves **~$2,400/year**. At the Opus 4.7 1M-context tier ($30 / MTok), every dollar figure doubles. Prompt caching (if enabled) scales both arms down proportionally, so the ratio holds.

## Caveats, briefly

- Token counts are approximations (character count ÷ 4); ratios are stable.
- MCP can reach near-parity on create if the agent remembers to set `contentFormat: "markdown"` on every call — the skill gets you there by default.
- Projection closes — but doesn't close — the read gap: MCP still costs ~3.7× even when the agent explicitly requests minimal fields.
- Agent reasoning and final-answer output tokens aren't measured; the real gap is likely a bit bigger.

Full method and reproduction steps: [METHODOLOGY.md](./METHODOLOGY.md).
