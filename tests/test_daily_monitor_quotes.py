import json
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools.daily_monitoring.config import validate_price_zones
from tools.daily_monitoring.runner import production_services


def chart(symbol="CHG.L", currency="GBp", price=568.0):
    return {"chart": {"error": None, "result": [{"meta": {
        "symbol": symbol, "currency": currency, "regularMarketPrice": price,
        "regularMarketTime": 1795797312, "shortName": "Example",
    }}]}}


def response(payload):
    return SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode())


class InternationalQuotesTest(unittest.TestCase):
    def test_tencent_quote_times_are_normalized_to_shanghai(self):
        raw = {"usAAPL": {"price": 358.54, "time": "2026-11-27 13:00:01"},
               "hk00700": {"price": 352, "time": "2026/11/27 16:09:04"},
               "sh600519": {"price": 1472.36, "time": "20261127161454"}}
        with patch("tools.trigger_scanner._curl_qq", return_value=raw):
            quotes = production_services().quote_provider(list(raw))

        self.assertEqual(quotes["usAAPL"]["time"], "2026-11-28 02:00:01")
        self.assertEqual(quotes["hk00700"]["time"], "2026-11-27 16:09:04")
        self.assertEqual(quotes["sh600519"]["time"], "2026-11-27 16:14:54")
        self.assertEqual(quotes["usAAPL"]["currency"], "USD")

    def test_local_markets_keep_native_currency_and_quote_time(self):
        cases = [
            ("BNP.PA", "EUR"), ("CHG.L", "GBp"), ("EKTA-B.ST", "SEK"),
            ("PRX.AS", "EUR"), ("RHM.DE", "EUR"), ("WTC.AX", "AUD"),
            ("2344.TW", "TWD"), ("2408.TW", "TWD"),
        ]
        for symbol, currency in cases:
            with self.subTest(symbol=symbol), \
                    patch("tools.trigger_scanner._curl_qq", return_value={}), \
                    patch("subprocess.run", return_value=response(chart(symbol, currency))):
                code = "yahoo:" + symbol
                quotes = production_services().quote_provider([code])

                self.assertIn(code, quotes)
                self.assertEqual(quotes[code]["price"], 568)
                self.assertEqual(quotes[code]["currency"], currency)
                self.assertEqual(quotes[code]["source"], "Yahoo Finance")
                self.assertEqual(quotes[code]["time"], "2026-11-28 00:35:12")

    def test_yahoo_failure_keeps_tencent_prices(self):
        with patch("tools.trigger_scanner._curl_qq", return_value={"hk00700": {"price": 600}}), \
                patch("subprocess.run", side_effect=subprocess.TimeoutExpired("curl", 15)):
            quotes = production_services().quote_provider(["hk00700", "yahoo:BNP.PA"])

        self.assertEqual(quotes["hk00700"]["price"], 600)
        self.assertNotIn("yahoo:BNP.PA", quotes)

    def test_second_yahoo_host_recovers_from_http_failure(self):
        failed = SimpleNamespace(returncode=22, stdout=b"")
        with patch("tools.trigger_scanner._curl_qq", return_value={}), \
                patch("subprocess.run", side_effect=[failed, response(chart())]):
            quotes = production_services().quote_provider(["yahoo:CHG.L"])

        self.assertEqual(quotes["yahoo:CHG.L"]["price"], 568)

    def test_rejects_wrong_security_currency_and_invalid_prices(self):
        invalid = [chart(symbol="OTHER.L"), chart(currency="GBP"),
                   chart(price=None), chart(price=True), chart(price=0),
                   chart(price=float("nan")), chart(price=float("inf")),
                   {"chart": {"error": {"code": "Not Found"}, "result": None}}]
        no_time = chart()
        del no_time["chart"]["result"][0]["meta"]["regularMarketTime"]
        invalid.append(no_time)
        for payload in invalid:
            with self.subTest(payload=payload), \
                    patch("tools.trigger_scanner._curl_qq", return_value={}), \
                    patch("subprocess.run", return_value=response(payload)):
                quotes = production_services().quote_provider(["yahoo:CHG.L"])

                self.assertNotIn("yahoo:CHG.L", quotes)

    def test_rejects_yahoo_symbol_for_wrong_market_in_configuration(self):
        target = {"id": "Example", "codes": {"UK": "yahoo:BNP.PA"}, "zones": []}

        self.assertTrue(validate_price_zones(target))
        target["codes"] = {"UK": "yahoo:CHG.L"}
        self.assertEqual(validate_price_zones(target), [])


if __name__ == "__main__":
    unittest.main()
