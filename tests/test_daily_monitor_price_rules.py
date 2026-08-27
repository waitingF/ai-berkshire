import unittest

from tools.trigger_scanner import judge_zone


class PricePriorityRuleTest(unittest.TestCase):
    def setUp(self):
        self.zone = {
            "label": "评估带",
            "dir": "range",
            "low": 100,
            "high": 120,
        }

    def test_price_below_range_is_triggered(self):
        status, message = judge_zone(90, self.zone, near_ratio=0.05)

        self.assertEqual(status, "TRIGGERED")
        self.assertIn("区间内或以下", message)

    def test_price_above_upper_boundary_within_five_percent_is_near(self):
        status, _ = judge_zone(126, self.zone, near_ratio=0.05)

        self.assertEqual(status, "NEAR")

    def test_price_more_than_five_percent_above_upper_boundary_is_far(self):
        status, _ = judge_zone(126.01, self.zone, near_ratio=0.05)

        self.assertEqual(status, "FAR")

    def test_price_ceiling_more_than_five_percent_above_is_far(self):
        ceiling = {"label": "不追高线", "dir": "below", "high": 440}

        self.assertEqual(judge_zone(487.31, ceiling, near_ratio=0.05)[0], "FAR")

    def test_above_warning_zone_keeps_directional_semantics(self):
        warning = {"label": "估值警戒线", "dir": "above", "low": 120}

        self.assertEqual(judge_zone(122, warning, near_ratio=0.05)[0], "WARN")
        self.assertEqual(judge_zone(117, warning, near_ratio=0.05)[0], "NEAR")
        self.assertEqual(judge_zone(100, warning, near_ratio=0.05)[0], "FAR")


if __name__ == "__main__":
    unittest.main()
