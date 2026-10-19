"""Render an editable title preview; source GIF/AEP is not a runtime dependency."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from config import DEFAULTS
from PIL import Image
from title_layer import render_title, title_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["preview", "final"], default="preview")
    parser.add_argument("--text")
    parser.add_argument("--subtext")
    parser.add_argument("--background", default="#242628")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        parser.error("FFmpeg required")
    overrides = {"content": {}}
    if args.text is not None:
        overrides["content"]["headline"] = args.text
    if args.subtext is not None:
        overrides["content"]["subline"] = args.subtext
    config = title_config(json.loads(args.definition.read_text()), overrides)
    profile = DEFAULTS["export"][args.mode]
    size = (profile["width"], profile["height"])
    fps = profile["fps"]
    background = Image.new("RGBA", size, args.background)
    count = max(1, round(config["duration"] * fps))
    args.output.parent.mkdir(exist_ok=True, parents=True)
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{size[0]}x{size[1]}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        profile["preset"],
        "-crf",
        str(profile["crf"]),
        "-maxrate",
        profile["maxrate"],
        "-bufsize",
        profile["bufsize"],
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(args.output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(count):
            image = background.copy()
            image.alpha_composite(render_title(config, frame / fps, size))
            process.stdin.write(image.convert("RGB").tobytes())
    except BaseException:
        process.stdin.close()
        process.wait()
        args.output.unlink(missing_ok=True)
        raise
    process.stdin.close()
    if process.wait() != 0:
        args.output.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg title render failed")
    moment = min(config["duration"] - 1 / fps, config["timing"]["tilt"][1] + 0.1)
    layer = render_title(config, moment, size)
    layer.save(args.output.with_suffix(".png"))
    background.alpha_composite(layer)
    background.convert("RGB").save(
        args.output.with_name(args.output.stem + "-poster.jpg")
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
