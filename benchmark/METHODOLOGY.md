# Methodology

How the numbers in [README.md](./README.md) are produced — capture, sanitization, measurement, and caveats. This is for people who want to reproduce or scrutinize the benchmark.

## What's measured

Per task, for each arm, the **tool-result payload** (read tasks) or the **tool-call input** (write tasks): bytes, character count, and approximate Claude tokens (chars ÷ 4).

**Approximate?** Yes — exact counting would use `anthropic.messages.count_tokens` and needs `ANTHROPIC_API_KEY`. The same approximation is applied to both arms, so the **ratio** is faithful. Expected error is within ~5% for English + JSON content.

Plus a fixed-overhead measurement: `SKILL.md` + references vs the aggregated JSON Schema for every Atlassian MCP tool.

**What's not measured** — yet:
- Agent reasoning, multi-turn tokens, final answer output. That's "full agent-loop" and needs an LLM harness.
- Output tokens (model response). On creates and transitions both arms return similar small confirmations.
- Prompt caching. Caching reduces the absolute cost for both arms roughly proportionally, so ratios hold.

## Pricing assumption

[README.md](./README.md) dollar figures use **Claude Opus 4.7 standard-tier input pricing — $15 / MTok** (April 2026). Tool-result tokens count as input tokens. At the 1M-context tier ($30/MTok above 200K tokens), every dollar figure doubles. Cache-read pricing would scale both arms down equally; ratios stay the same.

## Tasks

Read tasks captured against a real Jira, sanitized to committable fixtures:

| task | skill | MCP |
|---|---|---|
| `small-issue` | `acli jira workitem view <KEY>` | `getJiraIssue` |
| `barebones` | same, targeted at an empty-description issue | same |
| `recent-assigned` | `acli jira workitem search --jql '...' --limit 5` | `searchJiraIssuesUsingJql`, `maxResults: 5` |
| `recent-assigned-projected` | same, plus `--fields key,summary,status,issuetype` | same, plus `fields: ["summary","status","issuetype"]` |

Write tasks synthesized (no Jira side effects) to measure the input payload each arm would emit:

| task | skill | MCP variants |
|---|---|---|
| `create-short` | `acli jira workitem create ... --description-file <(mdadf --compact <<MD ... MD)` | `createJiraIssue` with ADF (default) or markdown (opt-in via `contentFormat`) |
| `create-rich` | same, richer markdown body | same |

Fixed-overhead: `measure-overhead` compares `jira/SKILL.md` (+ on-demand references) against the full 31-tool Atlassian MCP schema dump.

Agent-loop (scripted scenario, not captured):

| task | scenario |
|---|---|
| `ship-ticket` | Sum of a 7-step canonical dev loop: session start + fetch ticket + list related + 2× transition + 2× comment. Steps 0-2 reuse measured per-op numbers; 3-6 use conservative estimates (no Jira mutations performed). The scenario JSON is swappable — refine the estimates with your own measurements and the totals recompute. |

Read tasks use each arm's natural defaults — no `--fields` projection, no `responseContentFormat` override.

## Data handling

Captures include real Jira content (issue keys, descriptions, account IDs, display names, time zones). They never land in git.

- `capture/` — **gitignored**. Raw captures live here.
- `fixtures/` — committed. Sanitized outputs.
- `blocklist.txt` — **gitignored**. Substrings that must not appear in fixtures. Copy `blocklist.example.txt` and fill in your org-specific terms before running `sanitize`.
- `blocklist.example.txt` — committed template.

`sanitize.py` is deterministic and size-preserving:
- **Free text** (summary, description, comments, ADF text nodes, summary cells in `acli` tables) is replaced with lorem ipsum of the same character count, so byte and token totals stay honest.
- **Structural fields** — URLs, UUIDs, account IDs, numeric IDs (issue/project/avatar), issue keys, emails, display names, time zones, custom-field values — get stable synthetic placeholders.
- **Blocklist substrings** are scrubbed last as a belt-and-suspenders layer.

`verify.sh` runs `rg` against every fixture file and fails the build if any blocklist term appears. Both `sanitize` and `verify` refuse to run without a local `blocklist.txt`.

## Reproducing

```bash
# one-time: copy and customise the blocklist
cp benchmark/blocklist.example.txt benchmark/blocklist.txt
# edit benchmark/blocklist.txt to list your company, project keys, names, etc.

# read tasks (capture from your Jira, sanitize, measure):
bash benchmark/bench.sh capture-skill small-issue <YOUR-ISSUE-KEY>
# (MCP capture: call mcp__..._getJiraIssue from a Claude session,
#  save result to benchmark/capture/mcp-small-issue.json)
bash benchmark/bench.sh sanitize small-issue
bash benchmark/bench.sh verify
bash benchmark/bench.sh measure small-issue

# same flow for barebones (pick an issue with empty description):
bash benchmark/bench.sh capture-skill barebones <EMPTY-ISSUE-KEY>
bash benchmark/bench.sh sanitize barebones
bash benchmark/bench.sh measure barebones

# same flow for recent-assigned:
bash benchmark/bench.sh capture-skill recent-assigned
# (MCP capture: searchJiraIssuesUsingJql with maxResults: 5)
bash benchmark/bench.sh sanitize recent-assigned
bash benchmark/bench.sh measure recent-assigned

# same for the projected variant (both arms request minimal fields):
bash benchmark/bench.sh capture-skill recent-assigned-projected
# (MCP capture: searchJiraIssuesUsingJql with fields=["summary","status","issuetype"])
bash benchmark/bench.sh sanitize recent-assigned-projected
bash benchmark/bench.sh measure recent-assigned-projected

# write tasks (pure synthesis, no Jira side effects):
bash benchmark/bench.sh synthesize-create create-short
bash benchmark/bench.sh synthesize-create create-rich
bash benchmark/bench.sh measure-create create-short
bash benchmark/bench.sh measure-create create-rich

# fixed overhead:
bash benchmark/bench.sh measure-overhead

# end-to-end agent loop (scripted sum; reads from tasks/ship-ticket.json):
bash benchmark/bench.sh measure-loop ship-ticket
```

## Layout

```
benchmark/
├── README.md              # user-facing: numbers + pitch
├── METHODOLOGY.md         # this file
├── bench.sh               # task orchestrator
├── sanitize.py            # raw capture → sanitized fixture
├── verify.sh              # ripgrep blocklist against fixtures/
├── measure.py             # 2-arm bytes + approx tokens
├── measure_create.py      # 3-arm create benchmark
├── measure_overhead.py    # skill context vs MCP schemas
├── synthesize_create.py   # input-only creates (mdadf → ADF)
├── blocklist.example.txt  # committed template
├── tasks/                 # per-task specs + markdown bodies
├── capture/               # gitignored — real data
└── fixtures/              # committed — sanitized / synthetic
```

## Limitations

- Token counts are approximate (chars / 4). Wire `count_tokens` for exactness — ratios will shift by a few percent, not materially.
- Full agent-loop cost (reasoning + multi-turn + final answer) not yet measured; the gap there is expected to be smaller than the payload gap because both arms produce similar final answers.
- Output tokens on read tasks not measured. Since the MCP arm has more to digest, the model sometimes writes longer summaries, so the gap on totals is probably slightly larger than what's shown.
- Daily-workload projection assumes 1 session + 10 views + 5 JQL searches + 3 rich creates per workday. Scale linearly for your own usage patterns.
