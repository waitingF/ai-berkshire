import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.daily_monitoring.models import MonitorItem, RunResult, SourceHealth, VerifiedFact
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
    verified_facts=(),
    source_urls=None,
    limitations=(),
    needs_human_review=False,
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
        verified_facts=verified_facts,
        source_urls=source_urls if source_urls is not None else ((
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/example.pdf",
        ) if section == "disclosures" else ()),
        next_workflow=workflow,
        limitations=limitations,
        needs_human_review=needs_human_review,
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
    def test_target_names_use_primary_research_link_in_every_section(self):
        research_link = "../腾讯/腾讯-earnings-2026Q2.md"
        markdown = render_markdown(
            result(
                [
                    item(
                        "price-link",
                        "price",
                        "P0",
                        metadata={
                            "market": "H",
                            "zone_label": "加仓带",
                            "low": 400,
                            "high": 430,
                            "direction": "range",
                            "price": 410,
                            "research_link": research_link,
                        },
                    ),
                    item(
                        "summary-link",
                        "disclosures",
                        "P0",
                        metadata={
                            "kind": "disclosure_summary",
                            "market": "H",
                            "announcement_count": 1,
                            "latest_time": "2026-08-26T18:36:00+08:00",
                            "updates": [],
                            "research_link": research_link,
                        },
                    ),
                    item(
                        "disclosure-link",
                        "disclosures",
                        "P1",
                        metadata={"research_link": research_link},
                    ),
                    item(
                        "other-link",
                        "other",
                        "P1",
                        metadata={"research_link": research_link},
                    ),
                ]
            ),
            run_date=date(2026, 8, 26),
        )

        self.assertEqual(
            markdown.count(f"[腾讯控股]({research_link})"),
            4,
        )

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
                    item(
                        "p2",
                        "price",
                        "P2",
                        target_id="远端样例",
                        name="Far Away Co",
                        title="等待带：FAR",
                        status="FAR",
                        metadata={
                            "market": "US",
                            "zone_label": "等待带",
                            "low": 80,
                            "high": 100,
                            "direction": "range",
                            "price": 120,
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
            "P0=到达建仓或研究复核条件；P1=距对应边界≤5%；P2 与已越警戒线事项不展示",
            markdown,
        )
        self.assertNotIn("above", markdown)
        self.assertIn(
            "| P0 | 腾讯控股 | H | 加仓带 | [400.00, 430.00] | 410.00 | 区间内 | TRIGGERED |",
            markdown,
        )
        self.assertIn(
            "| P1 | Example Co | US | 复核线 | ≤ 100.00 | 104.00 | 4.0% | NEAR |",
            markdown,
        )
        self.assertNotIn("### [P0] 腾讯控股", markdown)
        self.assertNotIn("Far Away Co", markdown)

    def test_above_warning_is_hidden_from_price_section_and_summary(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "warning",
                        "price",
                        "P0",
                        target_id="沃尔玛",
                        name="Walmart",
                        title="估值警戒线：WARN",
                        status="WARN",
                        notify=True,
                        metadata={
                            "market": "US",
                            "zone_label": "估值警戒线",
                            "low": 120,
                            "high": None,
                            "direction": "above",
                            "price": 122,
                        },
                    )
                ]
            ),
            run_date=date(2026, 8, 27),
        )

        self.assertNotIn("Walmart", markdown)
        self.assertNotIn("| WARN |", markdown)
        self.assertIn("P0 0 · P1 0 · 新增价格 0", markdown)
        self.assertIn("无 P0/P1 建仓或关注价格事项", markdown)

    def test_disclosure_section_renders_table_and_preserves_details(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "d",
                        "disclosures",
                        "P0",
                        title="2026Q2业绩公告",
                        status="VERIFIED",
                        workflow="/earnings-review",
                        verified_facts=(
                            VerifiedFact(
                                fact="收入同比增长 12%",
                                official_url="https://www1.hkexnews.hk/example.pdf",
                                page=3,
                                confidence="高",
                            ),
                        ),
                        limitations=("现金流附注待复核",),
                        needs_human_review=True,
                        metadata={
                            "published_at": "2026-08-25",
                            "note": "核验利润率",
                        },
                    )
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertIn(
            "| 优先级 | 标的 | 披露/事项 | 日期 | 状态 | 为什么现在 | 核验事实/正式来源 | 下一流程 | 备注 |",
            markdown,
        )
        self.assertIn("收入同比增长 12%（高，第 3 页；[正式来源]", markdown)
        self.assertIn("`/earnings-review 腾讯`", markdown)
        self.assertIn("待人工确认", markdown)
        self.assertIn("现金流附注待复核", markdown)
        self.assertIn("核验利润率", markdown)
        self.assertNotIn("### [P0] 腾讯控股｜2026Q2业绩公告", markdown)

    def test_disclosure_summary_renders_compact_linked_updates(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "summary",
                        "disclosures",
                        "P0",
                        title="2 项公告更新",
                        status="REVIEW",
                        source_urls=(
                            "https://www1.hkexnews.hk/results.pdf",
                            "https://www1.hkexnews.hk/circulation.pdf",
                        ),
                        metadata={
                            "kind": "disclosure_summary",
                            "market": "H",
                            "announcement_count": 2,
                            "latest_time": "2026-08-26T18:36:00+08:00",
                            "updates": [
                                {
                                    "summary": "2026年中期业绩",
                                    "source_urls": [
                                        "https://www1.hkexnews.hk/results.pdf"
                                    ],
                                },
                                {
                                    "summary": "H股全流通申请",
                                    "source_urls": [
                                        "https://www1.hkexnews.hk/circulation.pdf"
                                    ],
                                },
                            ],
                        },
                    )
                ]
            ),
            run_date=date(2026, 8, 26),
        )

        self.assertIn(
            "| 优先级 | 标的 | 市场 | 更新摘要 | 公告数 | 最新时间 | 状态 |",
            markdown,
        )
        self.assertIn("[2026年中期业绩](https://www1.hkexnews.hk/results.pdf)", markdown)
        self.assertIn("[H股全流通申请](https://www1.hkexnews.hk/circulation.pdf)", markdown)
        self.assertIn("| 2 | 18:36 | REVIEW |", markdown)
        self.assertNotIn("出现了需要研究核验的增量", markdown)

    def test_other_section_renders_table(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "o",
                        "other",
                        "P1",
                        title="论文复检",
                        status="UPCOMING_7D",
                        workflow="/thesis-tracker",
                        needs_human_review=True,
                        metadata={"date": "2026-08-30", "note": "复核竞争格局"},
                    )
                ]
            ),
            run_date=date(2026, 8, 25),
        )

        self.assertIn(
            "| 优先级 | 标的/数据源 | 事项 | 日期 | 状态 | 为什么现在 | 下一流程 | 备注 |",
            markdown,
        )
        self.assertIn("| P1 | 腾讯控股 | 论文复检 | 2026-08-30 | UPCOMING_7D |", markdown)
        self.assertIn("`/thesis-tracker 腾讯`", markdown)
        self.assertIn("复核竞争格局", markdown)
        self.assertNotIn("### [P1] 腾讯控股｜论文复检", markdown)

    def test_other_section_omits_resolved_items(self):
        markdown = render_markdown(
            result(
                [
                    item(
                        "resolved-gap",
                        "other",
                        "P2",
                        target_id="Keyence",
                        name="Keyence",
                        title="本地研究链接失效：已解除",
                        status="RESOLVED",
                        resolved=True,
                        notify=True,
                    )
                ]
            ),
            run_date=date(2026, 8, 31),
        )

        self.assertNotIn("Keyence", markdown)
        self.assertNotIn("已解除", markdown)
        self.assertIn("## 三、其他监控\n\n无新增或持续事项。", markdown)

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
