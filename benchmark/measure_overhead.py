#!/usr/bin/env python3
"""Measure the fixed per-session overhead of the skill vs the
Atlassian MCP server — the tokens every agent pays just to have
the capability available, before doing any work.

Skill arm:
  - jira/SKILL.md — always in context for sessions that use the skill.
  - jira/references/*.md — loaded on-demand via progressive disclosure,
    so reported separately as an upper bound.

MCP arm:
  - fixtures/mcp-tool-schemas.json — aggregated JSON-Schema for every
    tool the Atlassian MCP server exposes. All tools are loaded when
    the server is configured; the model sees each one's definition.

We also split the MCP list into a Jira-focused subset (Jira tools plus
shared helpers) for a fairer apples-to-apples with the Jira-only skill.

Usage:
  python3 measure_overhead.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Tools in the Atlassian MCP server that a Jira-only workflow would
# plausibly rely on. Confluence-only tools are excluded.
JIRA_FOCUS_SUBSET = {
    "mcp__claude_ai_Atlassian__addCommentToJiraIssue",
    "mcp__claude_ai_Atlassian__addWorklogToJiraIssue",
    "mcp__claude_ai_Atlassian__atlassianUserInfo",
    "mcp__claude_ai_Atlassian__createIssueLink",
    "mcp__claude_ai_Atlassian__createJiraIssue",
    "mcp__claude_ai_Atlassian__editJiraIssue",
    "mcp__claude_ai_Atlassian__fetch",
    "mcp__claude_ai_Atlassian__getAccessibleAtlassianResources",
    "mcp__claude_ai_Atlassian__getIssueLinkTypes",
    "mcp__claude_ai_Atlassian__getJiraIssue",
    "mcp__claude_ai_Atlassian__getJiraIssueRemoteIssueLinks",
    "mcp__claude_ai_Atlassian__getJiraIssueTypeMetaWithFields",
    "mcp__claude_ai_Atlassian__getJiraProjectIssueTypesMetadata",
    "mcp__claude_ai_Atlassian__getTransitionsForJiraIssue",
    "mcp__claude_ai_Atlassian__getVisibleJiraProjects",
    "mcp__claude_ai_Atlassian__lookupJiraAccountId",
    "mcp__claude_ai_Atlassian__search",
    "mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql",
    "mcp__claude_ai_Atlassian__transitionJiraIssue",
}


def approx_tokens(s: str) -> int:
    return max(1, round(len(s) / 4))


def measure_text(path: Path, label: str) -> dict:
    text = path.read_text()
    return {
        "label": label,
        "bytes": path.stat().st_size,
        "chars": len(text),
        "tokens_approx": approx_tokens(text),
    }


def measure_schemas(schemas_path: Path, label: str, subset_names: set[str] | None = None) -> dict:
    tools = json.loads(schemas_path.read_text())
    if subset_names is not None:
        tools = [t for t in tools if t["name"] in subset_names]
    serialized = json.dumps(tools, separators=(",", ":"))
    return {
        "label": label,
        "count": len(tools),
        "bytes": len(serialized.encode("utf-8")),
        "chars": len(serialized),
        "tokens_approx": approx_tokens(serialized),
    }


def main() -> int:
    here = Path(__file__).parent
    repo = here.parent

    skill_md = repo / "jira" / "SKILL.md"
    refs = sorted((repo / "jira" / "references").glob("*.md"))
    mcp_fixture = here / "fixtures" / "mcp-tool-schemas.json"

    if not skill_md.exists():
        print(f"missing {skill_md}", file=sys.stderr)
        return 2
    if not mcp_fixture.exists():
        print(f"missing {mcp_fixture}", file=sys.stderr)
        return 2

    # Skill — initial (SKILL.md only) and max (SKILL.md + all refs).
    skill_initial = measure_text(skill_md, "skill (SKILL.md only)")
    refs_combined_text = "\n\n".join(p.read_text() for p in refs)
    refs_tokens = approx_tokens(refs_combined_text)
    skill_max = {
        "label": "skill (SKILL.md + all refs)",
        "bytes": skill_initial["bytes"] + sum(p.stat().st_size for p in refs),
        "chars": skill_initial["chars"] + len(refs_combined_text),
        "tokens_approx": skill_initial["tokens_approx"] + refs_tokens,
    }

    # MCP — full list and Jira-focused subset.
    mcp_full = measure_schemas(mcp_fixture, "mcp (all 31 tools)")
    mcp_jira = measure_schemas(
        mcp_fixture, "mcp (Jira subset)", subset_names=JIRA_FOCUS_SUBSET
    )

    rows = [skill_initial, skill_max, mcp_jira, mcp_full]

    print("=== fixed-overhead benchmark ===")
    print("(tokens the agent pays to have the capability loaded, pre-task)")
    print()
    print(f"{'arm':<32} {'bytes':>8} {'~tokens':>8} {'notes'}")
    print("-" * 72)
    for r in rows:
        note = ""
        if "count" in r:
            note = f"{r['count']} tools"
        print(f"{r['label']:<32} {r['bytes']:>8} {r['tokens_approx']:>8}  {note}")
    print()
    print(f"per-reference detail ({len(refs)} files):")
    for p in refs:
        txt = p.read_text()
        print(f"  {p.name:<24} {p.stat().st_size:>8} {approx_tokens(txt):>8}")
    print()

    baseline = skill_initial["tokens_approx"]
    print(f"ratios (vs skill initial = {baseline} tokens):")
    for r in rows[1:]:
        ratio = round(r["tokens_approx"] / max(1, baseline), 2)
        print(f"  {r['label']:<32} {ratio}x")
    print()
    print("Note: tokens are approximations (chars/4). See benchmark/README.md.")
    print("Note: skill references are loaded on-demand (progressive disclosure),")
    print("      so the real skill overhead sits between initial and max.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
