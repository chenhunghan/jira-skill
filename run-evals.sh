#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="jira/SKILL.md"
EVALS_FILE="jira/evals/evals.json"
TRIGGERS_FILE="jira/evals/trigger-evals.json"
OUT_DIR="jira-workspace/eval-run-1"
RESULTS_FILE="$OUT_DIR/results.json"

mkdir -p "$OUT_DIR"

SKILL_CONTENT=$(<"$SKILL_FILE")

# Load reference files if they exist
REFS_CONTENT=""
REFS_DIR="jira/references"
if [ -d "$REFS_DIR" ]; then
  for ref_file in "$REFS_DIR"/*.md; do
    [ -f "$ref_file" ] || continue
    REFS_CONTENT+="
<reference path=\"${ref_file#jira/}\">
$(<"$ref_file")
</reference>
"
  done
fi

SYSTEM_PROMPT="You are evaluating a Jira skill for Claude Code. The skill instructs an AI agent how to manage Jira work items using acli and mdadf.

Here is the full SKILL.md content the agent would receive:

<skill>
$SKILL_CONTENT
</skill>
${REFS_CONTENT:+
The skill also has these reference files available. Use them when SKILL.md tells you to:
$REFS_CONTENT}
You are role-playing as the agent that has loaded this skill. When given a user prompt, respond EXACTLY as the agent would: produce the acli commands you would run, explain your reasoning, and follow all rules in the skill. Do NOT actually execute commands. Do NOT use any MCP tools. Just show what you WOULD do.

For this eval, assume the following environment:
- The workspace .jira-skill.json contains: {\"defaultProject\": \"MYPROJECT\"}
- The project key MYPROJECT is valid and resolved.
- When the skill says to fetch current state (e.g. view before edit), show the view command you would run, then proceed with the mutation. Do not wait for confirmation — this is a dry run.

IMPORTANT: You must follow every instruction in the skill including Safety Rules, Operating Constraints, and Execution Steps."

echo '{"task_evals":[],"trigger_evals":[]}' > "$RESULTS_FILE"

echo "=== RUNNING TASK-LEVEL EVALS ==="
EVAL_COUNT=$(python3 -c "import json; print(len(json.load(open('$EVALS_FILE'))['evals']))")

for i in $(seq 0 $((EVAL_COUNT - 1))); do
  EVAL_ID=$(python3 -c "import json; print(json.load(open('$EVALS_FILE'))['evals'][$i]['id'])")
  PROMPT=$(python3 -c "import json; print(json.load(open('$EVALS_FILE'))['evals'][$i]['prompt'])")
  EXPECTATIONS=$(python3 -c "import json; exps=json.load(open('$EVALS_FILE'))['evals'][$i]['expectations']; print('\n'.join(f'- {e}' for e in exps))")

  echo ""
  echo "--- Eval #$EVAL_ID: ${PROMPT:0:60}..."

  RESPONSE=$(claude -p \
    --system-prompt "$SYSTEM_PROMPT" \
    --allowedTools "" \
    --model sonnet \
    --max-turns 1 \
    "$PROMPT" 2>/dev/null) || { echo "  [ERROR] claude CLI failed"; continue; }

  echo "$RESPONSE" > "$OUT_DIR/eval-${EVAL_ID}-response.txt"

  # Now grade the response against expectations
  GRADE_PROMPT="Grade this AI agent response against the expected behaviors. For each expectation, answer PASS or FAIL with a brief reason.

Response to grade:
<response>
$RESPONSE
</response>

Expectations:
$EXPECTATIONS

Output format — one line per expectation, nothing else:
PASS|FAIL: <expectation summary> — <reason>"

  GRADE=$(claude -p \
    --allowedTools "" \
    --model haiku \
    --max-turns 1 \
    "$GRADE_PROMPT" 2>/dev/null) || { echo "  [ERROR] grading failed"; continue; }

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

echo ""
echo "=== RUNNING TRIGGER-LEVEL EVALS ==="
TRIGGER_COUNT=$(python3 -c "import json; print(len(json.load(open('$TRIGGERS_FILE'))))")

TRIGGER_PASS=0
TRIGGER_FAIL=0

for i in $(seq 0 $((TRIGGER_COUNT - 1))); do
  QUERY=$(python3 -c "import json; print(json.load(open('$TRIGGERS_FILE'))[$i]['query'])")
  EXPECTED=$(python3 -c "import json; print(json.load(open('$TRIGGERS_FILE'))[$i]['should_trigger'])")

  TRIGGER_PROMPT="Given this skill description (from SKILL.md frontmatter):

description: $(head -4 "$SKILL_FILE" | grep 'description:' | sed 's/^description: //')

Should this skill activate for the following user query? Answer ONLY 'yes' or 'no'.

Query: \"$QUERY\""

  ANSWER=$(claude -p \
    --allowedTools "" \
    --model haiku \
    --max-turns 1 \
    "$TRIGGER_PROMPT" 2>/dev/null) || { echo "  [ERROR] trigger eval failed for: ${QUERY:0:50}"; continue; }

  ANSWER_LOWER=$(echo "$ANSWER" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')

  if [ "$EXPECTED" = "True" ] || [ "$EXPECTED" = "true" ]; then
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
echo "Full results in: $OUT_DIR/"
