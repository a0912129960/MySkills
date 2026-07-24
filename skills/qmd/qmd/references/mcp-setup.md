# QMD MCP registration

The central MySkills installer may register one stdio server named `qmd` with
command `qmd` and argument `mcp` for installed Claude Code, Codex, and
Antigravity CLIs.

An identical existing registration is adopted without rewriting it. A missing
registration may be offered for addition. A same-name registration with
different settings is a conflict and is never overwritten automatically.
Unrelated MCP servers and settings are preserved.

Claude and Codex use their supported MCP management interfaces. Antigravity is
merged structurally into
`%USERPROFILE%\.gemini\config\mcp_config.json`; that location is independent of
the Antigravity Skill copy target.

CLI access is the required QMD capability. MCP registration is optional:
working CLI access without registration is `CLI_ONLY`, not a degraded Skill.
Do not start QMD's optional persistent HTTP server for this integration.
