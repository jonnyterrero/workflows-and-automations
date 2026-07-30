#!/usr/bin/env python3
"""Collect recent release and commit activity for the repos listed in sources.json.

Default transport is GitHub's public Atom feeds on github.com. They need no
token and stay reachable in restricted-egress environments where api.github.com
is blocked. Pass --api to use the REST API instead when it is reachable; that
path returns full release bodies and richer commit metadata, and honours
GITHUB_TOKEN for rate limits.

Writes a single JSON digest that the content-engine skill reads as its factual
base. The digest records what shipped; it never interprets it.

Some sandboxes (including Claude Code on the web) block direct HTTP to
github.com and api.github.com, so neither transport works from a script there.
Run with --print-urls to emit the feed URLs and fetch them with the WebFetch
tool instead.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = SKILL_ROOT / "sources.json"
DEFAULT_OUT_DIR = SKILL_ROOT / ".cache"

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
USER_AGENT = "content-engine/1.0 (+workflows-and-automations)"
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def fetch(url: str, accept: str, timeout: int = 30) -> str:
    """GET a URL as text. Honours HTTPS_PROXY and the system CA bundle."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, "replace")


def clean_text(raw: str | None, limit: int = 1200) -> str:
    """Flatten feed HTML into a plain summary. Truncation is marked, never silent."""
    if not raw:
        return ""
    # Unescape before stripping: Atom content arrives as escaped markup, so tags
    # would otherwise survive as literal text. Unescape again for entities that
    # were nested inside those tags.
    text = WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", html.unescape(raw)))).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + " [truncated]"
    return text


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def atom_entries(xml_text: str) -> list[dict]:
    """Extract entries from a GitHub Atom feed."""
    root = ET.fromstring(xml_text)
    entries = []
    for node in root.findall("a:entry", ATOM_NS):
        link = node.find("a:link", ATOM_NS)
        author = node.find("a:author/a:name", ATOM_NS)
        entries.append(
            {
                "title": (node.findtext("a:title", default="", namespaces=ATOM_NS) or "").strip(),
                "updated": node.findtext("a:updated", default="", namespaces=ATOM_NS),
                "url": link.get("href") if link is not None else "",
                "author": (author.text or "").strip() if author is not None else "",
                "summary": clean_text(node.findtext("a:content", namespaces=ATOM_NS)),
            }
        )
    return entries


def within_window(entries: list[dict], cutoff: datetime, max_entries: int) -> list[dict]:
    kept = []
    for entry in entries:
        when = parse_dt(entry.get("updated"))
        if when is None or when >= cutoff:
            kept.append(entry)
    return kept[:max_entries]


def collect_via_atom(source: dict, cutoff: datetime, max_entries: int) -> dict:
    owner, repo = source["owner"], source["repo"]
    base = f"https://github.com/{owner}/{repo}"
    branch = source.get("default_branch", "main")
    out: dict = {"releases": [], "commits": [], "errors": []}

    for key, url in (("releases", f"{base}/releases.atom"), ("commits", f"{base}/commits/{branch}.atom")):
        try:
            out[key] = within_window(atom_entries(fetch(url, "application/atom+xml")), cutoff, max_entries)
        except (urllib.error.URLError, urllib.error.HTTPError, ET.ParseError, TimeoutError) as exc:
            out["errors"].append(f"{key}: {type(exc).__name__}: {exc}")
    return out


def collect_via_api(source: dict, cutoff: datetime, max_entries: int) -> dict:
    owner, repo = source["owner"], source["repo"]
    base = f"https://api.github.com/repos/{owner}/{repo}"
    since = cutoff.isoformat().replace("+00:00", "Z")
    out: dict = {"releases": [], "commits": [], "errors": []}

    try:
        raw = json.loads(fetch(f"{base}/releases?per_page={max_entries}", "application/vnd.github+json"))
        for rel in raw:
            when = parse_dt(rel.get("published_at") or rel.get("created_at"))
            if when is not None and when < cutoff:
                continue
            out["releases"].append(
                {
                    "title": rel.get("name") or rel.get("tag_name") or "",
                    "tag": rel.get("tag_name") or "",
                    "updated": rel.get("published_at") or rel.get("created_at") or "",
                    "url": rel.get("html_url") or "",
                    "author": (rel.get("author") or {}).get("login", ""),
                    "prerelease": bool(rel.get("prerelease")),
                    "summary": clean_text(rel.get("body"), limit=4000),
                }
            )
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        out["errors"].append(f"releases: {type(exc).__name__}: {exc}")

    try:
        raw = json.loads(
            fetch(f"{base}/commits?since={since}&per_page={max_entries}", "application/vnd.github+json")
        )
        for item in raw:
            commit = item.get("commit") or {}
            out["commits"].append(
                {
                    "title": (commit.get("message") or "").splitlines()[0],
                    "updated": (commit.get("author") or {}).get("date", ""),
                    "url": item.get("html_url") or "",
                    "author": (item.get("author") or {}).get("login")
                    or (commit.get("author") or {}).get("name", ""),
                    "summary": clean_text(commit.get("message")),
                }
            )
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as exc:
        out["errors"].append(f"commits: {type(exc).__name__}: {exc}")

    return out


def build_digest(sources: list[dict], days: int, max_entries: int, use_api: bool) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    collect = collect_via_api if use_api else collect_via_atom
    results = []

    for source in sources:
        slug = f"{source['owner']}/{source['repo']}"
        log(f"fetching {slug} ...")
        activity = collect(source, cutoff, max_entries)
        results.append(
            {
                "repo": slug,
                "label": source.get("label", slug),
                "niche": source.get("niche", ""),
                "why_it_matters": source.get("why_it_matters", ""),
                "url": f"https://github.com/{slug}",
                **activity,
            }
        )
        counts = f"{len(activity['releases'])} releases, {len(activity['commits'])} commits"
        problems = f" | errors: {'; '.join(activity['errors'])}" if activity["errors"] else ""
        log(f"  {counts}{problems}")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "transport": "rest-api" if use_api else "atom",
        "sources": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES, help="path to sources.json")
    parser.add_argument("--days", type=int, default=14, help="lookback window in days (default: 14)")
    parser.add_argument("--max-entries", type=int, default=15, help="max releases/commits per repo")
    parser.add_argument("--repo", action="append", help="only this owner/repo (repeatable)")
    parser.add_argument("--api", action="store_true", help="use api.github.com instead of Atom feeds")
    parser.add_argument("--out", type=Path, help="digest path (default: .cache/digest-<UTC date>.json)")
    parser.add_argument(
        "--print-urls",
        action="store_true",
        help="print feed URLs and exit, for fetching with WebFetch where direct HTTP is blocked",
    )
    args = parser.parse_args()

    if not args.sources.exists():
        log(f"error: sources file not found: {args.sources}")
        return 1
    config = json.loads(args.sources.read_text(encoding="utf-8"))
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    if args.repo:
        wanted = {r.lower() for r in args.repo}
        sources = [s for s in sources if f"{s['owner']}/{s['repo']}".lower() in wanted]
    if not sources:
        log("error: no sources selected")
        return 1

    if args.print_urls:
        for source in sources:
            slug = f"{source['owner']}/{source['repo']}"
            branch = source.get("default_branch", "main")
            print(f"{slug}\treleases\thttps://github.com/{slug}/releases.atom")
            print(f"{slug}\tcommits\thttps://github.com/{slug}/commits/{branch}.atom")
        return 0

    digest = build_digest(sources, args.days, args.max_entries, args.api)

    out = args.out or DEFAULT_OUT_DIR / f"digest-{datetime.now(timezone.utc):%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(digest, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {out}")

    if all(s["errors"] and not s["releases"] and not s["commits"] for s in digest["sources"]):
        log("error: every source failed; digest has no activity")
        log("hint: if these are 403s, this environment blocks github.com - rerun with --print-urls")
        log("      and fetch those URLs with WebFetch, or run this script where egress is open.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
