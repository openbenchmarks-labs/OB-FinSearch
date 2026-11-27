# OB-FinSearch

Open, independent benchmark of web search APIs for financial research agents: which search API helps an agent answer questions about equities, filings and crypto, including live stock closes and coin prices. The agent, prompt, search budget and grader stay fixed; only the search API changes. Search APIs measured: Brave, Exa, Firecrawl, Keenable, Nimble, Parallel, Perplexity, SERP, SpecStream, Tako, Tavily, TinyFish and You.com.

**Public dataset:** [`openbenchmarks/OB-FinSearch`](https://huggingface.co/datasets/openbenchmarks/OB-FinSearch)

Published and maintained by **[OpenBenchmarks Labs](https://openbenchmarks.com)**.

## Methodology

The benchmark evaluates search APIs across four financial task types:

- **Historical lookup**: Questions answered from one or two documents, such as a filing and its earnings call. 2 searches.
- **Multi-hop lookup**: Questions that combine figures from three or more documents into a ranking, trend or comparison. 6 searches.
- **Live lookup**: Single-query market-moment questions asking for a stock's official close or a coin's traded price window, graded against verified market answer keys (`--closes`, `--coin-key`).
- **Live filings**: Questions about company filings published the same day, asked once to each tool with 1 search and graded by the judge.

For historical and multi-hop tasks, the agent receives only the question, date, and search snippets (url, title, snippet, and publication date when the tool returns one) with page fetching disabled (`--mode search`). `judge/answer_judge.py` grades each answer against ground truth within its tolerance, and `judge/board_summary.py` computes accuracy, repeat variance, and cost.

## Tools evaluated

13 search tools (19 setups) configured in [`tools/`](tools/README.md):

`brave`, `exa`, `firecrawl`, `keenable`, `nimble`, `parallel`, `perplexity`, `serp`, `specstream`, `tako`, `tavily`, `tinyfish`, `you`

## Dataset

No question files are committed to this repository.

- **Public split:** Hosted on Hugging Face at [`openbenchmarks/OB-FinSearch`](https://huggingface.co/datasets/openbenchmarks/OB-FinSearch) and downloaded automatically by `finsearch run` (or pass `--data` for a local file or folder).
- **Held-out split:** Private evaluation items used for published leaderboards stay private to prevent contamination.

See [`data/README.md`](data/README.md) for the exact `.jsonl` file names and field schemas.

## Repository structure

- [`data/`](data/README.md): Dataset layout, Hugging Face location, and file schemas (no question files committed).
- [`harness/`](harness/README.md): `finsearch` CLI (`vendors`, `run`, `rejudge`, `summary`, `live-collect`, `live-grade`, `live-filings`), agent loop, and search adapters.
- [`tools/`](tools/README.md): One `<tool>.yaml` config per search tool (13 tools, 19 setups).
- [`judge/`](judge/README.md): Answer judge, prompt, and board summary calculations.
- [`benchmark.yaml`](benchmark.yaml): Benchmark contract, scope, and refresh cadence.
- [`AGENTS.md`](AGENTS.md): Entry guide for coding agents.

## Quick start

Run the offline test suite (no API keys required):

```sh
uv venv && uv pip install -e ".[dev]"
.venv/bin/pytest
```

To run against live APIs, copy `.env.example` to `.env`, add your keys, and inspect the `finsearch` CLI:

```sh
cp .env.example .env
.venv/bin/finsearch --help
```

## Adding or updating a tool

1. Add or edit `tools/<tool>.yaml`. For a new search API, also add `harness/adapters/<tool>.py`, register it in `harness/adapters/__init__.py`, and add its key to `.env.example`.
2. Run `.venv/bin/pytest`.
3. Open a pull request.

## Links

- [Hugging Face dataset](https://huggingface.co/datasets/openbenchmarks/OB-FinSearch)

## Related benchmarks

- [OB-Code-Websearch](https://github.com/openbenchmarks-labs/OB-Code-Websearch): Web search APIs for coding agents ([leaderboard](https://openbenchmarks.com/web-search-for-coding-agents))
- [OB-Company-News](https://github.com/openbenchmarks-labs/OB-Company-News): Company news search and news-index APIs ([leaderboard](https://openbenchmarks.com/company-news))
- [OB-Company-Search-Multi-Turn](https://github.com/openbenchmarks-labs/OB-Company-Search-Multi-Turn): Multi-hop company research agents ([leaderboard](https://openbenchmarks.com/multi-turn-company-search))
- [All OpenBenchmarks leaderboards](https://openbenchmarks.com)

## License

MIT. See [LICENSE](LICENSE).
