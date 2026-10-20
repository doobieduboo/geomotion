"""Checks encoded bytes, timing and layout; does not certify facts or human review."""

import json
import math
import re
import subprocess
from pathlib import Path
from config import DEFAULTS
from execution import probe
from project_state import digest, atomic_json


def audio_measure(path):
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-vn",
            "-af",
            "loudnorm=I="
            + str(DEFAULTS["audio"]["voice_integrated_lufs"])
            + ":TP="
            + str(DEFAULTS["audio"]["final_true_peak_dbtp"])
            + ":print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    matches = re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)
    if not matches:
        raise ValueError("No encoded loudness measurement")
    data = json.loads(matches[-1])
    return {k: float(data[k]) for k in ("input_i", "input_tp", "input_lra")}


def check(
    path, mode, duration=None, narrated=False, voice_end=None, require_layout=False
):
    path = Path(path)
    cfg, limits = DEFAULTS["export"][mode], DEFAULTS["qa"]
    data = probe(path)
    errors, warnings = [], []
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = map(int, video["r_frame_rate"].split("/"))
    if (video["width"], video["height"]) != (cfg["width"], cfg["height"]) or abs(
        num / den - cfg["fps"]
    ) > 0.001:
        errors.append("Encoded dimensions/fps differ from preset")
    if video.get("codec_name") != "h264" or video.get("pix_fmt") != "yuv420p":
        errors.append("Encoded video must be H.264/yuv420p")
    audio_streams = [s for s in data["streams"] if s["codec_type"] == "audio"]
    if any(s.get("codec_name") != "aac" for s in audio_streams):
        errors.append("Encoded audio must be AAC")
    count = int(video["nb_read_frames"])
    if (
        duration is not None
        and abs(count - max(1, round(duration * cfg["fps"])))
        > limits["duration_tolerance_frames"]
    ):
        errors.append("Encoded frame count differs from timeline")
    decode = subprocess.run(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    if decode.returncode or decode.stderr.strip():
        errors.append("Full decode failed: " + decode.stderr[-1000:])
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=best_effort_timestamp_time",
            "-of",
            "json",
            str(path),
        ]
    )
    pts = [float(f["best_effort_timestamp_time"]) for f in json.loads(raw)["frames"]]
    if len(pts) != count or any(
        abs(b - a - 1 / cfg["fps"]) > 0.002 for a, b in zip(pts, pts[1:])
    ):
        errors.append("Nonuniform presentation cadence; inspect segment joins")
    layout = path.with_suffix(".layout.json")
    if layout.exists():
        errors.extend(json.loads(layout.read_text()).get("errors", {}).keys())
    elif require_layout:
        errors.append("Layout telemetry missing")
    audio = any(s["codec_type"] == "audio" for s in data["streams"])
    measured = None
    if narrated and not audio:
        errors.append("Narrated video has no audio")
    if audio:
        measured = audio_measure(path)
        if (
            not math.isfinite(measured["input_tp"])
            or measured["input_tp"] > DEFAULTS["audio"]["final_true_peak_dbtp"]
        ):
            errors.append("Encoded true peak exceeds preset")
        if narrated and (
            not math.isfinite(measured["input_i"])
            or abs(measured["input_i"] - DEFAULTS["audio"]["voice_integrated_lufs"])
            > limits["loudness_tolerance_lu"]
        ):
            errors.append("Encoded integrated loudness differs from preset")
        filt = f"silencedetect=noise={limits['silence_noise_db']}dB:d={limits['silence_min_seconds']}"
        scan = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(path),
                "-vn",
                "-af",
                filt,
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        pauses = re.findall(r"silence_(?:start|end|duration): [\d.]+", scan.stderr)
        if pauses:
            warnings.append(
                {
                    "silence_candidates": pauses,
                    "note": "Review breaths/punctuation; no automatic cuts",
                }
            )
    if (
        voice_end is not None
        and count / cfg["fps"] - voice_end > limits["tail_warning_seconds"]
    ):
        warnings.append("Tail exceeds voice_end allowance; inspect authored fade")
    black = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-vf",
            f"blackdetect=d={limits['black_min_seconds']}",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    intervals = re.findall(r"black_start:[^\n]+", black.stderr)
    if intervals:
        warnings.append(
            {
                "black_intervals": intervals,
                "note": "Review against intentional transitions/fades",
            }
        )
    result = {
        "sha256": digest(path),
        "mode": mode,
        "frames": count,
        "audio": measured,
        "errors": errors,
        "warnings": warnings,
        "automated_pass": not errors,
        "human_review": "required",
    }
    atomic_json(path.with_suffix(".qa.json"), result)
    return result


def contact_sheet(path, destination, times):
    from PIL import Image, ImageDraw
    import io

    frames = []
    for t in times:
        raw = subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(max(0, t)),
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                "scale=180:-1",
                "-f",
                "image2pipe",
                "-vcodec",
                "mjpeg",
                "-",
            ]
        )
        with Image.open(io.BytesIO(raw)) as im:
            frame = im.convert("RGB")
        ImageDraw.Draw(frame).text(
            (4, 4), f"{t:.2f}s", fill="white", stroke_width=1, stroke_fill="black"
        )
        frames.append(frame)
    if not frames:
        raise ValueError("Contact sheet requires sample times")
    width, height = frames[0].size
    sheet = Image.new(
        "RGB", (width * min(4, len(frames)), height * math.ceil(len(frames) / 4))
    )
    for i, frame in enumerate(frames):
        sheet.paste(frame, ((i % 4) * width, (i // 4) * height))
    sheet.save(destination)
