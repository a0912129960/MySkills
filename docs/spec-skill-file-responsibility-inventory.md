# Spec Skill File Responsibility Inventory

Status: accepted as the target ownership baseline by `DEC-022`. Detailed open
boundaries remain specification decisions; this inventory does not authorize
implementation. It covers every current source file under
`spec-package-generator` and `implement-spec-task`.

## Inventory Summary

- `spec-package-generator`: 59 files — 1 `SKILL.md`, 1 agent manifest,
  1 example, 17 references, and 39 templates.
- `implement-spec-task`: 7 files — 1 `SKILL.md`, 1 agent manifest,
  1 reference, and 4 templates.
- Total: 66 current source files.

Target ownership rules:

1. `SKILL.md` is a minimal entry router and safety boundary, never the workflow
   or architecture owner.
2. `package-schema.yaml` owns every generated file role's physical path/pattern,
   producer, authority category, writer, loading, lifecycle, cleanup, and
   contract/guide keys. `file-contracts.json` owns parser/check profiles;
   `file-guide.yaml` owns concise AI-facing purpose/use. `architecture.md`
   explains stable module seams without restating any catalog.
3. `workflow.md` owns sequencing, gates, transitions, and stop/resume behavior.
4. `id-schema.yaml` owns ID classification and deterministic ID rules.
5. Templates own shape, not policy. `output-files.md` no longer owns a parallel
   artifact catalog; a human-readable catalog is generated from Package Schema
   role definitions on demand.
6. Validator code owns executable checks. Markdown must not duplicate its rule
   list.
7. Current normative artifacts own meaning. Indices, matrices, HTML, dashboards,
   reports, and prompts are derived views only.
8. Only question/decision cards survive as cold history. Other intermediate or
   consumed records are removed after their result is atomically represented in
   current state.

Action labels:

- **Keep** — already has a distinct responsibility.
- **Rewrite** — retain the file but narrow it to one responsibility.
- **Merge then retire** — move unique rules to the named owner and remove the file.
- **Retire** — redundant under the confirmed target model.
- **Transient output** — retain a template only if the artifact is needed while
  work is active; delete generated instances after their result is applied.

## Primary Duplication Clusters

| Cluster | Current duplicate owners | Proposed single owner |
|---|---|---|
| Pipeline and gates | both `SKILL.md` files, `workflow.md`, `stage-manifest.md`, `status-tracking.md` | `workflow.md`; current position in workflow status |
| Artifact authority/invalidation | `SKILL.md`, `artifact-authority-and-invalidation.md`, `stage-manifest.md`, every template's `dependsOn`/`invalidates` | `architecture.md` plus executable ID/artifact validation |
| Questions and decisions | workflow status, stage manifest, 14, 15, question governance, frontmatter IDs, Gate reviews | Active Question State in workflow status; cold Decision Archive |
| Generated-file responsibilities | `SKILL.md`, `workflow.md`, `output-files.md`, templates, Markdown AI file-order list | three DEC-041 catalogs joined by role; templates only define shape and human catalog is generated |
| Context loading order | `SKILL.md`, `workflow.md`, `status-tracking.md`, `stage-manifest.md`, `context-window-management.md`, `markdown-ai-compatibility.md` | minimal `SKILL.md` routing plus `workflow.md` current-stage reads |
| PRD/EARS/BDD/Test/Task chain | `ears-bdd-tdd.md`, `test-contracts.md`, `traceability-and-tasking.md`, readiness rules and templates | one specification/tasking reference plus `id-schema.yaml`; test contract reference only for validation semantics |
| Readiness | `machine-readiness.md`, Gate checklists, final analysis, readiness result, dashboard | validator implementation and one current readiness result |
| Task scope/routing | task file, task index, Manifest, dashboard, executor contract | Task owns behavior; Manifest owns routing; index/dashboard are derived |
| Task lifecycle | task index, task file, Manifest, dashboard `localStorage`, Execution Records | one `execution/task-state.yaml` |
| Context convergence | context lifecycle, proposed/verified updates, implementation evidence, convergence report, project-context update log | current project context; other outputs are transient |
| Review presentation | Gate HTML, Gate checklists, dashboard, Markdown summaries | HTML/dashboard are derived human surfaces; validator owns checks |

## `spec-package-generator` Root And Metadata

| Current file | Current responsibility | Overlap / issue | Proposed action |
|---|---|---|---|
| `SKILL.md` | Entry point plus artifact model, full workflow, authority, rules, resources, completion | Duplicates almost every reference; 386 lines despite claiming to be entry-only | **Rewrite** as a small router: purpose, safety boundary, mode-to-reference routing, stop boundary |
| `agents/openai.yaml` | Codex display and invocation policy | Required platform metadata; no domain duplication | **Keep** |
| `examples/full-lifecycle.md` | Example pipeline | Repeats workflow and becomes stale when workflow changes | **Retire** from runtime skill; move any valuable scenario to tests/fixtures |

## `spec-package-generator/references`

| Current file | Current responsibility | Overlap / issue | Proposed action |
|---|---|---|---|
| `artifact-authority-and-invalidation.md` | Artifact authority and file-level invalidation graph | Authority repeats `SKILL.md` and stage manifest; file-level invalidation conflicts with ID-level Current rewrite impact | **Merge then retire** into `architecture.md` and validator rules |
| `constitution-governance.md` | Project-rule scopes and amendment timing | Specialized, conditionally loaded policy; some timing repeats workflow | **Keep**, trimmed to constitution semantics only |
| `context-lifecycle.md` | Current project facts, evidence inventory, proposed/verified context timing | Timing repeats workflow; update-log concepts retain history | **Rewrite** to own only current-evidence states and promotion rules |
| `context-window-management.md` | Stage-specific read order and bounded prompt context | Repeats routing in `SKILL.md`, workflow, status, stage manifest, and Markdown compatibility | **Merge then retire** into minimal router and workflow read sets |
| `cross-project-analysis.md` | Provider/consumer analysis and cross-project risk | Single-project placeholder rule creates unnecessary artifact; some Task slicing overlaps tasking reference | **Keep** as conditional Gate 2 analysis; remove mandatory single-project output |
| `dashboard-guidelines.md` | Dashboard shape, sources, task loop, status behavior | Duplicates dashboard template, output roles, readiness, task lifecycle, and executor loop | **Merge then retire**: shape in template, lifecycle in Package Schema, purpose/use in File Guide |
| `ears-bdd-tdd.md` | PRD/EARS/BDD ownership and conversion rules | Traceability/test/task rules repeat `test-contracts.md` and `traceability-and-tasking.md` | **Merge then retire** into one concise specification-and-tasking reference |
| `machine-readiness.md` | Readiness sequence and hard-fail rules | Duplicates readiness template, checklists, final analysis, dashboard, tasking, and executor rules | **Merge then retire** after rules become executable validator checks |
| `markdown-ai-compatibility.md` | Recommended load order and generic formatting | Repeats output list, status/stage read order, prompt rules, and archive loading that target design forbids | **Retire**; current index/Manifest and workflow define bounded reads |
| `mermaid-rendering.md` | Conditional Mermaid source/render behavior | Distinct tool-specific policy | **Keep** and load only when a diagram is required |
| `output-files.md` | Purpose and expected content of every generated artifact | A Markdown catalog would duplicate the executable Package Schema and drift | **Retire as authority**; generate an on-demand human view from Package Schema roles |
| `question-and-decision-governance.md` | 14/15 authority, question format, grilling protocol, scenario checklists | Duplicates workflow/status and permanently couples history to current artifacts | **Merge then retire**: transaction sequence into workflow, archive isolation into architecture, current shape into status/archive templates |
| `stage-manifest.md` | Stage order, ownership, stale graph, resume | Duplicates workflow, status, output catalog, and frontmatter; creates another mutable owner | **Retire** together with `00-stage-manifest.md` |
| `status-tracking.md` | When/how to update status, stage values, resume and completion | Duplicates workflow and status template; lists historical updates rather than current state | **Merge then retire** into workflow plus a narrow status template |
| `test-contracts.md` | Test-contract fields, modes, TDD pattern, embedded static test inventory, readiness checklist | Fields duplicate template; 300+ lines of repository test cases are runtime history; readiness repeats machine readiness | **Rewrite** to validation semantics only; move static test cases to repository tests and let template own shape |
| `traceability-and-tasking.md` | Trace chain, vertical tasks, waves, prompts | Trace and TDD repeat other references; lifecycle repeats task index/dashboard/executor | **Merge then retire** into one specification-and-tasking reference; keep only semantic slicing rules there |
| `workflow.md` | Full workflow, modes, gates, revisions, stop/resume | Correct owner but duplicates `SKILL.md` and specialized references | **Rewrite** as sole sequencing owner; link to conditional policies without restating them |

## `spec-package-generator/templates`

### Intake And Decision Control

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `00-context-inventory.template.md` | Current feature-specific verified/unverified evidence | User-provided source log, proposed/verified update sections duplicate context lifecycle artifacts | **Rewrite** to current evidence and current gaps only |
| `00-source-requirement.template.md` | Current user requirement input | Question/Decision references and assumption history duplicate governance logs | **Rewrite** to current requirement and current unresolved ambiguity only |
| `00-spec-workflow-status.template.md` | Current phase and resumable transaction progress facts | Generated-file lists, recent decisions, duplicated sketch/gate fields, question content, persisted next-action prose | **Rewrite** as the single compact current workflow-state owner; Controller derives next action |
| `00-stage-manifest.template.md` | Stage order, artifact ownership/invalidation | Duplicates workflow, output catalog, status, and template frontmatter | **Retire** |
| `14-decision-log.template.md` | Permanent normalized decisions | Coupled current authority and duplicated 15 data | **Retire**, replaced by cold compact Decision Archive template |
| `15-open-questions.template.md` | Permanent question lifecycle | Retains resolved history and duplicates active status | **Retire**; unresolved question lives in Active Question State, historical question in cold archive |

### Gate 1

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `09-gate1-flow-sketch.template.md` | Early draft flow confirmation | Repeats PRD/BDD flow, questions and decision audit | **Transient output**; keep only draft flow needed for confirmation, then absorb into current Gate 1 artifacts and delete |
| `10-gate1-prd.template.md` | Current product scope, scenarios, rules, acceptance | Question references/frontmatter duplicate current state/archive | **Keep and rewrite** as Gate 1 product owner with ID Schema definitions |
| `11-gate1-ears.template.md` | Current precise observable requirements | Source Question/Decision column couples history | **Keep and rewrite** to link current PRD/EARS IDs only |
| `12-gate1-bdd.template.feature` | Current acceptance scenarios | Distinct normative behavior examples | **Keep** with current BDD IDs/tags defined by ID Schema |
| `13-gate1-review.template.html` | Derived human confirmation surface | Repeats PRD/EARS/BDD and renders decision/question history | **Transient derived output**; no authority, delete after Gate result is current |
| `gate1-checklist.template.md` | Gate 1 validation | Duplicates validator/readiness and review HTML | **Retire** after executable validation exists |

### Gate 2

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `19-gate2-solution-sketch.template.md` | Early solution confirmation | Repeats project impact/design/test/task plan and decision audits | **Transient output**; absorb confirmed content into current Gate 2 owners, then delete |
| `20-gate2-project-impact.template.md` | Current cross-project responsibilities, contracts and release constraints | Some responsibility text repeats solution sketch/diagram | **Keep and rewrite** as the cross-project impact owner |
| `21-gate2-technical-design.template.md` | Current design decisions and technical boundaries | Has no design IDs; likely-file sections duplicate Task/Manifest/preflight routing | **Replace** with a YAML multi-document owner for independently revisable `DESIGN-nnn` records; remove speculative path-routing sections |
| `22-gate2-constitution-compliance.template.md` | Current compliance outcome and explicit exceptions | Amendment history and baseline copies can duplicate current constitution | **Keep conditionally**, current findings only |
| `24-gate2-test-strategy.template.md` | Test approach, risk coverage, Test ID index | Embeds full Test Contract format/examples also present in test-case template/reference | **Rewrite** as strategy and Test ID index; individual test contracts own executable details |
| `25-gate2-review.template.html` | Derived Gate 2 confirmation surface | Repeats all Gate 2 artifacts | **Transient derived output**, delete after confirmation is current |
| `gate2-checklist.template.md` | Gate 2 validation | Duplicates validator/readiness and review HTML | **Retire** after executable validation exists |
| `proposed-context-update.template.md` | Candidate reusable context facts | Becomes history after verification/rejection | **Transient output**, delete after convergence applies or rejects it |

### Final Planning And Readiness

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `30-approved-feature-baseline.template.md` | Copies approved scope and ID lists | Duplicates Gate artifacts, Current ID Index and Gate state | **Retire**; current IDs plus Gate confirmation identify the baseline |
| `31-final-task-index.template.md` | Cross-task planning view | Duplicates Task details and lifecycle state; currently both normative and derived | **Rewrite** as a regenerated planning view only; remove lifecycle and duplicated contracts |
| `task.template.md` | Current normative behavior/scope for one Task | Duplicates Manifest routing paths, status, test contract details and index metadata | **Rewrite** to own Task outcome, scope meaning, acceptance, and current ID references only |
| `32-task-plan-review.template.md` | Human Task Plan confirmation | Duplicates task index and becomes approval history | **Transient human surface**; write current confirmation into workflow/task state, then delete |
| `task-execution-manifest.template.yaml` | One Task's execution routing | Contains lifecycle state and pins mutable state; overlaps Task path fields | **Rewrite** to immutable routing only; no lifecycle, no mutable/pinned overlap |
| `tdd-prompt.template.md` | Copyable executor invocation | Fully derivable from Manifest and dashboard | **Retire**; render invocation on demand |
| `34-final-traceability-matrix.template.md` | Human-readable current ID relationship view | Derived graph can drift if edited | **Keep only as validator-generated view** or render on demand; never normative |
| `35-final-analysis-report.template.md` | Consistency/traceability/risk summary | Duplicates validator and readiness result | **Retire** |
| `35a-final-readiness-result.template.md` | Persisted current readiness | Duplicates checklists and hand-authored rules | **Replace** with validator-generated current readiness result/schema |
| `36-final-dashboard.template.html` | Derived human execution surface | Copies many Task/Manifest fields and owns duplicate lifecycle via `localStorage` | **Keep and rewrite** as `current/views/dashboard.html`: feature name, Task count/order, and Task cards with ID, title, one-line outcome, dependencies, Task/Manifest links, and copyable Manifest-backed execution Prompt only; remove all other fields, local state, and export |
| `37-implementation-package-approval.template.md` | Optional named approval | Duplicates Task Plan Gate/readiness | **Retire by default**; external governance may supply its own approval artifact |

### Context, Constitution, And Convergence

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `constitution.template.md` | Per-package workflow constitution | Duplicates Skill architecture/governance | **Retire** |
| `implementation-constitution.template.md` | Current project implementation rules | May duplicate external `AGENTS.md`/project rules | **Keep only as a project-level current rule source when no existing owner exists**; never feature-local history |
| `constitution-amendment.template.md` | Proposed rule change and rationale | Becomes historical after current constitution changes; overlaps Decision Archive | **Transient output**; archive the material decision card, apply current rule, delete amendment |
| `implementation-evidence.template.md` | Current execution/convergence summary and record index | Designed as permanent index to Execution Record history | **Transient output**; retain only while evidence is being applied |
| `40-convergence-report.template.md` | Compares implementation with approved baseline and context proposal | Historical after current state/context promotion | **Transient output**, delete after atomic application |
| `project-context.template.md` | Current reusable verified project facts | `Update Log` is history | **Keep and rewrite** as current facts only; remove update log |
| `verified-context-update.template.md` | Evidence-backed promotion instruction | Historical after project context is updated | **Transient output**, delete after application |

### Validation And Miscellaneous

| Current file | Intended owner | Duplicate / historical content | Proposed action |
|---|---|---|---|
| `test-case-contract.template.md` | One executable Test ID contract shape | Field list duplicates test-contract reference and strategy | **Keep** as contract shape; other files reference it without copying fields |

## `implement-spec-task`

| Current file | Current responsibility | Overlap / issue | Proposed action |
|---|---|---|---|
| `SKILL.md` | Entry plus qualification, preflight, execution and stop flow | Duplicates execution contract and generator package rules | **Rewrite** as minimal router and safety boundary |
| `agents/openai.yaml` | Codex display and invocation policy | Required metadata | **Keep** |
| `references/execution-contract.md` | Executor authority, qualification, preflight, coordination, lifecycle, evidence, revision | Repeats generator Task/Manifest model and permanent-history rules | **Rewrite** as sole executor sequencing owner; reference package contract without restating it |
| `templates/execution-preflight.template.md` | Current proposed/approved execution boundary | Needed only while selected Task is active | **Transient output**; may later be folded into current Task State if one owner is preferable |
| `templates/work-unit-brief.template.md` | Bounded internal worker instruction | Current coordination only, not specification | **Transient output**, delete when the active Task completes |
| `templates/execution-record.template.md` | Detailed append-only execution/review history | Conflicts with decision to delete non-decision history | **Transient output**; consolidate current result/state, then delete |
| `templates/spec-change-request.template.md` | Evidence-backed request to revise current specification | Needed only until the planned Current rewrite reaches final `PASS` | **Transient output**, delete after application |

## Final 43-Template Disposition Matrix

This matrix closes repository migration accounting. `Closed disposition` uses
exactly `rewrite`, `merge_replace`, `render_none`, `retire`, or
`external_current`. `target role: none` means the producer is retired or its
value is returned in conversation/on demand and no file is persisted. A source
appears exactly once; runtime Package Schema contains only retained target
roles, not these legacy source names.

The enum is operational: `rewrite` retains exactly one source as the rewritten
sole template producer for its target role; `merge_replace` merges behavior into
the named template/programmatic producer and deletes this source; `render_none`
deletes the source and replaces it with a non-persistent renderer; `retire`
deletes it without replacement; `external_current` deletes/replaces it through
the registered project-scope Current producer. Multiple sources may target one
role only through `merge_replace`; they never become competing final producers.

| Source template | Closed disposition | Target role / replacement producer | Persistence |
|---|---|---|---|
| `00-context-inventory.template.md` | merge_replace | `candidate_discussion`; Controller promotes verified meaning into typed Records/project context | active transaction |
| `00-source-requirement.template.md` | merge_replace | `requirement_records` | Current normative |
| `00-spec-workflow-status.template.md` | rewrite | `workflow_state` / Controller | latest state |
| `00-stage-manifest.template.md` | retire | none; Package Schema plus Controller transitions | none |
| `09-gate1-flow-sketch.template.md` | merge_replace | `candidate_review`; merge into the retained generic review renderer | latest active transaction view |
| `10-gate1-prd.template.md` | merge_replace | `requirement_records` | Current normative |
| `11-gate1-ears.template.md` | merge_replace | `requirement_records` | Current normative |
| `12-gate1-bdd.template.feature` | rewrite | `bdd_records` | Current normative |
| `13-gate1-review.template.html` | rewrite | `candidate_review` | latest active transaction view |
| `14-decision-log.template.md` | rewrite | `decision_archive` | retained cold |
| `15-open-questions.template.md` | rewrite | `active_question` | active transaction |
| `19-gate2-solution-sketch.template.md` | merge_replace | `candidate_review`; merge into the retained generic review renderer | latest active transaction view |
| `20-gate2-project-impact.template.md` | merge_replace | `design_records` | Current normative |
| `21-gate2-technical-design.template.md` | rewrite | `design_records` | Current normative |
| `22-gate2-constitution-compliance.template.md` | merge_replace | `design_records` for current applicable constraints; external rule source remains external | Current normative |
| `24-gate2-test-strategy.template.md` | merge_replace | `test_records` | Current normative |
| `25-gate2-review.template.html` | merge_replace | `candidate_review`; merge into the retained generic review renderer | latest active transaction view |
| `30-approved-feature-baseline.template.md` | retire | none; Current Records/ID Index plus matching VALID own baseline | none |
| `31-final-task-index.template.md` | merge_replace | `task_records`; dashboard renderer derives summary | Current normative |
| `32-task-plan-review.template.md` | merge_replace | `candidate_review`; merge into the retained generic review renderer | latest active transaction view |
| `34-final-traceability-matrix.template.md` | render_none | none; Controller graph query | generated on demand |
| `35a-final-readiness-result.template.md` | retire | none; Controller `pass` plus `validation_result` qualifies implementation | none |
| `35-final-analysis-report.template.md` | retire | none; typed Validator findings and Controller summary | none |
| `36-final-dashboard.template.html` | rewrite | `dashboard_view` | latest Current view |
| `37-implementation-package-approval.template.md` | retire | none; external governance remains outside Feature Package | none |
| `40-convergence-report.template.md` | render_none | none; Controller applies verified result directly to Current/context | generated on demand |
| `constitution.template.md` | retire | none; Skill definitions own workflow architecture | none |
| `constitution-amendment.template.md` | retire | none; current external rule changes in their owner, compact ruling in `decision_archive` | none |
| `gate1-checklist.template.md` | retire | none; executable contracts and Gate Controller | none |
| `gate2-checklist.template.md` | retire | none; executable contracts and Gate Controller | none |
| `implementation-constitution.template.md` | external_current | `project_rule_source` outside Feature Package, only when no existing project-rule owner exists | external current |
| `implementation-evidence.template.md` | render_none | none; verified current result goes to Task State/project context | generated on demand |
| `project-context.template.md` | external_current | `project_context` outside Feature Package | external current |
| `proposed-context-update.template.md` | render_none | none; active discussion then verified direct context application | generated on demand |
| `task.template.md` | rewrite | `task_records` | Current normative |
| `task-execution-manifest.template.yaml` | rewrite | `task_manifest` / Controller | while Task ID active |
| `tdd-prompt.template.md` | retire | none; Dashboard copies the Manifest-backed invocation | none |
| `test-case-contract.template.md` | merge_replace | `test_records` | Current normative |
| `verified-context-update.template.md` | external_current | `project_context` outside Feature Package | external current |
| `implement-spec-task/execution-preflight.template.md` | rewrite | `task_state` stores only approved current boundary; detailed proposal is conversational | latest state |
| `implement-spec-task/execution-record.template.md` | retire | none; current result goes to Task State/context, detailed chronology is deleted | none |
| `implement-spec-task/spec-change-request.template.md` | merge_replace | `candidate_discussion`; merge into Controller handoff, which creates `active_question` through the normal protocol after User authorization | active transaction |
| `implement-spec-task/work-unit-brief.template.md` | render_none | none; bounded agent message | generated on demand |

Repository validation must count exactly 43 source rows, require one closed
disposition for each source file, require every non-`none` target role to exist
in Package Schema/File Guide and resolve to one File Contract, and reject any
retired source still referenced by instructions, examples, generators, or tests.

### Programmatic And Non-Persistent Producer Inventory

| Producer | Output roles | Writer rule |
|---|---|---|
| Package Controller | `current_id_index`, five Current Record-owner roles, `task_manifest`, `active_question`, `candidate_discussion`, `candidate_application_plan`, `workflow_state`, `id_allocation_state`, `decision_archive` | AI supplies Q/discussion/after payload meaning only through Controller; Controller resolves paths, allocates IDs, applies payloads, and writes atomically |
| Task Execution Controller | `task_state` | Sole lifecycle writer except the human-only `accepted` transition mediated by the Controller |
| Package Validator | `validation_result`, `validator_attempt` | Read-only toward Current/Candidate/History; atomic latest-result/attempt writes only |
| User View Renderer | `candidate_review`, `dashboard_view` | Deterministic one-way render, atomic latest-only overwrite; never read back as authority |
| Migration Adapter | project-scope `migration_plan` plus writes delegated through Package Controller | Separately authorized, temporary, idempotent; ordinary resume refuses while active |
| Project Context Controller | external `project_context` and conditional external `project_rule_source` | Writes only after verified convergence/human rule authorization; never creates Feature history |
| On-demand Presenter | traceability, analysis, convergence, implementation evidence, context proposal, Work Unit Brief, execution preflight detail | `persistence: none`; returns output to User/agent channel and creates no package file |

Every retained role has one writer in this table. Templates specify shape but do
not choose paths or become writers. A new producer or persisted output requires
updating this inventory and all three joined catalogs before repository
validation can pass.

### Final AI Purpose Guide Inputs

These are the concise semantics that move into `file-guide.yaml`; paths and
contracts remain in their separate owners.

| Role | Purpose | AI use |
|---|---|---|
| `current_id_index` | Active Specification ID membership only | Query membership; never infer location, relationship, history, or next ID |
| `requirement_records` | Current observable requirement statements | Load only selected REQ targets/dependents |
| `bdd_records` | Current behavior examples | Load only selected scenarios and graph neighbors |
| `design_records` | Current technical decisions needed by this Feature | Load only selected design inputs |
| `test_records` | Current verification contracts | Load selected TEST inputs; execute through Manifest routing |
| `task_records` | Current Task outcome and specification coverage | Load the selected TASK; never read lifecycle from it |
| `task_manifest` | Immutable execution read/write/test routing for one TASK | Implementation reads only selected Manifest; never derive behavior from it |
| `dashboard_view` | Latest minimal User Task overview and copyable invocation | Display only; never use as generation/implementation input |
| `active_question` | One active material question, answer, and declared change subjects | Read during its transaction; remove after deterministic DEC binding clear |
| `candidate_discussion` | Durable working explanation/context for that one question | Resume planning only; never treat as Current or History |
| `candidate_application_plan` | Exact temporary question/validation-basis Current delta, allocation baseline, and expected final | Controller allocates/applies/reconciles; delete after its question or validated-repair commit |
| `candidate_review` | Latest User-facing confirmation rendering during active question work | Display only; overwrite when needed and delete after that question commits |
| `decision_archive` | Compact ID-free rationale for confirmed material decisions | Load only for an explicit historical question; never resume or implement from it |
| `workflow_state` | Three-field transaction phase/Q/sealed-Plan checkpoint | Controller reads internally and returns a bounded summary; AI does not load the file by default |
| `task_state` | Latest lifecycle value for active TASK IDs | Qualification/status transition only; no specification meaning |
| `id_allocation_state` | Monotonic five-class Specification and shared Q/DEC decision high-water counters | Controller-only; never load into AI context or derive from History during normal work |
| `validation_result` | Latest typed legality evidence for raw evaluated checkpoint, canonical Current/rules/allocation/engine, and finish/repair/migration transaction | Controller qualification and deterministic repair only; AI receives a bounded summary |
| `validator_attempt` | Explicit invalid-checkpoint episode and three-repair circuit breaker | Validator/Controller-only; remove when that corrected checkpoint commits |
| `project_context` | Current verified reusable project facts | Load only facts relevant to the Feature; no update history |
| `project_rule_source` | Current implementation rules when no stronger owner exists | Treat as applicable project rules, never Feature history |
| `migration_plan` | Sealed one-time legacy source disposition and exact final targets | Adapter only; resume dispatches migration recovery and ordinary work refuses while present |

## Missing Target Files And Executable Support

These do not exist today:

| Proposed file | Responsibility |
|---|---|
| `references/package-schema.yaml` | Sole executable authority for generated areas, paths/patterns, file roles, producers, cardinality, writers, authority/lifecycle, loading, cleanup, and contract/guide keys |
| `references/file-contracts.json` | Sole strict machine catalog for role parser, structural shape, deterministic checks and ID-scan mode |
| `references/file-guide.yaml` | Sole concise AI-facing role purpose and usage catalog, joined on demand by the Package Controller |
| `references/architecture.md` | Stable current/planning/state/archive/authority model shared by the generator workflow |
| `references/id-schema.yaml` | Sole executable ID classification, format, content, definition-role-per-class, and relationship schema; never physical paths |
| `references/specification-and-tasking.md` | Consolidated semantic PRD/EARS/BDD/Test/Task transformation and slicing rules |
| `templates/00-current-id-index.template.yaml` | Shape for the per-package active-ID-only index; no owner locations or relationships |
| `templates/active-question.template.yaml` | Closed one-Q Record shape for `candidate/question.yaml` |
| `templates/candidate-discussion.template.md` | One replaceable active discussion surface; no authority or retained history |
| `templates/application-plan.template.yaml` | Closed basis/allocation-baseline/expected-final/exact-target shape; seal lives in Workflow State |
| `templates/decision-archive.template.yaml` | YAML multi-document compact question/decision cards, no Specification IDs |
| `templates/workflow-state.template.yaml` | Three-field phase/Q/sealed-Plan binding shape |
| `templates/task-state.template.yaml` | Single current Task lifecycle owner |
| `templates/id-allocation.template.yaml` | Six monotonic Feature-lifetime high-water integers for five Specification classes plus shared Q/DEC decision sequence; Controller-only |
| `templates/validation-result.template.json` | Latest-only typed VALID/INVALID/ERROR evidence with raw evaluated-checkpoint and generic transaction binding; produced by Validator |
| `templates/validator-attempt.template.json` | Active transaction repair count and previous evaluated checkpoint binding; produced by Validator |
| project-scope migration-plan contract | Temporary finite legacy source disposition and exact final-target plan, outside normal Feature transaction |
| Package Controller module | Resume, symbolic-ID reservation, seal, virtual apply, exact payload application, decision cleanup, explicit finish, repair transition, and qualification |
| Package Validator module | Read-only final Current/index/schema/reference/legacy/State legality plus atomic latest-result and attempt ownership; never readiness or workflow `pass` |
| Controller/Validator tests and fixtures | State/resume matrix, exact Plan, interruption, repair, cleanup, no-reuse, legacy residue, and qualification |

## Proposed Net Consolidation

The primary target is not a raw minimum file count. It is one owner per
responsibility and selective loading. The proposed source-level consolidation:

- add the target Package Schema plus the previously identified authority/template files;
- retire or merge 23 current files/templates that are pure duplicate control,
  historical indices, checklists, reports, or prompts;
- rewrite the remaining references/templates so they contain only their owned
  semantics or shape;
- keep active-work templates where needed, but garbage-collect their generated
  outputs after the result enters current state.

The most consequential removals are `00-stage-manifest`, permanent 14/15
governance, approved baseline copy, Gate checklists, final analysis report,
prompt files, permanent execution records, and dashboard-local lifecycle state.

## Closed Boundary Decisions

1. Keep one conditional `specification-and-tasking.md`; templates/File Contracts
   own shape and executable checks, so a second semantic reference is unnecessary.
2. Task State stores only the approved current execution boundary and lifecycle;
   detailed preflight is presented conversationally and is not another file.
3. Traceability renders on demand without persistence. Readiness is derived from
   Controller `pass` plus latest Validation Result and has no separate View/file.
4. Gate 2 meaning is represented only by applicable DESIGN/TEST Records; no
   artifact is required to exist merely because a legacy template existed.
5. Decision Archive cards have exactly `id` and `content.question/decision`.
