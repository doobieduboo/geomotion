"""Measured text and image bounds in actual render pixels."""

from PIL import Image, ImageDraw


def wrap(text, font, width):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            if draw.textlength(word, font=font) > width:
                raise ValueError("Unbreakable text exceeds available width: " + word)
            candidate = (line + " " + word).strip()
            if line and draw.textlength(candidate, font=font) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def callout_layout(
    title, lines, title_font, body_font, max_width, padding, image_size=None
):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    available = max_width - 2 * padding
    if available <= 0:
        raise ValueError("Callout max width must exceed padding")
    blocks = [(line, title_font) for line in wrap(title, title_font, available) if line]
    for line in lines:
        blocks.extend((part, body_font) for part in wrap(line, body_font, available))
    content_width = max(
        (draw.textlength(text, font=font) for text, font in blocks), default=0
    )
    width = max_width if image_size else max(1, round(content_width + 2 * padding))
    image_height = (
        round((width - 2 * padding) * image_size[1] / image_size[0])
        if image_size
        else 0
    )
    rows, y = [], padding + image_height + (padding if image_size and blocks else 0)
    for text, font in blocks:
        bounds = font.getbbox(text or "Ag")
        line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
        rows.append((text, font, padding, y - bounds[1]))
        y += line_height + padding // 2
    height = y + padding - (padding // 2 if blocks else 0)
    return width, height, image_height, rows


def callout_image(image, item):
    """Display an exact source-pixel detail without modifying the original asset."""
    crop = item.get("image_crop")
    if crop is None:
        return image
    if image is None or not isinstance(crop, (list, tuple)) or len(crop) != 4:
        raise ValueError("image_crop requires an image and four source-pixel bounds")
    if any(type(v) is not int for v in crop):
        raise ValueError("image_crop bounds must be integer source pixels")
    left, top, right, bottom = crop
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError("image_crop must stay inside the original image")
    return image.crop((left, top, right, bottom))


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def inspect_boxes(boxes, size):
    errors = []
    for name, box in boxes:
        if box[0] < 0 or box[1] < 0 or box[2] > size[0] or box[3] > size[1]:
            errors.append(f"{name}: outside frame")
    for i, (name, box) in enumerate(boxes):
        for other, other_box in boxes[i + 1 :]:
            if overlaps(box, other_box):
                errors.append(f"{name}: overlaps {other}")
    return errors


def callout_opacity(item, time):
    """Source-time eased visibility; unchanged full opacity when fades are omitted."""
    start, end = item.get("start", 0), item.get("end", float("inf"))
    fade_in, fade_out = item.get("fade_in", 0), item.get("fade_out", 0)
    if fade_in < 0 or fade_out < 0 or fade_in + fade_out > end - start:
        raise ValueError("Callout fades must be nonnegative and fit within its lifetime")
    if time < start or time >= end:
        return 0.0
    def ease(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3 - 2 * value)
    incoming = ease((time - start) / fade_in) if fade_in else 1.0
    outgoing = ease((end - time) / fade_out) if fade_out else 1.0
    return min(incoming, outgoing)


def fade_callout(layer, item, time):
    """Fade the already composed frame, image, text and leader as one layer."""
    opacity = callout_opacity(item, time)
    if opacity >= 1:
        return layer
    result = layer.copy()
    result.putalpha(layer.getchannel("A").point(lambda alpha: round(alpha * opacity)))
    return result
