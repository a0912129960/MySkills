# Question And Decision Governance Reference

Use this reference for cross-stage questions, answers, and decision history.

## Files

- `14-decision-log.md`
- `15-open-questions.md`

## Rules

- These files may be created after Gate 1 clarification and updated later.
- File numbers indicate earliest creation only.
- Lifecycle and update permissions are controlled by `00-stage-manifest.md`.
- Resolved open questions are not deleted; they are marked `resolved` and linked to a Decision ID.
- Blocking questions prevent gate approval and readiness.
- Do not ask every possible question mechanically. Extract answers from the requirement when present, record low-risk assumptions when safe, and ask only when the missing answer affects PRD, EARS, BDD, test strategy, task scope, release safety, or architecture validity.

Open question status values:

- `open`: unanswered and still relevant.
- `answered`: the user answered, but the answer has not yet been converted into a decision or artifact update.
- `resolved`: answered and reflected in the affected artifacts, with a Decision ID when material.
- `deferred`: intentionally postponed with an explicit reason and affected gate/readiness impact.
- `superseded`: replaced by a newer question, decision, or revised artifact.

Gate 1 scenario field status values are separate from open question status values:

- `extracted`: directly found in the requirement or source material.
- `assumed`: safely assumed and recorded.
- `asked`: raised as a question.
- `blocking`: required before the gate can be approved.
- `not-applicable`: not relevant to this scenario.

## Material Assumptions

A material assumption is any assumption that affects PRD behavior, EARS statements, BDD scenarios, test strategy, task scope, release behavior, permissions, or user-visible behavior.

Rules:

- Material assumptions must be recorded in `15-open-questions.md` or `14-decision-log.md` with affected artifacts.
- Gate 1 review must show each material assumption as an explicit confirm/override item.
- Unconfirmed material assumptions are unresolved and block Gate 1 approval, Gate 2 approval when still relevant, and final readiness.
- Low-risk non-material assumptions may be recorded without blocking readiness.

## Question Format

Every critical question must be recorded with:

- Question ID
- Layer: Business, EARS, BDD, Architecture Source, Greenfield Technology, Solution, Test Contract, or Task Split
- Question
- Why it matters
- Default assumption if unanswered
- Affected artifacts
- Blocking status
- Answer
- Decision ID
- Status

Architecture-source questions are mandatory whenever `00-context-inventory.md` has a missing in-scope source. They do not count against Gate 1 or Gate 2 clarification budgets.

In greenfield mode, architecture-source questions are replaced by greenfield technology questions. These questions are mandatory when the choice affects Gate 2 design, test strategy, task order, or generated prompts.

## Human-Facing Question Presentation

When asking the user clarification questions in chat, present them as a numbered list that can be answered in batch.

Each question shown to the user must include:

- Question text
- Suggested default answer
- Why it matters
- Affected artifacts
- Blocking status

Use concise labels so the user can answer quickly. Example:

```text
1. Which role can approve this request?
   Suggested default: requester manager only
   Why it matters: affects PRD permission rule, EARS requirement, BDD scenarios, and task scope
   Blocking: yes
```

End the question batch with an answer-format hint:

```text
You can answer in batch, for example: "1 use default, 2 choose B, 3 no".
```

If a question is non-blocking but material, ask for explicit confirm/override in the gate review instead of silently treating the default as approved.

## Gate 1 Scenario Checklist

For every core user scenario, the agent must classify each field as `extracted`, `assumed`, `asked`, `blocking`, or `not-applicable`:

- Actor / role
- Trigger
- Preconditions
- Main flow
- Observable outcome
- Exception flow
- State transition
- Permission rule
- Out of scope boundary
- Acceptance criteria

Gate 1 must not be approved while a core scenario has a blocking field. If the missing field is low risk, record the assumption and affected artifacts instead of asking.

Gate 1 must not be approved while a material assumption is unconfirmed.

## Gate 2 Solution Checklist

For every solution-impacting area, derive from verified context or confirmed greenfield design first; ask only when more than one reasonable choice remains and the choice affects implementation or review:

- API / DTO contract and compatibility
- Data storage, schema, or query approach
- Cross-project integration mechanism
- Permission or security behavior
- Validation and error-code behavior
- Logging, audit, or operational evidence
- Release order and contract compatibility when verified released contracts or active consumers exist
- BDD scenario to Test ID mapping
- Test Contract completeness for automated and semi-automated validation
- Task split boundary, allowed modify paths, and read-only references

For greenfield projects, also confirm these choices before Gate 2 approval when applicable:

- Frontend framework and routing approach
- Backend/runtime framework
- Package manager and workspace layout
- Database or storage technology
- Authentication and authorization provider
- Test runner and test strategy bootstrap
- Linting, formatting, and type-checking tools
- Deployment target and environment model
- Initial directory structure and module boundaries

Gate 2 must not be approved while an automated or semi-automated Test ID lacks the Test Contract fields required by `24-gate2-test-strategy.md`, unless the item is downgraded to manual with an explicit fallback and reason.

## Decision History

Record each material decision with:

- Decision ID
- Question or issue
- Answer or ruling
- Affected artifacts
- Date
