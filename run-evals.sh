#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash run-evals.sh                       # run all (auto-detects claude or codex)
#   bash run-evals.sh --triggers-only       # trigger evals only
#   bash run-evals.sh --tasks-only          # task evals only
#   bash run-evals.sh --task 7              # single task eval by id
#   bash run-evals.sh --trigger 5           # single trigger eval by index (0-based)
#   CLI=codex bash run-evals.sh             # force codex backend
#   CLI=claude bash run-evals.sh            # force claude backend
#   bash run-evals.sh --no-refs --task 1    # run without reference files

RUN_TASKS=true
RUN_TRIGGERS=true
SINGLE_TASK=""
SINGLE_TRIGGER=""
INCLUDE_REFS=true

# Parse flags (order-independent)
while [ $# -gt 0 ]; do
  case "$1" in
    --triggers-only) RUN_TASKS=false; shift ;;
    --tasks-only) RUN_TRIGGERS=false; shift ;;
    --task) RUN_TRIGGERS=false; SINGLE_TASK="${2:?missing eval id}"; shift 2 ;;
    --trigger) RUN_TASKS=false; SINGLE_TRIGGER="${2:?missing trigger index}"; shift 2 ;;
    --no-refs) INCLUDE_REFS=false; shift ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
done

# Auto-detect CLI backend
if [ -z "${CLI:-}" ]; then
  if command -v claude >/dev/null 2>&1; then
    CLI=claude
  elif command -v codex >/dev/null 2>&1; then
    CLI=codex
  else
    echo "Error: neither 'claude' nor 'codex' CLI found. Install one or set CLI=<path>." >&2
    exit 1
  fi
fi
echo "Using CLI: $CLI"

# Model selection per backend
case "$CLI" in
  claude|*/claude)
    MODEL_GENERATE="${MODEL_GENERATE:-sonnet}"
    MODEL_GRADE="${MODEL_GRADE:-haiku}"
    ;;
  codex|*/codex)
    # Default: use codex's default model (omit -m flag).
    # With an OpenAI API key, override for cheaper/faster runs:
    #   MODEL_GENERATE=gpt-4.1-mini MODEL_GRADE=gpt-4.1-nano bash run-evals.sh
    MODEL_GENERATE="${MODEL_GENERATE:-}"
    MODEL_GRADE="${MODEL_GRADE:-}"
    ;;
  *)
    MODEL_GENERATE="${MODEL_GENERATE:-}"
    MODEL_GRADE="${MODEL_GRADE:-}"
    ;;
esac
echo "Models: generate=$MODEL_GENERATE grade=$MODEL_GRADE"

# CLI-agnostic prompt runner
# Usage: run_prompt <model> <system_prompt> <user_prompt>
run_prompt() {
  local model="$1" system="$2" prompt="$3"
  case "$CLI" in
    claude|*/claude)
      claude -p \
        --system-prompt "$system" \
        --allowedTools "" \
        --model "$model" \
        --max-turns 1 \
        "$prompt" 2>/dev/null
      ;;
    codex|*/codex)
      local tmpout codex_args
      tmpout=$(mktemp)
      codex_args=(exec --sandbox read-only -o "$tmpout")
      [ -n "$model" ] && codex_args+=(-m "$model")
      echo "$system" | codex "${codex_args[@]}" "$prompt" >/dev/null 2>&1 || true
      cat "$tmpout"
      rm -f "$tmpout"
      ;;
    *)
      echo "Error: unsupported CLI '$CLI'" >&2
      return 1
      ;;
  esac
}

SKILL_FILE="jira/SKILL.md"
EVALS_FILE="jira/evals/evals.json"
TRIGGERS_FILE="jira/evals/trigger-evals.json"
OUT_DIR="jira-workspace/eval-run-1"
RESULTS_FILE="$OUT_DIR/results.json"

mkdir -p "$OUT_DIR"

SKILL_CONTENT=$(<"$SKILL_FILE")

# Load reference files if they exist and --no-refs was not passed
REFS_CONTENT=""
REFS_DIR="jira/references"
if [ "$INCLUDE_REFS" = true ] && [ -d "$REFS_DIR" ]; then
  for ref_file in "$REFS_DIR"/*.md; do
    [ -f "$ref_file" ] || continue
    REFS_CONTENT+="
<reference path=\"${ref_file#jira/}\">
$(<"$ref_file")
</reference>
"
  done
fi

SYSTEM_PROMPT_BASE="You are evaluating a Jira skill for Claude Code. The skill instructs an AI agent how to manage Jira work items using acli and mdadf.

Here is the full SKILL.md content the agent would receive:

<skill>
$SKILL_CONTENT
</skill>
${REFS_CONTENT:+
The skill also has these reference files available. Use them when SKILL.md tells you to:
$REFS_CONTENT}
You are role-playing as the agent that has loaded this skill. When given a user prompt, respond EXACTLY as the agent would: produce the acli commands you would run, explain your reasoning, and follow all rules in the skill. Do NOT actually execute commands. Do NOT use any MCP tools. Just show what you WOULD do."

DEFAULT_ENVIRONMENT="For this eval, assume the following environment:
- The workspace .jira-skill.json contains: {\"defaultProject\": \"MYPROJECT\"}
- The project key MYPROJECT is valid and resolved.
- When the skill says to fetch current state (e.g. view before edit), show the view command you would run, then proceed with the mutation. Do not wait for confirmation — this is a dry run."

SYSTEM_PROMPT_FOOTER="
IMPORTANT: You must follow every instruction in the skill including Safety Rules, Operating Constraints, and Execution Steps."

echo '{"task_evals":[],"trigger_evals":[]}' > "$RESULTS_FILE"

if [ "$RUN_TASKS" = true ]; then
echo "=== RUNNING TASK-LEVEL EVALS ==="
EVAL_COUNT=$(jq '.evals | length' "$EVALS_FILE")

for i in $(seq 0 $((EVAL_COUNT - 1))); do
  EVAL_ID=$(jq -r ".evals[$i].id" "$EVALS_FILE")
  [ -n "$SINGLE_TASK" ] && [ "$EVAL_ID" != "$SINGLE_TASK" ] && continue
  PROMPT=$(jq -r ".evals[$i].prompt" "$EVALS_FILE")
  EXPECTATIONS=$(jq -r ".evals[$i].expectations[] | \"- \" + ." "$EVALS_FILE")

  # Use per-eval environment override if present, otherwise default
  EVAL_ENV=$(jq -r ".evals[$i].environment // empty" "$EVALS_FILE")
  if [ -n "$EVAL_ENV" ]; then
    EVAL_SYSTEM_PROMPT="$SYSTEM_PROMPT_BASE

For this eval, assume the following environment:
$EVAL_ENV
$SYSTEM_PROMPT_FOOTER"
  else
    EVAL_SYSTEM_PROMPT="$SYSTEM_PROMPT_BASE

$DEFAULT_ENVIRONMENT
$SYSTEM_PROMPT_FOOTER"
  fi

  echo ""
  echo "--- Eval #$EVAL_ID: ${PROMPT:0:60}..."

  RESPONSE=$(run_prompt "$MODEL_GENERATE" "$EVAL_SYSTEM_PROMPT" "$PROMPT") || { echo "  [ERROR] generate failed"; continue; }

  echo "$RESPONSE" > "$OUT_DIR/eval-${EVAL_ID}-response.txt"

  # Grade the response against expectations
  GRADE_PROMPT="Grade this AI agent response against the expected behaviors. For each expectation, answer PASS or FAIL with a brief reason.

Response to grade:
<response>
$RESPONSE
</response>

Expectations:
$EXPECTATIONS

Output format — one line per expectation, nothing else:
PASS|FAIL: <expectation summary> — <reason>"

  GRADE=$(run_prompt "$MODEL_GRADE" "" "$GRADE_PROMPT") || { echo "  [ERROR] grading failed"; continue; }

  echo "$GRADE" > "$OUT_DIR/eval-${EVAL_ID}-grade.txt"

  PASS_COUNT=$(echo "$GRADE" | grep -c "^PASS" || true)
  FAIL_COUNT=$(echo "$GRADE" | grep -c "^FAIL" || true)
  TOTAL=$((PASS_COUNT + FAIL_COUNT))

  if [ "$FAIL_COUNT" -eq 0 ] && [ "$TOTAL" -gt 0 ]; then
    echo "  PASS ($PASS_COUNT/$TOTAL expectations)"
  else
    echo "  PARTIAL ($PASS_COUNT/$TOTAL expectations)"
    echo "$GRADE" | grep "^FAIL" | sed 's/^/    /'
  fi
done
fi

if [ "$RUN_TRIGGERS" = true ]; then
echo ""
echo "=== RUNNING TRIGGER-LEVEL EVALS ==="
TRIGGER_COUNT=$(jq 'length' "$TRIGGERS_FILE")

TRIGGER_PASS=0
TRIGGER_FAIL=0

for i in $(seq 0 $((TRIGGER_COUNT - 1))); do
  [ -n "$SINGLE_TRIGGER" ] && [ "$i" != "$SINGLE_TRIGGER" ] && continue
  QUERY=$(jq -r ".[$i].query" "$TRIGGERS_FILE")
  EXPECTED=$(jq -r ".[$i].should_trigger" "$TRIGGERS_FILE")

  TRIGGER_PROMPT="Given this skill description (from SKILL.md frontmatter):

description: $(head -4 "$SKILL_FILE" | grep 'description:' | sed 's/^description: //')

Should this skill activate for the following user query? Answer ONLY 'yes' or 'no'.

Query: \"$QUERY\""

  ANSWER=$(run_prompt "$MODEL_GRADE" "" "$TRIGGER_PROMPT") || { echo "  [ERROR] trigger eval failed for: ${QUERY:0:50}"; continue; }

  ANSWER_LOWER=$(echo "$ANSWER" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')

  if [ "$EXPECTED" = "true" ]; then
    EXPECTED_ANSWER="yes"
  else
    EXPECTED_ANSWER="no"
  fi

  if [[ "$ANSWER_LOWER" == *"$EXPECTED_ANSWER"* ]]; then
    TRIGGER_PASS=$((TRIGGER_PASS + 1))
    STATUS="PASS"
  else
    TRIGGER_FAIL=$((TRIGGER_FAIL + 1))
    STATUS="FAIL (got: $ANSWER_LOWER, expected: $EXPECTED_ANSWER)"
  fi

  echo "  [$STATUS] ${QUERY:0:70}..."
done

echo ""
echo "=== SUMMARY ==="
echo "Trigger evals: $TRIGGER_PASS pass, $TRIGGER_FAIL fail out of $TRIGGER_COUNT"
fi

echo "Full results in: $OUT_DIR/"
