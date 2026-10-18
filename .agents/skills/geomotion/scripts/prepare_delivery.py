"""Prepare reusable Sites media player assets; publication is a separate Sites step."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from config import DEFAULTS, SKILL_ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("video", type=Path)
    p.add_argument("--stage", choices=["preview", "final"], required=True)
    p.add_argument(
        "--output", type=Path, required=True, help="Site static directory, usually dist"
    )
    p.add_argument("--title", required=True)
    p.add_argument("--category", default="GEOMOTION / VIDEO")
    p.add_argument("--credits", type=Path)
    p.add_argument("--narrated", action="store_true")
    p.add_argument(
        "--revision", help="Optional filename revision; default is content hash"
    )
    a = p.parse_args()
    video = a.video.resolve()
    out = a.output.resolve()
    cfg = DEFAULTS
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    expected = cfg["export"][a.stage]
    num, den = map(int, stream["r_frame_rate"].split("/"))
    if (stream["width"], stream["height"]) != (
        expected["width"],
        expected["height"],
    ) or abs(num / den - expected["fps"]) > 0.01:
        p.error(
            f"{a.stage} requires an already rendered {expected['width']}x{expected['height']} / {expected['fps']}fps input. Never upscale preview footage to final."
        )
    if a.revision and not re.fullmatch("[a-zA-Z0-9_-]+", a.revision):
        p.error("revision must contain only letters, digits, _ or -")
    revision = a.revision
    if not revision:
        h = hashlib.sha256()
        with video.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        revision = h.hexdigest()[:12]
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    for name in ["index.html", "app.js"]:
        shutil.copy2(SKILL_ROOT / "templates/player" / name, out / name)
    qualities = cfg["delivery"][
        "editing_qualities" if a.stage == "preview" else "final_qualities"
    ]
    variants = []
    for width in qualities:
        dest = media / f"{revision}-{width}p.mp4"
        if width == expected["width"]:
            if dest.resolve() != video:
                shutil.copy2(video, dest)
        elif not dest.exists():
            if width != cfg["export"]["preview"]["width"]:
                raise ValueError(
                    "Only 360p preview and native 1080p final are supported by the delivery preset"
                )
            enc = cfg["export"]["preview"]
            fps = enc["fps"]
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-i",
                    str(video),
                    "-vf",
                    f"scale={enc['width']}:{enc['height']},fps={fps}",
                    "-c:v",
                    "libx264",
                    "-preset",
                    enc["preset"],
                    "-crf",
                    str(enc["crf"]),
                    "-maxrate",
                    enc["maxrate"],
                    "-bufsize",
                    enc["bufsize"],
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    enc["audio_bitrate"],
                    "-movflags",
                    "+faststart",
                    str(dest),
                ],
                check=True,
            )
        variants.append(
            {
                "height": width,
                "src": f"media/{dest.name}",
                "bytes": dest.stat().st_size,
                "downloadName": f"geomotion-{revision}-{width}p.mp4",
            }
        )
    poster = media / f"{revision}-poster.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            "0",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            f"scale={cfg['export']['preview']['width']}:{cfg['export']['preview']['height']}",
            str(poster),
        ],
        check=True,
    )
    manifest = {
        "stage": a.stage,
        "title": a.title,
        "category": a.category,
        "duration": float(probe["format"]["duration"]),
        "narrated": a.narrated,
        "poster": f"media/{poster.name}",
        "defaultQuality": cfg["delivery"][
            "default_preview_quality"
            if a.stage == "preview"
            else "default_final_quality"
        ],
        "variants": variants,
    }
    if a.credits:
        shutil.copy2(a.credits, out / "credits.md")
        manifest["credits"] = "credits.md"
    temp = out / "media.json.tmp"
    temp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    temp.replace(out / "media.json")
    print(
        json.dumps(
            {
                "directory": str(out),
                "stage": a.stage,
                "qualities": qualities,
                "publication": "required via Sites tools",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
