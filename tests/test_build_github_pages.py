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
                "![图表](chart.png)\n",
                encoding="utf-8",
            )
            (report_dir / "chart.png").write_bytes(b"fake image")
            (nested_dir / "01-开篇.md").write_text("# 开篇\n", encoding="utf-8")

            builder.build_site(reports_dir, output_dir)

            index_html = (output_dir / "index.html").read_text(encoding="utf-8")
            directory_html = (output_dir / "reports" / "腾讯" / "index.html").read_text(encoding="utf-8")
            nested_directory_html = (
                output_dir / "reports" / "腾讯" / "《看懂腾讯》" / "index.html"
            ).read_text(encoding="utf-8")
            report_html_path = output_dir / "reports" / "腾讯" / "最终报告.html"
            report_html = report_html_path.read_text(encoding="utf-8")

            self.assertIn("AI Berkshire Reports", index_html)
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
            self.assertEqual((output_dir / "reports" / "腾讯" / "chart.png").read_bytes(), b"fake image")


if __name__ == "__main__":
    unittest.main()
