"""Add supplied screen-space PNG/atlas layers to verified native checkpoints.

Version 1 requires an execution.py base checkpoint and its matching .render.json.
Positions are native-pixel top-left coordinates, including atlas frames (anchors
are deliberately unused). Geographic positioning and camera effects belong to
supplied assets/the original renderer. No scene rendering or network requests.
"""
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from PIL import Image
from config import DEFAULTS
from execution import exclusive, probe, verify_segment
from layout import callout_opacity
from map_assets import select_sprite
from project_state import atomic_json, digest


def _identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _packets(path, selector):
    result = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", selector, "-show_packets",
        "-show_streams", "-show_data_hash", "sha256", "-of", "json", str(path),
    ]))
    streams = {s["index"]: s for s in result.get("streams", [])}
    records = []
    for p in result.get("packets", []):
        stream = streams[p["stream_index"]]
        clock = Fraction(stream["time_base"])
        records.append({
            "stream": p["stream_index"], "hash": p["data_hash"],
            **{k: str(int(p[k]) * clock) if k in p else None for k in ("pts", "dts", "duration")},
            "flags": p.get("flags"), "side_data": p.get("side_data_list", []),
        })
    return records


def _video_packets(path, fps, offset=0):
    result = []
    for p in _packets(path, "v:0"):
        frame = Fraction(p["pts"]) * fps
        if abs(float(frame) - round(frame)) > .001:
            raise ValueError("Base video has non-native frame timestamps")
        result.append([round(frame) + offset, p["hash"]])
    return result


def _audio_packets(path):
    # Stream indexes change when mapping; local audio stream order is unchanged.
    records = _packets(path, "a")
    indexes = {value: n for n, value in enumerate(sorted({p["stream"] for p in records}))}
    for p in records:
        p["stream"] = indexes[p["stream"]]
    return records


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _pair(value, name):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain two integer pixels")
    if any(_number(v, name) != int(v) for v in value):
        raise ValueError(f"{name} must contain integer pixels")
    return tuple(map(int, value))


def _profile(path, profile, frames=None):
    streams = probe(path)["streams"]
    video = [s for s in streams if s["codec_type"] == "video"]
    if len(video) != 1:
        raise ValueError("Expected exactly one native video stream")
    v = video[0]
    count = int(v["nb_read_frames"])
    if (v["width"], v["height"], Fraction(v["r_frame_rate"]), v["codec_name"], v.get("pix_fmt")) != (
        profile["width"], profile["height"], profile["fps"], "h264", "yuv420p"
    ) or (frames is not None and frames != count):
        raise ValueError("Native profile/frame count mismatch; preview upscaling is unsupported")
    return count


def _load(recipe_path, mode):
    if mode not in ("preview", "final"):
        raise ValueError("mode must be preview or final")
    recipe_path = Path(recipe_path).resolve()
    recipe = json.loads(recipe_path.read_text())
    if recipe.get("version") != 1 or set(recipe) - {"version", "base_video", "base_checkpoint", "overlays"}:
        raise ValueError("Unsupported composite recipe; expected version 1")
    if not recipe.get("base_checkpoint"):
        raise ValueError("Composite v1 requires base_checkpoint and matching base .render.json")
    root = recipe_path.parent
    base = (root / recipe["base_video"]).resolve()
    checkpoint = (root / recipe["base_checkpoint"]).resolve()
    profile = dict(DEFAULTS["export"][mode])
    frames = _profile(base, profile)
    fps = profile["fps"]
    manifest_path = checkpoint / "checkpoint.json"
    receipt_path = base.with_suffix(".render.json")
    manifest = json.loads(manifest_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    base_hash = digest(base)
    if (manifest.get("version") != 1 or not manifest.get("fingerprint")
        or receipt.get("fingerprint") != manifest["fingerprint"]
        or receipt.get("sha256") != base_hash or receipt.get("frames") != frames):
        raise ValueError("Base render receipt/checkpoint identity mismatch")
    chunks = []
    expected = 0
    records = manifest.get("segments", {})
    try:
        ordered = sorted(records, key=lambda key: int(key.split("-")[0]))
        for key in ordered:
            a, b = map(int, key.split("-"))
            record = records[key]
            source = checkpoint / f"{a}-{b}.mp4"
            if key != f"{a}-{b}" or a != expected or b <= a or b > frames:
                raise ValueError("Base checkpoint ranges must cover the native timeline exactly")
            if record.get("frames") != b-a or digest(source) != record.get("sha256"):
                raise ValueError("Base checkpoint segment hash/frame record mismatch")
            verify_segment(source, b-a, profile)
            packets = _video_packets(source, fps, a)
            if sorted(p[0] for p in packets) != list(range(a, b)):
                raise ValueError("Checkpoint segment packet cadence mismatch")
            chunks.append({"start": a, "stop": b, "source": str(source), "sha256": record["sha256"]})
            expected = b
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed base checkpoint") from exc
    base_packets = _video_packets(base, fps)
    # The concat demuxer inserts SPS/PPS NALs at MP4 GOP boundaries. Compare
    # identically remuxed packets rather than claiming raw chunk hashes alone
    # prove source binding (or stripping codec data out of that comparison).
    with tempfile.TemporaryDirectory(prefix="geomotion-bind-") as temporary:
        directory = Path(temporary)
        for n, chunk in enumerate(chunks):
            (directory / f"{n}.mp4").symlink_to(chunk["source"])
        listing = directory / "concat.txt"
        listing.write_text("".join(f"file '{n}.mp4'\nduration {(c['stop']-c['start'])/fps:.12f}\n" for n, c in enumerate(chunks)))
        reference = directory / "bound.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-copyts", "-f", "concat", "-safe", "1", "-i", str(listing), "-map", "0:v:0", "-c", "copy", "-avoid_negative_ts", "disabled", str(reference)], check=True)
        combined = _video_packets(reference, fps)
    if expected != frames or combined != base_packets:
        raise ValueError("Checkpoint encoded packets do not correspond to base video")
    overlays = []
    allowed = {"image", "atlas", "atlas_metadata", "start", "end", "position", "size", "fade_in", "fade_out", "world_heading_deg", "camera_heading_deg"}
    if not isinstance(recipe.get("overlays"), list):
        raise ValueError("overlays must be an array")
    assets = {}
    for item in recipe["overlays"]:
        if not isinstance(item, dict) or set(item) - allowed or ("image" in item) == ("atlas" in item):
            raise ValueError("Each overlay requires exactly one image or atlas")
        item = dict(item)
        for k in ("start", "end"):
            _number(item.get(k), k)
        if not 0 <= item["start"] < item["end"] <= frames/fps:
            raise ValueError("Overlay interval must fit the base video")
        for k in ("fade_in", "fade_out", "world_heading_deg", "camera_heading_deg"):
            _number(item.get(k, 0), k)
        callout_opacity(item, item["start"])
        kind = "image" if "image" in item else "atlas"
        path = (root / item[kind]).resolve()
        assets[str(path)] = digest(path)
        with Image.open(path) as opened:
            if opened.format != "PNG":
                raise ValueError("Composite overlays must be supplied PNG files")
            image = opened.convert("RGBA")
        item[kind] = str(path)
        if kind == "atlas":
            metadata = item.get("atlas_metadata")
            if isinstance(metadata, str):
                metadata_path = (root / metadata).resolve()
                assets[str(metadata_path)] = digest(metadata_path)
                metadata = json.loads(metadata_path.read_text())
            if not isinstance(metadata, dict):
                raise ValueError("Atlas requires atlas_metadata object or local JSON path")
            item["atlas_metadata"] = metadata
            sample, _, _ = select_sprite(image, metadata, item.get("world_heading_deg", 0), item.get("camera_heading_deg", 0))
        else:
            if "atlas_metadata" in item:
                raise ValueError("atlas_metadata requires atlas")
            sample = image
        size = _pair(item.get("size", list(sample.size)), "size")
        position = _pair(item.get("position"), "position")
        if (min(size) <= 0 or min(position) < 0 or position[0]+size[0] > profile["width"]
            or position[1]+size[1] > profile["height"]):
            raise ValueError("Overlay bounds would require clipping")
        item.update(position=position, size=size)
        overlays.append({"item": item, "image": image, "sha256": assets[str(path)]})
    source = {
        "recipe": str(recipe_path), "recipe_sha256": digest(recipe_path),
        "base_video": str(base), "base_sha256": base_hash,
        "base_checkpoint": str(checkpoint), "checkpoint_sha256": digest(manifest_path),
        "base_render_receipt_sha256": digest(receipt_path), "base_fingerprint": manifest["fingerprint"],
        "video_packet_identity": _identity(base_packets), "assets": assets,
    }
    return source, profile, frames, chunks, overlays, base_packets


def _active(overlay, a, b, fps):
    item = overlay["item"]
    return max(a, math.ceil(item["start"]*fps)) < min(b, math.ceil(item["end"]*fps))


def plan(recipe_path, mode="final"):
    """Validate source proof and native bounds without encoding or fetching maps."""
    source, profile, frames, chunks, overlays, _ = _load(recipe_path, mode)
    ranges = {"composited_ranges": [], "copied_ranges": []}
    for chunk in chunks:
        key = "composited_ranges" if any(_active(o, chunk["start"], chunk["stop"], profile["fps"]) for o in overlays) else "copied_ranges"
        ranges[key].append([chunk["start"], chunk["stop"]])
    return {"version": 1, "source": source, "mode": mode, "profile": profile, "frames": frames,
            "basemap_requests": 0, "scene_renders": 0, **ranges}


def _encode(source, target, a, b, overlays, cfg):
    w, h, fps = cfg["width"], cfg["height"], cfg["fps"]
    decoder = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(source), "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    command = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", cfg["preset"], "-crf", str(cfg["crf"]), "-maxrate", cfg["maxrate"], "-bufsize", cfg["bufsize"], "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for n in range(a, b):
            raw = decoder.stdout.read(w*h*3)
            if len(raw) != w*h*3:
                raise ValueError("Incomplete source checkpoint frame")
            frame = None
            for overlay in overlays:
                item = overlay["item"]
                alpha = callout_opacity(item, n/fps)
                if alpha <= 0:
                    continue
                if frame is None:
                    frame = Image.frombytes("RGB", (w, h), raw).convert("RGBA")
                image = overlay["image"]
                if "atlas" in item:
                    image, _, _ = select_sprite(image, item["atlas_metadata"], item.get("world_heading_deg", 0), item.get("camera_heading_deg", 0), n/fps-item["start"])
                image = image.resize(item["size"], Image.Resampling.LANCZOS)
                if alpha < 1:
                    image = image.copy()
                    image.putalpha(image.getchannel("A").point(lambda value: round(value*alpha)))
                frame.alpha_composite(image, item["position"])
            encoder.stdin.write(frame.convert("RGB").tobytes() if frame is not None else raw)
        encoder.stdin.close()
        decoder.stdout.close()
        if decoder.wait() or encoder.wait():
            raise ValueError("Composite FFmpeg process failed")
    except BaseException:
        for process in (decoder, encoder):
            process.kill()
            process.wait()
        raise
    verify_segment(target, b-a, cfg)


def composite(recipe_path, output, checkpoint, mode="final", final_requested=False):
    """Atomically produce an additive revision; resume only compatible changed GOPs."""
    if mode == "final" and not final_requested:
        raise ValueError("Final requires an explicit user request")
    source, cfg, frames, chunks, overlays, base_packets = _load(recipe_path, mode)
    output, checkpoint = Path(output).resolve(), Path(checkpoint).resolve()
    base = Path(source["base_video"])
    protected = {base, Path(source["recipe"]), base.with_suffix(".render.json"),
                 Path(source["base_checkpoint"])/"checkpoint.json",
                 *(Path(c["source"]) for c in chunks), *(Path(p) for p in source["assets"])}
    generated = {checkpoint / f"{c['start']}-{c['stop']}{suffix}"
                 for c in chunks for suffix in (".mp4", ".compositing.mp4")}
    generated.update(checkpoint / name for name in ("concat.txt", "composite.lock", "composite-checkpoint.json"))
    output_paths = {output, output.with_name(output.stem + ".compositing.mp4"),
                    output.with_suffix(".composite.json"), output.with_name(output.stem + ".compositing.json")}
    if (output_paths & protected or output_paths & generated or generated & protected
        or checkpoint == Path(source["base_checkpoint"])):
        raise ValueError("Keep clean base video/checkpoints/assets separate from composite outputs")
    output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.mkdir(parents=True, exist_ok=True)
    code = {name: digest(Path(__file__).with_name(name)) for name in ("compositor.py", "layout.py", "map_assets.py")}
    audio = _audio_packets(base)
    # MP4's default 1000 Hz movie clock rounds nonzero audio edit-list offsets.
    # Retain an exact common clock for all original audio packet timestamps.
    movie_clock = math.lcm(cfg["fps"], *(Fraction(p[k]).denominator for p in audio
                           for k in ("pts", "dts", "duration") if p[k] is not None))
    if movie_clock > 2147483647:
        raise ValueError("Original audio clock cannot be represented exactly in MP4")
    with exclusive(checkpoint / "composite.lock"):
        manifest_path = checkpoint / "composite-checkpoint.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"version": 1, "segments": {}}
        if manifest.get("version") != 1:
            raise ValueError("Unsupported composite checkpoint version")
        reused, changed, copied = [], [], []
        for chunk in chunks:
            a, b = chunk["start"], chunk["stop"]
            key = f"{a}-{b}"
            active = [o for o in overlays if _active(o, a, b, cfg["fps"])]
            identity = _identity({"base": source["base_sha256"], "chunk": chunk["sha256"], "profile": cfg, "code": code,
                                  "overlays": [{"item": o["item"], "sha256": o["sha256"]} for o in active]})
            target = checkpoint / (key + ".mp4")
            previous = manifest["segments"].get(key, {})
            valid = previous.get("identity") == identity and target.is_file() and digest(target) == previous.get("sha256")
            if valid:
                try:
                    verify_segment(target, b-a, cfg)
                except (ValueError, KeyError, subprocess.CalledProcessError):
                    valid = False
            if valid:
                reused.append([a, b])
            else:
                temporary = target.with_name(key + ".compositing.mp4")
                temporary.unlink(missing_ok=True)
                if active:
                    _encode(chunk["source"], temporary, a, b, active, cfg)
                else:
                    shutil.copy2(chunk["source"], temporary)
                temporary.replace(target)
                manifest["segments"][key] = {"identity": identity, "sha256": digest(target), "frames": b-a, "source_sha256": chunk["sha256"]}
                atomic_json(manifest_path, manifest)
            (changed if active else copied).append([a, b])
        listing = checkpoint / "concat.txt"
        listing.write_text("".join(f"file '{c['start']}-{c['stop']}.mp4'\nduration {(c['stop']-c['start'])/cfg['fps']:.12f}\n" for c in chunks))
        temporary = output.with_name(output.stem + ".compositing.mp4")
        try:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-copyts", "-f", "concat", "-safe", "1", "-i", str(listing), "-i", str(base), "-map", "0:v:0", "-map", "1:a?", "-c", "copy", "-avoid_negative_ts", "disabled", "-movie_timescale", str(movie_clock), "-movflags", "+faststart", str(temporary)], check=True)
            _profile(temporary, cfg, frames)
            output_packets = _video_packets(temporary, cfg["fps"])
            if sorted(p[0] for p in output_packets) != list(range(frames)):
                raise ValueError("Composite output timestamp cadence mismatch")
            unaffected = lambda records: [p for p in records if any(a <= p[0] < b for a, b in copied)]
            if unaffected(output_packets) != unaffected(base_packets):
                raise ValueError("Unchanged video packet identity mismatch")
            if _audio_packets(temporary) != audio:
                raise ValueError("Original audio packet data/timestamps changed")
            subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(temporary), "-f", "null", "-"], check=True)
            # Detect source edits during decoding/assembly before promoting anything.
            paths = {source["recipe"]: source["recipe_sha256"], str(base): source["base_sha256"], **source["assets"],
                     str(Path(source["base_checkpoint"])/"checkpoint.json"): source["checkpoint_sha256"],
                     str(base.with_suffix(".render.json")): source["base_render_receipt_sha256"],
                     **{c["source"]: c["sha256"] for c in chunks}}
            if any(digest(path) != sha for path, sha in paths.items()):
                raise ValueError("Composite sources changed during execution")
            receipt = {"version": 1, "kind": "native_overlay_composite", "source": source, "code": code,
                       "profile": cfg, "mode": mode, "frames": frames, "sha256": digest(temporary),
                       "composited_ranges": changed, "copied_ranges": copied, "resumed_ranges": reused,
                       "audio_packets_sha256": _identity(audio), "audio_packet_count": len(audio),
                       "audio_data_and_timestamps_identical": True, "unchanged_video_packets_identical": True,
                       "basemap_requests": 0, "scene_renders": 0, "segments": {f"{c['start']}-{c['stop']}": manifest["segments"][f"{c['start']}-{c['stop']}"] for c in chunks}}
            staged_receipt = output.with_name(output.stem + ".compositing.json")
            atomic_json(staged_receipt, receipt)
            temporary.replace(output)
            staged_receipt.replace(output.with_suffix(".composite.json"))
            return receipt
        finally:
            temporary.unlink(missing_ok=True)
