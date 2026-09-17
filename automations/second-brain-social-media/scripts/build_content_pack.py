"""
build_content_pack.py

Distills the normalized Instagram "Second Brain" (produced by build_second_brain.py)
into a compact, ChatGPT-ready CONTENT CONTEXT PACK for an automated content workflow.

Where build_second_brain.py produces the full, faithful archive (all ~57k records),
this tool produces the *useful* slice for generating content in your own voice:

  - voice & style profile (from your own posts / stories / reels / comments)
  - your own content log (captions + formats + hashtags)
  - saved inspiration (who + what you save)
  - topics / interests / searches (what you care about; what you mute)
  - audience + posting cadence

Primary account is emphasized; the other is included as a condensed reference.

Reads:  <OUT_DIR>/<account>/normalized/*.jsonl   (already mojibake-fixed)
Writes: <OUT_DIR>/content_pack/*.md, *.json, and content_pack.zip

Python 3.10+ (stdlib only).
"""
from __future__ import annotations

import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from paths import data_root

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

OUT_DIR = data_root()  # local working folder; never the public git repo
PACK_DIR = OUT_DIR / "content_pack"

PRIMARY = "jxnnys.wrld"
SECONDARY = "juicedupjonnyy"

# voice = the words you write yourself
VOICE_TYPES = ["own_post", "own_post_archived", "own_story", "own_reel", "repost",
               "post_comment", "reel_comment"]
OWN_CONTENT_TYPES = ["own_post", "own_post_archived", "own_reel", "own_story"]

# very small English stopword set (stdlib only, no downloads)
STOP = set("""
a an and the of to in on for with at by from is are was were be been being this that these those
i me my we our you your he she it they them his her its their as or but if then so than too very
just not no yes do does did done have has had will would can could should may might must up down
out over under again more most some any all each other into out about after before while when where
who what which why how i'm im dont don't cant can't got get getting really actually literally lol
haha omg like know think going go get one two new day time now today good great best love
""".split())

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "]",
    flags=re.UNICODE,
)
# skin-tone modifiers, ZWJ, variation selectors, gender signs — not standalone emojis
EMOJI_MODIFIERS = set("\U0001F3FB\U0001F3FC\U0001F3FD\U0001F3FE\U0001F3FF"
                      "\U0000200D\U0000FE0F\U00002640\U00002642")
WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'’]+")

MAX_SAMPLE_LINES = 400        # cap per md section for readability

# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #

def load_type(account: str, rtype: str) -> list[dict]:
    path = OUT_DIR / account / "normalized" / f"{rtype}.jsonl"
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def count_type(account: str, rtype: str) -> int:
    path = OUT_DIR / account / "normalized" / f"{rtype}.jsonl"
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())

# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #

def clean_text(t: Any) -> str:
    if not isinstance(t, str):
        return ""
    return t.strip()


def flat(t: str) -> str:
    """Collapse internal newlines/whitespace so a caption fits one markdown bullet."""
    return re.sub(r"\s+", " ", t).strip()


def voice_profile(account: str) -> dict[str, Any]:
    texts: list[tuple[str, str, str]] = []   # (type, date, text)
    for rtype in VOICE_TYPES:
        for r in load_type(account, rtype):
            t = clean_text(r.get("text"))
            if t:
                texts.append((rtype, (r.get("datetime") or "")[:10], t))

    all_text = "\n".join(t for _, _, t in texts)
    words = [w.lower() for w in WORD_RE.findall(all_text)]
    content_words = [w for w in words if w not in STOP and len(w) >= 4]
    emojis = [e for e in EMOJI_RE.findall(all_text) if e not in EMOJI_MODIFIERS]
    lengths = [len(t) for _, _, t in texts if t]
    with_hashtags = sum(1 for _, _, t in texts if "#" in t)
    hashtags = Counter()
    for rtype in VOICE_TYPES:
        for r in load_type(account, rtype):
            for h in (r.get("hashtags") or []):
                hashtags[h.lower()] += 1

    # representative caption samples: prefer longer own_post captions
    posts = [(d, t) for ty, d, t in texts if ty == "own_post"]
    posts.sort(key=lambda x: len(x[1]), reverse=True)
    story_lines = [t for ty, _, t in texts if ty == "own_story"]
    comment_lines = [t for ty, _, t in texts if ty in ("post_comment", "reel_comment")]

    return {
        "account": account,
        "total_authored_texts": len(texts),
        "avg_caption_len_chars": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "pct_texts_with_hashtags": round(100 * with_hashtags / len(texts), 1) if texts else 0,
        "emoji_uses": len(emojis),
        "top_emojis": [e for e, _ in Counter(emojis).most_common(15)],
        "top_words": [w for w, _ in Counter(content_words).most_common(40)],
        "top_hashtags": [f"#{h}" for h, _ in hashtags.most_common(25)],
        "sample_post_captions": [t for _, t in posts[:25]],
        "sample_story_lines": story_lines[:40],
        "sample_comments": comment_lines[:30],
    }


def cadence(account: str) -> dict[str, Any]:
    by_month: Counter = Counter()
    by_dow: Counter = Counter()
    by_hour: Counter = Counter()
    dows = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    total = 0
    for rtype in OWN_CONTENT_TYPES:
        for r in load_type(account, rtype):
            ts = r.get("timestamp")
            if not ts:
                continue
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            by_month[dt.strftime("%Y-%m")] += 1
            by_dow[dows[dt.weekday()]] += 1
            by_hour[dt.hour] += 1
            total += 1
    return {
        "total_own_content_items": total,
        "by_month": dict(sorted(by_month.items())),
        "by_weekday": {d: by_dow.get(d, 0) for d in dows},
        "by_hour_utc": {str(h): by_hour.get(h, 0) for h in range(24)},
    }


def saved_inspiration(account: str) -> dict[str, Any]:
    saved = load_type(account, "saved_post")
    authors = Counter()
    caption_words = Counter()
    samples: list[dict] = []
    for r in saved:
        u = r.get("username")
        if u:
            authors[u] += 1
        t = clean_text(r.get("text"))
        if t:
            for w in WORD_RE.findall(t.lower()):
                if w not in STOP and len(w) >= 4:
                    caption_words[w] += 1
            if len(samples) < 40:
                samples.append({"author": u, "text": t[:200], "url": r.get("url")})
    return {
        "total_saved": len(saved),
        "top_saved_accounts": [{"account": a, "saves": n} for a, n in authors.most_common(30)],
        "recurring_saved_themes": [w for w, _ in caption_words.most_common(30)],
        "sample_saved": samples,
    }


def topics(account: str) -> dict[str, Any]:
    def _from_extra(r: dict) -> str:
        """Some types (interest, topics) carry the value inside extra."""
        ex = r.get("extra") or {}
        for k in ("Interest", "Name", "Topic", "Title", "Value"):
            v = clean_text(ex.get(k))
            if v:
                return v
        # otherwise first non-empty string extra value that isn't a timestamp field
        for k, v in ex.items():
            if "time" in k.lower():
                continue
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""

    def clean_interest(v: str) -> str:
        for pre in ("The user might be interested in ", "The user is interested in "):
            if v.startswith(pre):
                return v[len(pre):]
        return v

    def vals(rtype: str, limit: int = 60) -> list[str]:
        out = []
        for r in load_type(account, rtype):
            v = clean_text(r.get("text")) or clean_text(r.get("username")) or _from_extra(r)
            if v:
                out.append(clean_interest(v))
        # de-dup preserving order
        seen = set()
        uniq = [x for x in out if not (x in seen or seen.add(x))]
        return uniq[:limit]
    return {
        "interest_categories": vals("interest"),
        "assigned_topics": vals("topic"),
        "muted_topics_see_less": vals("topic_see_less"),
        "search_keywords": vals("search_keyword"),
        "profile_searches": vals("profile_search"),
    }


def audience(account: str) -> dict[str, Any]:
    following = load_type(account, "following")
    locs = [clean_text(r.get("text")) for r in load_type(account, "location") if clean_text(r.get("text"))]
    return {
        "followers": count_type(account, "follower"),
        "following": count_type(account, "following"),
        "close_friends": count_type(account, "close_friend"),
        "favorited_profiles": count_type(account, "favorited_profile"),
        "sample_following": [r.get("username") for r in following[:50] if r.get("username")],
        "locations": locs[:15],
    }


def music_taste(account: str) -> dict[str, Any]:
    tracks = load_type(account, "saved_music")
    artists = Counter()
    samples = []
    for r in tracks:
        ex = r.get("extra") or {}
        title = clean_text(r.get("text")) or clean_text(ex.get("Title"))
        artist = clean_text(ex.get("Artist"))
        if artist:
            artists[artist] += 1
        if title and len(samples) < 40:
            samples.append(f"{title} — {artist}" if artist else title)
    return {
        "total_saved_tracks": len(tracks),
        "top_artists": [{"artist": a, "saves": n} for a, n in artists.most_common(25)],
        "sample_tracks": samples,
    }


def bio_history(account: str) -> list[str]:
    changes = load_type(account, "profile_change")
    changes.sort(key=lambda r: (r.get("timestamp") or 0))
    out = []
    for r in changes:
        t = clean_text(r.get("text"))
        if t:
            date = (r.get("datetime") or "")[:10]
            out.append(f"{date}  {flat(t)}")
    return out


def not_interested(account: str) -> list[str]:
    out = []
    for r in load_type(account, "not_interested"):
        t = clean_text(r.get("text"))
        u = r.get("username")
        if t or u:
            out.append(f"@{u}: {flat(t)}" if u else flat(t))
    return out[:60]

# --------------------------------------------------------------------------- #
# Markdown writers
# --------------------------------------------------------------------------- #

def w(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def md_voice(profile: dict, secondary_profile: dict, bio_hist: list[str]) -> list[str]:
    L = ["# Voice & Style Profile", "",
         f"Primary account: **{profile['account']}**  ·  "
         f"generated {datetime.now(timezone.utc).date().isoformat()}", "",
         "Use this to write captions, hooks, and replies that sound like me.", ""]
    if bio_hist:
        L += ["## How I've described myself (bio / name history)",
              "Signals identity + how I self-present over time.", ""]
        L += [f"- {b}" for b in bio_hist]
        L.append("")
    L += ["## Metrics (primary)",
         f"- Authored texts analyzed: {profile['total_authored_texts']}",
         f"- Average caption length: {profile['avg_caption_len_chars']} chars",
         f"- Captions using hashtags: {profile['pct_texts_with_hashtags']}%",
         f"- Emoji uses: {profile['emoji_uses']}",
         f"- Signature emojis: {' '.join(profile['top_emojis']) or '(few/none)'}",
         "",
         "## Recurring vocabulary",
         ", ".join(profile["top_words"]) or "(n/a)",
         "",
         "## Hashtags I actually use",
         " ".join(profile["top_hashtags"]) or "(rarely uses hashtags)",
         "",
         "## Real caption samples (longest, most representative)"]
    for t in profile["sample_post_captions"]:
        L.append(f"- {flat(t)}")
    L += ["", "## Story one-liners (quick, casual voice)"]
    for t in profile["sample_story_lines"]:
        L.append(f"- {flat(t)}")
    L += ["", "## How I reply in comments"]
    for t in profile["sample_comments"]:
        L.append(f"- {flat(t)}")
    L += ["", "---", "",
          f"## Secondary account reference: {secondary_profile['account']}",
          f"- Signature emojis: {' '.join(secondary_profile['top_emojis']) or '(few/none)'}",
          f"- Recurring vocabulary: {', '.join(secondary_profile['top_words'][:25]) or '(n/a)'}",
          "- Sample captions:"]
    for t in secondary_profile["sample_post_captions"][:8]:
        L.append(f"  - {flat(t)}")
    return L


def md_my_content(account: str) -> list[str]:
    L = [f"# My Content Log — {account}", "",
         "Everything I've posted, newest first. Feeds pattern detection "
         "(what formats/topics I post, how I caption them).", ""]
    for rtype, label in [("own_post", "Posts"), ("own_reel", "Reels"), ("own_story", "Stories")]:
        recs = load_type(account, rtype)
        L += [f"## {label} ({len(recs)})", ""]
        shown = 0
        for r in recs:
            t = clean_text(r.get("text"))
            if rtype == "own_story" and not t:
                continue                      # skip caption-less stories in the readable log
            date = (r.get("datetime") or "")[:10]
            n_media = len(r.get("media_uris") or [])
            tags = " ".join(f"#{h}" for h in (r.get("hashtags") or []))
            piece = flat(t) if t else "(no caption)"
            L.append(f"- **{date}** · {n_media} media · {piece} {tags}".rstrip())
            shown += 1
            if shown >= MAX_SAMPLE_LINES:
                L.append(f"> …first {MAX_SAMPLE_LINES} shown; full data in "
                         f"`../{account}/normalized/{rtype}.jsonl`.")
                break
        L.append("")
    return L


def md_saved(insp: dict, music: dict) -> list[str]:
    L = ["# Saved Inspiration", "",
         f"What I bookmark = my taste / content references. Total saved: {insp['total_saved']}.", "",
         "## Accounts I save from most"]
    for a in insp["top_saved_accounts"]:
        L.append(f"- {a['account']} — {a['saves']} saves")
    L += ["", "## Recurring themes in what I save",
          ", ".join(insp["recurring_saved_themes"]) or "(n/a)", "",
          "## Sample saved posts"]
    for s in insp["sample_saved"]:
        who = s.get("author") or "?"
        L.append(f"- @{who}: {s.get('text') or ''}".rstrip())
    if music.get("total_saved_tracks"):
        L += ["", f"## Saved music / audio taste ({music['total_saved_tracks']} tracks)",
              "Signals the sonic vibe for reels/stories.", "",
              "### Top artists"]
        for a in music["top_artists"]:
            L.append(f"- {a['artist']} — {a['saves']}")
        L += ["", "### Sample saved tracks"]
        for t in music["sample_tracks"]:
            L.append(f"- {t}")
    return L


def md_topics(top: dict, not_interested_list: list[str]) -> list[str]:
    L = ["# Topics, Interests & Searches", ""]
    for key, label in [
        ("interest_categories", "Interest categories (IG-assigned)"),
        ("assigned_topics", "Assigned topics"),
        ("search_keywords", "Things I searched"),
        ("profile_searches", "Profiles I searched"),
        ("muted_topics_see_less", "Topics I muted (see less) — AVOID these"),
    ]:
        vals = top.get(key) or []
        L += [f"## {label} ({len(vals)})", ", ".join(vals) if vals else "(none)", ""]
    if not_interested_list:
        L += [f"## Posts I marked 'not interested' — AVOID these vibes ({len(not_interested_list)})", ""]
        L += [f"- {x}" for x in not_interested_list]
        L.append("")
    return L


def md_audience(aud: dict, cad: dict) -> list[str]:
    L = ["# Audience & Posting Cadence", "",
         "## Audience",
         f"- Followers: {aud['followers']}",
         f"- Following: {aud['following']}",
         f"- Close friends: {aud['close_friends']}",
         f"- Favorited profiles: {aud['favorited_profiles']}",
         f"- Locations of interest: {', '.join(aud.get('locations') or []) or '(n/a)'}",
         "",
         f"## Posting cadence ({cad['total_own_content_items']} own items)",
         "", "### By month"]
    for m, n in cad["by_month"].items():
        L.append(f"- {m}: {n}")
    L += ["", "### By weekday"]
    for d, n in cad["by_weekday"].items():
        L.append(f"- {d}: {n}")
    L += ["", "### By hour (UTC)"]
    for h, n in cad["by_hour_utc"].items():
        if n:
            L.append(f"- {int(h):02d}:00 — {n}")
    return L


def md_start_here(profile: dict, cad: dict, aud: dict, insp: dict, top: dict) -> list[str]:
    peak_dow = max(cad["by_weekday"].items(), key=lambda x: x[1])[0] if cad["by_weekday"] else "?"
    return [
        "# START HERE — Content Context Pack",
        "",
        f"Generated {datetime.now(timezone.utc).date().isoformat()} from Instagram exports "
        f"for **{profile['account']}** (primary) and **{SECONDARY}** (reference).",
        "",
        "## What this is",
        "A distilled context pack for an automated content workflow. Upload the whole",
        "`content_pack/` folder (or `content_pack.zip`) to a ChatGPT Project / custom GPT,",
        "or paste `voice_profile.md` into the system instructions.",
        "",
        "## Files",
        "- `voice_profile.md` — how I write (the most important file).",
        "- `my_content_log.md` — everything I've posted, with captions.",
        "- `saved_inspiration.md` — accounts/themes I bookmark.",
        "- `topics_interests.md` — what I care about + what to avoid.",
        "- `audience_cadence.md` — audience size + when I post.",
        f"- `{SECONDARY}_reference.md` — condensed second Instagram account.",
        "- `x_twitter.md` — X/Twitter voice, top tweets by engagement (if archive present).",
        "- `content_pack.json` — machine-readable profile (for automation / Make / n8n).",
        "",
        "## Snapshot",
        f"- Signature emojis: {' '.join(profile['top_emojis']) or '(few)'}",
        f"- Core vocabulary: {', '.join(profile['top_words'][:15])}",
        f"- Avg caption length: {profile['avg_caption_len_chars']} chars; "
        f"hashtags on {profile['pct_texts_with_hashtags']}% of captions",
        f"- Audience: {aud['followers']} followers / {aud['following']} following",
        f"- Busiest posting day: {peak_dow}",
        f"- Saves from {len(insp['top_saved_accounts'])} recurring accounts; "
        f"top themes: {', '.join(insp['recurring_saved_themes'][:8])}",
        "",
        "## Suggested system prompt seed",
        "> You write social captions in my voice. Keep them "
        f"~{int(profile['avg_caption_len_chars'])} characters, casual, "
        f"{'emoji-forward' if profile['emoji_uses'] > profile['total_authored_texts'] else 'light on emoji'}. "
        "Favor my recurring vocabulary and signature emojis. Match the tone of the sample "
        "captions in voice_profile.md. Avoid the muted topics in topics_interests.md.",
        "",
        "## Provenance",
        "Built from the full archive in this same folder (see ../README.md). Raw exports "
        "were never modified. DMs and media binaries are excluded from this pack.",
    ]


def md_secondary(account: str, profile: dict) -> list[str]:
    L = [f"# Reference: {account}", "",
         "Condensed profile for the secondary account.", "",
         f"- Authored texts: {profile['total_authored_texts']}",
         f"- Signature emojis: {' '.join(profile['top_emojis']) or '(few)'}",
         f"- Vocabulary: {', '.join(profile['top_words'][:30])}",
         f"- Hashtags: {' '.join(profile['top_hashtags']) or '(rare)'}",
         "", "## Sample captions"]
    for t in profile["sample_post_captions"][:12]:
        L.append(f"- {flat(t)}")
    L += ["", "## Story one-liners"]
    for t in profile["sample_story_lines"][:20]:
        L.append(f"- {flat(t)}")
    return L

# --------------------------------------------------------------------------- #
# X / Twitter  (optional — folded in if a twitter archive is found)
# --------------------------------------------------------------------------- #

# candidate locations for the extracted X archive (a "data/" folder of *.js files)
X_DIR_CANDIDATES = [
    OUT_DIR / "twitter archives",
    OUT_DIR / "twitter-archives",
    Path(r"C:\Users\JTerr\Downloads") / "twitter archives",
]
X_URL_RE = re.compile(r"https://t\.co/\w+")


def find_x_data() -> Path | None:
    for c in X_DIR_CANDIDATES:
        if (c / "data" / "tweets.js").exists():
            return c / "data"
    return None


def load_x_js(path: Path) -> Any:
    """X exports wrap JSON as `window.YTD.<name>.partN = [ ... ]`."""
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    i = raw.find("=")
    if i == -1:
        return []
    try:
        return json.loads(raw[i + 1:])
    except json.JSONDecodeError:
        return []


def expand_tweet_text(tweet: dict) -> str:
    txt = tweet.get("full_text") or tweet.get("text") or ""
    for u in (tweet.get("entities", {}) or {}).get("urls", []) or []:
        if u.get("url") and u.get("expanded_url"):
            txt = txt.replace(u["url"], u["expanded_url"])
    txt = X_URL_RE.sub("", txt)                    # drop leftover media t.co links
    return re.sub(r"\s+", " ", txt).strip()


def x_profile(data_dir: Path) -> dict[str, Any]:
    account = (load_x_js(data_dir / "account.js") or [{}])
    acc = account[0].get("account", {}) if account else {}
    prof = (load_x_js(data_dir / "profile.js") or [{}])
    p = prof[0].get("profile", {}) if prof else {}
    tweets_raw = load_x_js(data_dir / "tweets.js")

    originals: list[tuple[int, str, str, int, int]] = []   # (fav, text, date, rt, faves)
    replies = 0
    retweets = 0
    hashtags = Counter()
    emojis: list[str] = []
    words: list[str] = []
    by_month: Counter = Counter()

    for row in tweets_raw:
        tw = row.get("tweet", row)
        text = expand_tweet_text(tw)
        if not text:
            continue
        if tw.get("full_text", "").startswith("RT @"):
            retweets += 1
            continue
        created = tw.get("created_at", "")
        try:
            dt = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y")
            date = dt.date().isoformat()
            by_month[dt.strftime("%Y-%m")] += 1
        except (ValueError, TypeError):
            date = ""
        fav = int(tw.get("favorite_count", 0) or 0)
        rt = int(tw.get("retweet_count", 0) or 0)
        is_reply = bool(tw.get("in_reply_to_status_id")) or tw.get("full_text", "").startswith("@")
        if is_reply:
            replies += 1
        for h in (tw.get("entities", {}) or {}).get("hashtags", []) or []:
            if h.get("text"):
                hashtags[h["text"].lower()] += 1
        if not is_reply:
            originals.append((fav, text, date, rt, fav))
            # voice signal from original tweets only, minus @mentions / URLs
            clean = re.sub(r"http\S+", "", re.sub(r"@\w+", "", text))
            emojis += [e for e in EMOJI_RE.findall(clean) if e not in EMOJI_MODIFIERS]
            words += [x.lower() for x in WORD_RE.findall(clean)
                      if x.lower() not in STOP | {"https", "http", "status", "amp"}
                      and len(x) >= 4]

    top_by_engagement = sorted(originals, key=lambda t: (t[0] + 2 * t[3]), reverse=True)[:25]
    recent = originals[:25]   # tweets.js is newest-first

    return {
        "handle": acc.get("username"),
        "display_name": acc.get("accountDisplayName"),
        "created_at": acc.get("createdAt"),
        "bio": (p.get("description", {}) or {}).get("bio"),
        "location": (p.get("description", {}) or {}).get("location"),
        "website": (p.get("description", {}) or {}).get("website"),
        "followers": len(load_x_js(data_dir / "follower.js")),
        "following": len(load_x_js(data_dir / "following.js")),
        "likes_count": len(load_x_js(data_dir / "like.js")),
        "total_tweets": len(tweets_raw),
        "original_tweets": len(originals),
        "replies": replies,
        "retweets": retweets,
        "top_emojis": [e for e, _ in Counter(emojis).most_common(15)],
        "top_words": [wd for wd, _ in Counter(words).most_common(40)],
        "top_hashtags": [f"#{h}" for h, _ in hashtags.most_common(20)],
        "by_month": dict(sorted(by_month.items())),
        "top_tweets_by_engagement": [
            {"date": d, "faves": f, "retweets": rt, "text": t}
            for (f, t, d, rt, _) in top_by_engagement
        ],
        "recent_tweets": [
            {"date": d, "faves": f, "retweets": rt, "text": t}
            for (f, t, d, rt, _) in recent
        ],
    }


def md_x(x: dict) -> list[str]:
    L = [f"# X / Twitter — @{x.get('handle')}", "",
         f"Display name: {x.get('display_name')}  ·  since {(x.get('created_at') or '')[:10]}",
         f"Bio: {x.get('bio') or '(none)'}",
         f"Location: {x.get('location') or '(none)'}  ·  Website: {x.get('website') or '(none)'}",
         "",
         "## Snapshot",
         f"- Followers: {x['followers']}  ·  Following: {x['following']}  ·  Likes given: {x['likes_count']}",
         f"- Tweets: {x['total_tweets']} total — {x['original_tweets']} original, "
         f"{x['replies']} replies, {x['retweets']} retweets",
         f"- Signature emojis: {' '.join(x['top_emojis']) or '(few)'}",
         f"- Recurring vocabulary: {', '.join(x['top_words'][:25]) or '(n/a)'}",
         f"- Hashtags: {' '.join(x['top_hashtags']) or '(rare)'}",
         "",
         "## Top tweets by engagement (what resonates)"]
    for t in x["top_tweets_by_engagement"]:
        L.append(f"- **{t['date']}** · ♥{t['faves']} ↻{t['retweets']} · {t['text']}")
    L += ["", "## Recent original tweets (current voice)"]
    for t in x["recent_tweets"]:
        L.append(f"- **{t['date']}** · {t['text']}")
    L += ["", "## Posting cadence by month"]
    for m, n in x["by_month"].items():
        L.append(f"- {m}: {n}")
    return L


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    prof = voice_profile(PRIMARY)
    prof2 = voice_profile(SECONDARY)
    cad = cadence(PRIMARY)
    aud = audience(PRIMARY)
    insp = saved_inspiration(PRIMARY)
    top = topics(PRIMARY)
    music = music_taste(PRIMARY)
    bio_hist = bio_history(PRIMARY)
    not_int = not_interested(PRIMARY)

    w(PACK_DIR / "00_START_HERE.md", md_start_here(prof, cad, aud, insp, top))
    w(PACK_DIR / "voice_profile.md", md_voice(prof, prof2, bio_hist))
    w(PACK_DIR / "my_content_log.md", md_my_content(PRIMARY))
    w(PACK_DIR / "saved_inspiration.md", md_saved(insp, music))
    w(PACK_DIR / "topics_interests.md", md_topics(top, not_int))
    w(PACK_DIR / "audience_cadence.md", md_audience(aud, cad))
    w(PACK_DIR / f"{SECONDARY}_reference.md", md_secondary(SECONDARY, prof2))

    # Optional: fold in X / Twitter if an archive is present
    x = None
    x_data = find_x_data()
    if x_data:
        x = x_profile(x_data)
        w(PACK_DIR / "x_twitter.md", md_x(x))
        print(f"  (folded in X archive: @{x.get('handle')}, {x['original_tweets']} original tweets)")

    machine = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primary_account": PRIMARY,
        "secondary_account": SECONDARY,
        "voice": prof,
        "voice_secondary": prof2,
        "cadence": cad,
        "audience": aud,
        "saved_inspiration": insp,
        "music_taste": music,
        "bio_history": bio_hist,
        "not_interested": not_int,
        "topics": top,
        "x_twitter": x,
    }
    (PACK_DIR / "content_pack.json").write_text(
        json.dumps(machine, ensure_ascii=False, indent=2), encoding="utf-8")

    # zip everything for one-shot upload
    zip_path = PACK_DIR / "content_pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PACK_DIR.glob("*")):
            if p.name != "content_pack.zip" and p.is_file():
                zf.write(p, arcname=p.name)

    print(f"Content pack written to: {PACK_DIR}")
    for p in sorted(PACK_DIR.glob("*")):
        print(f"  {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
