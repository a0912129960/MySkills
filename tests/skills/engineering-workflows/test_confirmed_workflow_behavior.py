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
        prompt = read(
            ENGINEERING
            / "spec-package-generator"
            / "templates"
            / "tdd-prompt.template.md"
        )
        self.assertIn("AGENTS.md", prompt)
        self.assertIn("CLAUDE.md", prompt)
        self.assertIn("PROJECT_RULES.md", prompt)
        self.assertIn("codebase-design", prompt)
        self.assertIn("interface", prompt)
        self.assertIn("seam", prompt)

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

    def test_spec_tasks_support_safe_parallel_waves(self) -> None:
        package = ENGINEERING / "spec-package-generator"
        task = read(package / "templates" / "task.template.md")
        index = read(package / "templates" / "31-final-task-index.template.md")
        prompt = read(package / "templates" / "tdd-prompt.template.md")

        for required in (
            "Parallel wave",
            "Exclusive ownership paths",
            "Shared read-only contracts",
            "Integration owner",
        ):
            with self.subTest(required=required):
                self.assertIn(required, f"{task}\n{index}")
        self.assertIn("Other workers may continue independent eligible tasks", prompt)

    def test_spec_uses_grill_me_only_as_an_explicit_pause(self) -> None:
        governance = read(
            ENGINEERING
            / "spec-package-generator"
            / "references"
            / "question-and-decision-governance.md"
        )
        self.assertIn("Do not invoke `grill-me` automatically", governance)
        self.assertIn("Ask one decision question at a time", governance)
        self.assertIn("Do not apply the plan during the grilling phase", governance)


if __name__ == "__main__":
    unittest.main()
