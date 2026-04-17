#!/usr/bin/env python3
"""Synthesize what each arm would EMIT to create a Jira issue.

Input-only benchmark: reads a task spec + its markdown body, produces
three fixture files showing what the agent would have to emit for:
  - skill arm: bash `acli jira workitem create ... --description-file
    <(mdadf --compact <<'MD' ... MD)` with markdown inlined verbatim.
  - mcp-adf arm: `createJiraIssue` tool call JSON with `description`
    as a stringified ADF document (default contentFormat for MCP).
  - mcp-md arm: `createJiraIssue` tool call JSON with `description` as
    markdown plus `contentFormat: "markdown"`.

For ADF generation, invokes `mdadf --compact` in a subprocess.

Usage:
  python3 synthesize_create.py --task create-short
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def run_mdadf(md: str) -> str:
    result = subprocess.run(
        ["mdadf", "--compact"],
        input=md,
        text=True,
        check=True,
        capture_output=True,
    )
    return result.stdout.rstrip("\n")


def render_skill(md: str, summary: str, project: str, issue_type: str) -> str:
    return (
        "acli jira workitem create \\\n"
        f"  --summary {shlex.quote(summary)} \\\n"
        f"  --project {shlex.quote(project)} \\\n"
        f"  --type {shlex.quote(issue_type)} \\\n"
        f"  --description-file <(mdadf --compact <<'MD'\n"
        f"{md.rstrip()}\n"
        "MD\n"
        ")\n"
    )


def _base_mcp_args(summary: str, project: str, issue_type: str, cloud_id: str) -> dict:
    return {
        "cloudId": cloud_id,
        "projectKey": project,
        "issueTypeName": issue_type,
        "summary": summary,
    }


def render_mcp_adf(md: str, summary: str, project: str, issue_type: str, cloud_id: str) -> str:
    adf_json = run_mdadf(md)
    payload = _base_mcp_args(summary, project, issue_type, cloud_id)
    # Schema declares description as `type: string`; in ADF mode the
    # string is the serialized ADF document. json.dumps escapes the
    # inner quotes, which is part of the agent's emitted cost.
    payload["description"] = adf_json
    return json.dumps(payload, separators=(",", ":"))


def render_mcp_markdown(md: str, summary: str, project: str, issue_type: str, cloud_id: str) -> str:
    payload = _base_mcp_args(summary, project, issue_type, cloud_id)
    payload["description"] = md.rstrip()
    payload["contentFormat"] = "markdown"
    return json.dumps(payload, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Task id (e.g. create-short)")
    args = ap.parse_args()

    here = Path(__file__).parent
    task_path = here / "tasks" / f"{args.task}.json"
    task = json.loads(task_path.read_text())
    md_path = task_path.parent / task["markdownFile"]
    md = md_path.read_text()
    fields = task["fields"]
    cloud_id = task["cloudId"]

    summary = fields["summary"]
    project = fields["projectKey"]
    issue_type = fields["issueTypeName"]

    fixtures_dir = here / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    skill_path = fixtures_dir / f"skill-{args.task}.txt"
    mcp_adf_path = fixtures_dir / f"mcp-adf-{args.task}.json"
    mcp_md_path = fixtures_dir / f"mcp-md-{args.task}.json"

    skill_path.write_text(render_skill(md, summary, project, issue_type))
    mcp_adf_path.write_text(
        render_mcp_adf(md, summary, project, issue_type, cloud_id) + "\n"
    )
    mcp_md_path.write_text(
        render_mcp_markdown(md, summary, project, issue_type, cloud_id) + "\n"
    )

    print(
        f"synthesized {args.task}: "
        f"skill={skill_path.stat().st_size}c, "
        f"mcp-adf={mcp_adf_path.stat().st_size}c, "
        f"mcp-md={mcp_md_path.stat().st_size}c",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
