import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillGenerationSetTest(unittest.TestCase):
    def test_generated_skill_sets_exactly_match_canonical_sources(self):
        canonical = {path.stem for path in (ROOT / "skills").glob("*.md")}
        codex = {
            path.parent.name
            for path in (ROOT / "codex-skills").glob("*/SKILL.md")
            if path.parent.name != "investment-memo-craft"
        }
        cursor = {
            path.parent.name
            for path in (ROOT / "cursor-skills").glob("*/SKILL.md")
        }
        dsh = {
            path.parent.name for path in (ROOT / "dsh-skills").glob("*/SKILL.md")
        }
        prompts = {path.stem for path in (ROOT / "codex-prompts").glob("*.md")}

        self.assertEqual(codex, canonical)
        self.assertEqual(cursor, canonical)
        self.assertEqual(dsh, canonical)
        self.assertEqual(prompts, canonical)

    def test_daily_monitor_is_the_only_active_monitoring_skill(self):
        canonical = {path.stem for path in (ROOT / "skills").glob("*.md")}

        self.assertIn("daily-monitor", canonical)
        self.assertNotIn("weekly-review", canonical)
        text = (ROOT / "skills" / "daily-monitor.md").read_text(encoding="utf-8")
        for requirement in (
            "python3 tools/daily_monitor.py --check",
            "--offline-fixtures",
            "--check-ai",
            "价格监控",
            "财报与正式披露监控",
            "其他监控",
            "不构成买卖或仓位结论",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


if __name__ == "__main__":
    unittest.main()
