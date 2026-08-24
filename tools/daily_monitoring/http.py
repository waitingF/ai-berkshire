"""Small retrying HTTP boundary with official-domain and redirect validation."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


OFFICIAL_HOSTS = {
    "cninfo": frozenset({"www.cninfo.com.cn", "static.cninfo.com.cn"}),
    "hkex": frozenset({"www1.hkexnews.hk", "www2.hkexnews.hk", "www.hkexnews.hk"}),
    "sec": frozenset({"www.sec.gov", "data.sec.gov"}),
}


class UnsafeUrlError(ValueError):
    """Raised before any request to a non-official URL."""


class SourceError(RuntimeError):
    """A safe, source-scoped network or response failure."""

    def __init__(self, source: str, safe_message: str, *, retryable: bool = False):
        super().__init__(f"{source}: {safe_message}")
        self.source = source
        self.safe_message = safe_message
        self.retryable = retryable


def validate_official_url(url: str, source: str) -> None:
    if source not in OFFICIAL_HOSTS:
        raise UnsafeUrlError(f"未知官方数据源: {source}")
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in OFFICIAL_HOSTS[source]:
        raise UnsafeUrlError(f"{source} 非官方地址: {url}")
    if parsed.username or parsed.password:
        raise UnsafeUrlError(f"官方地址不得包含用户信息: {url}")


class HttpClient:
    """urllib client used only at the external boundary and injectable in tests."""

    def __init__(
        self,
        *,
        edgar_identity: str | None = None,
        timeout: float = 20.0,
        retries: int = 2,
        sleep=time.sleep,
    ):
        self.edgar_identity = (edgar_identity or "").strip()
        self.timeout = timeout
        self.retries = retries
        self._sleep = sleep
        self._last_sec_request = 0.0

    def _headers(self, source: str, extra: dict[str, str] | None) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "AI-Berkshire-Daily-Monitor/1.0",
        }
        if source == "sec":
            if not self.edgar_identity:
                raise SourceError("sec", "未配置 EDGAR_IDENTITY")
            headers["User-Agent"] = self.edgar_identity
        if extra:
            headers.update(extra)
        return headers

    def _pace_sec(self, source: str) -> None:
        if source != "sec":
            return
        elapsed = time.monotonic() - self._last_sec_request
        if self._last_sec_request and elapsed < 0.5:
            self._sleep(0.5 - elapsed)
        self._last_sec_request = time.monotonic()

    def _request(
        self,
        method: str,
        url: str,
        *,
        source: str,
        params: dict[str, Any] | None = None,
        form: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_bytes: int = 25 * 1024 * 1024,
    ) -> bytes:
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}{'&' if '?' in url else '?'}{query}"
        validate_official_url(url, source)
        data = None
        request_headers = self._headers(source, headers)
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            request_headers.setdefault(
                "Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"
            )

        final_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._pace_sec(source)
            request = urllib.request.Request(
                url, data=data, headers=request_headers, method=method
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    validate_official_url(response.geturl(), source)
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_bytes:
                        raise SourceError(source, "响应超过大小上限")
                    payload = response.read(max_bytes + 1)
                    if len(payload) > max_bytes:
                        raise SourceError(source, "响应超过大小上限")
                    return payload
            except urllib.error.HTTPError as exc:
                final_error = exc
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt == self.retries:
                    raise SourceError(
                        source, f"HTTP {exc.code}", retryable=retryable
                    ) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                final_error = exc
                if attempt == self.retries:
                    raise SourceError(source, "连接失败或超时", retryable=True) from exc
            if attempt < self.retries:
                self._sleep(min(2**attempt, 4))
        raise SourceError(source, f"请求失败: {type(final_error).__name__}")

    @staticmethod
    def _decode_json(source: str, payload: bytes) -> Any:
        try:
            return json.loads(payload.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceError(source, "响应不是有效 JSON") from exc

    def get_json(
        self,
        url: str,
        *,
        source: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self._decode_json(
            source,
            self._request(
                "GET", url, source=source, params=params, headers=headers
            ),
        )

    def post_form_json(
        self,
        url: str,
        form: dict[str, Any],
        *,
        source: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self._decode_json(
            source,
            self._request(
                "POST", url, source=source, form=form, headers=headers
            ),
        )

    def get_text(
        self,
        url: str,
        *,
        source: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        payload = self._request(
            "GET", url, source=source, params=params, headers=headers
        )
        return payload.decode("utf-8", errors="replace")

    def get_bytes(self, url: str, *, source: str, max_bytes: int) -> bytes:
        return self._request(
            "GET", url, source=source, max_bytes=max_bytes
        )
