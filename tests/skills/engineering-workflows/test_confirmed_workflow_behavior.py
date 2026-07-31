from __future__ import annotations

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = ROOT / "skills" / "engineering"
PRODUCTIVITY = ROOT / "skills" / "productivity"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ConfirmedWorkflowBehaviorTests(unittest.TestCase):
    def test_router_mentions_only_managed_workflow_names(self) -> None:
        router = read(ENGINEERING / "ask-myskills" / "SKILL.md")
        for excluded_name in (
            "ask-matt",
            "setup-matt-pocock-skills",
            "to-tickets",
            "triage",
            "wayfinder",
            "research",
            "teach",
            "writing-great-skills",
        ):
            with self.subTest(excluded_name=excluded_name):
                self.assertNotIn(f"`{excluded_name}`", router)

        self.assertIn("spec-package-generator", router)
        self.assertIn("ai-handoff", router)
        self.assertIn("session-checkpoint", router)
        self.assertIn("wiki-query", router)
        self.assertIn("obsidian-cli", router)
        self.assertIn("qmd", router)

        inventory = json.loads(
            (ROOT / "inventory" / "skills.json").read_text(encoding="utf-8")
        )
        managed_names = {
            skill["managed_name"]
            for skill in inventory["skills"]
            if skill["state"] == "managed"
        }
        routed_names = set(re.findall(r"`([a-z][a-z0-9-]+)`", router))
        self.assertLessEqual(routed_names, managed_names)

    def test_lightweight_implementation_does_not_commit_by_default(self) -> None:
        workflow = read(ENGINEERING / "implement" / "SKILL.md")
        self.assertIn("formal `spec-package-generator` package", workflow)
        self.assertIn("Load `codebase-design` when", workflow)
        self.assertIn("Do not create a branch, commit, stage, push", workflow)
        self.assertIn("`code-review`", workflow)

    def test_formal_spec_task_executor_is_fail_closed_and_human_gated(
        self,
    ) -> None:
        package = ENGINEERING / "implement-spec-task"
        workflow = read(package / "SKILL.md")
        execution = read(package / "references" / "execution-contract.md")

        for required in (
            "Task Execution Manifest",
            "Execution Preflight",
            "one formal Task",
            "awaiting-preflight-approval",
            "ready-for-review",
            "changes-requested",
            "accepted",
            "Spec Change Request",
            "Execution Record",
            "append-only",
            "Do not start the next Task",
        ):
            with self.subTest(required=required):
                self.assertIn(required, f"{workflow}\n{execution}")

        self.assertIn("fail closed", workflow.lower())
        self.assertIn("Only the human", execution)
        self.assertIn("Do not create a branch, worktree, commit, stage, push", execution)

    def test_formal_spec_task_executor_controls_same_task_subagents(
        self,
    ) -> None:
        package = ENGINEERING / "implement-spec-task"
        execution = read(package / "references" / "execution-contract.md")
        work_unit = read(package / "templates" / "work-unit-brief.template.md")

        for required in (
            "Task Coordinator",
            "Task Test Owner",
            "Task Work Unit",
            "Work Unit Brief",
            "exclusive write",
            "shared files",
            "read-only",
            "Integrated Task Validation",
        ):
            with self.subTest(required=required):
                self.assertIn(required.lower(), f"{execution}\n{work_unit}".lower())

        self.assertIn("same workspace", execution)
        self.assertIn("must not interpret the full specification package", work_unit)

    def test_code_review_preserves_both_axes_and_smell_baseline(self) -> None:
        workflow = read(ENGINEERING / "code-review" / "SKILL.md")
        baseline = read(
            ENGINEERING
            / "code-review"
            / "references"
            / "standards-baseline.md"
        )
        self.assertIn("**Standards**", workflow)
        self.assertIn("**Spec**", workflow)
        for smell in (
            "Mysterious Name",
            "Duplicated Code",
            "Feature Envy",
            "Data Clumps",
            "Primitive Obsession",
            "Repeated Switches",
            "Shotgun Surgery",
            "Divergent Change",
            "Speculative Generality",
            "Message Chains",
            "Middle Man",
            "Refused Bequest",
        ):
            with self.subTest(smell=smell):
                self.assertIn(smell, baseline)

    def test_diagnosis_only_request_does_not_authorize_a_fix(self) -> None:
        workflow = read(ENGINEERING / "diagnosing-bugs" / "SKILL.md")
        self.assertIn(
            "Diagnosis does not authorize a repair",
            workflow,
        )
        self.assertIn(
            "Apply the fix only when the human requested implementation",
            workflow,
        )

    def test_to_spec_uses_the_local_lightweight_artifact(self) -> None:
        workflow = read(ENGINEERING / "to-spec" / "SKILL.md")
        self.assertIn(".scratch/<feature-slug>/spec.md", workflow)
        self.assertIn("Do not interview", workflow)
        self.assertIn("Do not create or mutate an issue", workflow)

    def test_prototype_keeps_artifacts_until_the_human_decides(self) -> None:
        workflow = read(ENGINEERING / "prototype" / "SKILL.md")
        logic = read(ENGINEERING / "prototype" / "LOGIC.md")
        ui = read(ENGINEERING / "prototype" / "UI.md")
        self.assertIn(".scratch/<prototype-slug>/", workflow)
        self.assertIn("Do not delete prototype files", workflow)
        self.assertIn("Do not promote code, create a branch, or commit", logic)
        self.assertIn("Keep all prototype files", ui)
        self.assertIn("Do not create a\nbranch, commit, or issue", ui)

    def test_checkpoint_is_local_and_never_delivered(self) -> None:
        workflow = read(PRODUCTIVITY / "session-checkpoint" / "SKILL.md")
        self.assertIn("<current-project-root>/HANDOFF.md", workflow)
        self.assertIn("never contact, create, or select another AI session", workflow)
        self.assertIn("inspect it first", workflow)

    def test_live_handoff_never_guesses_the_destination_agent(self) -> None:
        workflow = read(PRODUCTIVITY / "ai-handoff" / "SKILL.md")
        self.assertIn(
            "ask the human rather than guessing an agent",
            " ".join(workflow.split()),
        )

    def test_spec_tasks_re_read_project_rules_and_conditionally_load_design(
        self,
    ) -> None:
        executor = read(ENGINEERING / "implement-spec-task" / "SKILL.md")
        manifest = read(
            ENGINEERING
            / "spec-package-generator"
            / "templates"
            / "task-execution-manifest.template.yaml"
        )
        combined = f"{executor}\n{manifest}"
        self.assertIn("AGENTS.md", combined)
        self.assertIn("CLAUDE.md", combined)
        self.assertIn("PROJECT_RULES.md", combined)
        self.assertIn("codebase-design", combined)
        self.assertIn("interface", combined)
        self.assertIn("seam", combined)

    def test_greenfield_package_bootstraps_confirmed_project_rules(self) -> None:
        skill = read(ENGINEERING / "spec-package-generator" / "SKILL.md")
        task = read(
            ENGINEERING
            / "spec-package-generator"
            / "templates"
            / "task.template.md"
        )
        self.assertIn("project-rules-init", skill)
        self.assertIn("project-rules-init", task)

    def test_spec_workflow_never_installs_mermaid_itself(self) -> None:
        package = ENGINEERING / "spec-package-generator"
        content = "\n".join(
            read(path)
            for path in package.rglob("*.md")
        )
        self.assertNotIn("offer to install", content.lower())
        self.assertNotIn("install the missing Mermaid", content)
        self.assertNotIn("npm install", content.lower())

    def test_spec_tasks_are_vertical_capability_slices(self) -> None:
        package = ENGINEERING / "spec-package-generator"
        tasking = read(package / "references" / "traceability-and-tasking.md")
        task = read(package / "templates" / "task.template.md")
        readiness = read(
            package / "templates" / "35a-final-readiness-result.template.md"
        )

        for required in (
            "vertical capability slice",
            "user- or system-observable outcome",
            "public validation seam",
            "end-to-end validation route",
        ):
            with self.subTest(required=required):
                combined = f"{tasking}\n{task}\n{readiness}".lower()
                self.assertIn(required.lower(), combined)

        self.assertNotIn("roughly 3-5 likely files", tasking)
        self.assertNotIn("one screen, one API", tasking)

    def test_spec_tasks_plan_parallel_waves_but_execute_one_formal_task(
        self,
    ) -> None:
        package = ENGINEERING / "spec-package-generator"
        task = read(package / "templates" / "task.template.md")
        index = read(package / "templates" / "31-final-task-index.template.md")
        manifest = read(
            package / "templates" / "task-execution-manifest.template.yaml"
        )

        for required in (
            "Parallel wave",
            "Exclusive ownership paths",
            "Shared read-only contracts",
            "Integration owner",
        ):
            with self.subTest(required=required):
                self.assertIn(required, f"{task}\n{index}")
        self.assertIn("formal_task_limit: 1", manifest)
        self.assertIn("same_task_subagents_allowed: true", manifest)

    def test_spec_uses_durable_one_question_grilling(self) -> None:
        package = ENGINEERING / "spec-package-generator"
        governance = read(
            package / "references" / "question-and-decision-governance.md"
        )
        status = read(package / "templates" / "00-spec-workflow-status.template.md")
        questions = read(package / "templates" / "15-open-questions.template.md")
        stage_manifest = read(package / "references" / "stage-manifest.md")
        stage_manifest_template = read(
            package / "templates" / "00-stage-manifest.template.md"
        )
        workflow = read(package / "references" / "workflow.md")
        status_tracking = read(package / "references" / "status-tracking.md")
        grill_me = read(PRODUCTIVITY / "grill-me" / "SKILL.md")
        grill_with_docs = read(ENGINEERING / "grill-with-docs" / "SKILL.md")
        package_contract_text = "\n".join(
            read(path)
            for path in sorted(package.rglob("*"))
            if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}
        )

        self.assertIn("## Durable Grilling Protocol", governance)
        self.assertIn("Ask exactly one active decision question", governance)
        self.assertIn("Only after all writes succeed", governance)
        self.assertIn("append a Decision ID", governance)
        self.assertIn("currently existing stage-owned affected", governance)
        self.assertIn("- Recommended answer and brief rationale", governance)
        self.assertIn("Active Question ID", status)
        self.assertIn("Previous answer persisted", status)
        self.assertIn("Ask exactly one active question at a time", questions)
        self.assertIn("durable one-question loop", workflow)
        gate1_clarification = stage_manifest.index(
            "4. Gate 1 durable decision clarification"
        )
        gate1_sketch = stage_manifest.index("5. Gate 1 flow sketch")
        architecture_grounding = stage_manifest.index("7. Architecture grounding")
        gate2_clarification = stage_manifest.index(
            "8. Gate 2 durable decision clarification"
        )
        gate2_sketch = stage_manifest.index("9. Gate 2 solution sketch")
        self.assertLess(gate1_clarification, gate1_sketch)
        self.assertLess(architecture_grounding, gate2_clarification)
        self.assertLess(gate2_clarification, gate2_sketch)
        self.assertIn(
            "## Durable Decision Clarification Status",
            stage_manifest_template,
        )
        self.assertIn("`gate1-decision-clarification`", stage_manifest_template)
        self.assertIn("`gate2-decision-clarification`", stage_manifest_template)
        self.assertNotIn("- Active Question ID:", stage_manifest_template)
        self.assertNotIn("mirrored from", stage_manifest)
        self.assertIn(
            "sole owner of the active\nQuestion ID",
            status_tracking,
        )
        self.assertNotIn("grill-me", package_contract_text)
        self.assertNotIn("grill-with-doc", package_contract_text)
        self.assertNotIn("spec-package-generator", grill_me)
        self.assertNotIn("spec-package-generator", grill_with_docs)
        self.assertNotIn("normal batch clarification", governance)

    def test_spec_evaluation_does_not_mix_decision_and_micro_gate_questions(
        self,
    ) -> None:
        cases = json.loads(
            (ROOT / "evaluations" / "cases" / "spec-package-generator.json").read_text(
                encoding="utf-8"
            )
        )
        core_cases = {case["id"]: case for case in cases["core_cases"]}
        intake = core_cases["greenfield-intake-micro-gate"]

        self.assertIn(
            "Do not ask for flow-sketch confirmation until",
            intake["prompt"],
        )
        self.assertIn(
            "without also requesting flow-sketch confirmation",
            intake["oracle"]["expected_outcome"],
        )

    def test_spec_package_requires_task_plan_gate_and_execution_manifests(
        self,
    ) -> None:
        package = ENGINEERING / "spec-package-generator"
        workflow = read(package / "references" / "workflow.md")
        manifest = read(
            package / "templates" / "task-execution-manifest.template.yaml"
        )
        task_plan = read(
            package / "templates" / "32-task-plan-review.template.md"
        )
        prompt = read(package / "templates" / "tdd-prompt.template.md")

        self.assertIn("Task Plan Gate", workflow)
        self.assertIn("Task Plan Gate", task_plan)
        self.assertIn("human-confirmed", task_plan)
        for required in (
            "task_id:",
            "artifact_digests:",
            "dependencies:",
            "allowed_production_paths:",
            "skill_plan:",
            "validation:",
            "evidence:",
            "freshness:",
        ):
            with self.subTest(required=required):
                self.assertIn(required, manifest)

        self.assertIn("$implement-spec-task <manifest-path>", prompt)
        self.assertNotIn("## Before Coding", prompt)
        self.assertNotIn("## After Coding", prompt)
        self.assertIn('path: "32-task-plan-review.md"', manifest)
        self.assertNotIn('path: "35a-final-readiness-result.md"\n      sha256:', manifest)
        self.assertIn("only_human_accepted_unblocks: true", manifest)
        self.assertNotIn("safe_deferrals:", manifest)
        self.assertIn("status_only_mutations:", manifest)

    def test_one_shot_never_bypasses_the_task_plan_gate(self) -> None:
        workflow = read(
            ENGINEERING
            / "spec-package-generator"
            / "references"
            / "workflow.md"
        )
        self.assertIn(
            "One-shot mode does not pre-approve or skip the Task Plan Gate",
            workflow,
        )
        self.assertIn(
            "wait for human confirmation before Manifests",
            workflow,
        )

    def test_spec_revision_handoff_is_explicit_and_evidence_backed(self) -> None:
        package = ENGINEERING / "implement-spec-task"
        request = read(
            package / "templates" / "spec-change-request.template.md"
        )
        for required in (
            "Task ID",
            "Code Evidence",
            "Classification",
            "Return Level",
            "Affected Normative Artifacts",
            "Partial Change State",
            "$spec-package-generator",
        ):
            with self.subTest(required=required):
                self.assertIn(required, request)

        generator = read(ENGINEERING / "spec-package-generator" / "SKILL.md")
        self.assertIn(
            "$spec-package-generator <feature-package-path> --revise-from <request-path>",
            generator,
        )
        self.assertIn("reopen Gate 1", generator)
        self.assertIn("reopen Gate 2", generator)
        self.assertIn("return to the Task Plan Gate", generator)
        self.assertIn("already committed or", generator)
        self.assertIn("remain uncommitted", generator)
        self.assertIn("Manifest version with new digests", generator)


if __name__ == "__main__":
    unittest.main()
