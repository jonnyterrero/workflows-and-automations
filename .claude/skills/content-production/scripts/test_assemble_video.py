#!/usr/bin/env python3
"""Offline tests for assemble_video.

ffmpeg execution is deliberately not exercised: the environment that renders
video is not always the one that runs tests, and the failure modes worth
catching are in validation and command construction, both of which are pure.

Run: python3 .claude/skills/content-production/scripts/test_assemble_video.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import assemble_video as av  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "assemble_video.py"

failures: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        failures.append(f"{label}: got {got!r}, want {want!r}")
    else:
        print(f"ok   {label}")


def check_raises(label: str, manifest: dict, fragment: str) -> None:
    try:
        av.validate_manifest(manifest)
    except av.ManifestError as exc:
        if fragment.lower() in str(exc).lower():
            print(f"ok   {label}")
        else:
            failures.append(f"{label}: message {str(exc)!r} lacks {fragment!r}")
        return
    failures.append(f"{label}: expected ManifestError, none raised")


def good_manifest() -> dict:
    return {
        "version": 1,
        "aspect": "9:16",
        "fps": 30,
        "scenes": [
            {"id": "s1", "clip": "assets/a.mp4", "duration": 4.5},
            {"id": "s2", "clip": "assets/b.mp4", "duration": 3.5},
        ],
        "audio": {"narration": "assets/vo.mp3"},
        "subtitles": {"file": "assets/cap.srt", "burn": True},
        "output": "final.mp4",
    }


def main() -> int:
    # --- validation accepts a good manifest ---
    av.validate_manifest(good_manifest())
    print("ok   accepts a valid manifest")

    # --- validation rejects each way a manifest can be wrong ---
    m = good_manifest(); m["version"] = 2
    check_raises("rejects wrong version", m, "version")
    m = good_manifest(); m["aspect"] = "4:3"
    check_raises("rejects unknown aspect", m, "aspect")
    m = good_manifest(); m["fps"] = 500
    check_raises("rejects out-of-range fps", m, "fps")
    m = good_manifest(); m["scenes"] = []
    check_raises("rejects empty scenes", m, "scenes")
    m = good_manifest(); del m["scenes"][0]["clip"]
    check_raises("rejects scene without clip", m, "clip")
    m = good_manifest(); m["scenes"][0]["duration"] = 0
    check_raises("rejects zero duration", m, "duration")
    m = good_manifest(); m["scenes"][0]["duration"] = "4.5"
    check_raises("rejects string duration", m, "duration")
    m = good_manifest(); m["scenes"][1]["id"] = "s1"
    check_raises("rejects duplicate scene id", m, "duplicate")
    m = good_manifest(); m["audio"] = {}
    check_raises("rejects missing narration", m, "narration")
    m = good_manifest(); m["subtitles"] = {"file": "cap.txt"}
    check_raises("rejects bad subtitle extension", m, "subtitle")
    m = good_manifest(); del m["output"]
    check_raises("rejects missing output", m, "output")

    # --- duration and asset accounting ---
    check("sums scene durations", av.total_duration(good_manifest()), 8.0)
    check("collects every asset path", len(av.asset_paths(good_manifest())), 4)
    m = good_manifest(); m["audio"]["music"] = "assets/bed.mp3"
    check("counts music as an asset", len(av.asset_paths(m)), 5)

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        check("reports all assets missing", len(av.missing_assets(good_manifest(), base)), 4)
        (base / "assets").mkdir()
        (base / "assets" / "a.mp4").write_bytes(b"")
        check("reports remaining missing", len(av.missing_assets(good_manifest(), base)), 3)

    # --- command construction ---
    base = Path("/run")
    work = Path("/run/.work")
    m = good_manifest()

    norm = av.normalize_cmd(m["scenes"][0], m, base, work / "norm-000.mp4")
    check("normalize targets portrait size", "scale=1080:1920" in " ".join(norm), True)
    check("normalize pads to frame", "pad=1080:1920" in " ".join(norm), True)
    check("normalize trims to duration", norm[norm.index("-t") + 1], "4.5")
    check("normalize drops clip audio", "-an" in norm, True)

    m169 = good_manifest(); m169["aspect"] = "16:9"
    check(
        "landscape uses 1920x1080",
        "scale=1920:1080" in " ".join(av.normalize_cmd(m169["scenes"][0], m169, base, work / "n.mp4")),
        True,
    )

    # Muxing: narration only.
    mux = av.mux_cmd(work / "silent.mp4", m, base, base / "final.mp4")
    joined = " ".join(mux)
    check("burns subtitles by default", "subtitles=" in joined, True)
    check("re-encodes video when burning subs", "libx264" in joined, True)
    check("encodes aac audio", "-c:a" in mux and mux[mux.index("-c:a") + 1] == "aac", True)
    check("uses -shortest", "-shortest" in mux, True)

    # Muxing: with a music bed.
    m_music = good_manifest(); m_music["audio"]["music"] = "assets/bed.mp3"
    joined = " ".join(av.mux_cmd(work / "s.mp4", m_music, base, base / "o.mp4"))
    check("mixes music bed", "amix=inputs=2" in joined, True)
    check("ducks music by default gain", "volume=-22dB" in joined, True)

    m_music["audio"]["music_gain_db"] = -30
    check(
        "respects custom music gain",
        "volume=-30dB" in " ".join(av.mux_cmd(work / "s.mp4", m_music, base, base / "o.mp4")),
        True,
    )

    # Muxing: subtitles off means the video stream is copied, not re-encoded.
    m_nosub = good_manifest(); m_nosub["subtitles"] = {"file": "assets/cap.srt", "burn": False}
    joined = " ".join(av.mux_cmd(work / "s.mp4", m_nosub, base, base / "o.mp4"))
    check("copies video when not burning", "-c:v copy" in joined, True)
    check("no subtitle filter when burn is false", "subtitles=" not in joined, True)

    # .ass subtitles use the ass filter, which carries its own styling.
    check("ass files use the ass filter", av.subtitle_filter(Path("/r/c.ass"), None).startswith("ass="), True)
    check("srt files use the subtitles filter", av.subtitle_filter(Path("/r/c.srt"), None).startswith("subtitles="), True)
    check(
        "force_style applied to srt",
        "force_style='Fontsize=42'" in av.subtitle_filter(Path("/r/c.srt"), "Fontsize=42"),
        True,
    )
    check("colons escaped for ffmpeg", r"\:" in av.subtitle_filter(Path("C:/r/c.srt"), None), True)

    # --- plan shape ---
    plan = av.build_plan(good_manifest(), base, work)
    check("plan is normalize-per-scene plus concat plus mux", len(plan), 4)
    check("plan ends with mux", plan[-1][0], "mux audio + subtitles")
    check("plan concat is second to last", plan[-2][0], "concat scenes")

    # --- concat list points at normalized clips ---
    with tempfile.TemporaryDirectory() as tmp:
        work_real = Path(tmp)
        list_file = av.write_concat_list(good_manifest(), work_real)
        lines = list_file.read_text().strip().splitlines()
        check("concat list has one line per scene", len(lines), 2)
        check("concat list references normalized clips", lines[0].endswith("norm-000.mp4'"), True)

    # --- CLI end to end, without ffmpeg ---
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp)
        (run / "manifest.json").write_text(json.dumps(good_manifest()), encoding="utf-8")

        proc = subprocess.run([sys.executable, str(SCRIPT), str(run / "manifest.json"), "--dry-run"],
                              capture_output=True, text=True)
        check("dry run exits 0 without ffmpeg", proc.returncode, 0)
        check("dry run emits ffmpeg commands", proc.stdout.count("ffmpeg"), 4)
        check("dry run executes nothing", (run / "final.mp4").exists(), False)

        # --check must fail when assets are absent.
        proc = subprocess.run([sys.executable, str(SCRIPT), str(run / "manifest.json"), "--check"],
                              capture_output=True, text=True)
        check("check fails on missing assets", proc.returncode, 1)
        check("check names the missing file", "assets/vo.mp3" in proc.stderr, True)

        # A malformed manifest fails before any ffmpeg work.
        (run / "bad.json").write_text("{not json", encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPT), str(run / "bad.json")],
                              capture_output=True, text=True)
        check("invalid JSON exits 1", proc.returncode, 1)
        check("invalid JSON explains itself", "not valid JSON" in proc.stderr, True)

        proc = subprocess.run([sys.executable, str(SCRIPT), str(run / "nope.json")],
                              capture_output=True, text=True)
        check("missing manifest exits 1", proc.returncode, 1)

    # --- shipped example manifest must stay valid ---
    example = SCRIPT.resolve().parents[1] / "templates" / "manifest.example.json"
    if example.exists():
        av.validate_manifest(json.loads(example.read_text(encoding="utf-8")))
        print("ok   shipped example manifest validates")
    else:
        failures.append(f"example manifest missing at {example}")

    print()
    if failures:
        print(f"FAILED ({len(failures)})")
        for line in failures:
            print(f"  {line}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
