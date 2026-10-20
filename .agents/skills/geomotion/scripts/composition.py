"""Deterministic screen composition; never drops evidence or invents visual layers."""

import math
from config import DEFAULTS
from layout import overlaps


def area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def inflate(box, gap):
    return (box[0] - gap, box[1] - gap, box[2] + gap, box[3] + gap)


def pixel_box(normalized, size):
    return tuple(value * size[i % 2] for i, value in enumerate(normalized))


def validate_composition(scene):
    options = scene.get("composition", {})
    if not isinstance(options, dict):
        raise ValueError("composition must be an object")
    allowed = set(DEFAULTS["composition"]["layout"])
    if set(options) - allowed:
        raise ValueError(
            "Unknown composition options: " + ", ".join(sorted(set(options) - allowed))
        )
    settings = {**DEFAULTS["composition"]["layout"], **options}
    for key in (
        "margin_design",
        "gap_design",
        "max_move_design_per_second",
        "placement_stability_weight",
    ):
        if (
            not isinstance(settings[key], (int, float))
            or not math.isfinite(settings[key])
            or settings[key] <= 0
        ):
            raise ValueError("Composition " + key + " must be positive and finite")
    if not 0 < settings["max_annotation_area_fraction"] < 1:
        raise ValueError("Invalid annotation area budget")
    for key in ("max_callouts", "max_media", "max_markers", "max_routes", "max_titles"):
        if type(settings[key]) is not int or settings[key] < 0:
            raise ValueError("Composition " + key + " must be a nonnegative integer")
    fallback = settings["fallback_focus_normalized"]
    if (
        len(fallback) != 4
        or not all(math.isfinite(v) for v in fallback)
        or not 0 <= fallback[0] < fallback[2] <= 1
        or not 0 <= fallback[1] < fallback[3] <= 1
    ):
        raise ValueError("Invalid fallback focus rectangle")
    ids = [region["id"] for region in scene.get("regions", []) if "id" in region]
    if len(ids) != len(set(ids)):
        raise ValueError("Region ids must be unique")
    for focus in scene.get("focuses", []):
        unknown = set(focus) - {"id", "start", "end", "event", "region_id", "bounds"}
        if unknown:
            raise ValueError("Unsupported focus fields: " + ", ".join(sorted(unknown)))
        if ("region_id" in focus) == ("bounds" in focus):
            raise ValueError(
                "Focus requires exactly one of region_id or geographic bounds"
            )
        if "region_id" in focus and focus["region_id"] not in ids:
            raise ValueError("Unknown focus region_id: " + focus["region_id"])
        if "bounds" in focus:
            west, south, east, north = focus["bounds"]
            if (
                not all(map(math.isfinite, (west, south, east, north)))
                or not -180 <= west < east <= 180
                or not -85 <= south < north <= 85
            ):
                raise ValueError(
                    "Invalid focus bounds; split antimeridian geometries explicitly"
                )
    cta = scene.get("cta")
    if cta is not None and (
        not isinstance(cta, dict)
        or not isinstance(cta.get("text"), str)
        or not cta["text"].strip()
    ):
        raise ValueError("CTA requires authored nonempty text")
    if cta:
        unknown = set(cta) - {"text", "start", "end", "event"}
        if unknown:
            raise ValueError("Unsupported CTA fields: " + ", ".join(sorted(unknown)))
    for item in scene.get("focuses", []) + ([cta] if cta else []):
        start, end = item.get("start", 0), item.get("end", scene["duration"])
        if (
            not all(map(math.isfinite, (start, end)))
            or not 0 <= start < end <= scene["duration"]
        ):
            raise ValueError("Composition interval outside source timeline")
    return settings


class Composer:
    """Step every output frame from zero, even when rendering only a later segment.

    Hard constraints win over placement preference. A blocked smooth path fails
    instead of teleporting a panel, hiding an archive, or changing camera/content.
    """

    def __init__(self, size, fps, settings=None):
        self.size, self.fps = size, fps
        self.settings = {**DEFAULTS["composition"]["layout"], **(settings or {})}
        scale = size[0] / DEFAULTS["design_width"]
        self.margin = self.settings["margin_design"] * scale
        self.gap = self.settings["gap_design"] * scale
        self.step_limit = self.settings["max_move_design_per_second"] * scale / fps
        self.previous = {}

    def _safe(self, box, obstacles):
        w, h = self.size
        m = self.margin
        return (
            m <= box[0]
            and m <= box[1]
            and box[2] <= w - m
            and box[3] <= h - m
            and not any(overlaps(box, inflate(other, self.gap)) for other in obstacles)
        )

    def _candidates(self, panel, obstacles, previous):
        w, h = self.size
        pw, ph = panel["size"]
        m = self.margin
        preferred = panel["preferred"]
        xs = [preferred[0], m, (w - pw) / 2, w - m - pw]
        ys = [preferred[1], m, (h - ph) / 2, h - m - ph]
        for box in obstacles:
            xs.extend((box[0] - self.gap - pw, box[2] + self.gap))
            ys.extend((box[1] - self.gap - ph, box[3] + self.gap))
        if previous:
            xs.append(previous[0])
            ys.append(previous[1])
        if panel.get("kind") == "cta":
            xs = [(w - pw) / 2]
        boxes = [(x, y, x + pw, y + ph) for x in xs for y in ys]
        if previous:
            # Candidate tracking is speed-limited in output seconds, not source seconds.
            extra = []
            for box in boxes:
                dx, dy = box[0] - previous[0], box[1] - previous[1]
                length = math.hypot(dx, dy)
                ratio = min(1, self.step_limit / max(length, 1e-9))
                x, y = previous[0] + dx * ratio, previous[1] + dy * ratio
                extra.append((x, y, x + pw, y + ph))
            boxes.extend(extra)
            boxes = [
                box
                for box in boxes
                if math.dist(box[:2], previous[:2]) <= self.step_limit + 1e-7
            ]
        return boxes

    def step(
        self, panels, focuses, reserved=(), annotations=(), counts=None, footprints=()
    ):
        counts = counts or {}
        totals = {
            **counts,
            "callouts": sum(p.get("kind") != "cta" for p in panels),
            "media": sum(p.get("kind") == "media" for p in panels),
        }
        for key in ("callouts", "media", "markers", "routes", "titles"):
            if totals.get(key, 0) > self.settings["max_" + key]:
                raise ValueError(
                    "Composition budget exceeded: "
                    + key
                    + "; revise authored timing, scale or framing"
                )
        obstacles = (
            list(focuses)
            + list(reserved)
            + [box for _, box in annotations]
            + list(footprints)
        )
        result = {}
        # Evidence is placed before supporting text. Nothing is discarded by priority.
        rank = {"media": 0, "cta": 1, "callout": 2}
        for panel in sorted(panels, key=lambda item: rank[item["kind"]]):
            key = panel["id"]
            if key in result:
                raise ValueError("Duplicate composition panel id: " + key)
            previous = self.previous.get(key)
            candidates = [
                box
                for box in self._candidates(panel, obstacles, previous)
                if self._safe(box, obstacles)
            ]
            if panel.get("placement", "auto") == "manual":
                x, y = panel["preferred"]
                pw, ph = panel["size"]
                candidates = [(x, y, x + pw, y + ph)]
                candidates = [box for box in candidates if self._safe(box, obstacles)]
                if previous:
                    candidates = [
                        box
                        for box in candidates
                        if math.dist(box[:2], previous[:2]) <= self.step_limit + 1e-7
                    ]
            if not candidates:
                raise ValueError(
                    "No safe continuous placement for "
                    + key
                    + "; reframe focus or change authored panel size/timing"
                )
            preferred = panel["preferred"]
            box = min(
                candidates,
                key=lambda b: math.dist(b[:2], preferred)
                + (
                    self.settings["placement_stability_weight"]
                    * math.dist(b[:2], previous[:2])
                    if previous
                    else 0
                ),
            )
            result[key] = box
            obstacles.append(box)
        annotation_area = (
            sum(area(box) for box in result.values())
            + sum(area(box) for _, box in annotations)
            + sum(area(box) for box in footprints)
        )
        if (
            annotation_area / (self.size[0] * self.size[1])
            > self.settings["max_annotation_area_fraction"]
        ):
            raise ValueError(
                "Annotation area budget exceeded; preserve more visible map"
            )
        self.previous = result
        return result
