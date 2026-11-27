"""The tool registry: one adapter class per tool, with its setups, prices and pacing read from tools/<tool>.yaml.

To benchmark an API that isn't here, subclass `Adapter` (see harness/search_api.py), add tools/<tool>.yaml and one
line to ADAPTERS. Or put the adapter in your own module and pass `--vendor-module your.module`: any module that
calls `register(...)` on import works.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import yaml

from ..search_api import Adapter, VendorCall
from .brave import Brave
from .exa import Exa
from .firecrawl import Firecrawl
from .keenable import Keenable
from .nimble import Nimble
from .parallel import Parallel
from .perplexity import Perplexity
from .serp import Serp
from .specstream import SpecStream
from .tako import Tako
from .tavily import Tavily
from .tinyfish import TinyFish
from .you import You

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"

ADAPTERS: dict[str, type[Adapter]] = {
    "exa": Exa, "parallel": Parallel, "you": You, "tavily": Tavily, "nimble": Nimble, "firecrawl": Firecrawl,
    "tako": Tako, "tinyfish": TinyFish, "perplexity": Perplexity, "brave": Brave, "serp": Serp, "keenable": Keenable,
    "specstream": SpecStream,
}

REGISTRY: dict[str, Adapter] = {}


def register(adapter: Adapter) -> Adapter:
    if not adapter.key:
        raise ValueError("adapter needs a key")
    REGISTRY[adapter.key] = adapter
    return adapter


def load_setups(tool: str, cls: type[Adapter]) -> list[Adapter]:
    """One adapter per setup in tools/<tool>.yaml."""
    spec = yaml.safe_load((TOOLS_DIR / f"{tool}.yaml").read_text())
    setups = []
    for key, setup in spec["setups"].items():
        adapter = cls(**setup.get("options", {}))
        pricing = setup.get("pricing", {})
        adapter.key, adapter.provider = key, setup["name"]
        adapter.search_unit_cost_usd = pricing.get("list_usd")
        adapter.fetch_unit_cost_usd = pricing.get("fetch_usd")
        adapter.live_limit = spec.get("live_limit")
        setups.append(adapter)
    return setups


for _tool, _cls in ADAPTERS.items():
    for _adapter in load_setups(_tool, _cls):
        register(_adapter)

BOARD_VENDORS = tuple(REGISTRY)


def load_module(path: str) -> None:
    """Import a module that registers extra adapters."""
    importlib.import_module(path)


def get(key: str) -> Adapter:
    if key not in REGISTRY:
        raise KeyError(f"unknown vendor {key!r}; known: {', '.join(sorted(REGISTRY))}")
    return REGISTRY[key]


def search(key: str, query: str, *, max_results: int = 10, live: bool = False,
           objective: str | None = None) -> VendorCall:
    """live=True only from live lookup: adapters may switch on freshness options there (see Adapter).
    `objective` goes only to objective_search adapters. Flags are passed only when set, so an adapter that
    overrides search() without them still works."""
    adapter = get(key)
    if live:
        return adapter.search(query, max_results=max_results, live=True)
    if adapter.objective_search and objective:
        return adapter.search(query, max_results=max_results, objective=objective)
    return adapter.search(query, max_results=max_results)


def fetch(key: str, url: str, *, objective: str, max_chars: int) -> VendorCall:
    return get(key).fetch(url, objective=objective, max_chars=max_chars)


def required_env(keys: list[str]) -> list[str]:
    return sorted({k for v in keys for k in get(v).env_keys})
