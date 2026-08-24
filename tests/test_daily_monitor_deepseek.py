import json
import ssl
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

from tools.daily_monitoring.context import ResearchContext
from tools.daily_monitoring.deepseek import (
    AnalysisRequest,
    DeepSeekClient,
    DeepSeekRequestError,
    InvalidModelOutput,
    parse_analysis,
)


FIXTURE = Path(__file__).parent / "fixtures" / "daily-monitor" / "deepseek-valid.json"
OFFICIAL_URL = (
    "https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0825/example.pdf"
)


def valid_payload(**overrides):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload.update(overrides)
    return payload


def request():
    return AnalysisRequest(
        target_id="腾讯",
        name="腾讯控股",
        priority_floor="P1",
        increment_title="中期业绩公告",
        increment_type="财报",
        official_urls=(OFFICIAL_URL,),
        prompt_chunks=("外部公告数据\n[PAGE 3]\n经营现金流发生变化。",),
        context=ResearchContext(
            target_id="腾讯",
            text="论文红线：自由现金流连续恶化。",
            source_paths=("reports/腾讯/thesis.md",),
        ),
    )


class SequenceTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.requests = []

    def __call__(self, payload):
        self.calls += 1
        self.requests.append(payload)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class HttpFailure(RuntimeError):
    def __init__(self, code):
        super().__init__(f"HTTP {code}")
        self.code = code


def envelope(payload):
    return {
        "choices": [
            {"message": {"content": json.dumps(payload, ensure_ascii=False)}}
        ]
    }


class DeepSeekSchemaTest(unittest.TestCase):
    def test_valid_response_is_parsed_and_citations_retained(self):
        result = parse_analysis(valid_payload(), priority_floor="P1")

        self.assertEqual(result.priority, "P0")
        self.assertEqual(result.verified_facts[0].page, 3)
        self.assertEqual(result.next_workflow, "/earnings-review")

    def test_model_cannot_downgrade_program_floor(self):
        result = parse_analysis(valid_payload(priority="P2"), priority_floor="P0")

        self.assertEqual(result.priority, "P0")

    def test_trade_action_or_unknown_field_is_rejected(self):
        payload = valid_payload(buy_action="买入")

        with self.assertRaises(InvalidModelOutput):
            parse_analysis(payload, priority_floor="P1")

    def test_fact_without_official_https_url_is_rejected(self):
        payload = valid_payload()
        payload["verified_facts"][0]["official_url"] = "https://example.com/report.pdf"

        with self.assertRaises(InvalidModelOutput):
            parse_analysis(payload, priority_floor="P1")

    def test_workflow_outside_allowlist_is_rejected(self):
        with self.assertRaises(InvalidModelOutput):
            parse_analysis(
                valid_payload(next_workflow="/investment-research"),
                priority_floor="P1",
            )


class DeepSeekClientTest(unittest.TestCase):
    @patch("tools.daily_monitoring.deepseek.urllib.request.urlopen")
    def test_production_request_uses_system_trust_context(self, urlopen):
        response = MagicMock()
        response.read.return_value = b"{}"
        urlopen.return_value.__enter__.return_value = response
        client = DeepSeekClient(api_key="test-key")

        client._post({"model": "synthetic"})

        context = urlopen.call_args.kwargs["context"]
        self.assertTrue(context.__class__.__module__.startswith("truststore"))

    @patch("tools.daily_monitoring.deepseek.urllib.request.urlopen")
    def test_certificate_failure_is_not_reported_as_timeout(self, urlopen):
        certificate_error = ssl.SSLCertVerificationError(
            1, "self-signed certificate in certificate chain"
        )
        urlopen.side_effect = urllib.error.URLError(certificate_error)
        client = DeepSeekClient(api_key="test-key")

        with self.assertRaises(DeepSeekRequestError) as caught:
            client._post({"model": "synthetic"})

        self.assertIn("TLS", caught.exception.safe_message)
        self.assertIn("证书", caught.exception.safe_message)
        self.assertFalse(caught.exception.retryable)

    def test_request_uses_json_mode_and_does_not_send_repository_paths(self):
        transport = SequenceTransport([envelope(valid_payload())])

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        sent = transport.requests[0]
        self.assertEqual(result.status, "OK")
        self.assertEqual(sent["response_format"], {"type": "json_object"})
        self.assertIn("JSON", sent["messages"][0]["content"])
        serialized = json.dumps(sent, ensure_ascii=False)
        self.assertNotIn("reports/腾讯/thesis.md", serialized)
        self.assertNotIn("test-key", serialized)

    def test_citation_must_belong_to_increment_sources(self):
        payload = valid_payload()
        payload["verified_facts"][0]["official_url"] = (
            "https://www.sec.gov/Archives/edgar/data/1/example.htm"
        )
        transport = SequenceTransport([envelope(payload), envelope(payload)])

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        self.assertEqual(result.status, "DEGRADED")
        self.assertTrue(result.needs_retry)

    def test_retries_invalid_json_once(self):
        transport = SequenceTransport(
            [
                {"choices": [{"message": {"content": "not-json"}}]},
                envelope(valid_payload()),
            ]
        )

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        self.assertEqual(result.status, "OK")
        self.assertEqual(transport.calls, 2)

    def test_second_timeout_returns_degraded_and_retryable(self):
        transport = SequenceTransport([TimeoutError(), TimeoutError()])

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        self.assertEqual(result.status, "DEGRADED")
        self.assertEqual(result.priority, "P1")
        self.assertTrue(result.needs_retry)
        self.assertTrue(result.needs_human_review)

    def test_empty_response_retries_once(self):
        transport = SequenceTransport(
            [{"choices": [{"message": {"content": ""}}]}, envelope(valid_payload())]
        )

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        self.assertEqual(result.status, "OK")
        self.assertEqual(transport.calls, 2)

    def test_rate_limit_retries_once(self):
        transport = SequenceTransport([HttpFailure(429), envelope(valid_payload())])

        result = DeepSeekClient(api_key="test-key", transport=transport).analyze(request())

        self.assertEqual(result.status, "OK")
        self.assertEqual(transport.calls, 2)

    def test_key_probe_contains_only_synthetic_data(self):
        transport = SequenceTransport([envelope(valid_payload())])
        client = DeepSeekClient(api_key="test-key", transport=transport)

        result = client.check_api_key()

        self.assertEqual(result.status, "OK")
        serialized = json.dumps(transport.requests[0], ensure_ascii=False)
        self.assertIn("synthetic", serialized.lower())
        self.assertNotIn("腾讯", serialized)


if __name__ == "__main__":
    unittest.main()
