"""Persistent, length-based boundary reveal; no connecting strokes between islands."""
import math
from config import DEFAULTS
from effects import glow_settings, bloom_emission


def validate_focus_strokes(region):
    """Reject ambiguous/resetting schedules before a render starts."""
    last_end = -math.inf
    for cue in region.get("focus_strokes", []):
        start, end = cue["start"], cue["end"]
        reveal = cue.get("reveal", 1)
        if not all(math.isfinite(v) for v in (start, end, reveal)):
            raise ValueError("Focus stroke times must be finite")
        if start < last_end or end <= start or reveal <= 0 or reveal > end-start+1e-9:
            raise ValueError("Focus strokes require ordered, nonoverlapping intervals and reveal within interval")
        for key in ("glow_radius_design", "glow_spread_design", "glow_opacity", "glow_fade_out", "stroke_width_design"):
            if key in cue and (not math.isfinite(cue[key]) or cue[key] < 0):
                raise ValueError("Focus stroke glow values must be finite and nonnegative")
        if cue.get('stroke_width_design', 1) == 0:
            raise ValueError('Focus stroke width must be positive')
        if cue.get("glow_opacity", 0) > 255:
            raise ValueError("Focus stroke glow opacity must be <=255")
        if "casing_opacity" in cue and (not math.isfinite(cue["casing_opacity"]) or not 0 <= cue["casing_opacity"] <= 255):
            raise ValueError("Focus casing opacity must be finite0..255")
        if "color" in cue and (len(cue["color"]) != 3 or any(
                not isinstance(v, int) or not 0 <= v <= 255 for v in cue["color"])):
            raise ValueError("Focus stroke color requires three RGB integers0..255")
        if "glow_layers" in cue:
            layers = cue["glow_layers"]
            if not isinstance(layers, list) or not 1 <= len(layers) <= 4:
                raise ValueError("Focus glow_layers requires one to four halo definitions")
            for layer in layers:
                radius, opacity, gain = layer["radius_design"], layer.get("opacity", 255), layer.get("gain", 1)
                if not all(math.isfinite(v) for v in (radius, opacity, gain)) or radius < 0 or not 0 <= opacity <= 255 or gain <= 0:
                    raise ValueError("Glow layers require finite nonnegative radius,opacity0..255 and positive gain")
        last_end = end


def stroke_state(region, time):
    """One core path: an active focus replaces the ordinary outline reveal."""
    active = next((c for c in region.get("focus_strokes", [])
                   if c["start"] <= time < c["end"]), None)
    cue = active if active is not None else region
    seconds = cue.get("reveal", 1 if active is not None else DEFAULTS['region_outline']['reveal'])
    progress = 1 if seconds <= 0 else max(0, min(1, (time-cue.get("start", 0))/seconds))
    origin = cue.get("stroke_origin", region.get("stroke_origin"))
    return progress, tuple(origin) if origin is not None else None, active


def outline_style(region, focus=None):
    """One preset owner; explicit scene values override inherited appearance."""
    base = DEFAULTS['region_outline']
    keys = ('stroke_width_design', 'casing_width_design', 'casing_opacity',
            'casing_color', 'glow_radius_design', 'glow_opacity')
    style = {key: base[key] for key in keys}
    for key in ('stroke_width_design','casing_width_design','casing_opacity','casing_color'):
        if key in region:style[key]=region[key]
    style['color'] = region.get('color', base['color'])
    style['glow'] = glow_settings()
    if focus is not None:
        style.update(base['focus_preset'])
        style.update({k:v for k,v in focus.items() if k not in ('start','end','reveal','stroke_origin')})
        # Explicit legacy single-halo controls replace the inherited multilayer
        # recipe rather than silently being ignored by it.
        if 'glow_layers' not in focus and any(k in focus for k in ('glow_radius_design','glow_opacity')):
            style.pop('glow_layers', None)
        if 'glow' not in focus and any(k in focus for k in ('glow_layers','glow_radius_design','glow_opacity')):
            style['glow'] = glow_settings(False)
        else:
            style['glow'] = glow_settings(focus.get('glow'))
    width = style['stroke_width_design']
    if not math.isfinite(width) or width <= 0:
        raise ValueError('Outline core width must be finite and positive')
    return style


def paint_outlines(size, scale, reference, focused, *, return_emission=False):
    """Render one reference border, replacing only the revealed focus path.

    Jobs supply projected pixel paths plus resolved styles. Widths use output
    scale only, never camera zoom. Separate masks prevent a white reference halo
    under the colored emphasis, including coincident neighboring boundaries.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageColor
    aa = DEFAULTS['region_outline']['antialias_scale']
    canvas = (size[0]*aa, size[1]*aa)
    core = Image.new('RGBA', canvas)
    casing = Image.new('RGBA', canvas)
    emphasis = Image.new('RGBA', canvas)
    halos = Image.new('RGBA', canvas)
    focus_emissions = []

    def line(layer, paths, width, fill):
        draw = ImageDraw.Draw(layer)
        for path in paths:
            points = [(x*aa,y*aa) for x,y in path]
            if len(points)<2:continue
            draw.line(points,fill=fill,width=width,joint='curve')
            radius=(width-1)/2
            for x,y in (points[0],points[-1]):
                draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=fill)

    def widths(style):
        w=max(1,round(style['stroke_width_design']*scale*aa))
        return w,max(w,round(style['casing_width_design']*scale*aa))

    def rgb(value):
        return ImageColor.getrgb(value) if isinstance(value,str) else tuple(value)

    # All reference borders share the preset halo radius; per-region core/color
    # overrides remain possible without changing the coordinate contract.
    for paths,style in reference:
        w,cw=widths(style)
        line(core,paths,w,rgb(style['color'])+(255,))
        line(casing,paths,cw,rgb(style['casing_color'])+(style['casing_opacity'],))
    base=DEFAULTS['region_outline']
    ordinary_glow=core.filter(ImageFilter.GaussianBlur(base['glow_radius_design']*scale*aa))
    ordinary_glow.putalpha(ordinary_glow.getchannel('A').point(lambda a:round(a*base['glow_opacity']/255)))
    for paths,style,fade in focused:
        if not paths:continue
        w,cw=widths(style)
        mask=Image.new('L',canvas)
        line(mask,paths,max(w,cw),255)
        # Erase old cores only on the revealed geometry; leave the rest of the
        # reference intact. Remove its soft halo locally as well.
        core.putalpha(ImageChops.subtract(core.getchannel('A'),mask))
        casing.putalpha(ImageChops.subtract(casing.getchannel('A'),mask))
        halo_mask=Image.new('L',canvas)
        margin=round(6*base['glow_radius_design']*scale*aa)
        line(halo_mask,paths,max(w,cw)+margin,255)
        ordinary_glow.putalpha(ImageChops.subtract(ordinary_glow.getchannel('A'),halo_mask))
        col=rgb(style['color'])
        if return_emission and style.get('glow',{}).get('enabled',True):
            light=Image.new('RGBA',canvas,col+(255,))
            light.putalpha(mask)
            light=light.resize(size,Image.Resampling.LANCZOS)
            radiant=bloom_emission(light,style['glow'],scale)
            if radiant is not None:focus_emissions.append(radiant*fade)
        line(emphasis,paths,cw,rgb(style['casing_color'])+(style['casing_opacity'],))
        line(emphasis,paths,w,col+(255,))
        emission=Image.new('L',canvas);line(emission,paths,w,255)
        spread=round(style.get('glow_spread_design',0)*scale*aa)
        if spread>0:emission=emission.filter(ImageFilter.MaxFilter(2*spread+1))
        layers=style.get('glow_layers',[{'radius_design':style['glow_radius_design'],'opacity':style['glow_opacity'],'gain':1}])
        for layer in layers:
            halo=emission.filter(ImageFilter.GaussianBlur(layer['radius_design']*scale*aa))
            opacity=layer.get('opacity',255)*fade;gain=layer.get('gain',1)
            glow=Image.new('RGBA',canvas,col+(255,))
            glow.putalpha(halo.point(lambda a:round(min(255,a*gain)*opacity/255)))
            halos.alpha_composite(glow)
    result=Image.new('RGBA',size)
    for layer in (ordinary_glow,halos,casing,core,emphasis):
        result.alpha_composite(layer.resize(size,Image.Resampling.LANCZOS))
    if return_emission:
        radiant=bloom_emission(core.resize(size,Image.Resampling.LANCZOS),glow_settings(),scale)
        for extra in focus_emissions:
            radiant=extra if radiant is None else radiant+extra
        return result,radiant
    return result


def map_cut(a, b):
    return abs(abs(a[0]) - 180) < 1e-7 and abs(abs(b[0]) - 180) < 1e-7


def projected_stroke_copies(path, project, world_vector, size):
    """Unwrap connected geometry before clipping; never bridge a camera wrap seam."""
    pieces = [[]]
    for point in path:
        if pieces[-1] and map_cut(pieces[-1][-1], point):
            pieces.append([])
        pieces[-1].append(point)
    if len(pieces) > 1:
        return [copy for piece in pieces if len(piece) > 1
                for copy in projected_stroke_copies(piece, project, world_vector, size)]
    wx, wy = world_vector
    norm = wx * wx + wy * wy
    points = []
    for ll in path:
        x, y = project(ll)
        if points:
            px, py = points[-1]
            turns = round(((px - x) * wx + (py - y) * wy) / norm)
            x, y = x + turns * wx, y + turns * wy
        points.append((x, y))
    if len(points) < 2:
        return []
    width, height = size
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    near = round(((width / 2 - (xmin + xmax) / 2) * wx
                  + (height / 2 - (ymin + ymax) / 2) * wy) / norm)
    radius = math.ceil(math.hypot(width, height) / math.sqrt(norm)) + 1
    return [[(x + k * wx, y + k * wy) for x, y in points]
            for k in range(near - radius, near + radius + 1)
            if xmax + k * wx >= -4 and xmin + k * wx <= width + 4
            and ymax + k * wy >= -4 and ymin + k * wy <= height + 4]


def prepare_stroke(polygons, origin=None):
    paths = []
    seen = set()
    for polygon in polygons:
        for ring in polygon:
            points = []
            for lon, lat, *_ in ring:
                p = (float(lon), float(lat))
                if not points or p != points[-1]:
                    points.append(p)
            if len(points) < 2:
                continue
            # Exact duplicate rings, including reversed/start-rotated copies.
            edges = frozenset(tuple(sorted((a, b))) for a, b in zip(points, points[1:]))
            if edges in seen:
                continue
            seen.add(edges)
            lengths = []
            for a, b in zip(points, points[1:]):
                dx = (b[0] - a[0] + 180) % 360 - 180
                ya = math.asinh(math.tan(math.radians(max(-85.0511, min(85.0511, a[1])))))
                yb = math.asinh(math.tan(math.radians(max(-85.0511, min(85.0511, b[1])))))
                lengths.append(0 if map_cut(a, b) else math.hypot(math.radians(dx), yb - ya))
            if sum(lengths) > 0:
                paths.append((points, lengths, sum(lengths)))
    # Establish mainland first, then draw disconnected components in sequence.
    paths.sort(key=lambda p: p[2], reverse=True)
    if origin is not None and paths:
        points, lengths, total = paths[0]
        if points[0] == points[-1]:
            body = points[:-1]
            index = min(range(len(body)), key=lambda i:
                (((body[i][0] - origin[0] + 180) % 360 - 180)
                 * math.cos(math.radians(origin[1]))) ** 2
                + (body[i][1] - origin[1]) ** 2)
            points = body[index:] + body[:index]
            points.append(points[0])
            lengths = lengths[index:] + lengths[:index]
            paths[0] = (points, lengths, total)
    return paths


def revealed_paths(paths, progress):
    remaining = max(0, min(1, progress)) * sum(p[2] for p in paths)
    result = []
    for points, lengths, total in paths:
        if remaining <= 0:
            break
        if remaining >= total:
            result.append(points)
            remaining -= total
            continue
        visible = [points[0]]
        for a, b, length in zip(points, points[1:], lengths):
            if remaining >= length:
                visible.append(b)
                remaining -= length
            else:
                ratio = remaining / length if length else 0
                dx = (b[0] - a[0] + 180) % 360 - 180
                # Interpolate in the same Mercator space as the measured length.
                ya = math.asinh(math.tan(math.radians(a[1])))
                yb = math.asinh(math.tan(math.radians(b[1])))
                visible.append((a[0] + dx * ratio, math.degrees(math.atan(math.sinh(ya + (yb - ya) * ratio)))))
                remaining = 0
                break
        if len(visible) > 1:
            result.append(visible)
        break
    return result
