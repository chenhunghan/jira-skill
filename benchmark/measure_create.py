#!/usr/bin/env python3
"""Measure bytes + approx tokens for a 3-arm create benchmark.

Prints a table with skill / mcp-adf / mcp-md. Ratios are computed
relative to skill (the baseline).

Usage:
  python3 measure_create.py --task create-short \\
    fixtures/skill-create-short.txt \\
    fixtures/mcp-adf-create-short.json \\
    fixtures/mcp-md-create-short.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def approx_tokens(s: str) -> int:
    return max(1, round(len(s) / 4))


def measure(path: str, label: str) -> dict:
    p = Path(path)
    t = p.read_text()
    return {
        "label": label,
        "path": str(p),
        "bytes": p.stat().st_size,
        "chars": len(t),
        "tokens_approx": approx_tokens(t),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill")
    ap.add_argument("mcp_adf")
    ap.add_argument("mcp_md")
    ap.add_argument("--task", default=None)
    args = ap.parse_args()

    rows = [
        measure(args.skill, "skill"),
        measure(args.mcp_adf, "mcp-adf"),
        measure(args.mcp_md, "mcp-md"),
    ]

    label = args.task or "(create, input-only)"
    print(f"=== token-efficiency benchmark: {label} (input-only) ===")
    print(f"{'arm':<10} {'bytes':>8} {'chars':>8} {'~tokens':>8}")
    for r in rows:
        print(f"{r['label']:<10} {r['bytes']:>8} {r['chars']:>8} {r['tokens_approx']:>8}")
    print()
    baseline = rows[0]["tokens_approx"]
    for r in rows[1:]:
        ratio = round(r["tokens_approx"] / max(1, baseline), 2)
        print(f"  {r['label']} / skill: {ratio}x tokens")
    print()
    print("Note: tokens are approximations (chars/4). See benchmark/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
