# Specification Skill Refactor And Migration Plan

## Status

This plan translates the confirmed decisions through `DEC-087` into an
ordered implementation and migration approach. It is a planning artifact, not
implementation authorization. Architecture decisions are closed; catalogs,
code, migrations, and fixtures must still be implemented and verified before
runtime replacement begins.

## Outcome

Replace the distributed specification control plane with one current
specification graph, one active-ID owner, one mutable Task lifecycle owner, one
immutable Task routing contract, one cold decision archive, and one
deterministic validation module plus one Controller-only monotonic ID allocator.
A permitted lifecycle update must never
invalidate its own execution Manifest, and an omitted specification update
must prevent final Current validation rather than appear during implementation.
Every ID-bearing definition must use the `DEC-024` two-field ID Record envelope.
`DEC-025` fixes its physical serialization as owner-grouped YAML multi-document
streams. `DEC-026` fixes one declarative schema language interpreted by one
generic validator. `DEC-027`, as refined by `DEC-048`, requires that validator
to inventory and inspect every existing Current Managed Package File after the
complete planned rewrite without requiring file presence.

## Target Authorities

| Concern | Sole owner | Constraint |
|---|---|---|
| Physical package architecture and file role lifecycle | bundled `references/package-schema.yaml` | Exact paths/patterns and permitted multiplicity; no Markdown or per-feature duplicate |
| AI-facing file purpose | bundled `references/file-guide.yaml` | Purpose/use only; no paths or parser rules |
| Current normative meaning | Current Specification Set | Contains current IDs only |
| Active ID membership | `current/id-index.yaml` | Contains IDs, not locations or relationships |
| Specification ID allocation | `control/id-allocation.yaml` | Controller-only monotonic high-water integers; no old IDs/content and no AI-selected suffixes |
| ID classification and relationships | bundled `references/id-schema.yaml` | Refers to definition roles, not physical paths; no Markdown duplicate |
| Current workflow question | Active Question State | At most one; removed after successful application |
| Task lifecycle | `control/task-state.yaml` | Mutable; never digest-pinned |
| Task execution routing | `current/manifests/<TASK-ID>.yaml` | Immutable routing only |
| Historical rationale | Decision Archive | Cold, non-authoritative, explicitly loaded only |
| Existing-file legality | Specification Package Validator output | `VALID`, `INVALID`, or `ERROR`; never workflow readiness |
| Completion and readiness | Workflow State Center controlled by Package Controller | Only this owner may set workflow `pass` |

## Deep Module Interface

The Specification Package Validator is the external seam for legality. Its full
operation runs only at an authorized explicit package finish, validation repair,
or migration checkpoint, returning deterministic failures and ephemeral
semantic investigations. Per-question and Candidate planning material is outside
this interface.

ID discovery, relationship traversal, digest calculation, old-ID detection,
derived-View structure checks, retry counting, and validator control-state updates
stay inside this module.
Callers must not reproduce those operations in `SKILL.md`, workflow prose,
templates, dashboards, or executor instructions.

The paired Package Controller is the progressive-disclosure seam. Its resume
operation reads Package Schema plus current workflow/validation state and
returns only phase, next action, and record/dynamic-role selectors. Controller
materializes selected Records instead of exposing whole class streams; AI does
not need to load the full Package Schema or feature package to enter safely.

The detailed target architecture, bounded tree, schema shape, growth rules and
acceptance criteria are defined in
`docs/spec-package-architecture-blueprint.md` as the confirmed implementation target.

## Required Validation Rules

Final validation and execution qualification fail when any of these conditions
hold:

- an ID has an unknown prefix, no definition, or multiple definitions;
- an ID-bearing definition does not conform to its schema-declared record
  envelope or kind-specific payload;
- an ID Record contains a top-level field other than `id` or `content`, or its
  content does not conform to the ID Content Schema selected by `id`;
- a definition appears outside its schema-declared owner;
- a reference is undefined or a required relationship is missing;
- a removed ID remains anywhere in the managed current package;
- the Current ID Index and discovered definition set disagree;
- a removed ID has any schema-scanned reverse-dependent occurrence whose owner
  is absent from the Plan or whose virtual-final payload still contains it;
- an existing Task Lifecycle State contains a key that is not an active TASK, or
  an existing state entry has an illegal value; Controller qualification, not
  Validator, decides when the state role must exist;
- any path is both digest-pinned and mutable;
- an immutable pinned digest is missing or stale;
- an existing generated View violates its declared structure/provenance shape
  during full validation; content freshness is checked only at display;
- a Decision Archive participates in current readiness, traceability,
  invalidation, resume, or execution routing.
- a file under the Current package root does not match exactly one declared
  Managed Package File role;
- any authoritative/routing managed content contains an unknown or removed ID,
  or Decision Archive contains a forbidden current/legacy Specification token;
  Candidate prose and View bytes are excluded.

Semantic ambiguity, unusual cross-artifact use, and sequence gaps are reported
as anomalies for focused investigation and do not silently become hard rules.

## Implementation Phases

### Phase 0: Lock Regressions With Tests

- Create minimal synthetic fixtures reproducing the pre-booking pinned/mutable
  overlap and stale-digest failure.
- Create a lifecycle-mutation fixture reproducing the corrected dimflow
  behavior: Task state changes while immutable Manifest qualification remains
  valid.
- Add fixtures for stale old IDs, undefined references, duplicate definitions,
  Task-state disagreement, archive leakage, an unclassified newly added file,
  a removed ID hidden in a non-record file, an interrupted direct-Current
  rewrite, and final validation cleanup.

Exit condition: every known defect is red before implementation and can pass
only through the validator's public interface.

### Phase 1: Build The Validation And Application-Control Module

- Add one executable Package Schema as the sole authority for top-level areas,
  canonical file paths/patterns, roles, producers, permitted multiplicity, writers,
  authority/lifecycle, contract/guide references, and cleanup behavior. Keep
  actual-file inventory derived rather than adding a per-feature handwritten
  location manifest. Deterministic parse/check details move to the proposed
  file-contract catalog rather than being duplicated here.
- Split file knowledge behind the DEC-041 role-keyed interface: Package Schema
  owns physical placement/producer/lifecycle,
  `file-contracts.json` owns deterministic parse/check contracts, and
  `file-guide.yaml` owns concise AI-facing purpose/use. The Package Controller
  returns a joined selected-role view rather than exposing all catalogs.
- Inventory both Skills' template roots and all programmatic generators. Require
  every retained producer to map to exactly one Package Schema output role, and
  forbid templates from selecting paths or filenames. Track all 43 current
  templates in a finite migration matrix; delete retired producers rather than
  registering obsolete output roles in the final Schema.
- Add the executable ID Schema.
- Validate the ID Schema itself before using its class rules.
- Require each ID class to declare exactly one definition-owner file in the ID
  Schema. Store that class's records only in the declared YAML multi-document
  stream; allow many managed consumers to reference them without duplicating
  their definitions or adding locations to the Current ID Index.
- Inventory the feature package from the Package Schema. Require every existing
  managed file to have exactly one declared role and fail on unknown,
  misplaced, duplicate-singleton, or malformed dynamic filenames. Do not treat
  an allowed role's absence as a Validator finding.
- Limit exhaustive ID-occurrence scanning to authoritative/routing Current roles
  whose contracts enable it, plus the separate Decision Archive lexical rule.
  Candidate planning, Views, chat, source code, and unrelated documentation are
  excluded.
- Raw-scan enabled managed content for current, unknown, removed and declared
  legacy tokens before structured class validation; prohibit YAML comments in
  authoritative/routing and Decision files so tokens cannot hide from parsing.
- Extract each dependency once from its schema-declared in-content marker. Do
  not maintain document-end or metadata reference inventories in parallel.
- Require every current normative reference target to be an ID Record. Treat
  schema-declared ID fields as the only authoritative dependency edges; file
  paths, headings, prose mentions, and copied rulings cannot substitute for an
  ID relationship. Generate both forward and reverse graphs for impact checks.
- Implement one complete final-Current validation only after the User explicitly
  declares package finish and Controller proves its completion profile. Do not
  validate each answered question, intermediate edit, or Candidate material.
- Bind every final result to independent exact normative/routing Current, schema,
  contract, ID rule, allocator, Validator and canonicalizer fingerprints plus a
  generic finish/repair/migration transaction fingerprint. Also bind one raw
  closed-input evaluated-checkpoint digest so malformed files, Views, History,
  unknown paths and Control inputs count toward repair exactly once. Derived View
  bytes remain outside canonical Current. Implementation accepts only an exact evidence match; no
  AI-maintained pre-edit invalidation step is trusted.
- Add one AI-facing Workflow State Center as the sole resume authority for the
  active transaction phase, active Q and sealed Plan binding. Derive every
  operation's completed/pending/conflict status by canonical target comparison;
  do not persist completed operations, array positions, or a reconciled Current
  fingerprint. Keep the validator-owned retry
  artifact internal rather than duplicating workflow status in it.
- Return only `VALID`, `INVALID`, or `ERROR` plus machine-readable findings.
  Controller alone owns the completion profile, explicit-finish boundary and
  final `pass`; Validator owns legality evidence only.
- Implement the Validator as one Python 3.10+ CLI package with an explicitly
  declared PyYAML 6.0.3 dependency and ordinary files. Keep parsing, graph
  checks, fingerprints, locks, and atomic replacement internal; add no SQLite,
  service, plugin, or custom YAML parser.

Exit condition: a complete rewritten Current is deterministically `VALID`, an
interrupted or invalid Current cannot drive development, and running final
validation twice without edits produces the same result.

### Phase 2: Establish New Authority Shapes

- Migrate every concrete Feature Package Root to the DEC-042 closed top level:
  `current/`, `candidate/`, `history/`, and `control/`. Reject all other root
  files/directories and every child directory not implied by a Package Schema
  role.
- Add Current ID Index, Task Lifecycle State, monotonic ID Allocation State,
  Decision Archive, and the compact three-field Workflow State Center.
- Rewrite Task and Manifest templates so Task owns behavior and Manifest owns
  immutable routing only.
- Remove lifecycle state from Task files, Task Index, Manifest, dashboard
  storage, and permanent execution evidence.

Exit condition: every responsibility has one writable owner and all other
representations are validator-generated views.

### Phase 3: Refactor `spec-package-generator`

- Reduce `SKILL.md` to the safety boundary and routing needed to select the
  current workflow reference.
- Make every material answer an Answer Application Transaction with a
  durable-but-transient, possibly multi-file Candidate recovery packet and one
  consolidated application plan followed by a complete direct-Current rewrite.
- After interruption, resume from Workflow State plus exact Candidate Plan and
  reclassify every canonical target against Current; there is no recorded
  operation progress or free-form cursor.
- Generate artifacts from current owners rather than replaying decisions or
  copying prior generated views.
- Rewrite Dashboard as one latest-only read-only User View for Task count, brief
  Task selection context, and copyable Manifest-backed execution Prompts. Remove
  `localStorage`, editable lifecycle state, export, and reconciliation behavior.
- After exact question-Plan reconciliation, automatically write one deterministic
  compact Decision Card, garbage-collect that question's Candidate material, and
  return to the clean between-question checkpoint. Do not run final validation or
  set `pass` per question. Only explicit User finish plus Controller completion
  and matching full `VALID` may finalize `pass`.

Exit condition: the workflow cannot activate another question until the
previous answer has been applied exactly, archived deterministically, and its
Candidate data cleaned; no intermediate full validation is required.

Every explicit package finish ends with a complete Validator run. No partial or
focused check may authorize Implementation. `DEC-028` fixes the
three-failure circuit-breaker and human handoff semantics. `DEC-029` stores its
cross-session control in one strict, atomically replaced, validator-owned JSON
artifact outside Current. Package validation remains read-only: only the
validator control artifact is mutable. SQLite remains a
future option only if concurrent writers or retained query history become real
requirements.

### Phase 4: Refactor `implement-spec-task`

- Qualify one Task from its immutable Manifest plus current Task Lifecycle
  State.
- Treat implementation defects as `changes-requested` without revising specs.
- Treat authoritative behavior changes as `spec-revision-required`, stop, and
  hand one temporary Spec Change Request to the generator workflow.
- Delete temporary execution/revision records after their current result has
  been consolidated into specification, project context, or lifecycle state.

Exit condition: implementation cannot write normative specifications, cannot
accept a Task, and cannot be interrupted twice by the same resolved condition.

### Phase 5: Migrate Existing Packages Through Final Current Validation

For each package:

1. Require no active Q/Candidate/attempt/competing migration, then inventory every
   legacy file plus active definitions, references, Task states and routing.
   Existing ordinary residue is resolved by a human before migration starts.
2. Initialize the six-counter allocation floor from the maximum observable raw
   active/legacy suffix and an optional trusted User minimum. Through separately authorized `package migrate`, build the registered
   project-scope migration plan: every legacy source path/fingerprint has one
   convert/merge/retire disposition and exact final target bindings. Do not add
   raw paths, kinds, or migration progress to ordinary Application Plan or
   Workflow State.
3. Migration uses symbolic new-ID handles; after floor initialization, Adapter
   captures the five Specification baselines, atomically reserves/substitutes
   contiguous ranges, writes the sealed Plan, and delegates exact writes to Controller.
   Remove a legacy file
   with retained meaning only after that meaning exists in its new owner;
   redundant, historical, or non-authoritative files may be retired directly.
4. Reconcile interruption from actual source existence/fingerprints and exact
   target states until every operation is complete and no legacy file is
   unaccounted. `package resume` refuses ordinary work while migration-plan
   exists but dispatches the unique migration apply/validate/cleanup resume path.
5. After Controller confirms the sealed migration plan is complete, run full
   validation with generic `transaction_kind: migration`; repair Current under
   that bounded transaction until `VALID` or handoff.
6. On matching `VALID`, atomically enter the null-binding finalizing cleanup
   marker, delete the migration plan/transient material, recheck all evidence,
   and let Controller set final `pass`. Migration history is not retained.
7. Run execution qualification twice without changing files.

Migrate pre-booking first because it is blocked and supplies the red regression
case. Migrate dimflow second because it demonstrates real completed work while
exposing duplicate state and dangling evidence references.

Exit condition: pre-booking has no pinned/mutable overlap or stale immutable
digests; dimflow has no Task/Index lifecycle disagreement or missing current
evidence references; both qualify deterministically without historical inputs.

### Phase 6: Remove The Old Control Plane

- Apply every exact disposition in the 43-row responsibility matrix; retire all
  rows marked retire/render-without-persistence after their replacement behavior
  is verified.
- Remove obsolete template fields, permanent prompt files, checklists,
  hand-authored readiness reports, dashboard-local lifecycle state, and
  historical execution indices.
- Delete tests that exercise retired shallow owners after equivalent behavior
  is covered through the Specification Package Validator interface.

Exit condition: searching the skill finds exactly one rule owner for ID schema,
workflow sequence, lifecycle, routing, output responsibility, and validation.

## Verified Package Baseline

The 2026-08-06 read-only comparison established the regression baseline:

| Signal | dimflow-work-assistant | pre-booking |
|---|---:|---:|
| Manifests | 6 | 8 |
| Manifests declaring `raw_digest_pinned: false` | 6 | 0 |
| Current pinned-digest mismatches | 0 | 29 |
| Human-accepted Tasks in Task Index | 4 | 0 |
| Accepted Task files still saying `not-started` | 3 | 0 |
| Referenced local evidence paths not present | 22 | 0 |

Dimflow's own workflow status records that Manifest v3 raw-pinned the mutable
Task Index and that Manifest v4 removed the conflict. This proves the skill can
support implementation after a local routing correction, while its remaining
state duplication and dangling evidence still cause correction churn.

## Completion Criteria

- Mutable lifecycle changes do not change any immutable Manifest digest.
- Every current ID has one definition and every current reference resolves.
- Removing an ID fails until all managed current references are updated or
  removed, then leaves zero old-ID occurrences after final Current validation.
- A failed or interrupted answer application keeps the same Active Question
  State and prevents the partially rewritten Current from driving development.
- Normal generation, readiness, resume, and implementation never load the
  Decision Archive or Git history.
- Both existing package migrations pass validation and repeated execution
  qualification without manual document repair.
- The retired files and fields no longer appear in skill instructions,
  templates, validators, or tests.

## Post-DEC-070 Assurance Audit

Three independent read-only reviews compared the current design from Validator,
AI-maintenance, and interruption/red-team perspectives. All retained the
exact-delta Application Plan architecture; none found that an ID-only Change
Set, persistent progress ledger, or permanent history could satisfy the same
requirements with less risk.

### Compared Architectures

| Architecture | Interruption recovery | Omission / unintended-edit proof | Maintenance and context | Result |
|---|---|---|---|---|
| Current plus final Validator only | Cannot recover intended unfinished work | Finds illegal residue, not planned-but-missing work | Lowest | Insufficient |
| Active ID Index plus explicit old-to-new transition map | Recovers ID membership intent only | Mapping alone proves neither exact content nor dependent updates | Low, but duplicates add/remove operations | Insufficient |
| ID-only Change Set plus Workflow State | Recovers removed/added scope | Cannot classify same-ID payloads or third-state conflicts | Low | Insufficient |
| Workflow State plus cursor/checklist | Appears resumable | Non-prefix completion and stale checkboxes can lie | Duplicate mutable progress | Reject |
| Full Candidate mirror plus promotion | Strong snapshot comparison | Detects broad differences but still not semantic correctness | Duplicates the complete specification and promotion machinery | Too heavy |
| Event log, SQLite, Git/worktree, or write broker | Strong replay/concurrency features | Still cannot prove human semantic intent | Adds history, service/repository state, compaction, merge, or credential recovery | Outside MVP |
| Exact-delta Plan plus AI manually rewriting Current | Strong for listed targets | Listed targets are checkable; payload is written twice | Moderate and avoidably error-prone | Incomplete |
| Exact-delta Plan plus Controller application and expected-final fingerprint | Strong for listed targets and crash resume | Prevents both unsatisfied Plan deltas and unlisted valid Current edits from reaching `pass` | Bounded temporary impacted payloads; one final digest | Selected direction |

An explicit `id_transitions`/old-to-new map is not required for application or
final residue validation. Record operations already derive removed IDs from
present-to-absent and added IDs from absent-to-present. The final Validator needs
only the active Index/definition agreement and a complete Current occurrence
scan. Do not add a second mapping unless a future confirmed consumer needs split,
merge, or migration topology rather than exact target application.

### Selected Assurance Model

The minimum closed model is:

1. AI submits each complete intended payload once with symbolic new-ID handles.
2. Controller validates the symbolic set, captures the allocation baseline,
   atomically reserves contiguous ID ranges, substitutes numeric IDs, writes and
   seals the Plan; AI neither chooses suffixes nor copies payloads into Current.
3. Controller extracts the visible Q's declared Current-ID subjects and rejects
   an answer that introduces undeclared Current IDs, or a Plan that omits any
   subject or updates a frozen subject in place; no second `affected_ids` or
   transition map is maintained.
4. Before the first Current write, Controller reads the complete normative and
   routing Current set, virtually applies every operation, and persists one
   `expected_final_current_fingerprint` inside the sealed Plan. Derived Views are
   excluded under DEC-045.
5. Plan seal freezes every Record in virtual-final authoritative Current.
   Controller applies each target through target-specific read/modify/atomic-
   replace behavior. Multiple logical targets in one physical YAML owner are
   consolidated into one physical replacement.
6. Resume classifies every unique target independently as pending, complete, or
   conflict. It never resumes from array position or a persisted progress flag.
7. Once every listed target is complete, the actual complete Current fingerprint
   must equal the expected-final fingerprint. A mismatch proves an unlisted or
   otherwise unexpected change; because the MVP stores no baseline snapshot, it
   fails closed for human recovery rather than spending three speculative repair
   cycles.
8. For a question Plan, exact reconciliation writes the deterministic DEC and
   cleans Candidate but does not run the full Validator or set `pass`.
9. Only explicit User finish plus Controller package-completion predicates runs
   the full Validator over file legality, Index/definition equality, graph,
   legacy residue and independent Current/rule/allocation/engine fingerprints.
   On deterministic `INVALID`, State is cleared first and a no-Q
   `basis: validation` repair Plan binds the prior result. Matching `VALID` plus
   cleanup/evidence recheck permits `pass`.

This closes execution omission and unlisted byte-valid edits without preserving
old specification history. It still cannot prove that AI chose every semantically
affected target or that an after payload matches human intent. ID replacement
and reverse-reference closure make encoded relationships mechanical. DEC-073/
083 eliminate the residual same-ID gap by freezing every Record in each sealed
Plan's virtual-final Current.

### P0 Contract Status

DEC-071 through DEC-087 close the architecture choices below. They remain P0
implementation work until encoded in catalogs, Controller/Validator code, and
fixtures; the list is no longer a menu of competing designs.

1. Define the closed Plan schema: question-or-validation basis, five-class
   allocation baseline, expected-final Current fingerprint, canonical target
   uniqueness, target/payload identity, and absent/present truth table.
   Absent-to-absent and canonical no-op operations are illegal. Validation basis
   alone may replace a malformed whole structured role using an exact raw-invalid
   before fingerprint and complete valid after payload.
2. Make Controller the only supported Current applier. Define virtual
   application, physical-file batching, same-directory temporary writes, and
   atomic replacement; do not claim cross-file atomicity.
3. At sealing, derive every removed ID from operations, enumerate its
   schema-scanned reverse references, require their logical owners to be Plan
   targets, and require the virtual final graph to contain zero removed IDs.
   Also require one operation for every Current ID token declared in the visible
   Q; reject answer-only IDs and require frozen subjects to be removal targets.
4. Encode the Blueprint's three-field question/finish/repair/migration State and
   cross-file resume table. A changed sealed Plan is conflict. Repair first
   clears State, then deletes/replaces the stale Plan; cross-file atomicity is
   never claimed and the consumed INVALID Plan hash cannot reseal.
5. Make question finalization idempotent: deterministically project Q/answer into
   an ID-free DEC, append by same-ID/same-content replay, clear bindings as the
   commit marker, and clean Candidate. This never means package `pass`.
6. Encode explicit User finish plus the versioned Controller completion profile:
   no active work, at least one REQ/BDD/DESIGN/TEST/TASK, graph closure, and exact
   Manifest/Task-State coverage. The validating transition is the durable finish
   authorization; only then run full validation and permit `pass`.
7. Implementation preflight requires legal `phase: pass`, no Candidate/retry/
   migration transaction, completion predicates, and an exact generic Validation
   Result match for Current, rules, allocation and Validator/canonicalizer.
8. Repair attempt state stores only count and last explicitly evaluated
   kind/fingerprint/result. Package fingerprint covers the complete raw input
   closure, not only Current. Normal transitions do not count; attempt is written
   before result; changed corrections including A/B/A consume once; the third
   changed repair may succeed, but a third still-INVALID result stops.
9. Enforce the DEC-007/019 clarification: no permanent symmetric supersession
   link or tombstone survives in Current/History; tests must reject either form.
   Any replacement meaning remains temporary in Q/discussion and exact Plan
   operations.
10. Encode the six-counter Controller allocator plus five-Spec-class Plan
   allocation-baseline proof. AI uses
   symbolic handles; each class's new IDs exactly fill the reserved range above
   baseline. Active maximum, gap filling, decrement, wrap, archive scan and
    AI-selected suffixes are forbidden; Q/DEC use the reserved DECISION suffix,
    and every initialized Feature retains the file.
11. Enforce seal-time freeze for every Record in virtual-final Current. Same-ID
    canonical content mutation afterward is illegal; no implementation-history
    predicate remains.
12. Add rejected legacy patterns including AC/SCR to ID Schema, prohibit YAML
    comments in authoritative/routing and Decision files, and raw-scan residue.
    Candidate prose/Views remain outside this scan.
13. Allocate the shared Q/DEC suffix from the allocator's `DECISION` counter;
    normal allocation never scans History IDs/content. Migration alone seeds the
    counter from observable Q/DEC values plus an optional trusted floor.
14. Implement deterministic full `INVALID -> planning(null,null) -> validation-
    basis repair Plan` under one attempt budget. `ERROR`, semantic uncertainty,
    non-representable repair, or expected-final mismatch stops immediately.
15. Keep ordinary Plan free of raw paths/kinds. Implement legacy conversion
    through a separately registered sealed project-scope migration plan with
    raw source fingerprints, allocation floor, generic migration validation, and
    finalizing-marker cleanup.

### P1 Documentation And Test Gaps

- Synchronize Blueprint, Context, File Contract examples, templates and migration
  adapter on the unordered exact target envelope and DEC-082 through DEC-087.
- Remove stale "locked Current rewrite", persisted completed-operation, required-
  missing-file, and permanent supersession wording from remaining Skill sources,
  templates, examples, and tests; historical interview analysis may retain
  clearly superseded proposals.
- Add fixtures for per-question no-PASS, explicit finish incompleteness, symbolic
  allocation and reuse rejection, unlisted valid edits, A/B/A repair, every
  Q/Plan/result/DEC/cleanup crash window, legacy residue/comments, migration
  floor/cleanup, and preflight with stray Candidate/attempt/migration files.

## Remaining Work, Not Open Architecture

The physical layout, Validator interface, derived-View policy, Dashboard scope,
Decision Card shape, exact Plan/write ownership, freeze rule, no-reuse allocator,
repair transition, State matrix, finalization, and qualification are decided.
Remaining blocking work is finite translation rather than another architecture
choice:

- encode the completed 43-template/programmatic-producer disposition matrix and
  retained Gate-role classification in repository checks;
- encode the Blueprint's closed REQ/BDD/DESIGN/TEST/TASK Content Schemas and
  graph cardinality rules;
- executable Package Schema/File Contract/File Guide/ID Schema catalogs;
- Controller/Validator/migration adapter implementations and fixture matrix.
