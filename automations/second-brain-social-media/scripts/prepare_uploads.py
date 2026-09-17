"""
prepare_uploads.py  —  Second-Brain upload-batch preparer

Point it at a folder (default: the folder this script lives in) and it walks
everything, throws out the noise, de-duplicates, and packs the useful text into
size-capped .zip "chunks" you upload to ChatGPT / Claude one at a time.

Designed for the "Social media clone" second-brain folder, but works on any folder.

What it does
------------
- Keeps only text-like files (json, jsonl, js, md, txt, csv, html, xml, yaml).
  Media (mp4/jpg/png/...) and stray .zip archives are skipped by default.
- Skips private Direct Messages (any path with a /messages/ segment).
- De-duplicates by content hash, so the same file living in two places
  (e.g. a copy under second-brain-instagram/) is packed only once.
- Groups files into buckets by their top-level folder, orders the buckets by
  value (distilled content pack first, raw archives last), and fills each zip
  up to a size cap.
- Writes an ordered UPLOAD_INDEX.md + manifest.json so you always know what each
  chunk is and what order to add them to your second brain.

Usage (Windows)
---------------
    python prepare_uploads.py
    python prepare_uploads.py --root "C:\\Users\\JTerr\\Downloads\\Social media clone"
    python prepare_uploads.py --max-mb 15 --include-dms --all

Default --root is SOCIAL_BRAIN_ROOT (or config.local.json / the Downloads working folder).
Output goes to <root>\\_prepared_uploads\\ . Re-running overwrites it cleanly.

Python 3.10+ (stdlib only).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from paths import data_root

# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

OUTPUT_DIRNAME = "_prepared_uploads"
DEFAULT_MAX_MB = 18                      # per-zip cap; comfortable for uploads

TEXT_EXTS = {".json", ".jsonl", ".js", ".md", ".txt", ".csv",
             ".html", ".htm", ".xml", ".yaml", ".yml", ".ndjson"}

# directories we never descend into
SKIP_DIRS = {OUTPUT_DIRNAME, ".git", ".claude", ".cursor", ".vscode",
             "__pycache__", "node_modules", ".idea", ".obsidian"}

# bucket priority: lower number = more valuable = upload first.
# matched as a substring against the bucket (top-level folder) name, lowercased.
BUCKET_PRIORITY = [
    ("content_pack", 0),               # the distilled gold
    ("second-brain", 1),               # normalized brain + docs
    ("instagram-", 4),                 # raw full-context exports (checked before account names)
    ("twitter", 3),                    # raw X archive
    ("jxnnys.wrld", 2),                # normalized account output (no "instagram-" prefix)
    ("juicedupjonnyy", 2),
]
DEFAULT_PRIORITY = 5


def bucket_priority(bucket: str) -> int:
    b = bucket.lower()
    for frag, pri in BUCKET_PRIORITY:
        if frag in b:
            return pri
    return DEFAULT_PRIORITY

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def human(n: int) -> str:
    f = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if f < 1024 or unit == "GB":
            return f"{f:.1f}{unit}" if unit != "B" else f"{int(f)}B"
        f /= 1024
    return f"{f:.1f}GB"


def sha256(path: Path, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(buf):
            h.update(chunk)
    return h.hexdigest()


def is_dm(rel: str) -> bool:
    return "/messages/" in "/" + rel.replace("\\", "/").strip("/") + "/"


def safe_slug(name: str) -> str:
    keep = [c if (c.isalnum() or c in "-_.") else "-" for c in name]
    return "".join(keep).strip("-.") or "root"

# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #

def collect(root: Path, out_dir: Path, exts: set[str],
            include_dms: bool) -> tuple[list[dict], dict]:
    """Walk root, filter, de-dup. Return (kept_files, stats)."""
    kept: list[dict] = []
    seen_hashes: dict[str, str] = {}       # hash -> first rel path
    stats = {"scanned": 0, "skipped_dir": 0, "skipped_ext": 0,
             "skipped_dm": 0, "duplicates": 0, "dup_bytes": 0, "kept_bytes": 0}

    for path in root.rglob("*"):
        # prune skip dirs early
        parts = {p.lower() for p in path.relative_to(root).parts[:-1]}
        if parts & {d.lower() for d in SKIP_DIRS}:
            continue
        if not path.is_file():
            continue
        stats["scanned"] += 1
        rel = str(path.relative_to(root)).replace("\\", "/")

        if path.suffix.lower() not in exts:
            stats["skipped_ext"] += 1
            continue
        if not include_dms and is_dm(rel):
            stats["skipped_dm"] += 1
            continue

        try:
            digest = sha256(path)
        except OSError:
            continue
        if digest in seen_hashes:
            stats["duplicates"] += 1
            stats["dup_bytes"] += path.stat().st_size
            continue
        seen_hashes[digest] = rel

        size = path.stat().st_size
        stats["kept_bytes"] += size
        top = path.relative_to(root).parts[0] if len(path.relative_to(root).parts) > 1 else "_root"
        kept.append({"path": path, "rel": rel, "size": size, "bucket": top})

    return kept, stats


def make_batches(kept: list[dict], out_dir: Path, max_bytes: int) -> list[dict]:
    """Pack kept files into size-capped zips, grouped by bucket, ordered by value."""
    # order files: bucket priority, then bucket name, then path
    kept.sort(key=lambda f: (bucket_priority(f["bucket"]), f["bucket"].lower(), f["rel"].lower()))

    batches: list[dict] = []
    seq = 0

    # group by bucket, then fill zips
    from itertools import groupby
    for bucket, group in groupby(kept, key=lambda f: f["bucket"]):
        files = list(group)
        pri = bucket_priority(bucket)
        part = 0
        cur: list[dict] = []
        cur_bytes = 0

        def flush() -> None:
            nonlocal part, cur, cur_bytes, seq
            if not cur:
                return
            part += 1
            seq += 1
            name = f"{seq:02d}_{safe_slug(bucket)}_part{part:02d}.zip"
            zpath = out_dir / name
            with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
                listing = [f["rel"] for f in cur]
                zf.writestr("_batch_manifest.txt",
                            f"bucket: {bucket}\nfiles: {len(cur)}\n"
                            f"uncompressed: {human(cur_bytes)}\n\n" + "\n".join(listing))
                for f in cur:
                    zf.write(f["path"], arcname=f["rel"])
            batches.append({
                "seq": seq, "zip": name, "bucket": bucket, "priority": pri,
                "files": len(cur), "uncompressed_bytes": cur_bytes,
                "zip_bytes": zpath.stat().st_size,
                "contents": [f["rel"] for f in cur],
            })
            cur = []
            cur_bytes = 0

        for f in files:
            # a single file larger than the cap still goes in its own zip
            if cur and cur_bytes + f["size"] > max_bytes:
                flush()
            cur.append(f)
            cur_bytes += f["size"]
        flush()

    return batches


def write_index(out_dir: Path, root: Path, batches: list[dict], stats: dict,
                max_bytes: int) -> None:
    total_zip = sum(b["zip_bytes"] for b in batches)
    lines = [
        "# Upload Index — second-brain chunks",
        "",
        f"Prepared {datetime.now(timezone.utc).date().isoformat()} from `{root.name}`.",
        "",
        f"**{len(batches)} chunks**, {sum(b['files'] for b in batches)} files, "
        f"{human(total_zip)} zipped ({human(stats['kept_bytes'])} raw).",
        "",
        "Upload them **in this order** — each row is one chunk. Add a chunk, let the",
        "model digest it, then add the next. Chunks are ordered most-useful first.",
        "",
        "| # | Chunk (zip) | What it is | Files | Size |",
        "| - | ----------- | ---------- | ----: | ---: |",
    ]
    what = {
        0: "Distilled content pack (voice, posts, taste) — best context",
        1: "Normalized brain + guides",
        2: "Normalized account records",
        3: "X / Twitter archive (text)",
        4: "Raw Instagram export JSON (deep archive)",
        5: "Other",
    }
    for b in batches:
        lines.append(f"| {b['seq']} | `{b['zip']}` | {what.get(b['priority'], 'Other')} "
                     f"| {b['files']} | {human(b['zip_bytes'])} |")
    lines += [
        "",
        "## Notes",
        f"- Per-chunk cap: {human(max_bytes)} (change with `--max-mb`).",
        f"- De-duplicated: {stats['duplicates']} identical files skipped "
        f"({human(stats['dup_bytes'])} saved).",
        f"- Skipped: {stats['skipped_ext']} non-text/media, {stats['skipped_dm']} DM files.",
        "- Each zip contains a `_batch_manifest.txt` listing its files.",
        "- Media binaries are intentionally excluded (run with `--all` to include everything).",
    ]
    (out_dir / "UPLOAD_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "max_bytes_per_zip": max_bytes,
        "stats": stats,
        "batches": batches,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # flat CSV of every file -> which chunk it landed in
    with (out_dir / "file_map.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["chunk", "zip", "file"])
        for b in batches:
            for rel in b["contents"]:
                wr.writerow([b["seq"], b["zip"], rel])

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare upload-ready second-brain chunks.")
    ap.add_argument("--root", type=Path, default=None,
                    help="folder to scan (default: SOCIAL_BRAIN_ROOT / config.local.json / Downloads working folder)")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB,
                    help=f"max size per zip chunk in MB (default {DEFAULT_MAX_MB})")
    ap.add_argument("--include-dms", action="store_true",
                    help="include Direct Message files (default: excluded)")
    ap.add_argument("--all", action="store_true",
                    help="include ALL file types, media included (default: text only)")
    ap.add_argument("--include-ext", default="",
                    help="comma-separated extra extensions to keep, e.g. .srt,.vtt")
    args = ap.parse_args()

    root = (args.root or data_root()).resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")
    out_dir = root / OUTPUT_DIRNAME
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    if args.all:
        exts = None  # sentinel: keep everything
    else:
        exts = set(TEXT_EXTS)
        for e in args.include_ext.split(","):
            e = e.strip().lower()
            if e:
                exts.add(e if e.startswith(".") else "." + e)

    # when --all, use a permissive matcher
    match_exts = exts if exts is not None else _AllExts()
    max_bytes = int(args.max_mb * 1024 * 1024)

    print(f"Scanning: {root}")
    kept, stats = collect(root, out_dir, match_exts, args.include_dms)
    if not kept:
        print("No files matched — nothing to pack.")
        return
    batches = make_batches(kept, out_dir, max_bytes)
    write_index(out_dir, root, batches, stats, max_bytes)

    print(f"\nDe-duplicated {stats['duplicates']} files ({human(stats['dup_bytes'])} saved).")
    print(f"Packed {sum(b['files'] for b in batches)} files into "
          f"{len(batches)} chunk(s) -> {out_dir}\n")
    for b in batches:
        print(f"  {b['seq']:>2}. {b['zip']:<40} {b['files']:>4} files  {human(b['zip_bytes'])}")
    print(f"\nOpen {out_dir / 'UPLOAD_INDEX.md'} for the ordered upload plan.")


class _AllExts:
    """A set-like object whose 'in' is always True (for --all)."""
    def __contains__(self, _item: object) -> bool:
        return True


if __name__ == "__main__":
    main()
