# Specification Package Architecture Blueprint

Status: proposed blueprint for confirmation; this document does not authorize
implementation.

## 1. Objective

Design a specification-package architecture in which:

1. AI can enter a feature and understand its current state immediately without
   loading the whole Skill, package, history, or schema.
2. Every file belongs to one unambiguous category and role.
3. Every filename, path, purpose, writer, lifecycle, and validation policy has
   one executable definition.
4. The directory tree is closed and depth-bounded. Neither AI nor humans may
   create arbitrary folders or unclassified files.

The central design rule is:

> The Package Schema is the blueprint. The Feature Package is one instance of
> that blueprint. Documentation explains the blueprint but never redefines it.

## 2. Evidence From The Current Repository

The current `spec-package-generator` has 59 source files and the paired
`implement-spec-task` has 7. The accepted responsibility inventory identifies
duplicated ownership across `SKILL.md`, workflow references, status, stage
manifest, output catalog, templates, checklists, readiness, dashboards, and
execution records.

The inspected `pre-booking` and `dimflow-work-assistant` feature packages are
currently flat at the feature root, with roughly 25-30 root files plus
`diagrams/`, `execution/`, `manifests/`, `prompts/`, and `tasks/`. There is no
machine-readable authority that proves whether a new filename or directory is
valid. This is why a scan cannot currently distinguish an approved artifact
from an accidental draft, obsolete history, or an AI-created folder.

This blueprint is therefore a migration target, not a description of the
current tree.

## 3. Two-Plane Architecture

Separate the architecture into a Skill Definition Plane and a Feature Instance
Plane.

```text
Skill Definition Plane
  package-schema.yaml  ------+
  file-contracts.json          |
  file-guide.yaml              |
  id-schema.yaml               |
  architecture.md              | creates, explains, validates
  workflow.md                  |
  Package Controller           |
  Package Validator            |
                               v
Feature Instance Plane
  current specification and execution inputs
  temporary Candidate recovery data
  cold Decision Cards
  current workflow/validation control data
```

### 3.1 Skill Definition Plane

This plane is installed once with the Skill. It owns the rules shared by every
generated feature and is not copied into each feature.

Proposed source layout:

```text
skills/engineering/spec-package-generator/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- package-schema.yaml
|   |-- file-contracts.json
|   |-- file-guide.yaml
|   |-- id-schema.yaml
|   |-- architecture.md
|   |-- workflow.md
|   `-- <conditional semantic policies only>
|-- templates/
|   `-- <templates referenced by role from package-schema.yaml>
`-- scripts/
    `-- <Package Controller and Package Validator entrypoints>
```

`references/package-schema.yaml` is the single bootstrap definition. Its
location is resolved relative to the installed Skill root. That relative
bootstrap path is the only physical convention that exists outside the schema;
repository validation must test it.

### 3.2 Feature Instance Plane

This plane contains one feature's live data. It never contains a writable copy
of the Package Schema or ID Schema. Its complete structure is derived from the
Skill Definition Plane.

The four top-level Feature areas are accepted by DEC-042. The child layout shown
below remains a blueprint proposal until its individual authority categories are
confirmed:

```text
.ai-dev/features/<feature>/
|-- current/
|   |-- id-index.yaml
|   |-- records/
|   |   |-- requirements.yaml
|   |   |-- bdd.yaml
|   |   |-- design.yaml
|   |   |-- tests.yaml
|   |   `-- tasks.yaml
|   |-- manifests/
|   |   `-- <TASK-ID>.yaml
|   `-- views/
|       `-- dashboard.html
|-- candidate/
|   |-- question.yaml
|   |-- discussion.md
|   |-- application-plan.yaml
|   `-- review.html
|-- history/
|   `-- decisions.yaml
`-- control/
    |-- workflow-state.yaml
    |-- task-state.yaml
    |-- id-allocation.yaml
    |-- validation-result.json
    `-- validator-attempt.json
```

The four root names and their closed-world status are accepted; proposed child
paths become authoritative only after they are individually confirmed and
encoded in `package-schema.yaml`. No prose-only diagram can authorize a path.

## 4. Authority Map

| Concern | Sole authority | Must not redefine it |
|---|---|---|
| Physical areas, paths, filenames, producer, permitted multiplicity, writer, authority, lifecycle, loading and cleanup | `package-schema.yaml` | `SKILL.md`, templates, workflow prose, architecture prose, generated files |
| File parser, structural shape and deterministic content-check profile | `file-contracts.json` | Package Schema, File Guide, templates, prose checklists |
| Concise AI-facing file purpose and use | `file-guide.yaml` | Package Schema, templates, output catalogs, workflow prose |
| ID classes, formats, record content shapes and relationship rules | `id-schema.yaml` | ID Index, Package Schema, templates, Markdown examples |
| Active ID membership | Feature `current/id-index.yaml` | definitions, traceability views, history |
| Current normative meaning | Schema-declared ID Record owner files | Index, views, Candidate, Decision Cards |
| Workflow order, state transitions, stop/resume and Gate behavior | `workflow.md` plus executable controller transitions | `SKILL.md`, status prose, templates |
| Current workflow phase and resumable progress facts | Feature `control/workflow-state.yaml` | Candidate notes, stage manifest, dashboard, persisted next-action prose |
| Monotonic REQ/BDD/DESIGN/TEST/TASK allocation high-water marks | Feature `control/id-allocation.yaml` | Active ID Index, Decision Archive, Git history, AI-selected suffixes |
| Retry enforcement and validation result | Validator-owned control files | AI-authored readiness Markdown, workflow prose |
| Historical questions and decisions | Feature `history/decisions.yaml` | Current artifacts, Candidate, status |
| Template field shape | One role-linked template | output catalog prose, `SKILL.md` |
| Executable validation behavior | Package Validator interpreting the schemas | checklists, dashboards, AI judgment |

The current `output-files.md` must not remain a second file/path/purpose catalog.
Its useful AI-facing purpose content moves into `file-guide.yaml` and is exposed
through a generated `describe` view; paths remain solely in Package Schema.

## 5. The Package Schema As The Core Blueprint

### 5.1 Responsibilities

The Package Schema declares:

- all allowed top-level areas;
- every closed file role;
- the one canonical path or anchored path pattern for that role;
- the maximum permitted multiplicity: singleton, repeated, or one-per-bound-ID,
  without requiring an instance to exist;
- the only allowed writer;
- whether it is normative, routing, mutable state, Candidate, cold history, or
  derived output;
- whether it is loaded normally, conditionally, explicitly, or never as AI
  specification context;
- its persistence and cleanup trigger;
- its source template or programmatic generator, if any;
- its one File Contract key and one File Guide key;
- its maximum path depth and permitted dynamic placeholder bindings.

It does not own parser/check details, AI-facing purpose text, ID content meaning,
or workflow sequencing.

It defines where a role may exist and how many instances are legal; it does not
say that an instance must currently exist. Output completion belongs to the
Controller and Workflow State Center, not the Validator.

### 5.2 Proposed Schema Shape

```yaml
schema_version: 1

package:
  root_policy:
    closed_world: true
    exact_case: true
    reject_symlinks: true
    reject_empty_directories: true
    max_directory_depth: 2
    recursive_wildcards: forbidden

areas:
  current:
    path: current
    authority_scope: managed_current
    unknown_files: reject
  candidate:
    path: candidate
    authority_scope: temporary_non_authoritative
    unknown_files: reject
  history:
    path: history
    authority_scope: cold_non_authoritative
    unknown_files: reject
  control:
    path: control
    authority_scope: operational_state
    unknown_files: reject

roles:
  current_id_index:
    area: current
    path: id-index.yaml
    multiplicity: singleton
    writer: package_controller
    authority: active_id_membership
    load_policy: routed
    lifecycle: persistent_current
    contract: current_id_index_v1
    guide: current_id_index

  requirement_records:
    area: current
    path: records/requirements.yaml
    multiplicity: singleton
    writer: package_controller
    authority: normative
    load_policy: impact_selected
    lifecycle: persistent_current
    contract: requirement_records_v1
    guide: requirement_records

  task_manifest:
    area: current
    path_pattern: manifests/{task_id}.yaml
    placeholder_bindings:
      task_id: TASK
    multiplicity: one_per_bound_id
    writer: package_controller
    authority: routing
    load_policy: selected_task_only
    lifecycle: while_id_active
    contract: task_manifest_v1
    guide: task_manifest

  candidate_discussion:
    area: candidate
    path: discussion.md
    multiplicity: singleton
    writer: package_controller
    authority: candidate
    load_policy: active_transaction_only
    lifecycle: active_transaction
    cleanup: after_owning_transaction_commit
    contract: candidate_discussion_v1
    guide: candidate_discussion

  candidate_application_plan:
    area: candidate
    path: application-plan.yaml
    multiplicity: singleton
    writer: package_controller
    authority: candidate
    load_policy: active_transaction_only
    lifecycle: active_transaction
    cleanup: after_owning_transaction_commit
    contract: candidate_application_plan_v1
    guide: candidate_application_plan

  active_question:
    area: candidate
    path: question.yaml
    multiplicity: singleton
    writer: package_controller
    authority: candidate
    load_policy: active_transaction_only
    lifecycle: active_transaction
    cleanup: after_owning_transaction_commit
    contract: active_question_v1
    guide: active_question

  decision_archive:
    area: history
    path: decisions.yaml
    multiplicity: singleton
    writer: package_controller
    authority: cold_history
    load_policy: explicit_history_request_only
    lifecycle: retained_cold
    contract: decision_archive_v1
    guide: decision_archive

  workflow_state:
    area: control
    path: workflow-state.yaml
    multiplicity: singleton
    writer: package_controller
    authority: mutable_state
    load_policy: first_read
    lifecycle: latest_state_only
    contract: workflow_state_v1
    guide: workflow_state

  validation_result:
    area: control
    path: validation-result.json
    multiplicity: singleton
    writer: package_validator
    authority: validation_evidence
    load_policy: qualification_only
    lifecycle: latest_result_only
    contract: validation_result_v1
    guide: validation_result
```

`after_owning_transaction_commit` is a closed trigger, not a generic phase name.
Question owns its Q/discussion/review and question-basis Plan through DEC binding
clear; validation repair owns its validation-basis Plan and attempt through
matching VALID commit; migration owns only its project-scope Plan and child
repair data through the verified migration cleanup marker. One transaction may
never delete another transaction's residue.

The YAML above demonstrates field shape. The complete retained persisted-role
catalog is closed to the following rows; every row has a same-name File Guide
key and a versioned File Contract key:

| `file_role` | Scope and canonical path/pattern | Multiplicity | Writer | Authority / lifecycle |
|---|---|---|---|---|
| `current_id_index` | Feature `current/id-index.yaml` | singleton | Package Controller | active membership / persistent Current |
| `requirement_records` | Feature `current/records/requirements.yaml` | singleton | Package Controller | normative / persistent Current |
| `bdd_records` | Feature `current/records/bdd.yaml` | singleton | Package Controller | normative / persistent Current |
| `design_records` | Feature `current/records/design.yaml` | singleton | Package Controller | normative / persistent Current |
| `test_records` | Feature `current/records/tests.yaml` | singleton | Package Controller | normative / persistent Current |
| `task_records` | Feature `current/records/tasks.yaml` | singleton | Package Controller | normative / persistent Current |
| `task_manifest` | Feature `current/manifests/{task_id}.yaml` | one per active TASK | Package Controller | routing / while ID active |
| `dashboard_view` | Feature `current/views/dashboard.html` | singleton | User View Renderer | derived view / latest view only |
| `active_question` | Feature `candidate/question.yaml` | singleton | Package Controller | Candidate / active transaction |
| `candidate_discussion` | Feature `candidate/discussion.md` | singleton | Package Controller | Candidate / active transaction |
| `candidate_application_plan` | Feature `candidate/application-plan.yaml` | singleton | Package Controller | Candidate / active transaction |
| `candidate_review` | Feature `candidate/review.html` | singleton | User View Renderer | Candidate view / active transaction |
| `decision_archive` | Feature `history/decisions.yaml` | singleton stream | Package Controller | cold history / retained cold |
| `workflow_state` | Feature `control/workflow-state.yaml` | singleton | Package Controller | mutable state / latest state only |
| `task_state` | Feature `control/task-state.yaml` | singleton | Task Execution Controller | mutable state / latest state only |
| `id_allocation_state` | Feature `control/id-allocation.yaml` | singleton | Package Controller | mutable state / monotonic Feature state |
| `validation_result` | Feature `control/validation-result.json` | singleton | Package Validator | validation evidence / latest result only |
| `validator_attempt` | Feature `control/validator-attempt.json` | singleton | Package Validator | mutable attempt / active transaction |
| `project_context` | Project `.ai-dev/context/project-context.md` | singleton | Project Context Controller | external current / persistent current |
| `project_rule_source` | Project `.ai-dev/context/implementation-rules.md` | singleton | Project Context Controller | external current / persistent current, only when no existing rule owner applies |
| `migration_plan` | Project `.ai-dev/migrations/{feature}.yaml` | one per migrating Feature | Migration Adapter | Candidate migration / active migration only |

There is no other persisted runtime role. Traceability, analysis, convergence,
implementation evidence, context proposal, Work Unit Brief, and detailed
preflight are declared producer outputs with `persistence: none`, so they have no
filesystem path. The 43-source migration disposition and producer tables in the
responsibility inventory prove how legacy templates reach this catalog.

Executable catalogs use one closed snake-case writer vocabulary:
`package_controller`, `task_execution_controller`, `package_validator`,
`user_view_renderer`, `migration_adapter`, and `project_context_controller`.
Title-case table labels denote those keys; they are not additional writer values
or sub-authorities.

### 5.3 Package Schema Meta-Validation

The Validator must reject the Package Schema itself before inspecting a feature
when any of these hold:

- unknown schema keys or enum values;
- duplicate role names;
- missing area, path/pattern, permitted multiplicity, writer, authority, load
  policy, lifecycle, contract key, or guide key;
- absolute paths, `..`, drive letters, URI paths, or paths escaping the role's
  declared Feature/Project scope root;
- overlapping exact paths or path patterns;
- an unanchored pattern or recursive `**` pattern;
- a Feature-scope dynamic placeholder not bound to an active ID class, or a
  project-scope migration placeholder not bound to the validated Feature slug;
- a dynamic directory placeholder rather than a leaf filename placeholder;
- a path deeper than its declared maximum;
- a template referenced by zero roles or multiple incompatible roles;
- a role whose File Contract or File Guide key does not resolve exactly once;
- a role that can be classified as more than one authority category.

This is a Validator `ERROR`, not a feature `INVALID`, because the blueprint
itself cannot be trusted.

### 5.4 Closed Output-Producer Coverage

The Package Schema must cover not only files already present in a Feature
Package, but every mechanism capable of producing a file.

The current repository has 39 templates under `spec-package-generator` and 4
under `implement-spec-task`. The responsibility inventory now maps all 43
exactly once to the closed retained-role catalog above or to `persistence: none`/
retirement. Repository validation must make that table executable before source
templates are removed.

Every final output role must declare exactly one producer:

```yaml
roles:
  dashboard_view:
    area: current
    path: views/dashboard.html
    authority: derived_view
    load_policy: explicit_user_review_only
    contract: dashboard_view_v1
    guide: dashboard_view
    producer:
      kind: template
      source: templates/36-final-dashboard.template.html

  task_manifest:
    area: current
    path_pattern: manifests/{task_id}.yaml
    contract: task_manifest_v1
    guide: task_manifest
    producer:
      kind: template
      source: templates/task-execution-manifest.template.yaml

  traceability_output:
    persistence: none
    contract: traceability_output_v1
    guide: traceability_output
    producer:
      kind: programmatic
      generator: traceability_renderer

  work_unit_brief:
    persistence: none
    contract: work_unit_brief_v1
    guide: work_unit_brief
    producer:
      kind: template
      source: ../implement-spec-task/templates/work-unit-brief.template.md
```

The producer entry points to an output role; it does not repeat the output path.
The role remains the only path/purpose authority. A template contains field
shape and placeholders only and cannot select or override its destination.

Coverage rules:

1. Repository validation inventories every file under both Skills' declared
   template roots and every registered programmatic generator.
2. Every retained template maps to exactly one output role.
3. One template may generate repeated instances of that one role only when the
   role path pattern is bound to an active ID.
4. Every persisted programmatic output maps to exactly one output role.
5. A non-persistent renderer still has a declared role with
   `persistence: none`; it may not leave a file in the Feature Package.
6. A role cannot name both a template and a programmatic generator unless one is
   explicitly a renderer of the other's in-memory result and the schema defines
   which producer owns the persisted bytes.
7. No template may embed a canonical output path, create a directory, or choose
   a filename from prose instructions.
8. A producer that emits an undeclared path is a hard failure even when the file
   contents are otherwise valid.
9. A retained template absent from the Package Schema is a repository error.
10. A Package Schema producer reference whose template/generator is absent is a
    repository error.

Retired templates must not be kept in the final Package Schema merely so the
coverage check passes: that would legitimize obsolete outputs. The finite
43-row responsibility matrix already classifies every source with the closed
enum `rewrite`, `merge_replace`, `render_none`, `retire`, or `external_current`.
`rewrite` is the sole retained template producer for a target; multiple legacy
sources reach one replacement only through `merge_replace`. Implementation turns that
matrix into an exact-once repository check; after replacement behavior is
verified, retired sources are deleted and every remaining producer maps to one
valid role.

### 5.5 Accepted Three-Layer File Knowledge Model

File knowledge is split into three focused layers so AI and the Validator do not
need one oversized definition. Every layer joins through the same closed
`file_role` key and no field has two owners.

```text
package-schema.yaml
  file_role -> canonical name/path, producer, permitted multiplicity, writer, authority,
               lifecycle, contract key, guide key
                         |
                         +--> file-contracts.json
                         |      contract key -> parser and deterministic checks
                         |
                         `--> file-guide.yaml
                                guide key -> concise AI-facing purpose and use
```

#### Layer 1: Physical File Definition

`package-schema.yaml` remains the bootstrap and physical architecture core. It
answers:

- which role exists;
- which template or programmatic producer creates it;
- its one canonical filename/path or ID-bound leaf pattern;
- whether an existing instance is singleton, repeated, or one-per-bound-ID;
- who may write it;
- its authority and lifecycle;
- which validation contract and AI guide entry apply.

It must not duplicate the contract rules or explanatory purpose text.

```yaml
roles:
  workflow_state:
    path: control/workflow-state.yaml
    producer: package_controller
    multiplicity: singleton
    writer: package_controller
    authority: mutable_state
    lifecycle: latest_state_only
    contract: workflow_state_v1
    guide: workflow_state
```

#### Layer 2: Validator File Contract

The proposed `file-contracts.json` is a strict machine catalog. It answers how
the Validator parses and checks bytes after Layer 1 classifies a path.

```json
{
  "contract_version": 1,
  "contracts": {
    "workflow_state_v1": {
      "parser": "yaml",
      "shape": {
        "type": "object",
        "required": [
          "phase",
          "active_question",
          "plan_fingerprint"
        ],
        "additionalProperties": false,
        "properties": {
          "phase": {
            "type": "string",
            "enum": [
              "discussing",
              "planning",
              "applying_current",
              "validating",
              "finalizing",
              "pass"
            ]
          },
          "active_question": {
            "type": ["string", "null"],
            "pattern": "^Q-[0-9]{3}$"
          },
          "plan_fingerprint": {
            "type": ["string", "null"],
            "pattern": "^sha256:[0-9a-f]{64}$"
          }
        }
      },
      "id_scan": "structured_only"
    },
    "managed_markdown_v1": {
      "parser": "markdown",
      "required_sections": ["Scope"],
      "id_scan": "in_content_markers"
    }
  }
}
```

This is a small declarative contract language represented as strict JSON, not
an assumption that standard JSON Schema alone can validate Markdown, Gherkin,
HTML, Mermaid, YAML multi-document streams, and cross-file ID relationships.
The Validator meta-validates the catalog, rejects duplicate JSON keys and
unknown contract fields, then dispatches to built-in parsers/check primitives.

It contains no output paths, producer names, lifecycle, or purpose prose.

#### Layer 3: AI File Guide

The proposed `file-guide.yaml` is the concise semantic catalog. It answers why a
role exists and when AI needs it.

```yaml
roles:
  workflow_state:
    purpose: Resume the one active specification transaction.
    ai_use: Read first through Controller resume output; never use as specification meaning.
```

It contains no canonical path, filename pattern, parser rule, field schema,
producer, or lifecycle rule. Those remain in Layers 1 and 2.

#### Joined Controller View

AI normally reads none of the three catalogs directly. `package resume` and
`package explain-role` join them by `file_role` and return only the selected
role:

```yaml
role: workflow_state
path: control/workflow-state.yaml
purpose: Resume the one active specification transaction.
ai_use: Read first through Controller resume output; never use as specification meaning.
format: yaml
writer: package_controller
```

Cross-layer validation must prove:

1. every Package Schema role resolves to exactly one contract and one guide;
2. every guide role resolves to exactly one Package Schema role;
3. every contract is used by at least one role unless explicitly declared as a
   reusable abstract contract;
4. no layer contains fields owned by another layer;
5. role and contract identifiers use closed formats and exact case;
6. a missing, unknown, or cyclic reference is a schema `ERROR`;
7. the joined role view can always provide path, purpose and validation format
   without scanning templates or generated feature files.

The ID Schema remains a separate orthogonal authority. It maps each ID class to
one `file_role`; Layer 1 resolves the role to a path and Layer 2 supplies the
file contract.

## 6. Relationship Between Package Schema And ID Schema

Physical locations must not be duplicated.

The ID Schema refers only to a role:

```yaml
classes:
  REQUIREMENT:
    scope: current
    id_pattern: '^REQ-[0-9]{3}$'
    allocation_counter: REQ
    definition_role: requirement_records
    content_schema: <class-specific shape>
  BDD:
    scope: current
    id_pattern: '^BDD-[0-9]{3}$'
    allocation_counter: BDD
    definition_role: bdd_records
    content_schema: <class-specific shape>
  DESIGN:
    scope: current
    id_pattern: '^DESIGN-[0-9]{3}$'
    allocation_counter: DESIGN
    definition_role: design_records
    content_schema: <class-specific shape>
  TEST:
    scope: current
    id_pattern: '^TEST-[0-9]{3}$'
    allocation_counter: TEST
    definition_role: test_records
    content_schema: <class-specific shape>
  TASK:
    scope: current
    id_pattern: '^TASK-[0-9]{3}$'
    allocation_counter: TASK
    definition_role: task_records
    content_schema: <class-specific shape>
  QUESTION:
    scope: candidate_control
    id_pattern: '^Q-[0-9]{3}$'
    allocation_counter: DECISION
    definition_role: active_question
    content_schema:
      type: object
      required: [question, answer]
      additionalProperties: false
      properties:
        question: {type: string, minLength: 1, maxLength: 1000}
        answer: {type: [string, 'null'], minLength: 1, maxLength: 2000}
  DECISION:
    scope: cold_history
    id_pattern: '^DEC-[0-9]{3}$'
    allocation_counter: DECISION
    definition_role: decision_archive
    content_schema: {question: string, decision: string}
```

The same ID Schema declares a `001..999` allocation range for the five Current
classes and shared Q/DEC decision sequence, plus a closed rejected-pattern
catalog for migration residue.
The initial required rejected shapes are `FR-nnn`, `EARS-nnn`, `SCN-nnn`,
`OQ-nnn`, `PRJ-nnnn`, `AC-nnn`, `SCR-nnn`, typed question forms such as
`Q-BIZ-nnn`, and typed test
forms such as `TEST-UNIT-nnn`, `TEST-CONTRACT-nnn`, or any other
`TEST-<TYPE>-nnn`. `BDD-SCENARIO-nnn` is likewise rejected. These are lexical
rules, not retained instances. Scope-aware scanning permits such values in the
active Candidate during migration but rejects them in final normative/routing
Current and in Decision Card content. YAML comments are prohibited in all
authoritative/routing Current files and the Decision Archive so parser-discarded
text cannot hide stale IDs. Candidate discussion/review is excluded; allocation
checks inspect only structured Q subjects and Plan targets/payloads, never
arbitrary Candidate prose.

Legacy matching is ASCII-case-sensitive and requires both sides to be outside
`[A-Z0-9-]`; it therefore rejects a complete legacy token without matching a
substring inside prose, paths, hashes, or a longer identifier. The initial
catalog is derived from both inspected Feature Packages and current source
templates. A newly observed legacy shape changes ID Schema and fixtures, not a
retained list of ID instances.

The Package Schema alone maps `requirement_records` to
`current/records/requirements.yaml`.

The resolution chain is:

```text
ID class
  -> definition role                 (ID Schema authority)
  -> canonical role path             (Package Schema authority)
  -> actual file discovered by scan  (Validator-derived fact)
```

The Current ID Index contains only active REQ, BDD, DESIGN, TEST, and TASK IDs.
It records neither the role nor the path. Q and DEC remain schema-governed IDs
but are invalid in Current and never enter its index or normative graph. PRD and
EARS are renderings of REQ meaning rather than separate identity classes. Test
level and Task type live in their class-specific content, not their ID prefixes.

Its complete closed shape is one unique canonical list:

```yaml
ids:
  - REQ-001
  - BDD-001
  - DESIGN-001
  - TEST-001
  - TASK-001
```

ID Schema derives class; the Index does not repeat class buckets, locations,
relationships, status, or counters. Controller regenerates it from the virtual
final definition set while applying a Plan. Validator requires exact set equality
with discovered Current definitions and canonical class/numeric ordering.

`control/id-allocation.yaml` independently stores only:

```yaml
highest_issued:
  REQ: 0
  BDD: 0
  DESIGN: 0
  TEST: 0
  TASK: 0
  DECISION: 0
```

Controller is its sole writer. The five Specification counters serve Plan
allocation; `DECISION` serves the shared transient-Q/cold-DEC suffix without
making History an allocation input. AI submits symbolic new-ID handles rather than
choosing numeric suffixes. During Plan assembly, Controller snapshots all five
high-water values as the Plan's `allocation_baseline`, validates the symbolic
operation set, reserves every required ID in one atomic counter replacement,
substitutes the reserved IDs throughout targets and payload references, and only
then writes the complete Plan. A crash after reservation burns a gap; counters
never decrement, fill gaps, or wrap. `999` fails closed pending an ID Schema
migration. The file is Controller-only context, not history, and stores no old
ID instance.

At seal, absent-to-present Record IDs for each class must equal the exact
contiguous range above that Plan's baseline through the current reserved
high-water. This is the persisted proof that a low deleted suffix was not
reused. Direct AI-selected numeric IDs are rejected. Replacing an unsealed Plan
may retain reservations only when symbolic bindings and per-class cardinalities
are unchanged; otherwise the old reservation remains burned and Controller
reserves a fresh range.

Validator checks the allocator's closed six-counter shape; active Specification
IDs and structured Candidate subjects/Plan payload IDs may not exceed their
class high-water, while every structured Q/DEC definition/reference suffix may
not exceed `DECISION`. The one active Q created by the supported flow must equal
the currently reserved `DECISION` suffix, and Finalizer requires Q/DEC suffix
identity before append. Validator never
requires an absent file, but Controller creates the all-zero allocator before a
new Feature's first Q and requires it for every initialized Feature and every
workflow `pass`, even when the active ID set is empty.

This guarantees no reuse through the supported Controller workflow after
migration. It cannot prove IDs deleted before migration or resist an actor with
the same filesystem authority deleting/rolling back allocation, State, and
validation evidence together. That hostile/direct-writer guarantee would need a
separately protected broker or database and remains outside the MVP.

### 6.1 Minimum Current Record Content Schemas

Every YAML stream document still has exactly the common fields `id` and
`content`; the following closed class-specific `content` shapes are the minimum
viable contract:

```yaml
REQ:
  content: {statement: <non-empty string>}

BDD:
  content:
    scenario: <non-empty string>
    given: [<non-empty string>, ...]
    when: [<non-empty string>, ...]
    then: [<non-empty string>, ...]
    requirements: [REQ-nnn, ...]

DESIGN:
  content:
    decision: <non-empty string>
    requirements: [REQ-nnn, ...]

TEST:
  content:
    method: automated | semi-automated | manual
    verifies: [<REQ|BDD|DESIGN ID>, ...]
    entry_point: <non-empty command or inspection seam>
    pass_criteria: <non-empty string>

TASK:
  content:
    title: <non-empty string>
    outcome: <non-empty observable result>
    covers: [<REQ|BDD|DESIGN|TEST ID>, ...]
    depends_on: [TASK-nnn, ...]
```

All object shapes reject extra keys. Every listed array preserves authored order,
rejects duplicates, and is non-empty except `TASK.depends_on`, which may be an
empty array. `given/when/then` each require at least one item. Every ID-valued
field is an in-content edge whose allowed target classes are shown above; no
document-end references duplicate it. Task dependency self-edges and cycles are
invalid. Classification such as test method lives inside the owning content,
never in the ID prefix. Supporting prose that does not need reference is kept in
Candidate discussion or a User View rather than adding optional fields to every
Record.

These shapes guarantee syntactic traceability without pretending to prove that
the chosen relationships or natural-language meaning are semantically correct.
Gate review owns that judgment; the Validator owns shape, target class,
existence, uniqueness, and cycle/cardinality rules.

Q and DEC use the allocator's one feature-local `DECISION` sequence. Controller
atomically reserves the next suffix before creating `Q-nnn`; successful question
finalization appends `DEC-nnn` with the identical reserved suffix before deleting
Q. A canceled/crashed reservation is a permanent harmless gap. Normal allocation
never scans History IDs or content, so the cold archive cannot control resume,
readiness, or the next sequence value. Migration initializes `DECISION` from the
greatest observable Q/DEC suffix and any trusted User floor.

## 7. Category Model

Every role has exactly one authority category and one lifecycle. Closed enums
prevent similar words from creating ambiguous categories.

### 7.1 Authority Categories

| Category | Meaning | Normal AI use |
|---|---|---|
| `normative` | Owns current specification meaning | Impact-selected only |
| `routing` | Selects immutable execution inputs without redefining behavior | Selected Task only |
| `mutable_state` | Owns current workflow or Task lifecycle | First-read or qualification only |
| `validation_evidence` | Validator-owned result for one exact Current fingerprint | Qualification only |
| `candidate` | Temporary non-authoritative discussion and application recovery | Active transaction only |
| `cold_history` | Compact material question and decision | Explicit historical request only |
| `derived_view` | Regenerable human display with no authority | On demand |

No role may be both normative and derived, both Candidate and history, or both
AI-authored and Validator-owned.

### 7.2 Lifecycles

| Lifecycle | Retention rule |
|---|---|
| `persistent_current` | Retain while its current role exists |
| `while_id_active` | Exactly one leaf file per active bound ID; delete with the ID |
| `active_transaction` | Retain only until the active transaction finalizes or is explicitly abandoned |
| `latest_state_only` | Replace; never append a state timeline |
| `monotonic_feature_state` | Retain for the Feature lifetime; atomically increase declared counters only and never delete during ordinary cleanup |
| `latest_result_only` | Replace; never accumulate old VALID/INVALID results |
| `latest_view_only` | Retain one canonical User Review View and atomically replace it only when new information must be shown; never create View history |
| `retained_cold` | Append compact Decision Cards to the one archive stream |
| `generated_on_demand` | Do not persist unless the schema explicitly requires it |

## 8. Bounded Feature Tree And Growth Rules

The target is not merely a tidy initial tree. It must remain bounded under
repeated AI work.

### 8.1 Hard Structural Rules

1. The feature root is closed-world. Every file must match exactly one role.
2. Every directory must be the parent of at least one schema-declared role.
3. Maximum directory depth is fixed by the Package Schema; the proposed default
   is two directories below the feature root.
4. Recursive wildcards and arbitrary nested directories are forbidden.
5. Dynamic placeholders may appear only in leaf filenames, never directory
   names.
6. Every dynamic placeholder is bound to an active ID class. A file whose bound
   ID is absent from the Current ID Index is invalid.
7. Empty directories, symlinks, Windows junctions/reparse-point escapes, and
   case-variant duplicates are rejected.
8. Unknown hidden files such as `.keep`, editor scratch files, exported review
   copies, and ad hoc notes are not silently ignored.
9. A role may define one exact path or one anchored pattern, never competing
   alternatives.
10. A new directory requires an intentional Package Schema change, schema
    meta-validation, repository tests, and human confirmation. Creating a folder
    inside a feature never changes the architecture.

### 8.2 Growth By Area

`current/records/` is finite: one YAML multi-document stream per closed ID
class. Adding records grows file content, not directories or one-file-per-ID
sprawl.

`current/views/` is finite and User-facing only: only fixed singleton User Review
View roles declared in the Package Schema may exist. Every View is generated
one-way from validated Records, is non-authoritative, and is excluded from normal
AI generation and Implementation read sets. User feedback returns through
Candidate and changes Records before regeneration; direct View edits never alter
specification meaning.

Each declared User Review View uses the `latest_view_only` lifecycle. Confirmation
does not delete it. The renderer atomically overwrites the same canonical file
only when new information must be shown to the User. Dated, versioned, copied,
append-only, or per-review View files are forbidden. This makes `views/` a bounded
latest-snapshot cache rather than a second history store. A retained snapshot may
remain stale while it is not being presented. Its bytes and ID occurrences are
excluded from the normative Current fingerprint and removed-ID occurrence gate.
The Validator still checks its canonical role, singleton multiplicity, parseable
format, non-authoritative marker, and source-fingerprint shape. Before display or
confirmation, the Controller compares that fingerprint with the source Records
and atomically replaces the same file on mismatch. Confirmation binds to the
displayed fingerprint and fails if the source changes during review.

Views do not need a visible stale or non-authoritative notice. Opening a retained
View directly from the filesystem is therefore a freshness-unverified convenience,
not a supported confirmation path. The machine-readable source fingerprint
remains mandatory, and only Controller-mediated display or confirmation guarantees
that it was refreshed against its source Records.

The minimum package retains one `current/views/dashboard.html` singleton. Its
only purpose is to let the User see the Task count, briefly understand Task
slicing, and copy a Manifest-backed execution Prompt. It is read-only and owns
no lifecycle state, readiness, task status, specification meaning, or execution
eligibility. It displays exactly feature name, total Task count, dependency/order
summary, and one card per Task with Task ID, title, one-sentence outcome,
dependency IDs, Task link, Manifest link, and a copy button for
`$implement-spec-task <manifest-path>`. Mutable Task status, `localStorage`,
status export, readiness, paths, tests, evidence, traceability, risks, and full
acceptance content are forbidden. Detailed review follows the Task link; current
eligibility is enforced by Controller and Implementation preflight.

Non-user-facing derived data does not belong in `views/`. It renders without
persistence unless an independently justified Package Schema role is confirmed.
No generic `artifacts/`, `generated/`, or catch-all output directory is allowed.

`current/manifests/` may grow only one leaf file per active Task ID. Removal of
the Task ID requires removal of its Manifest. No Task subdirectory is allowed.

Each existing Manifest is immutable routing with this closed minimum shape:

```yaml
task_id: TASK-001
task_fingerprint: sha256:<canonical-TASK-record>
read_ids: [REQ-001, BDD-001, DESIGN-001, TEST-001, TASK-001]
write_scope: [src/feature/**]
read_only_scope: [src/shared/**]
test_ids: [TEST-001]
validation_commands: [<non-empty command>, ...]
```

`read_ids` is Controller-derived from the Task's schema graph and is checked
against Current rather than becoming another normative relationship owner.
`test_ids` is the TEST subset selected from that graph. Scopes are normalized
project-relative anchored patterns; absolute paths, parent traversal and an
overlap between write/read-only scopes are invalid. Manifest contains no Task
meaning, lifecycle, approval, evidence, prompt, timestamps, mutable digest, or
copied acceptance prose. Its filename, `task_id`, and TASK Record agree. Any
Current graph change replaces the frozen TASK ID/Manifest rather than mutating a
previously sealed Manifest in place.

`candidate/` has a fixed file set and no subdirectories. The sole active Q
definition lives in `question.yaml`; Workflow State, the application plan and
permitted recovery notes may reference its ID but cannot redefine it. Multiple
interrupted discussion segments live in the one active `discussion.md`; machine
progress lives in the one `application-plan.yaml`. Only one transaction is
active because the workflow asks and applies one material question at a time.

Within the Q's two-field content, every Current Specification ID token in
`content.question` is a declared change subject, not a context citation.
Context-only IDs belong in `discussion.md`. Before asking for the answer,
Controller extracts and displays the subject set plus each subject's reverse
dependents; pure-add questions may declare no existing subject. The bounded
question and answer strings have File-Contract maximum lengths. An answer may
not introduce a Current Specification ID that was not already declared in the
question. If it does, Controller returns to discussion, presents the enlarged
subject set in the question, clears the answer, and asks for confirmation again.
At Plan seal, every subject must have exactly one Record operation. Because every
subject in an initialized package is frozen, it must be `present -> absent`.
This adds no `affected_ids` field and no old-to-new map while preventing AI from
confirming a named old ID and then omitting its removal operation.

The contract cannot infer a missing semantic subject from arbitrary prose. The
User/AI still chooses the subject IDs during the visible question; after that
choice, subject coverage and all schema-encoded reverse references are
mechanical.

`application-plan.yaml` is assembled and atomically written by Controller from
AI-supplied exact symbolic operations, then sealed before Current application.
AI supplies each complete after payload once but never chooses numeric IDs,
writes a physical path, or writes Controller-computed baseline/fingerprint
fields. The Plan contains one closed basis, the allocator baseline, an unordered
logical set of exact deltas for impacted Records or declared files, and the
expected final authoritative Current fingerprint. Array position carries no
progress, dependency, priority, or correctness meaning; Controller serializes
the unique canonical targets deterministically only to stabilize the sealed Plan
fingerprint.

Its top level is closed to exactly these four fields:

```yaml
basis:
  kind: question
  id: Q-042
  fingerprint: sha256:<canonical-complete-answered-question-record>
allocation_baseline:
  REQ: 12
  BDD: 8
  DESIGN: 4
  TEST: 9
  TASK: 5
expected_final_current_fingerprint: sha256:<virtual-final-current>
operations:
  - target:
      record_id: REQ-014
    before:
      state: present
      fingerprint: sha256:<canonical-record-target>
    after:
      state: absent
```

`basis` is exactly one of two closed variants. `kind: question` requires the Q
`id` and fingerprint of the complete parsed answered `question.yaml`, not only
its answer. `kind: validation` instead requires the canonical fingerprint of the
latest full `INVALID` Validation Result and is used only for deterministic final
validation repair; it has no Q and creates no Decision Card. The Plan may exist
in `planning` as one complete but still replaceable file. Presence does not seal
it. Only a State `plan_fingerprint` equal to the canonical logical hash of all
four top-level fields seals it. The Plan then becomes immutable until Controller
explicitly invalidates the seal after a deterministic `INVALID` result.

Every operation uses the same `target` / `before` / `after` envelope. An
authoritative Record target stores only `record_id`; ID Schema derives its owner
role and Package Schema resolves its file. A fixed declared-file target stores
only `file_role`. The MVP's dynamic Task Manifest stores
`file_role: task_manifest` plus `task_id`. Raw paths, a generic key/binding field,
duplicated Record owner role, operation kind, progress field, and `OP-nnn` are
forbidden.

`before` and `after` are closed state objects. `state: absent` permits no other
field. `before.state: present` requires the target-scoped canonical fingerprint;
`after.state: present` requires the complete expected payload and does not store
a second derived fingerprint. Creation, update, and removal are derived from
those state pairs. Vague instructions and a complete copied Candidate
specification are illegal. The Plan is temporary, non-authoritative, and deleted
after finalization.

`absent -> absent` and a canonical `present -> present` no-op are illegal.
For a Record target, every present after payload is exactly one `{id, content}`
Record whose `id` equals `target.record_id`. For a Task Manifest target, the
payload's Task binding equals `target.task_id`. All extra fields, ambiguous YAML
types, duplicate canonical targets, and target/payload disagreement fail before
sealing. `operations` may be empty only for an explicitly answered no-Current-
change decision; final expected fingerprint must then equal the baseline Current.

Each Record or declared file instance may be targeted by at most one operation;
multiple intended changes to the same target are consolidated before sealing.
Controller compares every operation independently with Current and derives an
ephemeral completed/pending/conflict summary. This correctly exposes non-prefix
results such as operations 1 and 3 complete while operation 2 remains pending.

Ordinary target fingerprints never hash a whole multi-record owner or raw YAML bytes. A
Record target hashes only its parsed `id`/`content` document; a declared
structured-file target hashes its complete parsed logical value. One shared
canonicalizer uses deterministic JSON-compatible serialization, sorted object
keys, preserved array order, UTF-8, no insignificant whitespace, and lowercase
`sha256:<64-hex>`. Unsupported YAML types are invalid rather than receiving
role-specific hashing behavior.

One closed validation-repair exception makes deterministic syntax repair
representable without weakening ordinary plans. If a declared structured role
cannot parse, `basis: validation` may target that whole `file_role`; its before
fingerprint is the domain-separated hash of exact raw invalid bytes and its
after payload is the complete valid logical file. Definition-owner roles may use
this whole-file target only in that malformed-input case. Question-basis Plans
and valid structured files never use raw fingerprints or whole-owner Record
replacement.

The sealed Plan additionally binds its basis, allocation baseline and one
`expected_final_current_fingerprint`. Controller computes the latter before the
first Current write by virtually applying every exact operation to the complete
normative/routing Current set; derived Views are excluded. Controller, not AI,
then applies the sealed payloads. When all targets classify complete, the actual
complete Current must equal the expected-final fingerprint before final
validation. This rejects an unlisted but structurally legal extra edit without a
full baseline snapshot. A mismatch cannot be repaired by guessing and requires
human recovery.

Do not add an `id_transitions` or old-to-new mapping. Controller derives removed
Record IDs from present-to-absent targets and added IDs from absent-to-present
targets, checks the removed IDs' reverse-reference closure at sealing, and
requires the virtual final graph to contain zero removed occurrences. Exact
dependent payloads already define the resulting references. A mapping would add
a second owner without changing application or residue-validation behavior.

Identity freeze is mechanical. Sealing a Plan freezes every Record in its
virtual-final authoritative Current, not only the Plan's explicit targets. A
validated workflow `pass` therefore also consists entirely of frozen Records.
Any later canonical content change must use remove-old/create-fresh operations.
If deterministic validation repair changes any Record in its invalid Current
baseline, the repair Plan uses another freshly allocated ID. Before first seal,
AI may resubmit changed symbolic operations and Controller atomically replaces
the unsealed Plan under the allocation rules above. This applies to all
REQ/BDD/DESIGN/TEST/TASK Records and deliberately makes semantic changes visible
through ID replacement rather than an unprovable Task implementation boundary.

`history/` has one YAML multi-document `decisions.yaml`; one Decision Card is
appended per confirmed material decision. No per-decision files or date folders
are created.

The minimum viable Decision Card has exactly this closed shape:

```yaml
---
id: DEC-001
content:
  question: <non-empty concise string>
  decision: <non-empty concise string>
```

`DEC-nnn` is an archive ID outside the Current ID Index. No date, Gate,
rationale, rejected alternative, consequence, optional metadata, Current or
removed Specification ID, transcript, or duplicated Current text is allowed.
Adding a field requires an explicit schema version and archive migration.

Because active Q question text may contain declared Specification subject IDs,
Finalizer uses a deterministic archive projection rather than AI paraphrase. It
replaces every Current or legacy Specification ID token in the already bounded Q
question/answer with the fixed phrase `the affected specification item(s)` and
normalizes whitespace only. Those exact projected strings become DEC
`question`/`decision`; lexical validation precedes the idempotent append. Replay
therefore produces identical bytes, while Current owns the concrete result and
History retains no old or new Specification ID.

`control/` has a fixed file set and no subdirectories. Workflow/Task state,
Specification ID allocation, the latest validation result, and the active
Validator attempt replace their prior contents rather than accumulating event
logs. ID allocation is the sole feature-lifetime monotonic exception: its six
integers only increase and are never reset during Candidate cleanup.

Writer authority and legality authority are intentionally separate. Controller
is the sole writer of `workflow-state.yaml`; File Contract declares its closed
field shapes and phase enum, and Validator rejects any illegal existing value.
Validator never selects a phase, edits Workflow State, or establishes `pass`.
Controller commands, resume, and Implementation fail closed when state legality
fails; an unknown phase has no inferred recovery transition.

The closed phase enum is `discussing`, `planning`, `applying_current`,
`validating`, `finalizing`, and `pass`. There is no persisted `idle`, `blocked`,
or `error` phase. A package not yet started need not have state; repair and
human-help behavior is derived from typed evidence without changing the current
work phase.

Workflow State legality uses the same Validator contract at four boundaries:
every Controller/resume entry, before each proposed atomic state replacement,
the final full managed-file validation, and every Implementation preflight. The
first two are narrow state guards, not full Current scans. One explicit invalid-
checkpoint episode shares a three-repair circuit breaker across state and
package findings. Initial INVALID consumes no repair; only evaluation of a
materially changed correction consumes one, including A/B/A. Legal phase writes
and identical reruns consume zero. The third repair may succeed, but a third
still-invalid evaluated checkpoint requires human help. Validator `ERROR`,
expected-final Current mismatch without recovery evidence, and unresolved
semantic choices stop immediately.

Workflow State has exactly three fields: `phase`, `active_question`, and
`plan_fingerprint`. It stores neither operation progress nor a Current
fingerprint. The latter was removed because a single last-observed digest cannot
distinguish a legitimate crash between Current/State writes from an unlisted edit
without a baseline snapshot or write-ahead log. Exact target reconciliation and
the Plan's expected-final fingerprint own those guarantees instead.

The complete phase-field/cross-file matrix is:

| State | `active_question` | `plan_fingerprint` | Required external evidence / unique next action |
|---|---|---|---|
| no State | absent | absent | With no Candidate, initialize/migrate; exactly one valid unanswered orphan Q is a recoverable start transient, never implementation-eligible |
| `discussing` | non-null Q | null | Q exists; null answer means ask/resume discussion, answered Q advances to question planning |
| `planning` question | non-null Q | null | Answered Q exists; Plan is absent or one complete unsealed `basis: question` Plan |
| `planning` repair | null | null | Latest full result is deterministic `INVALID`; disk Plan is absent, the stale invalid Plan, or one complete unsealed `basis: validation` repair Plan |
| `applying_current` | Q or null according to basis | non-null matching Plan hash | Immutable sealed Plan exists; Q binding is required only for question basis; every target is independently pending/complete/conflict |
| `validating` package finish | null | null | Explicit User finish plus Controller completion profile holds, or a sealed migration is reconciled; run one full validation |
| `validating` repair | null | non-null matching repair Plan hash | Validation-basis repair Plan is fully reconciled; run one full validation |
| `finalizing` decision pre-commit | non-null Q | non-null matching question Plan hash | Exact Plan reconciliation succeeded; append deterministic DEC, then clear both bindings; full Validator is not run per question |
| `finalizing` validated repair pre-cleanup | null | non-null matching repair Plan hash | Matching `VALID` exists; clear Plan binding, then clean transient data |
| `finalizing` clean marker | null | null | Delete only residue owned by the committed transaction. Without matching full VALID evidence, await/start the next Q; with matching specification/repair/migration VALID evidence, recheck and enter `pass` |
| `pass` | null | null | Candidate, migration and active attempt are absent; allocator exists; Controller completion profile and latest full `VALID` evidence match actual authoritative Current/rules/allocation |

Any other nullability, a seventh phase, a missing bound Q/Plan, a changed sealed
Plan, or `pass` with transaction residue is `INVALID`. `finalizing` uses the
listed substates rather than another phase. Completing one Q never means the
whole package is implementation-ready: after its DEC/cleanup the clean marker
either starts the next question or waits for an explicit User finish request.
Q reservation increments the six-counter allocation fingerprint, so even an
empty-operations decision makes the pre-Q VALID stale. Clean-marker resume can
therefore enter `pass` only when Validation Result matches the post-Q allocator
and proves a later authorized finish/repair/migration validation.

A transaction starts by atomically creating the complete Q before changing
State. `no State`, `pass`, or clean-marker `finalizing` plus exactly one valid
unanswered orphan Q is a Controller-recognized start transient: qualification
fails, and resume binds it into `discussing`. An answered, multiple, or malformed
orphan is `INVALID` and is never silently deleted.

Because `DECISION` is reserved before Q creation, a crash may leave `pass`, no
Candidate and only a higher DECISION high-water than the retained VALID. When
the five Specification counters and all other evidence still match, Controller
classifies this uniquely as a burned pre-Q gap: it never decrements the counter,
permits explicit next-Q start, and requires a later explicit finish before
Implementation can regain qualification. Any other stale allocation difference
is conflict. A bound unanswered Q with no Plan may be explicitly abandoned by
the User; Controller deletes only its Q/discussion/review, preserves the burned
suffix, and atomically enters the clean marker. Answered or planned work cannot
be silently abandoned.

`control/validator-attempt.json` is transient and closed to exactly:

```json
{
  "repair_count": 1,
  "last_evaluated": {
    "kind": "package",
    "fingerprint": "sha256:<kind-plus-checkpoint>",
    "result": "INVALID"
  }
}
```

`kind` is `state` or `package`. The fingerprint hashes a canonical envelope
containing that kind plus the exact evaluated State closure or the full raw
closed-inventory `evaluated_checkpoint_fingerprint`. Only an explicit evaluation in an
active invalid-checkpoint episode updates this file; ordinary legal phase
transitions do not. A first `INVALID` starts an episode at count zero.
Re-evaluating the same envelope does not increment. Evaluating a different
correction increments exactly once and records whether it is `VALID` or
`INVALID`, even for A/B/A values; the third changed repair may succeed, while its
still-INVALID result requires human help. A first evaluation that is directly
VALID creates no attempt file; ERROR never arms or advances repair.

For a full validation, Validator evaluates in memory. If the result starts or
continues an invalid episode, it atomically creates/updates attempt state before
atomically overwriting Validation Result; otherwise it writes only the result. A
crash after attempt but before result is recovered by re-evaluating the same
envelope without another increment and repairing the latest result. After a
corrected VALID is durable, Controller removes attempt state and closes that
episode. Narrow State/Plan guards use the same episode rule but never overwrite
Validation Result. Missing attempt state is legal before the first INVALID; once
a matching INVALID episode exists, missing/corrupt/conflicting attempt state
fails closed. The file stores no findings/history.

After automatic budget exhaustion, State and attempt evidence remain unchanged.
Controller may accept an exact repair only through an explicit human-approved
repair command; that command seals its Plan before autonomous resume can apply
it and does not reset or decrement `repair_count`. If the human-approved result
is still INVALID, no AI auto-repair is re-enabled and another explicit human
decision is required. A crash before seal requires the human to resubmit; a
sealed approved Plan resumes normally.

`control/task-state.yaml` is the single latest-only lifecycle owner and has no
per-Task files or event history:

```yaml
tasks:
  TASK-001: not-started
  TASK-002: accepted
```

Its key set equals the active TASK definition set whenever the file exists. The
closed values are `not-started`, `awaiting-preflight-approval`, `in-progress`,
`ready-for-review`, `changes-requested`, `accepted`, `re-slice-required`,
`spec-revision-required`, `blocked`, and `deferred`; File Contract owns the
transition table. Only a human sets `accepted`; only `accepted` satisfies a
dependent Task by default. Manifest and TASK Record own immutable scope/routing,
so Task State stores no paths, Work Units, evidence prose, timestamps, reviewer,
or copied acceptance content. Replacing a frozen TASK ID removes its state entry
and creates the fresh Task at `not-started`; accepted behavior change uses a new
Rework Task rather than resetting the accepted ID.

## 9. AI Progressive Disclosure

AI should not begin by reading `package-schema.yaml`, every reference, every
Current record, or history. The deep Package Controller hides that complexity
behind a small interface.

### 9.1 Minimal `SKILL.md`

`SKILL.md` should contain only:

- when the Skill applies;
- the safety/authority boundary;
- the one entry command or operation used to resume/create a package;
- the rule that Controller-returned record/dynamic-role selectors are the
  authoritative AI read set;
- the fail-closed stop rule.

It must not contain the artifact catalog, directory tree, state machine, ID
patterns, Validator rule list, or template field definitions.

### 9.2 Package Controller Interface

Proposed external interface:

```text
package resume <feature-root>
package explain-role <role>
package validate <feature-root>
package finish <feature-root>
```

`resume` reads the Package Schema, Workflow State Center and current validation
state, then returns a compact result such as:

```yaml
feature: pre-booking
phase: applying_current
transaction: Q-024
targets:
  - target: {record_id: REQ-014}
    status: complete
  - target: {record_id: BDD-009}
    status: pending
  - target: {file_role: task_manifest, task_id: TASK-006}
    status: complete
next_action: reconcile_then_apply
read_selectors: []
blocked_reason: null
```

The target list is sorted by canonical target only for stable display; array
position is never an identity or cursor. The result contains role names, not a
copied architecture. `next_action` is a
Controller-derived result, not a field persisted in Workflow State. A nonempty
`read_selectors` item is closed to one role plus either `record_ids` for a
multi-Record owner, one dynamic binding such as `task_id`, or `whole_role: true`
for a singleton. Controller resolves paths and materializes only those logical
records/instances; AI never has to load an entire class stream merely because
one Record was selected.

`explain-role` joins the role's canonical path/writer/authority/lifecycle from
Package Schema, parser/check profile from File Contracts, and purpose/use from
File Guide. This replaces hand-maintained duplicate file catalogs.

`validate` performs the complete final Current validation only from an authorized
finish, repair, or migration checkpoint and returns typed findings. It does not
edit Current or invent semantic requirements.

`finish` is the explicit User declaration that question/discussion work is done.
Controller first proves the package completion profile, starts final validation,
and enters `pass` only after matching `VALID` evidence and transient cleanup. A
normal answered Q is finalized separately and never implies package finish.

### 9.3 Phase-Based Read Policy

| Phase | Default reads |
|---|---|
| Enter/resume | Compact Controller summary only; State is an internal Controller read |
| Discuss | Active Candidate files plus only impacted Current roles |
| Plan | Active Q/discussion plus impacted Current roles and reverse dependents |
| Apply Current | Compact target-status summary only; Controller reads Plan and applies payloads |
| Validate/repair | Typed findings plus only roles needed to propose a deterministic repair; no archive or broad reread |
| Implement | Controller qualification summary, selected Task Manifest, selected Task and referenced Current Records; raw Validation Result remains internal |
| Historical explanation | Explicitly selected Decision Cards only |

History, unrelated ID classes, all Tasks, all Manifests, generated views, and
conditional semantic policies are never loaded merely because they exist.

## 10. Candidate, Current, Validation And Finalization Flow

```text
1. Controller creates the all-zero allocator for a new Feature, then creates or
   resumes the fixed Candidate files.
2. Discussion may pause and resume; Controller derives the exact next action
   from Workflow State and the fixed transition table.
3. AI submits confirmed exact symbolic operations to Controller; until that
   submission, durable planning prose remains in `discussion.md` and no partial
   Plan exists.
4. Controller validates every unique target, before state and complete after
   payload; verifies Q subject coverage; captures the allocation baseline;
   reserves and substitutes fresh numeric IDs; derives removed IDs and their
   reverse-reference closure; virtually applies the whole Plan to authoritative
   normative/routing Current; stores its expected-final fingerprint; atomically
   writes the complete Plan; and seals it through Workflow State. Seal freezes
   every Record in the virtual-final Current.
5. Controller applies the sealed after payloads directly to Current. AI does not
   manually copy the same payload a second time. Logical targets sharing one
   physical YAML owner are batched into one atomic file replacement; no progress
   cursor is persisted and no cross-file atomicity is claimed.
6. After interruption, resume compares every exact operation delta with Current
   and derives each canonical target's `complete`, `pending`, or `conflict`
   status independently.
7. After every target is complete, Controller requires the actual complete
   normative/routing Current fingerprint to equal the expected-final fingerprint.
   A mismatch proves an unlisted/unexpected change and stops for human recovery;
   the MVP stores no baseline snapshot from which to guess a rollback.
8. A question-basis Plan does not invoke the full Validator. Controller enters
   decision pre-commit `finalizing`, deterministically appends the compact DEC,
   clears Q/Plan bindings as the durable commit marker, and deletes Candidate
   material idempotently. A same-ID/same-content DEC is complete;
   same-ID/different-content is `ERROR`.
9. At the clean marker, Controller either starts the next Q or waits. Only the
   User's explicit `package finish` request starts package qualification.
10. Finish requires the one versioned Controller completion profile: no active Q,
    ordinary Plan, discussion/review, attempt, or migration; at least one active
    REQ, BDD, DESIGN, TEST and TASK; graph/cardinality closure; and exactly one
    Manifest plus Task-State entry per active TASK. The explicit User finish call
    is the final human confirmation; the atomic transition to
    `validating(null,null)` durably proves it was accepted, so no second Gate/
    readiness status file is needed. Validator remains absence-neutral and does
    not own this presence/readiness decision.
11. Controller fingerprints the completion-profile name/version and satisfied
    predicate values with authoritative Current,
    schema/contract/ID rules, allocation, Validator and canonicalizer evidence,
    atomically enters `validating(null,null)`, and runs the full Validator.
    Task-State evidence contains only role presence and exact active-TASK key-set
    equality; mutable lifecycle values are excluded so normal execution progress
    cannot stale specification qualification.
12. On deterministic `INVALID`, Controller first verifies the evaluated Current
    still matches the result, then atomically changes only Workflow State to
    `planning(null,null)`. The old Plan, if any, may temporarily remain. It is
    then atomically deleted or replaced with one validation-basis exact repair
    Plan. A disk Plan whose hash still equals the INVALID transaction fingerprint
    is stale and cannot be resealed; a new Plan must bind the complete INVALID
    result fingerprint and the invalid Current baseline. No cross-file atomicity
    is claimed. Seal, apply, reconcile and full validate repeat within the same
    attempt budget.
13. The third changed repair may succeed; a third still-`INVALID` result stops.
    `ERROR`, semantic uncertainty, an unrepresentable repair, or expected-final
    mismatch stops immediately.
14. Matching `VALID` records authoritative Current, independent rule/engine and
    allocator fingerprints, plus a generic finish/repair/migration transaction
    binding. Controller enters the appropriate finalizing checkpoint, removes
    repair/migration Plan and attempt data idempotently, rechecks all evidence and
    the completion profile, then atomically enters `pass`.
15. Implementation qualifies only when Workflow State is legal and `pass`, no
    active Candidate/attempt/migration transaction exists, allocation is legal,
    the completion profile still holds, and Current plus every rule/engine/
    allocation digest still match Validation Result.
```

The minimum resume decision table is normative:

| Observed condition | Controller result |
|---|---|
| no State, no Candidate | initialize/migrate; never claim `pass` |
| no State, `pass`, or clean-marker `finalizing` plus exactly one valid unanswered orphan Q | qualification-ineligible start transient; bind Q and enter `discussing` |
| the same start states plus answered/multiple/inconsistent Candidate data | `INVALID`; do not guess or delete |
| `discussing`, bound Q missing | `INVALID` |
| `discussing`, Q unanswered | resume discussion |
| `discussing`, Q unanswered, explicit User abandon, no Plan | delete only Q/discussion/review, retain allocation gap, enter clean marker |
| `discussing`, Q answered | atomically enter `planning` |
| question `planning`, Q unanswered or answer introduces undeclared subject | return to discussion and reconfirm the complete subject set |
| question `planning`, no Plan | continue symbolic Plan construction from Q/discussion |
| repair `planning`, no Plan and matching latest INVALID | continue deterministic repair construction from that exact evaluated checkpoint; semantic/non-representable repair goes human |
| repair `planning`, disk Plan hash equals latest INVALID transaction fingerprint | stale invalid Plan; delete/replace it, never reseal it |
| repair `planning`, new validation-basis Plan | require matching INVALID/current baseline, allocate, validate and seal |
| either `planning`, valid new unsealed Plan | compute expected final, then seal and enter `applying_current` |
| `applying_current`, Plan missing/hash/basis/Q mismatch | conflict; immediate human recovery |
| `applying_current`, any target conflict | conflict; immediate human recovery |
| `applying_current`, pending targets exist | Controller applies pending exact payloads and reclassifies every target |
| `applying_current`, all complete but full Current != expected final | unexpected edit; immediate human recovery |
| question-basis apply, all complete and full Current == expected final | enter decision pre-commit `finalizing`; do not run full Validator |
| validation-basis apply, all complete and full Current == expected final | enter repair `validating` |
| clean-marker `finalizing`, no matching full VALID for actual Current/rules/allocation | remove decision-owned residue, then await/start next Q; never claim `pass` |
| clean-marker `finalizing`, explicit finish but completion profile fails | report exact incomplete condition; do not run Validator |
| clean-marker `finalizing`, explicit finish and completion profile holds | enter package-finish `validating` and run Validator once |
| `validating`, no current result or stale result | run full Validator once using attempt-before-result write order |
| `validating`, matching `INVALID`, automatic budget remains | atomically clear State seal first, then replace stale Plan with a validation-basis repair Plan if representable |
| `validating`, matching `INVALID`, budget exhausted | retain evidence and require explicit human-approved repair; never reset the count |
| `validating`, `ERROR` | immediate human recovery |
| package-finish `validating`, matching `VALID` | enter clean-marker `finalizing`; matching post-Q allocation/finish evidence survives crash, so recheck, clean, then `pass` |
| migration child-repair `VALID` with parent migration Plan present | recheck parent hash/source/target/allocation closure, enter clean marker, then delete both owned Plans and `pass` |
| ordinary repair `validating`, matching `VALID` | enter validated-repair pre-cleanup, clear Plan binding, clean, recheck, then `pass` |
| decision pre-commit `finalizing`, DEC absent | append deterministic DEC atomically |
| decision pre-commit `finalizing`, same DEC ID/content | treat append as complete and clear bindings |
| decision pre-commit `finalizing`, same DEC ID/different content | `DEC_COMMIT_COLLISION`; human recovery |
| clean-marker `finalizing`, matching specification/repair/migration VALID | clean only that transaction's residue, recheck completion/evidence, then `pass` |
| clean-marker `finalizing` after a claimed VALID commit but evidence missing/mismatched | immediate human recovery; do not infer or revalidate after transaction evidence may be deleted |
| `pass`, no residue, only DECISION high-water advanced | burned pre-Q reservation; remain ineligible, allow explicit next-Q start or explicit finish, never roll counter back |
| `pass` with other residue or stale/mismatched evidence | implementation ineligible; resume reports the exact violation and never edits specification automatically |
| illegal State shape/phase | `INVALID`; no inferred transition |

Resume may improve wording but must return one of these outcomes for every
combination. It never uses operation array positions, archive content, or a
persisted prose next action.

Q is active decision recovery data, not history. Its definition and permitted
Candidate/Control references survive interruption, incomplete application,
`ERROR`, or failed DEC writing. After exact Plan reconciliation and successful
deterministic DEC append, Finalizer clears Q/Plan bindings as the commit marker,
then deletes every Candidate Q occurrence. Binding clear itself proves that DEC
was checked; resume never tries to rediscover or match DEC after Q is gone. This
decision cleanup does not require or imply full-package `VALID` or `pass`. The
final durable set is Current plus independent compact Decision Cards, never
completed Q data.

The workflow does not add a second mandatory User confirmation after each
decision application. The User's answer authorizes the rewrite; existing Gate
or final review, plus explicit on-demand inspection, owns semantic review. This
accepts that Controller completion and Validator legality cannot prove semantic
equivalence to human intent, without adding another per-decision interruption or
persistent review artifact.

The authoritative Current fingerprint covers only parsed canonical logical
content at every normative or routing Current path, sorted by canonical relative
path. It excludes Candidate, History, Control, schema/engine inputs and derived
View bytes. Package Schema, File Contracts, ID Schema, allocator, Validator and
canonicalizer each have independent fingerprints so the exact reason evidence
became stale is mechanically visible. File Guide wording is excluded because it
does not affect package validity.

Existing View shape may be checked during full final validation, and unsafe,
misplaced, linked or unknown paths always fail physical safety checks. After
`pass`, however, malformed or stale View content never blocks Implementation:
Views are non-authoritative, excluded from fingerprints and rebuilt only at a
Controller-mediated User display/confirmation boundary.

`control/validation-result.json` is one latest-only closed object and is excluded
from every fingerprint it records:

```json
{
  "result": "VALID",
  "evaluated_checkpoint_fingerprint": "sha256:<closed-raw-evaluation-inputs>",
  "current_fingerprint": "sha256:<authoritative-current>",
  "package_schema_fingerprint": "sha256:<canonical-schema>",
  "file_contracts_fingerprint": "sha256:<canonical-contract-catalog>",
  "id_schema_fingerprint": "sha256:<canonical-id-schema>",
  "allocation_state_fingerprint": "sha256:<canonical-id-allocation>",
  "validator_fingerprint": "sha256:<validator-implementation>",
  "canonicalizer_fingerprint": "sha256:<canonicalizer-implementation>",
  "transaction_kind": "specification",
  "transaction_fingerprint": "sha256:<finish-contract>",
  "findings": []
}
```

Every field is required. `result` is exactly `VALID`, `INVALID`, or `ERROR`;
`transaction_kind` is `specification`, `validation_repair`, `migration`, or null.
`evaluated_checkpoint_fingerprint` hashes the complete input closure that can
change the result: sorted raw path/type/bytes inventory plus external rule,
engine, allocation and transaction inputs, excluding Validation Result and
attempt themselves. It remains computable for safely inventoried malformed
content and is also the attempt envelope's package fingerprint. For package
finish, the transaction fingerprint is the canonical digest of the
Controller completion profile plus Current/rule/allocation evidence. For repair
or migration it is the sealed Plan hash. Each finding is a closed object with
stable `code`, `classification` (`violation` or `system_error`), nullable
structured `location`, and concise `message`.

The File Contract closes nullability by result:

- `VALID`: every fingerprint and transaction binding is non-null and `findings`
  is empty;
- `INVALID`: evaluated-checkpoint and transaction bindings are non-null and at
  least one `violation` exists. A semantic fingerprint may be null only when a
  violation identifies the malformed input that prevented its computation;
- `ERROR`: values that could not be safely computed may be null and at least one
  `system_error` exists.

Transaction kind/fingerprint are either both non-null or both null; VALID and
INVALID require both. INVALID findings are all `violation`; any system error
makes the whole result ERROR.

An escaping link/reparse point, unsafe traversal, unreadable authority input, or
parser/engine failure that prevents a trustworthy Current fingerprint is always
`ERROR`, even when its stable finding code also identifies the physical cause.
`INVALID` is reserved for deterministically inspected content with all required
evidence non-null.

Non-blocking investigations are returned ephemerally and never retained in a
final VALID. `validator_fingerprint` and `canonicalizer_fingerprint` hash their
complete executable/rules compatibility contract, not a version label. Only a
full authorized package validation overwrites this file, after the attempt-state
write described above; narrow guards do not. Repair validation additionally
requires actual Current equal to Plan expected-final and transaction fingerprint
equal to the sealed Plan.

Implementation qualification recomputes authoritative Current and independent
rule/engine/allocation evidence in a fixed order, then runs narrow existing-path
and State safety guards plus the Controller completion profile. It does not run
semantic graph validation or repair. View content is ignored; only an unsafe,
misplaced, duplicated or unknown View path blocks qualification.

## 11. Validator Algorithm

The Validator Module exposes a small `validate(feature_root)` interface and
hides the following implementation:

1. Resolve and meta-validate the bundled Package Schema.
2. Resolve and meta-validate the ID Schema referenced by the Package Schema.
3. Resolve the feature root without following escaping links or reparse points.
4. Inventory every file and directory under the feature root.
5. Classify every file into exactly one role by canonical path.
6. Reject unknown, misplaced, ambiguous, over-multiplicity, too-deep,
   case-wrong, orphaned, or forbidden-link paths that actually exist.
7. Enforce only permitted role multiplicity; never infer that an absent role is
   required, applicable, ready, or `not-applicable`.
8. Parse files with the role-declared parser and validate their shape.
9. If `id_allocation_state` exists, validate its exact six-key shape,
   permitted-range values, and that every active ID plus structured Q subject or
   Plan payload ID is no greater than its reserved class high-water. At Plan seal,
   validate each class's absent-to-present IDs against the exact contiguous range
   above `allocation_baseline`. Absence remains legal to Validator; Controller
   initialization/allocation/pass guards own applicability.
10. Load the active ID Index if present and every existing schema-declared
   definition-owner file. Treat an absent Index as an empty active set, so any
   existing definition or reference produces `ID_ACTIVE_SET_MISMATCH`.
11. Validate ID format, class, unique definition, owner role and content shape.
12. For every authoritative/routing role whose contract enables ID scanning,
    reject YAML comments, raw-scan every string scalar for all Current and legacy
    token shapes, require every well-formed Current token to belong to the active
    Index, and reject a token outside its schema-declared ID-valued field as
    `ID_UNDECLARED_REFERENCE_POSITION`. Apply the separate no-Spec-ID lexical
    contract to Decision Archive. Candidate prose and Views use `id_scan: none`.
13. Extract graph edges from those schema-declared ID-valued fields only; the
    exhaustive scalar scan in step 12 catches removed IDs hidden in ordinary
    statement/title/decision/pass-criteria prose even though they are not edges.
14. Reject undefined IDs, removed/unknown ID occurrences, invalid target classes,
    missing required edges, and forbidden relationship shapes.
15. Compare dynamic files to their active bound IDs.
16. During full final validation, validate each retained View's structure and
    provenance shape without requiring content freshness or treating it as
    authority; display/confirmation separately refreshes it. Implementation
    qualification ignores View content.
17. Produce one typed result: `VALID`, `INVALID`, or `ERROR` with stable findings.
18. Evaluate in memory. For an initial INVALID or a correction in its active
    episode, atomically create/update attempt state first; direct VALID or ERROR
    does not create/advance it. Then atomically overwrite the latest result. On
    `VALID`, require the authorized finish/repair/migration predicate and persist
    all Current, rule, allocation, engine and transaction evidence.

`INVALID` is a deterministic package violation. `ERROR` means the Validator,
schema, parser, control state, or filesystem safety assumptions cannot be
trusted. Semantic review advice is non-blocking and cannot start an automatic
modify/check loop.

The minimum implementation is one Python 3.10+ command-line package. It uses
PyYAML 6.0.3 through an explicitly declared specification-workflow dependency,
the Python standard library for JSON, hashing and filesystem operations, and
same-directory temporary files plus atomic replacement for Validator-owned
state/results. It does not reuse another Skill's private environment, implement
a YAML parser, introduce SQLite, run a service, or require a plugin. Parser
dispatch, ID graph construction and stable finding codes remain internal behind
the one `validate(feature_root)` interface.

## 12. Required Validator Findings For Physical Architecture

At minimum, physical validation needs stable finding codes for:

| Code | Condition |
|---|---|
| `PKG_UNKNOWN_PATH` | File or directory is not declared by any role |
| `PKG_WRONG_PATH` | Recognized filename appears outside its canonical role path |
| `PKG_DUPLICATE_ROLE` | Singleton role appears more than once |
| `PKG_AMBIGUOUS_ROLE` | A path matches multiple role patterns |
| `PKG_INVALID_DYNAMIC_NAME` | Dynamic filename does not bind to a valid active ID |
| `PKG_DEPTH_EXCEEDED` | Directory depth exceeds the schema limit |
| `PKG_FORBIDDEN_LINK` | Symlink, junction or escaping reparse point is present |
| `PKG_CASE_MISMATCH` | Actual casing differs from the canonical path |
| `PKG_ORPHAN_DIRECTORY` | Directory is not required by any present/allowed role |
| `PKG_WRONG_FORMAT` | File does not parse using its role format |
| `PKG_WRITER_CONFLICT` | Persisted ownership metadata conflicts with the role writer, when such metadata is applicable |

The executable contract also reserves these cross-file codes:

| Code | Condition |
|---|---|
| `ID_ALLOCATION_MISSING` | An initialized Feature lacks the Controller allocation state |
| `ID_ALLOCATION_INVALID` | Allocation keys/ranges are invalid or an ID exceeds its reserved high-water |
| `ID_LEGACY_PATTERN` | Final managed content contains a scope-rejected legacy ID shape |
| `ID_ACTIVE_SET_MISMATCH` | Active Index and discovered Current definitions differ |
| `ID_UNDEFINED_REFERENCE` | A managed Current reference has no active definition |
| `ID_REMOVED_RESIDUE` | A Plan-removed ID remains in authoritative Current |
| `ID_UNDECLARED_REFERENCE_POSITION` | A Current-format token occurs outside a schema-declared ID-valued field |
| `PLAN_INVALID_SHAPE` | Plan fields, state objects, target identity, or no-op invariants fail |
| `PLAN_BINDING_MISMATCH` | Q, State, Plan fingerprint, or expected-final binding differs |
| `PLAN_TARGET_CONFLICT` | A target matches neither its exact before nor after state |
| `PLAN_UNEXPECTED_CURRENT` | All targets complete but complete Current differs from expected-final |
| `PLAN_REPAIR_STALE` | A planning repair still contains the consumed invalid Plan or mismatched INVALID basis |
| `STATE_INVALID_COMBINATION` | Phase fields or required cross-file evidence violate the matrix |
| `VALIDATOR_ATTEMPT_CONFLICT` | Required retry evidence is missing, corrupt, or disagrees with the evaluated episode |
| `DEC_COMMIT_COLLISION` | Existing DEC suffix has different deterministic projected content |
| `PACKAGE_INCOMPLETE` | Explicit finish was requested but the Controller completion profile is not satisfied |
| `QUALIFICATION_STALE` | `pass` evidence no longer matches Current/schema/engine or residue exists |

Finding text may improve, but finding codes and semantics are part of the
Validator interface and must be tested.

## 13. Mapping Current Artifacts Into The Blueprint

The accepted inventory suggests this migration direction:

| Current artifact group | Target treatment |
|---|---|
| `00-spec-workflow-status.md` | Replace with structured `workflow_state` role |
| `00-stage-manifest.md` | Retire; Package Schema owns files and workflow owns sequencing |
| `14-decision-log.md` and `15-open-questions.md` | Active question moves to `candidate/question.yaml`; Workflow State references its ID; compact resolved cards move to the one cold archive |
| PRD and EARS | Merge into `requirement_records`; no PRD/EARS identity class or duplicate prose owner |
| BDD feature files | Convert into `bdd_records` |
| Project impact, technical design and applicable compliance | Merge into `design_records` or the external current rule owner |
| Test strategy and test-case contracts | Merge into `test_records` |
| Gate sketches and Gate/Task-plan review HTML | Re-render through the one latest `candidate_review`; delete after transaction |
| Task index and Task files | Consolidate normative meaning into `task_records`; dashboard derives summary |
| Manifest files | Keep one dynamic leaf file per active Task ID |
| Prompt files | Retire persistent copies; render invocation on demand |
| Traceability, analysis, readiness and convergence reports | Render without persistence; readiness is Controller `pass` plus `validation_result` |
| Dashboard | Keep and rewrite as the simplified read-only latest `current/views/dashboard.html` User View; remove local state and export/reconciliation behavior |
| `execution/` records and evidence | Transient while active; consolidate current result/state, then delete rather than archive |
| Diagrams | Render into `candidate_review` when User inspection is required; otherwise do not persist |
| Context proposals and convergence reports | Candidate/transient roles; delete after application |

Before implementation, every retained template must map to exactly one Package
Schema role and every retired template must disappear from Skill instructions,
tests, and generated examples.

Ordinary revision and one-time legacy migration have different interfaces and
must not be mixed. The ordinary Application Plan has no raw path or operation
kind and Workflow State never stores migration operations. A separately
authorized `package migrate` adapter owns one temporary project-scope
`migration_plan` role at the Package-Schema-declared path
`.ai-dev/migrations/<feature>.yaml`, outside the Feature Package root. The role
is legal only until migration completes and is excluded from normal AI loading.
Migration may start only from no State or a clean marker with zero managed
Candidate, attempt, or competing migration data. Existing ordinary transaction
residue requires human resolution first and is never deleted by migration.

The migration Plan is complete and sealed by presence; no draft migration file
exists. Its closed top level is:

```yaml
feature_root: .ai-dev/features/pre-booking
allocation_floor: {REQ: 12, BDD: 8, DESIGN: 4, TEST: 9, TASK: 5, DECISION: 11}
sources:
  - relative_path: 01-prd.md
    fingerprint: sha256:<raw-legacy-bytes>
    disposition: convert
    target_bindings: [{record_id: REQ-013}]
allocation_baseline: {REQ: 12, BDD: 8, DESIGN: 4, TEST: 9, TASK: 5}
operations: [<ordinary exact target envelopes after symbolic-ID substitution>]
expected_final_current_fingerprint: sha256:<virtual-final-current>
```

Each source disposition is exactly `convert`, `merge`, or `retire`. Before its
first write, the adapter inventories every observable active definition,
Manifest and legacy package file, raw-scans known Current/legacy/Q/DEC ID tokens,
takes the greatest suffix per mapped counter, and optionally accepts a trusted
User minimum. It initializes each high-water to
`max(observed_suffix, supplied_floor)`; the no-reuse guarantee begins at that
migration floor and cannot prove already deleted, unobservable history. Source
fingerprints hash raw legacy bytes. Migration targets use symbolic new-ID handles
until allocator initialization; Adapter then captures the five Specification
counters as `allocation_baseline`, atomically reserves/substitutes the required
contiguous ranges exactly like ordinary Plan assembly, and only then atomically
writes the complete sealed-by-presence migration Plan. It cannot choose numeric
target suffixes directly.

Progress is derived from source existence/fingerprint and exact final target
state, never a cursor. A source carrying retained meaning is removed only after
every bound target equals its after payload; redundant/historical sources may be
retired directly. Any unknown source, changed fingerprint, ambiguous mapping, or
non-idempotent state stops for human recovery.

After all sources are accounted and removed, Controller enters migration
`validating`; full validation writes `transaction_kind: migration` and the
migration Plan hash. On matching VALID, Controller atomically enters
`finalizing(null,null)` as the verified cleanup marker, deletes the migration
Plan, rechecks Current/rule/engine/allocation evidence, and enters `pass`. A crash
after the marker resumes cleanup from the marker itself without rediscovering the
deleted Plan. `package resume` refuses ordinary revision or Implementation while
the project-scope migration role exists, but dispatches to the unique migration
apply/validate/cleanup resume path rather than stranding the transaction.

If migration validation is INVALID, its validation-basis repair Plan remains a
child of the still-present sealed migration Plan. After matching repair VALID,
Controller rechecks the parent migration hash, source/target completion and
allocation evidence before entering the clean marker. That transition proves
the parent check; cleanup may then delete both Plans without requiring another
`transaction_kind: migration` validation run.

The mapping must cover both producer roots, not only the generator Skill:

- all 39 current `spec-package-generator/templates/*` files;
- all 4 current `implement-spec-task/templates/*` files;
- every programmatic renderer or writer introduced by the refactor;
- outputs written outside the feature root, such as project-level Current
  Context, through an explicit schema scope and canonical path;
- non-persistent outputs through an explicit `persistence: none` role.

## 14. How The Blueprint Meets The Four Requirements

### Requirement 1: Immediate, concise AI understanding

- Minimal `SKILL.md` routes into one controller interface.
- `resume` returns phase, next action and bounded record/dynamic-role selectors.
- `explain-role` reveals one role on demand from the executable authority.
- History and unrelated Current content are excluded from default loading.
- The full Package Schema is implementation context, not mandatory prompt
  context.

### Requirement 2: Clear categories

- Closed authority and lifecycle enums prevent synonymous classifications.
- Every file matches exactly one role and one category.
- Candidate, Current, cold history, mutable state, validation evidence, routing
  and derived views cannot share authority.
- Writer ownership is explicit and validated.

### Requirement 3: Unique filename, location and purpose

- Package Schema is the sole role/path/producer/lifecycle catalog.
- File Contracts are the sole parser/check-profile catalog, and File Guide is
  the sole AI-facing purpose/use catalog.
- ID Schema refers to roles, never physical paths.
- Templates are linked to roles and cannot choose output paths themselves.
- Architecture/workflow prose use role names and never restate the full path
  catalog.
- Validator derives actual inventory rather than trusting a handwritten feature
  manifest.

### Requirement 4: No unbounded directory growth

- Closed-world roots and a fixed maximum depth.
- No recursive wildcards or dynamic directories.
- Dynamic leaf files exist only one-per-active-ID.
- One file per ID class, one Candidate working set, one Decision archive stream,
  and latest-only state/result files.
- Unknown, empty, orphaned, linked, misplaced and case-variant paths fail.
- Architecture expansion requires a reviewed Package Schema change, not a new
  folder created inside a feature.

## 15. Acceptance Criteria For The Blueprint's Implementation

Implementation is complete only when all of the following are proven:

1. A fresh AI invocation can call `resume` and receive a bounded next-action
   result without reading the complete package or history.
2. Every retained generated file role exists exactly once in Package Schema with
   path/pattern, producer, category, writer and lifecycle, and resolves exactly
   once to its File Contract and File Guide purpose.
3. Every retained template and every programmatic generator maps to exactly one
   role; all 43 current templates have an explicit migration disposition before
   implementation begins.
4. No second Markdown or template catalog repeats canonical paths.
5. Package Schema, File Contracts, File Guide, ID Schema, and all cross-layer
   references meta-validate fail closed.
6. An unknown root file, unknown nested directory, misplaced known file,
   duplicate singleton, over-depth path, dynamic file for an inactive ID, and
   symlink/junction escape each fail with stable finding codes.
7. Candidate can resume after interruption using only workflow state, the active
   question, discussion/application plan and impacted Current roles.
8. Candidate cleanup removes all temporary material without touching Current or
   Decision Cards.
9. Removing an active ID fails until its definition, all managed occurrences,
   bound dynamic files and required edges are synchronized.
10. A final `VALID` is bound to the complete raw evaluation-input closure, every
    authoritative normative/routing Current input, plus independent Package
    Schema, File Contract, ID Schema, allocator,
    Validator, canonicalizer, and finish/repair/migration transaction evidence;
    View bytes remain outside qualification fingerprints.
11. Any authoritative normative/routing Current, rule, engine, or allocation
    change makes the prior result inapplicable without an AI-maintained
    invalidation write.
12. Implementation cannot start without Controller-owned final workflow `pass`
    and a matching Validator `VALID` result.
13. Repeated package generation and validation create no new directory shape,
    orphan Candidate folder, old result history, or per-decision file sprawl.
14. Every Record in a sealed Plan's virtual-final Current or passed baseline
    rejects same-ID canonical content mutation; replacement removes the old ID
    and leaves zero Current residue.
15. Deleting the highest active ID never causes reuse: Controller allocation
    advances only the feature-lifetime high-water and cancellation creates a
    permanent gap.
16. An `INVALID` final result can produce a validation-basis exact repair Plan
    within the same attempt budget, while ERROR/semantic uncertainty/unexpected
    Current never enters a speculative repair loop.
17. Every legal Workflow State/cross-file combination has one resume outcome,
    and every illegal combination fails with a stable finding.

## 16. Remaining Implementation Work

The assurance decisions are now closed. Implementation still requires finite
translation work rather than another architecture choice:

- encode the confirmed 43-template disposition matrix and every programmatic or
  non-persistent producer in Package Schema/inventory tests;
- finish the class-specific REQ/BDD/DESIGN/TEST/TASK `content_schema` definitions;
- encode the Plan, three-field State, allocation, validation-result, attempt, and
  project-scope migration-plan contracts exactly as described above;
- implement the phase/resume and deterministic repair tables as Controller tests;
- encode the closed rejected legacy-pattern catalog and raw/comment scope
  fixtures from both inspected legacy packages;
- implement the one-time migration adapter and exact source-disposition fixtures;
- migrate/retire producers only after exact-once inventory tests pass.

No physical runtime path should be implemented before its Package Schema role,
File Contract, File Guide entry, producer disposition, and fixture exist.
