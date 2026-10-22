"""Regression checks for renderer-only performance shortcuts.

These checks use local synthetic tiles and never request Esri imagery.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "geomotion"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from render_scene import (
    adjusted_basemap,
    composite_glow,
    load_font,
    main as render_main,
)


class RenderShortcuts(unittest.TestCase):
    def test_identity_tone_reuses_image_without_enhancement(self):
        image = Image.new("RGB", (12, 12), (18, 70, 120))
        with (
            patch("render_scene.ImageEnhance.Color", side_effect=AssertionError("identity Color called")),
            patch("render_scene.ImageEnhance.Brightness", side_effect=AssertionError("identity Brightness called")),
        ):
            result = adjusted_basemap(image, {"saturation": 1.0, "brightness": 1.0})
        self.assertIs(result, image)

    def test_nondefault_tone_matches_previous_order(self):
        image = Image.new("RGB", (12, 12), (18, 70, 120))
        settings = {"saturation": 0.72, "brightness": 1.3}
        legacy = ImageEnhance.Brightness(
            ImageEnhance.Color(image).enhance(settings["saturation"])
        ).enhance(settings["brightness"])
        result = adjusted_basemap(image, settings)
        self.assertEqual(result.tobytes(), legacy.tobytes())

    def test_empty_glow_is_noop(self):
        base = Image.new("RGBA", (48, 48), (40, 60, 80, 255))
        before = base.tobytes()
        with patch("render_scene.Image.Image.filter", side_effect=AssertionError("blur called")):
            composite_glow(base, None, 6)
        self.assertEqual(base.tobytes(), before)

    def test_active_glow_matches_previous_two_pass_blend(self):
        base = Image.new("RGBA", (48, 48), (40, 60, 80, 255))
        stroke = Image.new("RGBA", base.size)
        for x in range(12, 36):
            for y in range(20, 23):
                stroke.putpixel((x, y), (220, 175, 80, 210))
        old = base.copy()
        old.alpha_composite(stroke.filter(ImageFilter.GaussianBlur(3)))
        old.alpha_composite(stroke)
        composite_glow(base, stroke, 3)
        self.assertEqual(base.tobytes(), old.tobytes())

    def test_font_cache_respects_distinct_env_paths(self):
        regular = SKILL_ROOT / "fonts/OpenSans-Regular.ttf"
        bold = SKILL_ROOT / "fonts/OpenSans-Bold.ttf"
        with patch.dict(os.environ, {"GEOMOTION_FONT_REGULAR": str(regular)}):
            one = load_font(19)
            self.assertIs(one, load_font(19))
        with patch.dict(os.environ, {"GEOMOTION_FONT_REGULAR": str(bold)}):
            two = load_font(19)
            self.assertIsNot(one, two)
        with patch.dict(os.environ, {"GEOMOTION_FONT_REGULAR": str(regular)}):
            self.assertIs(one, load_font(19))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class EmptyMapRender(unittest.TestCase):
    def test_scene_with_no_active_geo_layers_skips_glow_and_tone(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scene = root / "scene.json"
            video = root / "empty.mp4"
            scene.write_text(json.dumps({
                "duration": 0.125,
                "camera": [{"time": 0, "center": [0, 0], "zoom": 0}],
            }))
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), (24, 55, 68)).save(tile, format="JPEG")
            with (
                patch("sys.argv", ["render_scene", str(scene), "--output", str(video)]),
                patch("render_scene.urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(tile.getvalue())),
                patch("render_scene.Image.Image.filter", side_effect=AssertionError("unnecessary GaussianBlur")),
                patch("render_scene.ImageEnhance.Color", side_effect=AssertionError("identity Color")),
                patch("render_scene.ImageEnhance.Brightness", side_effect=AssertionError("identity Brightness")),
            ):
                render_main()
            self.assertTrue(video.is_file())
            self.assertGreater(video.stat().st_size, 0)
            self.assertTrue(video.with_suffix(".layout.json").is_file())


if __name__ == "__main__":
    unittest.main()
