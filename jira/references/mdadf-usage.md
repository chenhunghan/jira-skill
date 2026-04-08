# Markdown to ADF

Read this file for platform-specific `mdadf` patterns not covered inline in SKILL.md. The POSIX process substitution example is already in SKILL.md.

## Windows PowerShell

Process substitution is not available. Write ADF to a temp file first:

```powershell
mdadf --compact input.md -o $env:TEMP\desc.json
acli jira workitem create `
  --summary "Fix the login page" `
  --project "MYPROJECT" `
  --type "Bug" `
  --description-file $env:TEMP\desc.json
```

## Rules

- Write the intended Jira rich text in Markdown first.
- Keep summaries and titles as plain text.
- Prefer `--key` for single known work items and comments.
- Prefer `--description-file`, `--body-file`, and `--body-adf` over inline JSON arguments.
