# Ticket Drafting Format

Read this file when creating or rewriting a Jira work item.

Draft the summary and description from the conversation context first. Use any directly observed code, runtime, or reproduction context only when it is already available. Do not rely on git history or PR links to explain the issue.

## Summary

- Write the summary as a concise, imperative title.
- Prefer the user-facing problem over the proposed fix.
- Use any extra user-provided context to sharpen the title.

Example:

- `Return actionable MCP response when the application is closed`

## Tasks and Stories

For `Task` and `Story` work items:

- Write a 1 to 3 sentence description that focuses on what the problem is and why it matters.
- Do not describe the solution. The implementation or PR can cover that separately.
- Do not include PR links in the description.

## Bugs

For `Bug` work items, use this exact structure in Markdown so the ADF output renders with bold section labels instead of Jira headings:

```md
**Short Description**
[1-2 sentences: what is broken and under what conditions]

**Steps to Reproduce**
1. [First step]
2. [Second step]
3. [Continue until the bug manifests]

**Expected Behavior**
[What should happen when following the steps above]

**Actual Behavior**
[What actually happens. Include the relevant error message when available, truncated to 2000 characters]

**Impact**
[Who is affected and how severely]

**Environment**
- App version: [include if known]
- OS: [include if known, otherwise omit]
```

Bug drafting rules:

- Use bold section labels such as `**Short Description**`, not Markdown headings such as `## Short Description`.
- Derive reproduction steps from the user-provided context and any directly observed behavior.
- Draft the bug with whatever context is available. Use "[unknown]" for missing fields rather than blocking on clarification. Only ask the user if the problem itself is ambiguous (e.g. you cannot tell what is broken).
- Truncate copied error text to 2000 characters.
- Do not set Priority, Technical Impact, or Business Urgency. Leave those for triage.
