"""Azure AI Content Safety — Prompt Shields scan.

Scans human-authored content at the pipeline trust boundary (Module 1)
before it enters the trusted pipeline. Uses the standalone Azure AI
Content Safety REST API, NOT the per-deployment content filter.

See: https://learn.microsoft.com/azure/ai-services/content-safety/quickstart-jailbreak
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv
from rich.console import Console

console = Console()

# Prompt Shields userPrompt field limit (characters).
_CHUNK_LIMIT = 10_000

# Key Vault configuration — mirrors the AIDC fetch-secrets.sh pattern.
_KEY_VAULT_NAME = "kv-aidc-eus2"
_KEY_VAULT_SECRET_NAME = "content-safety-key"


@dataclass
class PromptShieldResult:
    """Result of a Prompt Shields scan."""

    attack_detected: bool
    chunks_scanned: int
    flagged_chunks: list[int] = field(default_factory=list)
    raw_responses: list[dict] = field(default_factory=list)


class PromptInjectionError(Exception):
    """Raised when the Prompt Shields scan detects a prompt-injection risk."""

    def __init__(self, result: PromptShieldResult, document_path: str = ""):
        self.result = result
        self.document_path = document_path
        super().__init__(
            f"Context document flagged as prompt-injection risk by Azure Content Safety "
            f"Prompt Shields. {len(result.flagged_chunks)} of {result.chunks_scanned} "
            f"chunk(s) flagged. Document: {document_path}"
        )


def _fetch_key_from_vault(vault_name: str, secret_name: str) -> str:
    """Fetch a secret from Azure Key Vault using the developer's az CLI session.

    Mirrors the AIDC fetch-secrets.sh pattern:
        az keyvault secret show --vault-name <vault> --name <secret> --query "value" -o tsv
    """
    try:
        result = subprocess.run(
            [
                "az", "keyvault", "secret", "show",
                "--vault-name", vault_name,
                "--name", secret_name,
                "--query", "value",
                "-o", "tsv",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise EnvironmentError(
            "Azure CLI (az) not found. Install it or add it to PATH. "
            "The pipeline fetches CONTENT_SAFETY_KEY from Key Vault at startup."
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise EnvironmentError(
            f"Failed to fetch secret '{secret_name}' from Key Vault '{vault_name}'. "
            f"Ensure you are logged in (az login) and have access. Error: {stderr}"
        )

    value = result.stdout.strip()
    if not value:
        raise EnvironmentError(
            f"Secret '{secret_name}' in Key Vault '{vault_name}' is empty."
        )
    return value


def _load_content_safety_env() -> tuple[str, str]:
    """Load Content Safety endpoint from env and key from Key Vault.

    Returns (endpoint, key).

    - CONTENT_SAFETY_ENDPOINT: from env var (fail-loud if missing).
    - CONTENT_SAFETY_KEY: fetched from Azure Key Vault kv-aidc-eus2,
      secret name 'content-safety-key'. Mirrors the AIDC fetch-secrets.sh
      pattern using the developer's az CLI session.
    """
    load_dotenv()

    endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT", "")
    if not endpoint:
        raise EnvironmentError(
            "CONTENT_SAFETY_ENDPOINT must be set. This identifies the Azure AI "
            "Content Safety resource used for Module 1 Prompt Shields scanning. "
            "See .planning/issues/azure_trusted_deployment_spec.md Item 3 for setup."
        )

    key = _fetch_key_from_vault(_KEY_VAULT_NAME, _KEY_VAULT_SECRET_NAME)

    return endpoint.rstrip("/"), key


def _scan_chunk(endpoint: str, key: str, text: str) -> dict:
    """Call the Prompt Shields API for a single text chunk."""
    resp = requests.post(
        f"{endpoint}/contentsafety/text:shieldPrompt?api-version=2024-09-01",
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/json",
        },
        json={"userPrompt": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def scan_for_prompt_injection(text: str) -> PromptShieldResult:
    """Scan text for prompt-injection risk using Azure Prompt Shields.

    Chunks the text at the API's character limit and scans each chunk.
    If ANY chunk is flagged, the overall result is attack_detected=True.
    """
    endpoint, key = _load_content_safety_env()

    # Chunk the text for scan only — downstream pipeline gets the full document
    chunks: list[str] = []
    for i in range(0, len(text), _CHUNK_LIMIT):
        chunks.append(text[i : i + _CHUNK_LIMIT])

    console.print(f"  Prompt Shields: scanning {len(chunks)} chunk(s)...")

    flagged: list[int] = []
    raw_responses: list[dict] = []

    for idx, chunk in enumerate(chunks):
        result = _scan_chunk(endpoint, key, chunk)
        raw_responses.append(result)

        analysis = result.get("userPromptAnalysis", {})
        if analysis.get("attackDetected", False):
            flagged.append(idx)
            console.print(f"  [red]Chunk {idx + 1}/{len(chunks)}: attack detected[/red]")
        else:
            console.print(f"  [green]Chunk {idx + 1}/{len(chunks)}: clean[/green]")

    return PromptShieldResult(
        attack_detected=len(flagged) > 0,
        chunks_scanned=len(chunks),
        flagged_chunks=flagged,
        raw_responses=raw_responses,
    )
