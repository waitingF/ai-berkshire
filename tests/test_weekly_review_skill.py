import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "weekly-review.md"


class WeeklyReviewSkillContractTest(unittest.TestCase):
    def setUp(self):
        self.text = SOURCE.read_text(encoding="utf-8")

    def test_default_scope_and_read_only_boundary_are_explicit(self):
        self.assertIn("重点标的看板", self.text)
        self.assertIn("买卖建议跟踪表", self.text)
        self.assertIn("未来 14 天", self.text)
        self.assertIn("不写入", self.text)
        self.assertIn("不修改", self.text)

    def test_priority_and_output_contract_are_explicit(self):
        for label in ("P0", "P1", "P2", "本周待办队列", "建议分流"):
            with self.subTest(label=label):
                self.assertIn(label, self.text)

    def test_price_is_not_a_fundamental_change(self):
        self.assertIn("价格变化不能单独改变论文健康度", self.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
