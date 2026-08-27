#!/usr/bin/env python3
"""Upload a rendered video to YouTube via Data API v3.

Read this before using it:

Uploads from an API project that has not passed a compliance audit are locked
to PRIVATE, permanently, regardless of the privacyStatus you send. That is a
YouTube policy for unverified projects created after 28 July 2020, not a bug
here. Lifting it requires submitting the YouTube API Services Audit and Quota
Extension Form and passing review.

So this script defaults to private and refuses to run without --confirm. Private
staging is genuinely useful: upload, review in YouTube Studio, publish by hand.
Treat anything beyond that as blocked until your project is audited.

Dependencies are optional and not installed by default:

    uv pip install google-api-python-client google-auth-oauthlib

Credentials: create an OAuth client (type: Desktop app) in Google Cloud Console
with the YouTube Data API v3 enabled, download the JSON, and pass it via
--client-secrets. The resulting token is cached next to it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VALID_PRIVACY = {"private", "unlisted", "public"}
# Retriable per Google's upload guidance.
RETRIABLE_STATUS = {500, 502, 503, 504}


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_metadata(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("video", "title"):
        if not data.get(key):
            raise ValueError(f"metadata is missing required field {key!r}")
    privacy = data.get("privacyStatus", "private")
    if privacy not in VALID_PRIVACY:
        raise ValueError(f"privacyStatus must be one of {sorted(VALID_PRIVACY)}, got {privacy!r}")
    title = data["title"]
    if len(title) > 100:
        raise ValueError(f"title is {len(title)} chars; YouTube's limit is 100")
    description = data.get("description", "")
    if len(description) > 5000:
        raise ValueError(f"description is {len(description)} chars; YouTube's limit is 5000")
    tags = data.get("tags", [])
    if sum(len(t) for t in tags) > 500:
        raise ValueError("tags exceed YouTube's ~500 character total budget")
    return data


def build_request_body(meta: dict) -> dict:
    return {
        "snippet": {
            "title": meta["title"],
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "categoryId": str(meta.get("categoryId", "28")),
        },
        "status": {
            "privacyStatus": meta.get("privacyStatus", "private"),
            "selfDeclaredMadeForKids": bool(meta.get("selfDeclaredMadeForKids", False)),
            **({"publishAt": meta["publishAt"]} if meta.get("publishAt") else {}),
        },
    }


def get_credentials(client_secrets: Path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = client_secrets.with_name("youtube-token.json")
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        token_path.chmod(0o600)
        log(f"cached token at {token_path} (treat it as a credential; it is gitignored)")
    return creds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("metadata", type=Path, help="path to upload metadata JSON")
    parser.add_argument("--client-secrets", type=Path, help="OAuth client secrets JSON (Desktop app)")
    parser.add_argument("--confirm", action="store_true", help="actually upload; without this it is a dry run")
    parser.add_argument("--allow-public", action="store_true",
                        help="permit privacyStatus other than private (still capped by audit status)")
    args = parser.parse_args()

    if not args.metadata.exists():
        log(f"error: metadata not found: {args.metadata}")
        return 1

    try:
        meta = load_metadata(args.metadata)
    except (ValueError, json.JSONDecodeError) as exc:
        log(f"error: {exc}")
        return 1

    base = args.metadata.parent
    video = base / meta["video"]
    if not video.exists():
        log(f"error: video not found: {video}")
        return 1

    privacy = meta.get("privacyStatus", "private")
    if privacy != "private" and not args.allow_public:
        log(f"error: privacyStatus is {privacy!r}; pass --allow-public to attempt it.")
        log("       Note it will still be forced private unless your project passed a YouTube audit.")
        return 1

    body = build_request_body(meta)
    size_mb = video.stat().st_size / 1_000_000
    log(f"video:   {video} ({size_mb:.1f} MB)")
    log(f"title:   {body['snippet']['title']}")
    log(f"privacy: {privacy}")

    if not args.confirm:
        log("")
        log("dry run: nothing uploaded. Re-run with --confirm to upload.")
        log("Reminder: unaudited projects have every upload locked to private.")
        return 0

    if not args.client_secrets or not args.client_secrets.exists():
        log("error: --client-secrets is required to upload (OAuth client JSON, type: Desktop app)")
        return 1

    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        log("error: upload dependencies are not installed. Run:")
        log("  uv pip install google-api-python-client google-auth-oauthlib")
        return 2

    youtube = build("youtube", "v3", credentials=get_credentials(args.client_secrets))
    media = MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    errors = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                log(f"  uploading... {int(status.progress() * 100)}%")
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS and errors < 5:
                errors += 1
                log(f"  retriable error {exc.resp.status}, retry {errors}/5")
                continue
            log(f"error: upload failed: {exc}")
            return 4

    video_id = response.get("id", "")
    log(f"uploaded: https://youtu.be/{video_id}")
    log(f"status:   {response.get('status', {}).get('privacyStatus')}")

    thumbnail = meta.get("thumbnail")
    if thumbnail and (base / thumbnail).exists():
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(base / thumbnail))).execute()
        log(f"thumbnail set from {thumbnail}")

    log("")
    log("If this shows as private and you expected otherwise, your project has not")
    log("passed a YouTube compliance audit. Publish manually in YouTube Studio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
