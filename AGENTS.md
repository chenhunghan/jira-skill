# Contributing

## Verify changes

After editing `jira/SKILL.md`, run the eval suite to check for regressions.

### Structural check (requires `jq`)

Validate JSON and count evals:

```bash
jq -e '.evals | map(select(.id == null or .prompt == null or .expectations == null or (.expectations | length) == 0)) | if length > 0 then error("invalid evals") else empty end' jira/evals/evals.json
jq -e 'map(select(.query == null or .should_trigger == null)) | if length > 0 then error("invalid triggers") else empty end' jira/evals/trigger-evals.json
jq -r '"Task evals: \(.evals | length)"' jira/evals/evals.json
jq -r '"Trigger evals: \(length)"' jira/evals/trigger-evals.json
```

### Behavioral eval (requires `claude` CLI)

`run-evals.sh` sends each eval prompt + the full SKILL.md + all `references/*.md` files to an LLM and grades the response against expectations. It uses `claude -p` (non-interactive print mode) and writes results to `jira-workspace/eval-run-1/`.

```bash
bash run-evals.sh
```

If `claude` CLI is not available (e.g. Codex, Cursor), run the same logic manually: for each eval in `jira/evals/evals.json`, paste the SKILL.md as system context, send the `prompt`, and check the response against the `expectations` array. The expectations are plain-English assertions — no test framework needed.

### What to check

- **Task evals** (`jira/evals/evals.json`): Does the agent produce correct `acli` commands, follow safety rules, use `mdadf --compact`, and respect operating constraints?
- **Trigger evals** (`jira/evals/trigger-evals.json`): Does the skill description trigger for Jira work (`should_trigger: true`) and stay silent for GitHub PRs, Confluence, auth setup, etc. (`should_trigger: false`)?

### Adding evals

When adding a feature or safety rule to SKILL.md, add a corresponding eval. Task evals go in `evals.json`, trigger boundary cases go in `trigger-evals.json`.

### Adding reference files

Put new reference files in `jira/references/`. Add a pointer in SKILL.md that tells the agent when to load the file (e.g. "read `references/foo.md` if the user needs X"). `run-evals.sh` auto-discovers all `references/*.md` files and includes them in the eval context.
