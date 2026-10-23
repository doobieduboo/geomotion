"""Conservative source dependencies for reusable, video-only frame ranges.

Keys describe generic render_scene output, never output paths, narration or audio.
Layout has temporal state: keep its complete prefix rather than assume that a
finished annotation cannot move a later panel. Region geometry and the scene-wide
imagery tile level are global dependencies. Esri's live service has no immutable
tile revision; these keys retain already rendered imagery, as checkpoints do.
"""

import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from config import DEFAULTS, SKILL_ROOT
from project_state import digest, load_project
from timeline import resolve_scene


VERSION = 1
_RENDER_SCRIPTS = (
    "render_scene.py", "scene_layout.py", "composition.py", "layout.py",
    "map_assets.py", "effects.py", "region_stroke.py", "world_overlay.py", "title_layer.py",
    "basemap.py", "timeline.py", "config.py", "project_state.py",
    "revision_cache.py", "tile_memory.py",
)
_PRESET_FIELDS = (
    "design_width", "typography", "palette", "composition", "subtitles",
    "basemap", "layout", "region_fill", "region_outline",
)
_VIDEO_PROFILE_FIELDS = ("width", "height", "fps", "crf", "preset", "maxrate", "bufsize")
_FILE_FIELDS = {"image", "flag", "geojson", "atlas", "atlas_metadata", "definition"}


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def _hash(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


@lru_cache(maxsize=1)
def _runtime():
    import numpy
    import PIL
    from PIL import features

    ffmpeg = shutil.which("ffmpeg")
    return {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "pillow": PIL.__version__,
        "pillow_libraries": {name: features.version(name) for name in features.get_supported()},
        "ffmpeg": subprocess.check_output([ffmpeg, "-version"], text=True)
        if ffmpeg else None,
    }


def _configuration(state):
    # snapshot() includes many non-rendering scripts and editorial settings.
    # Select renderer dependencies explicitly, including this key algorithm.
    frozen = (state or {}).get("configuration", {})
    scripts = {name: frozen.get(name) or digest(SKILL_ROOT / "scripts" / name)
               for name in _RENDER_SCRIPTS}
    fonts = {}
    for name in {value for key, value in DEFAULTS["typography"].items() if key.endswith("_font")} | {DEFAULTS["subtitles"]["font"]}:
        path = SKILL_ROOT / name
        fonts[name] = frozen.get(path.name) or digest(path)
    for env in ("GEOMOTION_FONT_BOLD", "GEOMOTION_FONT_REGULAR"):
        if os.environ.get(env):
            fonts[env] = frozen.get(env) or digest(os.environ[env])
    return {"scripts": scripts, "fonts": fonts, "runtime": _runtime(),
            "preset": {name: DEFAULTS[name] for name in _PRESET_FIELDS}}


def render_keys(scene_path, mode, ranges, *, state=None):
    """Return ``{(first_frame, stop_frame): sha256}`` for half-open frame ranges.

    ``state`` may be the current project_state.snapshot(), captured by the caller
    before rendering. It supplies frozen renderer/font hashes, not a whole-scene
    fingerprint. Exceptions reject reuse; callers must never turn an error into
    an old cache key. No network or frame rendering is performed here.

    The conservative layout prefix means edits can invalidate later ranges after
    the edited cue ends. Appending a later cue preserves earlier ranges, except
    genuine global dependencies (subtitle reservation, geometry, imagery level).
    """
    from basemap import ATTRIBUTION, tile_zoom
    from composition import validate_composition
    from render_scene import camera_at, validate

    if mode not in ("preview", "final"):
        raise ValueError("Unknown render mode: " + str(mode))
    path = Path(scene_path).resolve()
    scene, _ = load_project(path)
    if scene.get("subtitle_cues"):
        if scene.get("subtitles"):
            raise ValueError("Use subtitle_cues or inline subtitles, not both")
        scene["subtitles"] = json.loads((path.parent / scene["subtitle_cues"]).read_text())
    scene, timeline = resolve_scene(scene)
    validate(scene)
    validate_composition(scene)
    profile = {**DEFAULTS["export"][mode], **scene.get("export", {}).get(mode, {})}
    width, height, fps = (int(profile[k]) for k in ("width", "height", "fps"))
    if min(width, height, fps) <= 0 or width % 2 or height % 2:
        raise ValueError("Export requires positive even dimensions and positive fps")
    count = max(1, round(timeline.duration * fps))
    ranges = list(ranges)
    for start, stop in ranges:
        if not isinstance(start, int) or not isinstance(stop, int) or not 0 <= start < stop <= count:
            raise ValueError("Frame range must satisfy 0 <= start < stop <= total frames")
    if not ranges:
        return {}

    files = {}
    world_images = {o["image"] for o in scene.get("world_overlays", [])}

    def asset(value, field):
        source = SKILL_ROOT / value if field == "definition" and value.startswith("library/") else path.parent / value
        source = source.resolve()
        if source not in files:
            files[source] = digest(source)
        result = {"sha256": files[source]}
        if field in ("image", "flag", "atlas"):
            # image_file caches by authored string and world overlays use RGBa.
            result["mode"] = "RGBa" if value in world_images else "RGBA"
        return result

    def dependencies(value):
        if isinstance(value, list):
            return [dependencies(item) for item in value]
        if isinstance(value, dict):
            return {key: asset(item, key) if key in _FILE_FIELDS and item else dependencies(item)
                    for key, item in value.items() if key not in ("event", "archive_id")}
        return value

    attribution = scene.get("attribution", "")
    if ATTRIBUTION not in attribution:
        attribution = " · ".join(filter(None, [attribution, ATTRIBUTION]))
    global_state = {
        "version": VERSION, "mode": mode, "configuration": _configuration(state),
        "profile": {key: profile[key] for key in _VIDEO_PROFILE_FIELDS},
        "basemap": {**DEFAULTS["basemap"], **scene.get("basemap", {})},
        "attribution": attribution, "composition": scene.get("composition", {}),
        # build_plans reserves subtitle space even before the first actual cue.
        "subtitle_reservation": bool(scene.get("subtitles")),
        "imagery_zoom": tile_zoom(max(k["zoom"] for k in scene["camera"]), mode),
        # Focus geometry can be used while its visible region is inactive.
        "region_geometry": [dependencies({key: region[key] for key in ("id", "geojson", "match") if key in region})
                            for region in scene.get("regions", [])],
    }
    global_hash = _hash(global_state)

    def prefix_item(item, cutoff, group):
        # Prefix capture deliberately retains expired cues for Composer history.
        start = item.get("start", 0)
        if not math.isfinite(start):
            raise ValueError("Layer start must be finite")
        if start > cutoff:
            return None
        result = dict(item)
        result.setdefault("start", 0)
        if group == "routes":
            result.setdefault("hide_at", timeline.source_duration)
        else:
            result.setdefault("end", timeline.source_duration)
        if "focus_strokes" in result:
            # This is an independent nested timeline, not the region lifetime.
            result["focus_strokes"] = [cue for cue in result["focus_strokes"]
                                       if cue.get("start", 0) <= cutoff]
        return dependencies(result)

    stops = set(stop for _, stop in ranges)
    clocks = hashlib.sha256()
    prefixes = {}
    # Hash each actual camera pose and source clock once; bounded memory even for
    # a long scene. Future interpolation endpoints still affect these poses.
    for frame in range(max(stops)):
        time = timeline.source_time(min(frame / fps, timeline.duration))
        camera = camera_at(scene["camera"], time)
        clocks.update(_encoded([frame, time, camera["center"], camera["zoom"], camera.get("rotation", 0)]))
        if frame + 1 in stops:
            layers = {}
            for group in ("world_overlays", "regions", "routes", "markers", "callouts", "titles", "subtitles", "focuses"):
                layers[group] = [{"index": index, "item": value} for index, item in enumerate(scene.get(group, []))
                                 if (value := prefix_item(item, time, group)) is not None]
            cta = scene.get("cta")
            layers["cta"] = prefix_item(cta, time, "cta") if cta else None
            prefixes[frame + 1] = _hash({"clock_camera_prefix": clocks.hexdigest(), "layers": layers})
    return {(start, stop): _hash({"global": global_hash, "prefix": prefixes[stop], "range": [start, stop]})
            for start, stop in ranges}


def render_key(scene_path, mode, start, stop, *, state=None):
    """Single-range convenience wrapper for :func:`render_keys`."""
    return render_keys(scene_path, mode, [(start, stop)], state=state)[(start, stop)]
