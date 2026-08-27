import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.daily_monitoring import config
from tools.daily_monitoring import state as state_module
from tools import trigger_scanner


class DisclosureSourceConfigTest(unittest.TestCase):
    def test_infers_official_sources_from_market_codes(self):
        target = {
            "id": "腾讯",
            "codes": {"A": "sh600519", "H": "hk00700", "US": "usTCEHY"},
        }

        sources = config.infer_sources(target)

        self.assertEqual(
            sources,
            {
                "cninfo": {"stock_code": "600519", "exchange": "sh"},
                "hkex": {"stock_code": "00700"},
                "sec": {"ticker": "TCEHY"},
            },
        )

    def test_explicit_source_configuration_overrides_inference(self):
        target = {
            "id": "腾讯",
            "codes": {"H": "hk00700", "US": "usTCEHY"},
            "disclosure_sources": {
                "hkex": {"stock_code": "700", "language": "zh"},
                "sec": {"cik": "0001293451", "forms": ["6-K", "20-F"]},
            },
        }

        sources = config.infer_sources(target)

        self.assertEqual(
            sources["hkex"], {"stock_code": "00700", "language": "zh"}
        )
        self.assertEqual(
            sources["sec"],
            {
                "ticker": "TCEHY",
                "cik": "0001293451",
                "forms": ["6-K", "20-F"],
            },
        )

    def test_explicitly_disabled_source_removes_market_inference(self):
        target = {
            "id": "纳指100",
            "codes": {"US": "usQQQM"},
            "disclosure_sources": {"sec": {"enabled": False}},
        }

        sources = config.infer_sources(target)

        self.assertNotIn("sec", sources)

    def test_rejects_unknown_disclosure_source(self):
        target = {
            "id": "腾讯",
            "codes": {"H": "hk00700"},
            "disclosure_sources": {"browser_search": {"query": "腾讯"}},
        }

        with self.assertRaisesRegex(config.ConfigError, "browser_search"):
            config.infer_sources(target)


class TriggerConfigTest(unittest.TestCase):
    def _write_targets(self, targets):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "triggers.json"
        path.write_text(
            json.dumps({"targets": targets}, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def test_accepts_one_downside_zone_plus_non_overlapping_above_warning(self):
        path = self._write_targets(
            [
                {
                    "id": "沃尔玛",
                    "codes": {"US": "usWMT"},
                    "zones": [
                        {
                            "label": "研究性分批评估带",
                            "market": "US",
                            "dir": "range",
                            "low": 80,
                            "high": 90,
                        },
                        {
                            "label": "估值警戒线",
                            "market": "US",
                            "dir": "above",
                            "low": 120,
                        },
                    ],
                }
            ]
        )

        targets = config.load_targets(path)

        self.assertEqual(
            [zone["dir"] for zone in targets[0]["zones"]], ["range", "above"]
        )

    def test_rejects_below_and_range_for_same_target_market(self):
        path = self._write_targets(
            [
                {
                    "id": "样例公司",
                    "codes": {"A": "sh600000"},
                    "zones": [
                        {
                            "label": "观察带",
                            "market": "A",
                            "dir": "range",
                            "low": 10,
                            "high": 12,
                        },
                        {
                            "label": "安全边际线",
                            "market": "A",
                            "dir": "below",
                            "high": 8,
                        },
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(config.ConfigError, "below/range 二选一"):
            config.load_targets(path)

    def test_rejects_multiple_above_warnings_for_same_target_market(self):
        path = self._write_targets(
            [
                {
                    "id": "样例公司",
                    "codes": {"US": "usTEST"},
                    "zones": [
                        {
                            "label": "警戒线一",
                            "market": "US",
                            "dir": "above",
                            "low": 120,
                        },
                        {
                            "label": "警戒线二",
                            "market": "US",
                            "dir": "above",
                            "low": 140,
                        },
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(config.ConfigError, "只能配置一个 above"):
            config.load_targets(path)

    def test_rejects_overlapping_downside_zone_and_above_warning(self):
        path = self._write_targets(
            [
                {
                    "id": "样例公司",
                    "codes": {"US": "usTEST"},
                    "zones": [
                        {
                            "label": "研究带",
                            "market": "US",
                            "dir": "range",
                            "low": 80,
                            "high": 120,
                        },
                        {
                            "label": "警戒线",
                            "market": "US",
                            "dir": "above",
                            "low": 110,
                        },
                    ],
                }
            ]
        )

        with self.assertRaisesRegex(config.ConfigError, "必须高于下行评估条件"):
            config.load_targets(path)

    def test_rejects_above_without_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triggers.json"
            path.write_text(
                json.dumps(
                    {
                        "targets": [
                            {
                                "id": "样例公司",
                                "codes": {"US": "usTEST"},
                                "zones": [
                                    {
                                        "label": "不追高线",
                                        "market": "US",
                                        "dir": "above",
                                    }
                                ],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(config.ConfigError, "dir=above 但无 low"):
                config.load_targets(path)

    def test_legacy_scanner_uses_same_zone_combination_contract(self):
        path = self._write_targets(
            [
                {
                    "id": "样例公司",
                    "name": "Example",
                    "group": "台账",
                    "codes": {"US": "usTEST"},
                    "zones": [
                        {
                            "label": "研究带",
                            "market": "US",
                            "dir": "range",
                            "low": 80,
                            "high": 90,
                        },
                        {
                            "label": "更低触发线",
                            "market": "US",
                            "dir": "below",
                            "high": 70,
                        },
                    ],
                }
            ]
        )
        previous = trigger_scanner.TRIGGERS_FILE
        trigger_scanner.TRIGGERS_FILE = str(path)
        self.addCleanup(setattr, trigger_scanner, "TRIGGERS_FILE", previous)

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = trigger_scanner.cmd_check()

        self.assertEqual(exit_code, 1)
        self.assertIn("below/range 二选一", output.getvalue())


class MonitoringStateTest(unittest.TestCase):
    def test_missing_state_starts_with_independent_mutable_schema_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"

            first = state_module.load_state(missing)
            second = state_module.load_state(missing)
            first["documents"]["sec:x"] = {"status": "DONE"}

            self.assertEqual(first["schema"], 1)
            self.assertEqual(second["documents"], {})
            self.assertEqual(second["price_states"], {})
            self.assertEqual(second["event_states"], {})

    def test_atomic_save_replaces_complete_json_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            payload = {
                "schema": 1,
                "documents": {"sec:x": {"status": "DONE"}},
            }

            state_module.save_state_atomic(path, payload)

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["documents"]["sec:x"][
                    "status"
                ],
                "DONE",
            )
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_rejects_unsupported_state_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text('{"schema": 99}', encoding="utf-8")

            with self.assertRaisesRegex(state_module.StateError, "99"):
                state_module.load_state(path)


if __name__ == "__main__":
    unittest.main()
