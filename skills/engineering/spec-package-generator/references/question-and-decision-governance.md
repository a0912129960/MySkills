# Question And Decision Governance Reference

Use this reference for cross-stage questions, answers, and decision history.

## Files

- `14-decision-log.md`
- `15-open-questions.md`

## Rules

- Create both files during intake before asking the first clarification
  question. Keep them even when no question remains so a resumed session has a
  stable decision-memory location.
- File numbers indicate earliest creation only.
- Lifecycle and update permissions are controlled by `00-stage-manifest.md`.
- Resolved open questions are not deleted; they are marked `resolved` and linked to a Decision ID.
- Blocking questions prevent gate approval and readiness.
- Do not ask every possible question mechanically. Extract answers from the requirement when present, record low-risk assumptions when safe, and ask only when the missing answer affects PRD, EARS, BDD, test strategy, task scope, release safety, or architecture validity.
- Use the `grilling` one-question-at-a-time decision-tree behavior for all
  critical business, greenfield, solution, test-contract, and task-split
  decisions. Do not batch questions.

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
- Resolve each material assumption through the one-question loop. Gate 1 review
  must show the resulting Decision ID and ruling as an audit item.
- Unconfirmed material assumptions are unresolved and block Gate 1 approval, Gate 2 approval when still relevant, and final readiness.
- Low-risk non-material assumptions may be recorded without blocking readiness.

## Question Format

Every critical question must be recorded with:

- Question ID
- Depends-on Question ID, when its branch is not yet selected
- Layer: Business, EARS, BDD, Architecture Source, Greenfield Technology, Solution, Test Contract, or Task Split
- Question
- Why it matters
- Recommended answer and brief rationale
- Default assumption if unanswered
- Affected artifacts
- Blocking status
- Answer
- Decision ID
- Status

Architecture-source questions are mandatory whenever `00-context-inventory.md`
has a missing in-scope source. Queue them with the other questions and present
only the single highest-impact resolvable question. They do not block Gate 1.

In greenfield mode, architecture-source questions are replaced by greenfield technology questions. These questions are mandatory when the choice affects Gate 2 design, test strategy, task order, or generated prompts.

## Human-Facing Question Presentation

Ask exactly one active decision question in each user-facing turn. Do not show a
batch, questionnaire, or second conditional question. Internally identify
dependent candidates, but activate them only after their prerequisite decision
is resolved.

The active question must include:

- Question ID
- Question text
- Recommended answer and brief rationale
- Why it matters
- Affected artifacts
- Blocking status

Use concise labels so the user can answer quickly. Example:

```text
Q-BIZ-003 — Which role can approve this request?
Recommended: requester manager only, because it preserves separation of duties
without introducing a second approval tier.
Why it matters: affects PRD permission rule, EARS requirement, BDD scenarios,
and task scope.
Affected artifacts: 10-gate1-prd.md, 11-gate1-ears.md, 12-gate1-bdd.feature
Blocking: yes
```

Do not rely on the chat turn as the record. Write the question row and active
question state before sending the question.

Resolve every material assumption through the same one-question loop before Gate
approval. Keep it visible in the Gate review as an audit item with its Decision
ID; do not turn the review into a batch of still-unresolved confirmations.

## Durable Grilling Protocol

Run this protocol whenever a critical decision is unresolved:

1. Re-read `00-spec-workflow-status.md`, `14-decision-log.md`,
   `15-open-questions.md`, the source requirement, and only the artifacts
   affected by the current decision.
2. Resolve discoverable facts from the environment. Record the evidence instead
   of asking the user to repeat it.
3. Identify the highest-impact unresolved question whose dependencies are
   resolved. Add or update its row in `15-open-questions.md`.
4. Before asking, set the applicable Gate 1 or Gate 2 clarification stage in
   `00-stage-manifest.md` to `waiting-for-user`. Set the Question ID as the
   single active question only in `00-spec-workflow-status.md`, set
   `waiting-for-user`, and make the next AI action "record this answer before
   selecting another question."
5. Ask only that question using the human-facing format above, then stop.
6. On the next turn, persist the user's answer first. Set the question to
   `answered`; if the answer is ambiguous, keep it active and ask one focused
   follow-up without advancing the branch.
7. When the ruling is clear, append a Decision ID to `14-decision-log.md`, apply
   it immediately to every currently existing stage-owned affected
   specification artifact, mark invalidated downstream artifacts stale, then
   mark the question `resolved` with its Decision ID.
8. Update `00-spec-workflow-status.md` with the recorded decision, affected
   files, remaining blockers, and next AI action. Only after all writes succeed
   may another question become active.
9. When no critical question remains, set the applicable clarification stage
   in `00-stage-manifest.md` to `complete`, then ask one final
   shared-understanding or applicable micro-gate confirmation question.
   Continue the normal Gate workflow after confirmation.

Specification writes in steps 3-9 are the interview's durable memory, not
implementation of the plan. Never mutate production code. Preserve Gate
ownership: Gate 1 answers may update only intake/governance and Gate 1
artifacts; Gate 2 answers may update Gate 2 artifacts; project context remains
convergence-only.

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
- Capability-slice boundary and user- or system-observable outcome
- Dependency wave, parallel ownership, allowed modify paths, shared contracts, and read-only references

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
