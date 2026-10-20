"""Bounded native segment workers, atomic checkpoints and exact frame joins."""

import concurrent.futures
import fcntl
import json
import math
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from config import DEFAULTS, SKILL_ROOT
from project_state import atomic_json, digest, snapshot, fingerprint, load_project
from timeline import resolve_scene


def worker_limit(requested=None):
    cfg = DEFAULTS["execution"]
    cpu = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else os.cpu_count() or 1
    )
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            cpu = min(cpu, max(1, math.floor(int(quota) / int(period))))
    except (OSError, ValueError):
        pass
    available = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    try:
        limit = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if limit != "max":
            used = int(Path("/sys/fs/cgroup/memory.current").read_text())
            available = min(available, max(0, int(limit) - used))
    except (OSError, ValueError):
        pass
    memory = max(
        1,
        int(
            (available / 1024**2 - cfg["memory_reserve_mb"])
            / cfg["estimated_worker_mb"]
        ),
    )
    if requested is not None and requested < 1:
        raise ValueError("workers must be positive")
    return max(1, min(cpu, memory, cfg["max_workers"], requested or cfg["max_workers"]))


@contextmanager
def exclusive(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another process owns this render checkpoint") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def probe(path):
    return json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )


def verify_segment(path, frames, profile):
    data = probe(path)
    videos = [s for s in data["streams"] if s["codec_type"] == "video"]
    if len(videos) != 1 or any(s["codec_type"] == "audio" for s in data["streams"]):
        raise ValueError("Checkpoint must contain exactly one video and no audio")
    v = videos[0]
    a, b = map(int, v["r_frame_rate"].split("/"))
    if (v["width"], v["height"], int(v["nb_read_frames"])) != (
        profile["width"],
        profile["height"],
        frames,
    ) or abs(a / b - profile["fps"]) > 0.001:
        raise ValueError("Checkpoint geometry/frame count mismatch")


def render(
    scene_path,
    mode,
    output,
    checkpoint,
    requested_workers=None,
    final_requested=False,
    runner=None,
):
    """runner is an explicit embedding/test hook, never a provider fallback."""
    if mode == "final" and not final_requested:
        raise ValueError("Final requires an explicit user request")
    scene_path, output, checkpoint = map(
        lambda p: Path(p).resolve(), (scene_path, output, checkpoint)
    )
    state = snapshot(scene_path)
    scene, _ = load_project(scene_path)
    _, timeline = resolve_scene(scene)
    profile = {**DEFAULTS["export"][mode], **scene.get("export", {}).get(mode, {})}
    fps = profile["fps"]
    count = max(1, round(timeline.duration * fps))
    size = max(1, round(DEFAULTS["execution"]["checkpoint_seconds"] * fps))
    ranges = [(start, min(count, start + size)) for start in range(0, count, size)]
    checkpoint.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    identity = fingerprint(state, mode)
    with exclusive(checkpoint / "render.lock"):
        manifest_path = checkpoint / "checkpoint.json"
        manifest = (
            json.loads(manifest_path.read_text())
            if manifest_path.exists()
            else {"version": 1, "fingerprint": identity, "segments": {}}
        )
        if manifest.get("version") != 1:
            raise ValueError("Unsupported checkpoint version")
        if manifest["fingerprint"] != identity:
            raise ValueError(
                "Checkpoint input/profile changed; use a new checkpoint directory"
            )
        atomic_json(manifest_path, manifest)
        pending = []
        for start, stop in ranges:
            key = f"{start}-{stop}"
            file = checkpoint / (key + ".mp4")
            record = manifest["segments"].get(key)
            sidecar = file.with_suffix(".layout.json")
            valid = (
                record
                and file.is_file()
                and digest(file) == record.get("sha256")
                and sidecar.is_file()
                and digest(sidecar) == record.get("layout_sha256")
            )
            if valid:
                try:
                    verify_segment(file, stop - start, profile)
                except (ValueError, subprocess.CalledProcessError, KeyError):
                    valid = False
            if not valid:
                pending.append((start, stop, file))

        def job(item):
            start, stop, file = item
            if runner:
                runner(scene_path, mode, file, start, stop)
            else:
                command = [
                    sys.executable,
                    str(SKILL_ROOT / "scripts/render_scene.py"),
                    str(scene_path),
                    "--mode",
                    mode,
                    "--output",
                    str(file),
                    "--start-frame",
                    str(start),
                    "--end-frame",
                    str(stop),
                    "--video-only",
                ]
                if final_requested:
                    command.append("--final-requested")
                subprocess.run(command, check=True)
            verify_segment(file, stop - start, profile)
            sidecar = file.with_suffix(".layout.json")
            if not sidecar.is_file():
                raise ValueError("Renderer must write layout telemetry")
            return f"{start}-{stop}", {
                "sha256": digest(file),
                "layout_sha256": digest(sidecar),
                "frames": stop - start,
            }

        workers = worker_limit(requested_workers)
        # At most `workers` expensive render processes; failed/completed chunks stay resumable.
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(job, item) for item in pending]
            for future in concurrent.futures.as_completed(futures):
                key, record = future.result()
                manifest["segments"][key] = record
                atomic_json(manifest_path, manifest)
        if snapshot(scene_path) != state:
            raise ValueError(
                "Inputs changed during render; refusing to assemble mixed revisions"
            )
        listing = checkpoint / "concat.txt"
        # Filenames are generated here; arbitrary user paths never enter concat syntax.
        listing.write_text(
            "".join(
                f"file '{a}-{b}.mp4'\nduration {(b-a)/fps:.12f}\n" for a, b in ranges
            )
        )
        temporary = output.with_name(output.stem + ".assembling.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            str(listing),
        ]
        if scene.get("audio"):
            cmd += ["-i", str((scene_path.parent / scene["audio"]).resolve())]
            if (
                scene.get("timeline", {}).get("cuts")
                and scene["timeline"].get("audio_clock", "source") == "source"
            ):
                cmd += [
                    "-filter_complex",
                    timeline.audio_filter(),
                    "-map",
                    "0:v",
                    "-map",
                    "[audio]",
                ]
            else:
                cmd += ["-map", "0:v", "-map", "1:a", "-af", "apad"]
            cmd += ["-c:a", "aac", "-b:a", profile["audio_bitrate"]]
        cmd += [
            "-c:v",
            "copy",
            "-t",
            str(count / fps),
            "-movflags",
            "+faststart",
            str(temporary),
        ]
        subprocess.run(cmd, check=True)
        v = next(s for s in probe(temporary)["streams"] if s["codec_type"] == "video")
        if int(v["nb_read_frames"]) != count:
            raise ValueError("Joined frame count mismatch")
        layout = {}
        composition_frames = []
        for a, b in ranges:
            sidecar = checkpoint / f"{a}-{b}.layout.json"
            if sidecar.exists():
                report = json.loads(sidecar.read_text())
                layout.update(report.get("errors", {}))
                composition_frames.extend(
                    report.get("composition", {}).get("frames", [])
                )
            elif runner is None:
                raise ValueError("Missing segment layout report")
        if snapshot(scene_path) != state:
            raise ValueError(
                "Inputs changed during audio assembly; keeping previous deliverable"
            )
        temporary.replace(output)
        atomic_json(
            output.with_suffix(".layout.json"),
            {"errors": layout, "composition": {"frames": composition_frames}},
        )
        receipt = {
            "fingerprint": identity,
            "sha256": digest(output),
            "frames": count,
            "workers": workers,
            "rendered_segments": len(pending),
            "resumed_segments": len(ranges) - len(pending),
        }
        atomic_json(output.with_suffix(".render.json"), receipt)
        return receipt
