from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
INVENTORY_PATH = ROOT / "inventory" / "skills.json"


def load_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} has no YAML frontmatter")

    frontmatter, _, _ = text[4:].partition("\n---\n")
    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip().strip('"')
    return values


class ManagedWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.origins = {
            origin["id"]: origin for origin in cls.inventory["origins"]
        }
        cls.skills = [
            skill
            for skill in cls.inventory["skills"]
            if skill["state"] == "managed"
            and skill["category"] in {"engineering", "productivity"}
            and skill["managed_name"] != "skill-evaluator"
        ]

    def test_inventory_selects_the_confirmed_agent_one_skill_set(self) -> None:
        self.assertEqual(
            {skill["managed_name"] for skill in self.skills},
            {
                "ai-handoff",
                "ask-myskills",
                "codebase-design",
                "code-review",
                "diagnosing-bugs",
                "domain-modeling",
                "grill-me",
                "grill-with-docs",
                "grilling",
                "implement",
                "implement-spec-task",
                "improve-codebase-architecture",
                "prototype",
                "session-checkpoint",
                "spec-package-generator",
                "tdd",
                "to-spec",
            },
        )

    def test_each_managed_workflow_has_canonical_metadata_and_policy(self) -> None:
        for skill in self.skills:
            with self.subTest(skill=skill["managed_name"]):
                skill_dir = (
                    ROOT / "skills" / skill["category"] / skill["managed_name"]
                )
                skill_md = skill_dir / "SKILL.md"
                openai_yaml = skill_dir / "agents" / "openai.yaml"

                self.assertTrue(skill_md.is_file(), f"missing {skill_md}")
                self.assertTrue(openai_yaml.is_file(), f"missing {openai_yaml}")

                frontmatter = load_frontmatter(skill_md)
                self.assertEqual(frontmatter.get("name"), skill["managed_name"])
                self.assertTrue(frontmatter.get("description"))

                metadata = openai_yaml.read_text(encoding="utf-8")
                self.assertIn(f"${skill['managed_name']}", metadata)

                claude_explicit = (
                    frontmatter.get("disable-model-invocation") == "true"
                )
                codex_policy = re.search(
                    r"(?m)^\s*allow_implicit_invocation:\s*(true|false)\s*$",
                    metadata,
                )
                expected_explicit = skill["invocation"] == "explicit"
                self.assertEqual(claude_explicit, expected_explicit)
                self.assertIsNotNone(codex_policy)
                self.assertEqual(
                    codex_policy.group(1) == "true",
                    not expected_explicit,
                )

    def test_inventory_preserves_import_provenance(self) -> None:
        for skill in self.skills:
            with self.subTest(skill=skill["managed_name"]):
                origin = self.origins[skill["origin"]]
                self.assertEqual(skill["owner"], "MySkills")
                self.assertEqual(skill.get("imported_on"), "2026-07-24")
                self.assertTrue(skill["source_name"])
                self.assertTrue(skill["source_path"])
                if origin["kind"] == "repository":
                    self.assertTrue(origin["repository_url"])
                    if skill["origin"] != "myskills":
                        self.assertRegex(origin["revision"], r"^[0-9a-f]{40}$")

    def test_managed_renames_do_not_leave_source_named_directories(self) -> None:
        self.assertFalse((ROOT / "skills" / "engineering" / "ask-matt").exists())
        self.assertFalse((ROOT / "skills" / "productivity" / "handoff").exists())

    def test_agent_one_buckets_contain_no_excluded_workflows(self) -> None:
        expected = {skill["managed_name"] for skill in self.skills}
        actual = {
            path.parent.name
            for bucket in ("engineering", "productivity")
            for path in (ROOT / "skills" / bucket).glob("*/SKILL.md")
            if path.parent.name != "skill-evaluator"
        }
        self.assertEqual(actual, expected)

    def test_packaged_markdown_links_resolve_inside_each_skill(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for skill in self.skills:
            skill_dir = ROOT / "skills" / skill["category"] / skill["managed_name"]
            markdown = skill_dir / "SKILL.md"
            for target in link_pattern.findall(markdown.read_text(encoding="utf-8")):
                target = target.split("#", 1)[0]
                if (
                    not target
                    or "://" in target
                    or target.startswith(("mailto:", "/"))
                ):
                    continue
                with self.subTest(skill=skill["managed_name"], target=target):
                    self.assertTrue((markdown.parent / target).resolve().exists())


if __name__ == "__main__":
    unittest.main()
