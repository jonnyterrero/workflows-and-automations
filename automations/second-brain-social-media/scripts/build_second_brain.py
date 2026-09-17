"""
build_second_brain.py

Normalizes Instagram data exports into a clean "Second Brain" dataset AND
produces ChatGPT-style zipped upload batches.

- Reads the raw exports directly off disk (raw exports are never modified).
- Flattens Instagram's messy label_values / string_list_data / string_map_data
  container shapes into one canonical record schema.
- Accounts are kept SEPARATE and tagged by source account (cross-linkable via
  the `account` field), never silently merged.
- Excludes media binaries (mp4/jpg/...) and direct messages (messages/) from the
  brain, but records everything that was skipped in a manifest.

Output layout (OUT_DIR):
  second-brain-instagram/
    build_second_brain.py            <- this tool
    README.md
    <account>/
      normalized/<type>.jsonl        <- one record per line, full fidelity
      normalized/_all.jsonl          <- every record for the account
      markdown/<type>.md             <- Obsidian-friendly tables (capped)
      manifest.json                  <- counts, files scanned/skipped, sizes
    _upload_batches/
      <account>/<account>-data-NN.zip
      <account>/file_inventory.csv
      <account>/skipped_media.csv
      batch_manifest.json

Python 3.10+  (stdlib only)
"""
from __future__ import annotations

import csv
import fnmatch
import json
import re
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from paths import data_root

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DOWNLOADS = Path(r"C:\Users\JTerr\Downloads")
OUT_DIR = data_root()  # local working folder; never the public git repo

# account name -> candidate export roots (first existing per name is used).
# OneDrive relocates these folders, so we list every place they've lived.
_SEARCH_BASES = [DOWNLOADS, DOWNLOADS / "Social media clone", OUT_DIR, OUT_DIR.parent]

def _resolve(*names: str) -> list[Path]:
    found: list[Path] = []
    for name in names:
        for base in _SEARCH_BASES:
            p = base / name
            if p.exists() and p not in found:
                found.append(p)
                break
    return found

ACCOUNTS: dict[str, list[Path]] = {
    "jxnnys.wrld": _resolve(
        "instagram-jxnnys.wrld-2026-09-08-3By1qyrF",
        "instagram-jxnnys.wrld-2026-09-08-dOZmNfXV",   # media-only split part
        "instagram-jxnnys.wrld-full context",          # renamed media export
    ),
    "juicedupjonnyy": _resolve(
        "instagram-juicedupjonnyy-2026-09-08-VMY6eL6j",
        "instagram-juicedupjonnyy-full context",       # renamed export
    ),
}

# High-value files to normalize. (glob on path suffix -> canonical record type)
REGISTRY: list[tuple[str, str]] = [
    ("your_instagram_activity/saved/saved_posts.json", "saved_post"),
    ("your_instagram_activity/saved/saved_collections.json", "saved_collection"),
    ("your_instagram_activity/likes/liked_posts.json", "liked_post"),
    ("your_instagram_activity/likes/liked_comments.json", "liked_comment"),
    ("your_instagram_activity/comments/post_comments_*.json", "post_comment"),
    ("your_instagram_activity/comments/reels_comments.json", "reel_comment"),
    ("connections/followers_and_following/following.json", "following"),
    ("connections/followers_and_following/followers_*.json", "follower"),
    ("connections/followers_and_following/close_friends.json", "close_friend"),
    ("connections/followers_and_following/*favorited*.json", "favorited_profile"),
    ("your_instagram_activity/media/posts_*.json", "own_post"),
    ("your_instagram_activity/media/reels.json", "own_reel"),
    ("your_instagram_activity/media/stories.json", "own_story"),
    ("your_instagram_activity/ai/interest_categories.json", "interest"),
    ("your_instagram_activity/media/reposts.json", "repost"),
    ("logged_information/recent_searches/word_or_phrase_searches.json", "search_keyword"),
    ("logged_information/recent_searches/profile_searches.json", "profile_search"),
    ("logged_information/recent_searches/recent_searches.json", "search_recent"),
    # watch / browsing history + topics (named priorities in the plan)
    ("ads_information/ads_and_topics/videos_watched.json", "video_watched"),
    ("ads_information/ads_and_topics/posts_viewed.json", "post_viewed"),
    ("preferences/your_topics/your_topics.json", "topic"),
    ("preferences/your_topics/your_ads_see_more/see_less_topics.json", "topic_see_less"),
    ("*other_categories_used_to_reach_you.json", "ad_category"),
    # --- added 2026-09-15: more content context ---
    ("your_instagram_activity/media/archived_posts.json", "own_post_archived"),
    ("your_instagram_activity/saved/saved_music.json", "saved_music"),
    ("personal_information/personal_information/profile_changes.json", "profile_change"),
    ("ads_information/ads_and_topics/posts_you're_not_interested_in.json", "not_interested"),
    ("ads_information/ads_and_topics/posts_you're_interested_or_not_interested_in.json", "not_interested"),
    ("personal_information/information_about_you/locations_of_interest.json", "location"),
    ("personal_information/information_about_you/profile_based_in.json", "location"),
]

MEDIA_EXTS = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp", ".gif",
              ".mp3", ".wav", ".m4a", ".heic", ".srt"}
BATCH_MAX_BYTES = 45 * 1024 * 1024          # ~45 MB uncompressed per zip
MD_ROW_CAP = 500                            # cap markdown table rows for readability

# --------------------------------------------------------------------------- #
# Canonical record
# --------------------------------------------------------------------------- #

@dataclass
class Record:
    account: str
    type: str
    timestamp: int | None = None
    datetime: str | None = None
    url: str | None = None
    username: str | None = None
    text: str | None = None
    hashtags: list[str] = field(default_factory=list)
    media_uris: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def fix_mojibake(s: Any) -> Any:
    """Instagram escapes UTF-8 bytes as latin-1 into JSON; undo it."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def ts_to_iso(ts: int | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


HASHTAG_RE = re.compile(r"#(\w+)")

def extract_hashtags(text: str | None) -> list[str]:
    return HASHTAG_RE.findall(text) if text else []


def strip_query(url: str | None) -> str | None:
    if not url:
        return url
    return url.split("?", 1)[0]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def match_type(rel: str) -> str | None:
    rel = rel.replace("\\", "/")
    for pattern, rtype in REGISTRY:
        if fnmatch.fnmatch(rel, "*" + pattern):
            return rtype
    return None

# --------------------------------------------------------------------------- #
# Shape parsers -> list[Record]
# --------------------------------------------------------------------------- #

def flatten_label_values(lvs: list[dict]) -> tuple[dict[str, Any], list[str], str | None]:
    """Flatten a label_values array into (fields, hashtags, owner_username)."""
    fields: dict[str, Any] = {}
    hashtags: list[str] = []
    owner: str | None = None
    for lv in lvs:
        if "vec" in lv and "label" in lv:                       # ads categories etc.
            fields[lv["label"]] = [fix_mojibake(x.get("value")) for x in lv["vec"]]
        elif "label" in lv:
            fields[lv["label"]] = fix_mojibake(lv.get("value"))
            if lv.get("href"):
                fields.setdefault(lv["label"] + "__href", lv["href"])
        elif "dict" in lv and "title" in lv:
            title = (lv.get("title") or "").lower()
            if title == "hashtags":
                for group in lv["dict"]:
                    for f in group.get("dict", []):
                        if f.get("label") == "Name" and f.get("value"):
                            hashtags.append(fix_mojibake(f["value"]))
            elif title == "owner":
                for group in lv["dict"]:
                    o = {f.get("label"): fix_mojibake(f.get("value")) for f in group.get("dict", [])}
                    owner = owner or o.get("Username") or o.get("Name")
    return fields, hashtags, owner


def parse_label_values_list(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    # obj may be a list of items, or a single {timestamp, label_values, ...} object
    items = obj if isinstance(obj, list) else [obj]
    out: list[Record] = []
    for it in items:
        if not isinstance(it, dict) or "label_values" not in it:
            continue
        fields, hashtags, owner = flatten_label_values(it.get("label_values", []))
        text = (fields.get("Caption") or fields.get("Search") or fields.get("Search term")
                or fields.get("Name") or fields.get("Title") or None)
        owner = owner or fields.get("Author") or fields.get("Username")
        if not isinstance(text, str):          # a vec-valued label can leak a list here
            text = None
        url = strip_query(fields.get("URL") or fields.get("URL__href"))
        media_uris = [m.get("uri") for m in it.get("media", []) if isinstance(m, dict) and m.get("uri")]
        tags = sorted(set(hashtags) | set(extract_hashtags(text)))
        out.append(Record(
            account=account, type=rtype,
            timestamp=it.get("timestamp"),
            datetime=ts_to_iso(it.get("timestamp")),
            url=url, username=owner, text=text, hashtags=tags,
            media_uris=media_uris,
            extra={k: v for k, v in fields.items() if k not in {"Caption", "URL", "URL__href"}},
            source_file=rel,
        ))
    return out


def _string_list_container(obj: Any) -> list[dict]:
    """Return the list of items from either a top-level list or a single-key dict."""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, list):
                return v
    return []


def parse_string_list(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    out: list[Record] = []
    for it in _string_list_container(obj):
        if not isinstance(it, dict):
            continue
        title = fix_mojibake(it.get("title")) or None
        sld = it.get("string_list_data") or [{}]
        first = sld[0] if sld else {}
        value = fix_mojibake(first.get("value")) or None
        href = strip_query(first.get("href"))
        ts = first.get("timestamp")
        username = value or title
        out.append(Record(
            account=account, type=rtype,
            timestamp=ts, datetime=ts_to_iso(ts),
            url=href, username=username, text=title if title != username else None,
            source_file=rel,
        ))
    return out


def parse_string_map(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    out: list[Record] = []
    for it in _string_list_container(obj) if not isinstance(obj, list) else obj:
        if not isinstance(it, dict):
            continue
        smd = it.get("string_map_data", {})
        def g(key: str) -> dict:
            return smd.get(key, {}) if isinstance(smd, dict) else {}
        comment = fix_mojibake(g("Comment").get("value"))
        search = fix_mojibake(g("Search").get("value"))
        owner = fix_mojibake(g("Media Owner").get("value")) or fix_mojibake(g("Author").get("value"))
        ts = g("Time").get("timestamp") or g("Search").get("timestamp")
        text = comment or search
        media_uris = [m.get("uri") for m in it.get("media_list_data", []) if isinstance(m, dict) and m.get("uri")]
        out.append(Record(
            account=account, type=rtype,
            timestamp=ts, datetime=ts_to_iso(ts),
            username=owner or None, text=text or None,
            hashtags=extract_hashtags(text), media_uris=media_uris,
            source_file=rel,
        ))
    return out


def parse_own_media(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    items = _string_list_container(obj) if isinstance(obj, dict) else obj
    out: list[Record] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        # A post may bundle several media items, or be a single media dict.
        media = it.get("media") if isinstance(it.get("media"), list) else None
        if media is None and it.get("uri"):
            media = [it]
        media = media or []
        title = fix_mojibake(it.get("title")) or (fix_mojibake(media[0].get("title")) if media else None)
        ts = it.get("creation_timestamp") or (media[0].get("creation_timestamp") if media else None)
        uris = [m.get("uri") for m in media if isinstance(m, dict) and m.get("uri")]
        out.append(Record(
            account=account, type=rtype,
            timestamp=ts, datetime=ts_to_iso(ts),
            text=title, hashtags=extract_hashtags(title),
            media_uris=uris, source_file=rel,
        ))
    return out


def _walk_labels(node: Any, into: dict[str, Any]) -> None:
    """Recursively collect {label: value} pairs from nested label/dict/vec shapes."""
    if isinstance(node, dict):
        if "label" in node and ("value" in node or "href" in node):
            val = node.get("value")
            if val:
                into[node["label"]] = fix_mojibake(val)
        for v in node.values():
            _walk_labels(v, into)
    elif isinstance(node, list):
        for v in node:
            _walk_labels(v, into)


def parse_profile_change(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    out: list[Record] = []
    for it in _string_list_container(obj):
        if not isinstance(it, dict):
            continue
        smd = it.get("string_map_data", {}) or {}
        def g(k: str) -> dict:
            return smd.get(k, {}) if isinstance(smd, dict) else {}
        changed = fix_mojibake(g("Changed").get("value"))
        prev = fix_mojibake(g("Previous value").get("value"))
        new = fix_mojibake(g("New value").get("value"))
        ts = g("Change date").get("timestamp")
        text = f"Changed {changed}: '{prev or '(empty)'}' -> '{new or '(empty)'}'" if changed else None
        out.append(Record(account=account, type=rtype, timestamp=ts, datetime=ts_to_iso(ts),
                          text=text, source_file=rel))
    return out


def parse_not_interested(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    items = obj if isinstance(obj, list) else _string_list_container(obj)
    out: list[Record] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        fields: dict[str, Any] = {}
        _walk_labels(it.get("label_values", []), fields)
        text = fields.get("Caption") or fields.get("Title")
        url = strip_query(fields.get("URL"))
        out.append(Record(account=account, type=rtype,
                          timestamp=it.get("timestamp"), datetime=ts_to_iso(it.get("timestamp")),
                          url=url, username=fields.get("Author") or fields.get("Username"),
                          text=fix_mojibake(text) if text else None, source_file=rel))
    return out


def parse_location(obj: Any, account: str, rtype: str, rel: str) -> list[Record]:
    out: list[Record] = []
    for lv in (obj.get("label_values", []) if isinstance(obj, dict) else []):
        # vec-of-values shape: "Locations of interest"
        if "vec" in lv:
            for v in lv["vec"]:
                val = fix_mojibake(v.get("value"))
                if val:
                    out.append(Record(account=account, type=rtype, text=val, source_file=rel))
        # nested dict shape: Country / Region / City
        elif "dict" in lv:
            parts = [fix_mojibake(d.get("value")) for d in lv["dict"]
                     if isinstance(d, dict) and d.get("value")]
            if parts:
                out.append(Record(account=account, type=rtype,
                                  text=", ".join(parts), source_file=rel))
    return out


# Which parser to use per record type
PARSERS: dict[str, Callable[[Any, str, str, str], list[Record]]] = {
    "saved_post": parse_label_values_list,
    "saved_collection": parse_label_values_list,
    "liked_post": parse_label_values_list,
    "interest": parse_label_values_list,
    "search_recent": parse_label_values_list,
    "repost": parse_label_values_list,
    "video_watched": parse_label_values_list,
    "post_viewed": parse_label_values_list,
    "topic": parse_label_values_list,
    "topic_see_less": parse_label_values_list,
    "ad_category": parse_label_values_list,
    "liked_comment": parse_string_list,
    "following": parse_string_list,
    "follower": parse_string_list,
    "close_friend": parse_string_list,
    "favorited_profile": parse_string_list,
    "profile_search": parse_string_list,
    "post_comment": parse_string_map,
    "reel_comment": parse_string_map,
    "search_keyword": parse_string_map,
    "own_post": parse_own_media,
    "own_reel": parse_own_media,
    "own_story": parse_own_media,
    "own_post_archived": parse_own_media,
    "saved_music": parse_label_values_list,
    "profile_change": parse_profile_change,
    "not_interested": parse_not_interested,
    "location": parse_location,
}

# --------------------------------------------------------------------------- #
# Per-account processing
# --------------------------------------------------------------------------- #

def iter_files(root: Path) -> Iterable[Path]:
    yield from (p for p in root.rglob("*") if p.is_file())


def is_dm(rel: str) -> bool:
    return "/messages/" in ("/" + rel.replace("\\", "/") + "/")


def process_account(account: str, roots: list[Path]) -> dict[str, Any]:
    acc_out = OUT_DIR / account
    (acc_out / "normalized").mkdir(parents=True, exist_ok=True)
    (acc_out / "markdown").mkdir(parents=True, exist_ok=True)

    records: list[Record] = []
    normalized_files: list[str] = []
    available_not_normalized: list[str] = []
    unhandled: list[str] = []
    dm_files = 0
    media_files = 0
    media_bytes = 0
    json_files = 0

    for root in roots:
        if not root.exists():
            continue
        for path in iter_files(root):
            rel = str(path.relative_to(root)).replace("\\", "/")
            ext = path.suffix.lower()
            if ext in MEDIA_EXTS:
                media_files += 1
                media_bytes += path.stat().st_size
                continue
            if ext != ".json":
                continue
            json_files += 1
            if is_dm(rel):
                dm_files += 1
                continue
            rtype = match_type(rel)
            if rtype is None:
                available_not_normalized.append(f"{root.name}/{rel}")
                continue
            try:
                obj = load_json(path)
                recs = PARSERS[rtype](obj, account, rtype, f"{root.name}/{rel}")
                if recs:
                    records.extend(recs)
                    normalized_files.append(f"{root.name}/{rel}  ->  {rtype} ({len(recs)})")
                else:
                    unhandled.append(f"{root.name}/{rel} (0 records)")
            except Exception as exc:  # noqa: BLE001 - log, never crash the run
                unhandled.append(f"{root.name}/{rel}  ERROR: {exc}")

    # de-dup exact repeats
    seen: set[tuple] = set()
    deduped: list[Record] = []
    for r in records:
        key = (r.type, r.url, r.timestamp, r.text, r.username)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    records = deduped

    # group by type
    by_type: dict[str, list[Record]] = {}
    for r in records:
        by_type.setdefault(r.type, []).append(r)
    for recs in by_type.values():
        recs.sort(key=lambda r: (r.timestamp or 0), reverse=True)

    # write jsonl per type + _all
    for rtype, recs in by_type.items():
        with (acc_out / "normalized" / f"{rtype}.jsonl").open("w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    with (acc_out / "normalized" / "_all.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    # write markdown per type
    for rtype, recs in by_type.items():
        write_markdown(acc_out / "markdown" / f"{rtype}.md", account, rtype, recs)

    counts = {rtype: len(recs) for rtype, recs in sorted(by_type.items())}
    manifest = {
        "account": account,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "export_dirs": [str(r) for r in roots],
        "total_records": len(records),
        "counts_by_type": counts,
        "json_files_scanned": json_files,
        "json_files_normalized": sorted(normalized_files),
        "json_files_available_not_normalized": sorted(available_not_normalized),
        "unhandled_or_empty": sorted(unhandled),
        "direct_message_files_excluded": dm_files,
        "media_files_excluded": media_files,
        "media_bytes_excluded": media_bytes,
    }
    (acc_out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{account}] {len(records)} records across {len(counts)} types "
          f"-> {acc_out}")
    return manifest


def md_escape(s: str | None) -> str:
    if not s:
        return ""
    return s.replace("\n", " ").replace("|", "\\|").strip()


def write_markdown(path: Path, account: str, rtype: str, recs: list[Record]) -> None:
    lines = [
        "---",
        f"account: {account}",
        f"type: {rtype}",
        f"count: {len(recs)}",
        f"generated: {datetime.now(timezone.utc).date().isoformat()}",
        "---",
        "",
        f"# {rtype} — {account} ({len(recs)})",
        "",
        "| Date | Account | Text | URL |",
        "| --- | --- | --- | --- |",
    ]
    shown = recs[:MD_ROW_CAP]
    for r in shown:
        date = (r.datetime or "")[:10]
        text = md_escape(r.text)[:160]
        url = r.url or ""
        lines.append(f"| {date} | {md_escape(r.username)} | {text} | {url} |")
    if len(recs) > MD_ROW_CAP:
        lines.append("")
        lines.append(f"> Showing first {MD_ROW_CAP} of {len(recs)}. "
                     f"Full data in `../normalized/{rtype}.jsonl`.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

# --------------------------------------------------------------------------- #
# ChatGPT-style upload batches
# --------------------------------------------------------------------------- #

def build_batches(account: str, roots: list[Path]) -> dict[str, Any]:
    batch_dir = OUT_DIR / "_upload_batches" / account
    batch_dir.mkdir(parents=True, exist_ok=True)

    kept: list[tuple[Path, str, int]] = []       # (path, arcname, size)
    inventory_rows: list[dict[str, Any]] = []
    skipped_media_rows: list[dict[str, Any]] = []

    for root in roots:
        if not root.exists():
            continue
        for path in iter_files(root):
            rel = str(path.relative_to(root)).replace("\\", "/")
            arc = f"{root.name}/{rel}"
            size = path.stat().st_size
            ext = path.suffix.lower()
            if ext != ".json":
                reason = "media" if ext in MEDIA_EXTS else "non-json"
                inventory_rows.append({"file": arc, "bytes": size, "kept": 0, "reason": reason})
                if ext in MEDIA_EXTS:
                    skipped_media_rows.append({"file": arc, "bytes": size})
                continue
            if is_dm(rel):
                inventory_rows.append({"file": arc, "bytes": size, "kept": 0, "reason": "direct_message"})
                continue
            kept.append((path, arc, size))
            inventory_rows.append({"file": arc, "bytes": size, "kept": 1, "reason": "json"})

    # pack kept json into size-capped zip batches
    kept.sort(key=lambda t: t[1])
    batches: list[dict[str, Any]] = []
    idx = 0
    cur: list[tuple[Path, str, int]] = []
    cur_bytes = 0

    def flush() -> None:
        nonlocal idx, cur, cur_bytes
        if not cur:
            return
        idx += 1
        name = f"{account}-data-{idx:02d}.zip"
        with zipfile.ZipFile(batch_dir / name, "w", zipfile.ZIP_DEFLATED) as zf:
            for p, arc, _ in cur:
                zf.write(p, arcname=arc)
        batches.append({"zip": name, "files": len(cur), "uncompressed_bytes": cur_bytes})
        cur = []
        cur_bytes = 0

    for p, arc, size in kept:
        if cur_bytes + size > BATCH_MAX_BYTES and cur:
            flush()
        cur.append((p, arc, size))
        cur_bytes += size
    flush()

    # csv reports
    with (batch_dir / "file_inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "bytes", "kept", "reason"])
        w.writeheader()
        w.writerows(inventory_rows)
    with (batch_dir / "skipped_media.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "bytes"])
        w.writeheader()
        w.writerows(skipped_media_rows)

    summary = {
        "account": account,
        "batches": batches,
        "json_files_included": len(kept),
        "media_files_skipped": len(skipped_media_rows),
        "total_files_seen": len(inventory_rows),
    }
    print(f"[{account}] {len(batches)} upload batch(es), "
          f"{len(kept)} json files -> {batch_dir}")
    return summary

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def write_readme(account_manifests: dict[str, dict], batch_summaries: dict[str, dict]) -> None:
    lines = [
        "# Instagram Second Brain",
        "",
        f"Generated {datetime.now(timezone.utc).date().isoformat()} from raw Instagram exports "
        "(raw exports were not modified).",
        "",
        "Accounts are kept **separate** and tagged by the `account` field so you can "
        "query one or both without anything being silently merged.",
        "",
        "## Layout",
        "- `<account>/normalized/*.jsonl` — clean records, one per line, full fidelity.",
        "- `<account>/normalized/_all.jsonl` — every record for that account.",
        "- `<account>/markdown/*.md` — Obsidian-friendly tables.",
        "- `<account>/manifest.json` — counts + what was scanned/skipped.",
        "- `_upload_batches/<account>/*.zip` — ChatGPT-ready batches (json only, no media, no DMs).",
        "",
        "## Record schema",
        "`account, type, timestamp, datetime, url, username, text, hashtags, media_uris, extra, source_file`",
        "",
        "## Summary",
    ]
    for acc, man in account_manifests.items():
        lines.append(f"\n### {acc} — {man['total_records']} records")
        for rtype, n in man["counts_by_type"].items():
            lines.append(f"- {rtype}: {n}")
        b = batch_summaries.get(acc, {})
        lines.append(f"- upload batches: {len(b.get('batches', []))} "
                     f"({b.get('json_files_included', 0)} json files; "
                     f"{man['media_files_excluded']} media + {man['direct_message_files_excluded']} DM files excluded)")
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    account_manifests: dict[str, dict] = {}
    batch_summaries: dict[str, dict] = {}
    for account, roots in ACCOUNTS.items():
        account_manifests[account] = process_account(account, roots)
        batch_summaries[account] = build_batches(account, roots)
    write_readme(account_manifests, batch_summaries)
    print(f"\nDone. Output at: {OUT_DIR}")


if __name__ == "__main__":
    main()
