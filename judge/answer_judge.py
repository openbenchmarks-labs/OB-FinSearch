"""The grader: Claude Opus 5.5 compares the agent's answer with the reference answer and tolerance."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

JUDGE_MODEL = "claude-opus-5-5"
JUDGE_EFFORT = "medium"
JUDGE_PROMPT = (Path(__file__).parent / "answer_judge_prompt.txt").read_text().rstrip("\n")


def judge_client() -> Any:
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set (see .env.example)")
    return anthropic.Anthropic(max_retries=4)


def parse_judge_payload(text: str) -> dict[str, Any]:
    """The first JSON object that carries a correct/incorrect verdict.

    A reply can mention other braces before that object. Taking the first `{`
    through the last `}` makes a real verdict unreadable.
    """
    decoder = json.JSONDecoder()
    body = text or ""
    index = 0
    while True:
        start = body.find("{", index)
        if start < 0:
            return {}
        try:
            payload, end = decoder.raw_decode(body, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(payload, dict) and "correct" in payload:
            return payload
        index = end


def judge(client: Any, q: dict[str, Any], candidate: str) -> dict[str, Any]:
    prompt = JUDGE_PROMPT.format(
        question=q["question"], answer=q["answer"], tolerance=q.get("tolerance", ""),
        candidate=candidate or "(no answer)",
    )
    t0 = time.perf_counter()
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=8000,
        output_config={"effort": JUDGE_EFFORT},
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    base = {"judge_model": response.model, "judge_ms": latency_ms,
            "judge_input_tokens": response.usage.input_tokens, "judge_output_tokens": response.usage.output_tokens}
    if response.stop_reason == "refusal":
        return base | {"correct": False, "reason": "judge refused", "judge_error": "refusal"}
    text = "".join(b.text for b in response.content if b.type == "text")
    verdict = parse_judge_payload(text)
    if "correct" not in verdict:
        return base | {"correct": False, "reason": f"unparseable judge output: {text[:200]}", "judge_error": "parse"}
    return base | {"correct": bool(verdict["correct"]), "reason": str(verdict.get("reason", ""))}
