"""Plan source-timed generic scene overlays in global output-frame order."""

from PIL import Image, ImageDraw, ImageFont
from config import DEFAULTS, SKILL_ROOT
from composition import Composer, pixel_box, validate_composition
from layout import callout_layout, wrap, inspect_boxes, overlaps
from title_layer import render_title
from map_assets import route_pose


def build_plans(
    scene,
    timeline,
    cameras,
    fps,
    size,
    project_for,
    regions,
    titles,
    image_file,
    load_font,
    metadata_file,
):
    width, height = size
    scale = width / DEFAULTS["design_width"]
    settings = validate_composition(scene)
    composer = Composer(size, fps, settings)
    draw = ImageDraw.Draw(Image.new("RGBA", size))
    padding = max(2, round(DEFAULTS["layout"]["callout_padding_design"] * scale))
    callouts = []
    for i, item in enumerate(scene.get("callouts", [])):
        if item.get("placement", "auto") not in ("auto", "manual"):
            raise ValueError("Callout placement must be auto or manual")
        image = image_file(item["image"]) if item.get("image") else None
        maximum = round(
            min(
                width - 2 * composer.margin,
                round(
                    item.get("width", DEFAULTS["layout"]["callout_max_width_design"])
                    * scale
                ),
            )
        )
        geometry = callout_layout(
            item.get("title", ""),
            item.get("lines", []),
            load_font(max(11, round(22 * scale)), True),
            load_font(max(9, round(19 * scale))),
            maximum,
            padding,
            image.size if image else None,
        )
        callouts.append((i, item, geometry))
    sub = DEFAULTS["subtitles"]
    sub_font = ImageFont.truetype(
        str(SKILL_ROOT / sub["font"]), max(1, round(sub["font_size_design"] * scale))
    )
    anchor = sub["anchor_normalized"]
    sub_position = (width * anchor[0], height * anchor[1])
    safe = DEFAULTS["composition"]["subtitle_safe_area_normalized"]
    stroke = max(1, round(sub["stroke_design"] * scale))
    subtitles = []
    for cue in scene.get("subtitles", []):
        lines = wrap(cue["text"], sub_font, width * (safe[2] - safe[0]))
        if len(lines) > sub["max_lines"]:
            raise ValueError("Subtitle exceeds preset max_lines; revise phrase cues")
        text = "\n".join(lines)
        box = draw.multiline_textbbox(
            sub_position,
            text,
            font=sub_font,
            anchor="mm",
            align="center",
            stroke_width=stroke,
        )
        subtitles.append((cue, box))
    reserved = []
    if subtitles:
        template = draw.multiline_textbbox(
            sub_position,
            "\n".join(["Ag"] * sub["max_lines"]),
            font=sub_font,
            anchor="mm",
            stroke_width=stroke,
        )
        reserved.append(
            (
                safe[0] * width,
                min(safe[1] * height, template[1]),
                safe[2] * width,
                max(safe[3] * height, template[3]),
            )
        )
    credit_font = load_font(max(8, round(12 * scale)))
    margin = max(4, round(10 * scale))
    credit = "\n".join(wrap(scene["attribution"], credit_font, width - 2 * margin))
    credit_bounds = draw.multiline_textbbox((0, 0), credit, font=credit_font)
    credit_position = (margin, height - margin - credit_bounds[3])
    credit_box = draw.multiline_textbbox(credit_position, credit, font=credit_font)
    reserved.append(credit_box)
    cta_layout = None
    cta = scene.get("cta")
    if cta:
        font = ImageFont.truetype(
            str(SKILL_ROOT / DEFAULTS["typography"]["display_font"]),
            max(1, round(DEFAULTS["composition"]["cta_font_size_design"] * scale)),
        )
        area = DEFAULTS["composition"]["cta_area_normalized"]
        lines = wrap(cta["text"], font, width * (area[2] - area[0]))
        if len(lines) > DEFAULTS["composition"]["cta_max_lines"]:
            raise ValueError("CTA exceeds preset max_lines; revise authored text")
        text = "\n".join(lines)
        metric = draw.multiline_textbbox(
            (0, 0), text, font=font, align="center", stroke_width=stroke
        )
        cta_layout = {"text": text, "font": font, "metric": metric, "stroke": stroke}
    route_specs = [
        (r, metadata_file(r["atlas_metadata"]) if r.get("atlas") else None)
        for r in scene.get("routes", [])
    ]
    plans = []
    for n, camera in enumerate(cameras):
        time = timeline.source_time(min(n / fps, timeline.duration))

        def visible(item):
            return (
                item.get("start", 0) <= time < item.get("end", timeline.source_duration)
            )

        project = project_for(camera)
        focuses = []
        for focus in scene.get("focuses", []):
            if not visible(focus):
                continue
            if "bounds" in focus:
                west, south, east, north = focus["bounds"]
                points = [
                    project(ll)
                    for ll in (
                        (west, south),
                        (west, north),
                        (east, south),
                        (east, north),
                    )
                ]
            else:
                points = [
                    project(ll)
                    for region, polys in regions
                    if region.get("id") == focus["region_id"]
                    for poly in polys
                    for ring in poly
                    for ll in ring
                ]
                if not points:
                    raise ValueError(
                        "Focus region has no selected geometry: " + focus["region_id"]
                    )
            box = (
                min(p[0] for p in points),
                min(p[1] for p in points),
                max(p[0] for p in points),
                max(p[1] for p in points),
            )
            if overlaps(box, (0, 0, width, height)):
                focuses.append(
                    (
                        max(0, box[0]),
                        max(0, box[1]),
                        min(width, box[2]),
                        min(height, box[3]),
                    )
                )
            else:
                raise ValueError(
                    f"Frame {n}: declared geographic focus is outside the camera view"
                )
        if not focuses:
            focuses = [pixel_box(settings["fallback_focus_normalized"], size)]
        annotations = []
        for cue, box in subtitles:
            if visible(cue):
                annotations.append(("subtitle", box))
        footprints = []
        markers = 0
        for i, item in enumerate(scene.get("markers", [])):
            if not visible(item):
                continue
            x, y = project(item["position"])
            if (
                not -12 * scale < x < width + 12 * scale
                or not -12 * scale < y < height + 12 * scale
            ):
                continue
            markers += 1
            radius = max(3, round(12 * scale))
            box = (
                (
                    x - 12,
                    y - round(65 * scale) - 3,
                    x + max(12, round(50 * scale) + 1),
                    y + 5,
                )
                if item.get("flag")
                else (x - radius, y - radius, x + radius, y + radius)
            )
            footprints.append(
                (
                    max(0, box[0]),
                    max(0, box[1]),
                    min(width, box[2]),
                    min(height, box[3]),
                )
            )
            if item.get("label"):
                offset = item.get("offset", [18, 15])
                box = draw.textbbox(
                    (x + offset[0] * scale, y + offset[1] * scale),
                    item["label"],
                    font=load_font(
                        max(10, round(item.get("font_size", 21) * scale)), True
                    ),
                    stroke_width=1,
                )
                annotations.append(("marker:" + str(i), box))
        title_count = 0
        for i, (start, end, config) in enumerate(titles):
            if start <= time < end:
                layer = render_title(config, time - start, size)
                box = layer.getchannel("A").getbbox()
                if box:
                    title_count += 1
                    annotations.append(("title:" + str(i), box))
                    if any(overlaps(box, focus) for focus in focuses):
                        raise ValueError(
                            f"Frame {n}: title overlaps protected map focus; revise title position/timing"
                        )
        routes = 0
        for route, meta in route_specs:
            if (
                not route["start"]
                <= time
                < route.get("hide_at", timeline.source_duration)
            ):
                continue
            routes += 1
            trail, _ = route_pose(route, time, project)
            x, y = trail[-1]
            if meta:
                factor = route.get("sprite_scale", 1) * scale
                left, top = (
                    x - meta["anchor"][0] * factor,
                    y - meta["anchor"][1] * factor,
                )
                box = (
                    left,
                    top,
                    left + max(1, round(meta["frame_width"] * factor)),
                    top + max(1, round(meta["frame_height"] * factor)),
                )
            else:
                box = (x - 3, y - 3, x + 3, y + 3)
            if overlaps(box, (0, 0, width, height)):
                footprints.append(
                    (
                        max(0, box[0]),
                        max(0, box[1]),
                        min(width, box[2]),
                        min(height, box[3]),
                    )
                )
        if any(overlaps(box, blocked) for box in footprints for blocked in reserved):
            raise ValueError(
                f"Composition frame {n}: map symbol overlaps reserved subtitle/attribution space"
            )
        panels = []
        for i, item, geometry in callouts:
            if not visible(item):
                continue
            w, h, _, _ = geometry
            ax, ay = project(item["position"])
            offset = item.get("offset", [-100, -300])
            panels.append(
                {
                    "id": "callout:" + str(i),
                    "kind": "media" if item.get("image") else "callout",
                    "size": (w, h),
                    "preferred": (ax + offset[0] * scale, ay + offset[1] * scale),
                    "placement": item.get("placement", "auto"),
                }
            )
        if cta and visible(cta):
            metric = cta_layout["metric"]
            w, h = metric[2] - metric[0], metric[3] - metric[1]
            preferred_y = max(
                composer.margin, min(box[1] for box in focuses) - composer.gap - h
            )
            panels.append(
                {
                    "id": "cta",
                    "kind": "cta",
                    "size": (w, h),
                    "preferred": ((width - w) / 2, preferred_y),
                }
            )
            title_count += 1
        try:
            positions = composer.step(
                panels,
                focuses,
                reserved,
                annotations,
                {"markers": markers, "routes": routes, "titles": title_count},
                footprints=footprints,
            )
            boxes = (
                annotations
                + [(key, box) for key, box in positions.items()]
                + [("attribution", credit_box)]
            )
            errors = inspect_boxes(boxes, size)
            if errors:
                raise ValueError("; ".join(errors))
        except ValueError as exc:
            raise ValueError(
                f"Composition frame {n} ({n/fps:.3f}s output / {time:.3f}s source): {exc}"
            ) from exc
        plans.append({"positions": positions, "focuses": focuses, "boxes": boxes})
    return plans, callouts, cta_layout
