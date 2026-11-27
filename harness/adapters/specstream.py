"""SpecStream web search, one best passage per result with its publication date, and its extract endpoint."""

from __future__ import annotations

from typing import Any

from ..search_api import Adapter, HttpRequest, _day, dedupe, env, hit, json_headers


def _data(payload: Any) -> dict[str, Any]:
    # A successful reply is {"data": {...}}; a failed one is {"error": {...}}.
    data = payload.get("data") if isinstance(payload, dict) else None
    return data if isinstance(data, dict) else {}


class SpecStream(Adapter):
    """SpecStream search with compact=true: each result carries one snippet of the lines on its page that best match
    the query, and `published` when the page states its date. Fetch reads the page live and returns the passages
    closest to the agent's objective. Every reply states its cost in `price_usd`."""
    env_keys = ("SPECSTREAM_API_KEY",)
    native_fetch = True

    def __init__(self, extra: dict[str, Any] | None = None):
        self.extra = extra or {}

    def _headers(self):
        return json_headers(Authorization=f"Bearer {env('SPECSTREAM_API_KEY')}")

    def reported_cost(self, payload):
        cost = _data(payload).get("price_usd")
        return float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0 else None

    def search_request(self, query, max_results):
        return HttpRequest("POST", "https://api.specstream.ai/v1/web-search", self._headers(),
                           {"q": query, "num": max(1, min(max_results, 100)), **self.extra}, timeout=45)

    def parse_hits(self, payload, max_results):
        hits = []
        for r in _data(payload).get("sources") or []:
            if not isinstance(r, dict):
                continue
            h = hit(r.get("url"), r.get("title"), r.get("snippet"), {"modified": r.get("modified")})
            # The harness reads dates only under its own key names, and `published` is not one of them.
            if day := _day(r.get("published")):
                h["published"] = day
            hits.append(h)
        return dedupe(hits, max_results)

    def fetch_request(self, url, objective, max_chars):
        body: dict[str, Any] = {"urls": [url], "format": "markdown", "max_chars": int(max_chars)}
        if objective.strip():
            body["query"] = objective.strip()[:2000]
        return HttpRequest("POST", "https://api.specstream.ai/v1/extract", self._headers(), body, timeout=60)

    def parse_page(self, payload, url):
        item = (_data(payload).get("results") or [{}])[0]
        if item.get("status") != "ok":
            raise RuntimeError(f"page not read: {item.get('status') or 'no result'}")
        return item.get("text") or "", item.get("url") or url, item.get("title") or ""
