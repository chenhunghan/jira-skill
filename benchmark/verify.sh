#!/usr/bin/env bash
# verify.sh - fail if any forbidden substring appears in fixtures/
#
# Usage: bash verify.sh
# Env overrides: BLOCKLIST (default benchmark/blocklist.txt),
#                FIXTURES  (default benchmark/fixtures)

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BLOCKLIST="${BLOCKLIST:-$HERE/blocklist.txt}"
FIXTURES="${FIXTURES:-$HERE/fixtures}"

if [[ ! -d "$FIXTURES" ]]; then
  echo "verify: no $FIXTURES directory — nothing to check"
  exit 0
fi

if [[ ! -f "$BLOCKLIST" ]]; then
  echo "verify: blocklist $BLOCKLIST missing — copy blocklist.example.txt and customize" >&2
  exit 2
fi

if ! command -v rg >/dev/null 2>&1; then
  echo "verify: ripgrep (rg) required" >&2
  exit 2
fi

# Strip comments/empty lines from blocklist into a temp file.
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
grep -v '^\s*#' "$BLOCKLIST" | grep -v '^\s*$' > "$tmp"

entries=$(wc -l < "$tmp" | tr -d ' ')
if [[ "$entries" -eq 0 ]]; then
  echo "verify: $BLOCKLIST has no active entries — add terms before verifying" >&2
  exit 2
fi

# rg exits 1 when no matches — the "clean" case. Capture output and
# check emptiness explicitly rather than relying on exit code.
hits=$(rg -i -n -f "$tmp" "$FIXTURES" 2>/dev/null || true)

if [[ -n "$hits" ]]; then
  echo "LEAK DETECTED in $FIXTURES:"
  echo "$hits"
  exit 1
fi

echo "verify: $FIXTURES is clean against $entries blocklist entries"
