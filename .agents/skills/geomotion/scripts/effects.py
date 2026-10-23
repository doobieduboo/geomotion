"""Geographic tint and separately composited linear-light bloom, independent of topic."""
import copy
import math
import numpy as np
from PIL import Image, ImageFilter
from config import DEFAULTS


def glow_settings(value=None, *, land=False):
    preset = DEFAULTS['region_fill' if land else 'region_outline']['glow']
    result = copy.deepcopy(preset)
    if value is False:
        result['enabled'] = False
    elif isinstance(value, dict):
        result.update(value)
    elif value is not None and value is not True:
        raise ValueError('glow must be a boolean or object')
    if not isinstance(result.get('enabled', True), bool):
        raise ValueError('glow.enabled must be boolean')
    layers = result.get('layers', [])
    if not isinstance(layers, list) or len(layers) > 4:
        raise ValueError('glow.layers requires at most four layers')
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError('glow layer must be an object')
        for key in ('radius_design', 'gain'):
            value = layer.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('glow radius/gain must be finite and nonnegative')
    for key in ('strength', 'inside_gain', 'flag_strength'):
        if key in result and (not isinstance(result[key], (int, float)) or
                not math.isfinite(result[key]) or result[key] < 0):
            raise ValueError('glow gains must be finite and nonnegative')
    return result


def to_linear(rgb):
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def composite_emission(base, emission):
    """Add RGB radiance in linear light; leave alpha/zero-emission pixels exact."""
    if emission is None or not np.any(emission):
        return base
    pixels = np.asarray(base.convert('RGB'), dtype=np.float32) / 255
    light = np.clip(to_linear(pixels) + emission, 0, 1)
    encoded = np.where(light <= .0031308, light * 12.92,
                       1.055 * light ** (1 / 2.4) - .055)
    image = Image.fromarray(np.uint8(np.clip(encoded * 255 + .5, 0, 255)))
    if base.mode == 'RGBA':
        image = image.convert('RGBA')
        image.putalpha(base.getchannel('A'))
    return image


def bloom_emission(layer, settings, scale):
    """Blur color-weighted geographic emission; never blur/reveal the whole scene."""
    if not settings.get('enabled', True):
        return None
    rgba = np.asarray(layer.convert('RGBA'), dtype=np.float32) / 255
    # Gaussian filtering is linear: blur premultiplied linear RGB, not dark RGBa.
    source = to_linear(rgba[:, :, :3]) * rgba[:, :, 3:4]
    result = np.zeros_like(source)
    for channel in range(3):
        mask = Image.fromarray(np.uint8(np.clip(source[:, :, channel] * 255 + .5, 0, 255)))
        for item in settings['layers']:
            radius = item['radius_design'] * scale
            result[:, :, channel] += np.asarray(mask.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255 * item['gain']
    return result * settings.get('strength', 1)


def paint_land(base, layer, scale, *, blend='normal', kind='flag', glow=None):
    """Clip color to supplied geometry; only emitted light falls outside its edge."""
    if blend not in ('normal', 'terrain_tint') or kind not in ('color', 'flag'):
        raise ValueError('Invalid land blend or kind')
    if kind == 'flag' and blend != 'normal':
        raise ValueError('Flag colors must use normal blending')
    settings = glow_settings(glow, land=True)
    rgba = np.asarray(layer.convert('RGBA'), dtype=np.float32) / 255
    mask = rgba[:, :, 3]
    if not np.any(mask):
        return base
    if blend == 'terrain_tint':
        pixels = np.asarray(base.convert('RGB'), dtype=np.float32) / 255
        cfg = DEFAULTS['region_fill']
        multiplier = np.maximum(cfg['tint_floor'], rgba[:, :, :3] ** cfg['tint_gamma'] * cfg['tint_exposure'])
        tinted = np.clip(pixels * multiplier, 0, 1)
        result = pixels * (1 - mask[:, :, None]) + tinted * mask[:, :, None]
        colored = Image.fromarray(np.uint8(np.clip(result * 255 + .5, 0, 255))).convert('RGBA')
        if base.mode == 'RGBA':
            colored.putalpha(base.getchannel('A'))
        base = colored
    else:
        base = base.copy()
        base.alpha_composite(layer)
    if not settings['enabled']:
        return base
    emission_layer = layer.copy()
    # Preserve original texture color in flag emission; color fills emit their
    # authored saturated RGB. Alpha prevents distant/unrelated land from glowing.
    emission = bloom_emission(emission_layer, settings, scale)
    emission *= (1 - mask[:, :, None])
    terrain = np.asarray(base.convert('RGB'), dtype=np.float32).mean(axis=2) / 255
    emission += to_linear(rgba[:, :, :3]) * (mask * terrain * settings['inside_gain'])[:, :, None]
    if kind == 'flag':
        emission *= settings['flag_strength']
    return composite_emission(base, emission)
