#!/usr/bin/env bash
# bench.sh - orchestrator for the token-efficiency benchmark
#
# Task-parameterized. Each task id matches tasks/<id>.json, and
# all capture/fixture filenames use the same slug.
#
# Commands:
#   capture-skill <TASK> [extra-args]  run the skill arm, save to capture/
#   sanitize <TASK>                    capture/<TASK>.* → fixtures/<TASK>.*
#   verify                             grep fixtures/ against blocklist.txt
#   measure <TASK>                     print bytes + approx tokens
#   synthesize-create <TASK>           input-only: generate fixtures from tasks/*.md
#   measure-create <TASK>              print 3-arm table (skill / mcp-adf / mcp-md)
#
# Tasks:
#   small-issue <KEY>     view a single issue (KEY required)
#   recent-assigned       list 5 most recent issues assigned to current user
#   create-short          input-only: create with short markdown body
#   create-rich           input-only: create with rich markdown body

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

die() { echo "error: $*" >&2; exit 2; }

# Dispatch: print the skill-arm command line for a task. Any additional
# positional args are task-specific (e.g. an issue key for small-issue).
skill_command() {
  local task="$1"; shift
  case "$task" in
    small-issue)
      local key="${1:-}"
      [[ -n "$key" ]] || die "task 'small-issue' needs an issue KEY"
      printf 'acli jira workitem view %q' "$key"
      ;;
    recent-assigned)
      printf "acli jira workitem search --jql %q --limit 5" \
        "assignee = currentUser() ORDER BY updated DESC"
      ;;
    *)
      die "unknown task: $task (small-issue|recent-assigned)"
      ;;
  esac
}

cmd="${1:-}"; shift || true

case "$cmd" in
  capture-skill)
    task="${1:-}"; [[ -n "$task" ]] || die "usage: bench.sh capture-skill <TASK> [extra-args]"
    shift
    command -v acli >/dev/null || die "acli not installed"
    mkdir -p "$HERE/capture"
    out="$HERE/capture/skill-$task.txt"
    skill_cmd="$(skill_command "$task" "$@")"
    echo "→ $skill_cmd"
    eval "$skill_cmd" > "$out" 2>&1
    echo "wrote $out ($(wc -c < "$out" | tr -d ' ') bytes)"
    ;;

  sanitize)
    task="${1:-}"; [[ -n "$task" ]] || die "usage: bench.sh sanitize <TASK>"
    command -v python3 >/dev/null || die "python3 required"
    mkdir -p "$HERE/fixtures"
    bl="$HERE/blocklist.txt"

    if [[ ! -f "$bl" ]]; then
      die "missing $bl — copy blocklist.example.txt → blocklist.txt and add your sensitive terms before sanitizing"
    fi

    skill_in="$HERE/capture/skill-$task.txt"
    mcp_in="$HERE/capture/mcp-$task.json"
    [[ -f "$skill_in" ]] || die "missing $skill_in (run: bench.sh capture-skill $task)"
    [[ -f "$mcp_in" ]] || die "missing $mcp_in (MCP capture must be done from an agent session; see README)"

    python3 "$HERE/sanitize.py" --blocklist "$bl" \
      "$skill_in" "$HERE/fixtures/skill-$task.txt"
    python3 "$HERE/sanitize.py" --blocklist "$bl" \
      "$mcp_in" "$HERE/fixtures/mcp-$task.json"
    ;;

  verify)
    bash "$HERE/verify.sh"
    ;;

  measure)
    task="${1:-}"; [[ -n "$task" ]] || die "usage: bench.sh measure <TASK>"
    command -v python3 >/dev/null || die "python3 required"
    skill="$HERE/fixtures/skill-$task.txt"
    mcp="$HERE/fixtures/mcp-$task.json"
    [[ -f "$skill" && -f "$mcp" ]] || die "fixtures missing; run: bench.sh sanitize $task"
    python3 "$HERE/measure.py" --task "$task" "$skill" "$mcp"
    ;;

  synthesize-create)
    task="${1:-}"; [[ -n "$task" ]] || die "usage: bench.sh synthesize-create <TASK>"
    command -v python3 >/dev/null || die "python3 required"
    command -v mdadf >/dev/null || die "mdadf not installed"
    mkdir -p "$HERE/fixtures"
    python3 "$HERE/synthesize_create.py" --task "$task"
    ;;

  measure-create)
    task="${1:-}"; [[ -n "$task" ]] || die "usage: bench.sh measure-create <TASK>"
    command -v python3 >/dev/null || die "python3 required"
    skill="$HERE/fixtures/skill-$task.txt"
    mcp_adf="$HERE/fixtures/mcp-adf-$task.json"
    mcp_md="$HERE/fixtures/mcp-md-$task.json"
    for f in "$skill" "$mcp_adf" "$mcp_md"; do
      [[ -f "$f" ]] || die "missing $f; run: bench.sh synthesize-create $task"
    done
    python3 "$HERE/measure_create.py" --task "$task" "$skill" "$mcp_adf" "$mcp_md"
    ;;

  measure-overhead)
    command -v python3 >/dev/null || die "python3 required"
    python3 "$HERE/measure_overhead.py"
    ;;

  *)
    cat <<EOF
usage: bench.sh <command>

commands:
  capture-skill <TASK> [args]   run the skill arm; save to capture/ (gitignored)
  sanitize <TASK>               capture/ → fixtures/ (committable)
  verify                        grep fixtures/ against blocklist.txt
  measure <TASK>                compute bytes + approx tokens (2-arm)
  synthesize-create <TASK>      input-only: generate fixtures from tasks/*.md
  measure-create <TASK>         print 3-arm table (skill / mcp-adf / mcp-md)
  measure-overhead              compare fixed per-session overhead
                                (SKILL.md + refs vs MCP tool schemas)

tasks:
  small-issue <KEY>             view a single issue (KEY required)
  recent-assigned               list 5 most recent assigned to current user
  create-short                  input-only: create issue with short markdown
  create-rich                   input-only: create issue with rich markdown
EOF
    exit 2
    ;;
esac
