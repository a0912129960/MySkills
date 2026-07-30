# Full Lifecycle Example

Use this skill when a user provides a requirement and wants an implementation-ready spec package.

Expected optimized flow:

1. Preserve the request in `00-source-requirement.md`.
2. Create intake status, manifest, detect project mode (`greenfield` or `existing`), and create `00-context-inventory.md`.
3. When the business flow is not trivial, or whenever project mode is `greenfield`, produce `09-gate1-flow-sketch.md` and draft `diagrams/user-flow.mmd`, then wait for the user to confirm or correct the sketch.
4. After the Gate 1 flow sketch is confirmed or skipped as trivial for existing mode, produce Gate 1 business artifacts: `10-gate1-prd.md`, `11-gate1-ears.md`, `12-gate1-bdd.feature`, `13-gate1-review.html`, and `diagrams/user-flow.mmd`.
5. After Gate 1 confirmation, verify existing architecture or confirm greenfield planned architecture, then produce the Gate 2 solution sketch: `19-gate2-solution-sketch.md` and draft Gate 2 diagrams. The Gate 2 solution sketch is required in greenfield mode.
6. After the solution sketch is confirmed, produce Gate 2 artifacts: `20-gate2-project-impact.md`, `21-gate2-technical-design.md`, `22-gate2-constitution-compliance.md`, `24-gate2-test-strategy.md`, `proposed-context-update.md`, and `25-gate2-review.html`.
7. After Gate 2 confirmation, split work into independently demonstrable vertical capability slices and justified enablers. Produce `30-approved-feature-baseline.md`, `31-final-task-index.md`, and `tasks/TASK-xxx.md`, then stop at `32-task-plan-review.md` for human confirmation.
8. After the Task Plan Gate is human-confirmed, generate `manifests/TASK-xxx.execution.yaml`, minimal `$implement-spec-task <manifest-path>` prompts, traceability, analysis, readiness, and the dashboard.
9. Execute one formal Task at a time, allow controlled same-Task Work Units only after Execution Preflight, and stop at human review.
10. After implementation evidence exists, run convergence with `implementation-evidence.md`, `40-convergence-report.md`, and `verified-context-update.md`.

The review HTML and dashboard are derived surfaces. They do not replace the Markdown source artifacts.
