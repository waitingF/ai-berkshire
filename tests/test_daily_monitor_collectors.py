import json
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.daily_monitoring import Disclosure
from tools.daily_monitoring.collectors import akshare, cninfo, hkex, sec
from tools.daily_monitoring.disclosures import deduplicate
from tools.daily_monitoring.http import (
    HttpClient,
    SourceError,
    UnsafeUrlError,
    validate_official_url,
)


FIXTURES = Path(__file__).parent / "fixtures" / "daily-monitor"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FixtureHttp:
    def __init__(self):
        self.calls = []

    def get_json(self, url, *, source, params=None, headers=None):
        self.calls.append(("GET", url, source, params))
        if url.endswith("company_tickers.json"):
            return load_fixture("sec-company-tickers.json")
        if "submissions/CIK" in url:
            return load_fixture("sec-submissions.json")
        if "activestock" in url:
            return load_fixture("hkex-active-stocks.json")
        if "titleSearchServlet" in url:
            return load_fixture("hkex-response.json")
        raise AssertionError(f"unexpected GET {url}")

    def post_form_json(self, url, form, *, source, headers=None):
        self.calls.append(("POST", url, source, form))
        if "topSearch" in url:
            return load_fixture("cninfo-org-search.json")
        if "hisAnnouncement/query" in url:
            return load_fixture("cninfo-response.json")
        raise AssertionError(f"unexpected POST {url}")


class OfficialUrlTest(unittest.TestCase):
    def test_rejects_non_official_download_host(self):
        with self.assertRaises(UnsafeUrlError):
            validate_official_url("https://example.com/file.pdf", source="hkex")

    def test_accepts_sec_archive_url(self):
        validate_official_url(
            "https://www.sec.gov/Archives/edgar/data/1293451/0001/report.htm",
            source="sec",
        )

    def test_rejects_http_even_on_official_host(self):
        with self.assertRaises(UnsafeUrlError):
            validate_official_url("http://www.cninfo.com.cn/file.pdf", source="cninfo")

    @patch("tools.daily_monitoring.http.urllib.request.urlopen")
    def test_official_request_uses_system_trust_context(self, urlopen):
        response = MagicMock()
        response.geturl.return_value = "https://data.sec.gov/submissions/CIK1.json"
        response.headers.get.return_value = None
        response.read.return_value = b"{}"
        urlopen.return_value.__enter__.return_value = response

        HttpClient(edgar_identity="Test User test@example.com").get_json(
            "https://data.sec.gov/submissions/CIK1.json",
            source="sec",
        )

        context = urlopen.call_args.kwargs["context"]
        self.assertTrue(context.__class__.__module__.startswith("truststore"))

    def test_sec_identity_requires_ascii_name_and_email(self):
        client = HttpClient(edgar_identity="测试用户 test@example.com")

        with self.assertRaises(SourceError) as caught:
            client.get_json(
                "https://data.sec.gov/submissions/CIK1.json",
                source="sec",
            )

        self.assertIn("ASCII", caught.exception.safe_message)
        self.assertIn("英文姓名", caught.exception.safe_message)


class SecCollectorTest(unittest.TestCase):
    def test_filters_configured_forms_and_builds_archive_url(self):
        http = FixtureHttp()

        documents = sec.collect(
            "拼多多",
            {"ticker": "PDD", "forms": ["6-K", "20-F"]},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            http=http,
        )

        self.assertEqual([doc.document_type for doc in documents], ["6-K"])
        self.assertEqual(documents[0].document_id, "0001293451-26-000123")
        self.assertEqual(documents[0].published_at, "2026-08-24T12:30:00.000Z")
        self.assertEqual(
            documents[0].official_url,
            "https://www.sec.gov/Archives/edgar/data/1293451/000129345126000123/pdd-20260824.htm",
        )

    def test_explicit_cik_skips_ticker_lookup(self):
        http = FixtureHttp()

        sec.collect(
            "拼多多",
            {"cik": "0001293451", "forms": ["6-K"]},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            http=http,
        )

        self.assertFalse(any(call[1].endswith("company_tickers.json") for call in http.calls))

    def test_missing_optional_recent_columns_do_not_break_later_rows(self):
        class MinimalSecHttp:
            def get_json(self, url, *, source, params=None, headers=None):
                return {
                    "filings": {
                        "recent": {
                            "accessionNumber": ["0000000001-26-000001", "0000000001-26-000002"],
                            "filingDate": ["2026-08-23", "2026-08-24"],
                            "form": ["10-Q", "10-Q"],
                        }
                    }
                }

        documents = sec.collect(
            "样例",
            {"cik": "1", "forms": ["10-Q"]},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            http=MinimalSecHttp(),
        )

        self.assertEqual(len(documents), 2)
        self.assertTrue(documents[1].official_url.endswith("-index.html"))


class CninfoCollectorTest(unittest.TestCase):
    def test_resolves_orgid_and_normalizes_announcement(self):
        http = FixtureHttp()

        documents = cninfo.collect(
            "贵州茅台",
            {"stock_code": "600519", "exchange": "sh"},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            http=http,
        )

        self.assertEqual(documents[0].document_id, "1224500001")
        self.assertEqual(documents[0].document_type, "财报")
        self.assertEqual(
            documents[0].download_url,
            "https://static.cninfo.com.cn/finalpage/2026-08-24/1224500001.PDF",
        )
        org_search = next(call for call in http.calls if "topSearch" in call[1])
        self.assertEqual(org_search[0], "POST")
        query = next(call for call in http.calls if "hisAnnouncement/query" in call[1])
        self.assertEqual(query[3]["stock"], "600519,gssh0600519")


class HkexCollectorTest(unittest.TestCase):
    def test_resolves_stockid_and_keeps_official_metadata(self):
        http = FixtureHttp()

        documents = hkex.collect(
            "腾讯",
            {"stock_code": "00700", "language": "en"},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            http=http,
        )

        self.assertEqual(documents[0].document_id, "2026082400123")
        self.assertEqual(documents[0].document_type, "财报")
        self.assertEqual(documents[0].published_at, "2026-08-24T17:15:00+08:00")
        self.assertEqual(
            documents[0].official_url,
            "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0824/2026082400123.pdf",
        )
        search = next(call for call in http.calls if "titleSearchServlet" in call[1])
        self.assertEqual(search[3]["stockId"], "7609")


class AkshareFallbackTest(unittest.TestCase):
    def test_official_link_is_verified_but_other_link_remains_clue(self):
        rows = load_fixture("akshare-fallback.json")

        clues = akshare.collect_fallback(
            "贵州茅台",
            {"stock_code": "600519", "exchange": "sh"},
            since=date(2026, 8, 20),
            until=date(2026, 8, 24),
            provider=lambda **kwargs: rows,
        )

        self.assertEqual([clue.verified for clue in clues], [True, False])
        self.assertEqual([clue.needs_human_review for clue in clues], [False, True])


def disclosure(source, document_id, title="2026 Interim Results", sha256=None, url=None):
    official_url = url or f"https://www.sec.gov/Archives/{source}/{document_id}.htm"
    return Disclosure(
        target_id="腾讯",
        source=source,
        document_id=document_id,
        title=title,
        published_at="2026-08-24T10:00:00Z",
        document_type="财报",
        official_url=official_url,
        download_url=official_url,
        sha256=sha256,
    )


class DisclosureDeduplicationTest(unittest.TestCase):
    def test_deduplicates_same_official_id(self):
        self.assertEqual(len(deduplicate([disclosure("sec", "x"), disclosure("sec", "x")])), 1)

    def test_merges_same_hash_but_preserves_both_official_urls(self):
        hk_url = "https://www1.hkexnews.hk/listedco/a.pdf"
        cninfo_url = "https://static.cninfo.com.cn/finalpage/a.PDF"

        merged = deduplicate(
            [
                disclosure("hkex", "hk-1", sha256="abc", url=hk_url),
                disclosure("cninfo", "cn-1", sha256="abc", url=cninfo_url),
            ]
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(set(merged[0].source_urls), {hk_url, cninfo_url})

    def test_does_not_merge_ambiguous_titles(self):
        first = disclosure("sec", "x", title="Results")
        second = replace(
            disclosure("hkex", "y", title="Results update"),
            official_url="https://www1.hkexnews.hk/listedco/y.pdf",
            source_urls=("https://www1.hkexnews.hk/listedco/y.pdf",),
        )

        self.assertEqual(len(deduplicate([first, second])), 2)


if __name__ == "__main__":
    unittest.main()
