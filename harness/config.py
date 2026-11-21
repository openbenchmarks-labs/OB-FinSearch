"""The fixed parts of the benchmark: models, search budgets, prices and defaults.

The reference board is produced with exactly these settings. Change them and your numbers are no longer
comparable with the board.
"""

from __future__ import annotations

import os
from datetime import date

from judge.answer_judge import JUDGE_MODEL

# Hugging Face dataset repo holding the public sample. Override with --data.
DATASET_REPO = os.environ.get("FINSEARCH_DATASET_REPO", "openbenchmarks/OB-FinSearch")
CONFIGS = {"historical-lookup": "single", "multi-hop-lookup": "multi"}   # dataset config -> search class
LOOKUPS = {"historical": "single", "multi_hop": "multi"}                 # row `lookup` -> search class

# One budget per search class.
# mode "search" (the board): searches only. mode "search_fetch": adds a page-fetch budget.
# The env overrides let a run name a different model; costs are always priced as the reference model.
REFERENCE_MODELS = {"single": ("gpt-6-luna", "high"), "multi": ("gpt-6-luna", "high")}
CLASS_MODELS = {
    "single": (os.environ.get("FINSEARCH_SINGLE_MODEL", "gpt-6-luna"), "high"),
    "multi": (os.environ.get("FINSEARCH_MULTI_MODEL", "gpt-6-luna"), "high"),
}
BUDGETS = {
    "search": {"single": ("single_s2", 2, 0), "multi": ("multi_s6", 6, 0)},
    "search_fetch": {"single": ("single_s2_f2", 2, 2), "multi": ("multi_s6_f10", 6, 10)},
}
MAX_RESULTS = 10            # results asked of the search API per call
FETCH_MAX_CHARS = 30_000    # page text handed to the agent per fetch
SAFETY_MAX_TURNS = 24       # turns are not budgeted; this only stops a runaway loop

# Date the agent is told is "today": the day the run starts. A resumed run keeps its original date.
DEFAULT_TODAY = date.today().isoformat()
DEFAULT_REPEATS = 3

# USD per million tokens: (uncached input, cached input, output). Used for the cost columns only.
PRICES = {
    "gpt-5.6-sol": (4.0, 0.2, 20.0),
    "gpt-5.6-luna": (0.2, 0.02, 1.2),
    "gpt-6-luna": (0.10, 0.01, 0.50),
    JUDGE_MODEL: (4.0, 4.0, 20.0),
}


def class_setup(mode: str) -> dict[str, dict]:
    return {cls: {"config": cfg, "searches": s, "fetches": f,
                  "model": CLASS_MODELS[cls][0], "effort": CLASS_MODELS[cls][1],
                  "price_model": REFERENCE_MODELS[cls][0]}
            for cls, (cfg, s, f) in BUDGETS[mode].items()}


def llm_cost(model: str, input_tokens: int, cached: int, output_tokens: int) -> float:
    unc, cac, out = PRICES.get(model, (0.0, 0.0, 0.0))
    return ((input_tokens - cached) * unc + cached * cac + output_tokens * out) / 1e6
