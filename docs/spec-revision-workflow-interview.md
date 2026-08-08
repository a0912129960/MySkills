# Specification Revision Workflow Interview

This is the durable memory for the current `grill-with-docs` session. Its only
inputs are the current repository and `spec-skill-handoff.md`; the two earlier
proposal files and `.scratch` interview history are intentionally excluded.

## Goal

Make specification revision safe under continuous change without letting
historical documents, duplicated lifecycle state, digest self-invalidation, or
execution-routing omissions repeatedly interrupt implementation.

## Confirmed Constraints And Decisions

| ID | Decision |
|---|---|
| DEC-001 | Retain the execution control plane and prefer prevention because uncontrolled AI scope changes have caused real damage. |
| DEC-002 | Every control must reduce total human attention; humans authorize decisions but do not manually maintain generated documents. |
| DEC-003 | The same underlying problem must not interrupt execution twice. Mutable state is centralized, immutable constraints stay near their owner, and derivable copies are removed. |
| DEC-004 | Keep Gate 1, Gate 2, and final packaging; add revision as an orthogonal dimension. |
| DEC-005 | Compute revision impact at Specification ID level, not file level. Traceability is derived and regenerated from links owned by normative artifacts. |
| DEC-006 | Superseded by DEC-016. The original permanent cross-stage Decision Record would remain coupled to current artifacts and control flow. |
| DEC-007 | Superseded on its freeze boundary by DEC-073. Its retained rules are that a frozen Specification Item changes through a fresh replacement ID, final Current retains no old ID/link/tombstone, and an accepted Task behavior change uses a Rework Task rather than resetting the old Task. |
| DEC-008 | Move Task Lifecycle State out of normative artifacts and execution manifests into one independent mutable state owner. |
| DEC-009 | Do not add QMD or another external dependency; verified implementation facts return through the verified context update flow. |
| DEC-010 | Use a closed ID-prefix schema. IDs identify; classification lives in fields. Standardize questions on `Q-`, tests on sequential `TEST-nnn`, and retire `FR-`, `PRJ-`, `SCN-`, and `OQ-`. |
| DEC-011 | Validator findings have two severities: deterministic consistency violations fail closed; semantically ambiguous anomalies are reported for AI investigation. |
| DEC-012 | When implementation discovers new reusable project facts, convergence and a verified context update are required rather than optional. |
| DEC-013 | Superseded by DEC-019. Acceptance becomes current lifecycle state and does not permanently reference a historical Execution Record. |
| DEC-014 | Superseded by DEC-015. The initial decision to retain isolated historical items was reversed after considering legacy projects and AI context cost. |
| DEC-015 | Superseded in its Candidate/promotion mechanism by DEC-035. Its retained rule is one current-only working package with no historical specification subsystem or normal Git-history loading. |
| DEC-016 | Retain past questions and decisions only in one cold Decision Archive because their rationale has historical value. The archive has no normative authority, current-artifact references, digest/invalidation/traceability/readiness/Gate role, or default resume-loading role. Active blocking questions live only in minimal current workflow state and are removed after application. |
| DEC-017 | Retained only for indivisible answer application and one-question sequencing. DEC-035 replaces isolated Candidate validation/promotion with a final direct-Current rewrite and validation. Failed application remains on the same question as `answered-pending-application`; decisions are never batch-replayed from history. |
| DEC-018 | Preserve Gate 1, Gate 2, final packaging, confirmation semantics, and one-question sequencing. Replace only the distributed decision control plane with Active Question State, Answer Application Transactions, direct normative ownership, and a decoupled cold Decision Archive. |
| DEC-019 | Permanently retain only cold question/decision history. All old Specification IDs and other consumed historical records are removed from the working package during the validated Current rewrite after their result is represented in current specification or lifecycle state; Git history remains untouched and unused by normal Skills. |
| DEC-020 | The Current ID Index is authoritative only for the set of active Specification IDs. It does not record definition locations or relationships; the validator discovers those from the small managed file set using the ID Schema. During the active Current rewrite, Index removal drives synchronized update/deletion before final validation. DEC-065 makes same-Feature concurrent mutation unsupported and removes any general lock/CAS claim. |
| DEC-021 | Use one bundled machine-readable `references/id-schema.yaml` as the sole authority for ID classification, closed prefixes, definition markers, allowed/required artifact patterns, and deterministic relationship rules. AI and validator consume the same schema; no Markdown duplicate is maintained. |
| DEC-022 | Accept the complete file-responsibility inventory as the target ownership baseline. Keep minimal `SKILL.md` routers; assign architecture, workflow, ID Schema, output catalog, and validation one owner each; let templates own shape only; make generated indices, reviews, reports, and dashboards non-authoritative; and resolve the remaining boundary details before implementation. |
| DEC-023 | Superseded by DEC-047. It established compact immutable Decision Cards instead of transcripts, but its seven-field content shape was larger than the accepted minimum viable archive. |
| DEC-024 | Give every ID Record exactly two common fields: `id` and `content`. The ID Schema derives the class from `id` and defines that class's required content shape; the Specification Package Validator fails closed on malformed content, invalid ID-valued fields, or class/owner disagreement. No other metadata is common to all records. |
| DEC-025 | Store authoritative ID Records as standard YAML multi-document streams grouped by owning concern. Each `---`-delimited document contains exactly `id` and `content`; do not add a list wrapper, embed the authority inside Markdown, or create one file per ID. |
| DEC-026 | Use one small domain-specific declarative language in the sole `id-schema.yaml`, interpreted by one generic Specification Package Validator. The schema declares ID patterns, owners, scopes, content shapes, and ID target classes; a built-in meta-schema validates the schema itself. Do not use full JSON Schema or class-specific validator implementations. |
| DEC-027 | Treat the final Current Specification Set as a closed-world Managed Package File set. One validator inventories and checks every existing file after the complete rewrite, rejects unknown or unclassified files, scans normative managed text for current and removed IDs, and validates structured records and relationships. DEC-062 defines the final three-repair circuit breaker. DEC-048 removes missing-file and inactive-View freshness enforcement from this scope. |
| DEC-028 | Superseded in its counting boundary by DEC-062. Its retained rules are one circuit breaker per Answer Application Transaction, no reset caused by AI edits or changed findings, a consolidated human-assistance report after exhaustion, and immediate stop on Validator `ERROR`. |
| DEC-029 | Refined by DEC-084. Persist retry enforcement in one transient Validator-owned JSON artifact outside Current; it stores only count and the last explicitly evaluated kind/fingerprint/result, uses atomic replacement, and has no findings/history/lock field. Do not use SQLite unless concurrent writers or retained query history become real requirements. |
| DEC-030 | Use IDs as the mandatory anchors for current normative relationships. Every content unit referenced by another current Specification Item, Test, Task, contract, or validation rule must be an ID Record; machine-relevant dependencies use schema-declared ID-valued fields rather than file paths, headings, or copied prose. Unreferenced supporting explanation needs no ID. The validator derives forward and reverse reference graphs so a changed or removed ID exposes every required synchronized update. |
| DEC-031 | Use a three-layer ID architecture: the sole `id-schema.yaml` defines each ID class, ID format, content schema, relationship rules, and exactly one definition-owner role; when that class has Records, they exist only in the role's one YAML multi-document definition file; any number of managed consumer files may reference those IDs through schema-approved reference positions. The Current ID Index continues to own active membership only and does not duplicate owner locations. |
| DEC-032 | Do not extend Specification Package Validator policy to conversations or arbitrary repository documents. Its exhaustive occurrence and relationship checks cover only declared Current Managed Package Files plus its validator-owned control artifact. Candidate planning, chat, and unrelated files are neither parsed nor treated as specification authority. |
| DEC-033 | Use one in-content reference mechanism at the point where a managed record depends on an ID. Do not maintain document-end reference lists, parallel metadata reference lists, or a second representation of the same edge. The ID Schema declares the exact in-content marker grammar and the validator extracts the graph directly from those markers. |
| DEC-034 | Bound exhaustive validation and normal Skill authority loading to explicit Managed Package Roots containing files that affect specification generation or development. Every file inside those roots is closed-world and must have exactly one role; files outside are not occurrence-scanned or treated as specification authority. Exact external evidence paths may be verified separately without scanning their containing repositories. |
| DEC-035 | Candidate is temporary discussion/planning recovery, never a complete replacement or validation target. Actual changes apply directly to Current. As refined by DEC-082, full legality validation runs only after explicit whole-package finish, not after each question Plan; only matching `VALID` plus Controller `pass` permits development. |
| DEC-036 | Candidate preserves one interrupted question and exact Current-application Plan; Workflow State is the sole resume phase/binding owner and progress is Current-derived. As refined by DEC-082, exact per-question completion writes its compact DEC and cleans Candidate, while explicit package finish alone authorizes final validation and `pass`. |
| DEC-037 | Automatically create one compact Decision Card for every confirmed material decision. This cold archive is the only retained history and is excluded from normal AI loading, Current graph/semantic validation, readiness, resume, implementation, and—after DEC-087—normal allocation. Its own File Contract still checks shape, comments and forbidden ID tokens. Candidate drafts, progress, repair data, summaries, old results, old IDs/content are deleted. |
| DEC-038 | Retained as the physical/bootstrap part of DEC-041. Use one Skill-bundled `references/package-schema.yaml` as the only executable physical-architecture authority. Feature Packages do not contain editable copies; ID Schema refers to owner roles rather than paths. DEC-041 moves parser/check contracts and AI-facing purpose out of this file so Package Schema owns only physical/operational role facts and cross-layer keys. |
| DEC-039 | Package Schema coverage is closed over output producers, not only existing Feature files. Every retained template from both `spec-package-generator` and `implement-spec-task`, every programmatic generator, every project-scoped output, and every non-persistent renderer must map to exactly one declared output role. Templates cannot own paths. All 43 current templates require an explicit migration disposition, retired producers are removed rather than legitimized in the final schema, and unregistered output is a hard failure. |
| DEC-040 | Separate migration completeness from final architecture validity. The 43-row matrix uses exactly `rewrite`, `merge_replace`, `render_none`, `retire`, or `external_current`; rewrite retains the sole template producer, merge_replace deletes a source after merging into the named replacement, render_none becomes non-persistent, retire has no replacement, and external_current moves to a registered project-scope producer. Final Package Schema contains only accepted producers/roles. |
| DEC-041 | Use three joined file-knowledge catalogs keyed by one closed `file_role`: `package-schema.yaml` solely owns canonical path/pattern, producer, permitted multiplicity, writer, authority, lifecycle, cleanup, and contract/guide keys; strict `file-contracts.json` solely owns parser, structural shape, deterministic checks, and ID-scan mode; concise `file-guide.yaml` solely owns AI-facing purpose and usage. The Package Controller joins only requested roles. Cross-layer meta-validation fails on missing, orphaned, duplicated, cyclic, or ownership-violating catalog definitions. DEC-048 clarifies that catalog completeness is validated but Feature file presence is not. |
| DEC-042 | Each existing `<project>/.ai-dev/features/<feature-name>/` is a closed Feature Package Root permitting only four top-level directory names: `current/`, `candidate/`, `history/`, and `control/`. No other root files or directories are allowed. Child paths exist only when implied by Package Schema roles; default maximum directory depth is two, dynamic directories are forbidden, and dynamic leaf files must bind to active IDs. Skill definitions and project-scoped Current Context remain outside this Feature tree under separate schema scopes. DEC-048 clarifies that Validator does not require all four directories or any file to be present. |
| DEC-043 | `current/` contains only `id-index.yaml`, `records/`, `manifests/`, and `views/`; there is no generic `artifacts/`. Records are the sole normative specification owners, Manifests own immutable execution routing only, and Views are one-way, non-authoritative renderings generated exclusively for User inspection/confirmation from validated Records. AI generation and Implementation cannot use Views as specification inputs. User feedback on a View enters Candidate, changes Records, and regenerates the View. Non-user-facing derived output must render without persistence or receive another explicitly justified schema role; it cannot be placed in Views as a catch-all. |
| DEC-044 | Each User Review View is a latest-only singleton cache at one Package-Schema-declared canonical path. Confirmation does not delete it. The renderer atomically overwrites that same file only when new information must be shown to the User; dated, versioned, copied, or append-only View history is forbidden. The View remains generated, non-authoritative, and excluded from normal AI generation and Implementation specification inputs. |
| DEC-045 | A retained User Review View may remain stale when no User display is requested. View bytes and their ID occurrences are excluded from the authoritative Current fingerprint and removed-ID occurrence gate, while the Validator still enforces their declared path, singleton cardinality, format, non-authoritative marker, and source-fingerprint shape. Before display or confirmation, the Controller compares the embedded source fingerprint with the current source Records and atomically overwrites the same View on mismatch. Confirmation binds to the displayed source fingerprint and fails if its source Records change during review. |
| DEC-046 | Do not add a visible stale/non-authoritative notice to retained User Review Views. Direct filesystem opening is an explicitly freshness-unverified convenience path; only Controller-mediated display and confirmation are freshness-guaranteed. This accepted limitation does not weaken the machine-readable source fingerprint or the rule that Views never act as specification inputs. |
| DEC-047 | Use the minimum viable cold Decision Card. `history/decisions.yaml` is one YAML multi-document stream; each card has a `DEC-nnn` archive ID and exactly the common `id`/`content` envelope, while `content` contains exactly two required non-empty strings: `question` and `decision`. Do not add date, Gate, rationale, rejected alternatives, consequence, optional metadata, transcripts, current or removed Specification IDs, or duplicated Current text. Future fields require an explicit schema version and archive migration rather than ad hoc AI expansion. |
| DEC-048 | The Specification Package Validator checks the legality of files that actually exist; it does not manage whether a file should currently exist, workflow state, readiness, applicability, or `not-applicable`. Every existing file must match one allowed role, canonical name/path, permitted multiplicity, parser/content contract, ID rules, and relationship rules. Package Schema expresses permitted multiplicity rather than minimum required presence, and missing-role findings or conditional-presence evaluation are forbidden in the Validator. An absent definition can still invalidate an existing reference or ID Index entry because that existing content is illegal, but absence alone is not a finding. |
| DEC-049 | Separate legality from completion. Validator returns `VALID`, `INVALID`, or `ERROR` for the exact existing-file and schema fingerprint; it never returns workflow `PASS`. The Package Controller and Workflow State Center solely own whether approved operations and outputs are complete. Only after completion is established and a matching Validator `VALID` exists may the Controller finalize and set workflow state to `pass`. Implementation requires both the matching `pass` state and `VALID` result and never infers readiness from legality alone. |
| DEC-050 | Implement the minimum Validator as one Python 3.10+ command-line package using ordinary files as the sole data authority and PyYAML 6.0.3 as an explicitly declared specification-workflow dependency. Keep YAML/JSON parsing, path classification, ID graph checks, fingerprints, finding codes, locking, and temporary-file-plus-atomic-replace behavior behind one CLI/module boundary. Do not reuse another Skill's private environment, write a YAML parser, introduce SQLite, run a service, or require a plugin unless future concurrent writers or retained query workloads demonstrate the need. |
| DEC-051 | Migrate one existing Feature Package per Candidate/Workflow-State transaction using a finite Controller-owned operation list that accounts for every legacy file as convert, merge, render, or retire. Apply idempotent writes and deletions directly to Current. A legacy file with retained meaning is removed only after that meaning exists in its new owner; redundant, historical, or non-authoritative files may be retired directly by their recorded operation. Finalization requires every migration operation complete, zero unaccounted legacy files, Validator `VALID`, Candidate cleanup, and then Controller-owned workflow `pass`. Validator never owns or enforces the migration checklist. |
| DEC-052 | Retain one simplified latest-only read-only Dashboard View because the User needs one place to see how many Tasks exist, briefly understand what each Task does, and copy its execution Prompt. The Dashboard is a generated singleton at one canonical path, has no authority, and is excluded from normal AI/Implementation inputs. Remove browser-local lifecycle state, editable controls, status export/reconciliation, and any duplicate ownership of readiness, task status, scope, tests, or specification meaning. |
| DEC-053 | The minimum `current/views/dashboard.html` displays exactly feature name, total Task count, dependency/order summary, and one card per Task containing Task ID, title, one-sentence outcome, dependency IDs, Task link, Manifest link, and a copy button for `$implement-spec-task <manifest-path>`. It is generated from current Task Records and immutable Manifests. Exclude mutable Task status, `localStorage`, status export, readiness, paths, tests, evidence, traceability, risks, and full acceptance content; detailed review follows the authoritative Task link and current eligibility is enforced by Controller/Implementation preflight. |
| DEC-054 | Do not reconstruct the missing legacy `docs/adr/0003-scope-specification-revisions-by-id.md`. No executable Skill instruction, template, or runtime path depends on it; its exact path appears only in the permitted handoff and planning notes. Current rules belong in the new schemas and Current owners, newly confirmed material decisions use the minimum Decision Card, and unknown historical rationale is not inferred. Remove the obsolete missing-ADR planning note when this planning packet finalizes; generic project-ADR discovery remains unchanged. |
| DEC-055 | Do not add a mandatory second User confirmation after every material decision. The answer authorizes its exact Current rewrite; Controller reconciliation governs question completion, while existing Gate/final review and explicit package finish govern final validation/readiness. Deterministic checks cannot prove semantic equivalence to human intent. |
| DEC-056 | Define seven closed ID classes in the single `id-schema.yaml`, separated by scope. Current contains exactly `REQ-nnn`, `BDD-nnn`, `DESIGN-nnn`, `TEST-nnn`, and `TASK-nnn`, owned respectively by `requirements.yaml`, `bdd.yaml`, `design.yaml`, `tests.yaml`, and `tasks.yaml`; only these enter `current/id-index.yaml` and the normative Current graph. Transient Candidate/Control uses `Q-nnn`, and cold History uses `DEC-nnn`; both formats and scope rules are still defined by ID Schema but neither enters Current. Validator rejects every ID occurrence outside its schema-approved scope. PRD/EARS render from REQ meaning, while Test level and Task type are content fields rather than ID subtypes. |
| DEC-057 | Treat Q as active decision-recovery data, never history. Retain it through interrupted discussion/application or failed DEC writing; after exact question Plan reconciliation and deterministic DEC commit, clear bindings and delete Q before another question or finish. DEC-082 removes the earlier per-Q matching-VALID requirement. |
| DEC-058 | Define one active bounded `Q-nnn` only in `candidate/question.yaml` with exact `id`/`content.question`/`content.answer`; other files may reference but not redefine it. DEC-086 adds declared-subject and no-new-ID-in-answer rules. File Contract owns shape and Controller owns phase legality/cleanup. |
| DEC-059 | Superseded by DEC-087 because archive-ID scanning made cold History a control dependency. Retained rule: each Q and its resulting DEC share one suffix and same-Feature concurrent mutation remains unsupported. |
| DEC-060 | Superseded on field count by DEC-076. Its retained rules are that Controller solely writes Workflow State and derives `next_action`; State never stores prompts, timestamps, prose status, errors, retry counts, question content, duplicated validation status, or operation progress. |
| DEC-061 | Define exactly six Workflow State phases: `discussing`, `planning`, `applying_current`, `validating`, `finalizing`, and `pass`. File Contract owns this closed enum and Validator rejects any seventh value; Controller remains the sole writer and owns transition eligibility. Do not add `idle`, `blocked`, or `error`: absence represents not started, while typed validator evidence and Controller-derived actions represent repair or human-help conditions without changing the durable work phase. |
| DEC-062 | Refined by DEC-084. State legality is checked at Controller/resume entry, pre-write, final validation and Implementation preflight. Narrow legal transitions do not consume retries. One explicit invalid-checkpoint episode permits three changed corrections including A/B/A; identical rerun costs zero, third still-invalid stops, and ERROR/semantic uncertainty/unexpected Current stops immediately. |
| DEC-063 | Refined by DEC-083. `candidate/application-plan.yaml` is a sealed temporary exact-delta Plan, not prose/full Candidate. It uses question or validation basis, allocation baseline, expected-final fingerprint and exact impacted target payloads; no vague instruction, path, progress or old-to-new ledger survives finalization. |
| DEC-064 | Do not persist operation progress and do not add `OP-nnn`. Controller derives each operation's status by comparing the sealed exact delta with Current on every entry/resume and before completion, and returns an ephemeral completed/pending/conflict summary keyed by canonical target. Operations targeting the same Record or file instance must be consolidated so each target appears once. DEC-076 later removes another non-progress fingerprint field without changing this rule. |
| DEC-065 | Retain the coherent DEC-064 architecture: sealed exact-delta Plan, persisted Workflow State, Current-derived per-target progress, Controller-applied Current rewrite, final Validator, three-repair limit, compact DEC history, and `pass` plus matching Validation Result before Implementation. Reject Q-048's lock/CAS/forced-resume layer, ID-only Change Set, and State removal. Same-Feature concurrent mutation is unsupported. DEC-076 is the permitted narrow refinement because audit proved the fourth field had no reliable unique consumer. |
| DEC-066 | Give every exact-delta Application Plan operation one uniform envelope: exactly one schema-declared target, `before` equal to either `absent` or the exact prior-target fingerprint, and `after` equal to either `absent` or the complete expected target payload. Derive creation, update, and removal from those state pairs instead of storing an operation kind. Controller uses the same comparison algorithm to classify every target as pending, complete, or conflict; no progress field is persisted. |
| DEC-067 | Use a closed target union in the Application Plan without repeating derivable locations. An authoritative Record target contains only `record_id`; ID Schema derives its definition-owner role and Package Schema resolves the file. A fixed declared-file target contains only `file_role`. The MVP's dynamic Task Manifest target contains `file_role: task_manifest` plus `task_id`; do not introduce a generic `binding_id` for hypothetical future roles. Raw paths, generic keys, and duplicated Record owner roles are forbidden. |
| DEC-068 | Encode Application Plan `before` and `after` as explicit closed state objects. `state: absent` permits no fingerprint/payload; `before.state: present` requires exactly the canonical prior-target fingerprint; `after.state: present` requires exactly the complete expected target payload. Controller derives the after fingerprint from that payload and never stores it twice. File Contract rejects missing, extra, or state-incompatible fields, eliminating ambiguous null/empty/magic-string states. |
| DEC-069 | Treat Application Plan operations as an unordered logical set of unique canonical targets. Array position carries no dependency, priority, correctness, or progress meaning. When sealing, serialize operations in a deterministic target order solely to stabilize the Plan fingerprint. Controller derives any safe create/update/remove application sequence and, on every resume, reclassifies all targets independently so non-prefix completion cannot be hidden. |
| DEC-070 | Fingerprint one resolved logical Application Plan target, never its containing file or raw YAML bytes. Record targets hash only their parsed `id`/`content` document; declared structured-file targets hash their complete parsed logical value. One shared canonicalizer uses deterministic JSON-compatible serialization with sorted object keys, preserved array order, UTF-8, no insignificant whitespace, and lowercase `sha256:<64-hex>`. File Contracts reject unsupported YAML types. The same module canonicalizes before comparison, after payloads, Current targets, and the sealed Plan. |
| DEC-071 | Close the Plan-to-Current write gap by making Controller the supported applier of sealed exact payloads; AI writes each after payload once. At seal Controller derives removed-ID closure, virtually applies all operations and stores expected-final Current. All targets and actual Current must match before question commit or repair validation. Mismatch goes to human recovery. Do not add `id_transitions`; remove/add operations and exact dependents already supply its consumers. |
| DEC-072 | Superseded on per-question `VALID`/`pass` timing and cleanup by DEC-082/084. Retained rule: binding clear is the crash-safe cleanup commit marker, same-ID/different-content DEC is an error, and Implementation requires matching final evidence plus no active transaction residue. |
| DEC-073 | Replace DEC-007's ambiguous implementation boundary with a mechanically provable identity-freeze rule. As refined by DEC-083, sealing a Plan freezes every Record in its virtual-final authoritative Current, not only explicit targets; a passed baseline is likewise frozen. Any later canonical `content` change requires a freshly allocated ID, removal of the old ID, reverse-reference closure, and exact dependent rewrites for REQ/BDD/DESIGN/TEST/TASK. |
| DEC-074 | Refined by DEC-083. Retain one Controller-only, Feature-lifetime `control/id-allocation.yaml` with monotonic REQ/BDD/DESIGN/TEST/TASK high-water integers, no old IDs/content, permanent crash/cancel gaps, no decrement/wrap, and migration-floor limits. High-water alone is not fresh-allocation proof; Plan baseline/range reservation supplies that proof. |
| DEC-075 | Superseded on Q binding and cross-file transition by DEC-083/084. Retained rule: deterministic final-validation repair uses another exact Plan and the same bounded attempt episode; `ERROR`, semantic uncertainty, non-representable repair, or expected-final mismatch stops immediately. |
| DEC-076 | Supersede DEC-060/064/065 only on Workflow State field count: remove `reconciled_current_fingerprint` because it cannot distinguish a crash between Current and State writes from an unlisted direct edit without a baseline snapshot/WAL, while target reconciliation and expected-final equality already own recovery and qualification. Retain Workflow State with exactly `phase`, `active_question`, and `plan_fingerprint`; retain all six phases and Current-derived per-target progress. This is a field deletion, not removal of persisted Workflow State. |
| DEC-077 | Superseded by DEC-083. The exact target/before/after envelope and State-based sealing remain; Plan top level is expanded to basis, allocation baseline, expected-final fingerprint, and operations. |
| DEC-078 | Superseded by DEC-082/084. The three-field State and canonical-target resume principle remain; matrix semantics now separate question completion, explicit final finish, validation repair, and migration. |
| DEC-079 | Superseded by DEC-085. Latest-only typed result remains, but generic transaction and allocation evidence replace a Q Plan-only binding; final VALID findings are empty and View content cannot block Implementation. |
| DEC-080 | Refined by DEC-085. Ordinary Plan remains path/kind-free; migration uses a sealed project-scope source inventory with raw source fingerprints, allocation floor, ordinary exact target envelopes, expected-final fingerprint, generic migration validation evidence, and cleanup-marker recovery. |
| DEC-081 | Refined by DEC-086. Question Current-ID tokens are declared subjects, context citations belong in discussion, every subject needs a Plan operation and frozen subjects are removed. The answer may not introduce an undeclared Current ID; Controller must expand/reconfirm the question first. |
| DEC-082 | Separate one-question decision completion from package completion. Exact question Plan reconciliation permits deterministic DEC append and Candidate cleanup but never full Validator execution or workflow `pass`. Only explicit User `package finish` plus the versioned Controller profile—no active work, at least one REQ/BDD/DESIGN/TEST/TASK, graph closure, and exact Manifest/Task-State coverage—authorizes final validation. The validating transition durably records finish authorization; no second Gate/readiness file is added. Validator remains absence-neutral. |
| DEC-083 | Make Plan identity/allocation/repair executable. Application Plan is closed to `basis`, `allocation_baseline`, `expected_final_current_fingerprint`, and `operations`; basis is answered Q or prior full INVALID result. AI submits symbolic new-ID handles; Controller snapshots counters, atomically reserves contiguous ranges, substitutes them, and seals the Plan. Seal freezes every virtual-final Record. Validation repair has no Q/DEC and binds the INVALID result. |
| DEC-084 | Close crash and retry semantics without adding State fields. State keeps exactly phase/Q/Plan hash but admits question, finish, validation-repair and cleanup-marker substates. Repair clears State before deleting/replacing the old Plan, never claims cross-file atomicity, and stale invalid Plan hashes cannot reseal. Attempt state contains only repair count and last explicitly evaluated kind/fingerprint/result; normal transitions do not count, and Validator writes attempt before result. |
| DEC-085 | Use one generic latest Validation Result binding: a raw full-input evaluated-checkpoint fingerprint; independent canonical Current, Package Schema, File Contracts, ID Schema, allocation, Validator and canonicalizer fingerprints; and transaction kind/fingerprint. VALID requires all evidence/empty findings; INVALID binds the raw checkpoint and may null only the semantic digest blocked by its violation; ERROR covers unsafe computation. Current digest excludes control/history/Candidate/Views. Migration uses an observable floor and cleanup marker. |
| DEC-086 | Make decision replay and subject coverage deterministic. Q question/answer are bounded; answer cannot introduce undeclared Current IDs. DEC content is a whitespace-normalized projection replacing Specification ID tokens with one fixed phrase, never an AI re-summary. Binding clear proves DEC commit, so cleanup does not rediscover History. Authoritative/routing YAML and Decision Archive prohibit comments; raw residue scans include AC/SCR and other declared legacy forms, while Candidate prose and Views are excluded. |
| DEC-087 | Remove the remaining cold-History control dependency. Add one `DECISION` high-water integer to the existing Controller allocation state; atomically reserve it before creating Q, and use the same suffix for DEC. Canceled/crashed reservations leave gaps. Normal Q allocation never scans Decision Archive IDs/content. The Application Plan allocation baseline still contains only five Specification counters; migration initializes all six counters from observable values plus an optional trusted floor. |

Terminology migration: historical question text below may use Validator `PASS`.
After DEC-049, read that result as Validator `VALID`; lowercase workflow `pass`
remains the Controller-owned completion state. Superseded Candidate-promotion
proposals remain historical analysis rather than current architecture.
Only the decision table above and the unresolved queue are current contract
summaries. Resolved question bodies below preserve the discussion trail and may
contain explicitly superseded field counts, timing, or recommendations.

## Repository Contradictions Recorded

- `31-final-task-index.md` is digest-pinned while its lifecycle fields are also
  mutable, so a permitted state change invalidates the Manifest.
- Lifecycle state is duplicated across the Task index, Task files, Manifest,
  and dashboard.
- Artifact invalidation is file-granular even though confirmed revision scope
  is ID-granular.
- Decision and question history have separate owners even though the confirmed
  model requires one record.
- The handoff says the Revision Model glossary and ADR 0003 were written, but
  neither exists in the current working tree. The glossary was reconstructed
  here from confirmed handoff decisions; the ADR remains unresolved.

## Deterministic Validator Contract

The confirmed hard failures are: unknown ID prefix; a definition marker in the
wrong owning artifact; duplicate definitions; undefined references; missing
required Tier-1 downstream references; invalid, missing, asymmetric, or cyclic
supersession links; disagreement between the Task index's Task set and the
Task Lifecycle State's Task set; overlap between pinned and mutable paths;
disagreement between the generated Decision Record index and body; acceptance
without an independent Execution Record; and an unhandled downstream ID during
revision.

The confirmed anomaly flags are: an ID used outside schema-declared artifacts;
a current item referencing a superseded ID; and ID sequence gaps.

## Active Question

### Q-001 — Historical authority boundary

- Status: superseded-by-DEC-015
- Depends on: DEC-005, DEC-007, DEC-011
- Question: After supersession, may a historical Specification Item participate in current readiness or execution qualification, or may it only be referenced as historical evidence?
- Why it matters: If historical items remain current validation inputs, stale obligations can continue to invalidate new work; if they are excluded too broadly, audit and accepted implementation evidence can become unverifiable.
- Recommended answer: Historical items never contribute current obligations. Current readiness and execution qualification traverse only active IDs; historical IDs remain referenceable from supersession links and immutable Execution Records, and validation checks their existence and link integrity without applying their old downstream-completeness rules.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; validator traversal and migration semantics depend on it.
- Answer: Agreed with the recommended separation of historical evidence from current obligations.
- Resulting decision: DEC-014

### Q-002 — Implementation boundary for supersession

- Status: resolved-by-DEC-073
- Depends on: DEC-007, DEC-014
- Question: When an AI has already changed real product code for a requirement but the Task has not yet been accepted, may the requirement still be overwritten in place, or must the old requirement be retained and a replacement ID created?
- Why it matters: Using human acceptance as the boundary permits in-progress implementation history to be rewritten; using preflight or red-test creation as the boundary creates historical IDs before any product behavior exists.
- Recommended answer: The boundary is the first immutable Execution Record that reports a production-code or deployable-configuration change intended to satisfy the Specification Item. Preflight, analysis, and red-only test evidence do not cross it. Once crossed, semantic revision requires a replacement ID, even if the Task has not reached `ready-for-review` or `accepted`; partial implementation state remains linked from the Spec Change Request and Execution Record.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; in-place revision, supersession, and partial-change migration all depend on it.
- Answer: Later assurance audit rejected implementation state as an executable
  boundary. Canonical identity freezes at first sealed Plan or validated
  workflow `pass`; no Execution Record or accepted-state history is required.
- Resulting decision: DEC-073
- Clarification history: The initial wording was not understood. Rephrased around the concrete difference between no product-code change and an in-progress product-code change; this is still Q-002, not a new decision.
- Review scenario raised by the user: During review, distinguish an Implementation Defect (code violates a still-correct specification) from a Specification Defect (review evidence shows the approved specification itself must change). An Implementation Defect stays on the same Task through `changes-requested` and does not revise specification history. A Specification Defect preserves the implemented-against Specification Item, records the review and partial implementation evidence in a Spec Change Request, creates a replacement Specification ID, and routes correction through a Rework Task; the obsolete behavior need not remain in the product merely because its historical specification is retained.
- Trust concern raised by the user: In-place edits let AI silently rewrite intent, while replacement IDs can still leave downstream items unmodified. Historical information may help explain code and rejected choices, but loading raw history as current context can also make AI follow obsolete requirements.

#### Q-002 option analysis

| Policy | Benefit | Failure mode |
|---|---|---|
| Always overwrite | Small current package and low ID churn. | Loses intent and code-to-spec history; enables silent weakening; Git history is not an explicit specification lineage. |
| Always create a new ID from first draft | Complete lineage and no destructive semantic edits. | Decision clarification creates excessive ID churn; AI sees a large graph; a new ID alone does not force downstream updates. |
| Freeze confirmed content, revise drafts in place | Uses existing Gate confirmations as the immutability boundary and avoids draft churn. | Requires a strict distinction between draft and confirmed content plus a generated revision transaction. |

Revised recommendation: freeze a Specification Item when its owning Gate or Task Plan is confirmed, earlier than production-code implementation. Any later normative meaning change creates a replacement ID. Before confirmation, draft content may be revised in place, but the Decision Record retains the question and ruling history. Pure presentation or generated-view changes do not create normative IDs. Every replacement is one validated revision transaction: create the replacement, link both directions, derive the Revision Impact Set, update/supersede or explicitly exempt every downstream ID with a reason, regenerate current views, and fail closed if any step is incomplete. Historical content remains cold evidence; normal execution loads only the active item and compact lineage metadata, retrieving old content only for review, migration, regression, or rationale investigation.

### Q-003 — Physical separation of active and historical IDs

- Status: resolved
- Depends on: DEC-014
- Question: Must current normative specification documents contain zero historical IDs, while old IDs are allowed only in a separately stored, explicitly loaded historical evidence set?
- Why it matters: Merely marking an old ID as superseded inside a current document still exposes obsolete content to normal AI retrieval and creates two apparent truths. Removing old IDs from every artifact, including history, would instead destroy auditability and the ability to explain existing code.
- Recommended answer: Current normative documents and current traceability views contain active IDs only. A generated revision transaction removes the old item from the active set and stores its immutable snapshot, lineage mapping, reason, and downstream disposition in a separate append-only history set. Execution Records may reference that historical snapshot. Normal specification generation and execution never load the history set; review, debugging, migration, and explicit rationale queries may load it. The active replacement need not embed the old ID; lineage is owned by the history set.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; it determines whether supersession links live in normative artifacts or in a separate history owner.
- Answer: Use a current-only working package; delete old IDs and old normative specifications after the validated replacement succeeds, while leaving Git history untouched and unused by normal Skills.
- Resulting decision: DEC-015
- User concern: Retaining old IDs in documents may itself be the source of AI confusion and omission.
- Legacy-code challenge raised by the user: Many completed systems have no retrievable historical specification. Therefore specification lineage cannot be a prerequisite for understanding, maintaining, qualifying, or revising existing code.

#### Q-003 revised recommendation after the legacy-code challenge

Historical lineage is useful audit evidence, not an authority or eligibility requirement. When lineage exists because this workflow created it, retain it outside the active set for targeted explanation, regression analysis, or accountability. When it does not exist, never invent or retroactively assign a historical Specification ID. Inspect current code, executable tests, schemas, runtime behavior, release documentation, and user decisions as present evidence; record uncertainty explicitly; and create a new current Specification Item only for behavior now being confirmed or changed. Missing history must not by itself block readiness or implementation.

#### Q-003 second revision after the context-cost challenge

The user prefers deletion because historical material increases retrieval noise, token usage, context size, and hallucination risk. This directly contradicts the initial retention decision DEC-014. Repository evidence supports the concern: the current duplicated decision/question history requires repeated reading of a large corpus while providing no demonstrated execution benefit.

Revised recommendation: use a current-only specification package and do not create a first-class historical specification store. A revision is prepared outside the active package, all downstream references are updated or removed, the candidate active graph is validated, and only then does it atomically replace the current graph. Superseded IDs and their normative content are deleted from the working package after validation. Version-control history may remain as emergency recovery infrastructure but is never a normal Skill input and is not treated as specification authority. Retain historical artifacts only when an explicit external audit, legal, contractual, or rollback requirement exists; none is currently evidenced for this workflow.

### Q-004 — Lifetime of resolved questions and decisions

- Status: resolved
- Depends on: DEC-003, DEC-006, DEC-015
- Question: May question and decision history be retained only as a cold archive after all control-plane authority, readiness impact, cross-artifact references, and default loading are removed from it?
- Why it matters: Permanently retaining every Q&A and superseded ruling recreates the token and stale-context problem even after old specification IDs are deleted. Removing all rationale immediately can, however, make a still-current surprising constraint hard to interpret.
- Recommended answer: Treat the detailed Decision Record as temporary workflow state. After the owning Gate is confirmed, delete resolved question/answer history. Preserve only a concise current rationale beside a still-binding, non-obvious constraint in its owning normative item; do not keep a separate growing decision log. Keep only unresolved active questions during drafting, and delete that register when empty.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; it reverses DEC-006 and determines the status/resume artifact model.
- Answer: Retain decisions because their original rationale has value, but isolate them as a cold archive that does not affect other artifacts or normal AI execution.
- Resulting decision: DEC-016
- Clarification requested by the user: `15-open-questions.md` is the durable interview register. It stores each question, dependency, layer, why it matters, recommended/default answer, affected artifacts, blocking status, human answer, linked Decision ID, and resolution status. `14-decision-log.md` is the normalized-ruling register populated after an answer is clear; it stores the material ruling, affected artifacts, and date. `00-spec-workflow-status.md` separately points to the one active Question ID. The intended flow is question row -> human answer -> normalized decision -> apply to specification -> next question. Their benefit is session resume and preventing repeated questions; their cost is duplicated ownership, manual linkage, and permanent retention of resolved history. In the observed package, both files together are about 346 KB while no question remains open.
- Repository verification: Under the current design these files materially affect other artifacts. `SKILL.md`, `workflow.md`, `status-tracking.md`, and `question-and-decision-governance.md` require reading them during resume and clarification. `artifact-authority-and-invalidation.md` assigns them governance authority. `35a-final-readiness-result` checks `15-open-questions.md`; Gate checklists require both files; source requirement, PRD, EARS, flow/solution sketches, approved baseline, stage manifest, and frontmatter contain Question/Decision ID references. Tests enforce those relationships. Therefore retaining the files without further redesign does affect normal execution and context.
- Revised recommendation: Keep, if desired, one cold question/decision archive outside the Current Specification Set. It has no normative authority, no IDs referenced by current artifacts, no digest or invalidation role, no readiness role, and is never read on normal resume. A compact current workflow-state owner holds only the active blocking question and Gate status. When resolved, its answer is applied to the owning current specification and may be copied to the cold archive, then removed from current workflow state. Explicit rationale/history requests are the only normal reason to load the archive.

### Q-005 — Decision Archive content depth

- Status: resolved
- Depends on: DEC-015, DEC-016
- Question: Should the Decision Archive retain full question/answer transcripts, or one compact decision card per material decision?
- Why it matters: Full transcripts preserve nuance but recreate large, noisy history and may contain abandoned assumptions. Overly terse rulings lose the reason the archive exists.
- Recommended answer: Store one compact immutable card per material decision: Decision ID, date and Gate, precise question, chosen ruling, short rationale, meaningful rejected alternative, and consequence. Do not store chat transcripts, recommended/default-answer scaffolding, status lifecycle, affected current IDs, or duplicated specification text. The archive may be searched only on explicit historical-rationale requests.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; archive schema and migration cannot be defined without it.
- Answer: Use one compact Decision Card per material decision. Do not retain
  full question-and-answer transcripts.
- Resulting decision: DEC-023

### Q-006 — Atomic answer application

- Status: resolved
- Depends on: DEC-003, DEC-015, DEC-016
- Question: Must each answered material question be applied to its owning current specification and validated before the workflow may activate the next question?
- Why it matters: If answers accumulate in a decision log and specifications are updated only after all questioning ends, omissions and contradictory partial interpretations compound. The archive then becomes a hidden specification source. Immediate application keeps one current authority and localizes failures to the answer that caused them.
- Repository evidence: The current `question-and-decision-governance.md` and `status-tracking.md` already intend answer -> normalized ruling -> affected-specification update -> next question ordering, but the duplicated 14/15 registers and widespread ID references make the operation non-atomic and expensive.
- Current recommendation after DEC-035: Treat answer application as one transaction: record the answer in Active Question State, plan the complete impact, apply every currently existing owning specification change directly to Current, validate the complete final Current, clear the active question, and only then write the cold Decision Card and activate the next question. Artifacts not yet created are later derived from the updated Current owner, never replayed from the Decision Archive. If application or validation fails, keep the same active question in `answered-pending-application`; do not ask another question.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; it determines whether omission prevention occurs during clarification or as a risky end-of-interview batch.
- Answer: Agreed that answering, modifying the specification, and successful validation are indivisible and must complete before the next question.
- Resulting decision: DEC-017
- Current mechanism note: DEC-035 later replaced isolated Candidate
  validation/promotion with temporary planning followed by direct Current rewrite
  and one final validation; the indivisible sequencing rule remains.

### Q-007 — Existing architecture retention boundary

- Status: resolved
- Depends on: DEC-004, DEC-016, DEC-017
- Question: Should the three-stage Gate architecture and one-question loop remain, while the existing distributed 14/15/status/readiness decision-control architecture is replaced by Active Question State plus Answer Application Transactions?
- Why it matters: Keeping the product-specification stages does not conflict with atomic application. Keeping the current decision control plane unchanged does: question text, answers, rulings, active IDs, readiness checks, and references have multiple owners and must be synchronized manually.
- Recommended answer: Preserve Gate 1, Gate 2, final packaging, confirmation semantics, and one-question sequencing. Replace only the decision control plane: current workflow state owns the full single Active Question State; current normative artifacts own applied rulings; readiness checks only that no Active Question State remains and the candidate graph validated; 14/15 content moves to a cold archive with no current references or automatic reads.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; it defines whether this is a targeted control-plane correction or a full workflow redesign.
- Answer: Preserve the overall three-stage and one-question workflow; redesign only the distributed decision control layer.
- Resulting decision: DEC-018

### Q-008 — Historical retention policy selection

- Status: resolved
- Depends on: DEC-015, DEC-016, DEC-017, DEC-018
- Question: After comparing AI effects, should the final model retain both historical decisions and old Specification IDs, remove both, or retain only a cold compact Decision Archive while removing old Specification IDs and normative history?
- Why it matters: Full retention maximizes forensic context but burdens normal AI retrieval and graph correctness. Full deletion minimizes current context but removes durable rationale and increases the chance of repeating rejected choices or inventing explanations. The hybrid separates rationale value from obsolete specification authority.
- Current recommendation after DEC-035: Use the hybrid: delete old Specification IDs, normative content, and derived historical views during the complete Current rewrite and require zero residual occurrences at final validation; retain compact material Decision Cards without old Specification IDs in a cold archive that is never loaded automatically or referenced by current artifacts.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; archive schema, migration, validator scope, and normal AI loading rules depend on it.
- Answer: Retain questions and decisions only; delete all other historical records and old IDs. Deletion occurs through validation of a unique current-ID index and synchronized treatment of every file containing a removed ID.
- Resulting decision: DEC-019
- User preference: Retain questions and decisions only; delete all other historical records and old Specification IDs.
- Implication: Spec Change Requests, superseded normative content, obsolete Manifests/prompts/readiness views, lifecycle event history, and detailed Execution Records may exist only while their result is still being qualified, reviewed, or applied. After an Answer Application Transaction, accepted-state transition, or final Current validation has durably written current specification and lifecycle state, those consumed records are deleted. This reverses the handoff's earlier non-goal of retaining SCRs and Execution Records and requires acceptance to be represented as current state rather than a permanent link to an old record.

### Q-009 — Current ID Index authority

- Status: resolved
- Depends on: DEC-005, DEC-011, DEC-015, DEC-019
- Question: Should one Current ID Index be authoritative for active-ID membership and definition location only, while each owning artifact remains authoritative for the ID's normative meaning?
- Why it matters: Removing an ID from a derived index cannot drive cleanup because regeneration would simply rediscover the still-present definition. Making the index authoritative for all specification content would create a large centralized duplicate. Membership-only authority lets removal initiate a complete occurrence cleanup without moving normative meaning away from its owning artifact.
- Current recommendation after DEC-035: During the controlled Current rewrite, remove the old ID from the Current ID Index, derive the complete occurrence/impact set, and update or delete every affected Current file. After all planned changes finish, run the read-only validator. Validation fails if the removed ID appears anywhere in Current, if the index and definitions disagree, or if a current ID lacks its schema-required relationships. Current remains unusable until the complete final validation passes.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; it decides whether the unique index is a comparison view or the active-set control authority.
- Answer: Use one authoritative index for active IDs, but do not record locations because they are faster and safer to derive by scanning the limited file set.
- Resulting decision: DEC-020
- Current mechanism note: DEC-035 later moved index removal and dependent
  cleanup into the locked direct-Current rewrite; no Candidate Index or
  promotion remains.

### Q-010 — Executable ID Schema format

- Status: resolved
- Depends on: DEC-010, DEC-011, DEC-020
- Question: Should ID classification, allowed/required artifact patterns, definition marker rules, and relationship requirements live in one machine-readable YAML ID Schema that both AI and validator consume?
- Why it matters: A Markdown-only policy cannot reliably drive deterministic validation; separate human and machine schemas create another synchronized duplicate. YAML keeps one executable authority while remaining reviewable.
- Recommended answer: Yes. Add one bundled `references/id-schema.yaml` as the sole schema owner. It defines the closed prefix list, category field values, definition marker, allowed definition artifact patterns, allowed/required reference artifact patterns, and deterministic relationship checks. The Current ID Index contains only active IDs and never repeats schema or locations.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; file count, validator inputs, and template frontmatter depend on it.
- Answer: Agreed to one executable YAML ID Schema shared by AI and validator, with no duplicate Markdown rules.
- Resulting decision: DEC-021

### Q-011 — Responsibility consolidation boundary

- Status: resolved
- Depends on: DEC-018, DEC-020, DEC-021
- Question: After the complete file-responsibility inventory, which references should remain separate owners and which should be merged or deleted as duplicates?
- Why it matters: Removing duplicated wording without first assigning one owner per rule can silently remove required behavior or leave references that still force broad context loading.
- Repository inventory: `docs/spec-skill-file-responsibility-inventory.md` covers all 66 current source files, identifies 11 major duplication clusters, proposes 23 retire/merge actions, and identifies 6 missing target authority/template files plus validator support.
- Recommended answer: Accept the inventory's ownership map as the target baseline, not as blanket implementation authorization: minimal `SKILL.md` routers; architecture, workflow, ID Schema, output catalog, and validator each own one concern; templates own shape only; generated indices/reviews/reports/dashboards are non-normative; detailed unresolved merge boundaries remain one-question decisions before implementation.
- Default assumption if unanswered: Apply the recommendation produced by the inventory.
- Blocking: yes; the target file map and migration sequence depend on it.
- Answer: Accept the inventory ownership map as the target baseline. Preserve
  distinct owners only when they have non-overlapping responsibilities; merge
  or retire duplicate control, history, checklist, report, prompt, and status
  owners. This acceptance defines the target architecture but does not
  authorize implementation before the remaining boundary decisions are
  resolved.
- Resulting decision: DEC-022

### Q-012 — Minimal ID Record envelope

- Status: resolved
- Depends on: DEC-020, DEC-021, DEC-022, DEC-023
- Question: Should every machine-readable ID Record have only the common
  envelope `id` plus `content`, while the ID Schema selects a kind-specific
  content schema that owns any required semantic relationships?
- Why it matters: A closed ID prefix and Current ID Index can prove membership,
  but they cannot make free-form Markdown tables or prose definitions reliably
  parseable. `id` establishes identity and selects the applicable ID Schema;
  `content` holds current authoritative meaning in that schema's required
  shape. A universal relationship field appears attractive, but relations such
  as PRD source, BDD coverage, Task dependency, Test ownership, and Decision
  consequence have different semantics and should not be flattened into one
  homogeneous list.
- Local LLM Wiki evidence: The Wiki separates its schema layer from compiled
  knowledge pages; each page uses fixed YAML frontmatter; relationships are
  typed and directional; and executable lint rejects missing required fields,
  invalid relationship types, broken targets, and self-reference. Its identity
  model cannot be copied directly because one Wiki page is one knowledge unit
  identified by path, while one specification artifact currently contains many
  Specification IDs.
- User corrections: The first recommendation copied too much Wiki governance.
  The subsequent three-field proposal still made different record types expose
  a homogeneous `references` field that may duplicate relation meaning already
  required inside their content.
- Repository evidence: Current templates demonstrate that relationships are
  type-specific. EARS owns PRD source and BDD coverage; BDD owns EARS tags; Test
  Contracts own BDD, EARS, artifact, and Task ownership fields; Tasks own Task
  dependencies plus BDD/EARS/Test coverage; Decisions own a ruling and its
  consequence rather than current specification-graph edges. A generic
  `references` list would either erase these meanings or repeat them.
- Revised recommendation: Require exactly two common fields: `id` and
  `content`. `content` is not unrestricted prose. The ID Schema derives the
  record class from `id`, then validates a small class-specific content shape.
  For example, EARS content may require `source` and `statement`; BDD content
  may require `requirement` and `scenario`; Task content may require
  `depends_on`, `covers`, and `outcome`; a Decision Card may require `question`,
  `ruling`, `rationale`, `rejected`, and `consequence`. All embedded ID-valued
  fields are discovered and validated as graph edges. Do not add universal
  `kind`, `references`, title, owner, location, lifecycle, status, timestamp,
  version, confidence, provenance, or history fields. Schema version belongs to
  the bundled ID Schema, digests belong to generated execution routing, and
  mutable state belongs to its separate owner.

#### Q-012 field analysis

| Candidate | AI / validator value | Duplication and drift cost | Recommendation |
|---|---|---|---|
| `id` | Selects identity and applicable content schema | None; indispensable | Common and required |
| `content` | Holds the only current normative meaning | None if it is the sole meaning owner | Common and required |
| `kind` / `type` | Selects validation rules | Duplicates classification already selected by the ID Schema | Exclude |
| `references` | Exposes graph edges | Flattens different meanings and duplicates type-specific relation fields | Exclude as a common field; validate ID-valued content fields instead |
| `title` / `summary` | Improves preview | Restates content and can become stale | Exclude; derive only for views |
| owner / location | Helps navigation | Duplicates validator discovery and creates another location index | Exclude |
| status / lifecycle | Controls execution | Creates the same mutable-state duplication already diagnosed | Exclude; keep in Task Lifecycle State |
| date / version / history | Supports chronology | Reintroduces historical noise and manual maintenance | Exclude from current records |
| confidence / provenance | Supports epistemic knowledge bases | Does not qualify approved specifications and adds judgment fields | Exclude |
| digest | Supports freshness | Changes whenever content changes and is generated mechanically | Exclude; Manifest owns immutable pins |
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; serialization and validator parsing should not be selected
  until the semantic field set is fixed.
- Answer: Use only `id` and `content` as the common envelope. Every ID class
  must have its own prescribed content format, and the validator must verify
  that format rather than relying on AI compliance.
- Resulting decision: DEC-024

### Q-013 — ID Record physical serialization

- Status: resolved
- Depends on: DEC-021, DEC-024
- Question: Should owning artifacts store ID Records as standard YAML
  multi-document streams, with one `---`-delimited YAML document per
  `id`/`content` record?
- Why it matters: The two-field envelope and per-class content schemas still
  need one unambiguous physical grammar. Markdown tables and headings require a
  custom parser and are vulnerable to pipe, multiline, indentation, and heading
  drift; a YAML list adds a wrapper and creates larger edit conflicts; one file
  per ID creates unnecessary file growth.
- Repository evidence: MySkills already installs and pins PyYAML 6.0.3 for
  deterministic YAML parsing, validates YAML elsewhere, and currently uses
  YAML execution manifests. Standard YAML multi-document parsing therefore
  reuses an existing dependency and parser rather than creating a new format.
- Recommended answer: Use one owner-grouped `.yaml` artifact per specification
  class or narrowly cohesive owner. Store each ID Record as one YAML document
  separated by `---`; each document contains only `id` and `content`. Parse with
  safe YAML multi-document loading, reject unknown top-level fields, and
  validate `content` through the class selected by `id`. Do not add a `records`
  wrapper, embed YAML inside Markdown, or create one file per ID. Human review
  surfaces may render these records, but the YAML remains directly readable and
  is the sole authority.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; templates, parser implementation, candidate editing, and
  migration output depend on the serialization.
- Answer: Use standard YAML multi-document streams, provided the selected
  serialization and each class's content format are fully checkable by the
  validator.
- Resulting decision: DEC-025

### Q-014 — Validator-readable ID Content Schema language

- Status: resolved
- Depends on: DEC-011, DEC-021, DEC-024, DEC-025
- Question: Should `id-schema.yaml` use one small domain-specific declarative
  rule language that the Specification Package Validator interprets for every
  ID class, instead of embedding full JSON Schema or hard-coding one validator
  implementation per class?
- Why it matters: YAML parsing proves only syntax. The validator must also
  determine the class, allowed owning files, exact content shape, required and
  forbidden fields, scalar/list/object types, cardinality, and whether every
  ID-valued field points to an existing allowed target class. If these rules are
  duplicated between schema, prose, and class-specific code, they can drift.
- Recommended answer: Use a compact declarative rule set in the sole
  `id-schema.yaml`. For each ID class declare `id_pattern`, `owners`, `scope`,
  and `content`. Within `content`, support only the validation primitives the
  workflow needs: `type` (`string`, `boolean`, `integer`, `enum`, `id`, `object`,
  or `list`), `required`, `additional_fields`, `fields`, `items`, `min_items`,
  `max_items`, `min_length`, `values`, and `target_classes`. A field with
  `type: id` is both a value-format rule and a graph edge; the validator checks
  its target exists, is current when required, and belongs to an allowed class.
  Validate `id-schema.yaml` itself against one small built-in meta-schema before
  reading any records. Do not repeat these rules in Markdown or write a separate
  validator function for each class.
- Example:

  ```yaml
  classes:
    EARS:
      id_pattern: '^EARS-[0-9]{3}$'
      owners: ['11-gate1-ears.yaml']
      scope: current
      content:
        type: object
        required: [source, statement]
        additional_fields: false
        fields:
          source:
            type: id
            target_classes: [PRD]
          statement:
            type: string
            min_length: 1
  ```

- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the validator implementation and every class-specific format
  depend on the schema language.
- Answer: Use one definition file and one generic validator. Every ID class's
  format must be declared so the validator can check it. The validator must
  inspect all package files after every adjustment so a newly added file cannot
  retain historical data or escape synchronized updates.
- Resulting decision: DEC-026, DEC-027

### Q-015 — Three-failure circuit-breaker semantics

- Status: resolved
- Depends on: DEC-003, DEC-017, DEC-027
- Question: Should the three-failure limit count every valid non-PASS validator
  result after an AI repair within the same Answer Application Transaction,
  resetting only after a full PASS or explicit human start of a new
  transaction?
- Why it matters: Resetting the counter when findings, files, or error text
  change lets AI repair forever. Counting validator crashes as specification
  failures instead hides a broken validation tool and produces misleading
  repair attempts.
- Recommended answer: The first validator result after an adjustment is attempt
  1 when it is `INVALID`. After each targeted AI repair, rerun the complete
  validator; any further `INVALID` result is attempt 2 or 3 regardless of
  whether the finding set changed. A full `PASS` resets the counter. Human
  direction may explicitly begin a new transaction and reset it; AI edits,
  finding renames, smaller finding counts, or changing files may not. At attempt
  3, set the transaction to `human-assistance-required`, make no further
  candidate edits, and report every current finding with exact file/ID,
  first-seen attempt, persistence across attempts, repairs tried, and the
  smallest unresolved decision needed from the human. A validator operational
  result of `ERROR` means no trustworthy validation occurred: stop immediately
  and report the tool failure without consuming or resetting the three
  specification-repair attempts.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; workflow state, validator result model, retry control, and
  human handoff format depend on it.
- Answer: Count every complete `INVALID` result within the same adjustment
  transaction. Only `PASS` or explicit human creation of a new transaction may
  reset the count. A validator operational `ERROR` stops immediately and is not
  counted as a specification failure.
- Resulting decision: DEC-028
- File-scope clarification: An unregistered new file is any path under the
  Candidate or Current package root that matches zero declared file roles. A
  path matching more than one role is also invalid. Dynamic families may use
  narrow patterns such as `tasks/TASK-[0-9]{3}.yaml`; broad catch-all patterns
  such as `**/*.md` are prohibited because they would allow arbitrary history
  or forgotten artifacts to escape role-specific validation.

### Q-016 — Persistent attempt-counter calculation

- Status: resolved
- Depends on: DEC-017, DEC-027, DEC-028
- Question: Should the validator calculate attempts from a separate,
  validator-owned JSON control artifact outside Current, incrementing only when
  a different complete final-Current fingerprint receives `INVALID`, instead of
  storing the counter in a workflow document or SQLite?
- Why it matters: Counting individual findings makes one bad Candidate consume
  many attempts. Counting validator invocations makes an accidental rerun of
  unchanged content consume another attempt. Keeping append-only attempt files
  creates the historical clutter this redesign removes, while process memory
  loses the count across sessions. Putting operational state in a normal
  workflow document makes that document both AI-editable input and validator
  bookkeeping, and can make the counter alter its own Current fingerprint.
- Local Obsidian/Wiki evidence:
  - The managed Wiki suite keeps durable knowledge in Markdown but stores
    machine tracking state separately in `.manifest.json` and
    `_meta/trust-ledger.json`. QMD's SQLite database is a rebuildable search
    index rather than the knowledge authority.
  - The only SQLite opened by a managed Wiki Skill is an external Antigravity
    history database, and it is opened in read-only mode. No managed Wiki Skill
    uses SQLite as its own mutable workflow-state authority.
  - `trust-ledger.json` is the relevant safety pattern: it has a schema version,
    rejects malformed and duplicate-key JSON, binds approval to SHA-256 material
    fingerprints, and writes through a same-directory temporary file followed
    by atomic replacement. An unreadable ledger fails closed.
  - `.manifest.json` provides a useful directory-fingerprint pattern but also a
    counterexample: its cache loader treats malformed JSON as empty state and
    its save path is not atomic. A retry counter must never copy this silent
    reset behavior.
- Storage comparison:

  | Owner | Benefit | Material risk | Decision fit |
  | --- | --- | --- | --- |
  | Existing Markdown/YAML workflow document | Human-readable and already present | AI may edit it; mixes normative and operational authority; risks self-fingerprinting and prompt exposure | Reject |
  | Separate validator-owned JSON control artifact | Human-inspectable, diffable during diagnosis, strict stdlib parsing, small atomic write surface, no extra runtime | Requires explicit fail-closed corruption handling and a single-writer lock | Best fit |
  | SQLite | Native transactions and concurrent writers; useful for many records and queries | Adds a binary second authority, schema migration, WAL/sidecar, backup and corruption handling; not Git-diffable; does not prevent an AI with the same filesystem access from changing state | Defer unless multi-writer concurrency or retained query history becomes a real requirement |

- Revised recommended answer: Do not put the counter in a specification or
  workflow document, and do not introduce SQLite for one active transaction.
  Store exactly one transient, untracked JSON control artifact owned exclusively
  by the validator and physically outside the Current package root.
  It contains `schema_version`, `transaction_id`, `invalid_attempts`,
  `last_counted_current_fingerprint`, `last_result`, and `repair_locked`; it
  contains no attempt history and is not loaded during normal AI work.
- Fingerprint rule: Enumerate every regular file under the Current root,
  including paths that later prove unknown or unclassified. Normalize relative
  paths, sort them, hash each path plus its raw content bytes, then SHA-256 the
  ordered aggregate. Reject symlinks. The control artifact and generated report
  are outside the Current root, so there is no mutable-field exclusion rule
  and the validator cannot change the fingerprint by recording its result.
- Update rule: Acquire a non-waiting exclusive validator lock, parse the JSON
  strictly, verify its transaction ID against Active Question State, calculate
  and validate the complete final Current, then write a temporary file, flush it,
  and atomically replace the prior state. A different fingerprint returning
  `INVALID` increments the count; an unchanged rerun preserves it. `ERROR`, a
  malformed/missing state for an already-started transaction, a lock conflict,
  or a transaction mismatch stops without resetting or consuming an attempt.
  Count 3 sets `repair_locked: true`. Successful final validation and cleanup
  remove the control artifact; explicit human initiation creates the next transaction.
  SQLite would not authenticate human intent, so reset authorization remains a
  workflow rule regardless of storage engine.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; cross-session retry enforcement and the no-history requirement
  depend on the counter owner and fingerprint rule.
- Answer: Agreed to the separate validator-owned JSON control artifact and to
  defer SQLite unless concurrent writers or retained query history are later
  required.
- Resulting decision: DEC-029

### Q-017 — Current design-ID granularity

- Status: resolved
- Depends on: DEC-005, DEC-015, DEC-019, DEC-021, DEC-024, DEC-025
- Question: Should one `DESIGN-nnn` represent one technical rule that can be
  changed independently and that actually constrains implementation, Tests, or
  Tasks, while headings, background facts, and explanatory prose receive no ID?
- Why it matters: A single ID for the whole technical design makes every change
  appear to affect every Task and Test. Giving every heading, component, or
  sentence an ID creates excessive records, references, tokens, and validator
  work. Reusing historical Decision IDs in current artifacts would also restore
  the archive-to-current coupling already removed by DEC-016 and DEC-019.
- Repository evidence: The current `21-gate2-technical-design` template is one
  large Markdown document with no design-item IDs. Its `keyDecisions` metadata
  points to the historical decision log, while project impact, test strategy,
  tasks, and traceability all depend on technical-design meaning. This provides
  neither an independently revisable current unit nor one stable normative
  owner and encourages duplicated design prose downstream.
- Recommended answer: Create one current `DESIGN-[0-9]{3}` record for each
  independently changeable technical rule that affects at least one downstream
  implementation, Test, Task, integration contract, or release constraint.
  Combine statements that must always change together. Split rules that can
  change separately and have different downstream consequences. Do not assign
  IDs to section headings, verified facts, examples, or explanation that does
  not itself constrain the implementation.
- Plain example: "Use OAuth login" and "retry a failed provider call three
  times" can change separately, so they receive two IDs. The explanation of why
  OAuth was chosen receives no current design ID; it belongs to the cold
  decision rationale if it is worth retaining. Whether all current Design IDs
  share one file owner is intentionally deferred to the next question.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the ID Schema, traceability graph, revision impact, and Task
  generation depend on it.
- Clarification: The first presentation used too much specification terminology.
  The user requested a concrete, plain-language explanation before choosing.
- Answer: Agreed that one independently changeable, implementation-constraining
  technical rule should receive one ID. More generally, IDs exist to find
  relationships quickly and prevent missed updates, so every content unit that
  another current item references must have an ID; content that is not a
  reference target does not need one.
- Resulting decision: DEC-030

### Q-018 — Single owner for current Design content

- Status: resolved
- Depends on: DEC-003, DEC-021, DEC-025, DEC-030
- Question: Should the complete content of every current `DESIGN-nnn` record
  exist exactly once in the Gate 2 technical-design YAML owner, while Project
  Impact, Tests, Tasks, and other current records express their dependency only
  through its ID and may not redefine the Design ruling?
- Plain meaning: "Owner" means the one place where the rule's complete text may
  be edited. For example, `DESIGN-002` owns the retry rule. A Test references
  `DESIGN-002` and owns its test-specific assertion; a Task references
  `DESIGN-002` and owns its implementation scope. Those consequences may
  necessarily mention the same value, but they cannot replace or redefine the
  Design owner. The validator finds them through the ID edges and requires them
  in the revision impact set when `DESIGN-002` changes.
- Why it matters: If the same technical rule is copied into a Test, Task,
  project-impact document, prompt, and dashboard, changing the owner does not
  prove that every copy was updated. If the full rule has one owner and all
  dependencies are ID edges, the validator can deterministically reject a
  removed, missing, wrong-class, or incomplete relationship.
- Recommended answer: Yes. Rewrite the current technical-design authority as
  one YAML multi-document stream containing all `DESIGN-nnn` definitions. Other
  normative records use Design IDs as their dependency links and own only their
  class-specific consequences; generated human views may render the resolved
  Design text but are non-authoritative and must be regenerated. The cold
  `DEC-nnn` archive keeps rationale separately and is not linked into the
  current reference graph.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; file ownership, ID Schema owner patterns, reference validation,
  derived views, and old-content removal depend on it.
- Answer: Agreed, and generalized beyond Design: the ID Schema defines class
  and format; actual definitions may be separated by class, but every class has
  exactly one definition file; multiple consumer files may reference one ID.
- Resulting decision: DEC-031

### Q-019 — Conversation ID presentation

- Status: resolved
- Depends on: DEC-017, DEC-027, DEC-030, DEC-031
- Question: Should conversations use a mandatory machine-readable ID-reference
  footer or inline reference markers?
- Answer: No. Do not expand the validator or ID syntax contract to conversation
  text or arbitrary documents. Conversation is not specification authority.
- Resulting decision: DEC-032

### Q-020 — One authoritative in-content reference representation

- Status: resolved
- Depends on: DEC-021, DEC-026, DEC-027, DEC-030, DEC-031, DEC-032
- Question: Should every Managed Package File express an ID relationship only
  once, at its point of use through the one schema-declared in-content marker,
  with no document-end or parallel metadata reference list?
- Failure example: If prose says "refer to Q-001" while a separately maintained
  `references` field says `Q-002`, the validator can prove the representations
  disagree but cannot prove which target was intended. Automatically choosing
  either value risks changing the specification rather than repairing syntax.
- Recommended answer: Eliminate duplicate authority. Use one explicit in-content
  marker such as `[[ref:Q-001]]` wherever the relationship is used, including
  inside the applicable YAML content value or prose-native format. The marker is
  the sole relationship source. Do not store a document-end list, a parallel
  metadata list, or another hand-maintained copy.
- Validator behavior: Extract the authoritative references according to the
  file role, reject bare or illegal ID occurrences, then validate target
  existence, target class, cardinality, and graph rules. If a generated
  reference view disagrees, fail with both sets and exact locations. The
  validator never selects Q-001 or Q-002. AI may repair only when definitions,
  surrounding current content, and relationship rules make the intended target
  unambiguous; otherwise it requests human direction rather than guessing, and
  no final Current `PASS` occurs.
- Scope boundary: These rules apply only inside declared Current Managed Package
  Files. Candidate planning, Decision Archive, chat, application source code, and
  unrelated repository documentation are outside this occurrence scan unless
  separately placed inside the managed package by an explicit file role.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the schema DSL, file-role parser, mismatch findings, generated
  views, and AI repair behavior depend on it.
- Answer: Use only one in-content reference mechanism. Do not add a document-end
  reference list or retain two independently maintained representations. Limit
  validator scanning to specific directories containing documents that affect
  specification generation or development rather than conversations, source
  code, or every repository document.
- Resulting decisions: DEC-033, DEC-034

### Q-021 — Core Package Schema placement and authority

- Status: resolved
- Depends on: DEC-015, DEC-019, DEC-027, DEC-029, DEC-032, DEC-034
- Question: Should one Skill-bundled `references/package-schema.yaml` be the
  executable core that alone defines the generated feature package's complete
  directory/file architecture, while State Center, Candidate, Current, History,
  ID Index, and all other outputs are merely roles placed at paths chosen by that
  schema rather than predeclared as top-level areas?
- Repository evidence: Both inspected features currently mix 25-30 top-level
  workflow/specification files with `tasks/`, `prompts/`, `manifests/`,
  `execution/`, `diagrams/`, historical question/decision logs, generated HTML,
  readiness reports, and context proposals under one feature root. Scanning or
  loading that flat root cannot distinguish current authority from derived,
  transient, cold, or validator-owned material.
- Physical-layout audit after user objection:
  - Neither inspected feature currently has `current/`, `candidate/`, `history/`,
    or `.control/`. Both place the numbered workflow/specification files at the
    feature root and use existing child directories named `diagrams/`,
    `execution/`, `manifests/`, `prompts/`, and `tasks/`; `execution/` itself
    contains Task directories.
  - The `spec-package-generator/templates/` source is also flat: all artifact
    templates, including Task and Manifest templates, share that one directory.
  - The assistant's prior drawing was therefore neither the current layout nor a
    faithful four-area target: it introduced a root State Center plus four
    directories (five responsibility surfaces) and showed only Candidate with a
    child directory without deciding the internal layouts of Current, History,
    or State.
  - Any four-area structure is a proposed migration target, not a description of
    the repository today. Existing internal concerns such as Tasks, Manifests,
    Prompts, Diagrams, and active execution data still require explicit ownership
    and may justify child directories in more than one area.
- Superseded explanation of why the assistant changed from five responsibility
  surfaces to four physical areas before recognizing the user's actual four-part
  requirement:
  - The five-surface proposal counted Current, Candidate, History, the AI-facing
    Workflow State Center, and validator-owned Control/Result separately. The
    separation protected different writers, but scattered live workflow state
    across a root file and a fifth directory.
  - The four-area proposal groups the last two under one physical `state/` area
    because both describe the active package rather than specification content,
    planning material, or history. It does not merge their write ownership:
    workflow state remains workflow-controller-owned, while retry state and
    validation results remain validator-owned.
  - Five areas provide stronger separation by location and simpler per-directory
    permissions, at the cost of an additional top-level concept and a less
    literal "single state center." Four areas provide one place to discover all
    live state, but require the package architecture definition and Validator to
    enforce the internal ownership seam.
  - Therefore the logical responsibilities remain distinct in either design;
  the unresolved choice is physical isolation (`control/` as a fifth area)
  versus physical grouping (`state/` with separately governed files).
- Correction after the user's second objection:
  - The user's earlier four-part requirement referred to four necessary
    architecture/control artifacts: (1) the active ID Index, (2) ID
    class/format/definition ownership, (3) every file's role and placement, and
    (4) Skill architecture/workflow outside `SKILL.md`. It did not declare four
    top-level runtime directories.
  - The assistant incorrectly transformed the later lifecycle concepts Current,
    Candidate, History, and State Center into a four-directory filesystem model,
    then debated whether validator Control made a fifth area. Withdraw that
    assumption. Directory count and nesting must be outputs of the core package
    definition, not prior decisions.
  - State is not inherently a directory. The existing package represents resume
    state in root-level `00-spec-workflow-status.md`; the redesigned State Center
    is a file role whose exact canonical path and format must be declared by the
    Package Schema. Validator control/result data are separate roles and likewise
    receive schema-declared placement rather than creating an assumed `state/`.
- Architecture-definition requirement from the user:
  - One machine-readable package architecture authority must declare every
    top-level area, allowed/required canonical file path or path pattern, file
    role, cardinality, writer, parser/validation policy, and cleanup behavior.
  - The Validator inventories the feature root from this definition and fails on
    a missing required file, an unknown file where the area is closed-world, a
    known filename at the wrong path, duplicate singleton roles, invalid dynamic
    filenames, or a file written by/represented as the wrong role.
  - This is separate from the Current ID Index. The index continues to list
    active IDs without locations. A package architecture definition declares
    canonical file roles/paths; the ID Schema declares ID formats, content, and
    which file role owns each ID class. Mapping role to path in only the package
    definition avoids duplicating physical locations.
  - Recommended concrete authority is one Skill-bundled
  `references/package-schema.yaml`, consumed by AI only when package structure
  is relevant and always consumed by the Validator. No per-feature handwritten
  file-location manifest is added; the Validator derives the actual inventory
  by scanning the small package against canonical paths and patterns.
- Recommended answer:
  - Put the executable Package Schema once in the Skill implementation at
    `skills/engineering/spec-package-generator/references/package-schema.yaml`;
    do not copy it into every generated feature package, where copies could drift
    or be edited to make an invalid package pass.
  - Treat the Package Schema as the physical-architecture authority. It defines
    exact roots, paths/patterns, roles, cardinality, writers, loading/ID-scan
    policy, lifecycle, and cleanup. The Validator receives a feature root and
    hides all traversal/classification implementation behind that interface.
  - Keep `id-schema.yaml` as the semantic ID authority. It maps each ID class to
    a file-role name, while `package-schema.yaml` alone maps that role to a path.
    This preserves the user's no-duplicated-location rule.
  - Keep one human/AI-readable `references/package-architecture.md` and workflow
    references outside `SKILL.md` to explain why and how to operate the layout;
    they are not executable authority and must never redefine paths already owned
    by the Package Schema.
  - Only after the complete file-role inventory is mapped into this schema should
    the physical directory tree be proposed. No `state/`, `current/`, or other
    top-level directory is accepted merely because it appeared in a sketch.
- Blueprint requested by the user:
  - `docs/spec-package-architecture-blueprint.md` now provides the proposed
    two-plane design, Package Schema shape, bounded generated tree, role/category
    model, progressive-disclosure controller interface, Candidate/Current/
    validation lifecycle, Validator algorithm, physical finding codes, migration
    mapping, growth constraints, and implementation acceptance criteria.
  - Its proposed generated areas (`current`, `candidate`, `history`, `control`)
    remain a schema proposal rather than an accepted path decision. The active
    decision is still whether the Skill-bundled Package Schema is the sole
    physical-architecture authority; path details follow only after that core is
    confirmed.
- Candidate/Current clarification after DEC-035:
  - The schema-declared Current role set is the only authoritative specification
    package, regardless of its eventual directory name. The active specification
    workflow may read an incomplete direct rewrite for repair and resume;
    implementation qualification requires final workflow `pass` and the matching
    validation result.
  - The confirmed plan is applied directly to Current. Intermediate edits are
    not validated and Current may temporarily contain an incomplete ID/content
    transition; the Workflow State Center and final validation result distinguish
    that state from an implementation-ready package.
  - After all index, definition, reference, content, and file changes finish,
    validate the complete final Current once. `INVALID` is repaired in the same
    Current transaction. Only successful final validation permits transient
    cleanup and final workflow `pass`.
  - Old IDs and old normative content are deleted from Current, not moved into a
    specification-history directory.
- Decision Archive clarification:
  - The schema-declared Decision Archive role is historical data, but only compact
    questions, chosen rulings, rationale, one meaningful rejected alternative,
    and consequences. It contains no old Specification IDs or old specification
    snapshots; its eventual path is owned by the Package Schema.
  - The human answer is planned temporarily, then applied directly to Current.
    Only after final Current validation passes is a compact Decision Card
    written. The archive is a result of the transaction, never the input used to
    generate or replay Current specification meaning.
  - No Current file references an archive Decision ID. The archive has no Gate,
    readiness, traceability, invalidation, resume, or normal loading role. An
    explicit "why was this chosen?" request may read it. If that rationale leads
    to a new change, a human-authorized rewrite must plan, apply, and validate a
    new final Current; the archive can never mutate Current directly.
- Clarification status: The user requested this lifecycle explanation before
  deciding the physical roots, then rejected Candidate validation/promotion in
  favor of one final Current validation. DEC-036 now supplies recovery and
  implementation qualification. DEC-037 resolves cleanup: automatically retain
  compact material Decision Cards only and delete all other Candidate/process
  data. Package Schema placement and authority are now the active decision;
  physical roots remain intentionally unspecified until it resolves.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; migration layout, loader allowlist, validator traversal,
  planning cleanup, archive isolation, and control-state placement
  depend on it.
- Answer: Agreed that the Skill-bundled Package Schema is the core definition
  controlling the complete architecture and that Feature Packages do not retain
  copies. It must cover every file the paired Skills can produce, including the
  fixed source template, canonical output role/path, and non-template producer.
- Resulting decisions: DEC-038, DEC-039

### Q-025 — Final Schema versus migration coverage

- Status: resolved
- Depends on: DEC-022, DEC-038, DEC-039
- Question: Should the final Package Schema contain only retained valid
  producers/output roles, while a separate finite migration matrix accounts for
  all 43 current templates and marks obsolete ones for deletion rather than
  registering obsolete outputs in the final schema?
- Why it matters: Requiring every current template to appear in the final Schema
  would make retired checklists, duplicated reports, permanent prompts, old
  14/15 logs, and historical execution records valid again. Omitting them from
  both Schema and migration evidence would instead risk accidental loss or an
  unmapped generator surviving outside validation.
- Recommended answer: Yes. Use the migration matrix to prove every current
  producer was considered, but let the final Package Schema describe only the
  accepted end state. Repository validation passes only after every retained
  producer maps to one role and every retired producer has been physically
  removed from source, tests, examples, and instructions.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the complete template-to-output catalog and final Schema cannot
  be produced until retained versus retired coverage is separated.
- Answer: Agreed. The migration matrix covers all 43 current templates; the
  final Package Schema registers only confirmed retained producers/outputs, and
  retired templates must be physically removed.
- Resulting decision: DEC-040

### Q-026 — Three-layer file knowledge architecture

- Status: resolved
- Depends on: DEC-021, DEC-026, DEC-038, DEC-039, DEC-040
- Question: Should file architecture use three joined catalogs keyed by one
  closed `file_role`: `package-schema.yaml` for canonical filename/path and
  producer/lifecycle ownership, `file-contracts.json` for declarative Validator
  parsing/check rules, and `file-guide.yaml` for concise AI-facing purpose/use?
- Why it matters: One large Schema makes AI disclosure and human maintenance
  harder, but three overlapping catalogs would recreate the synchronization
  problem. Separating physical definition, executable contract, and semantic
  guide works only if each field has exactly one owner and the Validator proves
  total cross-layer references.
- Recommended answer: Yes. Keep Package Schema as the bootstrap and physical
  core, use strict JSON for the machine contract catalog because it avoids YAML
  coercion and is not intended as prose, and use concise YAML for the on-demand
  AI guide. The Package Controller joins only selected roles, so AI never needs
  to load all three files.
- Proposed ownership:
  - `package-schema.yaml`: role, path/pattern, producer, cardinality, writer,
    authority, lifecycle, contract key, guide key;
  - `file-contracts.json`: parser, structured shape, deterministic text checks,
    ID-scan mode, and reusable validation primitives;
  - `file-guide.yaml`: purpose and short AI usage guidance only.
- Cross-layer invariant: every role has exactly one contract and one guide;
  guide roles cannot be orphaned; contracts must be used or explicitly abstract;
  paths cannot appear outside Package Schema; validation rules cannot appear in
  the guide; purpose prose cannot appear in templates or contract definitions.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; final Package Schema fields, output-role matrix, Controller
  response, and Validator meta-schema depend on this split.
- Answer: Agreed to the three layers connected by `file_role` and joined on
  demand by the Package Controller.
- Resulting decision: DEC-041

### Q-027 — Schema-declared top-level feature areas

- Status: resolved
- Depends on: DEC-034, DEC-038, DEC-041
- Question: Should the accepted Package Schema declare exactly four closed
  top-level Feature areas—`current/`, `candidate/`, `history/`, and `control/`—
  with no undeclared root files, while their permitted child paths come only
  from registered file roles and the default maximum directory depth is two?
- Root-path clarification requested by the user:
  - `<feature>` means the existing concrete feature package root under
    `<project>/.ai-dev/features/<feature-name>/`; it is not a new literal
    `feature/xxx/` wrapper.
  - For example, the proposed four areas would be direct children of
    `C:/project/mydimerco-api/.ai-dev/features/pre-booking/` and
    `C:/project/auto-log/.ai-dev/features/dimflow-work-assistant/`.
  - Existing numbered root files and the current `tasks/`, `manifests/`,
    `prompts/`, `execution/`, and `diagrams/` directories would be migrated,
    rewritten, rendered on demand, or retired according to the 43-template/file
    migration matrix; no additional feature-name nesting is introduced.
  - Skill definitions such as `references/package-schema.yaml` remain under the
    installed Skill, and project-scoped files such as Current Project Context
    remain separate schema scopes. They are not placed under these four
    feature-instance areas merely because the Feature tree is closed.
- Why it matters: Now that path authority and file purpose are separated, the
  physical roots can be decided without making prose diagrams authoritative.
  Too many roots weaken discovery; mixing all lifecycles in one flat root
  recreates the current ambiguity; unrestricted children permit AI-created
  directory growth.
- Recommended answer: Yes. These four names distinguish current managed inputs,
  temporary Candidate recovery, cold Decision Cards, and current operational
  state. `control/` contains state roles but is not specification authority.
  Candidate, History, and Control allow only fixed leaf files and no child
  directories; Current child categories remained a later decision. DEC-043
  subsequently accepted only `records/`, `manifests/`, and User-facing `views/`
  and rejected the provisional `artifacts/`. Dynamic filenames are leaf files
  bound to active IDs.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the 43-template output mapping needs accepted root/path
  categories before assigning canonical target paths.
- Answer: Agreed. The four areas are direct children of each existing concrete
  `.ai-dev/features/<feature-name>/` root.
- Resulting decision: DEC-042

### Q-028 — Current internal authority categories

- Status: resolved
- Depends on: DEC-024, DEC-025, DEC-030, DEC-031, DEC-041, DEC-042
- Question: Should `current/` contain only `id-index.yaml` plus three fixed child
  directories—`records/` for authoritative ID Record streams, `manifests/` for
  per-active-Task immutable routing, and `views/` for generated User Review
  projections—thereby removing the proposed separate `artifacts/` category?
- Why it matters: DEC-025 already makes YAML multi-document ID Record streams the
  normative owners. Persisting PRD/EARS/BDD/design/test documents as another
  broadly named `artifacts/` category risks copying normative meaning and
  restoring the dual-source problem. Treating them as generated managed views
  preserves Gate review surfaces without granting a second authority.
- `artifacts/` versus `views/` clarification requested by the user:
  - The first blueprint used `artifacts/` as a provisional home for persistent
    human/AI-readable outputs such as PRD, EARS, BDD, technical design, project
    impact, and test strategy. That name describes only "something produced";
    it does not determine whether the file owns meaning, is manually editable,
    is generated, or may drive implementation.
  - If an artifact is normative, DEC-025 requires its independently referenced
    meaning to be an ID Record in `records/`. If it is immutable execution
    routing, it belongs in `manifests/`. If it is rendered from those owners for
    review or navigation, it is a `view`. Therefore no exclusive responsibility
    remains for a generic `artifacts/` directory under the accepted model.
  - A View may still be persisted and exhaustively checked. "View" means
    regenerable and non-authoritative, not temporary or unimportant. For
    example, `records/requirements.yaml` owns requirement meaning while a
    persisted `views/product.md` renders the current PRD; editing the rendering
    cannot override the Record, and drift fails regeneration comparison.
  - Keeping `artifacts/` would require a fourth category such as "manually
    authored current consumer document that references Records but owns no
    independently referenced meaning." Any content there that actually affects
    development would need promotion into an ID Record, while content that does
    not affect development is explanatory rendering. The category consequently
    encourages disputed ownership without adding a unique capability.
- Recommended answer: Yes. Use:
  - `current/id-index.yaml`: active ID membership only;
  - `current/records/`: one finite owner file per closed ID class;
  - `current/manifests/`: one immutable leaf file per active Task ID;
  - `current/views/`: fixed User-facing PRD/EARS/BDD/design/test/task-index/
    traceability/dashboard/diagram review roles generated from Records,
    persisted only when Package Schema requires them and otherwise rendered on
    demand.
  Views may contain current rendered content but cannot introduce definitions;
  Validator regeneration/comparison detects drift, and normal AI generation or
  Implementation cannot load them as specification authority. Task lifecycle
  and workflow state remain in `control/`, Candidate review surfaces remain in
  `candidate/`, and no generic catch-all directory is allowed.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; retained Gate templates and all Current target paths in the
  43-template migration matrix depend on the authority/view split.
- Answer: Agreed to remove `artifacts/` and use Records, Manifests, and Views,
  with the additional restriction that Views contain only files generated from
  true specification Records for User-facing visual inspection/validation and
  have no authority.
- Resulting decision: DEC-043

### Q-029 — User Review View persistence lifecycle

- Status: resolved
- Depends on: DEC-032, DEC-037, DEC-041, DEC-043
- Question: After a User finishes the review/confirmation for which a View was
  generated, should that View normally be deleted and rendered again on demand,
  with persistence allowed only for a small Package-Schema-declared latest
  dashboard or other explicitly required User surface?
- Why it matters: Persisting every Gate review, PRD rendering, diagram, report,
  dashboard, and confirmation surface recreates file/context growth even though
  none has authority. Deleting all Views immediately may inconvenience ongoing
  User review or a dashboard that is intentionally used between sessions.
- Recommended answer: Render User Review Views on demand and delete them after
  their review result is represented in Records/control state. Permit persistent
  latest-only Views only as named singleton roles with a concrete ongoing User
  need; never keep dated/versioned review copies. A persisted View carries the
  source Current fingerprint and Validator checks it by regeneration/comparison.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the 43-template migration must decide whether Gate HTML,
  PRD/EARS/BDD renderings, diagrams, task index, traceability, and dashboard are
  non-persistent renderers or retained singleton View roles.
- Answer: Keep the latest single file after confirmation. Overwrite it only when
  new information must be presented for User inspection; never create a
  versioned or historical View copy.
- Resulting decision: DEC-044

### Q-030 — Stale retained View and old-ID handling

- Status: resolved
- Depends on: DEC-019, DEC-032, DEC-034, DEC-043, DEC-044
- Question: Because an unchanged latest-only View may become stale after Records
  change, should it be treated as a non-normative cache excluded from the
  authoritative Current fingerprint and removed-ID occurrence gate, while its
  embedded source fingerprint must be checked and the same file atomically
  regenerated before it is shown to the User or confirmed again?
- Why it matters: Requiring every retained View to match Current during final
  specification validation would force regeneration after every Record edit,
  contradicting the decision to overwrite only when User-facing information is
  needed. Ignoring freshness when showing the file could display obsolete
  content or let a User confirm an older Record set. Including View bytes in the
  normative PASS fingerprint would also make harmless rendering changes
  invalidate the specification.
- Recommended answer: Yes. Structure validation checks the canonical
  name/location, singleton cardinality, format, non-authoritative marker, and
  source fingerprint. Specification validation and old-ID cleanup apply to
  Records and Manifests and do not treat an inactive cached View as authority.
  Before display or confirmation, the Controller compares the source
  fingerprint: reuse on a match and atomically overwrite on a mismatch.
  Confirmation binds to that fingerprint and fails if Current changes during
  review. The View visibly identifies itself as a generated snapshot that must
  be opened through the workflow for freshness.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the Validator's managed occurrence set and Current PASS
  fingerprint cannot be finalized until retained View freshness is separated
  from specification authority.
- Answer: Agreed. If a View does not need to be shown to the User, it does not
  need to change. It is refreshed only at the next User display or confirmation
  boundary.
- Resulting decision: DEC-045

### Q-031 — Direct opening of a retained View

- Status: resolved
- Depends on: DEC-043, DEC-044, DEC-045
- Question: Because a User can open a retained View directly from the filesystem
  without invoking the Controller, should every View visibly state that it is a
  potentially stale, non-authoritative cached snapshot and instruct the User to
  refresh/open it through the Skill before relying on or confirming it?
- Why it matters: The Controller can enforce source-fingerprint refresh only
  when it knows a display is occurring. A direct file open cannot be intercepted,
  so an old but structurally valid View could otherwise look current even though
  its Records have changed.
- Recommended answer: Yes. Put one fixed visible notice in every human-readable
  View and machine-readable provenance containing at least its source
  fingerprint. The notice does not create another status authority; it only
  states that freshness is guaranteed by the Skill's display/confirmation
  operation, not by directly opening the retained file.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; this determines the minimum common View contract and whether
  direct filesystem opening is a supported trustworthy review path.
- Answer: No visible warning or refresh instruction is needed. Direct opening
  freshness is not important enough to add more content to the View.
- Resulting decision: DEC-046

### Q-032 — Compact Decision Card schema

- Status: resolved
- Depends on: DEC-019, DEC-023, DEC-024, DEC-025, DEC-037, DEC-042
- Question: Should the sole cold archive be `history/decisions.yaml`, serialized
  as one YAML multi-document stream whose cards use `DEC-nnn` and the common
  `id`/`content` envelope, with `content` containing exactly `date`, `gate`,
  `question`, `ruling`, `rationale`, `rejected`, and `consequence`?
- Why it matters: This merges the old question and decision histories into one
  retrievable unit without retaining transcripts or separate logs. An exact
  closed shape lets the Validator reject AI-added metadata, duplicated current
  specification text, status history, or archive sprawl. Date and Gate preserve
  minimal temporal/process context; the other fields preserve what was asked,
  chosen, why, the meaningful alternative, and the effect.
- Recommended answer: Yes, with all seven `content` fields required and concise.
  `rejected` records at most one meaningful alternative, not an option list.
  Cards must contain no current or removed Specification IDs, cannot be
  referenced by Current, and are loaded only for an explicit historical-rationale
  request. `DEC-nnn` belongs to the cold archive namespace rather than the
  Current ID Index.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the ID Schema, history File Contract, migration from the old
  question/decision files, and automatic finalizer output need one exact shape.
- Answer: Adopt a minimum viable design first instead of expanding historical
  content pre-emptively. The minimum machine-checkable card retains only the
  problem and the decision as `question` and `decision` inside `content`.
- Resulting decision: DEC-047

### Q-033 — Conditional file absence

- Status: resolved
- Depends on: DEC-038, DEC-039, DEC-041, DEC-043, DEC-044, DEC-047
- Question: For conditional roles such as a User Review View or a Manifest for
  an active Task, should `not applicable` be represented only by the file being
  absent, with Package Schema declaring a deterministic presence condition,
  instead of creating empty placeholder files or recording a separate
  `not-applicable` status?
- Why it matters: Placeholder files and duplicated applicability status create
  more state for AI to synchronize and can disagree with the actual package.
  Unconstrained absence, however, could hide a missing required output unless
  the Validator can derive exactly when the role must exist.
- Recommended answer: Yes. A conditional role declares one deterministic
  presence condition based only on existing authorities such as active ID
  membership or Workflow State. When false, the file must be absent; when true,
  it must exist and pass its contract. Do not create empty files, readiness
  checklist entries, or `not-applicable` markers.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; role cardinality, readiness derivation, View/Manifest creation,
  and missing-file findings depend on one applicability representation.
- Answer: Rejected the proposed presence-condition model. The Validator must not
  require any file to exist or manage file state. It only checks whether each
  file that does exist is permitted and whether its name, location, format,
  IDs, and references are legal.
- Resulting decision: DEC-048

### Q-034 — Completion owner after legality validation

- Status: resolved
- Depends on: DEC-036, DEC-041, DEC-048
- Question: Since a legality-only Validator can validly accept a package in
  which a workflow output has not been created yet, should completion be owned
  solely by the Package Controller and Workflow State Center, with Validator
  returning `VALID` rather than workflow `PASS`, and Implementation requiring
  both a completed workflow state and a matching `VALID` fingerprint?
- Why it matters: If Validator `PASS` is also treated as readiness, missing
  workflow outputs silently become "complete" even though file presence is
  intentionally outside Validator authority. Putting presence rules back into
  Validator would violate the boundary just confirmed. Separating `VALID` from
  workflow `pass` gives each module one responsibility.
- Recommended answer: Yes. The Controller knows which approved operations and
  outputs the active workflow promised and records their completion in the
  Workflow State Center. It may request legality validation only after those
  operations finish. Validator reports `VALID`, `INVALID`, or `ERROR` for the
  exact existing-file fingerprint; only the Controller may set workflow `pass`.
  Implementation requires both values to match and never infers completeness
  from Validator output alone.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; finalization, status names, implementation preflight, and the
  division between Controller and Validator depend on it.
- Answer: Agreed to the proposed responsibility boundary: management state owns
  completion, Validator owns legality, and Implementation requires both.
- Resulting decision: DEC-049

### Q-035 — Minimum Validator implementation technology

- Status: resolved
- Depends on: DEC-026, DEC-029, DEC-041, DEC-048, DEC-049
- Question: Should the first Validator implementation be one Python command-line
  module using the repository's existing Python validation/test toolchain and
  ordinary YAML/JSON/filesystem data, with no SQLite database, service, plugin,
  or separate runtime architecture?
- Why it matters: The Validator is central and must behave deterministically on
  Windows paths, YAML multi-document records, JSON contracts, closed path roles,
  ID graphs, fingerprints, and atomic control-file replacement. A database or
  service adds lifecycle and synchronization failure modes before concurrency or
  retained queries exist. A language/runtime choice that differs from the
  repository's existing validators also raises installation and maintenance
  cost.
- Repository evidence: Repository-wide validation and test entry points already
  use Python plus `argparse`; `manifests/dependencies.json` already defines
  Python 3.10+ as a runtime prerequisite and PyYAML 6.0.3 as a pinned installable
  dependency, although PyYAML is currently isolated to the `skill-evaluator`
  private environment. PowerShell has no repository-provided YAML parser, and
  no general JavaScript YAML dependency is declared.
- Recommended answer: Yes. Implement one small Python 3.10+ package behind one
  CLI entry point, use files as the sole data authority, keep parsers and finding
  codes as internal modules, and use temporary-file-plus-atomic-replace for the
  Validator-owned result/control files. Declare PyYAML 6.0.3 explicitly for the
  specification workflow instead of depending on another Skill's private
  environment or writing a YAML parser. Do not add SQLite unless future
  concurrent writers or retained query workloads are demonstrated.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; executable schema design, dependency policy, atomic writes,
  tests, and Skill invocation all depend on the implementation boundary.
- Answer: Agreed to the proposed Python 3.10+, explicitly declared PyYAML 6.0.3,
  file-only, single-CLI implementation without SQLite, service, or plugin.
- Resulting decision: DEC-050

### Q-036 — Existing Feature Package migration completion

- Status: resolved
- Depends on: DEC-036, DEC-039, DEC-040, DEC-048, DEC-049, DEC-050
- Question: Should each existing Feature Package be migrated in place through
  the same Candidate plus Workflow State Center transaction, with a finite
  Controller-owned migration plan accounting for every legacy file as
  convert/merge/render/retire, and legacy files removed only after their accepted
  Current meaning has been written to the new owner?
- Why it matters: Validator intentionally cannot fail because an expected new
  file is missing, so it cannot prove migration completeness. Deleting all
  legacy files first risks losing accepted meaning; keeping them until the end
  lets old and new sources coexist temporarily but requires one authoritative
  progress owner so an interrupted migration does not become ambiguous.
- Recommended answer: Yes. Migrate one Feature Package per transaction. The
  Controller owns a closed migration operation list, applies idempotent writes
  and deletions directly to Current, and records completion in Workflow State.
  It may retire a legacy file only after all retained meaning assigned to that
  operation exists in its new owner. Finalization requires every operation
  complete, zero unaccounted legacy files, Validator `VALID`, Candidate cleanup,
  and then workflow `pass`. Validator checks legality only and never owns the
  migration checklist.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; migration safety, interruption recovery, deletion order, and
  acceptance testing for the two known packages depend on it.
- Answer: Agreed to one in-place, resumable migration transaction per Feature
  Package, with Controller-owned exhaustive legacy-file disposition and
  Validator limited to legality.
- Resulting decision: DEC-051

### Q-037 — Dashboard in the minimum viable package

- Status: resolved
- Depends on: DEC-039, DEC-040, DEC-043, DEC-044, DEC-045, DEC-046, DEC-047
- Question: Should the minimum viable architecture retire the dedicated
  persistent Dashboard and generate only a declared latest User Review View when
  the User actually requests information, adding a dedicated Dashboard role
  later only if a concrete ongoing use appears?
- Why it matters: Dashboard authority and synchronization are already resolved
  if it is a View: it is generated, non-authoritative, may remain stale while
  unused, and refreshes before Controller-mediated display. The remaining cost
  is its template, role, renderer, contract, tests, and AI-facing purpose. Keeping
  it without a current User need violates the newly accepted minimum viable
  approach and duplicates information available from Records and Workflow State.
- Recommended answer: Yes. Retire the current Dashboard producer/template in the
  migration matrix. Keep the generic View mechanism, not a default dashboard
  file. When the User requests a review, render the smallest schema-declared
  latest singleton needed for that review. A future Dashboard must be added as
  an explicit User-facing View role through Package Schema, File Contract, File
  Guide, renderer, and tests; it never becomes authority or a workflow-state
  owner.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the template migration matrix and final View-role catalog need
  an explicit keep/retire disposition for Dashboard output.
- Answer: Retain a simplified Dashboard. The User needs one place to copy the
  execution Prompt, see the Task count, and briefly inspect what each Task will
  do before deciding which one to run.
- Resulting decision: DEC-052

### Q-038 — Minimum Dashboard content

- Status: resolved
- Depends on: DEC-043, DEC-044, DEC-045, DEC-046, DEC-049, DEC-052
- Question: Should the minimum Dashboard contain only feature name, total Task
  count, dependency/order summary, and one card per Task with Task ID, title,
  one-sentence outcome, dependency IDs, links to its Task/Manifest, and a copy
  button for the generated `$implement-spec-task <manifest-path>` Prompt?
- Why it matters: These fields let the User understand Task slicing and select
  an execution Prompt without copying the Task contract into HTML. Adding
  readiness details, allowed paths, tests, evidence, traceability, risks,
  acceptance criteria, editable status, local storage, or export recreates the
  large duplicate Dashboard and its synchronization problems.
- Recommended answer: Yes. Keep only the listed display fields and copy action.
  Generate them from current Task Records and immutable Manifests. Detailed Task
  review happens through the linked authoritative owner, while the Controller
  and Implementation preflight enforce current eligibility. The Dashboard does
  not display or own mutable Task status in the minimum version.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the Dashboard renderer, template, File Contract, source roles,
  and migration disposition need one closed minimum field set.
- Answer: Agreed to exactly the proposed minimum Dashboard fields and exclusions.
- Resulting decision: DEC-053

### Q-039 — Missing ADR 0003 disposition

- Status: resolved
- Depends on: DEC-019, DEC-037, DEC-047, DEC-051
- Question: Should the missing legacy ADR 0003 remain absent instead of being
  reconstructed, with any still-current rule represented directly in the new
  Current Records and any newly confirmed material decision represented only by
  the minimum Decision Card?
- Why it matters: Reconstructing a missing historical ADR requires inference
  from old discussions and risks inventing rationale, retaining obsolete IDs,
  and creating another history format outside `history/decisions.yaml`. Leaving
  a live reference to a nonexistent ADR is also invalid and must be removed or
  replaced during migration.
- Repository evidence: `docs/adr/` currently contains only ADR 0001 and 0002.
  The exact missing ADR 0003 path appears only in the permitted handoff and these
  planning notes, not in either Skill's executable instructions, templates, or
  runtime lookup paths. Generic instructions to inspect applicable project ADRs
  are unrelated and remain valid.
- Recommended answer: Yes. Do not recreate ADR 0003. Encode verifiably current
  normative rules in the new schema/Current owners, retain only Decision Cards
  confirmed under the new model, and remove the obsolete missing-ADR note when
  this planning packet finalizes. Do not infer or preserve unknown historical
  rationale.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; the migration matrix must either retire the dangling reference
  or add a new file role, and the accepted single-history-format rule favors
  retirement.
- Answer: Agreed not to reconstruct ADR 0003.
- Resulting decision: DEC-054

### Q-040 — Minimum closed Current ID class set

- Status: resolved
- Depends on: DEC-010, DEC-017, DEC-021, DEC-024, DEC-026, DEC-030, DEC-031
- Question: Should the first-version Current graph contain exactly five ID
  classes—`REQ-nnn`, `BDD-nnn`, `DESIGN-nnn`, `TEST-nnn`, and `TASK-nnn`—while
  `Q-nnn` remains transient control identity and `DEC-nnn` remains cold archive
  identity outside the Current ID Index?
- Why it matters: `id-schema.yaml`, record-owner filenames, allowed reference
  targets, migration, and Validator finding rules cannot be concrete until the
  first-version Current ID classes and exact formats are closed.
- Repository evidence: The current workflow's durable chain is PRD/EARS behavior
  -> BDD scenario -> Test -> Task, with Gate 2 technical design constraining
  Tests and Tasks. Existing identities are inconsistent: EARS uses `EARS-xxx`,
  BDD uses `BDD-SCENARIO-xxx`, tests use subtype-bearing forms such as
  `TEST-UNIT-xxx`, and Tasks use `TASK-xxx`. DEC-010 already established that
  IDs identify while classification belongs in fields, standardized tests on
  `TEST-nnn`, and retired `SCN-`; DEC-030 established `DESIGN-nnn` for
  independently changeable technical rules.
- Recommended answer: Yes. Use exactly these owner streams and formats:
  `requirements.yaml` / `^REQ-[0-9]{3}$`, `bdd.yaml` /
  `^BDD-[0-9]{3}$`, `design.yaml` / `^DESIGN-[0-9]{3}$`, `tests.yaml` /
  `^TEST-[0-9]{3}$`, and `tasks.yaml` / `^TASK-[0-9]{3}$`. A REQ record owns
  one business/behavior requirement and its EARS pattern/statement, so PRD and
  EARS do not become two IDs for the same meaning; their User review renderings
  are Views. BDD owns Given/When/Then acceptance examples. Test level and Task
  type live in content fields rather than ID prefixes. Project impact, contracts,
  and release constraints that independently constrain implementation are
  DESIGN records. Supporting narrative that is never referenced receives no ID.
  `Q-nnn` and `DEC-nnn` are governed in their non-Current scopes and never enter
  `current/id-index.yaml`.
- User concern: If `Q-nnn` and `DEC-nnn` are excluded from Current, can the
  workflow still ensure that a decision was applied?
- Clarification:
  - They are excluded from the Current specification graph, not removed from
    their own lifecycles. The active `Q-nnn` remains in Workflow State and
    Candidate until the transaction finalizes; the compact `DEC-nnn` remains in
    cold `history/decisions.yaml` afterward.
  - The enforcement chain is active Question plus answer -> closed application
    operation list naming affected Current IDs/roles -> idempotent writes and
    reconciliation -> Controller completion -> Validator `VALID` -> automatic
    Decision Card -> Candidate/active-Question cleanup -> workflow `pass`.
  - Current references to Q/DEC would not prove semantic application. They would
    prove only that an ID was mentioned while recreating archive-to-Current
    coupling and stale-history risk. Application evidence belongs to the
    transient operation list and Controller state.
  - Deterministic validation can prove that declared operations completed,
    Current IDs/references are structurally consistent, and removed IDs are
    gone. It cannot prove that AI-authored prose semantically matches human
    intent. Only User review of changed Current meaning can reduce that semantic
    risk; retaining Q/DEC references would not solve it.
  - Follow-up answer: Do not require a second User confirmation after each
    decision application. Accept the semantic limitation and rely on existing
    Gate/final review or explicit on-demand inspection instead.
  - Follow-up decision: DEC-055
- Default assumption if unanswered: Use the recommended minimum five Current
  classes; adding a class later requires an explicit schema migration.
- Blocking: yes; this is the remaining core schema input rather than a historical
  documentation question.
- Answer: Agreed to the minimum five Current classes, with the clarification that
  Q and DEC remain classes in the same ID Schema but are forbidden from Current.
- Resulting decision: DEC-056

### Q-041 — Active Question definition owner

- Status: answered
- Depends on: DEC-024, DEC-025, DEC-031, DEC-036, DEC-041, DEC-056
- Question: Should the one active `Q-nnn` be defined in a fixed
  `candidate/question.yaml` file using the same `id`/`content` envelope, while
  `control/workflow-state.yaml` references only that Q ID and
  `candidate/discussion.md` contains non-authoritative recovery notes without a
  second Q definition?
- Why it matters: Q must have one parseable definition owner to satisfy the
  class -> definition -> reference architecture. Putting full question content
  in Workflow State makes the state center a second discussion/specification
  owner; defining Q again in discussion notes creates duplicate authority.
- Recommended answer: Yes. `candidate/question.yaml` contains exactly one active
  Q Record. Its minimal content shape is `question` plus `answer`, where `answer`
  may be null until the User responds; File Contract checks the shape but the
  Controller owns whether null is allowed in the current workflow phase.
  Workflow State stores only `active_question: Q-nnn`; application-plan and
  discussion files may reference the Q in their one schema-approved in-content
  position but cannot redefine it. Finalization removes the Q file and all Q
  references after creating the independent DEC card.
- User clarification question: Is `Q-001` deleted after it is handled?
- Clarification: Yes, but only after Controller completion, matching Validator
  `VALID`, and successful creation of the minimum DEC card. Finalization then
  deletes `candidate/question.yaml` and every Candidate/Control Q reference.
  Current never contains the Q. Interruption, `INVALID`, `ERROR`, incomplete
  operations, or failed DEC writing retains the Q so resume still has one stable
  transaction anchor. Once finalized, retaining Q would create exactly the stale
  historical ID the architecture is designed to remove.
- User risk question: Compared with continuously retaining information, which is
  more harmful for AI, given that deletion may lose context or cost cleanup
  tokens while retention may increase hallucination and prompt size?
- Risk analysis:
  - Stored bytes do not consume model tokens by themselves. Token cost occurs
    when files are searched, selected, read, summarized, or injected into a
    prompt. Physical and loader separation therefore matters more than raw
    retention size.
  - Premature deletion has high-severity, localized risk: interruption recovery
    may fail, rationale may be lost, AI may re-ask/reconstruct information, and
    an incorrectly applied decision may become harder to diagnose. Cleanup also
    adds one-time write/validation work and tokens.
  - Broad retention has lower immediate severity but cumulative recurring risk:
    stale/current authority ambiguity, accidental retrieval, salience dilution,
    incompatible-version synthesis, larger searches, more relationship rules,
    and repeated token use on every later task. Retaining old IDs inside normal
    roots is especially harmful because the Validator and AI must distinguish
    them forever.
  - For an active Q, deletion before `VALID`/DEC/finalization is more dangerous
    than retention, so it is forbidden. After finalization, the DEC card keeps
    the minimum question/decision knowledge and Current keeps the operative
    result; the Q file then contains duplicate workflow scaffolding rather than
    unique necessary knowledge. Retaining it is more harmful over time.
  - The accepted hybrid is lifecycle-based rather than "delete all" or "keep
    all": retain active recovery data until pass; retain current authority;
    retain only minimum Decision Cards in cold non-loaded history; delete old
    IDs, duplicate drafts, progress scaffolding, and obsolete generated data.
  - Final answer: Formally adopt deletion of completed Q data and retain only
    Current plus the minimum DEC card.
  - Resulting decision: DEC-057
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; Candidate paths, Q content schema, Workflow State schema,
  resume behavior, and cleanup cannot be finalized without one owner.
- Answer: Agreed. Use `candidate/question.yaml` as the sole actual definition
  owner for the active Q; all other permitted occurrences are references only.
- Resulting decision: DEC-058

### Q-042 — Q number allocation after cleanup

- Status: superseded-by-DEC-087
- Depends on: DEC-037, DEC-047, DEC-057, DEC-058
- Question: After a completed Q is deleted, should the next Q derive its number
  from the next Decision Card and keep the same suffix (`Q-012` becomes
  `DEC-012`), rather than retain a separate Q counter or reuse `Q-001` for every
  transaction?
- Why it matters: Q cleanup removes the only active Q definition. A persistent
  monotonic Q counter adds control state whose only purpose is historical
  uniqueness, while always reusing `Q-001` makes interruption logs and targeted
  diagnostics ambiguous. The retained Decision Archive already supplies a
  durable monotonic sequence.
- Recommended answer: Yes. Under the feature lock, allocate the active Q as one
  greater than the highest existing `DEC-nnn` suffix, or `Q-001` when no Decision
  Card exists. Successful finalization appends `DEC-nnn` with the identical
  suffix before deleting Q. A canceled question that produces no material
  decision and is explicitly garbage-collected may leave the number available
  because no durable Q or DEC survives. This avoids both a second counter and
  completed-Q retention.
- Default assumption if unanswered: Use the recommended shared suffix rule.
- Blocking: yes; the Controller and Decision Archive append contract need one
  deterministic collision-free allocation rule.
- Answer: Agreed to derive the Q suffix from the next Decision Card and preserve
  that suffix when the Q becomes its retained DEC.
- Resulting decision: DEC-059
- Later correction: DEC-087 preserves the shared Q/DEC suffix but allocates it
  from the existing Controller allocation state, because scanning cold History
  contradicted its no-control-dependency boundary.

### Q-043 — Minimum Workflow State fields

- Status: answered
- Depends on: DEC-036, DEC-049, DEC-057, DEC-058, DEC-059
- Question: Should `control/workflow-state.yaml` store only the minimum durable
  facts needed for safe resume—`phase`, `active_question`, `plan_fingerprint`,
  `completed_operations`, and `reconciled_current_fingerprint`—while the
  Controller derives `next_action` instead of persisting it as a second state
  fact?
- Why it matters: The State Center must reveal where work stopped and detect a
  changed plan or Current after interruption. Persisting prompts, timestamps,
  errors, retry counts, question content, validation status, or a hand-written
  next action duplicates other authorities and creates drift. A derived next
  action still gives AI the requested resume instruction without making AI
  maintain another synchronized field.
- Recommended answer: Yes. Use exactly these five fields in the minimum schema.
  `phase` is a closed enum; `active_question` is `Q-nnn` or null;
  `plan_fingerprint` is null until a complete application plan is sealed;
  `completed_operations` contains only operation keys defined by that sealed
  plan; and `reconciled_current_fingerprint` binds the recorded progress to the
  last Current state verified by the Controller. `package resume` derives and
  returns `next_action` from these facts plus the fixed workflow transition
  table. No free-form status or duplicated Validator data is allowed.
- Default assumption if unanswered: Use the recommended five-field schema and
  derive `next_action`.
- Blocking: yes; Candidate application-plan fields and resume transitions must
  bind to this schema.
- Answer: Agreed to the exact five-field minimum and Controller-derived
  `next_action`.
- Resulting decision: DEC-060
- Later refinement: DEC-064 removes `completed_operations` after exact-delta
  plans make progress safely derivable from Current.

### Q-044 — Workflow phase values

- Status: answered
- Depends on: DEC-049, DEC-057, DEC-060
- Question: Should `phase` use exactly six values—`discussing`, `planning`,
  `applying_current`, `validating`, `finalizing`, and `pass`—with no separate
  `idle`, `blocked`, or `error` phase?
- Why it matters: Each extra phase expands transition logic and allows different
  files to disagree about what recovery means. The package need not exist before
  its first Q; validator findings and retry exhaustion already live in
  validator-owned evidence; and the Controller can derive `ask_user`, `repair`,
  or `request_human_help` as the next action without changing the durable work
  phase.
- Recommended answer: Yes. Start a transaction by atomically creating the Q and
  entering `discussing`. Move to `planning` after a non-null answer, to
  `applying_current` after sealing the plan, to `validating` after all plan
  operations reconcile, and to `finalizing` only with matching `VALID` evidence.
  After DEC append and Q/Candidate cleanup, enter `pass`, clear
  `active_question`, clear `plan_fingerprint`, and clear
  `reconciled_current_fingerprint`; the authoritative final fingerprint
  remains solely in `validation-result.json`. A new Q invalidates the old pass
  by entering `discussing` before any Current edit.
- User impact question: What effect do these six phase values have on AI?
- AI impact analysis:
  - A closed enum replaces free-form status interpretation. AI does not have to
    guess whether words such as "editing", "checking", "repairing", and
    "almost done" mean different states.
  - Phase gives the Controller a deterministic context boundary: discussion
    loads the active Q, application loads the sealed plan and impacted Current
    roles, validation loads typed findings, and implementation is allowed only
    at `pass`. This reduces unrelated reads and stale-history exposure.
  - Together with the sealed plan and fingerprints, phase lets an AI
    resume at an observable boundary instead of rereading the whole package or
    trusting its conversational memory. This reduces repeated writes and missed
    operations after interruption.
  - Keeping repair inside `validating` prevents `INVALID` from becoming a new
    vague workflow phase. Typed findings and the three-distinct-state limit tell
    AI whether to repair or request human help, reducing an unbounded
    modify/check loop.
  - Too few phases would hide whether an answer, sealed plan, Current rewrite,
    validation, or cleanup is complete; AI would need inference and broad reads.
    Too many phases would add transition branches, synonyms, and contradictory
    combinations. These six correspond to actual authority or side-effect
    boundaries.
  - The residual risk is high leverage: if the Controller writes the wrong
    phase, AI can confidently take the wrong action. Sole-writer transitions,
    field invariants, fingerprints, and implementation's `pass` plus matching
    `VALID` preflight must therefore fail closed. The enum itself adds negligible
    prompt cost compared with prose status.
- User control objection: If the phase has only six legal values, should state
  be controlled by Validator; otherwise what prevents a seventh value?
- Responsibility clarification:
  - Yes, File Contract must declare the exact phase enum and Validator must check
    every existing `workflow-state.yaml`. A seventh value, wrong type, unknown
    field, malformed fingerprint, or undefined Q reference is a typed `INVALID`
    finding.
  - "Validator-controlled" must mean legality control, not write ownership.
    Controller remains the only state writer and owns when a transition is
    allowed. Validator reads and rejects illegal state but never chooses a phase,
    repairs the file, or sets `pass`; otherwise the checker would also decide
    whether its own preconditions were complete.
  - Controller commands, `package resume`, and Implementation all fail closed on
    an illegal Workflow State. An unknown seventh phase has no transition and is
    not guessed back into a known phase; it requests human repair immediately.
  - This preserves DEC-048/DEC-049: Validator verifies the legality of an
    existing state file, while completion and readiness remain Controller-owned.
- Default assumption if unanswered: Use the recommended six phases.
- Blocking: yes; the state contract and executable transition table require a
  closed phase enum.
- Answer: Agreed to the six phases after clarifying that Validator controls their
  legal enum while Controller controls writes and transitions.
- Resulting decision: DEC-061

### Q-045 — State legality checkpoints

- Status: answered
- Depends on: DEC-035, DEC-048, DEC-049, DEC-060, DEC-061
- Question: At which checkpoints must Workflow State legality be checked without
  turning every transition into a full Current validation?
- Why it matters: Checking state only at the final validation lets an illegal
  seventh phase misdirect AI earlier. Running the complete package validator on
  every edit recreates the expensive modify/check loop that this architecture is
  intended to remove.
- Recommended answer: Reuse one File-Contract validation function at four
  fail-closed boundaries, while reserving full Current validation for the final
  `validating` phase:
  1. At entry to every Controller command, including `resume`, validate the
     existing Workflow State shape, enum, Q reference, fingerprints, and recorded
     operation keys before deriving any action.
  2. Before every state write, Controller validates the proposed four-field
     document and the requested transition in memory, then atomically replaces
     the file. This is a state guard, not a full package scan and not a validator
     retry attempt.
  3. At final `validating`, run the one full closed-world legality validation of
     existing managed files. Re-run it only after a repaired distinct Current
     state, up to the accepted three-state limit.
  4. On every Implementation entry, validate Workflow State legality, require
     `phase: pass`, and recompute Current/schema fingerprints against the retained
     `VALID` result. A fingerprint mismatch blocks and starts no implementation;
     it does not silently run from stale evidence.
  An illegal current or proposed state stops immediately. Unknown phase or
  unsafe transition is not guessed or automatically rewritten without evidence.
- User repair-limit addition: When a checkpoint reports a repairable problem, AI
  should attempt self-repair, limited to three repairs; after that a human must
  intervene.
- Repair-count clarification: Apply one transaction-wide budget to both state
  legality and final-package findings so AI cannot escape the limit by moving the
  error between checkpoints. Initial detection is not itself a repair. Each
  different post-repair checkpoint fingerprint consumes one of three repair
  cycles; rerunning unchanged bytes consumes nothing and grants no extra repair.
  If repair three remains `INVALID`, Controller locks automated writes and emits
  the consolidated human-assistance report. `ERROR` and unresolved semantic
  choices still stop immediately because editing specification content cannot
  repair an untrustworthy checker or invent a User decision.
- Default assumption if unanswered: Use these four checkpoints.
- Blocking: yes; Controller commands, Validator retry accounting, and
  Implementation preflight depend on the boundary definition.
- Answer: Agreed to the four checkpoints, with one transaction-wide limit of
  three evidence-based AI self-repairs before mandatory human intervention.
- Resulting decision: DEC-062

### Q-046 — Application-plan content depth

- Status: answered
- Depends on: DEC-024, DEC-025, DEC-036, DEC-051, DEC-058, DEC-060, DEC-062
- Question: Should each operation in `candidate/application-plan.yaml` carry the
  exact intended Current delta for its target records/files, rather than only a
  prose instruction such as "update related tests"?
- Why it matters: Workflow State can remember that `op-002` completed, but after
  interruption AI still needs a deterministic definition of what `op-002` was
  supposed to produce. Prose-only plans recreate the omission and reinterpretation
  risk; copying the entire Candidate package would recreate a second specification.
- Recommended answer: Store only impacted deltas. The plan has `question` plus an
  ordered `operations` list. Each operation has a local `key`, closed `kind`, one
  target `role`, and a kind-specific exact payload: complete replacement Records
  for an upsert, exact IDs for removal, or an exact declared file target for
  render/retire. Every affected downstream Record receives its own operation;
  vague catch-all instructions are illegal. The sealed plan is temporary and
  non-authoritative, may duplicate only impacted content, and is deleted after
  finalization. Exact field names and operation kinds can then be defined in the
  File Contract.
- Default assumption if unanswered: Use exact impacted deltas, not prose-only
  instructions or a full Candidate copy.
- Blocking: yes; plan fingerprinting, idempotent resume, derived operation progress,
  and omission prevention depend on this choice.
- Answer: Agreed. Store exact impacted deltas rather than natural-language
  modification instructions.
- Resulting decision: DEC-063

### Q-047 — Operation progress representation

- Status: answered
- Depends on: DEC-056, DEC-060, DEC-063
- Question: Because the sealed plan contains exact observable deltas, should
  Controller derive operation progress from Current rather than persist
  `completed_operations` or introduce an eighth `OP-nnn` ID class?
- Why it matters: Operations are temporary execution steps, not reusable
  specification knowledge. Giving them durable-looking IDs expands ID Schema and
  scanning rules, while a key list duplicates the ordering already owned by the
  immutable sealed plan. A bare cursor would be unsafe if the plan could change,
  but `plan_fingerprint` already rejects reordering or mutation.
- Initial recommendation before DEC-063's consequence was applied: Keep the accepted field name but define
  `completed_operations` as a non-negative integer. `0` means none; `2` means
  exactly the first two ordered operations are reconciled. Controller may only
  increment it by one after comparing that operation's exact expected delta with
  Current, and writes the new Current fingerprint atomically with the increment.
  Resume selects operation `completed_operations + 1`. The sealed plan cannot be
  edited; replacing it requires returning to `planning`, a new fingerprint, and
  resetting/reconciling progress. No `OP` ID or local key exists.
- User clarification question: Is `completed_operations` an ID counter, and what
  does it do for AI?
- Clarification: No. It neither allocates nor counts Specification IDs. The
  proposed integer is only an execution cursor: with a fingerprint-sealed ordered
  plan, value `2` says the first two operations were last confirmed against
  Current and Controller should inspect operation three next. AI should receive
  that derived resume instruction rather than interpret the raw number itself.
- New design consequence from DEC-063: Because every operation now contains an
  exact observable delta, Controller can instead compare all operation outcomes
  with Current on every resume and derive both completed progress and the next
  operation. If the plan also forbids touching the same Record/file target in
  multiple operations, completed state remains directly observable and no cursor
  needs synchronization after a crash.
- Revised recommendation: Remove `completed_operations` from persisted Workflow
  State and reduce DEC-060's five fields to four. `package resume` should return a
  derived `completed_operations` summary for AI, but the state file should store
  only `phase`, `active_question`, `plan_fingerprint`, and
  `reconciled_current_fingerprint`. Consolidate all changes to the same target
  into one plan operation. This costs a small deterministic scan of the limited
  plan/Current set and eliminates a mutable field that could lie or lag after an
  interrupted write.
- Default assumption if unanswered: Use the revised derived-progress
  recommendation and remove the persisted cursor.
- Blocking: yes; Workflow State field types, plan schema, resume, and operation
  reconciliation depend on it.
- User omission example: If operations 1 and 3 are applied first, a prefix count
  cannot show that operation 2 is still missing. This demonstrates that the
  cursor can conceal rather than prevent omission.
- Answer: Agreed. Remove persisted `completed_operations`; derive each
  operation's status independently from the sealed plan and Current.
- Resulting decision: DEC-064

### Q-048 — Candidate Change Set responsibility

- Status: resolved
- Depends on: DEC-063, DEC-064
- Question: Should the temporary ID transition and affected-ID scope be renamed
  from `candidate/application-plan.yaml` to `candidate/change-set.yaml` so it is
  clearly an immutable statement of what this transaction must change, not a
  second progress/status store?
- Why it matters: ID-only evidence minimizes duplicate state and matches the
  removed-ID safety model, but cannot observe every same-ID semantic edit.
  Before/after content distinguishes pending work from an unexpected third value,
  at the cost of copying Current meaning into Candidate and expanding validation.
- Initial recommendation before the duplication objection: For a Record or
  declared file instance, `before` is
  either `absent` or its exact content fingerprint; `after` is either `absent` or
  the exact replacement payload. Controller classifies each unique target as:
  `complete` when it matches `after`, `pending` when it matches `before`, and
  `conflict` otherwise. AI may apply only `pending`; `conflict` enters the shared
  repair process and cannot be overwritten by assumption. This single
  before/after model can later replace separate upsert/remove operation kinds.
- User scope objection: Adding before/after evidence appears to add more
  Validator rules and more places containing the same information. Why not
  record only which IDs should be adjusted; is the extra data merely for AI to
  find its next action faster?
- Clarification:
  - The extra evidence was proposed for interruption/conflict detection, not AI
    speed. It lets a machine distinguish pending from unexpected third-party
    content, but it duplicates impacted Current meaning and increases contract
    surface.
  - No second Validator would be created; the same Validator would interpret an
    additional Application Plan contract. Nevertheless, that additional schema
    and duplicate content are real complexity costs.
  - Do not write workflow progress into the authoritative Current ID Records.
    That would mix temporary execution state into normative meaning. Instead,
    Candidate may contain only the ID-level change set.
- Revised recommendation: Prefer the smaller ID-centered plan:

  ```yaml
  question: Q-012
  remove_ids: [REQ-001]
  add_ids: [REQ-009]
  affected_ids: [BDD-002, TEST-004, TASK-003]
  ```

  Controller derives progress by scanning Current: removed IDs must reach zero
  occurrences, added IDs must appear in the Current ID Index and their one owner,
  and every affected ID is included in the bounded rewrite scope. Final Validator
  checks the complete ID/reference graph and rejects residue. Non-ID routing and
  View effects are derived from the resulting Current IDs rather than copied into
  this plan. This is omission control, not a progress log.
- Accepted limitation to confirm: An ID-only plan cannot mechanically prove that
  a same-ID semantic rewrite is correct or even meaningfully changed. It is fully
  observable only when a normative semantic change replaces/removes/adds an ID,
  while reference-only edits remain observable through old-ID occurrence scans.
  This matches the earlier accepted assumption that an ID transition is the
  practical machine-verifiable proxy for AI applying the content change.
- User duplication question: Workflow State already records state; is another
  mechanism needed?
- State-ownership clarification:
  - No second progress/status mechanism is needed. `workflow-state.yaml` remains
    the only persisted workflow status and stores the phase plus transaction
    fingerprints.
  - `application-plan.yaml` is not status. It is the temporary intent/scope input
    that says which ID transitions and affected IDs must be reconciled. Without
    it, `phase: applying_current` can say work is underway but cannot recover what
    the interrupted work was supposed to change.
  - Current is the actual result. Controller compares Plan intent with Current
    facts and returns ephemeral completed/pending/conflict information; none of
    those labels or per-ID flags are written back to Plan, Current, or Workflow
    State.
  - `validator-attempt.json` retains only the independent three-repair circuit
    breaker, and `validation-result.json` retains only final legality evidence.
    Neither is application progress.
- User conceptual question: Does Application Plan record what this round must do
  and which items are done or not done, making it temporary state?
- Clarification:
  - It records only the first half: the bounded completion obligation for this
    one transaction—Q, removed IDs, added IDs, and affected IDs. It survives an
    interruption and is deleted after finalization, so it is temporary
    transaction data in the broad sense.
  - It never records the second half. No `done`, `pending`, cursor, checkbox, or
    per-ID status is persisted. Current is the observed reality; Controller
    compares it with the sealed obligation and derives progress on demand.
  - `application-plan` is therefore a misleading name after removing operations
    and progress. `change-set.yaml` better expresses a frozen intended ID delta.
    Rename the role to `candidate_change_set` and Workflow State field to
    `change_set_fingerprint`; do not keep aliases for the old names.
- User cardinality question: Does this mean the file will always have only one
  instance?
- Cardinality clarification:
  - Yes, per Feature Package its permitted multiplicity is singleton at the one
    canonical path `candidate/change-set.yaml`; it is not one global file shared
    by every feature.
  - Singleton means at most one, not required presence. It may be absent before a
    transaction and after successful finalization. Validator checks legality of
    an existing file but does not require one to exist.
  - During `discussing`/`planning`, Controller may build and atomically replace
    this one file. Once its fingerprint is stored and phase enters
    `applying_current`, it is sealed and cannot be edited in place.
  - Interruption, `INVALID`, or incomplete application retains the same file.
    Successful DEC creation and finalization delete it; the next Q recreates the
    same canonical path. Numbered copies, timestamps, parallel change sets, and
    retained versions are illegal. Parallel work requires a separate Feature
    Package, not another Candidate file.
- User concurrency scenarios:
  1. What happens when subqueries work concurrently?
  2. What happens when multiple agents work concurrently?
  3. What happens when a session closes midway and a new session starts different
     work?
- Proposed concurrency behavior:
  - Subqueries/subagents may inspect different IDs and return analysis in
    parallel, but they do not write Candidate, Current, History, or Control. The
    coordinating Controller consolidates their findings into the one Change Set
    and serializes mutations. Their raw outputs are not additional package files.
  - Multiple agents may write different Feature Packages independently. For the
    same Feature Package, every mutation goes through one feature-scoped
    command lock plus expected-fingerprint compare-and-swap. The first accepted
    write advances the fingerprint; a concurrent writer holding stale input is
    rejected and must resume/reconcile. Parallel direct filesystem writes are
    unsupported and fail closed when the next fingerprint guard observes them.
  - The command lock is runtime coordination outside the Feature Package, not a
    retained status file or session-long ownership lease. It is released on
    command/process exit, so a crashed Agent cannot permanently own the feature.
    Durable recovery comes from Workflow State, Q, Change Set, and Current—not
    an Agent/session ID.
  - A new session always runs `resume` before starting a Q. If an active
    transaction exists, it resumes that same Q regardless of which Agent created
    it and may not overwrite it with a new transaction.
  - Before `applying_current`, explicit cancellation is safe only after Controller
    verifies Current still matches the prior reconciled/validated fingerprint;
    it then removes the unsealed Candidate data. At or after
    `applying_current`, a new transaction is blocked because Current may be
    partial. The existing transaction must be reconciled and finalized, or a
    human must authorize a recovery/rollback path. It is never silently discarded.
  - A new request may be incorporated into the same Change Set only while phase
    is `discussing` or `planning`. Once sealed, finish the current transaction
    before opening another Q. Unrelated work can proceed immediately only in a
    different Feature Package.
- User enforcement challenge: How can the architecture prevent an Agent from
  modifying files, and how can it force a newly opened Session to call `resume`?
- Enforcement-limit correction:
  - It cannot provide hard prevention when every Agent runs as the same OS user
    with unrestricted direct filesystem tools. A process lock and
    compare-and-swap protect Controller-mediated writes only. The same Agent can
    bypass them with a raw file write; ordinary ACL/read-only flags are not a
    security boundary when that Agent can change those permissions.
  - A Skill also has no global Session-start hook. It cannot force an arbitrary
    new chat to run code merely because the Session opened. It can require every
    managed entry point to call Controller `enter`, which internally performs
    `resume`, before the Skill reads or writes a Feature Package.
  - Under the minimum architecture, enforcement is therefore fail-closed at
    managed boundaries rather than prevention against a malicious/bypassing
    writer: specification-generation entry runs `enter/resume`; every Controller
    write uses a short feature lock plus expected fingerprint; Implementation
    runs qualification preflight; and any unexpected Current/State fingerprint
    blocks further managed work and requires reconciliation.
  - Subagent read-only status is an orchestration instruction, not a filesystem
    capability restriction. For stronger isolation, give each writer a separate
    worktree/package and merge through Controller, or introduce an external write
    broker running under different OS credentials with package ACLs denying Agent
    writes. The latter is a real hard boundary but adds a service, credentials,
    lifecycle management, and recovery surface, contradicting the accepted MVP
    in DEC-050.
  - No validator can prove that a structurally valid direct semantic rewrite was
    intended. It can detect changed fingerprints, illegal IDs/relationships, or
    bypass of `pass`, but human intent remains outside mechanical proof.
- Revised enforcement recommendation: Define this Skill as a cooperative managed
  workflow with fail-closed bypass detection, not an adversarial filesystem
  sandbox. Make `enter/resume` automatic inside every official specification and
  implementation entry point, forbid direct same-feature writes in Agent
  instructions, and serialize accepted changes through Controller. Do not add a
  privileged service for the MVP; document that raw unrestricted writes cannot
  be prevented, only detected at the next managed boundary.
- User necessity objection: This managed-enforcement layer does not appear to
  solve the omission problem. It adds locks, compare-and-swap behavior, entry
  checks, and recovery rules that themselves require maintenance, while an Agent
  with direct filesystem access can still bypass all of them.
- Necessity reassessment:
  - The objection is valid. A command lock, compare-and-swap, and a mandatory
    `enter/resume` convention do not prove that all affected IDs were updated and
    do not make a semantically valid but unintended edit detectable.
  - Their only distinct benefit is coordinating two cooperative writers that
    intentionally mutate the same Feature Package at the same time. That is a
    concurrency feature, not an omission-control feature.
  - The omission-control minimum already has separate owners: the Change Set
    preserves the intended ID transition across interruption; final validation
    checks the closed Current ID/reference graph and removed-ID residue; and
    Implementation accepts only a `PASS` whose Current fingerprint still
    matches. None requires a session identity, long-lived lock, or a second
    concurrency protocol.
  - A new Session can inspect the one Workflow State and retained Change Set as
    its ordinary package-loading behavior. Calling that behavior `resume` does
    not require a separate persisted mechanism or a global Session hook.
  - For the MVP, same-Feature concurrent mutation can instead be an unsupported
    operating constraint: analysis may be parallel, but specification writes are
    serialized by the coordinator. If that convention is violated, the final
    Validator may catch structural/reference damage, but the design must not
    claim hard prevention or complete bypass detection.
- Revised minimum recommendation after the necessity objection: Remove the
  feature lock, compare-and-swap write protocol, forced-Session-resume claim, and
  fingerprint-based bypass-reconciliation layer from this design. Keep only the
  existing Workflow State/Change Set needed for interruption recovery, the one
  final Validator, and Implementation's matching-PASS preflight. Declare
  same-Feature concurrent writers unsupported rather than building a partial
  enforcement subsystem in the MVP.
- Next confirmation question: Should the MVP explicitly reject same-Feature
  concurrent writers and remove the lock/CAS/forced-resume enforcement layer,
  while retaining ordinary state-based continuation plus final validation and
  matching-PASS implementation preflight?
- User simplification question: After removing that enforcement layer, is a
  replacement required, or should the persisted temporary-state mechanism also
  be removed?
- Temporary-state reassessment:
  - Persisted execution phase is no longer necessary once lock ownership,
    compare-and-swap, and bypass reconciliation are removed. `phase`,
    `active_question`, `change_set_fingerprint`, and
    `reconciled_current_fingerprint` can all be derived from the existing Q,
    Change Set, Current, and matching final Validation Result.
  - A `resume` command can therefore be a read-only computation rather than a
    stateful protocol. It scans those owners and returns an ephemeral phase and
    next action. A crash during validation simply causes validation to run again;
    `validating` does not need to be durably recorded.
  - The Change Set is different from progress state. It preserves the confirmed
    intended `remove_ids`, `add_ids`, and `affected_ids` while Current may contain
    only part of that transition. Deleting it would force the next AI to infer
    the intended change from free-form discussion or from a partially modified
    Current, recreating the omission and hallucination risk this design is meant
    to reduce.
  - The final Validation Result is also not temporary workflow state. Its
    matching Current fingerprint is the evidence Implementation consumes; if it
    is absent or mismatched, Implementation stops.
  - Validator retry counting remains Validator-owned circuit-breaker data only
    while an invalid package is being repaired. It does not describe application
    progress and is cleared after success or human handoff.
- Revised minimum alternative: Delete persisted `workflow-state.yaml` and do not
  replace it with another status file. Keep the singleton ID-only Change Set as
  interruption intent, derive resume/next action on demand, and retain only the
  matching final Validation Result as implementation evidence. This reduces one
  maintained authority while preserving recoverability after a partial Current
  rewrite.
- Next confirmation question after simplification: Should persisted Workflow
  State be removed and replaced by derived resume output, while retaining the
  minimal Change Set because it is the only machine-readable record of intended
  ID changes during an interrupted Current rewrite?
- User correction: Removing lock/CAS does not logically imply that durable
  workflow state should also be removed. Before changing that accepted design,
  compare at least ten architectures and have independent subagents judge them.
- Correction accepted: The previous recommendation to remove persisted Workflow
  State was premature and is withdrawn. Concurrency coordination and
  interruption recovery are separate concerns; removing one does not decide the
  other.
- Twelve alternatives considered:

  | # | Architecture | Recovery / omission value | Cost or failure |
  |---|---|---|---|
  | 1 | Current only | No extra owner | Cannot recover intended scope from partial Current |
  | 2 | Current plus final Validator only | Detects legal ID/reference residue | Still cannot know what this transaction intended to change |
  | 3 | Q/discussion plus Current, no structured Change Set or State | Preserves human context | AI must reinterpret prose after interruption; omissions are not mechanically bounded |
  | 4 | Workflow State plus Current, no Change Set | Shows a coarse phase | Cannot identify missing remove/add/affected IDs |
  | 5 | Full six-phase, four-field State plus separate Change Set | Strong navigation and explicit checkpoints | `reconciled_current_fingerprint` and duplicated progress facts can become stale |
  | 6 | Minimal independent checkpoint State plus Change Set | Separates where the Controller committed from what must change | One additional small owner and cross-file invariant |
  | 7 | One `transaction.yaml` containing Q, phase, and Change Set | One atomic work-period owner | Mixes human Q definition, Controller checkpoint, and Candidate intent; conflicts with the accepted Q shape |
  | 8 | Put only `draft | sealed` inside Change Set; derive other phases | One work-period owner and explicit commitment boundary | Cannot independently attest that sealed Candidate bytes did not drift |
  | 9 | Fully derive phase from Q/Change Set/Current/Validation presence | Fewest persisted fields | Planning versus committed-before-first-write is byte-identical; same-ID semantic completion is unobservable |
  | 10 | Per-ID or per-operation progress/cursor | Direct resume hints | Duplicates Current, can hide out-of-order omissions, and adds synchronization rules already rejected |
  | 11 | Append-only event/WAL, full Candidate snapshot, or Git transaction | Strong replay/rollback or atomic promotion | Restores history, duplicate specifications, token growth, or external Git transaction complexity |
  | 12 | SQLite, worktree broker, or ACL-protected service | Strongest atomicity/concurrency enforcement | Adds database/service/schema/credential/recovery infrastructure beyond the MVP |

- Independent subagent review:
  - All three reviewers rejected the inference that lock/CAS removal makes
    durable state unnecessary. All retained structured Change Set intent and at
    least one durable commitment/checkpoint fact.
  - All three agreed that `completed_operations`, persisted next-action prose,
    per-ID done flags, and—after dropping CAS/bypass reconciliation—
    `reconciled_current_fingerprint` should not be retained.
  - All three agreed that no state design proves same-ID semantic correctness,
    prevents unrestricted direct writes, or replaces the final ID/reference
    Validator.
  - Reviewer recommendations differed only in placement: a minimal independent
    Workflow checkpoint, a two-field sealed-Candidate anchor, or a
    `draft | sealed` bit inside Change Set. This is the remaining design choice.
- Facts that cannot be reliably derived from partial Current alone:
  - the transaction's originally confirmed remove/add/affected ID scope;
  - whether the Candidate is still editable or has been committed for Current
    application;
  - planning versus application before the first observable Current write;
  - repair attempts already consumed across Sessions;
  - whether the Controller has completed finalization, rather than the Validator
    merely finding one exact Current structurally legal.
- Facts that should be derived rather than persisted:
  - which remove/add obligations currently match Current;
  - per-ID completed/pending positions and the next mechanical repair;
  - whether an existing Validation Result still matches Current;
  - long-form next-action text, Agent/Session identity, timestamps, and errors.
- Current synthesis: Retain a durable state mechanism, but define it as a small
  Controller checkpoint rather than an application progress ledger. The leading
  separated form is `phase` plus `sealed_change_set_fingerprint`; the active Q
  is derived from the singleton `question.yaml`, application progress is derived
  from Change Set versus Current, and the Current reconciliation fingerprint is
  removed. Change Set continues to own intent and Validation Result continues to
  own legality evidence. This gives three non-overlapping answers: State says
  where the Controller committed, Change Set says what must change, and
  Validation Result says which exact Current passed.
- Revised next question: Should the durable checkpoint remain a separate
  `workflow-state.yaml`, or should its one irreducible commitment fact
  (`draft | sealed`) be merged into `candidate/change-set.yaml`?
- User requested comparison: Compare the proposed minimal independent State with
  both the currently installed Skill and the previously accepted redesign.
- Baseline comparison:

  | Concern | Installed Skill today | Accepted redesign before Q-048 | Current minimal-State proposal |
  |---|---|---|---|
  | State file | Large `00-spec-workflow-status.md` | `control/workflow-state.yaml` | Same `control/workflow-state.yaml` |
  | State shape | Open Markdown sections, checklists and prose | Four closed fields after DEC-064 | Two closed fields |
  | Durable fields | Stage/status/waiting flag, checklist, active Q bookkeeping, decisions, files, stale items, next action, resume prose, and more | `phase`, `active_question`, `plan_fingerprint`, `reconciled_current_fingerprint` | `phase`, `sealed_change_set_fingerprint` |
  | Phase vocabulary | Many stage and status values including blocked/stale/complete | Exactly six closed phases | Same six closed phases |
  | Active Q owner | Status points to `15-open-questions.md`; both must be reconciled | Q defined in `candidate/question.yaml`, ID repeated in State | Q defined and discovered only from singleton `candidate/question.yaml` |
  | Intended change scope | Distributed through prose, decisions, stale lists and affected files | Sealed exact-delta Application Plan | Sealed ID-only Change Set |
  | Application progress | Human/AI-maintained checklist and next action | Derived from Plan versus Current; no operation cursor after DEC-064 | Same derived model, now Change Set versus Current |
  | Current-change checkpoint | No executable fingerprint contract | Last reconciled Current fingerprint persisted in State | Removed because same-Feature concurrent mutation/CAS is unsupported |
  | Resume | Read Status, Stage Manifest, Context Inventory, Decision Log and Open Questions; follow prose `Next AI Action` | Controller derives action from four State fields plus package facts | Controller derives action from phase, sealed Change Set and package facts |
  | Completion | Markdown status/readiness distributed across files | Controller alone sets `phase: pass`; Implementation also requires matching `VALID` | Unchanged: `pass` plus matching `VALID` |
  | Validator | Checklists/advisory readiness; no executable closed State schema | Enum/shape/invariant guard plus one final full Current validation | Same boundary, but two State fields mean fewer invariants |
  | Concurrent same-Feature writers | Not reliably controlled | Q-048 considered lock/CAS and bypass checks | Explicitly unsupported; State does not claim to be a lock |

- Exact delta from the previously accepted four-field State:
  - Keep `phase` and all six accepted values. This preserves the AI-facing
    durable checkpoint, Controller transition ownership, Validator enum guard,
    final `pass`, and implementation preflight.
  - Rename/narrow `plan_fingerprint` to
    `sealed_change_set_fingerprint`, reflecting the proposed ID-only Change Set
    rather than exact operations.
  - Remove `active_question` from State because one canonical
    `candidate/question.yaml` already defines the sole active Q and the Change
    Set references that Q. The Package Schema already rejects a second location.
  - Remove `reconciled_current_fingerprint` because its distinct purpose was to
    bind progress/CAS to the last Controller-observed Current. With operation
    progress derived on every resume and concurrent same-Feature writers
    unsupported, maintaining it after every accepted Current write adds drift
    without improving the final omission check.
  - `completed_operations` is not part of this comparison because DEC-064 had
    already removed it before the two-field proposal.
- Guarantees intentionally lost relative to the four-field redesign:
  - State no longer records which Q it expected independently of the canonical Q
    file; corruption is detected through Q/Change Set contracts instead of a
    duplicate State binding.
  - State no longer detects that Current changed since the Controller's last
    application checkpoint. During application the Controller rescans Current;
    at completion the full Validator checks it; after `pass`, the matching
    Validation Result fingerprint still detects any change before Implementation.
  - Consequently this proposal cannot support safe same-Feature concurrent
    writers or claim general direct-write detection. Neither guarantee solves
    semantic omission, and both are deliberately outside the MVP.
- Guarantees unchanged relative to the four-field redesign:
  - interrupted discussion/application remains durable through Q and Change Set;
  - AI resumes from one of the same six bounded phases;
  - no seventh phase, persisted next-action prose, progress cursor, or per-ID done
    flag is permitted;
  - only Controller writes/transitions State and only Controller establishes
    `pass`; Validator checks legality but never chooses a phase;
  - final validation still scans the complete managed Current ID/reference graph,
    and three failed repair cycles still require human intervention;
  - Implementation still requires both `phase: pass` and an exact matching final
    Validation Result.
- User progress challenge: With only phase and an ID-only Change Set, how does AI
  know what has actually been changed? Why replace the previously agreed method
  at all?
- Correction after re-reading DEC-063 and DEC-064:
  - The original design already had a precise answer. Progress was not owned by
    Workflow State; it was derived by comparing every sealed exact-delta
    Application Plan operation independently with its Current target.
  - An operation whose Current target equals its exact `after` value is complete;
    one still equal to `before` is pending; any third value is conflict. This
    reveals non-prefix progress such as operations 1 and 3 complete while 2 is
    pending without a cursor or persisted done flags.
  - `phase` only says which workflow boundary is active. A Current fingerprint
    only says bytes changed. Neither identifies which intended target is complete.
    The exact Plan is what answers "what has been changed so far."
  - The later ID-only Change Set was proposed to reduce duplicated temporary
    content and Validator/schema surface after the User questioned maintenance
    cost. That optimization preserves removed/new-ID residue checking, but it
    cannot observe whether an `affected_id` with the same ID received its intended
    content rewrite. It therefore weakens the accepted interruption-recovery
    requirement and is not an equivalent replacement.
  - The temporary exact impacted payload is justified duplication: it is scoped
    only to changed targets, sealed for one active transaction, excluded from
    normal Current authority, and deleted after finalization. It is not retained
    specification history or a second complete Candidate specification.
- Revised recommendation after the progress challenge: Withdraw the ID-only
  Change Set replacement and retain DEC-063/DEC-064's sealed exact-delta
  Application Plan with independently derived per-target progress. Do not restore
  `completed_operations`. Evaluate Workflow State field simplification separately
  because it must not remove the Plan evidence that makes resume deterministic.
- Revised next question: Should Q-048 be resolved by retaining the original
  exact-delta Application Plan and limiting simplification only to genuinely
  duplicated Workflow State fields?
- User reset request: The repeated shifts between the original design, the
  proposed simplifications, and their purposes have become unclear. State plainly
  what problem exists, what each existing mechanism was designed to do, what is
  actually missing, and what the conclusion is.
- Design reset summary:
  - The product problem remains unchanged: historical/removed IDs and incomplete
    cross-file revisions can misdirect later AI development, while interrupted
    work must be resumable without trusting conversational memory.
  - The stable redesign through DEC-064 already assigns non-overlapping owners:
    Current owns truth; Candidate Q owns the active discussion; the sealed
    exact-delta Application Plan owns intended changes; Workflow State owns the
    coarse durable phase; Controller derives per-target progress by comparing the
    Plan with Current; Validator checks the final closed-world file/ID graph;
    Validation Result plus `pass` gates Implementation; History retains only
    compact Decision Cards.
  - That design did not lack a progress-recovery mechanism. DEC-063/DEC-064's
    exact deltas and independent target comparison already handle interruption
    and non-prefix completion.
  - Q-048 began only because concurrency scenarios raised the question of
    preventing other Agents or Sessions from writing. Lock/CAS/forced resume was
    explored for that separate concern, then rejected because unrestricted raw
    writes cannot be hard-prevented and same-Feature concurrent mutation need not
    be an MVP feature.
  - The later ID-only Change Set and two-field/no-State variants were attempts to
    reduce maintenance after rejecting concurrency enforcement. They were not
    required by the original omission problem and weakened deterministic resume.
    They are withdrawn proposals, not accepted architecture.
  - What is missing is therefore not another state mechanism. The remaining work
    is to finish the executable exact-delta Plan/File Contract, complete the
    file-role/template migration matrix, implement Controller and Validator, and
    test the accepted flows. Same-Feature concurrent writers remain explicitly
    unsupported in the MVP.
- Current recommendation / rollback point: Return to the coherent DEC-064
  baseline: exact-delta `candidate/application-plan.yaml`; four-field
  `control/workflow-state.yaml`; derived per-target progress with no cursor;
  direct Current rewrite; one final Validator; three-repair limit; compact DEC
  history; and `pass` plus matching Validation Result before Implementation.
  Discard the lock/CAS/forced-resume, ID-only Change Set, and State-removal/two-
  field experiments. Do not reopen these components unless a concrete failure in
  the DEC-064 baseline is demonstrated.
- Default assumption if unanswered: Preserve DEC-063/DEC-064's sealed exact
  impacted deltas and independently derived progress; do not replace that
  recovery evidence with an ID-only Change Set.
- Blocking: yes; Application Plan schema, resume evidence, and the policy for
  same-ID semantic edits depend on this boundary.
- Answer: Agreed to return to the DEC-064 baseline. Retain the exact-delta
  Application Plan and four-field Workflow State; withdraw the lock/CAS,
  forced-resume, ID-only Change Set, and State-removal/two-field experiments.
- Resulting decision: DEC-065

### Q-049 — Exact-delta operation shape

- Status: resolved
- Depends on: DEC-063, DEC-064, DEC-065
- Question: Should the executable Application Plan use one uniform target plus
  `before`/`after` operation shape, rather than several unrelated operation
  formats, so Controller can always classify each target as pending, complete,
  or conflict with the same algorithm?
- Why it matters: DEC-063 requires exact impacted deltas but intentionally leaves
  field names and operation kinds open. The File Contract and Controller cannot
  be implemented until record creation, update, removal, and declared-file
  changes share either one mechanically comparable representation or several
  explicit schemas.
- Recommended answer: Use one uniform operation envelope. Every operation names
  exactly one schema-declared target; `before` is either `absent` or the target's
  exact fingerprint, and `after` is either `absent` or the complete expected
  target payload. Creation is absent-to-payload, update is fingerprint-to-payload,
  and removal is fingerprint-to-absent. Target-specific File Contracts define
  whether the target is an ID Record or a declared file instance. Do not store a
  separate kind when it can be derived from before/after, and do not add progress
  fields.
- Default assumption if unanswered: Use the uniform target plus before/after
  envelope.
- Blocking: yes; exact File Contract fields, reconciliation code, conflict
  findings, and idempotent resume depend on it.
- Answer: Agreed to the uniform target plus `before`/`after` envelope.
- Resulting decision: DEC-066

### Q-050 — Stable Application Plan target identity

- Status: resolved
- Depends on: DEC-031, DEC-041, DEC-063, DEC-066
- Question: Should every operation target a logical Package-Schema role plus an
  optional schema-governed key, rather than storing a raw file path in the
  Application Plan?
- Why it matters: Record owners are YAML multi-document streams, dynamic files
  bind to active IDs, and canonical paths belong only to Package Schema. A raw
  path would duplicate physical architecture and become stale after a legal path
  migration, while an ID alone cannot distinguish a Record target from a dynamic
  file instance using the same ID.
- Recommended answer: Use one closed target object:

  ```yaml
  target:
    role: requirement_records
    key: REQ-001
  ```

  `role` is always required. `key` is required for a Record inside a multi-record
  owner and for an ID-bound dynamic file; it is absent for a fixed singleton
  file. The role's File Contract determines target granularity and the permitted
  key class, while Package Schema resolves the canonical physical file. Do not
  persist a path, target type, or duplicated owner location.
- Default assumption if unanswered: Use `record_id` with schema-derived owner for
  Record targets, and `file_role` plus optional `binding_id` for declared-file
  targets.
- Blocking: yes; operation uniqueness, target lookup, payload parsing, dynamic
  file binding, and path-migration safety depend on it.
- User redundancy challenge: Because an ID/key should already have a schema
  owner that identifies its role, does writing both `role` and `key` help AI, or
  is `role` only another index value that creates duplicate maintenance?
- Reassessment:
  - For an authoritative ID Record, the challenge is correct. ID Schema already
    maps the ID class to exactly one definition-owner role. `REQ-001` therefore
    resolves uniquely to `requirement_records`; repeating that role in the Plan
    adds no information and creates a possible class/role mismatch.
  - For a declared file instance, an ID is not necessarily unique across roles.
    `TASK-003` can identify the Task Record and also bind a Task Manifest. Here
    `role` selects the file collection and the binding ID selects its instance;
    the pair acts as a composite logical index without duplicating a path.
  - For a fixed singleton declared file, only its role can identify it because
    there is no instance key.
  - Explicit role can save AI one lookup, but that small navigation benefit does
    not justify duplicating a fact that the Controller can deterministically
    derive. AI normally receives the resolved target from Controller rather than
    interpreting catalog joins itself.
- Revised recommendation: Use a closed two-variant target rather than always
  storing `role + key`:

  ```yaml
  target:
    record_id: REQ-001
  ```

  for an authoritative ID Record, with owner role derived from ID Schema; or:

  ```yaml
  target:
    file_role: task_manifest
    binding_id: TASK-003
  ```

  for a declared file instance, where `binding_id` is omitted for a singleton.
  Exactly one variant is legal. Do not use generic `key`, repeat a derived Record
  owner role, or store a raw path.
- Revised next question: Should Record operations identify only `record_id` and
  derive their owner role from ID Schema, while declared-file operations use
  `file_role` plus an optional schema-bound `binding_id`?
- User purpose question: What does recording these IDs accomplish, and what is
  `candidate/application-plan.yaml` itself for?
- Purpose clarification:
  - The Application Plan is not an ID index, specification owner, status file, or
    historical archive. It is the sealed, temporary executable intent for one
    answered question while the associated Current rewrite is incomplete.
  - It answers exactly: which logical Current targets this decision must change,
    what each target looked like before application, and what exact result each
    target must reach. Workflow State cannot answer this because phase records
    only where the transaction is, while Current shows only whatever subset has
    already been written.
  - A Record ID is stored only as the stable address of one target inside a YAML
    multi-document owner. Without it, Controller would have to scan prose or
    infer which Record an `after` payload replaces; removal would have no
    remaining payload from which to infer a target at all.
  - Example: one decision affects `REQ-004`, `BDD-007`, and `TEST-010`. If a
    Session stops after applying REQ and TEST, the sealed Plan lets Controller
    classify those two exact results as complete and BDD as pending. Without the
    Plan, partial Current cannot reveal that BDD was intended, so the next AI can
    incorrectly validate or continue from an incomplete semantic change.
  - The IDs and exact impacted payloads exist only during the active transaction.
    After Controller reconciliation, final `VALID`, DEC writing, and Candidate
    cleanup, the entire Plan is deleted before `pass`; old IDs in it never become
    retained history or normal development context.
  - If deterministic recovery from a partially rewritten Current were removed
    from the requirements, this file could be eliminated. Under the accepted
  interruption/resume requirement, it is the one durable owner of intended
  work and therefore has a concrete consumer: Controller resume/reconciliation.
- User clarification accepted: The confusion was caused by presenting only the
  proposed `key`/`role` fields without first explaining the Application Plan's
  transaction-level purpose. It was not yet a rejection of logical target
  identity. For remaining schema questions, explain the owning file, concrete
  consumer, lifecycle, and failure prevented before asking the User to choose
  fields.
- User terminology question: What is `binding_id`?
- `binding_id` clarification:
  - It is not a new ID class, counter, definition, relationship, or index entry.
    It reuses one existing active Current ID to select a particular file instance
    from a Package-Schema role whose filename is dynamic.
  - Example: Package Schema maps `task_manifest` to
    `current/manifests/<TASK-ID>.yaml`. `file_role: task_manifest` selects the
    collection; `binding_id: TASK-003` substitutes the declared placeholder and
    identifies `current/manifests/TASK-003.yaml` without persisting that path in
    the Plan.
  - File Contract checks that the selected role permits a binding, that the ID
    has the required class and is active, and that no two operations target the
    same role/ID pair. A fixed singleton role such as a Dashboard has no binding
    ID.
  - In the current MVP inventory, Task Manifest is the primary concrete consumer.
    If the final migration matrix confirms that it is the only dynamic file role,
    a role-specific name such as `task_id` may be clearer than the generic
    `binding_id`; do not generalize the field merely for hypothetical future
    roles.
- Answer: Agreed. Record targets use only `record_id`; fixed files use only
  `file_role`; the MVP Task Manifest uses `file_role: task_manifest` plus the
  existing `task_id`. Do not add generic `key`/`binding_id` or raw paths.
- Resulting decision: DEC-067

### Q-051 — Machine-checkable before/after encoding

- Status: resolved
- Depends on: DEC-063, DEC-066, DEC-067
- Owning file and consumer: These fields live only inside the transient sealed
  `candidate/application-plan.yaml`. Controller reads them to compare one target
  with Current during apply/resume; the Application Plan File Contract validates
  their shape. They are deleted with the Plan after successful finalization.
- Failure prevented: Controller must distinguish target absence from a literal
  null/empty payload and must know whether a fingerprint or payload is legally
  required. A magic string/object union is compact but easier for AI and parser
  code to misinterpret.
- Question: Should `before` and `after` use explicit closed state objects so
  absence and presence are unambiguous and mechanically validated?
- Recommended answer: Use these exact variants:

  ```yaml
  before:
    state: absent
  ```

  or:

  ```yaml
  before:
    state: present
    fingerprint: sha256:...
  ```

  and:

  ```yaml
  after:
    state: absent
  ```

  or:

  ```yaml
  after:
    state: present
    payload: <complete target value>
  ```

  The File Contract rejects extra/missing conditional fields. Controller derives
  the expected after fingerprint from the canonical payload; do not store that
  fingerprint twice. This is slightly more verbose than the scalar `absent`, but
  it gives one predictable object shape to AI and Validator.
- Default assumption if unanswered: Use explicit `state: absent | present`
  objects with conditional fingerprint/payload.
- Blocking: yes; canonical hashing, payload validation, pending/complete/conflict
  classification, and finding codes depend on it.
- Answer: Agreed to explicit `state: present | absent` objects with conditional
  fingerprint/payload fields.
- Resulting decision: DEC-068

### Q-052 — Application Plan operation ordering semantics

- Status: resolved
- Depends on: DEC-063, DEC-064, DEC-066, DEC-068
- Owning file and consumer: `candidate/application-plan.yaml` contains the
  temporary collection of exact target deltas. Controller reconciles every
  target independently during apply/resume; no list position is persisted in
  Workflow State or exposed as completion evidence.
- Failure prevented: If list order is treated as workflow progress, an AI can
  again assume that completing item 3 implies items 1 and 2 completed, recreating
  the cursor problem rejected by DEC-064. If order has no semantics but YAML
  serialization changes arbitrarily, the sealed plan fingerprint can change for
  no meaningful reason.
- Question: Should operations be an unordered logical set with unique canonical
  targets, while the serialized YAML is sorted deterministically only for stable
  fingerprints and Controller derives any safe application sequence?
- Recommended answer: Yes. Reject duplicate canonical targets and do not encode
  dependencies, priority, progress, or correctness in array position. Canonically
  sort Record targets by ID and file targets by role plus Task ID when sealing
  the Plan. Controller may process pending targets in a deterministic safe order
  derived from the state transition (create, update, remove) and ID relationships,
  but resume always reclassifies every target independently.
- Default assumption if unanswered: Use unordered-set semantics with canonical
  serialization and Controller-derived application order.
- Blocking: yes; plan hashing, duplicate-target findings, resume summaries, and
  application sequencing depend on it.
- Answer: Agreed to unordered-set semantics with deterministic sealed
  serialization; list position never represents progress.
- Resulting decision: DEC-069

### Q-053 — Target-scoped canonical fingerprints

- Status: resolved
- Depends on: DEC-026, DEC-063, DEC-066, DEC-068, DEC-069
- Owning file and consumer: `before.fingerprint` lives only in the sealed
  Application Plan. Controller computes the same value from the current logical
  target during apply/resume to decide whether that target is still pending or
  has become a conflict; after-payload comparison uses the same canonicalizer.
- Failure prevented: Hashing the entire multi-record owner file would make an
  unrelated Record update change every operation's `before` value. Hashing raw
  YAML bytes would also create false conflicts from key order, indentation, or
  line-ending changes that parse to the same structured value.
- Question: Should each operation fingerprint only its resolved logical target,
  using the target role's parser followed by one canonical structured
  serialization, rather than hashing the containing file or raw YAML bytes?
- Recommended answer: Yes. For a Record target, hash only that parsed `id` plus
  `content` document; for a declared structured-file target, hash its complete
  parsed logical value. Serialize JSON-compatible values deterministically with
  sorted object keys, preserved array order, UTF-8, and no insignificant
  whitespace, then store lowercase `sha256:<64-hex>`. The same Controller module
  canonicalizes `before`, `after.payload`, Current comparison, and the sealed
  Plan. File Contracts reject unsupported or ambiguous YAML value types rather
  than creating role-specific hash algorithms.
- Default assumption if unanswered: Use target-scoped canonical structured
  SHA-256 fingerprints.
- Blocking: yes; independent progress, conflict classification, cross-platform
  stability, and Plan sealing depend on it.
- Answer: Agreed, provided this solves target-level resume/conflict detection.
- Resulting decision: DEC-070

### Q-054 — Mechanical boundary for omitted semantic dependents

- Status: resolved
- Depends on: DEC-005, DEC-007, DEC-030, DEC-033, DEC-063, DEC-070, DEC-071
- Concrete problem: Exact Plan targets and fingerprints prove whether every
  *listed* target reached its expected result. They cannot prove that AI listed a
  semantically affected target whose ID/reference does not mechanically change.
- Existing accepted boundary: DEC-007 permits a Specification Item to be edited
  in place before implementation, but requires a replacement ID after
  implementation. Under the replacement path, schema-declared consumers still
  containing the removed ID fail final validation, making downstream omission
  mechanically visible. Under an in-place same-ID edit, reverse ID dependents can
  be shown to AI for impact analysis, but Validator cannot prove which of them
  needed semantic rewriting.
- Why it matters to the original failure: A specification change discovered by
  code review after development falls on the implemented/replacement-ID side and
  is therefore mechanically traceable. Expanding replacement to every previously
  validated (`pass`) semantic change would catch more pre-implementation
  omissions, but would churn IDs throughout ordinary specification discussion.
- Question: Keep DEC-007's boundary—edit in place before implementation and
  replace the ID after implementation—or move the freeze boundary earlier so
  every semantic change to a previously `pass` Record requires a replacement ID?
- Revised recommendation after the requested multi-agent red team: Freeze every
  normative Record when it first appears in a sealed Application Plan or a
  validated workflow `pass` baseline. The former makes the payload immutable
  during application/repair; the latter makes every later semantic revision use
  remove/add/reference churn. This is earlier than implementation, but it is the
  only proposed boundary that is both mechanically provable and independent of
  deleted execution history. Task states such as `in-progress`,
  `ready-for-review`, and `accepted` are either reversible, too late, or lack an
  executable Task-to-Spec input closure.
- User mechanism question: Is there one place that records which old IDs must be
  replaced by which new IDs, after which Validator can detect every old ID that
  was not replaced?
- Clarification:
  - There is one active-transaction owner, but it is not a second old-to-new
    mapping table. The sealed Application Plan records exact Record removals,
    Record creations, and complete reference/content rewrites. It survives
    interruption and is deleted before final workflow `pass`; it is never a
    permanent old-ID registry.
  - Controller derives the removed-ID set from Record operations whose
    `before` is present and `after` is absent, then discovers every Current
    reverse reference before sealing. Each discovered target must have its own
    exact operation. One-to-one, split, merge, deletion-without-replacement, and
    pure-add changes therefore use the same mechanism without an ambiguous
    pairing field.
  - `current/id-index.yaml` owns only the final active-ID allowlist. During the
    rewrite, Controller adds the new IDs, applies every exact dependent target,
    removes the old definitions, and removes the old IDs from the Index.
  - Final Validator scans only Current normative/routing content against that
    active allowlist and the definition owners. Any remaining occurrence of an
    old well-formed ID is undefined/not active and therefore `INVALID`, even
    without retaining a separate historical blacklist. Candidate may
    intentionally contain the old IDs during application and is excluded from
    the Current residue scan.
  - After exact question-Plan reconciliation, Finalizer deterministically writes
    the compact Decision Card without Specification IDs and deletes the Plan/Q.
    This returns to the clean between-question checkpoint, not workflow `pass`.
    Only explicit package finish plus Controller completion and final `VALID`
    enters `pass`, so Implementation sees neither the old ID nor transaction data.
  - Neither per-question Controller reconciliation nor final Validator needs an
    old-to-new pair. Before Q cleanup, Controller proves every target and the
    complete Current equal that Plan's expected final. At explicit package
    finish, Validator proves the active Index/definitions/references have no
    removed or undefined residue and binds the complete final Current. Exact
    `after` payloads, not a parallel mapping, define each consumer result.
- Multi-agent assurance audit requested by the User:
  - Three independent reviewers compared Current-only validation, active Index
    plus transition map, ID-only Change Set, progress cursor/checklist, full
    Candidate promotion, event/DB/Git transaction systems, exact Plan with AI
    manual copying, and exact Plan with Controller application. The full matrix
    and P0/P1 gaps are recorded once in `docs/spec-skill-refactor-plan.md`.
  - All three retained the exact-delta Plan. They rejected Current-only,
    ID-only, cursor, full Candidate, and event/DB/Git variants for either missing
    recovery/omission evidence or adding a second specification/history/control
    plane.
  - Two reviewers concluded that explicit `id_transitions` has no unique runtime
    consumer: removed/added IDs are already derived from Record operations,
    exact dependent after payloads already define routing, and Validator needs
    only final active membership plus zero old occurrences. The red-team reviewer
    found a map useful only if it drives additional split/merge-specific logic;
    no such requirement currently exists.
  - Resulting decision (DEC-071): Do not add `id_transitions`. During planning,
    Q/discussion may explain split/merge meaning; the sealed machine contract
    remains exact operations only. Controller derives removed IDs from
    present-to-absent Record targets and performs reverse-reference closure before
    sealing.
  - The more important correction is write ownership: AI writes each exact
    after payload once into the Plan, then Controller applies it. AI must not copy
    the same payload manually into Current.
  - To detect an unlisted but otherwise legal Current modification, Controller
    virtually applies the Plan to the complete normative/routing Current at seal
    time and stores one `expected_final_current_fingerprint`. All listed targets
    must reconcile and the actual complete Current must match that fingerprint
    before final Validator execution. A mismatch has no safe baseline recovery
    in the MVP and goes directly to human assistance.
  - The audit also found blocking gaps outside the Plan envelope: finalizing
    cleanup crash recovery, Specification ID no-reuse allocation, the executable
    freeze predicate, legacy-ID rejection patterns, pass cleanup guards,
    A/B/A repair counting, and stale Blueprint/Context/refactor-plan wording.
    DEC-072 through DEC-081 initially closed finalization, freeze, allocation,
    repair, State, Plan, qualification and migration. A second crash/maintenance
    red team found per-question PASS, fresh-allocation proof, repair atomicity,
    generic validation binding, deterministic replay, and cold-History allocation
    dependency gaps; DEC-082 through DEC-087 close them without replacing the
    exact-delta architecture.
- Correction to the earlier clarification: An explicit old-to-new pair is useful
  to a human explanation but is not needed by Controller application or final
  Validator residue checks once exact operations, reverse-reference closure, and
  the expected-final fingerprint exist. Do not create a second transition owner
  without a confirmed consumer.
- Default assumption if unanswered: Use the mechanically provable first-seal /
  first-`pass` boundary because the User prioritized solving omission risk over
  minimizing ID churn.
- Blocking: yes; ID replacement rate, Plan target expansion, removed-ID checks,
  and the residual semantic omission guarantee depend on it.
- Answer: Adopted under the User's accepted minimal-safe objective after three
  independent audit agents compared six freeze boundaries. The deliberate cost
  is more ID churn; the avoided cost is a sticky implementation-history latch,
  a complete Task-to-Spec execution-input graph, and an unprovable same-ID
  semantic omission gap.
- Resulting decision: DEC-073

### Q-022 — Trusted Current validation

- Status: resolved
- Depends on: DEC-015, DEC-027, DEC-029, DEC-034
- Question: Should every normal specification-generation, resume, or
  implementation entry validate `current/` and require it to match the exact
  fingerprint, ID Schema fingerprint, and validator version recorded when the
  last Candidate was promoted, blocking use if any value differs?
- Why it matters: Candidate validation protects Current only at promotion time.
  Without a Current check, a direct file edit, partial copy, damaged file,
  validator upgrade, or schema change could bypass the transaction and still
  drive implementation. A structurally valid direct edit must also be rejected
  because it never passed the authorized Candidate promotion boundary.
- Recommended answer:
  - Keep one validator-owned, non-historical
    `.control/current-attestation.json` containing only the last promoted
    package fingerprint, ID Schema fingerprint, and validator version. Keep the
    transient retry/lock transaction state separate and delete only that
    transient state after promotion.
  - Before normal generation, resume, or development, run Current validation,
    recompute the complete Current fingerprint, and compare all three values
    with the attestation. Proceed only when validation is `PASS` and the values
    match.
  - A missing, malformed, mismatched, or stale attestation makes Current
    `UNTRUSTED`; the Skill stops and may not silently bless the files even when
    their current structure happens to validate.
  - The first migration performs a full Current validation and creates the
    initial attestation only through an explicit migration operation.
  - Candidate `PASS` authorizes promotion, not partial copying. After atomic
    replacement, verify that the promoted Current fingerprint equals the
    validated Candidate fingerprint, then atomically replace the attestation.
    A failure leaves the prior Current and prior attestation authoritative.
- Meaning of Candidate validation: It is the pre-commit safety boundary that
  permits all related files to be changed together without exposing partial
  work. Current validation is the use-time safety boundary that proves the
  package still equals a previously promoted PASS. Both are required; neither
  substitutes for the other.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; Candidate value, direct-edit detection, Current loading,
  `.control/` contents, migration, and promotion recovery depend on it.
- Answer: No. Do not split validation into Candidate validation and use-time
  Current attestation. Candidate is only a temporary discussion/planning area.
  Apply the complete ID/content/reference transition to Current, then validate
  that final Current once; the purpose is to prove no historical material
  remains before later development.
- Resulting decision: DEC-035

### Q-023 — Preventing unvalidated Current from driving implementation

- Status: resolved
- Depends on: DEC-003, DEC-017, DEC-028, DEC-029, DEC-035
- Question: Because Current is edited directly and may be temporarily incomplete,
  should each final validation `PASS` be bound to the complete Current package
  fingerprint, so any managed-file change automatically makes that result
  inapplicable and `implement-spec-task` must match the current fingerprint to a
  final `PASS` before development can begin?
- Why it matters: Removing Candidate promotion also removes the untouched
  fallback package. A crash, tool error, interrupted AI turn, or `INVALID`
  result can leave Current with some old IDs removed and some dependent content
  not yet updated. The risk is not reading that state for repair; it is treating
  it as implementation-ready before final validation.
- Existing-Skill audit requested by the user:
  - `spec-package-generator` uses `00-spec-workflow-status.md` as its resume point
    and `00-stage-manifest.md` as stage-order authority. Status supports
    `in-progress`, `stale`, and `blocked`; resume follows `Next AI Action` and
    reconciles disagreements from the separate owners.
  - The durable decision protocol writes sequentially: persist the answer,
    append the Decision, apply affected specification artifacts, mark downstream
    artifacts stale, resolve the question, then update workflow status. It says
    no next question may start until all writes succeed, but it has no atomic
    transaction or rollback if interruption occurs between those writes.
  - Gate re-open and Spec Change Request flows stop downstream generation, mark
    dependent artifacts stale, require human reconfirmation, and regenerate
    Manifest versions/digests before implementation should resume. These are
    instruction-level controls recorded in editable Markdown.
  - Final readiness is a persisted Markdown checklist/result. Repository scan
    found no executable specification-package validator or runtime lock used by
    this Skill.
  - `implement-spec-task` does fail closed when readiness is not `pass`, Task
    Plan approval is absent, or a Manifest-pinned normative digest differs. It
    also refuses to edit specification artifacts and returns a Spec Change
    Request when code evidence requires a specification change.
  - However, executor qualification does not read the generator workflow status
    or stage-manifest rewrite state. The current Manifest template pins only the
    approved baseline, Task Index, selected Task, Test Strategy, and Task Plan
    review—not every upstream PRD, EARS, BDD, technical-design, decision, or
    status artifact. A revision interrupted before stale/readiness/Manifest
    propagation can therefore leave an old implementation package that still
    appears eligible.
  - Current behavior is consequently advisory recovery plus partial freshness
    detection, not mutual exclusion. It often catches completed invalidation or
    pinned-file edits, but cannot deterministically prevent every half-applied
    Current rewrite from being consumed.
- Effectiveness clarification requested by the user:
  - The existing Markdown status/readiness/digest mechanism is not sufficient
    for the stated omission-prevention goal. Continuing it unchanged would
    still leave the same interruption and incomplete-propagation gaps.
  - Invalidating the previous `PASS` before the first Current edit is only an
    implementation safety gate. It prevents a partial rewrite from being
    treated as development-ready, but it neither discovers missing edits nor
    proves that the final specification is complete.
  - The closed-world final Validator is the omission detector. It inventories
    every managed file, rejects unknown files, compares the active ID Index with
    definitions, validates every schema-declared reference in both directions,
    rejects removed-ID occurrences, and checks required derived outputs.
  - The two proposed controls are therefore complementary: invalidation closes
    the time window during modification; final validation closes detectable
    structural and referential omissions before development.
  - Even the new Validator cannot prove an unencoded semantic relationship. If
    two requirements are related only in natural-language meaning and no ID
    reference or schema rule represents that relationship, an AI may still miss
    the synchronized change while all deterministic checks pass. DEC-030 and
    DEC-033 reduce this residual risk by requiring every normative relationship
    that must trigger synchronized change to be expressed as an in-content ID
    reference.
- Earlier minimal recommendation after user challenge:
  - Do not add a filesystem read lock. The same specification workflow must be
    able to inspect, repair, and resume the partially rewritten Current.
  - Before the first Current content edit, invalidate/remove the previous final
    validation `PASS` as the transaction's first durable write and retain the
    active question/application state. If interruption occurs afterward, there
    is no valid implementation handoff result to consume.
  - Apply all planned ID Index changes, definitions, references, content, file
    deletion, and derived-view regeneration directly to Current. Do not validate
    each intermediate edit.
  - After the planned rewrite is complete, run the one full Current validation.
    `INVALID` permits targeted repair/rerun under the existing three-attempt
    limit. `ERROR` stops with no `PASS`. A process restart resumes the same
    application from Active Question State and Current.
  - `implement-spec-task` must require the new final validation result to be
    `PASS`; an absent, pending, `INVALID`, or `ERROR` result blocks development.
    `PASS` then permits deletion of Candidate planning and consumed transient
    records, writing the cold Decision Card, and clearing Active Question State.
  - If specification rewriting and implementation are guaranteed never to
    overlap and only the human invokes implementation after completion, this is
    a readiness prerequisite rather than mutual exclusion. Git remains only
    emergency recovery when the rewrite cannot be completed.
- ID-versus-package-state clarification requested by the user:
  - Specification IDs identify current normative content and its relationships.
    They do not by themselves prove that every Current file represents the same
    completed rewrite. One ID change can require synchronized updates to several
    other ID Records and consumer files, leaving an interrupted intermediate
    package even though every intended change is ID-anchored.
  - An Answer Application Transaction may be anchored by its active Question or
    review finding, but individual byte/file edits do not need new historical
    change IDs. The final Current retains only the resulting active IDs and
    content under DEC-019.
  - A final validation result is package-level evidence, not another
    Specification ID. It means that one exact fingerprint of the whole
    closed-world Current package passed all checks.
  - Prefer derived freshness over an AI-maintained `PASS -> pending` state: the
    Validator writes `PASS` together with the complete Current fingerprint;
    `implement-spec-task` recomputes the fingerprint once at its qualification
    boundary and accepts the result only when they match. Any managed-file edit,
    including an interrupted first edit, makes the old result inapplicable
    automatically. This comparison is not a second full validation and is not
    performed on ordinary specification reads.
  - The transient retry/application control can still record attempt count and
    the active transaction, but implementation eligibility is derived from the
    fingerprint match rather than trusting AI to update a mutable readiness
    flag in the correct order.
- Modification/check loop risk raised by the user:
  - A fingerprint comparison cannot create a repair loop: it only returns
    `MATCH` or `MISMATCH` for implementation qualification and never edits
    Current, expands scope, reopens a Gate, or invokes the Validator itself.
  - A badly scoped Validator could recreate the existing boundary/check loop if
    it treated semantic preference, speculative completeness, or review advice
    as blocking errors. The final Validator must therefore fail only on finite,
    deterministic rules declared in the schema and managed-file catalog.
  - Run the full Validator only after the planned Current rewrite is complete,
    not after every ID or file edit. On `INVALID`, repair only the reported
    deterministic violations and rerun against the same approved change scope;
    validation may not invent requirements or automatically reopen questioning,
    Gate confirmation, or implementation review.
  - Semantic ambiguity is a non-blocking investigation finding under DEC-011,
    not an endless automatic repair instruction. A finding that requires a new
    product/specification decision is escalated to the human as a new explicit
    transaction rather than silently extending the current one.
  - DEC-062 bounds deterministic repair to three distinct repaired checkpoint
    states across state and package validation. The third failed repaired state
    produces one consolidated report and stops; an unchanged rerun does not
    create progress or justify another repair cycle.
  - `implement-spec-task` encountering `MISMATCH` stops with one stable reason:
    Current is not the exact validated package. It must not automatically edit
    specifications, repeatedly launch validation, or bounce between boundary
    and check phases.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; interruption recovery, final-result ownership, retry counting,
  cleanup order, and implementation qualification depend on it.
- Answer: Candidate may preserve interrupted discussion but remains
  non-authoritative and temporary. Each answered question becomes one exact Plan
  applied directly to Current; State plus Plan lets AI resume and Controller
  prove target/full-Current completion. That question then writes its compact
  Decision and cleans Candidate without running full validation. Only when the
  User explicitly declares the whole package finished does Controller check the
  completion profile and run one full Validator. Complete ID replacement is the
  mechanical evidence that named content was adjusted; semantic correctness
  remains outside Validator. Matching final evidence plus cleanup permits State
  `pass`.
- Resulting decision: DEC-036

### Q-024 — Decision Card retention trigger after Candidate cleanup

- Status: resolved
- Depends on: DEC-016, DEC-019, DEC-023, DEC-035, DEC-036
- Question: After confirming that "history" means only compact cold Decision
  Cards, should every resolved material decision produce one card, or should a
  card be retained only when the human explicitly requests it?
- Why it matters: Earlier decisions intentionally retained questions and material
  decisions while deleting all other historical specification/process data. If
  "process history" now means a detailed timeline or preserved Candidate packet,
  it reverses that boundary and can restore the context growth and stale-source
  ambiguity this redesign is intended to remove.
- Recommended answer: Yes. Candidate is the complete temporary recovery source
  while work is active; after final validation, retain only the compact material
  decision rationale already allowed by DEC-019 and DEC-023, plus at most a small
  completion fact that does not contain old Specification IDs or copied Current
  content. Delete the raw process and Validator repair trail.
- User challenge: The workflow proposed writing process history without first
  identifying a concrete future consumer or benefit. The user does not know what
  such history should contain and expects it to provide almost no value.
- Reassessment:
  - Raw Candidate discussion exists only to resume the active transaction; delete
    it after finalization.
  - Current-application progress exists only to resume or reconcile interrupted
    work; clear it after finalization.
  - Validator findings and retry state exist only to repair the active Current;
    delete them after finalization.
  - A transaction-completion event has no identified consumer because final
    Current and final workflow `pass` already own the useful result; do not create
    a separate completion history merely for chronology.
  - Old Specification IDs, replaced content, and detailed change timelines harm
    normal AI retrieval and remain prohibited.
  - The only plausible cold-history value is answering an explicit future
    question such as "why was this non-obvious choice made?" or avoiding repeat
    consideration of one rejected alternative. It is not required for resume,
    validation, implementation, readiness, rollback, or Current authority.
- Revised recommendation: Do not retain process history or a completion summary.
  Make a compact Decision Card exceptional and opt-in: retain one only when the
  human explicitly marks a non-obvious decision rationale as worth remembering.
  Otherwise finalization deletes the entire Candidate transaction and transient
  control/repair data, leaving only Current plus final workflow state. If agreed,
  this narrows DEC-016 and DEC-023 from automatic material-decision retention to
  explicit human-selected retention.
- Terminology clarification from the user:
  - The user's "history data" means the same compact Decision Cards already
    discussed; it does not introduce a detailed process log.
  - The assistant's later phrases "process history" and "transaction completion
    summary" incorrectly suggested a second historical subsystem. Remove that
    concept.
  - The only historical data under consideration is the cold Decision Archive
    containing compact cards. Candidate drafts, Current-application progress,
    Validator findings/retries, resume logs, prior `PASS` results, old IDs, and
    old specification content are transient or replaced current state, not
    history, and are deleted rather than archived.
- Current recommendation after clarification: Preserve one compact card for each
  confirmed material decision, consistent with DEC-016 and DEC-023, but preserve
  no transcript, process timeline, or completion summary. Because the archive is
  physically cold and excluded from default loading and Current validation, this
  retains rationale without adding normal AI context. The remaining decision is
  whether card creation is automatic for every material decision or explicit
  human opt-in.
- Default assumption if unanswered: Use the recommended answer.
- Blocking: yes; Candidate garbage collection, archive schema, Workflow State
  Center finalization, and physical root layout depend on it.
- Answer: Automatically create the compact Decision Card for every confirmed
  material decision.
- Resulting decision: DEC-037
- Later timing refinement: DEC-082/084 writes the deterministic card and cleans
  that question immediately after exact Plan reconciliation; it no longer waits
  for whole-package final validation or implies workflow `pass`.

#### Requested comparison evidence

- Full retention helps targeted forensic work, rollback analysis, audit, and remembering rejected alternatives, but only when retrieval is explicit and narrow.
- Full retention harms normal AI work when stale and current requirements coexist: it increases token use, salience dilution, accidental stale retrieval, authority ambiguity, graph/link validation complexity, and the chance that generated outputs combine incompatible versions.
- Full deletion gives normal AI one current truth, smaller searches, simpler validation, and fewer opportunities to follow stale IDs. It loses rationale, makes repeated design debates more likely, weakens incident explanation, and encourages AI to infer or invent why unusual code exists.
- Repository evidence favors removing history from normal context: the inspected package's duplicated question/decision files total about 346 KB with no open question, yet the current workflow requires rereading them; the existing ID ecosystem also has extensive references and inconsistent prefixes.
- The hybrid keeps normal execution equivalent to full deletion while allowing explicit rationale retrieval. Its residual risk is accidental archive loading, mitigated by physical separation, no current references, and a strict explicit-load rule.

## Unresolved Queue

- Complete the executable schemas, migration dispositions, and fixtures implied
  by DEC-074 through DEC-087; no unresolved product-policy question remains.
