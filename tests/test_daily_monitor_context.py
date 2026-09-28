import tempfile
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import quote

from tools.daily_monitoring.context import (
    build_context,
    find_completeness_gaps,
    primary_research_report,
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ResearchContextTest(unittest.TestCase):
    def test_primary_report_returns_link_and_latest_labeled_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "reports" / "公司" / "公司-research-20260801.md"
            latest = root / "reports" / "公司" / "公司-thesis.md"
            write(older, "# 旧报告\n**报告日期：2026-08-01**\n")
            write(
                latest,
                "# 投资论文\n**建立日期：2026年4月9日** | "
                "**最新追踪更新：2026年8月31日**\n"
                "\n**数据截止：2026-08-25**\n",
            )

            selected = primary_research_report(
                root,
                root / "reports" / "daily-monitor",
                {"links": [str(older.relative_to(root)), str(latest.relative_to(root))]},
            )

            self.assertEqual(
                selected,
                (quote("../公司/公司-thesis.md", safe="/-._~"), date(2026, 8, 31)),
            )

    def test_primary_report_reads_generic_header_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "reports" / "Booking" / "最终报告.md",
                "# 报告\n> 日期：2026-05-16\n",
            )

            selected = primary_research_report(
                root,
                root / "reports" / "daily-monitor",
                {"links": ["reports/Booking/最终报告.md"]},
            )

            self.assertEqual(
                selected,
                (quote("../Booking/最终报告.md", safe="/-._~"), date(2026, 5, 16)),
            )

    def test_primary_report_keeps_undated_link_without_inventing_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports" / "公司" / "最终报告.md", "# 无日期报告\n")

            selected = primary_research_report(
                root,
                root / "reports" / "daily-monitor",
                {"links": ["reports/公司/最终报告.md"]},
            )

            self.assertEqual(
                selected,
                (quote("../公司/最终报告.md", safe="/-._~"), None),
            )

    def test_context_uses_target_files_and_matching_rows_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "reports" / "重点标的看板.md",
                "# 看板\n\n| 标的 | 健康度 | 本周关注 |\n|---|---|---|\n"
                "| 腾讯 | 7/10 | 核验自由现金流 |\n"
                "| 另一家公司 | 1/10 | 不应进入腾讯上下文 |\n",
            )
            write(
                root / "reports" / "标的跟踪表.md",
                "# 台账\n\n| 标的 | 状态 |\n|---|---|\n| 腾讯 | 待触发 |\n| 另一家公司 | 已触发 |\n",
            )
            write(
                root / "reports" / "腾讯" / "腾讯-thesis.md",
                "# 腾讯 thesis\n\n## 论文红线\n\n自由现金流连续恶化。\n\n"
                "## 下次检查\n\n2026Q3 财报后。\n",
            )
            write(
                root / "reports" / "另一家公司" / "另一家公司-thesis.md",
                "# 另一家公司\n\n内部秘密，不应进入腾讯上下文。\n",
            )
            target = {
                "id": "腾讯",
                "name": "腾讯控股",
                "links": ["reports/腾讯/腾讯-thesis.md"],
            }

            context = build_context(root, target, max_chars=4000)

            self.assertIn("论文红线", context.text)
            self.assertIn("核验自由现金流", context.text)
            self.assertNotIn("内部秘密", context.text)
            self.assertNotIn("不应进入腾讯上下文", context.text)
            self.assertLessEqual(len(context.text), 4000)

    def test_context_rejects_link_that_escapes_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside-secret.md"
            outside.write_text("secret", encoding="utf-8")
            target = {"id": "腾讯", "name": "腾讯", "links": ["../outside-secret.md"]}

            context = build_context(root, target, max_chars=4000)

            self.assertNotIn("secret", context.text)
            self.assertTrue(any("越界" in item for item in context.limitations))
            outside.unlink()


class CompletenessGapTest(unittest.TestCase):
    def test_missing_configured_link_is_other_monitoring_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports" / "重点标的看板.md", "# 看板\n腾讯\n")
            write(root / "reports" / "标的跟踪表.md", "# 台账\n")
            target = {
                "id": "腾讯",
                "name": "腾讯",
                "links": ["reports/腾讯/missing-thesis.md"],
                "zones": [],
                "events": [],
            }

            gaps = find_completeness_gaps(root, [target], today=date(2026, 8, 25))

            broken = next(gap for gap in gaps if gap.metadata["gap_type"] == "broken_link")
            self.assertEqual(broken.section, "other")
            self.assertEqual(broken.priority, "P1")
            self.assertTrue(broken.needs_human_review)

    def test_explicit_price_in_linked_report_without_zone_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports" / "重点标的看板.md", "# 看板\n腾讯\n")
            write(root / "reports" / "标的跟踪表.md", "# 台账\n")
            write(
                root / "reports" / "腾讯" / "研究.md",
                "# 腾讯研究\n\n仅在 400–430 港元进入复核区间。\n",
            )
            target = {
                "id": "腾讯",
                "name": "腾讯",
                "links": ["reports/腾讯/研究.md"],
                "zones": [],
                "events": [],
            }

            gaps = find_completeness_gaps(root, [target], today=date(2026, 8, 25))

            self.assertIn("unregistered_price", {gap.metadata["gap_type"] for gap in gaps})

    def test_thesis_without_next_check_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports" / "重点标的看板.md", "# 看板\n腾讯\n")
            write(root / "reports" / "标的跟踪表.md", "# 台账\n")
            write(
                root / "reports" / "腾讯" / "腾讯-thesis.md",
                "# 腾讯论文\n\n## 红线\n\n自由现金流恶化。\n",
            )
            target = {
                "id": "腾讯",
                "name": "腾讯",
                "links": ["reports/腾讯/腾讯-thesis.md"],
                "zones": [],
                "events": [],
            }

            gaps = find_completeness_gaps(root, [target], today=date(2026, 8, 25))

            self.assertIn("missing_next_check", {gap.metadata["gap_type"] for gap in gaps})

    def test_overdue_open_ledger_row_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports" / "重点标的看板.md", "# 看板\n")
            write(
                root / "reports" / "标的跟踪表.md",
                "# 台账\n\n"
                "| ID | 标的 | 复检日 | 状态 |\n"
                "|---|---|---|---|\n"
                "| row-1 | 某公司 | 2026-08-20 | 待触发 |\n",
            )

            gaps = find_completeness_gaps(root, [], today=date(2026, 8, 25))

            overdue = next(gap for gap in gaps if gap.metadata["gap_type"] == "overdue_ledger")
            self.assertEqual(overdue.priority, "P0")
            self.assertIn("某公司", overdue.name)


if __name__ == "__main__":
    unittest.main()
