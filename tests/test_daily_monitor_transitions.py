import unittest
from datetime import date

from tools.daily_monitoring import transitions


def target():
    return {"id": "腾讯", "name": "腾讯控股"}


def zone(direction="range"):
    return {
        "label": "复核带",
        "market": "H",
        "dir": direction,
        "low": 400,
        "high": 430,
        "note": "需核验经营条件与 thesis 红线",
    }


class PriceTransitionTest(unittest.TestCase):
    def test_first_entry_into_review_band_is_p0(self):
        item = transitions.price_item(
            target(), zone(), previous="FAR", current="TRIGGERED", price=410
        )

        self.assertEqual(item.priority, "P0")
        self.assertTrue(item.notify)
        self.assertFalse(item.resolved)
        self.assertIn("价格条件", item.why_now)
        self.assertNotIn("建议买入", item.why_now)

    def test_unchanged_trigger_stays_p0_without_notification(self):
        item = transitions.price_item(
            target(), zone(), previous="TRIGGERED", current="TRIGGERED", price=410
        )

        self.assertEqual((item.priority, item.notify), ("P0", False))
        self.assertEqual(item.status, "TRIGGERED")

    def test_unchanged_near_stays_p1_without_notification(self):
        item = transitions.price_item(
            target(), zone(), previous="NEAR", current="NEAR", price=390
        )

        self.assertEqual((item.priority, item.notify), ("P1", False))

    def test_leaving_band_emits_one_resolved_item(self):
        item = transitions.price_item(
            target(), zone(), previous="TRIGGERED", current="FAR", price=450
        )

        self.assertTrue(item.resolved)
        self.assertTrue(item.notify)
        self.assertEqual(item.priority, "P2")

    def test_first_run_uses_current_priority_without_notifying(self):
        item = transitions.price_item(
            target(), zone(), previous=None, current="TRIGGERED", price=410
        )

        self.assertEqual((item.priority, item.notify), ("P0", False))
        self.assertIn("初始基线", item.why_now)

    def test_far_price_is_visible_as_p2_without_notification(self):
        item = transitions.price_item(
            target(), zone(), previous="FAR", current="FAR", price=500
        )

        self.assertEqual((item.priority, item.notify), ("P2", False))
        self.assertEqual(item.status, "FAR")

    def test_quote_failure_and_recovery_each_notify_once(self):
        failed = transitions.price_item(
            target(), zone(), previous="FAR", current="NO_DATA", price=None
        )
        recovered = transitions.price_item(
            target(), zone(), previous="NO_DATA", current="FAR", price=500
        )

        self.assertEqual((failed.priority, failed.notify), ("P1", True))
        self.assertTrue(failed.needs_human_review)
        self.assertTrue(recovered.resolved)
        self.assertTrue(recovered.notify)

    def test_repeated_missing_quote_stays_p1_without_notification(self):
        item = transitions.price_item(
            target(), zone(), previous="NO_DATA", current="NO_DATA", price=None
        )

        self.assertEqual((item.priority, item.notify), ("P1", False))


class EventTransitionTest(unittest.TestCase):
    def test_event_classifier_has_fourteen_day_window(self):
        event = {"date": "2026-09-07", "type": "财报", "label": "中报"}

        status, days = transitions.classify_event(event, date(2026, 8, 24))

        self.assertEqual((status, days), ("UPCOMING_14D", 14))

    def test_overdue_review_event_is_p0_even_on_first_run(self):
        event = {"date": "2026-08-20", "type": "复检", "label": "论文复检"}

        item = transitions.event_item(
            target(), event, previous=None, current="OVERDUE", days=-4
        )

        self.assertEqual(item.priority, "P0")
        self.assertEqual(item.section, "other")
        self.assertTrue(item.notify)

    def test_financial_event_within_fourteen_days_belongs_to_disclosure_section(self):
        event = {"date": "2026-09-07", "type": "财报", "label": "中报"}

        item = transitions.event_item(
            target(), event, previous="FUTURE", current="UPCOMING_14D", days=14
        )

        self.assertEqual(item.section, "disclosures")
        self.assertEqual(item.priority, "P1")
        self.assertTrue(item.notify)

    def test_unchanged_upcoming_event_does_not_renotify(self):
        event = {"date": "2026-09-07", "type": "投资者日", "label": "Investor Day"}

        item = transitions.event_item(
            target(), event, previous="UPCOMING_14D", current="UPCOMING_14D", days=14
        )

        self.assertEqual(item.priority, "P2")
        self.assertFalse(item.notify)

    def test_done_event_is_hidden(self):
        event = {
            "date": "2026-08-20",
            "type": "财报",
            "label": "中报",
            "done": True,
        }

        self.assertEqual(transitions.classify_event(event, date(2026, 8, 24)), ("DONE", None))
        self.assertIsNone(
            transitions.event_item(
                target(), event, previous="TODAY", current="DONE", days=None
            )
        )


class PriorityFloorTest(unittest.TestCase):
    def test_ai_cannot_lower_program_floor(self):
        self.assertEqual(transitions.apply_priority_floor("P2", "P0"), "P0")

    def test_ai_can_raise_program_floor(self):
        self.assertEqual(transitions.apply_priority_floor("P0", "P1"), "P0")

    def test_rejects_invalid_priority(self):
        with self.assertRaisesRegex(ValueError, "P9"):
            transitions.apply_priority_floor("P9", "P1")


if __name__ == "__main__":
    unittest.main()
