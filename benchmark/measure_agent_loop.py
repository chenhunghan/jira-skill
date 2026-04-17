#!/usr/bin/env python3
"""Sum an end-to-end agent-loop scenario from its step-by-step breakdown.

Reads benchmark/tasks/<scenario>.json (steps with per-step skill/mcp
token numbers — measured where available, estimated otherwise) and
prints a table + totals + derived metrics (ratio, session capacity).

Usage:
  python3 measure_agent_loop.py --task ship-ticket
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="ship-ticket")
    ap.add_argument(
        "--context-window",
        type=int,
        default=200_000,
        help="context window size for capacity calculation (default 200K)",
    )
    args = ap.parse_args()

    here = Path(__file__).parent
    task_path = here / "tasks" / f"{args.task}.json"
    task = json.loads(task_path.read_text())

    steps = task["steps"]

    print(f"=== agent-loop benchmark: {task['id']} ===")
    print()
    print(task["scenario"])
    print()
    print(f"{'#':<3} {'step':<54} {'skill':>8} {'mcp':>8}")
    print("-" * 76)

    skill_total = 0
    mcp_total = 0
    for s in steps:
        label = s["label"]
        if len(label) > 54:
            label = label[:53] + "…"
        print(f"{s['step']:<3} {label:<54} {s['skill_tokens']:>8,} {s['mcp_tokens']:>8,}")
        skill_total += s["skill_tokens"]
        mcp_total += s["mcp_tokens"]

    print("-" * 76)
    print(f"{'':<3} {'TOTAL tokens per loop':<54} {skill_total:>8,} {mcp_total:>8,}")
    print()

    ratio = round(mcp_total / max(1, skill_total), 2)
    saved_pct = round(100 * (mcp_total - skill_total) / max(1, mcp_total), 1)
    print(f"  MCP / skill   : {ratio}x tokens")
    print(f"  saved per loop: {mcp_total - skill_total:,} tokens ({saved_pct}%)")

    ctx = args.context_window
    skill_cap = ctx // max(1, skill_total)
    mcp_cap = ctx // max(1, mcp_total)
    cap_ratio = round(skill_cap / max(1, mcp_cap), 2)
    print()
    print(f"  at a {ctx:,}-token context window:")
    print(f"    skill: ~{skill_cap} complete loops per session")
    print(f"    mcp  : ~{mcp_cap} complete loops per session")
    print(f"    capacity: {cap_ratio}x more dev cycles per session")

    notes = task.get("notes") or []
    if notes:
        print()
        print("Notes:")
        for n in notes:
            print(f"  - {n}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
