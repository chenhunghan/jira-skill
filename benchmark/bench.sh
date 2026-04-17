#!/usr/bin/env bash
# bench.sh - orchestrator for the token-efficiency benchmark
#
# Commands:
#   capture-skill <KEY>   run acli, save to capture/skill-<KEY>.txt (gitignored)
#   sanitize <KEY>        capture/ → fixtures/ (committable)
#   verify                grep fixtures/ against blocklist.txt
#   measure               compute bytes + approx tokens for current fixtures
#   all <KEY>             capture-skill → sanitize → verify → measure
#                         (MCP capture is a manual prerequisite — see README)

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

die() { echo "error: $*" >&2; exit 2; }

cmd="${1:-}"; shift || true

case "$cmd" in
  capture-skill)
    KEY="${1:-}"; [[ -n "$KEY" ]] || die "usage: bench.sh capture-skill <KEY>"
    command -v acli >/dev/null || die "acli not installed"
    mkdir -p "$HERE/capture"
    out="$HERE/capture/skill-$KEY.txt"
    echo "→ acli jira workitem view $KEY"
    acli jira workitem view "$KEY" > "$out" 2>&1
    echo "wrote $out ($(wc -c < "$out" | tr -d ' ') bytes)"
    ;;

  sanitize)
    KEY="${1:-}"; [[ -n "$KEY" ]] || die "usage: bench.sh sanitize <KEY>"
    command -v python3 >/dev/null || die "python3 required"
    mkdir -p "$HERE/fixtures"
    bl="$HERE/blocklist.txt"

    if [[ ! -f "$bl" ]]; then
      die "missing $bl — copy blocklist.example.txt → blocklist.txt and add your sensitive terms before sanitizing"
    fi

    skill_in="$HERE/capture/skill-$KEY.txt"
    mcp_in="$HERE/capture/mcp-$KEY.json"
    [[ -f "$skill_in" ]] || die "missing $skill_in (run: bench.sh capture-skill $KEY)"
    [[ -f "$mcp_in" ]] || die "missing $mcp_in (see README for manual MCP capture)"

    python3 "$HERE/sanitize.py" --blocklist "$bl" \
      "$skill_in" "$HERE/fixtures/skill-small-issue.txt"
    python3 "$HERE/sanitize.py" --blocklist "$bl" \
      "$mcp_in" "$HERE/fixtures/mcp-small-issue.json"
    ;;

  verify)
    bash "$HERE/verify.sh"
    ;;

  measure)
    command -v python3 >/dev/null || die "python3 required"
    skill="$HERE/fixtures/skill-small-issue.txt"
    mcp="$HERE/fixtures/mcp-small-issue.json"
    [[ -f "$skill" && -f "$mcp" ]] || die "fixtures missing; run: bench.sh sanitize <KEY>"
    python3 "$HERE/measure.py" "$skill" "$mcp"
    ;;

  all)
    KEY="${1:-}"; [[ -n "$KEY" ]] || die "usage: bench.sh all <KEY>"
    "$0" capture-skill "$KEY"
    "$0" sanitize "$KEY"
    "$0" verify
    "$0" measure
    ;;

  *)
    cat <<EOF
usage: bench.sh <command>

commands:
  capture-skill <KEY>   run acli, save to capture/ (gitignored)
  sanitize <KEY>        capture/ → fixtures/ (committable)
  verify                check fixtures/ against blocklist.txt
  measure               compute bytes + approx tokens for fixtures/
  all <KEY>             run the full pipeline
                        (requires capture/mcp-<KEY>.json to exist already)
EOF
    exit 2
    ;;
esac
