import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "reports_index.py"


def load_reports_index_module():
    spec = importlib.util.spec_from_file_location("reports_index", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReportsIndexTest(unittest.TestCase):
    def test_collapsible_groups_enable_markdown_rendering(self):
        reports_index = load_reports_index_module()
        items = [{
            "title": "腾讯最终报告",
            "path": "reports/腾讯/最终报告.md",
            "bucket": "公司",
            "group": "腾讯",
            "series": "",
            "type": "研究",
            "date": "2026-09-19",
        }]

        index = reports_index.render(items, {})

        self.assertIn('<details markdown="1">', index)
        self.assertIn('[腾讯最终报告](腾讯/最终报告.md)', index)


if __name__ == "__main__":
    unittest.main()
