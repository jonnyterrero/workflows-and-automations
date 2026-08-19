"""Research tools: arXiv, Semantic Scholar, web fetch, report writer."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from agents import function_tool

from ..common.config import settings
from ..common.logging import get_logger

log = get_logger(__name__)

REPORT_DIR = Path("/tmp/agent_trio_reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


@function_tool
def search_arxiv(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Search arXiv for recent papers."""
    import arxiv

    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    out = []
    for r in search.results():
        out.append(
            {
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "summary": r.summary[:600],
                "published": r.published.isoformat() if r.published else None,
                "url": r.entry_id,
                "pdf": r.pdf_url,
                "categories": r.categories,
            }
        )
    return out


@function_tool
async def search_semantic_scholar(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Search Semantic Scholar for peer-reviewed work with citation counts."""
    headers = {"x-api-key": settings.semantic_scholar_key} if settings.semantic_scholar_key else {}
    async with httpx.AsyncClient(timeout=20, headers=headers) as c:
        r = await c.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,abstract,citationCount,venue,openAccessPdf,url",
            },
        )
        r.raise_for_status()
        return r.json().get("data", [])


@function_tool
async def fetch_url(url: str, max_chars: int = 8000) -> dict[str, Any]:
    """Fetch a URL and return cleaned text content. Use for primary sources / docs."""
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=25, follow_redirects=True,
                                 headers={"User-Agent": "agent-trio/0.1"}) as c:
        r = await c.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        return {"url": url, "title": (soup.title.string if soup.title else None), "text": text[:max_chars]}


@function_tool
def save_report(title: str, markdown: str) -> dict[str, Any]:
    """Persist a finished research report to disk and return its path."""
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)[:80].strip().replace(" ", "_")
    fname = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe or 'report'}.md"
    path = REPORT_DIR / fname
    path.write_text(markdown)
    return {"path": str(path), "bytes": len(markdown.encode()), "title": title}
