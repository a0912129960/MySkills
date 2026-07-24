---
name: improve-codebase-architecture
description: Scan a codebase for architecture deepening opportunities, render an offline visual report, and discuss only the human-selected candidate. Use only when explicitly invoked.
disable-model-invocation: true
---

# Improve Codebase Architecture

This is a report-and-discussion workflow. It does not schedule scans, run in the
background, or implement a refactor.

## Survey

Load `codebase-design` and use its terms exactly. Read domain language and
applicable ADRs. Use the scope named by the human; otherwise use Git history
when available to identify recently changing hot spots, or ask for a scope when
neither is available.

Explore for shallow interfaces, scattered change, poor locality, missing public
test seams, and repeated dependency knowledge. Apply the deletion test and do
not recommend a speculative seam with only one real adapter.

## Offline report

Create a self-contained HTML report in the operating-system temporary directory
using the packaged guidance in [HTML-REPORT.md](HTML-REPORT.md). It must work
without network access. Use embedded CSS and inline SVG. Mermaid source may be
rendered with the centrally managed Mermaid CLI when available; otherwise use
the complete basic HTML/CSS/SVG fallback.

For each candidate include files, observed friction, a deepening direction,
test impact, before/after visual, ADR conflicts, and recommendation strength.
Identify the top recommendation and give the absolute report path.

Ask which one candidate the human wants to discuss. Do not design an interface
or edit production code until they select one. For the selected candidate, use
the `grilling`, `domain-modeling`, and `codebase-design` workflows as needed and
record only human-confirmed domain or architecture decisions.
