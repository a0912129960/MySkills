# Markdown AI Compatibility Reference

Use this reference when the generated package will be consumed by Claude, Gemini, or another AI agent.

## Core Rule

Markdown files must be complete enough for another AI to understand the task without opening `36-final-dashboard.html`.

## Recommended File Order For Other AI

Provide files in this order:

1. `30-approved-feature-baseline.md`
2. `00-stage-manifest.md`
3. `00-spec-workflow-status.md`
4. `00-context-inventory.md`
5. `09-gate1-flow-sketch.md`, if present
6. `19-gate2-solution-sketch.md`, if present
7. `20-gate2-project-impact.md`
8. `21-gate2-technical-design.md`
9. `22-gate2-constitution-compliance.md`
10. `24-gate2-test-strategy.md`
11. `25-gate2-review.html`
12. `14-decision-log.md`, if present
13. `15-open-questions.md`, if present
14. `gate1-checklist.md`, if present
15. `gate2-checklist.md`, if present
16. `31-final-task-index.md`
17. `34-final-traceability-matrix.md`
18. `35-final-analysis-report.md`
19. `35a-final-readiness-result.md`
20. `36-final-dashboard.html`
21. `37-implementation-package-approval.md`, if present
22. `implementation-evidence.md`, if present
23. `tasks/TASK-xxx.md`
24. `prompts/TASK-xxx.prompt.md`
25. `.ai-dev/context/constitution.md`, if present
26. `.ai-dev/context/project-context.md`, if present

For Gate 1 business review, provide:

1. `00-source-requirement.md`
2. `00-stage-manifest.md`
3. `00-context-inventory.md`
4. `09-gate1-flow-sketch.md`, if present
5. `10-gate1-prd.md`
6. `11-gate1-ears.md`
7. `12-gate1-bdd.feature`
8. `13-gate1-review.html`
9. `14-decision-log.md`, if present
10. `15-open-questions.md`, if present
11. `gate1-checklist.md`, if present
12. `diagrams/user-flow.mmd`
13. `diagrams/user-flow.svg`, if available

For Gate 2 solution review, provide additionally:

1. `19-gate2-solution-sketch.md`, if present
2. `20-gate2-project-impact.md`
3. `21-gate2-technical-design.md`
4. `22-gate2-constitution-compliance.md`
5. `24-gate2-test-strategy.md`
6. `proposed-context-update.md`
7. `25-gate2-review.html`
8. `gate2-checklist.md`, if present
9. `diagrams/api-flow.mmd`
10. `diagrams/cross-project-flow.mmd`, if applicable
11. `diagrams/api-flow.svg`, if available
12. `diagrams/cross-project-flow.svg`, if applicable and available

SVG files are for visual review. Markdown and `.mmd` files remain the AI-readable source of truth.

## Prompting Other AI

Tell the AI:

- Which item to implement.
- Which files to read first.
- Which paths are allowed to modify.
- Which paths are read-only references.
- To implement only the selected item.
- To avoid unrelated refactoring.
- To stop if contracts or high-impact requirements are unclear.
- To follow the task's TDD and validation section.

## Formatting Guidance

- Use stable headings.
- Use tables for summaries.
- Use bullet lists for scope, paths, assumptions, and risks.
- Keep prompts copyable as plain Markdown.
- Avoid putting key instructions only in images or HTML.
