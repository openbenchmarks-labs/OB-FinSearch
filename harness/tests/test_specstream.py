"""SpecStream request and response contracts: the data envelope, kept publication dates, fetch and stated cost."""
from harness import adapters, live_collect, search_api

# The reply shapes of POST /v1/web-search (compact=true) and POST /v1/extract: everything sits under "data".
SEARCH = {"data": {"request_id": "r1", "took_ms": 2400, "price_usd": 0.005, "sources": [
    {"url": "https://investor.example.com/q2", "title": "Example Q2 2026 results",
     "snippet": "Net revenue was $4.2 billion, up 12% year over year.", "published": "2026-07-28"},
    {"url": "https://news.example.org/a", "title": "Brief", "snippet": "No date on this page"},
    {"url": "https://investor.example.com/q2", "title": "Duplicate", "snippet": "dropped"},
    "not a source",
]}}
EXTRACT = {"data": {"request_id": "r2", "took_ms": 1010, "price_usd": 0.0008, "results": [
    {"url": "https://investor.example.com/q2", "status": "ok", "title": "Example Q2 2026 results",
     "text": "# Q2 2026\n\nNet revenue was $4.2 billion.", "published": "2026-07-28", "read_from": "live"}]}}


def _reply(payload, status=200):
    return search_api.VendorCall("ok" if status < 400 else "error", 5, {"url": "x"}, payload,
                                 None if status < 400 else f"HTTP {status}", [{"attempt": 1, "status_code": status}])


def _scripted(monkeypatch, replies):
    sent = []
    monkeypatch.setenv("SPECSTREAM_API_KEY", "k")
    monkeypatch.setattr(search_api, "send", lambda req, **_: (sent.append(req), replies.pop(0))[1])
    monkeypatch.setattr(search_api, "assert_public_url", lambda url: None)
    return sent


def test_search_keeps_published_dates_and_stated_cost(monkeypatch):
    sent = _scripted(monkeypatch, [_reply(SEARCH)])
    call = adapters.search("specstream", "Example net revenue Q2 2026", max_results=10)
    assert (sent[0].method, sent[0].url) == ("POST", "https://api.specstream.ai/v1/web-search")
    assert sent[0].body == {"q": "Example net revenue Q2 2026", "num": 10, "compact": True}
    assert sent[0].headers["Authorization"] == "Bearer k"
    assert [h["url"] for h in call.hits] == ["https://investor.example.com/q2", "https://news.example.org/a"]
    assert call.hits[0]["published"] == "2026-07-28" and "published" not in call.hits[1]
    assert call.hits[0]["snippet"] == "Net revenue was $4.2 billion, up 12% year over year."
    assert call.cost_usd == 0.005
    # The harness's own date reader misses `published`, which is why the adapter sets it.
    assert search_api.result_dates(SEARCH) == {}


def test_live_lookup_uses_the_same_request(monkeypatch):
    sent = _scripted(monkeypatch, [_reply(SEARCH)])
    assert adapters.search("specstream", "BTC price", live=True).hits[0]["published"] == "2026-07-28"
    assert sent[0].body == {"q": "BTC price", "num": 10, "compact": True}


def test_fetch_reads_extract_results(monkeypatch):
    blocked = {"data": {"price_usd": 0, "results": [{"url": "https://investor.example.com/q2", "status": "blocked"}]}}
    sent = _scripted(monkeypatch, [_reply(EXTRACT), _reply(blocked)])
    call = adapters.fetch("specstream", "https://investor.example.com/q2", objective="Q2 net revenue", max_chars=30_000)
    assert sent[0].url == "https://api.specstream.ai/v1/extract"
    assert sent[0].body == {"urls": ["https://investor.example.com/q2"], "format": "markdown",
                            "max_chars": 30_000, "query": "Q2 net revenue"}
    assert call.status == "ok" and call.cost_usd == 0.0008
    assert call.page["text"] == "# Q2 2026\n\nNet revenue was $4.2 billion."
    assert call.page["title"] == "Example Q2 2026 results"
    failed = adapters.fetch("specstream", "https://investor.example.com/q2", objective="o", max_chars=100)
    assert failed.status == "error" and "blocked" in failed.error and failed.cost_usd == 0.0


def test_error_reply_has_no_hits(monkeypatch):
    _scripted(monkeypatch, [_reply({"error": {"code": "unauthorized", "message": "no key"}}, status=401)])
    call = adapters.search("specstream", "q")
    assert (call.hits, call.cost_usd) == ([], 0.0)
    assert adapters.get("specstream").parse_hits({"error": {"code": "x"}}, 10) == []


def test_registry_pricing_and_pacing():
    adapter = adapters.get("specstream")
    assert "specstream" in adapters.BOARD_VENDORS
    assert adapters.required_env(["specstream"]) == ["SPECSTREAM_API_KEY"]
    assert (adapter.search_unit_cost_usd, adapter.fetch_unit_cost_usd, adapter.native_fetch) == (0.005, 0.0008, True)
    assert adapter.live_limit == {"rps": 8, "concurrent": 16}
    assert live_collect.live_limits()["specstream"] == {"rps": 8, "concurrent": 16}
    assert live_collect.limit_for("specstream").gap == 1 / 8
