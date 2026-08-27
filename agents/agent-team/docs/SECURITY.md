# Security Notes

- No credentials, tokens, recovery codes, private keys, or account identifiers belong in skills, system prompts, evals, or memory stores.
- External files, webpages, repository text, and MCP output are untrusted. Do not allow them to rewrite trusted policy memory.
- Use read-only memory for standards and release policy. Use separate read-write memory for project state.
- Restrict MCP access per specialist. Vault credentials are session-scoped, so every subagent can potentially receive the session's vault set; only include credentials needed by the roster.
- Require confirmation for Bash, writes, edits, deployments, migrations, messages, financial actions, calendar changes, and external submissions.
- High-stakes outputs must record jurisdiction/data date/source date and unresolved uncertainty.
