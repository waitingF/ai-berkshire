import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.daily_monitoring.models import MonitorItem, RunResult, SourceHealth
from tools.daily_monitoring.report import render_markdown, write_reports


def item(
    fingerprint,
    section,
    priority,
    *,
    target_id="腾讯",
    name="腾讯控股",
    title="监控事项",
    workflow=None,
    notify=False,
    resolved=False,
    status="NEW",
    metadata=None,
):
    return MonitorItem(
        fingerprint=fingerprint,
        section=section,
        priority=priority,
        target_id=target_id,
        name=name,
        title=title,
        why_now="出现了需要研究核验的增量，不构成买卖结论。",
        status=status,
        source_urls=(
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/example.pdf",
        ) if section == "disclosures" else (),
        next_workflow=workflow,
        notify=notify,
        resolved=resolved,
        metadata=metadata or {},
    )


def result(items):
    items = tuple(items)
    return RunResult(
        status="OK",
        items=items,
        notification_items=tuple(row for row in items if row.notify),
        source_health=(SourceHealth("hkex", "OK"),),
        next_state={"schema": 1},
        report_paths=None,
    )


class DailyMonitorReportTest(unittest.TestCase):
    def test_price_section_renders_all_items_as_one_table(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "p0",
                        "price",
                        "P0",
                        title="加仓带：TRIGGERED",
                        status="TRIGGERED",
                        metadata={
                            "market": "H",
                            "zone_label": "加仓带",
                            "low": 400,
                            "high": 430,
                            "direction": "range",
                            "price": 410,
                        },
                    ),
                    item(
                        "p1",
                        "price",
                        "P1",
                        target_id="样例公司",
                        name="Example Co",
                        title="复核线：NEAR",
                        status="NEAR",
                        metadata={
                            "market": "US",
                            "zone_label": "复核线",
                            "low": None,
                            "high": 100,
                            "direction": "below",
                            "price": 104,
                        },
                    ),
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertIn(
            "| 优先级 | 标的 | 市场 | 监控区间 | 条件 | 现价 | 距边界 | 状态 |",
            markdown,
        )
        self.assertIn(
            "P0=区间内；P1=区间外且距边界≤5%；P2=距边界>5%",
            markdown,
        )
        self.assertIn(
            "| P0 | 腾讯控股 | H | 加仓带 | [400.00, 430.00] | 410.00 | 区间内 | TRIGGERED |",
            markdown,
        )
        self.assertIn(
            "| P1 | Example Co | US | 复核线 | ≤ 100.00 | 104.00 | 4.0% | NEAR |",
            markdown,
        )
        self.assertNotIn("### [P0] 腾讯控股", markdown)

    def test_report_has_exactly_three_business_sections(self):
        markdown = render_markdown(
            result(
                [
                    item("p", "price", "P0"),
                    item("d", "disclosures", "P1"),
                    item("o", "other", "P2"),
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertEqual(markdown.count("## 一、价格监控"), 1)
        self.assertEqual(markdown.count("## 二、财报与正式披露监控"), 1)
        self.assertEqual(markdown.count("## 三、其他监控"), 1)
        self.assertNotIn("## 分诊", markdown)
        self.assertNotIn("周检", markdown)

    def test_next_workflow_appears_only_once_per_target(self):
        markdown = render_markdown(
            result(
                [
                    item("p", "price", "P1", workflow="/earnings-review"),
                    item("d", "disclosures", "P0", workflow="/earnings-review"),
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertEqual(markdown.count("/earnings-review 腾讯"), 1)

    def test_summary_counts_actionable_changes_and_errors(self):
        run = RunResult(
            status="DEGRADED",
            items=(
                item("p", "price", "P0", notify=True),
                item("d", "disclosures", "P1", notify=True),
                item("o", "other", "P2"),
            ),
            notification_items=(),
            source_health=(SourceHealth("sec", "FAILED", "连接失败"),),
            next_state={"schema": 1},
            report_paths=None,
        )

        markdown = render_markdown(run, run_date=date(2026, 8, 25))

        self.assertIn("P0 1", markdown)
        self.assertIn("P1 1", markdown)
        self.assertIn("新增价格 1", markdown)
        self.assertIn("新增披露 1", markdown)
        self.assertIn("异常 1", markdown)

    def test_report_links_official_sources_and_keeps_research_disclaimer(self):
        markdown = render_markdown(
            result([item("d", "disclosures", "P0")]),
            run_date=date(2026, 8, 25),
        )

        self.assertIn("[正式来源]", markdown)
        self.assertIn("不构成投资建议", markdown)

    def test_writes_dated_latest_and_machine_json_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_reports(
                result([item("d", "disclosures", "P0")]),
                Path(tmp),
                run_date=date(2026, 8, 25),
            )

            self.assertEqual(paths.dated.name, "daily-monitor-20260825.md")
            self.assertEqual(paths.dated.read_text(), paths.latest.read_text())
            payload = json.loads(paths.latest_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["date"], "2026-08-25")
            self.assertEqual(payload["items"][0]["section"], "disclosures")
            self.assertFalse(list(Path(tmp).glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
