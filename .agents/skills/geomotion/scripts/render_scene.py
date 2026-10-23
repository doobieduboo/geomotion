"""Topic-agnostic, scene-driven 2D geographic motion graphics renderer."""

import argparse
import io
import json
import math
import os
import shutil
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from basemap import ATTRIBUTION, tile_url, tile_zoom, validate_basemap
from config import DEFAULTS, SKILL_ROOT
from map_assets import clip_flag, flagpole, select_sprite, route_pose, route_visibility
from world_overlay import project_world_overlay
from effects import paint_land, composite_emission, glow_settings
from region_stroke import prepare_stroke, revealed_paths, projected_stroke_copies, stroke_state, validate_focus_strokes, outline_style, paint_outlines
from timeline import resolve_scene
from project_state import load_project, atomic_json, snapshot, fingerprint
from layout import wrap, inspect_boxes, fade_callout, callout_image
from scene_layout import build_plans
from tile_memory import check_tile_memory
from composition import validate_composition
from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from title_layer import render_title, title_config


def merc(lon, lat, zoom):
    scale = 256 * 2**zoom
    lat = max(-85.0511, min(85.0511, lat))
    return np.array(
        [
            (lon + 180) / 360 * scale,
            (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * scale,
        ]
    )


def ease(v):
    v = max(0, min(1, v))
    return v * v * (3 - 2 * v)


def camera_at(keys, t):
    if t <= keys[0]["time"]:
        return keys[0]
    if t >= keys[-1]["time"]:
        return keys[-1]
    for a, b in zip(keys, keys[1:]):
        if a["time"] <= t <= b["time"]:
            u = (t - a["time"]) / (b["time"] - a["time"])
            u = u if b.get("ease") == "linear" else ease(u)
            # Take the short path at the antimeridian; keep an unwrapped center.
            delta = (b["center"][0] - a["center"][0] + 180) % 360 - 180
            heading = (b.get("rotation", 0) - a.get("rotation", 0) + 180) % 360 - 180
            return {
                "center": [
                    a["center"][0] + u * delta,
                    a["center"][1] + u * (b["center"][1] - a["center"][1]),
                ],
                "zoom": a["zoom"] + u * (b["zoom"] - a["zoom"]),
                "rotation": a.get("rotation", 0) + u * heading,
            }


def validate(scene):
    if not math.isfinite(scene.get("duration", 0)) or scene.get("duration", 0) <= 0:
        raise ValueError("duration must be positive")
    keys = scene.get("camera", [])
    for region in scene.get('regions',[]):
        validate_focus_strokes(region)
        outline_style(region)
        glow_settings(region.get('fill_glow'),land=True)
        if region.get('fill_blend',DEFAULTS['region_fill']['blend']) not in ('normal','terrain_tint'):
            raise ValueError('Invalid region fill_blend')
        for cue in region.get('focus_strokes',[]):outline_style(region,cue)
    for overlay in scene.get('world_overlays',[]):
        kind=overlay.get('fill_kind','flag');blend=overlay.get('fill_blend','normal')
        if kind not in ('color','flag') or blend not in ('normal','terrain_tint') or (kind=='flag' and blend!='normal'):
            raise ValueError('Invalid world overlay fill_kind/fill_blend')
        glow_settings(overlay.get('glow'),land=True)
    if not keys:
        raise ValueError("camera requires at least one keyframe")
    last = -1
    for k in keys:
        if not math.isfinite(k["time"]) or k["time"] < 0 or k["time"] <= last:
            raise ValueError("camera times must increase strictly")
        last = k["time"]
        lon, lat = k["center"]
        if not (-180 <= lon <= 180 and -85 <= lat <= 85):
            raise ValueError("Invalid camera coordinate")
        if not 0 <= k["zoom"] <= 18:
            raise ValueError("Camera zoom must be 0–18")
    for route in scene.get("routes", []):
        if len(route.get("points", [])) < 2 or route.get("end", 0) <= route.get(
            "start", 0
        ):
            raise ValueError("Routes need 2+ points and end > start")
    for item in scene.get("markers", []) + scene.get("callouts", []):
        lon, lat = item["position"]
        if not (-180 <= lon <= 180 and -85 <= lat <= 85):
            raise ValueError("Invalid layer coordinate")


def color(value):
    return tuple(value) if value else ImageColor.getrgb(DEFAULTS["palette"]["outline"])


@lru_cache(maxsize=128)
def _cached_font(path, size):
    return ImageFont.truetype(path, size)


def load_font(size, bold=False):
    role = "bold_font" if bold else "regular_font"
    override = os.environ.get(
        "GEOMOTION_FONT_BOLD" if bold else "GEOMOTION_FONT_REGULAR"
    )
    path = Path(override) if override else SKILL_ROOT / DEFAULTS["typography"][role]
    if not path.is_file():
        raise FileNotFoundError(
            f"Required font is missing: {path}. Restore the bundled font or set an explicit font override."
        )
    return _cached_font(str(path.resolve()), size)


def adjusted_basemap(image, settings):
    """Skip identity enhancements; preserve configured adjustment order."""
    if settings["saturation"] != 1:
        image = ImageEnhance.Color(image).enhance(settings["saturation"])
    if settings["brightness"] != 1:
        image = ImageEnhance.Brightness(image).enhance(settings["brightness"])
    return image


def composite_glow(base, layer, radius):
    """Composite an existing geographic layer with its original glow."""
    if layer is not None:
        base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius)))
        base.alpha_composite(layer)


def projector(camera, width, height, scale, mode):
    z = tile_zoom(camera["zoom"], mode)
    center = merc(*camera["center"], z)
    zoom_scale = 2 ** (camera["zoom"] - z) * scale
    angle = math.radians(camera.get("rotation", 0))
    cs, sn = math.cos(angle), math.sin(angle)

    def project(ll):
        xy = merc(*ll, z)
        world = 256 * 2**z
        xy[0] = center[0] + (xy[0] - center[0] + world / 2) % world - world / 2
        v = (xy - center) * zoom_scale
        return width / 2 + cs * v[0] - sn * v[1], height / 2 + sn * v[0] + cs * v[1]

    return project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--mode", choices=["preview", "final"], default="preview")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--final-requested", action="store_true")
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--end-frame", type=int)
    parser.add_argument("--video-only", action="store_true")
    parser.add_argument("--plan-only", action="store_true",
                        help="Compute the complete layout without imagery or video")
    parser.add_argument("--layout-plan", type=Path,
                        help="Reuse a previously validated global layout")
    parser.add_argument("--plan-fingerprint",
                        help="Exact source/config fingerprint required for layout sharing")
    args = parser.parse_args()
    if args.plan_only and args.layout_plan:
        parser.error("--plan-only and --layout-plan cannot be combined")
    if args.plan_only and (args.start_frame != 0 or args.end_frame is not None):
        parser.error("--plan-only requires the full source timeline")
    if (args.plan_only or args.layout_plan) and not args.plan_fingerprint:
        parser.error("Shared layout requires --plan-fingerprint")
    if args.mode == "final" and not args.final_requested:
        parser.error(
            "Final requires the user's explicit request; pass --final-requested to record it"
        )
    scene, archive_warnings = load_project(args.scene)
    if scene.get("subtitle_cues"):
        if scene.get("subtitles"):
            raise ValueError("Use subtitle_cues or inline subtitles, not both")
        scene["subtitles"] = json.loads(
            (args.scene.resolve().parent / scene["subtitle_cues"]).read_text()
        )
    scene, timeline = resolve_scene(scene)
    validate(scene)
    validate_composition(scene)
    if not args.plan_only and not shutil.which("ffmpeg"):
        parser.error("Install FFmpeg")
    root = args.scene.resolve().parent

    def path(value):
        return (root / value).resolve()

    export = {
        **DEFAULTS["export"][args.mode],
        **scene.get("export", {}).get(args.mode, {}),
    }
    width, height, fps = (int(export[k]) for k in ("width", "height", "fps"))
    if min(width, height, fps) <= 0 or width % 2 or height % 2:
        raise ValueError("Export requires positive even dimensions and positive fps")
    duration = timeline.source_duration
    count = max(1, round(timeline.duration * fps))
    first, stop = args.start_frame, (
        args.end_frame if args.end_frame is not None else count
    )
    if not 0 <= first < stop <= count:
        parser.error("Frame range must satisfy 0 <= start < end <= total frames")
    if scene.get("audio") and not args.video_only and (first != 0 or stop != count):
        parser.error("Partial render requires --video-only when scene has audio")
    if args.video_only:
        scene.pop("audio", None)
    scale = width / DEFAULTS["design_width"]
    basemap = {**DEFAULTS["basemap"], **scene.get("basemap", {})}
    validate_basemap(basemap)
    if ATTRIBUTION not in scene.get("attribution", ""):
        scene["attribution"] = " · ".join(
            filter(None, [scene.get("attribution"), ATTRIBUTION])
        )
    all_cameras = [
        camera_at(
            scene["camera"], timeline.source_time(min(n / fps, timeline.duration))
        )
        for n in range(count if args.plan_only else stop)
    ]
    prepared = all_cameras[first:stop]
    world_images = {o["image"] for o in scene.get("world_overlays", [])}
    image_cache = {}
    metadata_cache = {}

    def metadata_file(value):
        if value not in metadata_cache:
            metadata_cache[value] = json.loads(path(value).read_text())
        return metadata_cache[value]

    def image_file(value):
        if value not in image_cache:
            image_cache[value] = Image.open(path(value)).convert("RGBa" if value in world_images else "RGBA")
        return image_cache[value]

    regions = []
    for region in scene.get("regions", []):
        data = json.loads(path(region["geojson"]).read_text())
        features = (
            data["features"]
            if data["type"] == "FeatureCollection"
            else (
                [data]
                if data["type"] == "Feature"
                else [{"geometry": data, "properties": {}}]
            )
        )
        combined_polys = []
        for feature in features:
            if any(
                feature.get("properties", {}).get(k) != v
                for k, v in region.get("match", {}).items()
            ):
                continue
            g = feature["geometry"]
            if g["type"] not in ["Polygon", "MultiPolygon"]:
                continue
            polys = (
                g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            )
            combined_polys.extend(polys)
        if combined_polys:
            regions.append((region, combined_polys))
    region_strokes = {}
    for region, polys in regions:
        origins = [region.get("stroke_origin")] + [c.get("stroke_origin", region.get("stroke_origin")) for c in region.get("focus_strokes", [])]
        for origin in origins:
            key = (id(region), tuple(origin) if origin is not None else None)
            if key not in region_strokes:
                region_strokes[key] = prepare_stroke(polys, origin)
    titles = []
    for item in scene.get("titles", []):
        definition = item["definition"]
        source = (
            SKILL_ROOT / definition
            if definition.startswith("library/")
            else path(definition)
        )
        config = title_config(json.loads(source.read_text()), item.get("overrides"))
        start = float(item.get("start", 0))
        if not math.isfinite(start) or start < 0:
            raise ValueError("Title start must be nonnegative and finite")
        titles.append((start, item.get("end", duration), config))
    current_fingerprint = None
    shared_plan = None
    if args.plan_only or args.layout_plan:
        current_fingerprint = fingerprint(snapshot(args.scene), args.mode)
        if current_fingerprint != args.plan_fingerprint:
            raise ValueError("Global layout fingerprint differs from current source")
        if args.layout_plan:
            document = json.loads(args.layout_plan.read_text())
            profile = {"mode": args.mode, "width": width, "height": height, "fps": fps}
            if (
                document.get("version") != 1
                or document.get("fingerprint") != current_fingerprint
                or document.get("profile") != profile
                or not isinstance(document.get("plans"), list)
                or len(document["plans"]) != count
            ):
                raise ValueError("Global layout is stale or incompatible")
            shared_plan = document["plans"]
    plans, callout_layouts, cta_layout = build_plans(
        scene,
        timeline,
        all_cameras,
        fps,
        (width, height),
        lambda camera: projector(camera, width, height, scale, args.mode),
        regions,
        titles,
        image_file,
        load_font,
        metadata_file,
        precomputed_plans=shared_plan,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.plan_only:
        if fingerprint(snapshot(args.scene), args.mode) != current_fingerprint:
            raise ValueError("Scene inputs changed during global layout planning")
        atomic_json(args.output, {
            "version": 1,
            "fingerprint": current_fingerprint,
            "profile": {"mode": args.mode, "width": width, "height": height, "fps": fps},
            "plans": [
                {"positions": plan["positions"], "focuses": plan["focuses"]}
                for plan in plans
            ],
        })
        print(args.output.resolve())
        return
    # Session-memory tiles only: this viewing service does not allow offline tile export.
    tile_images = {}
    # One source level for the complete scene, including checkpoint renders.
    # Changing integer tile levels mid-ramp changes the imagery underneath it.
    imagery_zoom = tile_zoom(max(k["zoom"] for k in scene["camera"]), args.mode)
    needed = set()
    for camera in prepared:
        z = imagery_zoom
        c = merc(*camera["center"], z)
        s = 2 ** (camera["zoom"] - z) * scale
        r = math.hypot(width, height) / 2 / s + 3
        for x in range(math.floor((c[0] - r) / 256), math.floor((c[0] + r) / 256) + 1):
            for y in range(
                max(0, math.floor((c[1] - r) / 256)),
                min(2**z - 1, math.floor((c[1] + r) / 256)) + 1,
            ):
                needed.add((z, x, y))
    tile_groups = {
        z: [tile for tile in needed if tile[0] == z]
        for z in {tile[0] for tile in needed}
    }
    bounds = {}
    for z, tiles in tile_groups.items():
        xmin = min(tile[1] for tile in tiles)
        xmax = max(tile[1] for tile in tiles)
        ymin = min(tile[2] for tile in tiles)
        ymax = max(tile[2] for tile in tiles)
        bounds[z] = (xmin, xmax, ymin, ymax)
    # Deduplicate wrapped tiles before parallel requests.
    physical_tiles = {(z, x % (2**z), y) for z, x, y in needed}
    check_tile_memory(bounds, len(physical_tiles))

    def fetch(tile):
        z, x, y = tile
        url = tile_url(z, x, y)
        req = urllib.request.Request(url, headers={"User-Agent": "GeoMotion/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                data = response.read()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                if image.size != (256, 256):
                    raise ValueError("Expected a 256px imagery tile")
                return tile, image.convert("RGB")
        except Exception as exc:
            raise RuntimeError(
                f"Esri World Imagery request failed from {url}: {exc}. Check access/network policy; no alternate basemap is permitted."
            ) from exc

    with ThreadPoolExecutor(max_workers=8) as pool:
        tile_images.update(pool.map(fetch, physical_tiles))
    mosaics = {}
    for z, tiles in tile_groups.items():
        xmin, xmax, ymin, ymax = bounds[z]
        im = Image.new("RGB", ((xmax - xmin + 1) * 256, (ymax - ymin + 1) * 256))
        for _, x, y in tiles:
            im.paste(
                tile_images[(z, x % (2**z), y)], ((x - xmin) * 256, (y - ymin) * 256)
            )
        mosaics[z] = (im, np.array([xmin * 256, ymin * 256]))
    tile_images.clear()  # Mosaics own source pixels; release decoded tiles.
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
    ]
    if scene.get("audio"):
        command += ["-i", str(path(scene["audio"]))]
        if (
            scene.get("timeline", {}).get("cuts")
            and scene["timeline"].get("audio_clock", "source") == "source"
        ):
            command += [
                "-filter_complex",
                timeline.audio_filter(),
                "-map",
                "0:v",
                "-map",
                "[audio]",
            ]
        else:
            command += ["-af", "apad"]
    command += [
        "-c:v",
        "libx264",
        "-preset",
        export["preset"],
        "-crf",
        str(export["crf"]),
        "-maxrate",
        export["maxrate"],
        "-bufsize",
        export["bufsize"],
        "-pix_fmt",
        "yuv420p",
    ]
    if scene.get("audio"):
        command += ["-c:a", "aac", "-b:a", export["audio_bitrate"]]
    temporary = args.output.with_name(args.output.stem + ".rendering.mp4")
    command += [
        "-t",
        str((stop - first) / fps),
        "-movflags",
        "+faststart",
        str(temporary),
    ]
    p = subprocess.Popen(command, stdin=subprocess.PIPE)
    layout_issues = {}
    try:
        for n, camera in enumerate(prepared, start=first):
            t = timeline.source_time(min(n / fps, timeline.duration))
            boxes = []
            z = imagery_zoom
            zoom_scale = 2 ** (camera["zoom"] - z) * scale
            center = merc(*camera["center"], z)
            a = math.radians(camera.get("rotation", 0))
            cs, sn = math.cos(a), math.sin(a)

            def project(ll):
                xy = merc(*ll, z)
                world = 256 * 2**z
                xy[0] = center[0] + (xy[0] - center[0] + world / 2) % world - world / 2
                v = (xy - center) * zoom_scale
                return (
                    width / 2 + cs * v[0] - sn * v[1],
                    height / 2 + sn * v[0] + cs * v[1],
                )

            mosaic, origin = mosaics[z]
            mid = center - origin
            af = (
                cs / zoom_scale,
                sn / zoom_scale,
                mid[0] - (cs * width / 2 + sn * height / 2) / zoom_scale,
                -sn / zoom_scale,
                cs / zoom_scale,
                mid[1] - (-sn * width / 2 + cs * height / 2) / zoom_scale,
            )
            im = mosaic.transform(
                (width, height), Image.Transform.AFFINE, af, Image.Resampling.BICUBIC
            )
            im = adjusted_basemap(im, basemap)
            im = im.convert("RGBA")

            def visible(item):
                return item.get("start", 0) <= t < item.get("end", duration)

            for overlay in scene.get("world_overlays", []):
                if visible(overlay):
                    layer = project_world_overlay(image_file(overlay["image"]), camera, im.size, scale)
                    fade = 1.0
                    if overlay.get("fade_in", 0) > 0:
                        fade = min(fade, ease((t - overlay.get("start", 0)) / overlay["fade_in"]))
                    if overlay.get("fade_out", 0) > 0:
                        fade = min(fade, ease((overlay.get("end", duration) - t) / overlay["fade_out"]))
                    if fade < 1:
                        layer.putalpha(layer.getchannel("A").point(lambda a: round(a * fade)))
                    im = paint_land(im,layer,scale,blend=overlay.get('fill_blend','normal'),kind=overlay.get('fill_kind','flag'),glow=overlay.get('glow'))
            if any(visible(region) for region, _ in regions):
                reference_jobs, focus_jobs = [], []
                world_pixels = 256 * 2 ** camera["zoom"] * scale

                def projected_paths(region, origin, progress):
                    return [copy
                        for path_points in revealed_paths(region_strokes[(id(region), origin)], ease(progress))
                        for copy in projected_stroke_copies(path_points, project,
                            (world_pixels * cs, world_pixels * sn), im.size)]

                for region, polys in sorted(regions, key=lambda pair: stroke_state(pair[0], t)[2] is not None):
                    if not visible(region):
                        continue
                    projected = [[[project(ll) for ll in ring] for ring in poly] for poly in polys]
                    if region.get("fill"):
                        texture = Image.new("RGBA", (1, 1), color(region["fill"]) + (255,))
                        layer=clip_flag(texture, projected, im.size,
                            region.get("opacity", DEFAULTS["region_fill"]["solid_opacity"]))
                        im=paint_land(im,layer,scale,blend=region.get("fill_blend",DEFAULTS["region_fill"]["blend"]),kind="color",glow=region.get("fill_glow"))
                    if region.get("flag"):
                        layer=clip_flag(image_file(region["flag"]), projected, im.size,
                            region.get("opacity", DEFAULTS["region_fill"]["flag_opacity"]))
                        im=paint_land(im,layer,scale,kind="flag",glow=region.get("fill_glow"))
                    base_progress, base_origin, _ = stroke_state({**region, "focus_strokes": []}, t)
                    style = outline_style(region)
                    style["color"] = color(style["color"])
                    reference_jobs.append((projected_paths(region, base_origin, base_progress), style))
                    progress, origin, cue = stroke_state(region, t)
                    if cue is not None:
                        style = outline_style(region, cue)
                        style["color"] = color(style["color"])
                        fade = cue.get("glow_fade_out", 0)
                        opacity = ease((cue["end"]-t)/fade) if fade > 0 else 1
                        focus_jobs.append((projected_paths(region, origin, progress), style, opacity))
                outline,emission=paint_outlines(im.size, scale, reference_jobs, focus_jobs,return_emission=True)
                im=composite_emission(im,emission)
                im.alpha_composite(outline)
            routes = None
            for route in scene.get("routes", []):
                if t < route["start"] or t >= route.get("hide_at", duration):
                    continue
                if routes is None:
                    routes = Image.new("RGBA", im.size)
                    rd = ImageDraw.Draw(routes)
                fading = "fade_in" in route or "fade_out" in route
                route_layer = Image.new("RGBA", im.size) if fading else routes
                route_draw = ImageDraw.Draw(route_layer) if fading else rd
                trail, heading = route_pose(route, t, project)
                col = color(route.get("color", [255, 105, 68]))
                if route.get("casing_width", 0) > 0:
                    route_draw.line(trail, fill=tuple(route.get("casing_color", [7,12,18]))+(255,),
                            width=max(1,round(route["casing_width"]*scale)), joint="curve")
                route_draw.line(
                    trail,
                    fill=col + (255,),
                    width=max(1, round(route.get("width", 4) * scale)),
                    joint="curve",
                )
                x, y = trail[-1]
                if route.get("arrow"):
                    angle = math.radians(heading)
                    dx, dy = math.sin(angle), -math.cos(angle)
                    progress = max(0, min(1, (t-route["start"])/(route["end"]-route["start"])))
                    grow = min(1, progress / .08)
                    length = route.get("head_length", 18) * scale * grow
                    half = route.get("head_width", 14) * scale * grow / 2
                    bx, by = x - dx * length, y - dy * length
                    route_draw.polygon([(x,y),(bx-dy*half,by+dx*half),
                                (bx+dy*half,by-dx*half)], fill=col+(255,),
                               outline=tuple(route.get("casing_color", [7,12,18]))+(255,))
                elif route.get("atlas"):
                    meta = metadata_file(route["atlas_metadata"])
                    frame, anchor, _ = select_sprite(
                        image_file(route["atlas"]), meta, heading,
                        animation_time_s=t-route["start"] if t < route["end"] else 0,
                    )
                    factor = route.get("sprite_scale", 1) * scale
                    size = (
                        max(1, round(frame.width * factor)),
                        max(1, round(frame.height * factor)),
                    )
                    frame = frame.resize(size, Image.Resampling.LANCZOS)
                    route_layer.alpha_composite(
                        frame,
                        (round(x - anchor[0] * factor), round(y - anchor[1] * factor)),
                    )
                else:
                    route_draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 246, 222, 255))
                if fading:
                    routes.alpha_composite(fade_callout(route_layer, route_visibility(route, duration), t))
            composite_glow(im, routes, 4 * scale)
            overlay = Image.new("RGBA", im.size)
            draw = ImageDraw.Draw(overlay)
            for marker in scene.get("markers", []):
                if not visible(marker):
                    continue
                x, y = project(marker["position"])
                col = color(marker.get("color"))
                r = max(3, round(12 * scale))
                if marker.get("flag"):
                    overlay.alpha_composite(
                        flagpole(
                            image_file(marker["flag"]),
                            (x, y),
                            t,
                            size=(round(50 * scale), round(32 * scale)),
                            pole_height=round(65 * scale),
                            canvas_size=im.size,
                        )
                    )
                elif marker.get("show_dot", True):
                    draw.ellipse(
                        (x - r, y - r, x + r, y + r),
                        fill=(7, 20, 28, 230),
                        outline=col + (255,),
                        width=max(1, round(2 * scale)),
                    )
                    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=col + (255,))
                label = marker.get("label")
                if label:
                    offset = marker.get("offset", [18, 15])
                    label_position = (x + offset[0] * scale, y + offset[1] * scale)
                    label_font = load_font(
                        max(10, round(marker.get("font_size", 21) * scale)), True
                    )
                    label_bounds = draw.textbbox(
                        label_position, label, font=label_font, stroke_width=1
                    )
                    if (
                        label_bounds[2] > 0
                        and label_bounds[3] > 0
                        and label_bounds[0] < width
                        and label_bounds[1] < height
                    ):
                        boxes.append(
                            (
                                "marker:" + str(scene["markers"].index(marker)),
                                label_bounds,
                            )
                        )
                    draw.text(
                        label_position,
                        label,
                        font=label_font,
                        fill=(239, 247, 239, 255),
                        stroke_width=1,
                        stroke_fill=(0, 0, 0, 230),
                    )
            for i, callout, geometry in callout_layouts:
                if not visible(callout):
                    continue
                panel_layer = Image.new("RGBA", im.size)
                panel_draw = ImageDraw.Draw(panel_layer)
                ax, ay = project(callout["position"])
                image = callout_image(image_file(callout["image"]) if callout.get("image") else None, callout)
                padding = max(
                    2, round(DEFAULTS["layout"]["callout_padding_design"] * scale)
                )
                w, h, image_height, rows = geometry
                box = plans[n]["positions"]["callout:" + str(i)]
                x, y = round(box[0]), round(box[1])
                boxes.append(("callout:" + str(i), (x, y, x + w, y + h)))
                col = color(callout.get("color"))
                px = max(x + padding, min(x + w - padding, ax))
                edge = y + h if ay > y + h / 2 else y
                if callout.get("show_leader", True):
                    panel_draw.line([(ax, ay), (px, edge)], fill=col + (210,), width=1)
                panel_draw.rounded_rectangle(
                    (x, y, x + w, y + h),
                    radius=max(4, round(14 * scale)),
                    fill=(9, 22, 29, 240),
                    outline=col + (210,),
                    width=1,
                )
                if image:
                    pic = image.resize(
                        (w - 2 * padding, image_height), Image.Resampling.LANCZOS
                    )
                    panel_layer.alpha_composite(pic, (x + padding, y + padding))
                for text, font, xx, yy in rows:
                    panel_draw.text(
                        (x + xx, y + yy), text, font=font, fill=(239, 247, 239, 255)
                    )
                overlay.alpha_composite(fade_callout(panel_layer, callout, t))
            for cue in scene.get("subtitles", []):
                if not visible(cue):
                    continue
                sub = DEFAULTS["subtitles"]
                font = ImageFont.truetype(
                    str(SKILL_ROOT / sub["font"]),
                    max(1, round(sub["font_size_design"] * scale)),
                )
                safe = DEFAULTS["composition"]["subtitle_safe_area_normalized"]
                lines = wrap(cue["text"], font, width * (safe[2] - safe[0]))
                if len(lines) > sub["max_lines"]:
                    raise ValueError(
                        "Subtitle exceeds preset max_lines; revise phrase cues"
                    )
                stroke = max(1, round(sub["stroke_design"] * scale))
                text = "\n".join(lines)
                anchor = sub["anchor_normalized"]
                bounds = draw.multiline_textbbox(
                    (width * anchor[0], height * anchor[1]),
                    text,
                    font=font,
                    anchor="mm",
                    align="center",
                    stroke_width=stroke,
                )
                boxes.append(("subtitle", bounds))
                draw.multiline_text(
                    (width * anchor[0], height * anchor[1]),
                    text,
                    font=font,
                    anchor="mm",
                    align="center",
                    fill=DEFAULTS["palette"]["text"],
                    stroke_width=stroke,
                    stroke_fill=DEFAULTS["palette"]["text_shadow"],
                )
            if "cta" in plans[n]["positions"]:
                box = plans[n]["positions"]["cta"]
                metric = cta_layout["metric"]
                position = (box[0] - metric[0], box[1] - metric[1])
                draw.multiline_text(
                    position,
                    cta_layout["text"],
                    font=cta_layout["font"],
                    align="center",
                    fill=DEFAULTS["palette"]["cta"],
                    stroke_width=cta_layout["stroke"],
                    stroke_fill=DEFAULTS["palette"]["text_shadow"],
                )
                boxes.append(
                    (
                        "cta",
                        draw.multiline_textbbox(
                            position,
                            cta_layout["text"],
                            font=cta_layout["font"],
                            align="center",
                            stroke_width=cta_layout["stroke"],
                        ),
                    )
                )
            for start, end, config in titles:
                if start <= t < end:
                    title_image = render_title(config, t - start, im.size)
                    title_box = title_image.getchannel("A").getbbox()
                    if title_box:
                        boxes.append(("title:" + str(start), title_box))
                    overlay.alpha_composite(title_image)
            if scene.get("attribution"):
                credit_font = load_font(max(8, round(12 * scale)))
                margin = max(4, round(10 * scale))
                credit = "\n".join(
                    wrap(scene["attribution"], credit_font, width - 2 * margin)
                )
                credit_bounds = draw.multiline_textbbox(
                    (0, 0), credit, font=credit_font
                )
                position = (margin, height - margin - credit_bounds[3])
                boxes.append(
                    (
                        "attribution",
                        draw.multiline_textbbox(position, credit, font=credit_font),
                    )
                )
                draw.multiline_text(
                    position, credit, font=credit_font, fill=(185, 207, 212, 240)
                )
            for issue in inspect_boxes(boxes, (width, height)):
                layout_issues.setdefault(issue, {"first_frame": n, "last_frame": n})[
                    "last_frame"
                ] = n
            im.alpha_composite(overlay)
            if n in {0, count // 2, count - 1}:
                im.convert("RGB").save(
                    args.output.with_name(args.output.stem + f"_frame_{n}.jpg")
                )
            p.stdin.write(im.convert("RGB").tobytes())
    except BaseException:
        p.stdin.close()
        p.wait()
        temporary.unlink(missing_ok=True)
        raise
    else:
        p.stdin.close()
    if p.wait() != 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg render failed")
    temporary.replace(args.output)
    atomic_json(
        args.output.with_suffix(".layout.json"),
        {
            "errors": layout_issues,
            "archive_warnings": archive_warnings,
            "composition": {
                "frames": [
                    {
                        "frame": n,
                        "positions": plans[n]["positions"],
                        "focuses": plans[n]["focuses"],
                    }
                    for n in range(first, stop)
                ]
            },
        },
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
