#!/usr/bin/env python3
"""Assemble a finished video from a run manifest using ffmpeg.

The model-driven half of the pipeline (script, narration, visuals) writes assets
into a run directory plus a manifest.json describing how they fit together. This
script is the deterministic half: it turns that manifest into a single rendered
file and never calls a paid API.

Pipeline, following the shape used by MoneyPrinterTurbo and AI-Content-Studio:

    normalize each scene clip  ->  concat  ->  mix audio + burn subtitles

Scene clip audio is dropped by design; narration is the voice track and music is
an optional bed. Run with --dry-run to print the exact ffmpeg commands without
executing them, which also works where ffmpeg is not installed.
"""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Portrait/landscape/square targets, matching the conventions these pipelines use.
ASPECTS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}
SUBTITLE_SUFFIXES = {".srt", ".ass", ".vtt"}
VIDEO_CODEC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]


class ManifestError(ValueError):
    """Manifest is structurally invalid. Message is written for a human."""


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path} is not valid JSON: {exc}") from exc
    validate_manifest(data)
    return data


def validate_manifest(m: dict) -> None:
    """Fail loudly and specifically. A bad manifest should never reach ffmpeg."""
    if m.get("version") != 1:
        raise ManifestError(f"unsupported manifest version {m.get('version')!r}; expected 1")

    aspect = m.get("aspect", "16:9")
    if aspect not in ASPECTS:
        raise ManifestError(f"aspect {aspect!r} not one of {sorted(ASPECTS)}")

    fps = m.get("fps", 30)
    if not isinstance(fps, int) or not 1 <= fps <= 120:
        raise ManifestError(f"fps must be an int in 1..120, got {fps!r}")

    scenes = m.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ManifestError("manifest needs a non-empty 'scenes' list")

    seen_ids = set()
    for i, scene in enumerate(scenes):
        where = f"scenes[{i}]"
        if not isinstance(scene, dict):
            raise ManifestError(f"{where} must be an object")
        if not scene.get("clip"):
            raise ManifestError(f"{where} is missing 'clip'")
        duration = scene.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ManifestError(f"{where} needs a positive numeric 'duration', got {duration!r}")
        scene_id = scene.get("id") or f"s{i + 1}"
        if scene_id in seen_ids:
            raise ManifestError(f"{where} has duplicate id {scene_id!r}")
        seen_ids.add(scene_id)

    audio = m.get("audio") or {}
    if not isinstance(audio, dict):
        raise ManifestError("'audio' must be an object")
    if not audio.get("narration"):
        raise ManifestError("audio.narration is required; generate it before assembling")

    subs = m.get("subtitles") or {}
    sub_file = subs.get("file")
    if sub_file and Path(sub_file).suffix.lower() not in SUBTITLE_SUFFIXES:
        raise ManifestError(f"subtitle file must be one of {sorted(SUBTITLE_SUFFIXES)}, got {sub_file!r}")

    if not m.get("output"):
        raise ManifestError("manifest is missing 'output'")


def asset_paths(m: dict) -> list[str]:
    """Every input file the manifest references, in declaration order."""
    paths = [scene["clip"] for scene in m["scenes"]]
    audio = m.get("audio") or {}
    paths.extend(p for p in (audio.get("narration"), audio.get("music")) if p)
    subs = m.get("subtitles") or {}
    if subs.get("file"):
        paths.append(subs["file"])
    return paths


def missing_assets(m: dict, base: Path) -> list[str]:
    return [p for p in asset_paths(m) if not (base / p).exists()]


def total_duration(m: dict) -> float:
    return round(sum(float(s["duration"]) for s in m["scenes"]), 3)


def probe_duration(path: Path) -> float | None:
    """Media duration in seconds via ffprobe, or None if it cannot be determined."""
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def check_narration_fit(m: dict, base: Path) -> str | None:
    """Warn when narration outruns the scenes: -shortest would truncate the voice."""
    narration = base / (m.get("audio") or {})["narration"]
    if not narration.exists():
        return None
    spoken = probe_duration(narration)
    if spoken is None:
        return None
    visual = total_duration(m)
    if spoken > visual + 0.25:
        return (
            f"narration is {spoken:.1f}s but scenes total {visual:.1f}s; "
            f"the last {spoken - visual:.1f}s of voiceover would be cut. "
            f"Add {spoken - visual:.1f}s of scene duration."
        )
    return None


def normalize_cmd(scene: dict, m: dict, base: Path, dest: Path) -> list[str]:
    """Scale to fit, pad to exact frame, fix fps, trim to duration, drop audio."""
    width, height = ASPECTS[m.get("aspect", "16:9")]
    fps = m.get("fps", 30)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={fps},setsar=1"
    )
    return [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(base / scene["clip"]),
        "-t", str(scene["duration"]),
        "-vf", vf,
        "-an",
        *VIDEO_CODEC,
        str(dest),
    ]


def concat_cmd(list_file: Path, dest: Path) -> list[str]:
    return [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy",
        str(dest),
    ]


def subtitle_filter(sub_path: Path, style: str | None) -> str:
    """.ass carries its own styling; .srt/.vtt take force_style."""
    escaped = str(sub_path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    if sub_path.suffix.lower() == ".ass":
        return f"ass='{escaped}'"
    if style:
        return f"subtitles='{escaped}':force_style='{style}'"
    return f"subtitles='{escaped}'"


def mux_cmd(video: Path, m: dict, base: Path, dest: Path) -> list[str]:
    """Attach narration, optionally duck a music bed under it, burn subtitles."""
    audio = m.get("audio") or {}
    subs = m.get("subtitles") or {}
    music = audio.get("music")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video)]
    cmd += ["-i", str(base / audio["narration"])]
    if music:
        cmd += ["-i", str(base / music)]

    filters = []
    if music:
        gain = audio.get("music_gain_db", -22)
        filters.append(
            f"[2:a]volume={gain}dB[bed];"
            f"[1:a][bed]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = "1:a"

    burn = subs.get("burn", True) and subs.get("file")
    if burn:
        filters.append(f"[0:v]{subtitle_filter(base / subs['file'], subs.get('style'))}[vout]")
        video_map = "[vout]"
    else:
        video_map = "0:v"

    if filters:
        cmd += ["-filter_complex", ";".join(filters)]
    cmd += ["-map", video_map, "-map", audio_map]
    # Re-encode video only when a filter touched it.
    cmd += VIDEO_CODEC if burn else ["-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", str(dest)]
    return cmd


def build_plan(m: dict, base: Path, workdir: Path) -> list[tuple[str, list[str]]]:
    """The full ordered command plan. Pure: builds commands, runs nothing."""
    plan: list[tuple[str, list[str]]] = []
    normalized = []

    for i, scene in enumerate(m["scenes"]):
        dest = workdir / f"norm-{i:03d}.mp4"
        normalized.append(dest)
        plan.append((f"normalize {scene.get('id', f's{i + 1}')}", normalize_cmd(scene, m, base, dest)))

    list_file = workdir / "concat.txt"
    silent = workdir / "silent.mp4"
    plan.append(("concat scenes", concat_cmd(list_file, silent)))
    plan.append(("mux audio + subtitles", mux_cmd(silent, m, base, base / m["output"])))
    return plan


def write_concat_list(m: dict, workdir: Path) -> Path:
    list_file = workdir / "concat.txt"
    lines = [f"file '{(workdir / f'norm-{i:03d}.mp4').as_posix()}'" for i in range(len(m["scenes"]))]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return list_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="path to manifest.json")
    parser.add_argument("--check", action="store_true", help="validate the manifest and assets, then exit")
    parser.add_argument("--dry-run", action="store_true", help="print ffmpeg commands without running them")
    parser.add_argument("--workdir", type=Path, help="scratch dir for intermediates (default: <run>/.work)")
    parser.add_argument("--keep-workdir", action="store_true", help="do not delete intermediates on success")
    args = parser.parse_args()

    if not args.manifest.exists():
        log(f"error: manifest not found: {args.manifest}")
        return 1

    try:
        manifest = load_manifest(args.manifest)
    except ManifestError as exc:
        log(f"error: {exc}")
        return 1

    base = args.manifest.parent.resolve()
    workdir = (args.workdir or base / ".work").resolve()

    scenes = len(manifest["scenes"])
    log(f"manifest ok: {scenes} scenes, {total_duration(manifest)}s, {manifest.get('aspect', '16:9')}")

    missing = missing_assets(manifest, base)
    if args.check:
        if missing:
            log(f"error: {len(missing)} missing asset(s):")
            for path in missing:
                log(f"  {path}")
            return 1
        warning = check_narration_fit(manifest, base)
        if warning:
            log(f"warning: {warning}")
        log("all assets present")
        return 0

    if missing and not args.dry_run:
        log(f"error: {len(missing)} missing asset(s); generate them before assembling:")
        for path in missing:
            log(f"  {path}")
        return 1

    if not args.dry_run:
        warning = check_narration_fit(manifest, base)
        if warning:
            log(f"warning: {warning}")

    workdir.mkdir(parents=True, exist_ok=True)
    plan = build_plan(manifest, base, workdir)

    if args.dry_run:
        for label, cmd in plan:
            print(f"# {label}")
            print(shlex.join(cmd))
        log(f"dry run: {len(plan)} commands, nothing executed")
        return 0

    if not shutil.which("ffmpeg"):
        log("error: ffmpeg not found on PATH. Install it, or use --dry-run to inspect the commands.")
        return 3

    for i, (label, cmd) in enumerate(plan, start=1):
        # The concat list references normalized clips, so it is written after they exist.
        if label == "concat scenes":
            write_concat_list(manifest, workdir)
        log(f"[{i}/{len(plan)}] {label}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"error: ffmpeg failed during '{label}' (exit {result.returncode})")
            log(result.stderr.strip()[:2000])
            log(f"intermediates left in {workdir}")
            return 4

    if not args.keep_workdir:
        shutil.rmtree(workdir, ignore_errors=True)

    out = base / manifest["output"]
    size_mb = out.stat().st_size / 1_000_000 if out.exists() else 0
    log(f"wrote {out} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
