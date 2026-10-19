"""Editable transparent title layers reconstructed from visual references."""

import copy
import math

from config import DEFAULTS, SKILL_ROOT
from PIL import Image, ImageColor, ImageDraw, ImageFont


def title_config(definition, overrides=None):
    config = copy.deepcopy(definition)
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    if config.get("schema_version") != 1 or config.get("type") != "title":
        raise ValueError("Expected a schema_version 1 title definition")
    if not math.isfinite(config["duration"]) or config["duration"] <= 0:
        raise ValueError("Title duration must be positive and finite")
    if (
        not isinstance(config["content"]["headline"], str)
        or not config["content"]["headline"].strip()
    ):
        raise ValueError("Title headline cannot be empty")
    for name in ("enter", "compact", "subline", "tilt"):
        start, end = config["timing"][name]
        if not 0 <= start < end <= config["duration"]:
            raise ValueError(f"Invalid {name} timing; fit all ranges inside duration")
    if not 0 <= config["timing"]["exit_seconds"] <= config["duration"]:
        raise ValueError("Invalid exit duration")
    layout = config["layout"]
    if len(layout["center"]) != 2 or not all(0 <= v <= 1 for v in layout["center"]):
        raise ValueError("Title center must be a normalized [x,y]")
    if not 0 < layout["scale"] <= 4 or not 0 < layout["max_width"] <= 1:
        raise ValueError("Invalid title layout scale or width")
    style = config["style"]
    for name in (
        "headline_size",
        "compact_headline_size",
        "subline_size",
        "headline_condense",
        "compact_condense",
    ):
        if style[name] <= 0:
            raise ValueError(f"{name} must be positive")
    if (
        style["gap"] < 0
        or style["panel_radius"] < 0
        or len(style["panel_padding"]) != 2
        or min(style["panel_padding"]) < 0
    ):
        raise ValueError("Invalid panel spacing")
    for name in ("text_color", "panel_color", "caret_color"):
        ImageColor.getrgb(style[name])
    if (
        style["font_role"] not in DEFAULTS["typography"]
        or not (SKILL_ROOT / DEFAULTS["typography"][style["font_role"]]).is_file()
    ):
        raise ValueError("Title requires an available preset font role")
    return config


def progress(t, bounds):
    value = max(0.0, min(1.0, (t - bounds[0]) / (bounds[1] - bounds[0])))
    return value * value * (3 - 2 * value)


def text_image(text, font_path, size, color, condense=1):
    font = ImageFont.truetype(str(font_path), max(1, round(size)))
    box = font.getbbox(text)
    layer = Image.new(
        "RGBA", (max(1, box[2] - box[0] + 4), max(1, box[3] - box[1] + 4))
    )
    ImageDraw.Draw(layer).text((2 - box[0], 2 - box[1]), text, font=font, fill=color)
    if condense != 1:
        layer = layer.resize(
            (max(1, round(layer.width * condense)), layer.height),
            Image.Resampling.LANCZOS,
        )
    return layer


def render_title(config, time_s, size):
    """Return an RGBA layer; time is local to this component, not the scene."""
    canvas = Image.new("RGBA", size)
    if time_s < 0 or time_s >= config["duration"]:
        return canvas
    style, layout, timing = config["style"], config["layout"], config["timing"]
    if time_s < timing["enter"][0]:
        return canvas
    unit = size[0] / DEFAULTS["design_width"] * layout["scale"]
    compact = progress(time_s, timing["compact"])
    font_path = SKILL_ROOT / DEFAULTS["typography"][style["font_role"]]
    font_size = (
        style["headline_size"]
        + (style["compact_headline_size"] - style["headline_size"]) * compact
    ) * unit
    condense = (
        style["headline_condense"]
        + (style["compact_condense"] - style["headline_condense"]) * compact
    )
    headline = text_image(
        config["content"]["headline"],
        font_path,
        font_size,
        style["text_color"],
        condense,
    )
    subline = text_image(
        config["content"].get("subline", ""),
        font_path,
        style["subline_size"] * unit,
        style["text_color"],
        0.7,
    )
    # The main text remains editable; panel dimensions follow the fitted title.
    panel_w = max(
        headline.width, subline.width + round(style["panel_padding"][0] * 2 * unit)
    )
    panel_h = subline.height + round(style["panel_padding"][1] * 2 * unit)
    gap = round(style["gap"] * unit)
    caret_w = max(1, round(8 * unit))
    block = Image.new(
        "RGBA", (panel_w + caret_w * 2 + 4, headline.height + gap + panel_h + 4)
    )
    x = (block.width - headline.width) // 2
    reveal = progress(time_s, timing["enter"])
    shown = round(headline.width * reveal)
    if shown:
        block.alpha_composite(headline.crop((0, 0, shown, headline.height)), (x, 0))
    if reveal < 1:
        cx = x + shown
        ImageDraw.Draw(block).rectangle(
            (cx, 0, cx + caret_w, headline.height), fill=style["caret_color"]
        )
    sub_progress = progress(time_s, timing["subline"])
    if sub_progress > 0:
        panel = Image.new("RGBA", (panel_w, panel_h))
        ImageDraw.Draw(panel).rounded_rectangle(
            (0, 0, panel_w - 1, panel_h - 1),
            radius=round(style["panel_radius"] * unit),
            fill=style["panel_color"],
        )
        panel.alpha_composite(
            subline, ((panel_w - subline.width) // 2, (panel_h - subline.height) // 2)
        )
        block.alpha_composite(
            panel.crop((0, 0, max(1, round(panel_w * sub_progress)), panel_h)),
            ((block.width - panel_w) // 2, headline.height + gap),
        )
    maximum = round(size[0] * layout["max_width"])
    if block.width > maximum:
        ratio = maximum / block.width
        block = block.resize(
            (max(1, maximum), max(1, round(block.height * ratio))),
            Image.Resampling.LANCZOS,
        )
    block = block.rotate(
        style["tilt_degrees"] * progress(time_s, timing["tilt"]),
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )
    # Move the title upward as it compacts, leaving space for the second line.
    cy = layout["center"][1] * size[1] + (1 - compact) * panel_h / 2
    canvas.alpha_composite(
        block,
        (
            round(layout["center"][0] * size[0] - block.width / 2),
            round(cy - block.height / 2),
        ),
    )
    fade = timing["exit_seconds"]
    if fade and time_s > config["duration"] - fade:
        opacity = max(0, (config["duration"] - time_s) / fade)
        canvas.putalpha(
            canvas.getchannel("A").point(lambda value: round(value * opacity))
        )
    return canvas
