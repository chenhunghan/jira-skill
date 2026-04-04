# Contributing

## Verify changes

After editing `jira/SKILL.md`, run the eval suite to check for regressions.

### Structural check (no dependencies)

Validate JSON and count evals:

```bash
python3 -c "
import json
evals = json.load(open('jira/evals/evals.json'))['evals']
triggers = json.load(open('jira/evals/trigger-evals.json'))
print(f'{len(evals)} task evals, {len(triggers)} trigger evals')
for e in evals:
    assert 'id' in e and 'prompt' in e and 'expectations' in e
for t in triggers:
    assert 'query' in t and 'should_trigger' in t
print('All valid.')
"
```

### Behavioral eval (requires `claude` CLI)

`run-evals.sh` sends each eval prompt + the full SKILL.md to an LLM and grades the response against expectations. It uses `claude -p` (non-interactive print mode) and writes results to `jira-workspace/eval-run-1/`.

```bash
bash run-evals.sh
```

If `claude` CLI is not available (e.g. Codex, Cursor), run the same logic manually: for each eval in `jira/evals/evals.json`, paste the SKILL.md as system context, send the `prompt`, and check the response against the `expectations` array. The expectations are plain-English assertions — no test framework needed.

### What to check

- **Task evals** (`jira/evals/evals.json`, 13 cases): Does the agent produce correct `acli` commands, follow safety rules, use `mdadf --compact`, and respect operating constraints?
- **Trigger evals** (`jira/evals/trigger-evals.json`, 26 cases): Does the skill description trigger for Jira work (`should_trigger: true`) and stay silent for GitHub PRs, Confluence, auth setup, etc. (`should_trigger: false`)?

### Adding evals

When adding a feature or safety rule to SKILL.md, add a corresponding eval. Task evals go in `evals.json`, trigger boundary cases go in `trigger-evals.json`.
