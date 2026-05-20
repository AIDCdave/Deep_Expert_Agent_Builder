"""Firecrawl URL extraction — scrape source URLs to markdown with caching."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import FirecrawlApp


@dataclass
class ScrapeResult:
    """Result of scraping a single URL."""

    url: str
    status: str  # "ok", "cached", "failed"
    markdown: str
    error: str = ""


def _url_hash(url: str) -> str:
    """Stable short hash for cache filenames."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _load_firecrawl() -> FirecrawlApp:
    """Initialize Firecrawl client from env."""
    load_dotenv()
    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        raise EnvironmentError("FIRECRAWL_API_KEY not set — add it to .env")
    return FirecrawlApp(api_key=api_key)


def scrape_urls(
    urls: list[str],
    cache_dir: Path,
    *,
    delay_s: float = 1.0,
) -> list[ScrapeResult]:
    """Scrape a list of URLs to markdown, with file-based caching.

    Parameters
    ----------
    urls : list[str]
        URLs to scrape.
    cache_dir : Path
        Directory for cached markdown files (e.g. working/url_cache/).
    delay_s : float
        Seconds to wait between API calls to respect rate limits.

    Returns
    -------
    list[ScrapeResult]
        One result per URL, in input order.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    app = _load_firecrawl()
    results: list[ScrapeResult] = []

    for i, url in enumerate(urls):
        h = _url_hash(url)
        cache_path = cache_dir / f"{h}.md"
        meta_path = cache_dir / f"{h}.url"

        # Check cache
        if cache_path.exists():
            markdown = cache_path.read_text(encoding="utf-8")
            results.append(ScrapeResult(url=url, status="cached", markdown=markdown))
            continue

        # Scrape
        try:
            response = app.scrape(url, formats=["markdown"])
            markdown = ""
            if isinstance(response, dict):
                markdown = response.get("markdown", "")
            elif hasattr(response, "markdown"):
                markdown = response.markdown or ""

            if not markdown:
                results.append(ScrapeResult(
                    url=url, status="failed", markdown="",
                    error="Empty markdown returned",
                ))
                continue

            # Write cache
            cache_path.write_text(markdown, encoding="utf-8")
            meta_path.write_text(url, encoding="utf-8")
            results.append(ScrapeResult(url=url, status="ok", markdown=markdown))

        except Exception as exc:
            results.append(ScrapeResult(
                url=url, status="failed", markdown="",
                error=str(exc)[:200],
            ))

        # Rate limit delay (skip after last URL)
        if i < len(urls) - 1:
            time.sleep(delay_s)

    return results


def load_cached_extractions(cache_dir: Path) -> dict[str, str]:
    """Load all cached URL extractions as {url: markdown}."""
    result: dict[str, str] = {}
    if not cache_dir.exists():
        return result
    for meta_path in cache_dir.glob("*.url"):
        url = meta_path.read_text(encoding="utf-8").strip()
        md_path = meta_path.with_suffix(".md")
        if md_path.exists():
            result[url] = md_path.read_text(encoding="utf-8")
    return result
