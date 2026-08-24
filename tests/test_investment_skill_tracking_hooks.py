import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "skills" / "investment-research.md"
CHECKLIST = ROOT / "skills" / "investment-checklist.md"
TRIGGER_MONITOR = ROOT / "skills" / "trigger-monitor.md"


class InvestmentSkillTrackingHooksTest(unittest.TestCase):
    def test_investment_research_requires_tracking_ledger_update(self):
        text = RESEARCH.read_text(encoding="utf-8")

        for requirement in (
            "reports/标的跟踪表.md",
            "每个已完成研究的标的",
            "重点标的看板",
            "禁止重复新增",
            "状态与命中率摘要",
            "跟踪表更新失败",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_investment_checklist_requires_key_target_promotion(self):
        text = CHECKLIST.read_text(encoding="utf-8")

        for requirement in (
            "reports/重点标的看板.md",
            "每个执行 Checklist 的标的",
            "无论 Checklist 结论",
            "reports/标的跟踪表.md",
            "移除该标的的旧事件行",
            "禁止重复新增",
            "重点标的更新失败",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_trigger_registration_routes_validation_to_daily_monitor(self):
        text = TRIGGER_MONITOR.read_text(encoding="utf-8")

        self.assertIn("python3 tools/daily_monitor.py --check", text)
        self.assertIn("--state-file", text)
        self.assertIn("--report-dir", text)
        self.assertNotIn("weekly-review", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
