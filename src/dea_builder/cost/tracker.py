"""Token tracking callback handler for LLM calls."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


@dataclass
class TokenRecord:
    """One LLM call's token usage."""

    model: str
    tier: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_s: float
    node: str = ""


# $/1M tokens — adjust as pricing changes
COST_PER_1M = {
    "gpt-5.5": {"prompt": 2.00, "completion": 10.00},
    "grok-4-1-fast-non-reasoning": {"prompt": 0.60, "completion": 2.40},
    "gpt-5.4-nano": {"prompt": 0.10, "completion": 0.40},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost for a single LLM call."""
    rates = COST_PER_1M.get(model, {"prompt": 2.0, "completion": 10.0})
    return (prompt_tokens * rates["prompt"] + completion_tokens * rates["completion"]) / 1_000_000


class TokenTracker(BaseCallbackHandler):
    """Accumulates per-call token usage across an entire run.

    Usage::

        tracker = TokenTracker()
        llm = get_llm("general", callbacks=[tracker])
        # ... run graph ...
        tracker.summary()   # totals by tier
        tracker.records     # raw list of TokenRecord
    """

    def __init__(self) -> None:
        super().__init__()
        self.records: list[TokenRecord] = []
        self._starts: dict[UUID, tuple[float, str]] = {}
        self._current_node: str = ""

    # -- context helpers --------------------------------------------------- #

    def set_current_node(self, node_name: str) -> None:
        """Set the current graph node name for attribution."""
        self._current_node = node_name

    # -- deployment → tier reverse map ------------------------------------- #

    _DEPLOYMENT_TO_TIER: dict[str, str] = {
        "gpt-5.4-nano": "worker-bee",
        "grok-4-1-fast-non-reasoning": "general",
        "gpt-5.5": "reasoning",
        "grok-4-20-reasoning": "reasoning",
    }

    def _resolve_tier(self, inv_params: dict[str, Any]) -> tuple[str, str]:
        """Extract (model_name, tier) from invocation params."""
        model = inv_params.get("model_name", "") or inv_params.get("model", "")
        # tier passed via model_kwargs.user in get_llm()
        tier = inv_params.get("user", "")
        if not tier:
            tier = self._DEPLOYMENT_TO_TIER.get(model, "unknown")
        return model, tier

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        inv = kwargs.get("invocation_params", {})
        model, tier = self._resolve_tier(inv)
        self._starts[run_id] = (time.monotonic(), model, tier)

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        inv = kwargs.get("invocation_params", {})
        model, tier = self._resolve_tier(inv)
        self._starts[run_id] = (time.monotonic(), model, tier)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        start_time, model, tier = self._starts.pop(
            run_id, (time.monotonic(), "", "unknown")
        )
        latency = time.monotonic() - start_time

        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("token_usage", {})

        self.records.append(
            TokenRecord(
                model=model,
                tier=tier,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_s=round(latency, 3),
                node=self._current_node,
            )
        )

    # -- reporting --------------------------------------------------------- #

    def summary(self) -> dict[str, Any]:
        """Return totals grouped by tier + grand total."""
        by_tier: dict[str, dict[str, int]] = {}
        for rec in self.records:
            t = by_tier.setdefault(rec.tier, {"prompt": 0, "completion": 0, "total": 0, "calls": 0})
            t["prompt"] += rec.prompt_tokens
            t["completion"] += rec.completion_tokens
            t["total"] += rec.total_tokens
            t["calls"] += 1

        grand = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
        for t in by_tier.values():
            for k in grand:
                grand[k] += t[k]

        return {"by_tier": by_tier, "grand_total": grand}

    def to_dicts(self) -> list[dict[str, Any]]:
        """Serialize all records for JSON trace output."""
        return [
            {
                "model": r.model,
                "tier": r.tier,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "latency_s": r.latency_s,
                "node": r.node,
            }
            for r in self.records
        ]
