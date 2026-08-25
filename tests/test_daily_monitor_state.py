import json
import tempfile
import unittest
from pathlib import Path

from tools.daily_monitoring import config
from tools.daily_monitoring import state as state_module


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
    def test_rejects_multiple_price_zones_for_same_target_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triggers.json"
            path.write_text(
                json.dumps(
                    {
                        "targets": [
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
                                        "label": "安全边际带",
                                        "market": "A",
                                        "dir": "below",
                                        "high": 8,
                                    },
                                ],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(config.ConfigError, "同一市场 A 配置了多个价格区间"):
                config.load_targets(path)


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
