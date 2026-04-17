# Token-efficiency benchmark: jira-skill vs Atlassian MCP

Compares how many tokens each approach costs to satisfy the same read-heavy Jira task.

## Arms

- **skill** — Claude + this repo's `jira` skill, driving `acli` through Bash. Output is table-like text.
- **mcp** — Claude + Atlassian's MCP server, calling `getJiraIssue` / `searchJiraIssuesUsingJql` directly. Output is JSON with full ADF.

## What's measured

Per task, for each arm: tool-result bytes, character count, approximate Claude tokens (chars ÷ 4). Approximate because no `ANTHROPIC_API_KEY` is wired for exact `count_tokens` calls yet — consistent approximation across arms keeps the **ratio** meaningful.

Fixed overhead (SKILL.md + references tokens vs MCP tool-schema tokens) is **not** measured in v1; tracked as follow-up.

## Data-handling rules

Captured payloads contain real company data — issue keys, project names, account IDs, display names. They must never land in git.

- `capture/` — raw captures, **gitignored**.
- `fixtures/` — sanitized, size-preserving, committed.
- `blocklist.txt` — **gitignored**; substrings that must not appear in fixtures; checked by `verify.sh`. Copy `blocklist.example.txt` → `blocklist.txt` and fill in your company/PII terms before running sanitize/verify.

`sanitize.py` is deterministic and size-preserving: free-text fields (summary, ADF text nodes, comment bodies) are replaced with lorem ipsum of the same character length, so byte and approximate-token counts stay honest. Structural fields (URLs, UUIDs, account IDs, issue keys, emails, display names) are swapped with stable placeholders.

## Workflow

```bash
# 1. capture the skill arm (runs acli against real Jira)
bash benchmark/bench.sh capture-skill BENCH-1

# 2. capture the MCP arm — done from a Claude agent session that has
#    the Atlassian MCP server configured. Save the raw tool result to
#    benchmark/capture/mcp-<KEY>.json. See docs/mcp-capture.md.

# 3. sanitize raw → fixtures
bash benchmark/bench.sh sanitize BENCH-1

# 4. verify no forbidden substrings leaked
bash benchmark/bench.sh verify

# 5. measure fixtures; writes metrics.json and prints summary
bash benchmark/bench.sh measure BENCH-1

# or do everything (2 must be done manually first):
bash benchmark/bench.sh all BENCH-1
```

## Layout

```
benchmark/
├── README.md                # this file
├── bench.sh                 # orchestrator
├── sanitize.py              # raw → fixture
├── measure.py               # fixture → metrics
├── verify.sh                # grep blocklist against fixtures
├── blocklist.txt            # forbidden substrings (one per line)
├── tasks/
│   └── view-small-issue.json
├── capture/                 # gitignored — real data
└── fixtures/                # committed — sanitized
```

## Known limitations (v1)

- Token counts are approximate. Wire `ANTHROPIC_API_KEY` + `count_tokens` for exactness.
- Fixed overhead (skill context vs MCP tool schemas) not yet measured.
- Only the payload arriving from the tool is measured — full agent-loop token cost (reasoning, multi-turn, final answer) would require running both arms through an LLM harness like `run-evals.sh`. Planned for v2.

## Tasks

- `small-issue` — view one issue via `acli jira workitem view <KEY>` vs MCP `getJiraIssue`.
- `recent-assigned` — list 5 issues via `acli jira workitem search --jql ... --limit 5` vs MCP `searchJiraIssuesUsingJql` with `maxResults: 5`.

Both arms use natural defaults (no `--fields` projection). A projected variant can be added later to isolate what projection buys you.
