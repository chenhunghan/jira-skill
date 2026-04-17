#!/usr/bin/env python3
"""Measure bytes and approximate Claude tokens for fixture files.

Approximation: chars / 4. Consistent across both arms, so ratios are
meaningful. Exact counts require wiring `anthropic.count_tokens` (needs
ANTHROPIC_API_KEY) — left as a follow-up.

Usage:
  python3 measure.py <skill-fixture> <mcp-fixture> [--task NAME] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def approx_tokens(s: str) -> int:
    return max(1, round(len(s) / 4))


def measure(path: str) -> dict:
    p = Path(path)
    text = p.read_text()
    return {
        "path": str(p),
        "bytes": p.stat().st_size,
        "chars": len(text),
        "tokens_approx": approx_tokens(text),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill")
    ap.add_argument("mcp")
    ap.add_argument("--task", default=None, help="label for the report header")
    ap.add_argument("--json", action="store_true", help="print JSON only")
    args = ap.parse_args()

    skill = measure(args.skill)
    mcp = measure(args.mcp)

    ratios = {
        "bytes_mcp_over_skill": round(mcp["bytes"] / max(1, skill["bytes"]), 2),
        "tokens_mcp_over_skill": round(
            mcp["tokens_approx"] / max(1, skill["tokens_approx"]), 2
        ),
    }

    result = {"skill": skill, "mcp": mcp, "ratios": ratios}

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    label = args.task or "(unnamed task)"
    print(f"=== token-efficiency benchmark: {label} ===")
    print(f"{'arm':<8} {'bytes':>8} {'chars':>8} {'~tokens':>8}")
    print(f"{'skill':<8} {skill['bytes']:>8} {skill['chars']:>8} {skill['tokens_approx']:>8}")
    print(f"{'mcp':<8} {mcp['bytes']:>8} {mcp['chars']:>8} {mcp['tokens_approx']:>8}")
    print()
    print(f"MCP / skill ratios:")
    print(f"  bytes : {ratios['bytes_mcp_over_skill']}x")
    print(f"  tokens: {ratios['tokens_mcp_over_skill']}x")
    print()
    print("Note: tokens are approximations (chars/4). See benchmark/README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
