import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build-github-pages.py"


def load_builder_module():
    spec = importlib.util.spec_from_file_location("build_github_pages", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildGitHubPagesTest(unittest.TestCase):
    def test_build_site_renders_markdown_index_and_static_assets(self):
        builder = load_builder_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports_dir = root / "reports"
            output_dir = root / "site"
            report_dir = reports_dir / "腾讯"
            report_dir.mkdir(parents=True)
            nested_dir = report_dir / "《看懂腾讯》"
            nested_dir.mkdir()
            (report_dir / "最终报告.md").write_text(
                "# 腾讯最终报告\n\n"
                "## 投资结论\n\n"
                "| 指标 | 判断 |\n"
                "| --- | --- |\n"
                "| 护城河 | 强 |\n\n"
                "详见 [thesis](腾讯-thesis.md#假设) 与 [标的跟踪](../标的跟踪表.md)。\n\n"
                "外链保持 [示例](https://example.com/note.md)。\n\n"
                "![图表](chart.png)\n",
                encoding="utf-8",
            )
            (report_dir / "腾讯-thesis.md").write_text("# thesis\n\n## 假设\n\n正文。\n", encoding="utf-8")
            (report_dir / "chart.png").write_bytes(b"fake image")
            (nested_dir / "01-开篇.md").write_text("# 开篇\n", encoding="utf-8")
            (reports_dir / "重点标的看板.md").write_text(
                "# 重点标的看板\n\n"
                "跳转 [标的跟踪表.md](标的跟踪表.md) 与 [thesis](腾讯/腾讯-thesis.md)。\n",
                encoding="utf-8",
            )
            (reports_dir / "标的跟踪表.md").write_text(
                "# 标的跟踪表\n\n"
                "| ID | 标的 | 建议日 | 来源 | 动作 | 锚定价 |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| 20260516-ADP | ADP | 2026-05-16 | [ADP/最终报告.md](ADP/最终报告.md) | 买入 | $209 |\n"
                "| 20260516-Uber | Uber | 2026-05-16 | [Uber/最终报告.md](Uber/最终报告.md) | 观望 | $75 |\n",
                encoding="utf-8",
            )
            (reports_dir / "portfolio-latest.md").write_text("# 组合最新报告\n\n组合。\n", encoding="utf-8")
            weekly_dir = reports_dir / "weekly-check"
            weekly_dir.mkdir()
            (weekly_dir / "weekly-check-20260731.md").write_text(
                "# 周检待办清单\n\n本周待办。\n",
                encoding="utf-8",
            )
            (weekly_dir / "weekly-check-latest.md").write_text(
                "# 最新周检\n\n"
                "**当前报告：** [2026-07-31 周检待办清单](../weekly-check/weekly-check-20260731.md)\n\n"
                "## 历史周检\n\n"
                "| 数据截止日 | 报告 |\n"
                "| --- | --- |\n"
                "| 2026-07-31 | [周检待办清单](../weekly-check/weekly-check-20260731.md) |\n",
                encoding="utf-8",
            )
            scan_dir = reports_dir / "trigger-scan"
            scan_dir.mkdir()
            (scan_dir / "trigger-scan-latest.md").write_text(
                "# 标的触发监控日报\n\n"
                "## 一、已触发价位区间\n\n"
                "| 标的 | 现价 |\n"
                "| --- | --- |\n"
                "| 腾讯 | 457.00 |\n",
                encoding="utf-8",
            )

            builder.build_site(reports_dir, output_dir)

            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            directory_html = (output_dir / "reports" / "腾讯" / "index.html").read_text(encoding="utf-8")
            nested_directory_html = (
                output_dir / "reports" / "腾讯" / "《看懂腾讯》" / "index.html"
            ).read_text(encoding="utf-8")
            report_html_path = output_dir / "reports" / "腾讯" / "最终报告.html"
            report_html = report_html_path.read_text(encoding="utf-8")
            board_html = (output_dir / "reports" / "重点标的看板.html").read_text(encoding="utf-8")
            ledger_html = (output_dir / "reports" / "标的跟踪表.html").read_text(encoding="utf-8")
            weekly_latest_html = (
                output_dir / "reports" / "weekly-check" / "weekly-check-latest.html"
            ).read_text(encoding="utf-8")
            composed_html = (
                output_dir / "reports" / "监控与周检" / "index.html"
            ).read_text(encoding="utf-8")
            site_js = (output_dir / "assets" / "site.js").read_text(encoding="utf-8")
            site_css = (output_dir / "assets" / "site.css").read_text(encoding="utf-8")

            self.assertEqual(builder.rewrite_markdown_href("腾讯/腾讯-thesis.md"), "腾讯/腾讯-thesis.html")
            self.assertEqual(
                builder.rewrite_markdown_href("../标的跟踪表.md#命中率"),
                "../标的跟踪表.html#命中率",
            )
            self.assertEqual(
                builder.rewrite_markdown_href("https://example.com/note.md"),
                "https://example.com/note.md",
            )
            self.assertEqual(builder.rewrite_markdown_href("#假设"), "#假设")
            self.assertIn('href="腾讯-thesis.html#假设"', report_html)
            self.assertIn('href="../标的跟踪表.html"', report_html)
            self.assertIn('href="https://example.com/note.md"', report_html)
            self.assertNotIn('href="腾讯-thesis.md', report_html)
            self.assertIn('href="标的跟踪表.html"', board_html)
            self.assertIn('href="腾讯/腾讯-thesis.html"', board_html)
            self.assertNotIn('href="标的跟踪表.md"', board_html)
            self.assertIn("<th>动作</th>", ledger_html)
            self.assertIn(">买入</td>", ledger_html)
            self.assertIn(">观望</td>", ledger_html)
            self.assertIn("initActionColumnFilter", site_js)
            self.assertIn(".action-filter", site_css)

            self.assertIn("AI Berkshire Reports", index_html)
            self.assertIn("常用入口", index_html)
            self.assertIn("重点标的看板", index_html)
            self.assertIn("标的跟踪表", index_html)
            self.assertIn("监控与周检", index_html)
            self.assertIn("组合最新报告", index_html)
            self.assertIn("看板", index_html)
            self.assertIn("标的跟踪", index_html)
            self.assertIn("周检", index_html)
            self.assertIn("组合", index_html)
            self.assertIn('class="pinned-home"', index_html)
            self.assertIn('aria-current="page"', index_html)
            self.assertIn("reports/%E9%87%8D%E7%82%B9%E6%A0%87%E7%9A%84%E7%9C%8B%E6%9D%BF.html", index_html)
            self.assertIn("reports/%E6%A0%87%E7%9A%84%E8%B7%9F%E8%B8%AA%E8%A1%A8.html", index_html)
            self.assertIn("reports/%E7%9B%91%E6%8E%A7%E4%B8%8E%E5%91%A8%E6%A3%80/index.html", index_html)
            self.assertIn("reports/portfolio-latest.html", index_html)
            self.assertNotIn("reports/weekly-check/weekly-check-latest.html", index_html)
            self.assertNotIn("reports/trigger-scan/trigger-scan-latest.html", index_html)
            self.assertNotIn('class="pinned-home"', directory_html)
            self.assertIn("看板", report_html)
            self.assertIn("标的跟踪", report_html)
            self.assertIn("周检", report_html)
            self.assertIn("组合", report_html)
            self.assertIn('aria-current="page"', weekly_latest_html)
            self.assertIn('href="../weekly-check/weekly-check-20260731.html"', weekly_latest_html)
            # 组合页：两个 latest 源内容被嵌入（扫描源 + 周检快照正文），标题降级
            self.assertIn("每日触发监控（自动扫描）", composed_html)
            self.assertIn("每周研究待办分诊（人工周检）", composed_html)
            self.assertIn("457.00", composed_html)
            self.assertIn("本周待办", composed_html)
            self.assertIn("历史周检", composed_html)
            self.assertIn("<th>数据截止日</th>", composed_html)
            self.assertIn('href="../weekly-check/weekly-check-20260731.html"', composed_html)
            self.assertIn("reports/%E7%9B%91%E6%8E%A7%E4%B8%8E%E5%91%A8%E6%A3%80/index.html", composed_html)
            # fixture 含 portfolio-latest.md → 组合页导航保留「组合」入口
            self.assertIn("reports/portfolio-latest.html", composed_html)
            self.assertIn("腾讯", index_html)
            self.assertIn("reports/%E8%85%BE%E8%AE%AF/index.html", index_html)
            self.assertNotIn("腾讯/最终报告.md", index_html)
            self.assertNotIn("reports/%E8%85%BE%E8%AE%AF/%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.html", index_html)
            self.assertIn("腾讯", directory_html)
            self.assertIn("最终报告.md", directory_html)
            self.assertIn("%E6%9C%80%E7%BB%88%E6%8A%A5%E5%91%8A.html", directory_html)
            self.assertIn("《看懂腾讯》/", directory_html)
            self.assertIn("%E3%80%8A%E7%9C%8B%E6%87%82%E8%85%BE%E8%AE%AF%E3%80%8B/index.html", directory_html)
            self.assertNotIn("《看懂腾讯》/01-开篇.md", directory_html)
            self.assertIn("01-开篇.md", nested_directory_html)
            self.assertIn("<h1", report_html)
            self.assertIn("腾讯最终报告", report_html)
            self.assertIn("<table>", report_html)
            self.assertIn('src="chart.png"', report_html)
            self.assertIn('data-back-to-top', index_html)
            self.assertIn('data-back-to-top', report_html)
            self.assertIn('.back-to-top', site_css)
            self.assertIn('initBackToTop', site_js)
            self.assertEqual((output_dir / "reports" / "腾讯" / "chart.png").read_bytes(), b"fake image")

    def test_nav_hides_missing_pinned_files_on_home_and_composed(self):
        """置顶入口文件缺失时（如组合报告仅存本地），首页与组合页导航都应隐藏对应链接。"""
        builder = load_builder_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports_dir = root / "reports"
            output_dir = root / "site"
            weekly_dir = reports_dir / "weekly-check"
            weekly_dir.mkdir(parents=True)
            (weekly_dir / "weekly-check-20260101.md").write_text(
                "# 周检待办清单\n\n本周待办。\n",
                encoding="utf-8",
            )
            (weekly_dir / "weekly-check-latest.md").write_text(
                "# 最新周检\n\n"
                "**当前报告：** [2026-01-01 周检待办清单](../weekly-check/weekly-check-20260101.md)\n",
                encoding="utf-8",
            )
            scan_dir = reports_dir / "trigger-scan"
            scan_dir.mkdir()
            (scan_dir / "trigger-scan-latest.md").write_text(
                "# 标的触发监控日报\n\n无。\n",
                encoding="utf-8",
            )
            # 刻意不创建 portfolio-latest.md 与看板/台账，验证导航过滤

            builder.build_site(reports_dir, output_dir)

            home_html = (output_dir / "index.html").read_text(encoding="utf-8")
            composed_html = (
                output_dir / "reports" / "监控与周检" / "index.html"
            ).read_text(encoding="utf-8")
            for page_html in (home_html, composed_html):
                self.assertNotIn("reports/portfolio-latest.html", page_html)
                self.assertNotIn("reports/%E9%87%8D%E7%82%B9%E6%A0%87%E7%9A%84%E7%9C%8B%E6%9D%BF.html", page_html)
                self.assertNotIn("reports/%E6%A0%87%E7%9A%84%E8%B7%9F%E8%B8%AA%E8%A1%A8.html", page_html)
            # 组合入口（构建生成）与「研究库」始终显示
            self.assertIn("reports/%E7%9B%91%E6%8E%A7%E4%B8%8E%E5%91%A8%E6%A3%80/index.html", home_html)
            self.assertIn("reports/%E7%9B%91%E6%8E%A7%E4%B8%8E%E5%91%A8%E6%A3%80/index.html", composed_html)


if __name__ == "__main__":
    unittest.main()
