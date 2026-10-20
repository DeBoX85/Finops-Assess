"""HTTP client: read-only allowlist, retry with Retry-After, ARG quota headers.
Hard rule 1 (CLAUDE.md): no write calls. GET is allowed. POST is allowed only to endpoints
that are queries and do not change state, listed in ALLOWED_POST. Add an entry only with a decision record.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .errors import BlockedRequest

ALLOWED_HOSTS = {"management.azure.com"}  # public cloud only; sovereign clouds out of scope this round
ALLOWED_POST = [
    # Azure Resource Graph query (read-only). Source: Learn, Resource Graph REST quickstart (read 2026-10-17)
    re.compile(r"^/providers/Microsoft\.ResourceGraph/resources$", re.I),
]
# ADR 0006 stage 1 (owner approved 2026-10-20): Cost Management Query and Forecast are POSTs that only read. Scope is a subscription, resource group
# or management group; billing scopes wait for the test-tenant facts. api-version must be a dated, non-preview value. Stage 2 (Cost Details report,
# blob download) is NOT allowed yet.
_SCOPE = r"(?:/subscriptions/[^/]+(?:/resourceGroups/[^/]+)?|/providers/Microsoft\.Management/managementGroups/[^/]+)"
ALLOWED_POST_COST = [re.compile(rf"^{_SCOPE}/providers/Microsoft\.CostManagement/(?:query|forecast)$", re.I)]
_API_VERSION = re.compile(r"(?:^|&)api-version=\d{4}-\d{2}-\d{2}(?:&|$)")
_ID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


@dataclass
class Response:
    status: int
    headers: dict
    body: dict | None


class UrllibTransport:
    def send(self, method, url, headers, body):
        data = json.dumps(body).encode() if body is not None else None
        if not url.startswith(("https://", "http://127.0.0.1")):  # 127.0.0.1 only for local tests
            raise BlockedRequest(f"scheme/host not allowed: {url[:30]}")
        req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310  scheme checked above
        try:
            with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310  scheme checked above
                raw = r.read()
                return Response(r.status, {k.lower(): v for k, v in r.headers.items()}, json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                b = json.loads(raw) if raw else None
            except ValueError:
                b = {"raw": raw[:500].decode("utf-8", "replace")}
            return Response(e.code, {k.lower(): v for k, v in e.headers.items()}, b)


@dataclass
class CallRecord:
    method: str
    endpoint: str  # IDs redacted
    status: int
    retries: int
    rows: int | None = None


def redact(path: str) -> str:
    return _ID.sub("{id}", path)


@dataclass
class Client:
    token_provider: object
    transport: object = field(default_factory=UrllibTransport)
    sleep: object = time.sleep
    max_retries: int = 5
    calls: list = field(default_factory=list)

    def _check(self, method, url):
        u = urlparse(url)
        if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
            raise BlockedRequest(f"host not allowed: {u.hostname}")
        if method == "GET":
            return
        if method == "POST" and any(p.match(u.path) for p in ALLOWED_POST):
            return
        if method == "POST" and any(p.match(u.path) for p in ALLOWED_POST_COST) and _API_VERSION.search(u.query):
            return
        raise BlockedRequest(f"{method} {redact(u.path)} is not on the read-only allowlist")

    def request(self, method, url, body=None) -> Response:
        method = method.upper()
        self._check(method, url)
        retries = 0
        while True:
            headers = {"Authorization": f"Bearer {self.token_provider.token()}", "Content-Type": "application/json"}
            r = self.transport.send(method, url, headers, body)
            wait = None
            if r.status in (429, 503):
                wait = _retry_after(r.headers)
            elif r.status == 200 and r.headers.get("x-ms-user-quota-remaining") == "0":
                # ARG quota exhausted: pause before the next call (headers per Learn throttling guidance)
                self.sleep(_hms(r.headers.get("x-ms-user-quota-resets-after")) or 1)
            if wait is None or retries >= self.max_retries:
                self.calls.append(CallRecord(method, redact(urlparse(url).path), r.status, retries))
                return r
            retries += 1
            self.sleep(wait)


def _retry_after(h):
    try:
        return max(1.0, float(h.get("retry-after", "")))
    except ValueError:
        return 2.0


def _hms(v):
    try:
        h, m, s = v.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except (ValueError, AttributeError):
        return None
