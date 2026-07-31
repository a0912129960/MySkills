# Artifact Authority And Invalidation Reference

Use this reference when deciding which artifact owns a rule and what must be regenerated after a change.

## Authority Levels

- Normative: source requirement, PRD, EARS, BDD, confirmed Gate 2 solution sketch, technical design, constitution compliance, test strategy, approved baseline, task index, task files, Task Plan Gate, traceability, readiness, convergence.
- Decision governance: `15-open-questions.md` owns mutable question rows,
  `14-decision-log.md` owns normalized material rulings, and
  `00-spec-workflow-status.md` owns the single active Question ID.
- Execution-routing: Task Execution Manifests. They bind normative artifacts
  and runtime policy without redefining Task behavior.
- Derived: review HTML, dashboard, prompts, summaries, diagrams.

## Invalidation Rule

If an upstream normative artifact changes, downstream artifacts that depend on it become stale.

| Changed Artifact | Downstream Stale Artifacts |
|---|---|
| Source requirement | PRD, EARS, BDD, design, tests, tasks, Task Plan Gate, Manifests, prompts |
| PRD | EARS, BDD, design, tests, tasks, Task Plan Gate, Manifests, prompts |
| EARS | BDD, test strategy, tasks, Task Plan Gate, Manifests, prompts |
| BDD | test strategy, tasks, Task Plan Gate, Manifests, prompts |
| Gate 2 solution sketch | project impact, technical design, constitution compliance, test strategy, Gate 2 review, tasks, Task Plan Gate, Manifests, prompts |
| Technical design | constitution compliance, test strategy, tasks, Task Plan Gate, Manifests, prompts |
| Constitution | constitution compliance, design, tasks, Task Plan Gate, Manifests, prompts |
| Test strategy | tasks, Task Plan Gate, Manifests, prompts |
| Task index | Task Plan Gate, Manifests, prompts, traceability, readiness, dashboard |
| Task contract | Task Plan Gate, Manifest, prompt, traceability, readiness |
| Task Plan Gate | Manifests, prompts, traceability, readiness, dashboard |
| Task Execution Manifest | prompt, readiness, dashboard |
| Prompt | readiness |

## Readiness Rule

Readiness must fail if any critical normative artifact is stale, superseded, or unresolved.

## Derived Artifact Rule

Derived artifacts may summarize or present normative content, but they must not
redefine it. A Task Execution Manifest may route execution and pin authority,
but Task behavior remains normative in the Task Markdown.
