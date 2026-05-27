"""Exa semantic search — find experts and source URLs by domain query."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from exa_py import Exa


@dataclass
class ExaResult:
    """One search result from Exa."""

    title: str
    url: str
    score: float
    published_date: str = ""
    author: str = ""
    highlights: list[str] = field(default_factory=list)
    text: str = ""


def _load_exa() -> Exa:
    """Initialize Exa client from env."""
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key:
        raise EnvironmentError("EXA_API_KEY not set — add it to .env")
    return Exa(api_key=api_key)


def search(
    query: str,
    *,
    num_results: int = 20,
    use_autoprompt: bool = True,
    category: str | None = None,
    include_text: bool = True,
    text_max_chars: int = 1000,
) -> list[ExaResult]:
    """Run a semantic search on Exa.

    Parameters
    ----------
    query : str
        Natural language search query.
    num_results : int
        Number of results to return.
    use_autoprompt : bool
        Let Exa optimize the query internally.
    category : str | None
        Optional category filter (e.g. "blog post", "research paper").
    include_text : bool
        Whether to include text snippets in results.
    text_max_chars : int
        Max characters of text content per result.

    Returns
    -------
    list[ExaResult]
        Search results sorted by relevance.
    """
    client = _load_exa()

    kwargs: dict[str, Any] = {
        "query": query,
        "num_results": num_results,
        "use_autoprompt": use_autoprompt,
    }
    if category:
        kwargs["category"] = category

    if include_text:
        kwargs["text"] = {"max_characters": text_max_chars}
    kwargs["highlights"] = True

    response = client.search_and_contents(**kwargs)

    results: list[ExaResult] = []
    for r in response.results:
        results.append(ExaResult(
            title=r.title or "",
            url=r.url or "",
            score=r.score if hasattr(r, "score") else 0.0,
            published_date=r.published_date or "" if hasattr(r, "published_date") else "",
            author=r.author or "" if hasattr(r, "author") else "",
            highlights=r.highlights if hasattr(r, "highlights") and r.highlights else [],
            text=r.text or "" if hasattr(r, "text") else "",
        ))

    return results


def search_multiple(
    queries: list[str],
    *,
    num_results: int = 10,
    **kwargs: Any,
) -> dict[str, list[ExaResult]]:
    """Run multiple Exa searches. Returns {query: results}."""
    all_results: dict[str, list[ExaResult]] = {}
    for q in queries:
        all_results[q] = search(q, num_results=num_results, **kwargs)
    return all_results


def results_to_markdown(results: list[ExaResult]) -> str:
    """Format Exa results as markdown for LLM consumption."""
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        lines.append(f"### Result {i}: {r.title}")
        lines.append(f"**URL:** {r.url}")
        if r.author:
            lines.append(f"**Author:** {r.author}")
        if r.published_date:
            lines.append(f"**Published:** {r.published_date}")
        if r.score:
            lines.append(f"**Relevance:** {r.score:.3f}")
        if r.highlights:
            lines.append("**Highlights:**")
            for h in r.highlights[:3]:
                lines.append(f"> {h}")
        if r.text:
            lines.append(f"\n{r.text[:500]}")
        lines.append("")
    return "\n".join(lines)


def results_to_json_serializable(results: list[ExaResult]) -> list[dict]:
    """Convert results to JSON-serializable dicts for trace output."""
    return [
        {
            "title": r.title,
            "url": r.url,
            "score": r.score,
            "published_date": r.published_date,
            "author": r.author,
            "highlights": r.highlights[:3],
        }
        for r in results
    ]
