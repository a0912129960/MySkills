# Artifact Authority And Invalidation Reference

Use this reference when deciding which artifact owns a rule and what must be regenerated after a change.

## Authority Levels

- Normative: source requirement, PRD, EARS, BDD, confirmed Gate 2 solution sketch, technical design, constitution compliance, test strategy, approved baseline, task index, task files, traceability, readiness, convergence.
- Derived: review HTML, dashboard, prompts, summaries, diagrams.

## Invalidation Rule

If an upstream normative artifact changes, downstream artifacts that depend on it become stale.

| Changed Artifact | Downstream Stale Artifacts |
|---|---|
| Source requirement | PRD, EARS, BDD, design, tests, tasks, prompts |
| PRD | EARS, BDD, design, tests, tasks, prompts |
| EARS | BDD, test strategy, tasks, prompts |
| BDD | test strategy, tasks, prompts |
| Gate 2 solution sketch | project impact, technical design, constitution compliance, test strategy, Gate 2 review, tasks, prompts |
| Technical design | constitution compliance, test strategy, tasks, prompts |
| Constitution | constitution compliance, design, tasks, prompts |
| Test strategy | tasks, prompts |
| Task index | traceability, readiness, dashboard |
| Task contract | prompt, traceability, readiness |
| Prompt | readiness |

## Readiness Rule

Readiness must fail if any critical normative artifact is stale, superseded, or unresolved.

## Derived Artifact Rule

Derived artifacts may summarize or present normative content, but they must not redefine it.
