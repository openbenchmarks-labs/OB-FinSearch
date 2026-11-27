# adapters

One file per search API. Each turns a query into that API's request and its reply into a list of results. Setups and prices come from `tools/<tool>.yaml`.

- `__init__.py` — Lists every tool, reads its setups from `tools/<tool>.yaml`, and sends searches and fetches to the right adapter.
- `exa.py` — Exa search and page contents. Live lookup asks for a fresh crawl.
- `parallel.py` — Parallel search and page extract.
- `you.py` — You.com search and page contents. The `core` setup also returns You.com's answer box.
- `tavily.py` — Tavily search and page extract.
- `nimble.py` — Nimble search and page extract.
- `firecrawl.py` — Firecrawl search and page scrape.
- `tako.py` — Tako search and page contents. Live lookup also asks for Tako's price cards.
- `tinyfish.py` — TinyFish search and page fetch.
- `keenable.py` — Keenable search (pro and realtime modes).
- `perplexity.py` — Perplexity search. No page fetch.
- `brave.py` — Brave search. No page fetch.
- `serp.py` — Google results through a RapidAPI endpoint. No page fetch.
- `specstream.py`: SpecStream search with one best passage per result and its publication date, and its extract endpoint as the page fetch.
