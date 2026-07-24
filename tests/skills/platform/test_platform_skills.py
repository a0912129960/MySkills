from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
PLATFORM_SKILLS = {
    "engineering/skill-evaluator": "explicit",
    "obsidian/json-canvas": "implicit",
    "obsidian/obsidian-bases": "implicit",
    "obsidian/obsidian-cli": "implicit",
    "obsidian/obsidian-markdown": "implicit",
    "qmd/qmd": "implicit",
}


class PlatformSkillContractTests(unittest.TestCase):
    def test_owned_managed_skills_have_matching_portable_metadata(self) -> None:
        for relative_path, invocation in PLATFORM_SKILLS.items():
            with self.subTest(skill=relative_path):
                skill_dir = ROOT / "skills" / relative_path
                skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                openai_yaml = (skill_dir / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                name = skill_dir.name

                self.assertRegex(skill_md, rf"(?m)^name:\s*{re.escape(name)}\s*$")
                self.assertIn(f"${name}", openai_yaml)
                self.assertNotIn("C:\\project\\LLM Wiki", skill_md)
                self.assertNotIn("$OBSIDIAN_WIKI_REPO", skill_md)

                if invocation == "explicit":
                    self.assertRegex(
                        skill_md, r"(?m)^disable-model-invocation:\s*true\s*$"
                    )
                    self.assertRegex(
                        openai_yaml,
                        r"(?m)^\s+allow_implicit_invocation:\s*false\s*$",
                    )
                else:
                    self.assertNotRegex(
                        skill_md, r"(?m)^disable-model-invocation:\s*true\s*$"
                    )
                    self.assertNotRegex(
                        openai_yaml,
                        r"(?m)^\s+allow_implicit_invocation:\s*false\s*$",
                    )

    def test_qmd_retains_allowed_tools_without_owning_installation(self) -> None:
        skill_md = (ROOT / "skills" / "qmd" / "qmd" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertRegex(skill_md, r"(?m)^allowed-tools:\s*.+qmd")
        self.assertNotIn("npm install", skill_md)
        self.assertIn("verified\nruntime capability", skill_md)
        self.assertIn("do not change host dependency", skill_md)

    def test_skill_evaluator_is_evaluation_only(self) -> None:
        skill_md = (
            ROOT / "skills" / "engineering" / "skill-evaluator" / "SKILL.md"
        ).read_text(encoding="utf-8")
        lowered = skill_md.lower()
        self.assertNotIn("package_skill.py", lowered)
        self.assertNotIn("create a new skill", lowered)
        self.assertIn("claude", lowered)
        self.assertIn("codex", lowered)
        self.assertIn("attestation", lowered)

    def test_inventory_is_the_only_skill_provenance_file(self) -> None:
        for relative_path in PLATFORM_SKILLS:
            skill_dir = ROOT / "skills" / relative_path
            with self.subTest(skill=relative_path):
                self.assertFalse((skill_dir / "PROVENANCE.json").exists())


if __name__ == "__main__":
    unittest.main()
