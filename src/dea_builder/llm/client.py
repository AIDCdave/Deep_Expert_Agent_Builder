"""Tiered LLM client factory — AzureChatOpenAI direct to Azure Cognitive Services."""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# ---------------------------------------------------------------------------
# Tier configuration
#
# Each tier maps to an Azure deployment name.  Deployment names are the
# names configured in the Azure portal, NOT model IDs.
# ---------------------------------------------------------------------------

TierName = Literal["worker-bee", "general", "reasoning"]

TIER_CONFIG: dict[TierName, dict] = {
    "worker-bee": {
        "deployment": "gpt-5.4-nano",
        "temperature": 0.2,
        "max_tokens": 4_096,
        "reasoning": False,
    },
    "general": {
        "deployment": "grok-4-1-fast-non-reasoning",
        "temperature": 0.4,
        "max_tokens": 16_384,
        "reasoning": False,
    },
    "reasoning": {
        "deployment": "gpt-5.5",
        "temperature": 1.0,
        "max_completion_tokens": 32_768,
        "reasoning": True,
    },
}

# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def _load_env() -> tuple[str, str, str]:
    """Load and validate Azure env vars.

    Returns (endpoint, api_key, api_version).
    """
    load_dotenv()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    if not endpoint:
        raise EnvironmentError(
            "AZURE_OPENAI_ENDPOINT not set — add it to .env or ~/.zshrc "
            "(e.g. https://dave-mot32g5b-eastus2.cognitiveservices.azure.com)"
        )
    if not api_key:
        raise EnvironmentError(
            "AZURE_OPENAI_API_KEY not set — add it to .env or ~/.zshrc"
        )
    return endpoint, api_key, api_version


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_llm(
    tier: TierName,
    *,
    callbacks: list | None = None,
    max_retries: int = 3,
) -> AzureChatOpenAI:
    """Return an AzureChatOpenAI client configured for the given cost tier.

    Parameters
    ----------
    tier : "worker-bee" | "general" | "reasoning"
        Model tier to use.
    callbacks : list, optional
        LangChain callback handlers (e.g. token tracker).
    max_retries : int
        Number of retries with exponential backoff on transient failures.
    """
    endpoint, api_key, api_version = _load_env()
    cfg = TIER_CONFIG[tier]

    kwargs: dict = {
        "azure_endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "azure_deployment": cfg["deployment"],
        "model": cfg["deployment"],  # explicit — Grok rejects model:null
        "temperature": cfg["temperature"],
        "max_retries": max_retries,
        "callbacks": callbacks or [],
        "model_kwargs": {"user": tier},  # pass tier name for token tracker
    }

    # Reasoning models require max_completion_tokens; non-reasoning use max_tokens.
    # Sending the wrong one returns HTTP 400 from Azure.
    if cfg.get("reasoning"):
        kwargs["max_completion_tokens"] = cfg["max_completion_tokens"]
    else:
        kwargs["max_tokens"] = cfg["max_tokens"]

    return AzureChatOpenAI(**kwargs)


def get_all_llms(
    *,
    callbacks: list | None = None,
) -> dict[TierName, AzureChatOpenAI]:
    """Return all three tiered clients in a dict keyed by tier name."""
    return {
        tier: get_llm(tier, callbacks=callbacks)
        for tier in TIER_CONFIG
    }
